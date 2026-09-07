"""Governed command-entrypoint paths for repository profiles."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import cast

from wn_dev_std.check_profiles import ProfileName
from wn_dev_std.checks_types import CheckResult

COMMAND_ROLES = ("build", "test", "signoff")

PROFILE_COMMAND_DEFAULTS: Mapping[ProfileName, Mapping[str, str]] = {
    "csharp-app": {"build": "build.ps1"},
}


def check_command_entrypoints(
    root: Path,
    profile: ProfileName,
    config: Mapping[str, object] | None,
) -> CheckResult | None:
    """Validate configured command paths and profile command defaults."""
    defaults = PROFILE_COMMAND_DEFAULTS.get(profile, {})
    configured, failures = _configured_commands(config)
    if _has_no_command_policy(defaults, configured, failures):
        return None
    if failures:
        return CheckResult("command entrypoints", False, "; ".join(failures))

    resolved_commands = dict(defaults)
    if configured is not None:
        resolved_commands.update(configured)

    path_failures: list[str] = []
    for role, value in sorted(resolved_commands.items()):
        failure = _command_path_failure(root, role, value)
        if failure is not None:
            path_failures.append(failure)
    if path_failures:
        return CheckResult("command entrypoints", False, "; ".join(path_failures))

    details = ", ".join(f"{role}={path}" for role, path in sorted(resolved_commands.items()))
    return CheckResult("command entrypoints", True, f"resolved {details}")


def _has_no_command_policy(
    defaults: Mapping[str, str],
    configured: Mapping[str, str] | None,
    failures: list[str],
) -> bool:
    return not defaults and not configured and not failures


def _configured_commands(
    config: Mapping[str, object] | None,
) -> tuple[dict[str, str] | None, list[str]]:
    if config is None:
        return None, []
    if "commands" not in config:
        return None, []
    value = config.get("commands")
    if not isinstance(value, dict):
        return None, ["commands must be a table"]
    return _parse_configured_commands(cast(Mapping[object, object], value))


def _parse_configured_commands(
    commands: Mapping[object, object],
) -> tuple[dict[str, str], list[str]]:
    failures: list[str] = []
    configured: dict[str, str] = {}
    for raw_role, raw_path in commands.items():
        failure = _configured_command_failure(raw_role, raw_path)
        if failure is not None:
            failures.append(failure)
        elif isinstance(raw_role, str) and isinstance(raw_path, str):
            configured[raw_role] = raw_path
    return configured, failures


def _configured_command_failure(role: object, path: object) -> str | None:
    if not isinstance(role, str) or role not in COMMAND_ROLES:
        return f"commands has unsupported role {role!r}; supported roles: " + ", ".join(
            COMMAND_ROLES
        )
    if not isinstance(path, str) or not path:
        return f"commands.{role} must be a non-empty string path"
    return None


def _command_path_failure(root: Path, role: str, value: str) -> str | None:
    label = f"commands.{role} path {value!r}"
    posix_path = PurePosixPath(value)
    syntax_failure = _command_path_syntax_failure(value, posix_path)
    if syntax_failure == "separators":
        return f"{label} must be a normalized repository-relative path using '/' separators"
    if syntax_failure == "absolute":
        return f"{label} must be relative to the audited repository"
    if syntax_failure == "normalization":
        return f"{label} must be a normalized repository-relative path without '.' or '..'"
    return _resolved_command_path_failure(root, posix_path, label)


def _command_path_syntax_failure(value: str, posix_path: PurePosixPath) -> str | None:
    if value != value.strip() or "\\" in value:
        return "separators"
    if _is_absolute_command_path(value, posix_path):
        return "absolute"
    if _is_non_normalized_command_path(value, posix_path):
        return "normalization"
    return None


def _is_absolute_command_path(value: str, posix_path: PurePosixPath) -> bool:
    windows_path = PureWindowsPath(value)
    return posix_path.is_absolute() or windows_path.is_absolute() or bool(windows_path.drive)


def _is_non_normalized_command_path(value: str, posix_path: PurePosixPath) -> bool:
    return value in {"", "."} or posix_path.as_posix() != value or ".." in posix_path.parts


def _resolved_command_path_failure(
    root: Path,
    posix_path: PurePosixPath,
    label: str,
) -> str | None:
    try:
        resolved_root = root.resolve()
        resolved_path = resolved_root.joinpath(*posix_path.parts).resolve()
    except (OSError, ValueError):
        return f"{label} is not a valid repository-relative filesystem path"
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError:
        return f"{label} resolves outside the audited repository"
    if not resolved_path.exists():
        return f"{label} does not exist"
    if not resolved_path.is_file():
        return f"{label} is not a file"
    return None
