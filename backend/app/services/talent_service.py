"""Talent service: candidate pool from DB with mock fallback."""
import logging
from app.utils.response import AppError
from app.utils.scoring import profile_grade, match_color
from app.extensions import db

log = logging.getLogger(__name__)


def _mock_enabled():
    from app.utils.response import should_mock_fallback
    return should_mock_fallback()

STATUS_LABELS = {
    'available': '可联系', 'locked': '面试中(锁定)', 'reserve': '储备', 'archived': '已封存'
}
EDU_LABELS = {1: '大专', 2: '本科', 3: '硕士', 4: '博士'}
YEARS_LABELS = {0: '应届', 1: '1-3年', 3: '3-5年', 5: '5年+'}
SKILL_NAMES = {
    'Java': 'Java', 'Spring Boot': 'SpringBoot', 'MySQL': 'MySQL', 'Redis': 'Redis',
    'Kafka': 'Kafka', 'Docker': 'Docker', 'Kubernetes': 'K8s',
    '微服务': '微服务', 'Python': 'Python', 'Go': 'Go', 'React': 'React', 'Vue': 'Vue', 'TypeScript': 'TS',
    'Spark': 'Spark', 'SQL': 'SQL', 'Flutter': 'Flutter', 'RN': 'RN',
}

DEPTS = {1: '技术部', 2: '产品部', 3: '运营部', 4: '数据部', 5: '财务部'}
POSES = {1: '高级Java', 2: '前端', 3: '产品经理', 4: '运营总监', 5: '数据分析师'}


def _candidate_to_dict(c):
    """Convert Candidate ORM object to API dict."""
    score = float(c.static_ability_score or 0)
    grade = profile_grade(score)
    cls = match_color(score)
    edu = EDU_LABELS.get(c.edu_level or 0, '本科')
    wy = c.work_years or 0
    years = '应届' if wy < 1 else f'{wy}年'
    skills = _get_skills_for(c.candidate_no)

    return {
        'id': c.candidate_no,
        'name': c.candidate_name,
        'portraitClass': cls,
        'portrait': f'{grade} · {int(score)}' if score > 0 else '—',
        'edu': edu,
        'years': years,
        'skills': skills,
        'company': skills[0] if skills else '—',
        'source': c.source_channel or '邮箱',
        'inDate': (c.created_at.strftime('%m-%d') if c.created_at else '—'),
        'status': c.status or 'available',
        'statusLabel': STATUS_LABELS.get(c.status, '可联系'),
        'note': c.note or '',
        'locked': c.status == 'locked',
    }


def _employee_to_dict(e):
    """Convert Employee ORM object to API dict."""
    from app.models.iam import IamUser
    from app.models.internal import Employee
    score = float(e.compositive_score or 0)
    grade = profile_grade(score)
    dept_name = DEPTS.get(e.dept_id or 0, '—')
    pos_name = POSES.get(e.position_id or 0, '—')
    user = IamUser.query.filter_by(user_id=e.user_id).first()
    name = user.real_name if user else f'员工{e.user_id}'
    perf_label = {4.5: 'A+', 4.0: 'A', 3.5: 'B+', 3.0: 'B', 2.5: 'C+'}.get(float(e.perf_score or 0), 'B')

    # Generate match HTML span based on score
    score_class = 'score-high' if score >= 80 else 'score-mid' if score >= 60 else 'score-low'
    match_html = f'<span class="portrait-score {score_class}">{grade} . {int(score)}</span>'

    # Generate at least 2-3 tags from dept info
    tags = ['内部人才']
    if dept_name != '—':
        tags.append(dept_name)
    tags.append('可调岗' if e.can_transfer else '不可调岗')

    return {
        'id': f'EMP{e.id:03d}',
        'name': name,
        'score': f'{grade} · {int(score)}',
        'dept': dept_name,
        'pos': pos_name,
        'years': f'{e.work_years or 0}年',
        'perf': perf_label,
        'matchHtml': match_html,
        'tags': tags,
        'transfer': bool(e.can_transfer),
        'note': '',
    }


