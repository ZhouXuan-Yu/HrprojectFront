"""Hire service: Offer and Entry management with full state machine.

Offer status state machine:
  draft -> sent -> accepted / rejected / expired

Each transition is validated. Salary is checked against demand budget.
Duplicate offers are prevented.
"""
import logging
import random
from datetime import datetime, timedelta, date
from app.utils.response import AppError
from app.extensions import db

log = logging.getLogger(__name__)


def _biz_no(prefix):
    """业务编号：前缀 + 时间戳(秒) + 3位随机数，避免同秒并发/连续创建撞唯一键。"""
    return f"{prefix}{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}"

OFFER_STATUS_LABELS = {0: '草稿', 1: '已发送', 2: '已接受', 3: '已拒绝', 4: '已过期'}

# Allowed state transitions: current -> [allowed next statuses]
OFFER_TRANSITIONS = {
    0: [1],       # draft -> sent
    1: [2, 3, 4], # sent -> accepted / rejected / expired
    2: [],        # accepted: terminal
    3: [],        # rejected: terminal
    4: [],        # expired: terminal
}


def _validate_offer_transition(offer, new_status):
    """Validate offer status transition. Raises AppError on invalid transition."""
    allowed = OFFER_TRANSITIONS.get(offer.offer_status, [])
    if new_status not in allowed:
        current_label = OFFER_STATUS_LABELS.get(offer.offer_status, '未知')
        target_label = OFFER_STATUS_LABELS.get(new_status, '未知')
        raise AppError(
            'INVALID_STATE',
            f'Offer状态"{current_label}"({offer.offer_status})不允许切换到"{target_label}"({new_status})'
        )


def _check_salary_within_budget(offer, salary_json):
    """Validate that offer salary is within the demand's salary range.

    salary_json is expected to contain 'baseSalary' or 'totalPackage' keys.
    The demand's salary_range is a string like '15K-25K' or '¥15K - ¥25K / 月'.
    """
    if not salary_json:
        return True  # No salary data, skip validation

    try:
        from app.models.demand import RecruitDemand
        demand = RecruitDemand.query.filter_by(id=offer.demand_id, is_deleted=0).first()
        if not demand or not demand.salary_range:
            return True  # No demand budget defined, skip

        salary_str = demand.salary_range
        import re
        numbers = re.findall(r'\d+', salary_str.replace('K', '000').replace('k', '000'))
        if len(numbers) < 2:
            return True  # Can't parse budget range

        budget_min = float(numbers[0])
        budget_max = float(numbers[1])

        # Determine the offered base salary
        offered = float(salary_json.get('baseSalary', salary_json.get('totalPackage', 0)))
        if offered <= 0:
            return True  # Not a numeric salary

        if offered < budget_min * 0.8 or offered > budget_max * 1.2:
            log.warning(
                "Offer salary %.2f outside budget range [%.2f, %.2f] for demand %s",
                offered, budget_min, budget_max, offer.demand_id,
            )
            return False

        return True
    except Exception as exc:
        log.warning("Salary budget check failed: %s", exc)
        return True  # If parsing fails, allow


def _check_duplicate_offer(resume_id, demand_id):
    """Check if the candidate already has an active offer for this demand.

    Returns (ok, existing_offer_no): ok=True 表示无重复可创建；
    ok=False 时 existing_offer_no 为已有进行中 Offer 的编号。
    """
    try:
        from app.models.hire import Offer
        existing = Offer.query.filter(
            Offer.resume_id == resume_id,
            Offer.demand_id == demand_id,
            Offer.offer_status.in_([0, 1]),  # draft or sent
            Offer.is_deleted == 0,
        ).first()
        if existing:
            log.warning(
                "Duplicate offer detected: resume_id=%s, demand_id=%s, existing_offer=%s",
                resume_id, demand_id, existing.offer_no,
            )
            return False, existing.offer_no
    except Exception as exc:
        log.warning("Duplicate offer check failed: %s", exc)
    return True, None


# ── Core API ──

