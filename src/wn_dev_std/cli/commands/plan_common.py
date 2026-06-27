"""Shared helpers for plan and work-log CLI commands."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Literal, cast

from wn_dev_std.plan_hygiene import PlanCatalog, PlanRecord
from wn_dev_std.plan_reader import PlanReadContext, load_plan_read_context


def add_root_argument(parser: argparse.ArgumentParser) -> None:
    """Add the common project root discovery argument."""
    parser.add_argument(
        "--root",
        default=".",
        help="Start path for project root discovery",
    )


def add_format_argument(parser: argparse.ArgumentParser) -> None:
    """Add the common output format argument."""
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=("text", "json"),
        default="text",
        help="Output format",
    )


def add_depends_on_argument(parser: argparse.ArgumentParser) -> None:
    """Add a repeated dependency argument."""
    parser.add_argument(
        "--depends-on",
        action="append",
        default=[],
        help="Dependency id; repeat for multiple dependencies",
    )


def context_from_args(args: argparse.Namespace) -> PlanReadContext:
    """Load a plan read context from parsed CLI args."""
    return load_plan_read_context(Path(string_attr(args, "root")))


def print_catalog_failures(context: PlanReadContext) -> bool:
    """Print catalog validation failures and report whether failures exist."""
    if not context.catalog.failures:
        return False
    print("plan catalog is not compliant:")
    for failure in context.catalog.failures:
        print(f"- {failure}")
    return True


def find_plan(catalog: PlanCatalog, plan_id: str) -> PlanRecord | None:
    """Find a plan by id."""
    for plan in catalog.plans:
        if plan.plan_id == plan_id:
            return plan
    return None


def output_format(args: argparse.Namespace) -> Literal["text", "json"]:
    """Return the requested output format."""
    value = string_attr(args, "output_format")
    if value in ("text", "json"):
        return value
    raise TypeError("expected output_format to be text or json")


def string_attr(args: argparse.Namespace, name: str) -> str:
    """Read a required string attribute from argparse results."""
    value = getattr(args, name)
    if isinstance(value, str):
        return value
    raise TypeError(f"expected {name} to be a string")


def optional_string_attr(args: argparse.Namespace, name: str) -> str | None:
    """Read an optional string attribute from argparse results."""
    value = getattr(args, name)
    if value is None or isinstance(value, str):
        return value
    raise TypeError(f"expected {name} to be a string or None")


def string_list_attr(args: argparse.Namespace, name: str) -> tuple[str, ...]:
    """Read a repeated string argument from argparse results."""
    value = getattr(args, name)
    if not isinstance(value, list):
        raise TypeError(f"expected {name} to be a list")
    items: list[str] = []
    for item in cast(list[object], value):
        if not isinstance(item, str):
            raise TypeError(f"expected {name} to contain only strings")
        if item.strip():
            items.append(item.strip())
    return tuple(items)
