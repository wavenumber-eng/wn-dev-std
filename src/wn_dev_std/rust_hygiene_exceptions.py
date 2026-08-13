"""Validation helpers for reviewed Rust structural-hygiene exceptions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence, Set


def exception_shape_failures(
    exceptions: Sequence[Mapping[str, object]],
    known_rules: Set[str],
) -> list[str]:
    """Return exception inventory shape, identity, and bound failures."""
    failures: list[str] = []
    ids: set[str] = set()
    scopes: set[tuple[str | None, str | None, str | None]] = set()
    for index, exception in enumerate(exceptions, start=1):
        failures.extend(_entry_failures(exception, index, known_rules, ids, scopes))
    return failures


def _entry_failures(
    exception: Mapping[str, object],
    index: int,
    known_rules: Set[str],
    ids: set[str],
    scopes: set[tuple[str | None, str | None, str | None]],
) -> list[str]:
    label = f"exceptions[{index}]"
    required = ("id", "path", "item", "rule", "reason", "review_trigger")
    failures = [
        f"{label}.{key} is required" for key in required if _string(exception.get(key)) is None
    ]
    max_value = exception.get("max_value")
    if type(max_value) is not int or max_value <= 0:
        failures.append(f"{label}.max_value must be a positive integer")
    exception_id = _string(exception.get("id"))
    if exception_id in ids:
        failures.append(f"{label}.id {exception_id!r} is duplicated")
    if exception_id is not None:
        ids.add(exception_id)
    rule = _string(exception.get("rule"))
    if rule is not None and rule not in known_rules:
        failures.append(f"{label}.rule {rule!r} is unknown")
    scope = (_string(exception.get("path")), _string(exception.get("item")), rule)
    if scope in scopes:
        failures.append(f"{label} duplicates exception scope {scope}")
    scopes.add(scope)
    return failures


def _string(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None
