"""Governance command registry."""

from __future__ import annotations

import argparse
from typing import cast

from wn_dev_std.cli.commands import governance_html
from wn_dev_std.cli.types import SubparserRegistry


def register(subparsers: SubparserRegistry) -> None:
    """Register the governance command."""
    parser = subparsers.add_parser(
        "governance",
        aliases=["gov"],
        help="Generate governance documentation",
        description="Generate browseable governance documentation.",
    )
    command_parsers = parser.add_subparsers(
        dest="governance_command",
        metavar="<governance-command>",
    )
    governance_html.register(command_parsers)
    parser.set_defaults(handler=run_help, parser=parser)


def run_help(args: argparse.Namespace) -> int:
    """Print command help when no subcommand is selected."""
    parser = cast(argparse.ArgumentParser, args.parser)
    parser.print_help()
    return 0
