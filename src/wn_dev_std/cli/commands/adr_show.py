"""`adr show` command."""

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
        help="Show a compliant ADR",
        description="Show a compliant Wavenumber ADR document.",
    )
    parser.add_argument("adr_id", help="ADR id to show")
    add_root_argument(parser)
    add_format_argument(parser)
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Run `adr show`."""
    return run_show_command(args, "adr", "ADR", "adr_id")