def create_offer(data):
    """Create a new Offer record with status=draft (0).

    Validates:
      - Salary within demand budget range
      - No duplicate active offer for same candidate+demand
    """
    from app.models.hire import Offer, HireEvent

    now = datetime.now()
    offer_no = _biz_no('OF')

    # Default valid_deadline to 7 days
    valid_deadline = data.get('validDeadline')
    if not valid_deadline:
        valid_deadline = now + timedelta(days=7)
    elif isinstance(valid_deadline, str):
        # 前端 date 输入传 'YYYY-MM-DD' 字符串，必须转成 datetime 才能写入 DateTime 列
        parsed = _parse_date(valid_deadline)
        if not parsed:
            raise AppError('VALIDATION_ERROR', 'Offer有效期格式不正确（应为 YYYY-MM-DD）')
        valid_deadline = datetime.combine(parsed, datetime.max.time().replace(microsecond=0))
    elif isinstance(valid_deadline, date) and not isinstance(valid_deadline, datetime):
        valid_deadline = datetime.combine(valid_deadline, datetime.max.time().replace(microsecond=0))

    # Validate salary against budget (deferred: we need the offer id first)
    # We store the salary_json for later checks during send_offer

    # Validate no duplicate for same resume+demand
    resume_id = data.get('resumeId')
    demand_id = data.get('demandId')
    if resume_id and demand_id:
        _dup_ok, _dup_no = _check_duplicate_offer(resume_id, demand_id)
        if not _dup_ok:
            raise AppError('DUPLICATE_OFFER',
                           f'该候选人在本需求已有进行中的Offer（{_dup_no}），请勿重复创建；可在Offer列表中查看或发送该Offer')

    offer = Offer(
        offer_no=offer_no,
        resume_id=resume_id or 0,
        process_id=data.get('processId', 0),
        demand_id=demand_id or 0,
        last_interview_id=data.get('lastInterviewId'),
        offer_content=data.get('offerContent', ''),
        salary_json=data.get('salaryJson', {}),
        valid_deadline=valid_deadline,
        offer_status=0,  # 0 = draft
        send_user_id=data.get('sendUserId', 0),
        send_time=now,
    )
    db.session.add(offer)
    db.session.flush()

    # Create hire event
    event_no = _biz_no('HE')
    event = HireEvent(
        event_no=event_no,
        process_id=data.get('processId'),
        offer_id=offer.id,
        hire_type=1,  # 1 = external offer
        event_status=0,  # 0 = pending
    )
    db.session.add(event)

    db.session.commit()
    log.info("Offer created (draft): %s, event: %s", offer_no, event_no)

    return {'id': offer_no, 'created': True, 'eventId': event_no}


def send_offer(offer_id):
    """Send offer — transitions from draft(0) to sent(1).

    Generates offer letter content if empty.
    Validates salary is within the demand's budget range.
    """
    from app.models.hire import Offer

    offer = Offer.query.filter_by(offer_no=offer_id, is_deleted=0).first()
    if not offer:
        raise AppError('NOT_FOUND', f'Offer {offer_id} 不存在')

    _validate_offer_transition(offer, 1)  # draft -> sent

    # Validate salary against demand budget
    if not _check_salary_within_budget(offer, offer.salary_json or {}):
        raise AppError('SALARY_OUT_OF_RANGE', 'Offer薪资超出需求预算范围，请调整')

    # Generate offer content if empty
    if not offer.offer_content:
        offer.offer_content = _generate_offer_letter(offer)

    now = datetime.now()
    offer.offer_status = 1  # sent
    offer.send_time = now

    db.session.commit()
    log.info("Offer sent: %s -> candidate(resume_id=%s)", offer_id, offer.resume_id)

    # 发送 Offer 邮件（含候选人确认链接）—— best-effort
    email_sent, email_msg = False, '未尝试'
    try:
        from app.services.confirm_service import send_offer_email
        email_sent, email_msg = send_offer_email(offer)
    except Exception as exc:
        log.warning("Offer 邮件发送失败（best-effort）: %s", exc)
        email_msg = str(exc)

    return {
        'sent': True,
        'id': offer_id,
        'sendTime': now.strftime('%Y-%m-%d %H:%M:%S'),
        'offerContent': offer.offer_content,
        'emailSent': email_sent,
        'emailMsg': email_msg,
    }


