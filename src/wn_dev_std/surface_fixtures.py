"""Fixture/data catalog checks for governed surfaces."""

from __future__ import annotations

import fnmatch
from collections.abc import Mapping
from pathlib import Path
from typing import cast

ACTIVE_FIXTURE_STATUSES = {"active", "generated"}
INACTIVE_FIXTURE_STATUSES = {"archived", "ignored"}
PHYSICAL_FIXTURE_KINDS = {"fixture_file", "physical_file", "corpus_file"}
DEFAULT_FIXTURE_ROOTS = ("tests/fixtures",)
DEFAULT_IGNORES = (
    ".git/**",
    ".mypy_cache/**",
    ".pytest_cache/**",
    ".ruff_cache/**",
    ".venv/**",
    "__pycache__/**",
    "build/**",
    "dist/**",
    "node_modules/**",
)


def validate_fixture_catalog(
    root: Path,
    manifest_path: Path,
    payload: Mapping[str, object],
    surface_fixture_targets: set[str],
    failures: list[str],
) -> None:
    """Validate optional fixture/data registry entries."""
    fixtures = _table_array(payload.get("fixtures"))
    config = _mapping(payload.get("fixture_governance"))
    if payload.get("fixtures") is not None and not fixtures:
        failures.append(f"{_rel(root, manifest_path)}: fixtures must be tables")
        return
    if not fixtures and config is None:
        return
    registry_configured = bool(fixtures) or config is not None
    fixture_paths = _validate_fixture_entries(
        root,
        manifest_path,
        fixtures,
        surface_fixture_targets,
        failures,
    )
    _validate_surface_fixture_registration(
        root,
        manifest_path,
        surface_fixture_targets,
        fixture_paths,
        registry_configured,
        failures,
    )
    _validate_discovered_fixture_files(root, manifest_path, config, fixture_paths, failures)


def _validate_fixture_entries(
    root: Path,
    manifest_path: Path,
    fixtures: tuple[Mapping[str, object], ...],
    surface_fixture_targets: set[str],
    failures: list[str],
) -> dict[str, str]:
    fixture_paths: dict[str, str] = {}
    seen_ids: set[str] = set()
    for index, fixture in enumerate(fixtures, start=1):
        label = f"{_rel(root, manifest_path)}: fixtures[{index}]"
        fixture_id = _required_string(fixture, "id", label, failures)
        kind = _required_string(fixture, "kind", label, failures)
        path = _optional_string(fixture, "path")
        status = _required_string(fixture, "status", label, failures)
        _required_string(fixture, "purpose", label, failures)
        _validate_fixture_id(label, fixture_id, seen_ids, failures)
        _validate_fixture_status(label, status, failures)
        _validate_fixture_path_presence(label, kind, path, failures)
        if fixture_id:
            fixture_paths[fixture_id] = path
        if path:
            fixture_paths[path] = path
        _validate_fixture_path(root, label, path, status, failures)
    _validate_unused_active_fixtures(
        manifest_path,
        root,
        fixtures,
        surface_fixture_targets,
        failures,
    )
    return fixture_paths


def _validate_fixture_id(
    label: str,
    fixture_id: str,
    seen_ids: set[str],
    failures: list[str],
) -> None:
    if not fixture_id:
        return
    if fixture_id in seen_ids:
        failures.append(f"{label}: duplicate fixture id {fixture_id!r}")
    seen_ids.add(fixture_id)


def _validate_fixture_status(label: str, status: str, failures: list[str]) -> None:
    allowed = ACTIVE_FIXTURE_STATUSES | INACTIVE_FIXTURE_STATUSES
    if status and status not in allowed:
        failures.append(f"{label}: invalid status {status!r}")


def _validate_fixture_path_presence(
    label: str,
    kind: str,
    path: str,
    failures: list[str],
) -> None:
    if kind in PHYSICAL_FIXTURE_KINDS and not path:
        failures.append(f"{label}: physical fixture kind {kind!r} requires path")


