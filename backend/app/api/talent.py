"""Talent API: /api/talent/*"""
from flask import Blueprint, request, g
from app.utils.response import success, success_list, error, AppError

bp = Blueprint('talent', __name__)


@bp.route('/list')
def get_list():
    """GET /api/talent/list — paginated talent pool."""
    from app.services.talent_service import list_talent
    data, total = list_talent(request.args)
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', 20))
    return success_list(data, total, page, page_size)


@bp.route('/<candidate_id>/note', methods=['PATCH'])
def update_note(candidate_id):
    """PATCH /api/talent/{id}/note — update candidate note."""
    from app.services.talent_service import update_note
    result = update_note(candidate_id, request.get_json(silent=True) or {})
    return success(result)


@bp.route('/match')
def get_match():
    """GET /api/talent/match — internal employee match results."""
    from app.services.talent_service import get_match_results
    result = get_match_results(request.args.get('demandId', ''))
    return success(result)


@bp.route('/match', methods=['POST'])
def create_match():
    """POST /api/talent/match — calculate match result for a candidate against a demand."""
    from app.services.match_service import get_match_result
    body = request.get_json(silent=True) or {}
    candidate_id = body.get('candidateId', '')
    demand_id = body.get('demandId', '')
    if not candidate_id or not demand_id:
        raise AppError('BAD_REQUEST', '缺少 candidateId 或 demandId 参数')
    result = get_match_result(demand_id, candidate_id)
    return success(result)


@bp.route('/candidate/<candidate_id>')
def get_candidate(candidate_id):
    """GET /api/talent/candidate/{id} — single candidate detail."""
    from app.services.talent_service import get_candidate_detail
    data = get_candidate_detail(candidate_id)
    return success(data)


@bp.route('/employee/<employee_id>')
def get_employee(employee_id):
    """GET /api/talent/employee/{id} — single employee detail."""
    from app.services.talent_service import get_employee_detail
    data = get_employee_detail(employee_id)
    return success(data)


@bp.route('/link', methods=['POST'])
def link_to_demand():
    """POST /api/talent/link — link candidates to demand."""
    from app.services.demand_service import link_candidate_to_demand
    body = request.get_json(silent=True) or {}
    demand_id = body.get('demandId') or ''
    names = body.get('names') or []
    if not demand_id or not names:
        raise AppError('BAD_REQUEST', '缺少 demandId 或 names 参数')
    results = []
    for name in names:
        r = link_candidate_to_demand(demand_id, name)
        results.append({'name': name, **r})
    return success({'linked': len(results), 'total': len(names), 'candidates': results})


@bp.route('/contact', methods=['POST'])
def contact_candidate():
    """POST /api/talent/contact — record candidate contact action."""
    from app.services.talent_service import update_note
    body = request.get_json(silent=True) or {}
    candidate_id = body.get('candidateId') or ''
    names = body.get('names') or []
    method = body.get('method', '系统记录')

    if names:
        results = []
        for name in names:
            note_text = f'【联系记录】HR通过{method}发起联系'
            results.append({'name': name, 'note': note_text})
        return success({'recorded': True, 'count': len(results), 'contacts': results})

    if candidate_id:
        note_text = f'【联系记录】HR通过{method}发起联系'
        update_note(candidate_id, note_text)
        return success({'recorded': True, 'contact': {'id': candidate_id, 'note': note_text}})

    raise AppError('BAD_REQUEST', '缺少 candidateId 或 names 参数')
