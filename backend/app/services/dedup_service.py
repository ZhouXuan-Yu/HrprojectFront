"""Dedup service: resume deduplication by phone hash, email, and name."""
import hashlib
import logging
from app.utils.response import AppError

log = logging.getLogger(__name__)


def _mock_enabled():
    from app.utils.response import should_mock_fallback
    return should_mock_fallback()


def hash_phone(phone: str) -> str:
    """Strip non-digit chars and return SHA256 hex digest.

    This is the same algorithm used for Candidate.mobile_hash.
    Returns empty string if phone is empty after stripping.
    """
    if not phone:
        return ''
    digits = ''.join(ch for ch in phone if ch.isdigit())
    if not digits:
        return ''
    return hashlib.sha256(digits.encode('utf-8')).hexdigest()


def check_duplicates(candidate_data: dict) -> dict:
    """Search existing candidates for potential duplicates by phone, email, name.

    Args:
        candidate_data: dict with keys 'name', 'phone', 'email' (all optional)

    Returns:
        dict: {has_duplicates: bool, candidates: [{id, candidate_no, name,
               match_reason, match_score}]}
    """
    from app.models.candidate import Candidate
    from app.extensions import db

    name = (candidate_data.get('name') or '').strip()
    phone = (candidate_data.get('phone') or '').strip()
    email = (candidate_data.get('email') or '').strip()

    matched_ids = set()
    matches = []

    try:
        # 1. Match by mobile_hash (exact)
        if phone:
            phone_hash = hash_phone(phone)
            if phone_hash:
                phone_matches = Candidate.query.filter(
                    Candidate.mobile_hash == phone_hash,
                    Candidate.is_deleted == 0
                ).all()
                for c in phone_matches:
                    if c.id not in matched_ids:
                        matched_ids.add(c.id)
                        matches.append({
                            'id': c.id,
                            'candidate_no': c.candidate_no,
                            'name': c.candidate_name,
                            'match_reason': 'phone',
                            'match_score': 'high',
                        })

        # 2. Match by email (case-insensitive)
        if email:
            email_lower = email.lower()
            email_matches = Candidate.query.filter(
                db.func.lower(Candidate.email) == email_lower,
                Candidate.is_deleted == 0
            ).all()
            for c in email_matches:
                if c.id not in matched_ids:
                    matched_ids.add(c.id)
                    matches.append({
                        'id': c.id,
                        'candidate_no': c.candidate_no,
                        'name': c.candidate_name,
                        'match_reason': 'email',
                        'match_score': 'high',
                    })

        # 3. Match by name (case-insensitive, exact match)
        if name:
            name_lower = name.lower()
            name_matches = Candidate.query.filter(
                db.func.lower(Candidate.candidate_name) == name_lower,
                Candidate.is_deleted == 0
            ).all()
            for c in name_matches:
                if c.id not in matched_ids:
                    matched_ids.add(c.id)
                    matches.append({
                        'id': c.id,
                        'candidate_no': c.candidate_no,
                        'name': c.candidate_name,
                        'match_reason': 'name',
                        'match_score': 'medium',
                    })

    except Exception as exc:
        log.error('DB query failed in check_duplicates: %s', exc, exc_info=True)
        if _mock_enabled():
            return _mock_check_duplicates(candidate_data)
        raise AppError('DB_ERROR', '查询重复候选人失败', 500)

    return {
        'has_duplicates': len(matches) > 0,
        'candidates': matches,
    }


