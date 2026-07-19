"""Cargo workspace helpers for Rust policy checks."""

from __future__ import annotations

import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fnmatch import fnmatchcase
from pathlib import Path
from typing import cast

SUPPORTED_EDITIONS = {"2021", "2024"}


@dataclass(frozen=True, slots=True)
class CargoMember:
    """Workspace member Cargo manifest loaded from the audited root."""

    key: str
    manifest: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class UnsafeLintTarget:
    """Effective unsafe lint level for one Cargo package."""

    label: str
    level: str | None


def metadata_failures(
    package: Mapping[str, object],
    label: str,
    failures: list[str],
    workspace_package: Mapping[str, object] | None = None,
) -> None:
    """Append package metadata failures, honoring workspace inheritance."""
    edition = _metadata_string_value(package, "edition", label, failures, workspace_package)
    if edition is not None and edition not in SUPPORTED_EDITIONS:
        failures.append(f"{label}.edition must be 2021 or 2024")
    _metadata_string_value(package, "rust-version", label, failures, workspace_package)


def workspace_failures(
    workspace: Mapping[str, object],
    metadata_required: bool,
    failures: list[str],
) -> None:
    """Append workspace metadata failures."""
    resolver = _string_value(workspace.get("resolver"))
    if resolver is None:
        failures.append("workspace.resolver is required")
    elif resolver not in {"2", "3"}:
        failures.append("workspace.resolver must be 2 or 3")

    package = mapping_value(workspace, "package")
    if package is None:
        if metadata_required:
            failures.append("workspace.package is required for virtual workspaces")
        return

    metadata_failures(package, "workspace.package", failures)
    edition = _string_value(package.get("edition"))
    if edition == "2024" and resolver != "3":
        failures.append('Edition 2024 workspaces require resolver = "3"')


def workspace_member_manifests(
    root: Path,
    workspace: Mapping[str, object] | None,
    failures: list[str],
) -> tuple[CargoMember, ...]:
    """Load bounded workspace member manifests declared by the root manifest."""
    if workspace is None:
        return ()
    exclude_patterns = _workspace_exclude_patterns(workspace, failures)
    members: list[CargoMember] = []
    for member in _string_array(workspace.get("members")):
        members.extend(_load_workspace_member_manifests(root, member, exclude_patterns, failures))
    return tuple(members)


def member_metadata_failures(
    members: Sequence[CargoMember],
    workspace_package: Mapping[str, object] | None,
    failures: list[str],
) -> None:
    """Append metadata failures for loaded workspace member packages."""
    for member in members:
        package = mapping_value(member.manifest, "package")
        if package is None:
            failures.append(f"workspace member {member.key} requires [package]")
            continue
        metadata_failures(
            package,
            f"workspace member {member.key} package",
            failures,
            workspace_package,
        )


def unsafe_lint_targets(
    cargo: Mapping[str, object],
    members: Sequence[CargoMember],
    failures: list[str],
) -> tuple[UnsafeLintTarget, ...]:
    """Return effective unsafe lint levels for root and member packages."""
    workspace_level = workspace_unsafe_lint_level(cargo)
    targets: list[UnsafeLintTarget] = []
    if mapping_value(cargo, "package") is not None:
        targets.append(
            UnsafeLintTarget(
                "package",
                _manifest_unsafe_lint_level(cargo, workspace_level, "package", failures),
            )
        )
    elif not members:
        targets.append(UnsafeLintTarget("workspace", workspace_level))

    for member in members:
        label = f"workspace member {member.key}"
        targets.append(
            UnsafeLintTarget(
                label,
                _manifest_unsafe_lint_level(member.manifest, workspace_level, label, failures),
            )
        )
    return tuple(targets)


def local_unsafe_lint_level(cargo: Mapping[str, object]) -> str | None:
    """Return the manifest-local unsafe lint level."""
    rust_lints = mapping_value(cargo, "lints.rust")
    return _unsafe_lint_level_from_table(rust_lints)


def workspace_unsafe_lint_level(cargo: Mapping[str, object]) -> str | None:
    """Return the root workspace unsafe lint level."""
    workspace_lints = mapping_value(cargo, "workspace.lints.rust")
    return _unsafe_lint_level_from_table(workspace_lints)


def mapping_value(mapping: Mapping[str, object], dotted_key: str) -> Mapping[str, object] | None:
    """Return a nested mapping value from a dotted TOML key."""
    current: object = mapping
    for part in dotted_key.split("."):
        if not isinstance(current, dict):
            return None
        current = cast(Mapping[str, object], current).get(part)
    if isinstance(current, dict):
        return cast(Mapping[str, object], current)
    return None


def _metadata_string_value(
    package: Mapping[str, object],
    key: str,
    label: str,
    failures: list[str],
    workspace_package: Mapping[str, object] | None,
) -> str | None:
    value = package.get(key)
    direct_value = _string_value(value)
    if direct_value is not None:
        return direct_value
    if _workspace_inheritance_enabled(value):
        return _workspace_metadata_value(key, label, failures, workspace_package)
    failures.append(f"{label}.{key} is required")
    return None


