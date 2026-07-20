"""In-memory rate limiter for Flask routes.

Provides a ``@rate_limit()`` decorator that tracks requests per IP address
using an in-memory sliding-window counter.  No external dependency required.

Usage::

    from app.middleware.rate_limit import rate_limit

    @api.route('/search')
    @rate_limit(max_requests=30, window_seconds=60)
    def search():
        ...

Configuration:

    * ``RATE_LIMIT_ENABLED`` (bool, default True) — master kill switch.
    * ``RATE_LIMIT_DEFAULT`` (int, default 60) — default requests per minute
      when the decorator is used without arguments.
"""

import logging
import time
import threading
from collections import defaultdict
from functools import wraps

from flask import request, current_app

from app.utils.response import error

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Per-IP sliding-window store
# ---------------------------------------------------------------------------
# Structure: {client_ip: [(timestamp,), ...]}
# We keep a sorted list of timestamps per IP and prune on each access.

_store: dict[str, list[float]] = defaultdict(list)
_lock = threading.Lock()

_CLEANUP_INTERVAL = 300  # seconds (5 minutes)
_last_cleanup: float = time.time()


def _prune(ip: str, window: float):
    """Remove timestamps older than *window* seconds for *ip*."""
    cutoff = time.time() - window
    with _lock:
        before = len(_store[ip])
        _store[ip] = [t for t in _store[ip] if t > cutoff]
        if not _store[ip]:
            del _store[ip]
        pruned = before - len(_store[ip])
    return pruned


def _periodic_cleanup(interval: int = _CLEANUP_INTERVAL):
    """Background thread that prunes stale entries from the entire store."""
    global _last_cleanup
    while True:
        time.sleep(interval)
        now = time.time()
        cutoff = now - 3600  # prune anything older than 1 hour
        with _lock:
            before = len(_store)
            ips_to_delete = [
                ip for ip, timestamps in list(_store.items())
                if not timestamps or max(timestamps) < cutoff
            ]
            for ip in ips_to_delete:
                del _store[ip]
            after = len(_store)
        log.debug(
            "Rate-limit cleanup: pruned %d stale IPs (%d -> %d entries)",
            before - after, before, after,
        )
        _last_cleanup = now


# ---------------------------------------------------------------------------
# Public decorator
# ---------------------------------------------------------------------------


def rate_limit(max_requests: int = None, window_seconds: int = 60):
    """Decorator that limits requests per client IP.

    Args:
        max_requests: Maximum number of requests allowed in the window.
            Defaults to ``RATE_LIMIT_DEFAULT`` config value (60).
        window_seconds: Length of the sliding window in seconds (default 60).

    Returns:
        429 with ``Retry-After`` header when the limit is exceeded.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # Master kill switch
            app = current_app
            if not app.config.get('RATE_LIMIT_ENABLED', True):
                return f(*args, **kwargs)

            _max_req = max_requests if max_requests is not None else \
                app.config.get('RATE_LIMIT_DEFAULT', 60)
            ip = request.remote_addr or 'unknown'
            now = time.time()

            with _lock:
                # Prune expired entries for this IP
                _store[ip] = [t for t in _store[ip] if t > now - window_seconds]
                count = len(_store[ip])

                if count >= _max_req:
                    retry_after = int(_store[ip][0] + window_seconds - now) + 1
                    resp = error(
                        'RATE_LIMITED',
                        f'请求过于频繁，请 {retry_after} 秒后再试',
                        429,
                    )
                    resp[0].headers['Retry-After'] = str(retry_after)
                    log.warning(
                        "Rate limit exceeded ip=%s path=%s limit=%d/%ds",
                        ip, request.path, _max_req, window_seconds,
                    )
                    return resp

                # Record this request
                _store[ip].append(now)

            return f(*args, **kwargs)
        return wrapper
    return decorator


# ---------------------------------------------------------------------------
# Flask app initialisation
# ---------------------------------------------------------------------------


def init_rate_limiter(app):
    """Register the rate-limiter cleanup thread.

    Call this from the app factory after config is loaded.
    """
    if not app.config.get('RATE_LIMIT_ENABLED', True):
        log.info("Rate limiter disabled via RATE_LIMIT_ENABLED config")
        return

    # Start background cleanup daemon thread
    thread = threading.Thread(
        target=_periodic_cleanup,
        args=(_CLEANUP_INTERVAL,),
        daemon=True,
        name='rate-limiter-cleanup',
    )
    thread.start()
    log.info(
        "Rate limiter initialised (cleanup every %ds, default %d req/min)",
        _CLEANUP_INTERVAL,
        app.config.get('RATE_LIMIT_DEFAULT', 60),
    )
