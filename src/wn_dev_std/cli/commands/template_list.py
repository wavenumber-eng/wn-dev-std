"""`template list` command."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from wn_dev_std.cli.types import SubparserRegistry
from wn_dev_std.template_library import template_catalog


def register(subparsers: SubparserRegistry) -> None:
    """Register the subcommand."""
    parser = subparsers.add_parser(
        "list",
        help="List templates shipped by this standard version",
        description="List templates shipped by this standard version.",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Run `template list`."""
    catalog = template_catalog()
    if getattr(args, "format", "text") == "json":
        print(json.dumps({"templates": [asdict(item) for item in catalog]}, indent=2))
        return 0
    for item in catalog:
        print(f"{item.name}: {item.summary}")
    return 0
