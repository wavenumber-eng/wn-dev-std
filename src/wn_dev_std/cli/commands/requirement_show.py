"""`requirement show` command."""

from __future__ import annotations

import argparse

from wn_dev_std.cli.commands.governance_common import (
    add_format_argument,
    add_root_argument,
)
from wn_dev_std.cli.commands.governance_show_common import run_show_command
from wn_dev_std.cli.types import SubparserRegistry


def register(subparsers: SubparserRegistry) -> None:
    """Register the subcommand."""
    parser = subparsers.add_parser(
        "show",
        help="Show a compliant requirement",
        description="Show a compliant Wavenumber requirement document.",
    )
    parser.add_argument("requirement_id", help="Requirement id to show")
    add_root_argument(parser)
    add_format_argument(parser)
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Run `requirement show`."""
    return run_show_command(args, "requirement", "Requirement", "requirement_id")
