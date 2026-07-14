"""Project root discovery and standard config loading."""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

PREFERRED_STANDALONE_CONFIG = "dev-std.toml"
LEGACY_STANDALONE_CONFIG = "wn-dev-std.toml"
STANDALONE_CONFIG_NAMES = (PREFERRED_STANDALONE_CONFIG, LEGACY_STANDALONE_CONFIG)


@dataclass(frozen=True, slots=True)
class DiscoveredRoot:
    """Resolved project root and marker information."""

    root: Path
    marker: str
    marker_path: Path | None
    found_standard_config: bool


def discover_project_root(start: Path) -> DiscoveredRoot:
    """Discover the nearest Wavenumber project root from a start path."""
    current = _start_directory(start).resolve()
    git_fallback: Path | None = None

    for candidate in (current, *current.parents):
        standalone = _standalone_config_path(candidate)
        if standalone is not None:
            return DiscoveredRoot(candidate, standalone.name, standalone, True)

        pyproject = candidate / "pyproject.toml"
        if _pyproject_has_standard_config(pyproject):
            return DiscoveredRoot(candidate, "pyproject.toml", pyproject, True)

        if (candidate / ".git").exists():
            git_fallback = candidate
            break

    if git_fallback is not None:
        return DiscoveredRoot(git_fallback, ".git", git_fallback / ".git", False)
    return DiscoveredRoot(current, "cwd", None, False)


def load_pyproject(root: Path) -> Mapping[str, object] | None:
    """Load root pyproject data if present."""
    path = root / "pyproject.toml"
    if not path.exists():
        return None
    with path.open("rb") as handle:
        return cast(Mapping[str, object], tomllib.load(handle))


def load_standard_config(
    root: Path,
    pyproject: Mapping[str, object] | None = None,
) -> Mapping[str, object] | None:
    """Load Wavenumber standard config from standalone TOML or pyproject."""
    standalone = _standalone_config_path(root)
    if standalone is not None:
        with standalone.open("rb") as handle:
            raw = cast(Mapping[str, object], tomllib.load(handle))
        tool_raw = raw.get("tool")
        if isinstance(tool_raw, dict):
            tool = cast(Mapping[str, object], tool_raw)
            config_raw = tool.get("wn_dev_std")
            if isinstance(config_raw, dict):
                return cast(Mapping[str, object], config_raw)
        return raw

    pyproject_data = pyproject if pyproject is not None else load_pyproject(root)
    if pyproject_data is None:
        return None
    tool_raw = pyproject_data.get("tool")
    if not isinstance(tool_raw, dict):
        return None
    tool = cast(Mapping[str, object], tool_raw)
    config_raw = tool.get("wn_dev_std")
    if not isinstance(config_raw, dict):
        return None
    return cast(Mapping[str, object], config_raw)


def standard_config_path(root: Path) -> Path | None:
    """Return the standard config marker path at a root, if one exists."""
    standalone = _standalone_config_path(root)
    if standalone is not None:
        return standalone
    pyproject = root / "pyproject.toml"
    if _pyproject_has_standard_config(pyproject):
        return pyproject
    return None


def _start_directory(start: Path) -> Path:
    if start.exists() and start.is_file():
        return start.parent
    return start


def _standalone_config_path(root: Path) -> Path | None:
    for name in STANDALONE_CONFIG_NAMES:
        path = root / name
        if path.exists():
            return path
    return None


def _pyproject_has_standard_config(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        with path.open("rb") as handle:
            pyproject = cast(Mapping[str, object], tomllib.load(handle))
    except tomllib.TOMLDecodeError:
        return False
    tool_raw = pyproject.get("tool")
    if not isinstance(tool_raw, dict):
        return False
    tool = cast(Mapping[str, object], tool_raw)
    return isinstance(tool.get("wn_dev_std"), dict)
