"""`adr list` command."""

from __future__ import annotations

import argparse

from wn_dev_std.cli.commands.governance_common import (
    add_format_argument,
    add_root_argument,
)
from wn_dev_std.cli.commands.governance_list_common import run_list_command
from wn_dev_std.cli.types import SubparserRegistry


def register(subparsers: SubparserRegistry) -> None:
    """Register the subcommand."""
    parser = subparsers.add_parser(
        "list",
        help="List compliant ADRs",
        description="List compliant ADR documents.",
    )
    add_root_argument(parser)
    add_format_argument(parser)
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Run `adr list`."""
    return run_list_command(args, "adr", "ADRs", "adrs", pretty_text=True)