def accept_offer(offer_id):
    """Accept offer — sent(1) -> accepted(2).

    Auto-creates Entry record for onboarding.
    Updates process status to 'accepted'.
    """
    from app.models.hire import Offer

    offer = Offer.query.filter_by(offer_no=offer_id, is_deleted=0).first()
    if not offer:
        raise AppError('NOT_FOUND', f'Offer {offer_id} 不存在')

    _validate_offer_transition(offer, 2)  # sent -> accepted

    offer.offer_status = 2  # accepted
    db.session.flush()

    # Auto-create entry
    _create_entry_from_offer(offer)

    # Update process status
    _update_process_status(offer, 6)  # accepted

    db.session.commit()
    log.info("Offer accepted: %s", offer_id)

    return {'accepted': True, 'id': offer_id}


def reject_offer(offer_id, reason=None):
    """Reject offer — sent(1) -> rejected(3).

    Reopens the demand position by decrementing filled_count if previously incremented.
    Updates process status to 'giveup'.
    """
    from app.models.hire import Offer

    offer = Offer.query.filter_by(offer_no=offer_id, is_deleted=0).first()
    if not offer:
        raise AppError('NOT_FOUND', f'Offer {offer_id} 不存在')

    _validate_offer_transition(offer, 3)  # sent -> rejected

    offer.offer_status = 3  # rejected
    db.session.flush()

    # Reopen the demand position
    _reopen_demand_position(offer)

    # Update process status
    _update_process_status(offer, 7)  # giveup

    # 释放候选人回人才库
    _release_candidate_for_offer(offer)

    db.session.commit()
    log.info("Offer rejected: %s, reason=%s", offer_id, reason or '无')

    return {'rejected': True, 'id': offer_id}


def withdraw_offer(offer_id, reason=None):
    """Withdraw offer — any active state -> rejected(3).

    HR-initiated withdrawal. Only valid for draft(0) or sent(1) status.
    """
    from app.models.hire import Offer

    offer = Offer.query.filter_by(offer_no=offer_id, is_deleted=0).first()
    if not offer:
        raise AppError('NOT_FOUND', f'Offer {offer_id} 不存在')

    if offer.offer_status not in (0, 1):
        current_label = OFFER_STATUS_LABELS.get(offer.offer_status, '未知')
        raise AppError('INVALID_STATE', f'Offer状态为"{current_label}"，无法撤回')

    offer.offer_status = 3  # rejected
    offer.soft_delete()

    # Reopen demand position (only if was sent)
    if offer.offer_status == 1:
        _reopen_demand_position(offer)

    # 释放候选人回人才库
    _release_candidate_for_offer(offer)

    db.session.commit()
    log.info("Offer withdrawn: %s, reason=%s", offer_id, reason or '无')

    return {'withdrawn': True, 'id': offer_id}


def expire_offers():
    """Mark offers older than 14 days in 'sent'(1) status as 'expired'(4).

    Returns count of expired offers.
    """
    from app.models.hire import Offer

    cutoff = datetime.now() - timedelta(days=14)
    expired_offers = Offer.query.filter(
        Offer.offer_status == 1,  # sent
        Offer.send_time <= cutoff,
        Offer.is_deleted == 0,
    ).all()

    count = 0
    for offer in expired_offers:
        offer.offer_status = 4  # expired
        _reopen_demand_position(offer)
        count += 1

    if count > 0:
        db.session.commit()
        log.info("Expired %d offers older than 14 days", count)

    return {'expiredCount': count}


