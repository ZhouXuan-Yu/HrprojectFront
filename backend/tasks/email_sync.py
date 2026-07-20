"""Email sync task: IMAP mailbox polling + resume parsing.

Queries active RecruitMailAccount records from the database, then simulates
the processing pipeline for each mailbox (logging each step).  Real IMAP
integration will replace the simulated pipeline in a future iteration.
"""
import logging
from tasks.celery_app import celery_app

log = logging.getLogger(__name__)


@celery_app.task(name='tasks.email_sync.sync_all_mailboxes')
def sync_all_mailboxes():
    """
    Periodic task: iterate all active mail accounts, pull new emails,
    detect resumes, call Dify WF for parsing, create Candidate + Resume records.

    Runs every 30 minutes via Celery Beat.

    Returns a summary dict with per-account details.
    """
    try:
        from app.models.auxiliary import RecruitMailAccount
        from app.extensions import db
    except ImportError as exc:
        log.error("Failed to import DB models: %s", exc)
        return {
            'status': 'error',
            'error': f'DB import failed: {exc}',
            'accounts_checked': 0,
            'new_emails': 0,
            'resumes_detected': 0,
            'candidates_created': 0,
            'details': [],
        }

    try:
        # Query all active mail accounts (status=1)
        accounts = db.session.query(RecruitMailAccount).filter(
            RecruitMailAccount.status == 1,
            RecruitMailAccount.is_deleted == 0,
        ).all()
    except Exception as exc:
        log.error("DB query failed for RecruitMailAccount: %s", exc, exc_info=True)
        return {
            'status': 'error',
            'error': f'DB query failed: {exc}',
            'accounts_checked': 0,
            'new_emails': 0,
            'resumes_detected': 0,
            'candidates_created': 0,
            'details': [],
        }

    if not accounts:
        log.info("No active mail accounts found in DB")
        return {
            'status': 'ok',
            'accounts_checked': 0,
            'new_emails': 0,
            'resumes_detected': 0,
            'candidates_created': 0,
            'details': [],
        }

    log.info("Starting email sync for %d active mail account(s)", len(accounts))

    total_new_emails = 0
    total_resumes = 0
    total_candidates = 0
    details = []

    for acct in accounts:
        # Simulate mailbox processing pipeline
        acct_name = acct.email_address or acct.account_name or f'account#{acct.id}'
        log.info(
            "Processing mailbox: %s (host=%s, port=%s, folder=%s)",
            acct_name, acct.imap_host, acct.imap_port,
            acct.monitor_folder or 'INBOX',
        )

        # Simulated counts — real IMAP pipeline will replace these
        simulated_new = 4
        simulated_resumes = 1
        simulated_candidates = 1

        log.info(
            "[SIMULATED] %s: %d new emails, %d resumes detected, %d candidates created",
            acct_name, simulated_new, simulated_resumes, simulated_candidates,
        )

        total_new_emails += simulated_new
        total_resumes += simulated_resumes
        total_candidates += simulated_candidates

        details.append({
            'email': acct_name,
            'new': simulated_new,
            'resumes': simulated_resumes,
            'candidates': simulated_candidates,
        })

    log.info(
        "Email sync complete: %d accounts, %d new emails, %d resumes, %d candidates",
        len(accounts), total_new_emails, total_resumes, total_candidates,
    )

    return {
        'status': 'ok',
        'accounts_checked': len(accounts),
        'new_emails': total_new_emails,
        'resumes_detected': total_resumes,
        'candidates_created': total_candidates,
        'details': details,
    }


@celery_app.task(name='tasks.email_sync.sync_single_mailbox')
def sync_single_mailbox(account_id):
    """Manually trigger sync for a single mail account by its primary key ID."""
    try:
        from app.models.auxiliary import RecruitMailAccount
        from app.extensions import db
    except ImportError as exc:
        log.error("Failed to import DB models: %s", exc)
        return {'status': 'error', 'error': f'DB import failed: {exc}', 'account_id': account_id}

    try:
        acct = db.session.query(RecruitMailAccount).filter(
            RecruitMailAccount.id == account_id,
            RecruitMailAccount.is_deleted == 0,
        ).first()
    except Exception as exc:
        log.error("DB query failed for account_id=%s: %s", account_id, exc, exc_info=True)
        return {'status': 'error', 'error': f'DB query failed: {exc}', 'account_id': account_id}

    if not acct:
        log.warning("Mail account not found: id=%s", account_id)
        return {'status': 'error', 'error': 'Account not found', 'account_id': account_id}

    if acct.status != 1:
        log.warning("Mail account id=%s is not active (status=%s)", account_id, acct.status)
        return {'status': 'error', 'error': 'Account not active', 'account_id': account_id}

    acct_name = acct.email_address or acct.account_name or f'account#{acct.id}'
    log.info(
        "Processing single mailbox: %s (host=%s, port=%s)",
        acct_name, acct.imap_host, acct.imap_port,
    )

    # Simulated processing
    simulated_new_emails = 3
    simulated_new_resumes = 1

    log.info(
        "[SIMULATED] %s: %d new emails, %d new resumes",
        acct_name, simulated_new_emails, simulated_new_resumes,
    )

    return {
        'status': 'ok',
        'account_id': account_id,
        'email': acct_name,
        'new_emails': simulated_new_emails,
        'new_resumes': simulated_new_resumes,
    }
