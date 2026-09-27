"""Contained project-path validation shared by opt-in policies."""

from __future__ import annotations

from pathlib import Path


def declared_path(
    root: Path,
    value: object,
    label: str,
    failures: list[str],
    *,
    directory: bool = False,
) -> Path | None:
    """Resolve a declared project path and report containment or kind failures."""
    candidate = _relative_candidate(value, label, failures)
    if candidate is None:
        return None
    resolved = (root / candidate).resolve()
    if not is_within(root, resolved):
        failures.append(f"{label} resolves outside the project root")
        return None
    return _existing_path(resolved, candidate, label, failures, directory)


def is_within(root: Path, path: Path) -> bool:
    """Return whether a resolved path is contained by a root."""
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _relative_candidate(value: object, label: str, failures: list[str]) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        failures.append(f"{label} must be a non-empty relative path")
        return None
    candidate = Path(value.strip())
    if candidate.is_absolute() or ".." in candidate.parts:
        failures.append(f"{label} must stay inside the project root")
        return None
    return candidate


def _existing_path(
    resolved: Path,
    candidate: Path,
    label: str,
    failures: list[str],
    directory: bool,
) -> Path | None:
    if not resolved.exists():
        failures.append(f"{label} does not exist: {candidate.as_posix()}")
        return None
    expected_kind = resolved.is_dir() if directory else resolved.is_file()
    if expected_kind:
        return resolved
    kind = "directory" if directory else "file"
    failures.append(f"{label} must be a {kind}: {candidate.as_posix()}")
    return None