def get_offer(offer_id):
    """Get offer detail by offer_no."""
    from app.models.hire import Offer
    offer = Offer.query.filter_by(offer_no=offer_id, is_deleted=0).first()
    if not offer:
        raise AppError('NOT_FOUND', f'Offer {offer_id} 不存在')

    return {
        'id': offer.offer_no,
        'resumeId': offer.resume_id,
        'processId': offer.process_id,
        'demandId': offer.demand_id,
        'offerContent': offer.offer_content,
        'salaryJson': offer.salary_json,
        'validDeadline': offer.valid_deadline.strftime('%Y-%m-%d %H:%M:%S') if offer.valid_deadline else None,
        'status': offer.offer_status,
        'statusLabel': OFFER_STATUS_LABELS.get(offer.offer_status, '未知'),
        'sendTime': offer.send_time.strftime('%Y-%m-%d %H:%M:%S') if offer.send_time else None,
    }


def update_offer_status(offer_id, data):
    """Update offer status (legacy). If accepted, auto-create entry."""
    from app.models.hire import Offer
    offer = Offer.query.filter_by(offer_no=offer_id, is_deleted=0).first()
    if not offer:
        raise AppError('NOT_FOUND', f'Offer {offer_id} 不存在')

    new_status = data.get('status')
    if new_status not in (0, 1, 2, 3, 4):
        raise AppError('BAD_REQUEST', f'无效的状态值: {new_status}')

    _validate_offer_transition(offer, new_status)
    offer.offer_status = new_status

    if new_status == 2:
        _create_entry_from_offer(offer)
        _update_process_status(offer, 6)
    elif new_status == 3:
        _reopen_demand_position(offer)
        _update_process_status(offer, 7)
        _release_candidate_for_offer(offer)

    db.session.commit()

    return {'updated': True, 'status': new_status}


def list_offers(page=1, page_size=20):
    """List all offers with pagination."""
    from app.models.hire import Offer

    query = Offer.query.filter(Offer.is_deleted == 0).order_by(Offer.id.desc())
    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for offer in rows:
        items.append({
            'id': offer.offer_no,
            'resumeId': offer.resume_id,
            'processId': offer.process_id,
            'demandId': offer.demand_id,
            'offerContent': offer.offer_content,
            'salaryJson': offer.salary_json,
            'validDeadline': offer.valid_deadline.strftime('%Y-%m-%d %H:%M:%S') if offer.valid_deadline else None,
            'status': offer.offer_status,
            'statusLabel': OFFER_STATUS_LABELS.get(offer.offer_status, '未知'),
            'sendTime': offer.send_time.strftime('%Y-%m-%d %H:%M:%S') if offer.send_time else None,
        })

    return {'items': items, 'total': total, 'page': page, 'pageSize': page_size}


# ── Entry management ──

def _create_entry_from_offer(offer):
    """Auto-create entry when offer is accepted."""
    from app.models.hire import Entry, HireEvent

    event = HireEvent.query.filter_by(offer_id=offer.id, is_deleted=0).first()
    if not event:
        return

    now = datetime.now()
    entry_no = _biz_no('EN')
    entry = Entry(
        entry_no=entry_no,
        event_id=event.id,
        resume_id=offer.resume_id,
        dept_id=1,  # TODO: resolve from demand
        position_id=1,
        entry_date=now.date(),
    )
    db.session.add(entry)

    event.event_status = 1  # 1 = entry created
    log.info("Auto-created entry %s from accepted offer %s", entry_no, offer.offer_no)


def create_entry(data):
    """Create entry record manually."""
    from app.models.hire import Entry
    now = datetime.now()
    entry_no = _biz_no('EN')
    entry = Entry(
        entry_no=entry_no,
        event_id=data.get('eventId') or 0,
        resume_id=data.get('resumeId') or 0,
        dept_id=data.get('deptId') or 0,
        position_id=data.get('positionId') or 0,
        entry_date=_parse_date(data.get('entryDate')) or now.date(),
    )
    db.session.add(entry)
    db.session.commit()
    return {'id': entry_no, 'created': True}


def get_entry(entry_id):
    """Get entry detail by entry_no."""
    from app.models.hire import Entry
    entry = Entry.query.filter_by(entry_no=entry_id, is_deleted=0).first()
    if not entry:
        raise AppError('NOT_FOUND', f'入职单 {entry_id} 不存在')

    return {
        'id': entry.entry_no,
        'eventId': entry.event_id,
        'resumeId': entry.resume_id,
        'deptId': entry.dept_id,
        'positionId': entry.position_id,
        'entryDate': entry.entry_date.strftime('%Y-%m-%d') if entry.entry_date else None,
    }


