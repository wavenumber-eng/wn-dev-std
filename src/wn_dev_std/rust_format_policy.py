"""Ownership proof for the bounded single-package Cargo formatter lane."""

from __future__ import annotations

import os
import shlex
import stat
import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from wn_dev_std.rust_cargo_workspace import mapping_value

MAX_MANIFEST_BYTES = 1024 * 1024
MAX_INVENTORY_ENTRIES = 20_000
MAX_DEPENDENCY_DEPTH = 64
MAX_DEPENDENCY_ENTRIES = 20_000
TRANSIENT_DIRECTORIES = {
    ".git",
    ".venv",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "target",
}
DEPENDENCY_TABLES = {
    "dependencies",
    "dev-dependencies",
    "build-dependencies",
    "dev_dependencies",
    "build_dependencies",
    "replace",
}


def has_format_lane(root: Path, commands: Sequence[str]) -> bool:
    """Accept the full lane, or an exactly selected and proven single package."""
    for command in commands:
        arguments = _arguments(command)
        if arguments == ["cargo", "fmt", "--all", "--", "--check"]:
            return True
        if _is_owned_selector(arguments) and _is_single_package(root, arguments[3]):
            return True
    return False


def _arguments(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return []


def _is_owned_selector(arguments: list[str]) -> bool:
    return (
        len(arguments) == 6
        and arguments[:2] == ["cargo", "fmt"]
        and arguments[2] in {"--package", "-p"}
        and arguments[4:] == ["--", "--check"]
    )


def _is_single_package(root: Path, selector: str) -> bool:
    manifest = _manifest(root / "Cargo.toml")
    if manifest is None or not _root_identity_matches(manifest, selector):
        return False
    if not _self_workspace(manifest):
        return False
    return _external_dependency_paths_only(root, manifest) and _no_extra_manifest(root)


def _manifest(path: Path) -> Mapping[str, object] | None:
    try:
        if _is_link(path) or not stat.S_ISREG(path.lstat().st_mode):
            return None
        with path.open("rb") as handle:
            source = handle.read(MAX_MANIFEST_BYTES + 1)
        if len(source) > MAX_MANIFEST_BYTES:
            return None
        return tomllib.loads(source.decode("utf-8"))
    except (OSError, ValueError, RecursionError):
        return None


def _root_identity_matches(manifest: Mapping[str, object], selector: str) -> bool:
    package = mapping_value(manifest, "package")
    return (
        package is not None
        and package.get("name") == selector
        and bool(selector)
        and "workspace" not in package
    )


def _self_workspace(manifest: Mapping[str, object]) -> bool:
    workspace = mapping_value(manifest, "workspace")
    return workspace is not None and all(
        workspace.get(key, []) == [] for key in ("members", "default-members", "exclude")
    )


def _external_dependency_paths_only(root: Path, manifest: Mapping[str, object]) -> bool:
    for value in _dependency_paths(manifest):
        if not isinstance(value, str) or not value:
            return False
        try:
            path = root / value
            lexical = Path(os.path.abspath(path))
            if lexical.is_relative_to(root.resolve()) or path.resolve().is_relative_to(
                root.resolve()
            ):
                return False
        except (OSError, ValueError):
            return False
    return True


def _dependency_paths(mapping: Mapping[str, object]) -> list[object]:
    if not _bounded_tables(mapping):
        return [None]
    paths: list[object] = []
    pending: list[tuple[Mapping[str, object], int]] = [(mapping, 0)]
    while pending:
        current, depth = pending.pop()
        paths.extend(_mapping_paths(current, depth, pending))
    return paths


def _bounded_tables(mapping: Mapping[str, object]) -> bool:
    pending = [(mapping, 0)]
    visited = 0
    while pending:
        current, depth = pending.pop()
        visited += len(current)
        if depth > MAX_DEPENDENCY_DEPTH or visited > MAX_DEPENDENCY_ENTRIES:
            return False
        pending.extend(
            (cast(Mapping[str, object], value), depth + 1)
            for value in current.values()
            if isinstance(value, dict)
        )
    return True


def _mapping_paths(
    mapping: Mapping[str, object],
    depth: int,
    pending: list[tuple[Mapping[str, object], int]],
) -> list[object]:
    paths: list[object] = []
    for key, value in mapping.items():
        if not isinstance(value, dict):
            continue
        nested = cast(Mapping[str, object], value)
        if key in DEPENDENCY_TABLES:
            paths.extend(_table_paths(nested))
        elif key == "patch":
            paths.extend(_patch_paths(nested))
        else:
            pending.append((nested, depth + 1))
    return paths


def _table_paths(table: Mapping[str, object]) -> list[object]:
    return [
        cast(Mapping[str, object], dependency)["path"]
        for dependency in table.values()
        if isinstance(dependency, dict) and "path" in dependency
    ]


def _patch_paths(table: Mapping[str, object]) -> list[object]:
    paths: list[object] = []
    for registry in table.values():
        if isinstance(registry, dict):
            paths.extend(_table_paths(cast(Mapping[str, object], registry)))
    return paths


def _is_link(path: Path) -> bool:
    return path.is_symlink() or path.is_junction()


def _no_extra_manifest(root: Path) -> bool:
    unreadable: list[OSError] = []
    visited = 0
    for directory, children, files in os.walk(root, onerror=unreadable.append):
        children[:] = [name for name in children if name not in TRANSIENT_DIRECTORIES]
        if any(_is_link(Path(directory) / name) for name in children):
            return False
        visited += len(children) + len(files)
        if visited > MAX_INVENTORY_ENTRIES:
            return False
        if Path(directory) != root and any(name.casefold() == "cargo.toml" for name in files):
            return False
    return not unreadable
