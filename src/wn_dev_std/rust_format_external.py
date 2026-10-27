"""Bounded direct external Cargo package identity checks for formatter ownership."""

from __future__ import annotations

import os
import stat
import tomllib
from collections.abc import Mapping
from pathlib import Path

from wn_dev_std.rust_cargo_workspace import mapping_value

MAX_EXTERNAL_MANIFESTS = 256
MAX_EXTERNAL_MANIFEST_BYTES = 4 * 1024 * 1024
MAX_MANIFEST_BYTES = 1024 * 1024


def separate_external_packages(root: Path, paths: set[Path]) -> bool:
    """Verify direct external identities without traversing their dependencies."""
    if len(paths) > MAX_EXTERNAL_MANIFESTS:
        return False
    remaining = MAX_EXTERNAL_MANIFEST_BYTES
    for path in sorted(paths):
        source = _identity_source(path, min(MAX_MANIFEST_BYTES, remaining))
        if source is None:
            return False
        remaining -= len(source)
        if not _separate_identity(root, path, source):
            return False
    return True


def _identity_source(path: Path, limit: int) -> bytes | None:
    try:
        if not _unlinked_path(path):
            return None
        manifest = path / "Cargo.toml"
        if manifest.is_symlink() or not stat.S_ISREG(manifest.lstat().st_mode):
            return None
        with manifest.open("rb") as handle:
            source = handle.read(limit + 1)
        return source if len(source) <= limit else None
    except (OSError, ValueError):
        return None


def _unlinked_path(path: Path) -> bool:
    if path.resolve() != path:
        return False
    return not any(parent.is_symlink() or parent.is_junction() for parent in (path, *path.parents))


def _separate_identity(root: Path, path: Path, source: bytes) -> bool:
    try:
        manifest: Mapping[str, object] = tomllib.loads(source.decode("utf-8"))
        package = mapping_value(manifest, "package")
        if package is None or not _named_package(package):
            return False
        redirect = package.get("workspace")
        return redirect is None or _separate_redirect(root, path, redirect)
    except (OSError, ValueError, RecursionError):
        return False


def _named_package(package: Mapping[str, object]) -> bool:
    name = package.get("name")
    return isinstance(name, str) and bool(name)


def _separate_redirect(root: Path, path: Path, redirect: object) -> bool:
    if not isinstance(redirect, str) or not redirect:
        return False
    target = Path(os.path.abspath(path / redirect))
    return target.is_dir() and _unlinked_path(target) and target.resolve() != root
