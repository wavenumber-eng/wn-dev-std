"""Shared audit check result types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CheckResult:
    """Single conformance check result."""

    name: str
    passed: bool
    detail: str
    scope: str = "repo"
    member: str | None = None
    warning: bool = False

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""
        payload: dict[str, object] = {
            "name": self.name,
            "passed": self.passed,
            "detail": self.detail,
            "scope": self.scope,
        }
        if self.member is not None:
            payload["member"] = self.member
        if self.warning:
            payload["level"] = "warning"
        return payload
