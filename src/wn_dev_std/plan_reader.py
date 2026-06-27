"""Read-only helpers for compliant plans and work logs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from wn_dev_std.plan_hygiene import PlanCatalog, load_plan_catalog
from wn_dev_std.root_discovery import DiscoveredRoot, discover_project_root, load_standard_config


@dataclass(frozen=True, slots=True)
class PlanReadContext:
    """Discovered root plus its validated plan catalog."""

    discovered_root: DiscoveredRoot
    catalog: PlanCatalog


def load_plan_read_context(start: Path) -> PlanReadContext:
    """Discover a project root and load its plan catalog."""
    discovered = discover_project_root(start)
    config = load_standard_config(discovered.root)
    catalog = load_plan_catalog(discovered.root, config)
    return PlanReadContext(discovered, catalog)
