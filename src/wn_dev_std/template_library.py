"""Version-matched project template discovery and copying."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Literal

TemplateName = Literal["typespec-contract", "lit-activity-web"]


@dataclass(frozen=True, slots=True)
class TemplateInfo:
    """Metadata for one copy-owned template."""

    name: TemplateName
    summary: str
    repository_path: str
    packaged_path: str


TEMPLATES: tuple[TemplateInfo, ...] = (
    TemplateInfo(
        "typespec-contract",
        "Independent TypeSpec contract authority with generated projections",
        "docs/templates/typespec-contract",
        "templates/typespec-contract",
    ),
    TemplateInfo(
        "lit-activity-web",
        "Lit application with typed activities, shell profiles, transports, and themes",
        "docs/templates/web/lit-activity",
        "templates/lit-activity-web",
    ),
)


def template_catalog() -> tuple[TemplateInfo, ...]:
    """Return templates shipped by this standard version."""
    return TEMPLATES


def copy_template(name: TemplateName, destination: Path) -> Path:
    """Copy a template to a new project-owned destination."""
    info = next(item for item in TEMPLATES if item.name == name)
    resolved_destination = destination.resolve()
    if resolved_destination.exists():
        raise FileExistsError(f"destination already exists: {resolved_destination}")

    repository_source = Path(__file__).resolve().parents[2] / info.repository_path
    ignore = shutil.ignore_patterns(
        "node_modules",
        "dist",
        "coverage",
        ".cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__pycache__",
    )
    if repository_source.is_dir():
        _require_destination_outside_source(repository_source.resolve(), resolved_destination)
        shutil.copytree(repository_source, resolved_destination, ignore=ignore)
        return resolved_destination

    packaged_source = resources.files("wn_dev_std").joinpath(info.packaged_path)
    with resources.as_file(packaged_source) as source:
        if not source.is_dir():
            raise FileNotFoundError(f"packaged template is missing: {info.packaged_path}")
        _require_destination_outside_source(source.resolve(), resolved_destination)
        shutil.copytree(source, resolved_destination, ignore=ignore)
    return resolved_destination


def _require_destination_outside_source(source: Path, destination: Path) -> None:
    if destination.is_relative_to(source):
        raise ValueError(f"destination must be outside the template source: {source}")
