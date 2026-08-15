"""
KisanAI OS
Rate Limiter

Simple in-memory sliding-window rate limiter (Phase 11 security).

Used for OTP requests and login attempts. Buckets are keyed by
``(namespace, identity)``; events older than the window are pruned on
each check. An identity at its limit is refused with a lockout until old
events age out of the window.

Pure in-memory by design: restarts reset counters, which is acceptable
for login/OTP throttling (the OTP codes themselves also expire in the
database). No PII is retained beyond the short window.
"""

import threading
import time


class RateLimiter:
    """In-memory sliding-window rate limiter."""

    def __init__(self, max_events: int, window_seconds: int):
        self.max_events = max_events
        self.window_seconds = window_seconds
        self._buckets: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def _key(self, namespace: str, identity: str) -> str:
        return f"{namespace}:{identity}"

    def allow(self, namespace: str, identity: str) -> bool:
        """Record one event and return True if still within the limit."""
        now = time.time()
        key = self._key(namespace, identity)
        window_start = now - self.window_seconds

        with self._lock:
            events = self._buckets.setdefault(key, [])
            events[:] = [t for t in events if t >= window_start]

            if len(events) >= self.max_events:
                return False

            events.append(now)
            return True

    def remaining(self, namespace: str, identity: str) -> int:
        """Number of events still allowed for the identity."""
        now = time.time()
        key = self._key(namespace, identity)
        window_start = now - self.window_seconds

        with self._lock:
            events = self._buckets.setdefault(key, [])
            events[:] = [t for t in events if t >= window_start]
            return max(0, self.max_events - len(events))

    def reset(self, namespace: str, identity: str) -> None:
        """Clear recorded events for an identity (e.g. after success)."""
        with self._lock:
            self._buckets.pop(self._key(namespace, identity), None)
