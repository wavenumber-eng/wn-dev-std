"""Work-log command registry."""

from __future__ import annotations

import argparse
from typing import cast

from wn_dev_std.cli.commands import log_create, log_list
from wn_dev_std.cli.types import SubparserRegistry


def register(subparsers: SubparserRegistry) -> None:
    """Register the command with the root parser."""
    parser = subparsers.add_parser(
        "log",
        help="Read and create compliant plan logs",
        description="Read and create compliant Wavenumber plan work logs.",
    )
    command_parsers = parser.add_subparsers(dest="log_command", metavar="<log-command>")
    log_create.register(command_parsers)
    log_list.register(command_parsers)
    parser.set_defaults(handler=run_help, parser=parser)


def run_help(args: argparse.Namespace) -> int:
    """Print command help when no subcommand is selected."""
    parser = cast(argparse.ArgumentParser, args.parser)
    parser.print_help()
    return 0
