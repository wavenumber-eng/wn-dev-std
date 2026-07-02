"""Shared helpers for ADR and requirement read commands."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from wn_dev_std.doc_governance import GovernanceCatalog, GovernanceRecord, load_governance_catalog
from wn_dev_std.plan_hygiene import read_document_body
from wn_dev_std.root_discovery import DiscoveredRoot, discover_project_root


@dataclass(frozen=True, slots=True)
class GovernanceReadContext:
    """Discovered root plus its validated governance catalog."""

    discovered_root: DiscoveredRoot
    catalog: GovernanceCatalog


def add_root_argument(parser: argparse.ArgumentParser) -> None:
    """Add a project-root discovery argument."""
    parser.add_argument("--root", help="Project root or nested path to discover from")


def add_format_argument(parser: argparse.ArgumentParser) -> None:
    """Add a text/JSON output format argument."""
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=("text", "json"),
        default="text",
        help="Output format",
    )


def output_format(args: argparse.Namespace) -> str:
    """Return normalized output format."""
    value = args.output_format
    if isinstance(value, str):
        return value
    raise TypeError("expected output_format to be a string")


def string_attr(args: argparse.Namespace, name: str) -> str:
    """Return an argparse string attribute."""
    value = getattr(args, name)
    if isinstance(value, str):
        return value
    raise TypeError(f"expected {name} to be a string")


def context_from_args(args: argparse.Namespace) -> GovernanceReadContext:
    """Load governance catalog using root discovery."""
    raw_root = getattr(args, "root", None)
    start = Path(raw_root) if isinstance(raw_root, str) and raw_root else Path.cwd()
    discovered = discover_project_root(start)
    catalog = load_governance_catalog(discovered.root)
    return GovernanceReadContext(discovered, catalog)


def print_catalog_failures(context: GovernanceReadContext) -> bool:
    """Print catalog failures and return whether failures were present."""
    if not context.catalog.failures:
        return False
    print("governance catalog is not compliant:")
    for failure in context.catalog.failures:
        print(f"- {failure}")
    return True


def records_for_type(
    catalog: GovernanceCatalog,
    record_type: str,
) -> tuple[GovernanceRecord, ...]:
    """Return catalog records of one governance type."""
    if record_type == "adr":
        return catalog.adrs
    if record_type == "requirement":
        return catalog.requirements
    raise ValueError(f"unknown record type: {record_type}")


def find_record(
    catalog: GovernanceCatalog,
    record_type: str,
    record_id: str,
) -> GovernanceRecord | None:
    """Find one governance record by type and id."""
    return next(
        (
            record
            for record in records_for_type(catalog, record_type)
            if record.record_id == record_id
        ),
        None,
    )


def record_body(catalog: GovernanceCatalog, record: GovernanceRecord) -> str:
    """Read one governance record body."""
    return read_document_body(catalog.root, record.relative_path)
