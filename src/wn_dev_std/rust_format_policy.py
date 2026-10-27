"""Ownership proof for bounded, completely selected Cargo formatter lanes."""

from __future__ import annotations

import os
import shlex
import stat
import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from wn_dev_std.rust_cargo_workspace import mapping_value
from wn_dev_std.rust_format_external import separate_external_packages

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
    """Accept the full lane, or exact selection of every proven owned package."""
    for command in commands:
        arguments = _arguments(command)
        if arguments == ["cargo", "fmt", "--all", "--", "--check"]:
            return True
        selectors = _owned_selectors(arguments)
        if selectors and _is_owned_workspace(root, selectors):
            return True
    return False


def _arguments(command: str) -> list[str]:
    try:
        return shlex.split(command)
    except ValueError:
        return []


def _owned_selectors(arguments: list[str]) -> list[str]:
    if arguments[:2] != ["cargo", "fmt"] or arguments[-2:] != ["--", "--check"]:
        return []
    pairs = arguments[2:-2]
    if not pairs or len(pairs) % 2:
        return []
    if any(flag not in {"--package", "-p"} for flag in pairs[::2]):
        return []
    names = pairs[1::2]
    return names if len(set(names)) == len(names) else []


def _is_owned_workspace(root: Path, selectors: list[str]) -> bool:
    try:
        if _is_link(root):
            return False
        root = root.resolve()
    except (OSError, ValueError, RuntimeError):
        return False
    manifest = _manifest(root / "Cargo.toml")
    if manifest is None:
        return False
    packages = _owned_packages(root, manifest)
    if packages is None or set(selectors) != {name for name, _ in packages.values()}:
        return False
    return _owned_dependencies(root, packages) and _no_extra_manifest(root, set(packages))


def _owned_dependencies(root: Path, packages: dict[Path, tuple[str, Mapping[str, object]]]) -> bool:
    owned = set(packages)
    external: set[Path] = set()
    return all(
        _declared_dependency_paths_only(root, path, cargo, owned, external)
        for path, (_, cargo) in packages.items()
    ) and separate_external_packages(root, external)


def _manifest(path: Path) -> Mapping[str, object] | None:
    try:
        if _is_link(path) or not stat.S_ISREG(path.lstat().st_mode):
            return None
        with path.open("rb") as handle:
            source = handle.read(MAX_MANIFEST_BYTES + 1)
        if len(source) > MAX_MANIFEST_BYTES:
            return None
        return tomllib.loads(source.decode("utf-8"))
    except (OSError, ValueError, RecursionError, RuntimeError):
        return None


def _package_name(manifest: Mapping[str, object]) -> str | None:
    package = mapping_value(manifest, "package")
    if package is None or "workspace" in package:
        return None
    name = package.get("name")
    if not isinstance(name, str) or not name:
        return None
    return name if all(character.isalnum() or character in "-_" for character in name) else None


def _owned_packages(
    root: Path, manifest: Mapping[str, object]
) -> dict[Path, tuple[str, Mapping[str, object]]] | None:
    name = _package_name(manifest)
    members = _workspace_members(manifest)
    if name is None or members is None:
        return None
    packages = {root: (name, manifest)}
    names = {name}
    for member in members:
        selected = _member_package(root, member)
        if selected is None:
            return None
        path, member_name, cargo = selected
        if path in packages or member_name in names:
            return None
        names.add(member_name)
        packages[path] = (member_name, cargo)
    return packages


def _member_package(root: Path, member: object) -> tuple[Path, str, Mapping[str, object]] | None:
    path = _member_path(root, member)
    if path is None:
        return None
    cargo = _manifest(path / "Cargo.toml")
    if cargo is None or "workspace" in cargo:
        return None
    name = _package_name(cargo)
    return (path, name, cargo) if name is not None else None


def _workspace_members(manifest: Mapping[str, object]) -> list[object] | None:
    workspace = mapping_value(manifest, "workspace")
    if workspace is None:
        return None
    if any(workspace.get(key, []) != [] for key in ("default-members", "exclude")):
        return None
    members = workspace.get("members", [])
    if not isinstance(members, list):
        return None
    declared = cast(list[object], members)
    return declared if len(declared) <= MAX_INVENTORY_ENTRIES else None


def _member_path(root: Path, raw: object) -> Path | None:
    relative = _literal_member(raw)
    if relative is None:
        return None
    path = root / relative
    if path == root:
        return None
    return path if _unlinked_member(root, path) else None


def _literal_member(raw: object) -> Path | None:
    if not isinstance(raw, str) or not raw or any(char in raw for char in "*?[]\\:\0"):
        return None
    relative = Path(raw)
    if relative.is_absolute() or ".." in relative.parts:
        return None
    return relative


def _unlinked_member(root: Path, path: Path) -> bool:
    try:
        if path.resolve() != path or not path.is_relative_to(root):
            return False
        for parent in (path, *path.parents):
            if parent == root:
                break
            if _is_link(parent):
                return False
    except (OSError, ValueError, RuntimeError):
        return False
    return True


def _declared_dependency_paths_only(
    root: Path,
    owner: Path,
    manifest: Mapping[str, object],
    packages: set[Path],
    external: set[Path],
) -> bool:
    return all(
        _declared_dependency(root, owner, value, packages, external)
        for value in _dependency_paths(manifest)
    )


def _declared_dependency(
    root: Path, owner: Path, value: object, packages: set[Path], external: set[Path]
) -> bool:
    if not isinstance(value, str) or not value:
        return False
    try:
        path = owner / value
        lexical = Path(os.path.abspath(path))
        resolved = path.resolve()
        if lexical.is_relative_to(root) or resolved.is_relative_to(root):
            return lexical in packages and resolved in packages
        external.add(lexical)
    except (OSError, ValueError, RuntimeError):
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


def _no_extra_manifest(root: Path, packages: set[Path]) -> bool:
    unreadable: list[OSError] = []
    visited = 0
    found: set[Path] = set()
    for directory, children, files in os.walk(root, onerror=unreadable.append):
        children[:] = [name for name in children if name not in TRANSIENT_DIRECTORIES]
        if any(_is_link(Path(directory) / name) for name in children):
            return False
        visited += len(children) + len(files)
        if visited > MAX_INVENTORY_ENTRIES:
            return False
        manifests = [name for name in files if name.casefold() == "cargo.toml"]
        if manifests:
            if len(manifests) != 1 or Path(directory) not in packages:
                return False
            found.add(Path(directory))
    return not unreadable and found == packages
