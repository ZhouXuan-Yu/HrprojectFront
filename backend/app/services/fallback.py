"""Centralised fallback strategy for external service degradation.

When an external service (DeepSeek API, database) is unavailable,
this module provides a unified decision layer that returns cached results,
mock data, or surfaces the error — depending on configuration and context.

Key components:

    * ``FallbackConfig`` — reads strategy from Flask app config.
    * ``FallbackCache`` — in-memory TTL cache of last successful responses.
    * ``get_fallback(service_name, context)`` — unified entry point.
"""

import logging
import time
from threading import Lock
from typing import Any, Optional

from flask import current_app

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# In-memory response cache (per-workflow, TTL 1 hour)
# ---------------------------------------------------------------------------

class FallbackCache:
    """Thin TTL cache for the last successful response per workflow key.

    Each cached entry stores the response dict and an expiry timestamp.
    """

    def __init__(self, default_ttl: int = 3600):
        self._data: dict[str, tuple[Any, float]] = {}
        self._lock = Lock()
        self._default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """Return cached value if still valid, else None."""
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return None
            value, expiry = entry
            if time.time() < expiry:
                return value
            del self._data[key]
            return None

    def set(self, key: str, value: Any, ttl: int = None):
        """Store a value with TTL (default 3600s)."""
        ttl = ttl if ttl is not None else self._default_ttl
        with self._lock:
            self._data[key] = (value, time.time() + ttl)

    def invalidate(self, key: str):
        """Remove a single key from the cache."""
        with self._lock:
            self._data.pop(key, None)

    def clear(self):
        """Clear all cached entries."""
        with self._lock:
            self._data.clear()

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._data)


# ---------------------------------------------------------------------------
# Fallback configuration — reads from Flask config
# ---------------------------------------------------------------------------

class FallbackConfig:
    """Strategy configuration for each external service.

    Reads from ``current_app.config`` with sensible defaults.

    Strategies per service (controlled via config):

        * ``DEEPSEEK_FALLBACK`` — ``'cache'`` | ``'local_ai'`` | ``'error'``
        * ``DB_FALLBACK`` — ``'mock'`` | ``'error'``
    """

    @staticmethod
    def get_strategy(service_name: str) -> str:
        """Return the fallback strategy for *service_name*.

        Args:
            service_name: One of ``'deepseek'``, ``'database'``.

        Returns:
            Strategy string: ``'cache'`` / ``'local_ai'`` / ``'mock'`` / ``'error'``.
        """
        config_key = f'{service_name.upper()}_FALLBACK'.replace('.', '_')
        try:
            return current_app.config.get(config_key, 'error')
        except RuntimeError:
            return 'error'

    @staticmethod
    def mock_fallback_enabled() -> bool:
        """Return True if mock fallback (fake data) is allowed for DB errors."""
        try:
            return current_app.config.get('MOCK_FALLBACK', False)
        except RuntimeError:
            return False


# ---------------------------------------------------------------------------
# Global cache instance
# ---------------------------------------------------------------------------

_cache = FallbackCache(default_ttl=3600)

WORKFLOW_DEEPSEEK_MATCH = 'deepseek:match'
WORKFLOW_DEEPSEEK_RESUME_PARSE = 'deepseek:resume_parse'
WORKFLOW_DEEPSEEK_INTERVIEW_QA = 'deepseek:interview_qa'


# ---------------------------------------------------------------------------
# Unified entry point
# ---------------------------------------------------------------------------

def get_fallback(service_name: str, context: str = None) -> dict:
    """Unified entry point to obtain fallback content.

    Args:
        service_name: Service identifier (``'deepseek'``,
            ``'database'``).
        context: Workflow context key used for cache lookups when the
            strategy is ``'cache'`` (e.g. ``'deepseek:match'``).

    Returns:
        A dict with ``{"ok": True, "data": ..., "fallback": True}`` when a
        cached/mock value is available, or raises ``FallbackNotAvailable``
        when the strategy is ``'error'`` or no fallback is possible.
    """
    strategy = FallbackConfig.get_strategy(service_name)

    if strategy == 'cache':
        if context is None:
            log.warning(
                "Fallback strategy is 'cache' for %s but no context provided",
                service_name,
            )
        else:
            cached = _cache.get(context)
            if cached is not None:
                log.info(
                    "Fallback returning cached result for %s (ctx=%s)",
                    service_name, context,
                )
                return {'ok': True, 'data': cached, 'fallback': True, 'source': 'cache'}
            log.info(
                "Fallback cache miss for %s (ctx=%s), falling through to error",
                service_name, context,
            )

    if strategy == 'mock':
        if FallbackConfig.mock_fallback_enabled():
            log.info("Fallback returning mock data for %s", service_name)
            return {'ok': True, 'data': _get_mock_data(service_name), 'fallback': True, 'source': 'mock'}
        log.info(
            "Fallback strategy is 'mock' for %s but MOCK_FALLBACK is disabled",
            service_name,
        )

    if strategy == 'local_ai':
        # Placeholder: local AI engine would be called here.
        log.info("Fallback local_ai requested for %s (not yet implemented)", service_name)

    raise FallbackNotAvailable(
        f"Service [{service_name}] unavailable and no fallback available "
        f"(strategy={strategy})"
    )


# ---------------------------------------------------------------------------
# Cache write-through
# ---------------------------------------------------------------------------

def cache_success(workflow: str, data: Any, ttl: int = None):
    """Store a successful response for future fallback use.

    Call this after every successful external service call::

        try:
            result = deepseek_client.chat_completion(...)
            cache_success('deepseek:match', result)
            return result
        except Exception:
            return get_fallback('deepseek', 'deepseek:match')
    """
    _cache.set(workflow, data, ttl=ttl)


# ---------------------------------------------------------------------------
# Mock data for development
# ---------------------------------------------------------------------------

_MOCK_DATA: dict = {
    'deepseek': {'choices': [{'message': {'content': '[mock] DeepSeek response'}}]},
    'database': {'rows': [], 'affected': 0},
}


def _get_mock_data(service_name: str) -> Any:
    """Return static mock data for *service_name*."""
    return _MOCK_DATA.get(service_name, {})


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class FallbackNotAvailable(Exception):
    """Raised when no fallback strategy can satisfy the request."""

    def __init__(self, message: str):
        super().__init__(message)