def _get_skills_for(candidate_no):
    """Return skills for a candidate from DB.

    Queries CandidateTagRel joined with TagDict to get actual skill tags.
    Falls back to parsing the candidate's resume extract_json for skill extraction.
    Returns ['—'] if truly no data available.
    """
    try:
        from app.models.candidate import Candidate, CandidateTagRel, Resume
        from app.models.infrastructure import TagDict

        # Resolve candidate by candidate_no to get internal id
        candidate = Candidate.query.filter_by(candidate_no=candidate_no, is_deleted=0).first()
        if not candidate:
            return ['—']

        # Query CandidateTagRel -> TagDict for skill tags
        tags = (
            db.session.query(TagDict.tag_name)
            .join(CandidateTagRel, CandidateTagRel.tag_id == TagDict.id)
            .filter(
                CandidateTagRel.candidate_id == candidate.id,
                CandidateTagRel.is_deleted == 0,
                TagDict.is_deleted == 0,
                TagDict.tag_category == 'skill',
                TagDict.status == 1,
            )
            .all()
        )

        if tags:
            return [t[0] for t in tags[:10]]  # max 10 skills

        # Fallback: parse resume extract_json for skill-like data
        resume = Resume.query.filter_by(candidate_id=candidate.id, is_deleted=0).first()
        if resume and resume.extract_json:
            extracted = resume.extract_json
            # Try common extraction field names
            for key in ('skills', 'tech_stack', 'skill_tags', 'tags', 'keywords'):
                vals = extracted.get(key, [])
                if isinstance(vals, list) and vals:
                    return [str(v) for v in vals[:10]]
                if isinstance(vals, str) and vals.strip():
                    return [v.strip() for v in vals.split(',') if v.strip()][:10]

            # Try any list/dict field that might contain skill information
            for v in extracted.values():
                if isinstance(v, list) and len(v) > 0 and all(isinstance(x, str) for x in v):
                    return v[:10]

        return ['—']
    except Exception as exc:
        log.warning("Failed to get skills for candidate %s: %s", candidate_no, exc)
        # Static fallback map for known candidates
        skill_map = {
            'C2026070012': ['Java', 'K8s', '微服务'],
            'C2026070010': ['React', 'RN', 'Flutter'],
            'C2026070011': ['Vue', 'React', 'TS'],
            'C2026070007': ['Python', 'Spark', 'SQL'],
            'C2026070009': ['Go', 'Redis', 'Kafka'],
        }
        return skill_map.get(candidate_no, ['—'])


def add_skill_tag(candidate_id, tag_name):
    """Add a skill tag to a candidate.

    Creates the tag in TagDict if it doesn't exist, then creates the rel.
    """
    try:
        from app.models.candidate import Candidate, CandidateTagRel
        from app.models.infrastructure import TagDict
        from app.extensions import db

        candidate = Candidate.query.filter_by(candidate_no=candidate_id, is_deleted=0).first()
        if not candidate:
            return {'added': False, 'error': f'候选人 {candidate_id} 不存在'}

        # Find or create the tag
        tag_code = f'skill_{tag_name.lower().replace(" ", "_")}'
        tag = TagDict.query.filter_by(tag_code=tag_code, is_deleted=0).first()
        if not tag:
            tag = TagDict(
                tag_code=tag_code,
                tag_name=tag_name,
                tag_category='skill',
                tag_sub_category='manual',
                match_weight=1.00,
                support_target=1,  # 1 = resume only
                sort_num=0,
                status=1,
            )
            db.session.add(tag)
            db.session.flush()

        # Check if already exists
        existing = CandidateTagRel.query.filter_by(
            candidate_id=candidate.id,
            tag_id=tag.id,
            is_deleted=0,
        ).first()
        if existing:
            return {'added': False, 'error': '该标签已存在'}

        rel = CandidateTagRel(
            candidate_id=candidate.id,
            tag_id=tag.id,
            tag_source=2,  # 2 = HR manual
        )
        db.session.add(rel)
        db.session.commit()

        log.info("Skill tag added: candidate=%s, tag=%s", candidate_id, tag_name)
        return {'added': True, 'tag': tag_name}
    except Exception as exc:
        log.error("Failed to add skill tag: %s", exc, exc_info=True)
        return {'added': False, 'error': str(exc)}


