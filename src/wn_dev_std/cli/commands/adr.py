"""ADR command registry."""

from __future__ import annotations

import argparse
from typing import cast

from wn_dev_std.cli.commands import adr_list, adr_show
from wn_dev_std.cli.types import SubparserRegistry


def register(subparsers: SubparserRegistry) -> None:
    """Register the command with the root parser."""
    parser = subparsers.add_parser(
        "adr",
        help="Read compliant ADRs",
        description="Read compliant Wavenumber ADR documents.",
    )
    command_parsers = parser.add_subparsers(dest="adr_command", metavar="<adr-command>")
    adr_list.register(command_parsers)
    adr_show.register(command_parsers)
    parser.set_defaults(handler=run_help, parser=parser)


def run_help(args: argparse.Namespace) -> int:
    """Print command help when no subcommand is selected."""
    parser = cast(argparse.ArgumentParser, args.parser)
    parser.print_help()
    return 0
