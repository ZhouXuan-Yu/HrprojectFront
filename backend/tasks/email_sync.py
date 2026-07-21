"""Email sync task: IMAP mailbox polling + resume parsing.

Wraps app.services.email_sync_service (real IMAP pipeline:
pull unread → detect resume → extract text → DeepSeek parse → ingest).
"""
import logging
from tasks.celery_app import celery_app

log = logging.getLogger(__name__)


@celery_app.task(name='tasks.email_sync.sync_all_mailboxes')
def sync_all_mailboxes():
    """Periodic task: sync all active mail accounts that are due.

    Celery Beat fires this every 15 minutes; each account is only synced
    when its own sync_freq（分钟）has elapsed since last_sync_time —
    so "每 2 小时"/"每天" 等频率由单个 beat tick 统一覆盖。

    Returns a summary dict with per-account details.
    """
    try:
        from app.services.email_sync_service import sync_all_accounts
    except ImportError as exc:
        log.error("Failed to import email sync service: %s", exc)
        return {
            'status': 'error', 'error': f'Import failed: {exc}',
            'accounts_checked': 0, 'new_emails': 0,
            'resumes_detected': 0, 'candidates_created': 0, 'details': [],
        }

    summary = sync_all_accounts(respect_freq=True)
    # Keep legacy field names for downstream consumers
    summary['resumes_detected'] = summary.get('resumes_ingested', 0)
    summary['candidates_created'] = summary.get('resumes_ingested', 0)
    log.info(
        "Email sync complete: %d accounts, %d new emails, %d resumes ingested",
        summary['accounts_checked'], summary['new_emails'],
        summary['resumes_ingested'],
    )
    return summary


@celery_app.task(name='tasks.email_sync.sync_single_mailbox')
def sync_single_mailbox(account_id):
    """Manually trigger sync for a single mail account by its primary key ID."""
    try:
        from app.services.email_sync_service import sync_mail_account
    except ImportError as exc:
        log.error("Failed to import email sync service: %s", exc)
        return {'status': 'error', 'error': f'Import failed: {exc}', 'account_id': account_id}

    return sync_mail_account(account_id)