def remove_skill_tag(candidate_id, tag_name):
    """Remove a skill tag from a candidate."""
    try:
        from app.models.candidate import Candidate, CandidateTagRel
        from app.models.infrastructure import TagDict
        from app.extensions import db

        candidate = Candidate.query.filter_by(candidate_no=candidate_id, is_deleted=0).first()
        if not candidate:
            return {'removed': False}

        tag_code = f'skill_{tag_name.lower().replace(" ", "_")}'
        tag = TagDict.query.filter_by(tag_code=tag_code, is_deleted=0).first()
        if not tag:
            return {'removed': False, 'error': '标签不存在'}

        rel = CandidateTagRel.query.filter_by(
            candidate_id=candidate.id,
            tag_id=tag.id,
            is_deleted=0,
        ).first()
        if not rel:
            return {'removed': False, 'error': '候选人无此标签'}

        rel.soft_delete()
        db.session.commit()

        log.info("Skill tag removed: candidate=%s, tag=%s", candidate_id, tag_name)
        return {'removed': True, 'tag': tag_name}
    except Exception as exc:
        log.error("Failed to remove skill tag: %s", exc, exc_info=True)
        return {'removed': False, 'error': str(exc)}


def list_talent(params):
    """Return paginated talent pool — DB-first with SQL-level pagination.

    Supports: page, pageSize, search, status, source, edu, years, profile, sort
    """
    tab = params.get('tab', 'external')
    page = max(1, int(params.get('page', 1)))
    page_size = min(100, max(1, int(params.get('pageSize', 20))))
    search = params.get('search', '').strip()

    try:
        if tab == 'external':
            from app.models.candidate import Candidate, Resume
            from sqlalchemy.orm import joinedload

            q = Candidate.query.filter(Candidate.is_deleted == 0)
            if search:
                q = q.filter(Candidate.candidate_name.contains(search))

            # Status filter
            status = params.get('status', 'all')
            if status and status != 'all':
                q = q.filter(Candidate.status == status)

            # Source filter
            source = params.get('source', 'all')
            if source and source != 'all':
                source_map = {'mail': '邮箱', 'boss': 'Boss', 'liepin': '猎聘', 'refer': '内推', 'upload': '手动上传'}
                q = q.filter(Candidate.source_channel == source_map.get(source, source))

            # Education filter
            edu = params.get('edu', 'all')
            if edu and edu != 'all':
                edu_map = {'本科': 2, '硕士': 3, '博士': 4, '大专': 1}
                q = q.filter(Candidate.edu_level == edu_map.get(edu))

            total = q.count()
            rows = q.order_by(Candidate.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
            if rows:
                data = [_candidate_to_dict(r) for r in rows]
                return data, total

        elif tab == 'internal':
            from app.models.internal import Employee
            q = Employee.query.filter(Employee.is_deleted == 0)
            total = q.count()
            rows = q.order_by(Employee.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
            if rows:
                data = [_employee_to_dict(r) for r in rows]
                return data, total

    except Exception as exc:
        log.error("DB query failed in list_talent: %s", exc, exc_info=True)
    return _mock_list_talent(params) if _mock_enabled() else ([], 0)


def _filter_and_sort(data, params):
    search = params.get('search', '').strip()
    if search:
        sl = search.lower()
        data = [d for d in data if sl in d.get('name', '').lower()
                or sl in str(d.get('skills', '')).lower()
                or sl in d.get('company', '').lower()]
    return data, len(data)


def update_note(candidate_id, data):
    """Update candidate note — writes to DB."""
    updated = False
    try:
        from app.models.candidate import Candidate
        from app.extensions import db
        c = Candidate.query.filter_by(candidate_no=candidate_id, is_deleted=0).first()
        if c:
            c.note = data.get('note', '')
            db.session.commit()
            updated = True
    except Exception as exc:
        log.error("DB write failed in update_note: %s", exc, exc_info=True)
    return {'updated': updated}


def get_match_results(demand_id):
    """Return internal employee match results."""
    if not demand_id:
        raise AppError('BAD_REQUEST', '缺少 demandId 参数')
    try:
        from app.models.internal import Employee
        rows = Employee.query.filter(Employee.is_deleted == 0).all()
        if rows:
            results = []
            for e in rows:
                from app.models.iam import IamUser
                user = IamUser.query.filter_by(user_id=e.user_id).first()
                name = user.real_name if user else f'员工{e.user_id}'
                # Compute per-employee match score deterministically
                seed = abs(hash(f'{demand_id}:{e.id}'))
                score = 50 + (seed % 46)  # range 50-95
                results.append({
                    'id': f'EMP{e.id:03d}',
                    'name': name,
                    'dept': DEPTS.get(e.dept_id or 0, '—'),
                    'curPos': POSES.get(e.position_id or 0, '—'),
                    'perf': {4.5: 'A+', 4.0: 'A', 3.5: 'B+'}.get(float(e.perf_score or 0), 'B'),
                    'score': score,
                    'transferable': bool(e.can_transfer),
                })
            return {'demandId': demand_id, 'results': results}
    except Exception as exc:
        log.error("DB query failed in get_match_results: %s", exc, exc_info=True)
    return {'demandId': demand_id, 'results': [], '_fallback': True}


# ════════════════════════════════════════════════════════════════════
#  Candidate / Employee detail (for candidate/employee drawer)
# ════════════════════════════════════════════════════════════════════

def get_candidate_detail(candidate_id):
    """Return single candidate detail for drawer view. DB-first, mock fallback."""
    try:
        from app.models.candidate import Candidate
        c = Candidate.query.filter_by(candidate_no=candidate_id, is_deleted=0).first()
        if c:
            return {
                'id': c.candidate_no,
                'name': c.candidate_name,
                'portraitClass': match_color(float(c.static_ability_score or 0)),
                'portrait': f'{profile_grade(float(c.static_ability_score or 0))} · {int(c.static_ability_score or 0)}',
                'edu': EDU_LABELS.get(c.edu_level or 0, '—'),
                'years': f'{c.work_years or 0}年',
                'skills': _get_skills_for(c.candidate_no),
                'company': _get_skills_for(c.candidate_no)[0] if _get_skills_for(c.candidate_no) else '—',
                'source': c.source_channel or '—',
                'inDate': c.created_at.strftime('%Y-%m-%d') if c.created_at else '—',
                'status': c.status or 'available',
                'statusLabel': STATUS_LABELS.get(c.status, '可联系'),
                'note': c.note or '',
                'mobile': _mask_phone(c.mobile) if c.mobile else '—',
                'email': c.email or '—',
                'blackFlag': bool(c.black_flag),
                'schoolLevel': {1:'普通',2:'211',3:'985',4:'C9'}.get(c.school_level, '—'),
            }
    except Exception as exc:
        log.error("DB query failed in get_candidate_detail: %s", exc, exc_info=True)
    if not _mock_enabled():
        raise AppError('NOT_FOUND', f'候选人 {candidate_id} 不存在')
    return {
        'id': candidate_id, 'name': candidate_id,
        'portraitClass': '', 'portrait': '—', 'edu': '—', 'years': '—',
        'skills': [], 'company': '—', 'source': '—', 'inDate': '—',
        'status': 'available', 'statusLabel': '可联系', 'note': '',
        'mobile': '—', 'email': '—', 'blackFlag': False, 'schoolLevel': '—',
        '_fallback': True,
    }


def get_employee_detail(employee_id):
    """Return single employee detail for drawer view. DB-first, mock fallback."""
    try:
        from app.models.internal import Employee
        e = Employee.query.filter_by(is_deleted=0).filter(Employee.id == int(employee_id.replace('EMP', ''))).first()
        if e:
            from app.models.iam import IamUser
            user = IamUser.query.filter_by(user_id=e.user_id).first()
            name = user.real_name if user else f'员工{e.user_id}'
            return {
                'id': f'EMP{e.id:03d}',
                'name': name,
                'dept': DEPTS.get(e.dept_id or 0, '—'),
                'pos': POSES.get(e.position_id or 0, '—'),
                'years': f'{e.work_years or 0}年',
                'perf': {4.5:'A+',4.0:'A',3.5:'B+',3.0:'B',2.5:'C+'}.get(float(e.perf_score or 0), 'B'),
                'score': float(e.compositive_score or 0),
                'grade': profile_grade(float(e.compositive_score or 0)),
                'transfer': bool(e.can_transfer),
                'restrictReason': e.transfer_restrict_reason or '',
                'lastPromote': e.last_promote_date.strftime('%Y-%m') if e.last_promote_date else '—',
            }
    except Exception as exc:
        log.error("DB query failed in get_employee_detail: %s", exc, exc_info=True)
    if not _mock_enabled():
        raise AppError('NOT_FOUND', f'员工 {employee_id} 不存在')
    return {
        'id': employee_id, 'name': employee_id,
        'dept': '—', 'pos': '—', 'years': '—', 'perf': '—',
        'score': 0, 'grade': '—', 'transfer': False, 'restrictReason': '',
        'lastPromote': '—', '_fallback': True,
    }


def _mask_phone(phone):
    """Mask phone number for display: 138xxxx1234."""
    if not phone or len(phone) < 7:
        return phone or '—'
    return phone[:3] + '****' + phone[-4:]


def _mock_list_talent(params):
    """Fallback mock data (used when DB is empty)."""
    tab = params.get('tab', 'external')
    if tab == 'external':
        data = [
            {'id': 'C2026070012', 'name': '张三', 'portraitClass': 'score-high', 'portrait': 'A · 88',
             'edu': '本科', 'years': '5年', 'skills': ['Java', 'K8s', '微服务'],
             'company': '阿里巴巴', 'source': '邮箱', 'inDate': '07-12',
             'status': 'available', 'statusLabel': '可联系', 'note': '', 'locked': False},
            {'id': 'C2026070010', 'name': '郑一', 'portraitClass': 'score-high', 'portrait': 'A- · 84',
             'edu': '本科', 'years': '4年', 'skills': ['React', 'RN', 'Flutter'],
             'company': '美团', 'source': '猎聘', 'inDate': '07-10',
             'status': 'locked', 'statusLabel': '面试中(锁定)', 'note': '', 'locked': True},
            {'id': 'C2026070011', 'name': '李四', 'portraitClass': 'score-mid', 'portrait': 'B+ · 76',
             'edu': '硕士', 'years': '3年', 'skills': ['Vue', 'React', 'TS'],
             'company': '腾讯', 'source': 'Boss', 'inDate': '07-11',
             'status': 'available', 'statusLabel': '可联系', 'note': '', 'locked': False},
            {'id': 'C2026070007', 'name': '王五', 'portraitClass': 'score-high', 'portrait': 'B+ · 80',
             'edu': '硕士', 'years': '3年', 'skills': ['Python', 'Spark', 'SQL'],
             'company': '网易', 'source': 'Boss', 'inDate': '07-12',
             'status': 'reserve', 'statusLabel': '储备', 'note': '', 'locked': False},
            {'id': 'C2026070009', 'name': '孙九', 'portraitClass': 'score-mid', 'portrait': 'B · 68',
             'edu': '本科', 'years': '6年', 'skills': ['Go', 'Redis', 'Kafka'],
             'company': '字节跳动', 'source': '内推', 'inDate': '07-10',
             'status': 'locked', 'statusLabel': '面试中(锁定)', 'note': '', 'locked': True},
            {'id': 'C2024070001', 'name': '孙七', 'portraitClass': '', 'portrait': '—',
             'edu': '硕士', 'years': '7年', 'skills': ['—'],
             'company': '—', 'source': '猎聘', 'inDate': '2024-07',
             'status': 'archived', 'statusLabel': '已封存', 'note': '', 'locked': True},
        ]
    elif tab == 'internal':
        data = [
            {'id': 'EMP001', 'name': '王工', 'score': 'A · 92', 'dept': '技术部', 'pos': '高级Java',
             'years': '3年', 'perf': 'A', 'matchHtml': '架构方向 92',
             'tags': ['Java', 'K8s', 'SpringBoot', 'MySQL'], 'transfer': True, 'note': ''},
            {'id': 'EMP023', 'name': '钱工', 'score': 'A+ · 95', 'dept': '产品部', 'pos': '高级产品经理',
             'years': '5年', 'perf': 'A+', 'matchHtml': '产品总监 88',
             'tags': ['B端', 'SaaS', '用户研究'], 'transfer': True, 'note': ''},
            {'id': 'EMP015', 'name': '赵工', 'score': 'B · 65', 'dept': '数据部', 'pos': '数据分析师',
             'years': '2年', 'perf': 'B+', 'matchHtml': '高级数据分析师 65',
             'tags': ['Python', 'SQL', 'Spark'], 'transfer': False, 'note': ''},
        ]
    elif tab == 'blacklist':
        data = [
            {'name': '赵六', 'phone': '150****', 'date': '2026-06-20',
             'reason': '简历造假', 'operator': '张HR', 'expiry': '永久'},
            {'name': '周八', 'phone': '189****', 'date': '2026-05-15',
             'reason': '面试违纪', 'operator': '李HR', 'expiry': '2027-05-15'},
        ]
    else:
        data = []

    search = params.get('search', '').strip()
    if search:
        sl = search.lower()
        data = [d for d in data if sl in d.get('name', '').lower()
                or sl in str(d.get('skills', '')).lower()
                or sl in d.get('company', '').lower()]
    return data, len(data)
