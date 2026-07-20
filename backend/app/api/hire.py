"""Hire API: /api/hire/* — Offer and Entry management."""
from flask import Blueprint, request, g
from app.utils.response import success, error, AppError

bp = Blueprint('hire', __name__)


@bp.route('/offer/create', methods=['POST'])
def create_offer():
    """POST /api/hire/offer/create — create a new offer."""
    from app.services.hire_service import create_offer
    result = create_offer(request.get_json(silent=True) or {})
    return success(result)


@bp.route('/offer/<offer_id>')
def get_offer(offer_id):
    """GET /api/hire/offer/{id} — get offer detail."""
    from app.services.hire_service import get_offer
    data = get_offer(offer_id)
    return success(data)


@bp.route('/offer/<offer_id>/status', methods=['PATCH'])
def update_offer_status(offer_id):
    """PATCH /api/hire/offer/{id}/status — update offer status."""
    from app.services.hire_service import update_offer_status
    result = update_offer_status(offer_id, request.get_json(silent=True) or {})
    return success(result)


@bp.route('/entry/create', methods=['POST'])
def create_entry():
    """POST /api/hire/entry/create — create entry record."""
    from app.services.hire_service import create_entry
    result = create_entry(request.get_json(silent=True) or {})
    return success(result)


@bp.route('/entry/<entry_id>')
def get_entry(entry_id):
    """GET /api/hire/entry/{id} — get entry detail."""
    from app.services.hire_service import get_entry
    data = get_entry(entry_id)
    return success(data)


@bp.route('/offers')
def list_offers():
    """GET /api/hire/offers — list all offers with pagination."""
    from app.services.hire_service import list_offers
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 20, type=int)
    result = list_offers(page=page, page_size=page_size)
    return success(result)


@bp.route('/entries')
def list_entries():
    """GET /api/hire/entries — list all entries with pagination."""
    from app.services.hire_service import list_entries
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pageSize', 20, type=int)
    result = list_entries(page=page, page_size=page_size)
    return success(result)


# ── New endpoints for Task 3 / Task 7 ──

@bp.route('/offer/<offer_id>/send', methods=['POST'])
def send_offer(offer_id):
    """POST /api/hire/offer/{id}/send — send offer to candidate (draft -> sent)."""
    from app.services.hire_service import send_offer
    result = send_offer(offer_id)
    return success(result)


@bp.route('/offer/<offer_id>/accept', methods=['POST'])
def accept_offer(offer_id):
    """POST /api/hire/offer/{id}/accept — accept offer (sent -> accepted)."""
    from app.services.hire_service import accept_offer
    result = accept_offer(offer_id)
    return success(result)


@bp.route('/offer/<offer_id>/reject', methods=['POST'])
def reject_offer(offer_id):
    """POST /api/hire/offer/{id}/reject — reject offer with reason (sent -> rejected)."""
    from app.services.hire_service import reject_offer
    body = request.get_json(silent=True) or {}
    result = reject_offer(offer_id, reason=body.get('reason', ''))
    return success(result)


@bp.route('/offer/<offer_id>', methods=['DELETE'])
def withdraw_offer(offer_id):
    """DELETE /api/hire/offer/{id} — withdraw/recall an offer."""
    from app.services.hire_service import withdraw_offer
    body = request.get_json(silent=True) or {}
    result = withdraw_offer(offer_id, reason=body.get('reason', ''))
    return success(result)


@bp.route('/offers/expire', methods=['POST'])
def expire_offers():
    """POST /api/hire/offers/expire — expire all sent offers older than 14 days."""
    from app.services.hire_service import expire_offers
    result = expire_offers()
    return success(result)
