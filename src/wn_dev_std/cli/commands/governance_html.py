"""Generate governance HTML command."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import cast

from wn_dev_std.cli.types import SubparserRegistry
from wn_dev_std.governance_html import generate_governance_html


def register(subparsers: SubparserRegistry) -> None:
    """Register the html subcommand."""
    parser = subparsers.add_parser(
        "html",
        help="Generate HTML pages for governance docs",
        description="Generate HTML pages for plans, logs, ADRs, and requirements.",
    )
    parser.add_argument("--root", default=".", help="Project root")
    parser.add_argument(
        "--output",
        required=True,
        help="Output directory for generated governance HTML",
    )
    parser.add_argument(
        "--css",
        action="append",
        default=[],
        help="CSS href to include; repeat for multiple stylesheets",
    )
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Run the html generation command."""
    report = generate_governance_html(
        Path(_string_attr(args, "root")),
        Path(_string_attr(args, "output")),
        css_hrefs=_string_list_attr(args, "css"),
    )
    print(f"Generated {len(report.pages)} governance page(s) under {report.output_root}")
    return 0


def _string_attr(args: argparse.Namespace, name: str) -> str:
    value = getattr(args, name)
    if isinstance(value, str):
        return value
    raise TypeError(f"expected {name} to be a string")


def _string_list_attr(args: argparse.Namespace, name: str) -> tuple[str, ...]:
    value = getattr(args, name)
    if not isinstance(value, list):
        return ()
    return tuple(
        item for item in cast(list[object], value) if isinstance(item, str) and item.strip()
    )
