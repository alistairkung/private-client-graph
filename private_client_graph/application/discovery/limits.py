"""Account for every attempted request and bounded response in a discovery session."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Limits:
    action_requests: int = 40
    session_requests: int = 160
    action_bytes: int = 12 * 1024 * 1024
    session_bytes: int = 32 * 1024 * 1024

    def __post_init__(self) -> None:
        if min(self.action_requests, self.session_requests, self.action_bytes, self.session_bytes) <= 0:
            raise ValueError("Discovery limits must be positive")


@dataclass
class Usage:
    requests: int = 0
    bytes: int = 0


class LimitReached(Exception):
    pass


class Action:
    def __init__(self, limits: Limits, session: Usage):
        self.limits = limits
        self.session = session
        self.used = Usage()

    def request(self) -> None:
        if self.session.requests >= self.limits.session_requests:
            raise LimitReached("Session request limit")
        if self.used.requests >= self.limits.action_requests:
            raise LimitReached("Action request limit")
        self.consume(0)
        self.session.requests += 1
        self.used.requests += 1

    def consume(self, size: int) -> None:
        session_left = self.limits.session_bytes - self.session.bytes
        action_left = self.limits.action_bytes - self.used.bytes
        admitted = min(size, session_left, action_left)
        self.session.bytes += admitted
        self.used.bytes += admitted
        if not session_left or size > session_left:
            raise LimitReached("Session byte limit")
        if not action_left or size > action_left:
            raise LimitReached("Action byte limit")