def _validate_fixture_path(
    root: Path,
    label: str,
    path: str,
    status: str,
    failures: list[str],
) -> None:
    if not path or status not in ACTIVE_FIXTURE_STATUSES:
        return
    target = (root / path).resolve()
    if not _is_within_root(root, target):
        failures.append(f"{label}: fixture path escapes repository root {path!r}")
        return
    if not target.exists():
        failures.append(f"{label}: missing fixture file {path!r}")


def _validate_unused_active_fixtures(
    manifest_path: Path,
    root: Path,
    fixtures: tuple[Mapping[str, object], ...],
    surface_fixture_targets: set[str],
    failures: list[str],
) -> None:
    for fixture in fixtures:
        fixture_id = _string_value(fixture.get("id"))
        status = _string_value(fixture.get("status"))
        path = _string_value(fixture.get("path"))
        if status != "active":
            continue
        if fixture_id not in surface_fixture_targets and path not in surface_fixture_targets:
            label = path or fixture_id
            failures.append(f"{_rel(root, manifest_path)}: unused active fixture {label!r}")


def _validate_surface_fixture_registration(
    root: Path,
    manifest_path: Path,
    surface_fixture_targets: set[str],
    fixture_paths: Mapping[str, str],
    registry_configured: bool,
    failures: list[str],
) -> None:
    if not registry_configured:
        return
    for target in sorted(surface_fixture_targets):
        if target not in fixture_paths:
            failures.append(f"{_rel(root, manifest_path)}: unregistered surface fixture {target!r}")


def _validate_discovered_fixture_files(
    root: Path,
    manifest_path: Path,
    config: Mapping[str, object] | None,
    fixture_paths: Mapping[str, str],
    failures: list[str],
) -> None:
    roots = _string_tuple(config.get("discovery_roots") if config else None)
    if not roots:
        roots = DEFAULT_FIXTURE_ROOTS
    ignores = DEFAULT_IGNORES + _string_tuple(config.get("ignore") if config else None)
    registered_paths = set(fixture_paths.values())
    for discovered in _discovered_files(root, manifest_path, roots, ignores, failures):
        if discovered not in registered_paths:
            failures.append(
                f"{_rel(root, manifest_path)}: discovered unregistered fixture {discovered!r}"
            )


def _discovered_files(
    root: Path,
    manifest_path: Path,
    roots: tuple[str, ...],
    ignores: tuple[str, ...],
    failures: list[str],
) -> list[str]:
    files: list[str] = []
    for root_text in roots:
        base = root / root_text
        if not _is_within_root(root, base.resolve()):
            failures.append(
                f"{_rel(root, manifest_path)}: fixture discovery root escapes repository "
                f"{root_text!r}"
            )
            continue
        if not base.exists():
            continue
        paths = (
            [base] if base.is_file() else sorted(path for path in base.rglob("*") if path.is_file())
        )
        for path in paths:
            relative = _rel(root, path)
            if not any(_path_matches(relative, pattern) for pattern in ignores):
                files.append(relative)
    return files


def _path_matches(path: str, pattern: str) -> bool:
    normalized = pattern.replace("\\", "/").strip("/")
    return fnmatch.fnmatchcase(path, normalized)


def _required_string(
    metadata: Mapping[str, object],
    key: str,
    label: str,
    failures: list[str],
) -> str:
    value = _string_value(metadata.get(key))
    if value:
        return value
    failures.append(f"{label}: missing {key}")
    return ""


def _optional_string(metadata: Mapping[str, object], key: str) -> str:
    value = metadata.get(key)
    return value.strip() if isinstance(value, str) else ""


def _string_value(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(
        item.strip() for item in cast(list[object], value) if isinstance(item, str) and item.strip()
    )


def _mapping(value: object) -> Mapping[str, object] | None:
    return cast(Mapping[str, object], value) if isinstance(value, dict) else None


def _table_array(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, list):
        return ()
    items: list[Mapping[str, object]] = []
    for item in cast(list[object], value):
        if isinstance(item, dict):
            items.append(cast(Mapping[str, object], item))
        else:
            return ()
    return tuple(items)


def _rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def _is_within_root(root: Path, target: Path) -> bool:
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return False
    return True