def list_entries(page=1, page_size=20):
    """List all entries with pagination."""
    from app.models.hire import Entry

    query = Entry.query.filter(Entry.is_deleted == 0).order_by(Entry.id.desc())
    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for entry in rows:
        items.append({
            'id': entry.entry_no,
            'eventId': entry.event_id,
            'resumeId': entry.resume_id,
            'deptId': entry.dept_id,
            'positionId': entry.position_id,
            'entryDate': entry.entry_date.strftime('%Y-%m-%d') if entry.entry_date else None,
        })

    return {'items': items, 'total': total, 'page': page, 'pageSize': page_size}


# ── Internal helpers ──

def _generate_offer_letter(offer):
    """Generate a basic offer letter content."""
    from app.models.demand import RecruitDemand
    from app.models.candidate import Candidate, Resume

    candidate_name = '候选人'
    position_name = '岗位'
    dept_name = '部门'

    try:
        resume = Resume.query.filter_by(id=offer.resume_id, is_deleted=0).first()
        if resume and resume.candidate_id:
            c = Candidate.query.filter_by(id=resume.candidate_id, is_deleted=0).first()
            if c:
                candidate_name = c.candidate_name

        demand = RecruitDemand.query.filter_by(id=offer.demand_id, is_deleted=0).first()
        if demand:
            dept_name = f'部门#{demand.dept_id}'
            position_name = f'岗位#{demand.position_id}'
    except Exception:
        pass

    return (
        f"【Offer Letter】\n\n"
        f"尊敬的 {candidate_name} 先生/女士：\n\n"
        f"感谢您参加我司面试。经过综合评估，我们非常荣幸地邀请您加入 {dept_name}，"
        f"担任 {position_name} 一职。\n\n"
        f"具体薪资待遇以附件/系统记录为准。如您接受此Offer，请在有效期内确认。\n\n"
        f"期待与您共事！\n"
        f"{datetime.now().strftime('%Y-%m-%d')}"
    )


def _reopen_demand_position(offer):
    """When offer is rejected/expired, reopen the demand by decrementing filled_count."""
    try:
        from app.models.demand import RecruitDemand
        demand = RecruitDemand.query.filter_by(id=offer.demand_id, is_deleted=0).first()
        if demand and demand.filled_count and demand.filled_count > 0:
            demand.filled_count -= 1
            log.info("Demand %s filled_count decremented to %s due to offer rejection", demand.demand_no, demand.filled_count)
    except Exception as exc:
        log.warning("Failed to reopen demand position: %s", exc)


def _update_process_status(offer, new_process_status):
    """Update the recruit process status for a given offer."""
    try:
        from app.models.process import RecruitProcess
        if offer.process_id:
            process = RecruitProcess.query.filter_by(id=offer.process_id, is_deleted=0).first()
            if process:
                process.process_status = new_process_status
    except Exception as exc:
        log.warning("Failed to update process status: %s", exc)


def _release_candidate_for_offer(offer):
    """Offer 被拒/撤回后，把候选人从面试锁定中释放回人才库（available）。"""
    try:
        from app.models.candidate import Candidate, Resume
        resume = Resume.query.filter_by(id=offer.resume_id, is_deleted=0).first()
        if resume and resume.candidate_id:
            cand = Candidate.query.filter_by(id=resume.candidate_id, is_deleted=0).first()
            if cand and cand.status == 'locked':
                cand.status = 'available'
                log.info("候选人锁已释放（Offer终止）: id=%s name=%s", cand.id, cand.candidate_name)
    except Exception as exc:
        log.warning("Failed to release candidate for offer: %s", exc)


def _parse_date(val):
    """Parse a date string to a Python date object. Returns None on failure."""
    if not val:
        return None
    if isinstance(val, date):
        return val
    try:
        return datetime.strptime(str(val)[:10], '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None
