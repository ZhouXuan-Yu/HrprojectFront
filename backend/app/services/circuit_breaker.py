"""Circuit breaker for external service calls.

Pattern::

    CLOSED  ──(5 consecutive failures)──►  OPEN
       ▲                                      │
       │            ┌──────────────────────────┘
       │            │  (30s timeout)
       │            ▼
       └──(1 success)── HALF_OPEN ──(1 failure)──►  OPEN

Protects against cascading failures when external services (DeepSeek)
are unavailable.  Each service should have its own ``CircuitBreaker`` instance.
"""

import logging
import time
from enum import Enum
from functools import wraps
from typing import Callable, Optional

log = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = 'CLOSED'
    OPEN = 'OPEN'
    HALF_OPEN = 'HALF_OPEN'


class CircuitBreaker:
    """State machine that protects calls to an external service.

    Usage::

        cb = CircuitBreaker(name='deepseek', threshold=5, timeout=30)

        @cb.wrap
        def call_deepseek():
            ...

        # Or call manually:
        if cb.allow_request():
            try:
                result = deepseek_api(...)
                cb.on_success()
                return result
            except Exception as e:
                cb.on_failure()
                raise
    """

    def __init__(
        self,
        name: str,
        threshold: int = 5,
        timeout: float = 30.0,
    ):
        """
        Args:
            name: Human-readable service name (used in logs).
            threshold: Consecutive failures before opening the circuit.
            timeout: Seconds to stay OPEN before transitioning to HALF_OPEN.
        """
        self.name = name
        self.threshold = threshold
        self.timeout = timeout

        self.state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._last_state_change: float = time.time()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def allow_request(self) -> bool:
        """Check whether a request to the external service is permitted.

        Returns:
            True if the request should proceed, False to fast-fail.
        """
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if the timeout has elapsed
            if time.time() - self._last_state_change >= self.timeout:
                self._transition_to(CircuitState.HALF_OPEN)
                log.info(
                    "Circuit %s -> HALF_OPEN after %.1fs timeout (probing)",
                    self.name, self.timeout,
                )
                return True
            return False

        # HALF_OPEN: allow exactly one probe
        return True

    def on_success(self):
        """Record a successful call.

        - CLOSED: reset failure count.
        - HALF_OPEN: close the circuit (full recovery).
        """
        if self.state == CircuitState.HALF_OPEN:
            self._transition_to(CircuitState.CLOSED)
            log.info(
                "Circuit %s recovered: HALF_OPEN -> CLOSED (probe succeeded)",
                self.name,
            )

        self._failure_count = 0

    def on_failure(self):
        """Record a failed call.

        - CLOSED: increment failure count; open if threshold reached.
        - HALF_OPEN: probe failed, back to OPEN.
        """
        self._failure_count += 1
        self._last_failure_time = time.time()

        if self.state == CircuitState.CLOSED:
            if self._failure_count >= self.threshold:
                self._transition_to(CircuitState.OPEN)
                log.warning(
                    "Circuit %s OPEN after %d consecutive failures",
                    self.name, self._failure_count,
                )

        elif self.state == CircuitState.HALF_OPEN:
            self._transition_to(CircuitState.OPEN)
            log.warning(
                "Circuit %s HALF_OPEN probe failed -> OPEN (backoff another %.1fs)",
                self.name, self.timeout,
            )

    def wrap(self, func: Callable):
        """Decorator that applies the circuit breaker to *func*.

        The decorated function will raise ``CircuitBreakerOpenError``
        when the circuit is OPEN and rejecting requests.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not self.allow_request():
                raise CircuitBreakerOpenError(
                    f"Circuit [{self.name}] is OPEN — rejecting request. "
                    f"Retry after {self._retry_after():.0f}s"
                )
            try:
                result = func(*args, **kwargs)
                self.on_success()
                return result
            except CircuitBreakerOpenError:
                # Don't count fast-fail as a real service failure
                raise
            except Exception as e:
                self.on_failure()
                raise
        return wrapper

    def reset(self):
        """Force the circuit back to CLOSED (e.g. after manual intervention)."""
        self._transition_to(CircuitState.CLOSED)
        self._failure_count = 0
        log.info("Circuit %s manually reset to CLOSED", self.name)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _transition_to(self, new_state: CircuitState):
        self.state = new_state
        self._last_state_change = time.time()

    def _retry_after(self) -> float:
        """Seconds remaining before the circuit transitions to HALF_OPEN."""
        if self.state != CircuitState.OPEN:
            return 0.0
        elapsed = time.time() - self._last_state_change
        return max(0.0, self.timeout - elapsed)

    @property
    def stats(self) -> dict:
        """Return current breaker statistics for monitoring/health checks."""
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self._failure_count,
            'threshold': self.threshold,
            'timeout': self.timeout,
            'retry_after': self._retry_after(),
        }

    def __repr__(self) -> str:
        return (
            f"<CircuitBreaker {self.name} "
            f"state={self.state.value} "
            f"failures={self._failure_count}/{self.threshold}>"
        )


class CircuitBreakerOpenError(Exception):
    """Raised when a circuit breaker rejects a request."""

    def __init__(self, message: str):
        super().__init__(message)
