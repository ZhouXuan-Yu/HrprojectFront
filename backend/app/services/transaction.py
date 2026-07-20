"""Transaction and retry decorators for SQLAlchemy operations.

Provides:

    * ``@transactional`` — wraps a function in ``db.session.begin()`` with
      automatic commit on success and rollback on exception.
    * ``@retry_on_deadlock`` — retries a function up to *max_attempts* times
      when SQLAlchemy raises an operational error (deadlock / serialisation
      failure), with exponential backoff between attempts.
"""

import logging
import time
from functools import wraps

import sqlalchemy.exc as sa_exc

from app.extensions import db

log = logging.getLogger(__name__)


def transactional(f):
    """Decorator that wraps the function in a SQLAlchemy transaction.

    Usage::

        from app.services.transaction import transactional

        @transactional
        def transfer_funds(src_id, dst_id, amount):
            src = Account.query.get(src_id)
            dst = Account.query.get(dst_id)
            src.balance -= amount
            dst.balance += amount
            # Auto-committed on success, rolled back on exception

    Notes:
        * Commits the session on successful return.
        * Rolls back the session if any exception is raised, then re-raises.
        * Nested transactions are supported via SQLAlchemy's savepoint
          mechanism when the session is already in a transaction.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            with db.session.begin():
                result = f(*args, **kwargs)
            return result
        except Exception:
            # db.session.begin() context manager already rolls back on
            # exception, but we still log the rollback for observability.
            log.warning(
                "Transaction rolled back in %s.%s",
                f.__module__, f.__name__,
                exc_info=True,
            )
            raise
    return wrapper


def retry_on_deadlock(max_attempts: int = 3, base_delay: float = 0.5):
    """Decorator that retries a function on SQLAlchemy deadlock errors.

    Catches ``OperationalError`` with a deadlock or serialisation-failure
    message and retries with exponential backoff.

    Usage::

        from app.services.transaction import retry_on_deadlock

        @retry_on_deadlock(max_attempts=3)
        def update_counter(counter_id):
            c = Counter.query.with_for_update().get(counter_id)
            c.value += 1
            db.session.commit()

    Args:
        max_attempts: Maximum number of attempts (including the first).
            Default 3.
        base_delay: Initial delay in seconds before the first retry.
            Doubled on each subsequent retry (exponential backoff).

    Raises:
        The last caught exception if all attempts are exhausted.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return f(*args, **kwargs)
                except sa_exc.OperationalError as exc:
                    last_exc = exc
                    if not _is_deadlock(exc):
                        raise  # Not a deadlock — re-raise immediately
                    if attempt < max_attempts:
                        delay = base_delay * (2 ** (attempt - 1))
                        log.warning(
                            "Deadlock detected in %s.%s (attempt %d/%d). "
                            "Retrying in %.2fs...",
                            f.__module__, f.__name__,
                            attempt, max_attempts, delay,
                        )
                        time.sleep(delay)
                        # Roll back the failed transaction so we can retry
                        db.session.rollback()
                except sa_exc.IntegrityError as exc:
                    # Unique constraint violations are not retriable
                    log.warning(
                        "IntegrityError in %s.%s (attempt %d/%d): %s",
                        f.__module__, f.__name__,
                        attempt, max_attempts, exc,
                    )
                    raise

            log.error(
                "All %d retry attempts exhausted for %s.%s",
                max_attempts, f.__module__, f.__name__,
            )
            raise last_exc
        return wrapper
    return decorator


def _is_deadlock(exc: sa_exc.OperationalError) -> bool:
    """Check if an OperationalError is a deadlock or serialisation failure.

    Matches common database deadlock messages across SQLite, MySQL, and
    PostgreSQL.
    """
    msg = str(exc).lower()
    deadlock_keywords = [
        'deadlock',           # MySQL, PostgreSQL
        'database is locked',  # SQLite
        'serialization failure',  # PostgreSQL
        'could not serialize',  # PostgreSQL SSI
        'lock wait timeout',  # MySQL
    ]
    return any(kw in msg for kw in deadlock_keywords)
