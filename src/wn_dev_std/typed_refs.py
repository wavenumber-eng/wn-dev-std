"""Shared typed reference validation helpers."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

LOCAL_REF_KINDS = {"local_file", "local_pytest", "fixture_file"}
LOGICAL_REF_KINDS = {
    "fixture_case",
    "fixture_set",
    "synthetic_vector",
    "oracle_artifact",
    "rack_evidence",
}
EXTERNAL_REF_KINDS = {
    "external_source",
    "external_test",
    "external_pytest",
    "external_cpp_test",
}


def validate_typed_ref(
    root: Path,
    label: str,
    ref: Mapping[str, object],
    failures: list[str],
) -> None:
    """Validate a shared typed evidence reference."""
    kind = required_string(ref, "kind", label, failures)
    target = required_string(ref, "target", label, failures)
    required_string(ref, "coverage_mode", label, failures)
    required_string(ref, "rationale", label, failures)
    if kind in LOCAL_REF_KINDS:
        validate_local_typed_ref(root, label, kind, target, failures)
    elif kind in LOGICAL_REF_KINDS:
        return
    elif kind in EXTERNAL_REF_KINDS:
        validate_external_typed_ref(label, ref, failures)
    elif kind:
        failures.append(f"{label}: unknown kind {kind!r}")


def validate_local_path_ref(
    root: Path,
    label: str,
    target: str,
    failures: list[str],
) -> None:
    """Validate a local path-style reference stays under the repository root."""
    if not target:
        return
    path_text = target.replace("\\", "/").split("#", 1)[0].split("?", 1)[0]
    path = (root / path_text).resolve()
    if not is_within_root(root, path):
        failures.append(f"{label}: local target escapes repository root {target!r}")
        return
    if not path.exists():
        failures.append(f"{label}: missing local target {target!r}")


def validate_local_typed_ref(
    root: Path,
    label: str,
    kind: str,
    target: str,
    failures: list[str],
) -> None:
    """Validate a typed local target."""
    if not target:
        return
    path_text = target.split("::", 1)[0]
    path = (root / path_text).resolve()
    if not is_within_root(root, path):
        failures.append(f"{label}: local target escapes repository root {target!r}")
        return
    if not path.exists():
        failures.append(f"{label}: missing local target {target!r}")
    if kind == "local_pytest" and "::" not in target:
        failures.append(f"{label}: local_pytest target should include :: test selector")


def validate_external_typed_ref(
    label: str,
    ref: Mapping[str, object],
    failures: list[str],
) -> None:
    """Validate a typed external target."""
    if not string_value(ref.get("repo")):
        failures.append(f"{label}: external refs require repo")


def required_string(
    metadata: Mapping[str, object],
    key: str,
    label: str,
    failures: list[str],
) -> str:
    """Return a required non-empty string field or record a failure."""
    value = string_value(metadata.get(key))
    if value:
        return value
    failures.append(f"{label}: missing {key}")
    return ""


def string_value(value: object) -> str:
    """Return a stripped string value."""
    return value.strip() if isinstance(value, str) else ""


def is_within_root(root: Path, target: Path) -> bool:
    """Return whether target is within root."""
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return False
    return True
