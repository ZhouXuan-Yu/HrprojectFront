"""Batch matching task: triggered after demand approval.

Calls the real match_service.batch_match_demand() to score candidates against
a demand, and provides a batch-all-active function that iterates over all
open demands in the database.
"""
import logging
from tasks.celery_app import celery_app

log = logging.getLogger(__name__)


@celery_app.task(name='tasks.match_batch.batch_match_demand')
def batch_match_demand(demand_id):
    """
    Match all candidates against a demand, write match records,
    and return the top-N results.

    Delegates to app.services.match_service.batch_match_demand() which
    handles DB reads for candidate data and scoring internally.
    """
    try:
        from app.services.match_service import batch_match_demand as run_match
    except ImportError as exc:
        log.error("Failed to import match_service: %s", exc)
        return {
            'status': 'error',
            'error': f'match_service import failed: {exc}',
            'demand_id': demand_id,
            'candidates_matched': 0,
            'top5': [],
        }

    try:
        log.info("Starting batch match for demand %s ...", demand_id)
        result = run_match(demand_id)
        log.info(
            "Batch match complete for demand %s: %d candidates matched",
            demand_id, result.get('totalMatched', 0),
        )
        return {
            'status': 'ok',
            'demand_id': demand_id,
            'candidates_matched': result.get('totalMatched', 0),
            'top5': result.get('candidates', [])[:5],
            'result': result,
        }
    except Exception as exc:
        log.exception("Batch match failed for demand %s: %s", demand_id, exc)
        return {
            'status': 'error',
            'error': str(exc),
            'demand_id': demand_id,
            'candidates_matched': 0,
        }


@celery_app.task(name='tasks.match_batch.batch_match_all_active')
def batch_match_all_active():
    """
    Match all open (demand_status=2) demands against available candidates.

    Queries RecruitDemand for open records, then calls batch_match_demand
    for each one.  Aggregates results into a summary.
    """
    try:
        from app.models.demand import RecruitDemand
        from app.extensions import db
    except ImportError as exc:
        log.error("Failed to import DB models: %s", exc)
        return {
            'status': 'error',
            'error': f'DB import failed: {exc}',
            'demands_processed': 0,
            'total_matches': 0,
        }

    try:
        open_demands = db.session.query(RecruitDemand).filter(
            RecruitDemand.demand_status == 2,
            RecruitDemand.is_deleted == 0,
        ).all()
    except Exception as exc:
        log.error("DB query failed for active demands: %s", exc, exc_info=True)
        return {
            'status': 'error',
            'error': f'DB query failed: {exc}',
            'demands_processed': 0,
            'total_matches': 0,
        }

    if not open_demands:
        log.info("No open demands found for batch matching")
        return {
            'status': 'ok',
            'demands_processed': 0,
            'total_matches': 0,
            'details': [],
        }

    log.info("Batch matching %d open demand(s) ...", len(open_demands))

    total_matches = 0
    details = []

    for demand in open_demands:
        demand_no = demand.demand_no or str(demand.id)
        log.info("Processing demand %s ...", demand_no)

        task_result = batch_match_demand(demand_no)

        if task_result.get('status') == 'ok':
            count = task_result.get('candidates_matched', 0)
            total_matches += count
            details.append({
                'demand_id': demand_no,
                'candidates_matched': count,
                'top3': task_result.get('top5', [])[:3],
            })
        else:
            details.append({
                'demand_id': demand_no,
                'error': task_result.get('error', 'unknown'),
            })

    log.info(
        "Batch match all complete: %d demands processed, %d total matches",
        len(open_demands), total_matches,
    )

    return {
        'status': 'ok',
        'demands_processed': len(open_demands),
        'total_matches': total_matches,
        'details': details,
    }
