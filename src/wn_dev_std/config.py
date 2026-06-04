"""Project configuration helpers for future conformance profiles."""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast


@dataclass(frozen=True, slots=True)
class ProjectConfig:
    """Parsed `wn-dev-std` project configuration."""

    profile: str
    distribution: str
    languages: tuple[str, ...]
    strict: bool


def load_project_config(root: Path) -> ProjectConfig:
    """Load `[tool.wn_dev_std]` from a project, falling back to strict Python defaults."""
    pyproject_path = root / "pyproject.toml"
    if not pyproject_path.exists():
        return _default_config()

    with pyproject_path.open("rb") as handle:
        pyproject = cast(Mapping[str, object], tomllib.load(handle))

    tool = _mapping_or_empty(pyproject.get("tool"))
    raw_config = _mapping_or_empty(tool.get("wn_dev_std"))
    return ProjectConfig(
        profile=_string(raw_config.get("profile"), "python-package"),
        distribution=_string(raw_config.get("distribution"), "pypi"),
        languages=_string_tuple(raw_config.get("languages"), ("python",)),
        strict=_bool(raw_config.get("strict"), True),
    )


def _default_config() -> ProjectConfig:
    return ProjectConfig(
        profile="python-package",
        distribution="pypi",
        languages=("python",),
        strict=True,
    )


def _mapping_or_empty(value: object) -> Mapping[str, object]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return cast(Mapping[str, object], value)
    raise ValueError("expected mapping value")


def _string(value: object, default: str) -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value
    raise ValueError("expected string value")


def _string_tuple(value: object, default: tuple[str, ...]) -> tuple[str, ...]:
    if value is None:
        return default
    if isinstance(value, list):
        raw_items = cast(list[object], value)
        items: list[str] = []
        for item in raw_items:
            if not isinstance(item, str):
                raise ValueError("expected string list value")
            items.append(item)
        return tuple(items)
    raise ValueError("expected string list value")


def _bool(value: object, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    raise ValueError("expected boolean value")
