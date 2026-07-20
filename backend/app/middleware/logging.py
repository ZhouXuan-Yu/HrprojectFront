"""Structured request/response logging for Flask.

Logs every request with a unique request ID, method, path, client IP, status
code, and response time.  Sensitive headers (Authorization, Cookie) and the
DeepSeek API key are masked before logging.

Logs are written to both stdout (for dev) and a rotating file (for production)
under the directory configured by ``REQUEST_LOG_DIR``.
"""

import logging
import logging.handlers
import os
import time
import uuid
import re

from flask import g, request

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sensitive-data patterns
# ---------------------------------------------------------------------------

_SENSITIVE_HEADERS = {'authorization', 'cookie', 'x-forwarded-for'}
_DEEPSEEK_API_KEY_PATTERN = re.compile(
    r'(sk-[a-zA-Z0-9]{10,60})',
    re.IGNORECASE,
)
# Also match the env-var / config value when it leaks into log messages
_DEEPSEEK_API_KEY_RAW_PATTERN = re.compile(
    r'(sk-[a-zA-Z0-9]{20,})',
    re.IGNORECASE,
)


def _mask_sensitive(value: str) -> str:
    """Mask sensitive strings like API keys in a log message."""
    return _DEEPSEEK_API_KEY_RAW_PATTERN.sub('sk-****', str(value))


def _redact_headers(headers: dict) -> dict:
    """Return a copy of headers dict with sensitive values masked."""
    return {
        k: ('****' if k.lower() in _SENSITIVE_HEADERS else v)
        for k, v in headers.items()
    }


# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------

_FORMAT = (
    '[%(asctime)s] %(levelname)-8s %(name)s | '
    'req_id=%(req_id)s %(message)s'
)
_DATE_FMT = '%Y-%m-%d %H:%M:%S'


def _configure_handlers(app) -> tuple:
    """Set up stdout and rotating-file handlers for the access logger.

    Returns the access logger instance.
    """
    access_log = logging.getLogger('app.access')
    access_log.setLevel(logging.DEBUG if app.debug else logging.INFO)
    access_log.propagate = False

    # --- Stdout handler (dev-friendly) ---
    stdout_handler = logging.StreamHandler()
    stdout_handler.setLevel(logging.DEBUG)

    # --- Rotating file handler (production) ---
    log_dir = app.config.get('REQUEST_LOG_DIR', os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs',
    ))
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, 'requests.log')

    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8',
    )
    file_handler.setLevel(logging.INFO)

    # --- Formatter ---
    formatter = logging.Formatter(_FORMAT, _DATE_FMT)
    stdout_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    access_log.addHandler(stdout_handler)
    access_log.addHandler(file_handler)

    return access_log, log_dir


# ---------------------------------------------------------------------------
# Flask hooks
# ---------------------------------------------------------------------------

def init_request_logging(app):
    """Register before/after/teardown request hooks.

    Call this from the app factory **after** extensions are initialised.
    """
    access_log, log_dir = _configure_handlers(app)

    @app.before_request
    def log_before_request():
        """Log incoming request details and start the timer."""
        g._request_start_time = time.time()

        # Ensure every request has a request ID
        if not hasattr(g, 'request_id'):
            g.request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))

        headers = _redact_headers(dict(request.headers))
        access_log.info(
            '>>>> %s %s ip=%s headers=%s',
            request.method,
            request.full_path,
            request.remote_addr or 'unknown',
            headers,
            extra={'req_id': g.request_id},
        )

    @app.after_request
    def log_after_request(response):
        """Log response status and elapsed time."""
        elapsed_ms = 0.0
        start = getattr(g, '_request_start_time', None)
        if start:
            elapsed_ms = (time.time() - start) * 1000

        access_log.info(
            '<<<< %s %s status=%s elapsed=%.1fms',
            request.method,
            request.full_path,
            response.status_code,
            elapsed_ms,
            extra={'req_id': g.get('request_id', '-')},
        )
        return response

    @app.teardown_request
    def log_teardown_request(exc=None):
        """Log any unhandled exception that occurred during the request."""
        if exc is not None:
            elapsed_ms = 0.0
            start = getattr(g, '_request_start_time', None)
            if start:
                elapsed_ms = (time.time() - start) * 1000

            access_log.error(
                '!!!! %s %s UNHANDLED_EXCEPTION elapsed=%.1fms exc=%s: %s',
                request.method,
                request.full_path,
                elapsed_ms,
                type(exc).__name__,
                _mask_sensitive(str(exc)[:500]),
                extra={'req_id': g.get('request_id', '-')},
                exc_info=True,
            )

    log.info("Request logging initialised (dir=%s)", log_dir)