def find_duplicates_in_pool() -> list:
    """Scan the entire candidate table for potential duplicates.

    Groups candidates by mobile_hash (non-null) and by email (non-null),
    returning groups with 2+ candidates.

    Returns:
        list: [{reason: 'phone'|'email', hash_or_email: str, candidates: [...]}]
    """
    from app.models.candidate import Candidate
    from app.extensions import db

    groups = []

    try:
        # 1. Group by mobile_hash
        phone_rows = (
            db.session.query(
                Candidate.mobile_hash,
                db.func.count(Candidate.id).label('cnt')
            )
            .filter(
                Candidate.mobile_hash.isnot(None),
                Candidate.mobile_hash != '',
                Candidate.is_deleted == 0,
            )
            .group_by(Candidate.mobile_hash)
            .having(db.func.count(Candidate.id) > 1)
            .all()
        )

        for row in phone_rows:
            candidates = Candidate.query.filter(
                Candidate.mobile_hash == row.mobile_hash,
                Candidate.is_deleted == 0,
            ).all()
            groups.append({
                'reason': 'phone',
                'hash_or_email': row.mobile_hash,
                'candidates': [_candidate_brief(c) for c in candidates],
            })

        # 2. Group by email (case-insensitive, non-null)
        email_rows = (
            db.session.query(
                db.func.lower(Candidate.email).label('email_lower'),
                db.func.count(Candidate.id).label('cnt'),
            )
            .filter(
                Candidate.email.isnot(None),
                Candidate.email != '',
                Candidate.is_deleted == 0,
            )
            .group_by(db.func.lower(Candidate.email))
            .having(db.func.count(Candidate.id) > 1)
            .all()
        )

        for row in email_rows:
            candidates = Candidate.query.filter(
                db.func.lower(Candidate.email) == row.email_lower,
                Candidate.is_deleted == 0,
            ).all()
            groups.append({
                'reason': 'email',
                'hash_or_email': row.email_lower,
                'candidates': [_candidate_brief(c) for c in candidates],
            })

    except Exception as exc:
        log.error('DB query failed in find_duplicates_in_pool: %s', exc, exc_info=True)
        if _mock_enabled():
            return _mock_duplicate_groups()
        raise AppError('DB_ERROR', '扫描重复候选人失败', 500)

    return groups


def merge_candidates(primary_id: int, duplicate_ids: list) -> dict:
    """Merge duplicate candidates into the primary.

    - Keeps the primary candidate intact
    - Soft-deletes the duplicates
    - Copies tags/notes from duplicates to primary (append, no overwrite)
    - Updates RecruitProcess records pointing to duplicates → point to primary

    Args:
        primary_id: ID of the primary candidate to keep
        duplicate_ids: list of duplicate candidate IDs to merge

    Returns:
        dict: summary of what was merged
    """
    from app.models.candidate import Candidate, CandidateTagRel
    from app.models.process import RecruitProcess
    from app.extensions import db

    if not primary_id or not duplicate_ids:
        raise AppError('BAD_REQUEST', '缺少 primary_id 或 duplicate_ids 参数')

    try:
        primary = Candidate.query.filter_by(id=primary_id, is_deleted=0).first()
        if not primary:
            raise AppError('NOT_FOUND', '主候选人不存在', 404)

        duplicates = Candidate.query.filter(
            Candidate.id.in_(duplicate_ids),
            Candidate.is_deleted == 0,
        ).all()

        found_ids = {c.id for c in duplicates}
        missing = [str(did) for did in duplicate_ids if did not in found_ids]
        if missing:
            log.warning('Some duplicate IDs not found or already deleted: %s', missing)

        merged_notes = []
        merged_tags = []
        updated_process_count = 0

        for dup in duplicates:
            # Copy note (append, no overwrite)
            if dup.note:
                if primary.note:
                    primary.note += '\n---\n' + dup.note
                else:
                    primary.note = dup.note
                merged_notes.append(dup.candidate_no)

            # Copy tags from duplicates to primary
            dup_tags = CandidateTagRel.query.filter_by(candidate_id=dup.id).all()
            for tag_rel in dup_tags:
                existing = CandidateTagRel.query.filter_by(
                    candidate_id=primary_id,
                    tag_id=tag_rel.tag_id,
                ).first()
                if not existing:
                    new_rel = CandidateTagRel(
                        candidate_id=primary_id,
                        tag_id=tag_rel.tag_id,
                        tag_source=tag_rel.tag_source,
                        valid_end=tag_rel.valid_end,
                    )
                    db.session.add(new_rel)
                    merged_tags.append(tag_rel.tag_id)

            # Update RecruitProcess records → point to primary
            processes = RecruitProcess.query.filter_by(candidate_id=dup.id).all()
            for proc in processes:
                proc.candidate_id = primary_id
                updated_process_count += 1

            # Soft-delete the duplicate
            dup.soft_delete()

        db.session.commit()

        return {
            'primary_id': primary_id,
            'primary_no': primary.candidate_no,
            'duplicates_merged': len(duplicates),
            'notes_copied': len(merged_notes),
            'tags_copied': len(set(merged_tags)),
            'process_updated': updated_process_count,
            'missing_ids': missing,
        }

    except AppError:
        raise
    except Exception as exc:
        db.session.rollback()
        log.error('DB write failed in merge_candidates: %s', exc, exc_info=True)
        if _mock_enabled():
            return _mock_merge_result(primary_id, duplicate_ids)
        raise AppError('DB_ERROR', '合并候选人失败', 500)


