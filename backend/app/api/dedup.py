"""Dedup API: /api/dedup/* — resume deduplication endpoints."""
from flask import Blueprint, request
from app.utils.response import success, error, AppError

bp = Blueprint('dedup', __name__)


@bp.route('/check', methods=['POST'])
def check_duplicates():
    """POST /api/dedup/check — check a candidate for duplicates.

    Body: { name?: string, phone?: string, email?: string }
    """
    from app.services.dedup_service import check_duplicates
    body = request.get_json(silent=True) or {}

    if not any(k in body for k in ('name', 'phone', 'email')):
        raise AppError('BAD_REQUEST', '请提供姓名、手机号或邮箱中至少一项')

    result = check_duplicates(body)
    return success(result)


@bp.route('/scan')
def scan_duplicates():
    """GET /api/dedup/scan — scan entire pool for duplicate candidates."""
    from app.services.dedup_service import find_duplicates_in_pool
    groups = find_duplicates_in_pool()
    return success({
        'total_groups': len(groups),
        'groups': groups,
    })


@bp.route('/merge', methods=['POST'])
def merge_duplicates():
    """POST /api/dedup/merge — merge duplicate candidates.

    Body: { primary_id: int, duplicate_ids: list[int] }
    """
    from app.services.dedup_service import merge_candidates
    body = request.get_json(silent=True) or {}

    primary_id = body.get('primary_id')
    duplicate_ids = body.get('duplicate_ids', [])

    if not primary_id:
        raise AppError('BAD_REQUEST', '缺少 primary_id 参数')
    if not isinstance(duplicate_ids, list) or not duplicate_ids:
        raise AppError('BAD_REQUEST', '缺少 duplicate_ids 参数或格式错误')

    result = merge_candidates(primary_id, duplicate_ids)
    return success(result)
