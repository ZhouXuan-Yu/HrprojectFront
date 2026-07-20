"""Interview API: /api/interview/*"""
from flask import Blueprint, request, g
from app.utils.response import success, success_list, error, AppError

bp = Blueprint('interview', __name__)


@bp.route('/list')
def get_list():
    """GET /api/interview/list — paginated interview list."""
    from app.services.interview_service import list_interviews
    data, total = list_interviews(request.args)
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', 20))
    return success_list(data, total, page, page_size)


@bp.route('/alerts')
def get_alerts():
    """GET /api/interview/alerts — interview alerts."""
    from app.services.interview_service import get_alerts
    data = get_alerts()
    return success(data)


@bp.route('/create', methods=['POST'])
def create():
    """POST /api/interview/create — create interview booking."""
    from app.services.interview_service import create_interview
    result = create_interview(request.get_json(silent=True) or {})
    return success(result)


@bp.route('/schedule', methods=['POST'])
def schedule():
    """POST /api/interview/schedule — schedule interview (batch)."""
    from app.services.interview_service import schedule_interview
    result = schedule_interview(request.get_json(silent=True) or {})
    return success(result)


@bp.route('/<interview_id>/evaluate', methods=['POST'])
def evaluate(interview_id):
    """POST /api/interview/{id}/evaluate — submit evaluation."""
    from app.services.interview_service import evaluate_interview
    result = evaluate_interview(interview_id, request.get_json(silent=True) or {})
    return success(result)


@bp.route('/<int:book_id>')
def get_detail(book_id):
    """GET /api/interview/{id} — single interview detail."""
    from app.services.interview_service import get_interview
    data = get_interview(book_id)
    return success(data)


@bp.route('/<int:book_id>', methods=['DELETE'])
def cancel(book_id):
    """DELETE /api/interview/{id} — cancel interview with reason."""
    from app.services.interview_service import cancel_interview
    body = request.get_json(silent=True) or {}
    result = cancel_interview(book_id, reason=body.get('reason', ''))
    return success(result)


@bp.route('/<int:book_id>/complete', methods=['POST'])
def complete(book_id):
    """POST /api/interview/{id}/complete — mark interview as completed (scheduled -> evaluating)."""
    from app.services.interview_service import complete_interview
    result = complete_interview(book_id, request.get_json(silent=True) or {})
    return success(result)


@bp.route('/<int:book_id>/offer', methods=['POST'])
def send_offer(book_id):
    """POST /api/interview/{id}/offer — send offer after evaluation passed."""
    from app.services.interview_service import send_offer
    result = send_offer(book_id, request.get_json(silent=True) or {})
    return success(result)


@bp.route('/<int:book_id>/onboard', methods=['POST'])
def confirm_onboard(book_id):
    """POST /api/interview/{id}/onboard — confirm candidate onboard."""
    from app.services.interview_service import confirm_onboard
    result = confirm_onboard(book_id)
    return success(result)


@bp.route('/calendar')
def get_calendar():
    """GET /api/interview/calendar — calendar view with week_start query param."""
    from app.services.interview_service import get_calendar
    week_start = request.args.get('week_start')
    data = get_calendar(week_start)
    return success(data)