# --- internal helpers ---

def _candidate_brief(c) -> dict:
    """Convert Candidate ORM object to a brief dedup dict."""
    return {
        'id': c.id,
        'candidate_no': c.candidate_no,
        'name': c.candidate_name,
        'mobile': c.mobile,
        'email': c.email,
        'status': c.status,
        'created_at': c.created_at.isoformat() if c.created_at else None,
    }


# --- mock fallbacks ---

def _mock_check_duplicates(candidate_data: dict) -> dict:
    """Mock check_duplicates for development without DB."""
    phone = (candidate_data.get('phone') or '').strip()
    email = (candidate_data.get('email') or '').strip()
    name = (candidate_data.get('name') or '').strip()

    candidates = []
    if phone and '13800138000' in phone:
        candidates.append({
            'id': 1,
            'candidate_no': 'C2026070012',
            'name': '张三',
            'match_reason': 'phone',
            'match_score': 'high',
        })
    if email and 'zhangsan@example.com' in email.lower():
        if not any(c['id'] == 1 for c in candidates):
            candidates.append({
                'id': 1,
                'candidate_no': 'C2026070012',
                'name': '张三',
                'match_reason': 'email',
                'match_score': 'high',
            })
    if name and name.lower() == '张三':
        if not any(c['id'] == 1 for c in candidates):
            candidates.append({
                'id': 1,
                'candidate_no': 'C2026070012',
                'name': '张三',
                'match_reason': 'name',
                'match_score': 'medium',
            })

    return {
        'has_duplicates': len(candidates) > 0,
        'candidates': candidates,
    }


def _mock_duplicate_groups() -> list:
    """Mock duplicate groups for development without DB."""
    return [
        {
            'reason': 'phone',
            'hash_or_email': 'mock_hash_abc123',
            'candidates': [
                {'id': 1, 'candidate_no': 'C2026070012', 'name': '张三',
                 'mobile': '138****0000', 'email': 'zhangsan@example.com',
                 'status': 'available', 'created_at': '2026-07-12T10:00:00'},
                {'id': 5, 'candidate_no': 'C2026070020', 'name': '张珊',
                 'mobile': '138****0000', 'email': 'zhangshan@example.com',
                 'status': 'available', 'created_at': '2026-07-14T14:30:00'},
            ],
        },
        {
            'reason': 'email',
            'hash_or_email': 'lisi@example.com',
            'candidates': [
                {'id': 3, 'candidate_no': 'C2026070011', 'name': '李四',
                 'mobile': '139****1111', 'email': 'lisi@example.com',
                 'status': 'available', 'created_at': '2026-07-11T09:00:00'},
                {'id': 7, 'candidate_no': 'C2026070030', 'name': '李肆',
                 'mobile': '137****2222', 'email': 'lisi@example.com',
                 'status': 'locked', 'created_at': '2026-07-15T16:00:00'},
            ],
        },
    ]


def _mock_merge_result(primary_id: int, duplicate_ids: list) -> dict:
    """Mock merge result for development without DB."""
    return {
        'primary_id': primary_id,
        'primary_no': 'C2026070012',
        'duplicates_merged': len(duplicate_ids),
        'notes_copied': 1,
        'tags_copied': 2,
        'process_updated': 1,
        'missing_ids': [],
    }
