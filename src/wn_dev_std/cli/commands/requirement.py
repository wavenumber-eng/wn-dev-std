"""Requirement command registry."""

from __future__ import annotations

import argparse
from typing import cast

from wn_dev_std.cli.commands import requirement_create, requirement_list, requirement_show
from wn_dev_std.cli.types import SubparserRegistry


def register(subparsers: SubparserRegistry) -> None:
    """Register the command with the root parser."""
    parser = subparsers.add_parser(
        "requirement",
        help="Read and create compliant requirements",
        description="Read and create compliant Wavenumber requirement documents.",
    )
    command_parsers = parser.add_subparsers(
        dest="requirement_command",
        metavar="<requirement-command>",
    )
    requirement_create.register(command_parsers)
    requirement_list.register(command_parsers)
    requirement_show.register(command_parsers)
    parser.set_defaults(handler=run_help, parser=parser)


def run_help(args: argparse.Namespace) -> int:
    """Print command help when no subcommand is selected."""
    parser = cast(argparse.ArgumentParser, args.parser)
    parser.print_help()
    return 0
