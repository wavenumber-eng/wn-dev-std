"""Template command registry."""

from __future__ import annotations

import argparse
from typing import cast

from wn_dev_std.cli.commands import template_copy, template_list
from wn_dev_std.cli.types import SubparserRegistry


def register(subparsers: SubparserRegistry) -> None:
    """Register the command with the root parser."""
    parser = subparsers.add_parser(
        "template",
        help="List and copy version-matched project templates",
        description="List and copy version-matched, project-owned templates.",
    )
    command_parsers = parser.add_subparsers(dest="template_command", metavar="<template-command>")
    template_list.register(command_parsers)
    template_copy.register(command_parsers)
    parser.set_defaults(handler=run_help, parser=parser)


def run_help(args: argparse.Namespace) -> int:
    """Print command help when no subcommand is selected."""
    parser = cast(argparse.ArgumentParser, args.parser)
    parser.print_help()
    return 0
