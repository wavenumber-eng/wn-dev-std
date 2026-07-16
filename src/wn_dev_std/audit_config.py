"""Audit configuration validation and workspace helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from wn_dev_std.checks_types import CheckResult
from wn_dev_std.root_discovery import standard_config_path
from wn_dev_std.standards import STANDARD_VERSION

AUDIT_SCOPES = (
    "all",
    "repo",
    "docs",
    "docs.adrs",
    "docs.artifacts",
    "docs.build",
    "docs.cli",
    "docs.design",
    "docs.domains",
    "docs.links",
    "docs.plans",
    "docs.release",
    "docs.requirements",
    "docs.surfaces",
    "docs.test_strategy",
    "docs.traceability",
    "docs.vendors",
    "tests",
    "language",
    "ci",
    "compat",
)


def standard_config_checks(
    root: Path,
    config: Mapping[str, object] | None,
) -> tuple[CheckResult, ...]:
    """Validate config shape and standard-version alignment."""
    marker_path = standard_config_path(root)
    if marker_path is None:
        return ()

    failures = _version_failures(root, marker_path, config)
    failures.extend(_kind_failures(root, marker_path, config))
    failures.extend(_enabled_scope_failures(root, marker_path, config))

    if failures:
        return (CheckResult("standard config", False, "; ".join(failures), "repo"),)

    detail = f"{_rel(root, marker_path)} targets standard_version {STANDARD_VERSION}"
    configured_scopes = configured_enabled_scopes(config)
    if configured_scopes is not None:
        detail += "; configured scopes: " + ", ".join(configured_scopes)
    return (CheckResult("standard config", True, detail, "repo"),)


def effective_scopes(
    scopes: Sequence[str] | None,
    config: Mapping[str, object] | None,
) -> tuple[str, ...]:
    """Return requested scopes, honoring configured defaults when no scopes were passed."""
    if scopes is not None:
        return normalize_scopes(scopes)
    configured = configured_enabled_scopes(config)
    if configured is not None:
        return configured
    return ("all",)


def normalize_scopes(scopes: Sequence[str]) -> tuple[str, ...]:
    """Normalize user-provided audit scopes."""
    selected = tuple(scope for scope in scopes if scope in AUDIT_SCOPES)
    if not selected:
        return ("all",)
    if "all" in selected:
        return ("all",)
    return selected


def scope_is_selected(scope: str, selected: Sequence[str]) -> bool:
    """Return whether a check scope is selected by requested audit scopes."""
    if "all" in selected:
        return True
    return any(scope == item or scope.startswith(f"{item}.") for item in selected)


def configured_enabled_scopes(config: Mapping[str, object] | None) -> tuple[str, ...] | None:
    """Return configured default audit scopes, if valid."""
    if config is None:
        return None
    value = config.get("enabled_scopes")
    if not isinstance(value, list):
        return None
    scopes: list[str] = []
    for item in cast(list[object], value):
        if isinstance(item, str) and item in AUDIT_SCOPES:
            scopes.append(item)
    if not scopes:
        return None
    return normalize_scopes(tuple(scopes))


def config_kind(config: Mapping[str, object] | None) -> str:
    """Return the configured audit boundary kind."""
    kind = string_config_value(config, "kind")
    if kind is None:
        return "package"
    return kind


def string_config_value(config: Mapping[str, object] | None, key: str) -> str | None:
    """Return a non-empty string config value."""
    if config is None:
        return None
    value = config.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def workspace_members(config: Mapping[str, object] | None) -> tuple[str, ...]:
    """Return configured workspace members."""
    if config is None:
        return ()
    workspace = config.get("workspace")
    if not isinstance(workspace, dict):
        return ()
    members = cast(Mapping[str, object], workspace).get("members")
    if not isinstance(members, list):
        return ()
    values: list[str] = []
    for member in cast(list[object], members):
        if isinstance(member, str) and member.strip():
            values.append(member.strip())
    return tuple(values)


def validated_member_path(root: Path, member: str) -> Path | str:
    """Return a resolved workspace member path or a validation failure detail."""
    raw_path = Path(member)
    member_key = member.replace("\\", "/").strip("/")
    if raw_path.is_absolute():
        return f"workspace member {member_key!r} must be a relative path"
    if ".." in raw_path.parts:
        return f"workspace member {member_key!r} must not contain '..'"
    resolved = (root / raw_path).resolve()
    if not _is_within_root(root, resolved):
        return f"workspace member {member_key!r} resolves outside the workspace root"
    if not resolved.exists():
        return f"workspace member {member_key!r} does not exist"
    if not resolved.is_dir():
        return f"workspace member {member_key!r} is not a directory"
    return resolved


def with_member(results: Sequence[CheckResult], member: str) -> tuple[CheckResult, ...]:
    """Attach a workspace member id to audit results."""
    return tuple(
        CheckResult(
            result.name,
            result.passed,
            result.detail,
            result.scope,
            member if result.member is None else result.member,
            result.warning,
        )
        for result in results
    )


def rel(root: Path, path: Path) -> str:
    """Return a path relative to the audit root."""
    return _rel(root, path)


def _version_failures(
    root: Path,
    marker_path: Path,
    config: Mapping[str, object] | None,
) -> list[str]:
    standard_version = string_config_value(config, "standard_version")
    if standard_version is None:
        return [
            f"{_rel(root, marker_path)} is missing standard_version; add "
            f'standard_version = "{STANDARD_VERSION}" after reviewing the current standard'
        ]
    if standard_version != STANDARD_VERSION:
        return [
            f"{_rel(root, marker_path)} targets standard_version {standard_version!r} "
            f"but installed wn-dev-std implements {STANDARD_VERSION!r}"
        ]
    return []


def _kind_failures(
    root: Path,
    marker_path: Path,
    config: Mapping[str, object] | None,
) -> list[str]:
    failures: list[str] = []
    kind = config_kind(config)
    raw_kind = string_config_value(config, "kind")
    if raw_kind is not None and kind not in {"package", "workspace"}:
        failures.append(f"{_rel(root, marker_path)} has unsupported kind {raw_kind!r}")
    if kind == "workspace":
        package_fields = [
            field for field in ("profile", "enabled_scopes") if _has_key(config, field)
        ]
        if package_fields:
            failures.append(
                f"{_rel(root, marker_path)} kind='workspace' must not declare "
                + ", ".join(package_fields)
            )
    elif _has_key(config, "workspace"):
        failures.append(f"{_rel(root, marker_path)} kind='package' must not declare [workspace]")
    return failures


def _enabled_scope_failures(
    root: Path,
    marker_path: Path,
    config: Mapping[str, object] | None,
) -> list[str]:
    if config is None or "enabled_scopes" not in config:
        return []
    value = config.get("enabled_scopes")
    if not isinstance(value, list):
        return [f"{_rel(root, marker_path)} enabled_scopes must be an array of strings"]
    invalid = [
        repr(item)
        for item in cast(list[object], value)
        if not isinstance(item, str) or item not in AUDIT_SCOPES
    ]
    if not invalid:
        return []
    return [
        f"{_rel(root, marker_path)} has invalid enabled_scopes "
        + ", ".join(invalid)
        + "; valid scopes: "
        + ", ".join(AUDIT_SCOPES)
    ]


def _has_key(config: Mapping[str, object] | None, key: str) -> bool:
    return config is not None and key in config


def _is_within_root(root: Path, path: Path) -> bool:
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()
