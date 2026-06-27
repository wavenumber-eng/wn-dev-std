"""Plan command registry."""

from __future__ import annotations

import argparse
from typing import cast

from wn_dev_std.cli.commands import plan_create, plan_list, plan_show, plan_status, plan_step
from wn_dev_std.cli.types import SubparserRegistry


def register(subparsers: SubparserRegistry) -> None:
    """Register the command with the root parser."""
    parser = subparsers.add_parser(
        "plan",
        help="Read and update compliant plans",
        description="Read and update compliant Wavenumber plan documents.",
    )
    command_parsers = parser.add_subparsers(dest="plan_command", metavar="<plan-command>")
    plan_create.register(command_parsers)
    plan_list.register(command_parsers)
    plan_show.register(command_parsers)
    plan_status.register(command_parsers)
    plan_step.register(command_parsers)
    parser.set_defaults(handler=run_help, parser=parser)


def run_help(args: argparse.Namespace) -> int:
    """Print command help when no subcommand is selected."""
    parser = cast(argparse.ArgumentParser, args.parser)
    parser.print_help()
    return 0