def _workspace_metadata_value(
    key: str,
    label: str,
    failures: list[str],
    workspace_package: Mapping[str, object] | None,
) -> str | None:
    inherited = _string_value(workspace_package.get(key)) if workspace_package else None
    if inherited is not None:
        return inherited
    failures.append(
        f"{label}.{key} inherits workspace value but workspace.package.{key} is missing"
    )
    return None


def _workspace_inheritance_enabled(value: object) -> bool:
    if not isinstance(value, dict):
        return False
    return cast(Mapping[str, object], value).get("workspace") is True


def _load_workspace_member_manifests(
    root: Path,
    member: str,
    exclude_patterns: Sequence[str],
    failures: list[str],
) -> tuple[CargoMember, ...]:
    loaded: list[CargoMember] = []
    for member_path in _workspace_member_paths(root, member, exclude_patterns, failures):
        key = _relative_path(root, member_path)
        manifest_path = member_path / "Cargo.toml"
        if not manifest_path.exists():
            failures.append(f"workspace member {key} requires Cargo.toml")
            continue
        manifest = _load_toml_mapping(manifest_path, f"{key}/Cargo.toml")
        if isinstance(manifest, str):
            failures.append(manifest)
            continue
        loaded.append(CargoMember(key, manifest))
    return tuple(loaded)


def _workspace_member_paths(
    root: Path,
    member: str,
    exclude_patterns: Sequence[str],
    failures: list[str],
) -> tuple[Path, ...]:
    raw_path = Path(member)
    if raw_path.is_absolute() or ".." in raw_path.parts:
        failures.append(f"workspace member {member!r} must be a bounded relative path")
        return ()
    uses_glob = _has_glob(member)
    paths = sorted(root.glob(member)) if uses_glob else [root / raw_path]
    if not paths:
        failures.append(f"workspace member {member!r} matched no directories")
        return ()
    return tuple(
        _valid_workspace_member_paths(
            root,
            member,
            paths,
            exclude_patterns,
            uses_glob,
            failures,
        )
    )


def _valid_workspace_member_paths(
    root: Path,
    member: str,
    paths: Sequence[Path],
    exclude_patterns: Sequence[str],
    uses_glob: bool,
    failures: list[str],
) -> list[Path]:
    valid: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if not _is_within_root(root, resolved):
            failures.append(f"workspace member {member!r} resolves outside the repository root")
        elif _is_excluded(root, resolved, exclude_patterns):
            continue
        elif not resolved.is_dir():
            if uses_glob:
                continue
            failures.append(
                f"workspace member {_relative_path(root, resolved)} must be a directory"
            )
        else:
            valid.append(resolved)
    return valid


def _workspace_exclude_patterns(
    workspace: Mapping[str, object],
    failures: list[str],
) -> tuple[str, ...]:
    patterns: list[str] = []
    for exclude in _string_array(workspace.get("exclude")):
        raw_path = Path(exclude)
        if raw_path.is_absolute() or ".." in raw_path.parts:
            failures.append(f"workspace exclude {exclude!r} must be a bounded relative path")
            continue
        patterns.append(_normalized_pattern(exclude))
    return tuple(patterns)


def _is_excluded(root: Path, path: Path, patterns: Sequence[str]) -> bool:
    if not patterns:
        return False
    relative = _relative_path(root, path)
    return any(_matches_exclude(relative, pattern) for pattern in patterns)


def _matches_exclude(relative: str, pattern: str) -> bool:
    return (
        relative == pattern
        or relative.startswith(pattern.rstrip("/") + "/")
        or fnmatchcase(relative, pattern)
    )


def _unsafe_lint_level_from_table(lints: Mapping[str, object] | None) -> str | None:
    if lints is None:
        return None
    value = lints.get("unsafe_code")
    if isinstance(value, str):
        return value.strip().lower()
    if isinstance(value, dict):
        return _string_value(cast(Mapping[str, object], value).get("level"))
    return None


def _manifest_unsafe_lint_level(
    manifest: Mapping[str, object],
    workspace_level: str | None,
    label: str,
    failures: list[str],
) -> str | None:
    local = local_unsafe_lint_level(manifest)
    if local is not None:
        return local
    if workspace_level is None:
        return None
    if _lints_workspace_enabled(manifest):
        return workspace_level
    failures.append(f"{label} must declare lints.workspace = true to inherit workspace.lints")
    return workspace_level


def _lints_workspace_enabled(cargo: Mapping[str, object]) -> bool:
    lints = mapping_value(cargo, "lints")
    return lints is not None and lints.get("workspace") is True


def _load_toml_mapping(path: Path, label: str) -> Mapping[str, object] | str:
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        return f"{label} is invalid TOML: {exc}"
    return cast(Mapping[str, object], data)


def _string_value(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _string_array(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    items: list[str] = []
    for item in cast(list[object], value):
        text = _string_value(item)
        if text is not None:
            items.append(text)
    return tuple(items)


def _has_glob(value: str) -> bool:
    return any(marker in value for marker in "*?[")


def _normalized_pattern(value: str) -> str:
    return value.replace("\\", "/").rstrip("/")


def _relative_path(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _is_within_root(root: Path, path: Path) -> bool:
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return False
    return True
