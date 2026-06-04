"""Implementation of the `standard` command."""

from __future__ import annotations

import argparse
from typing import Literal, cast

from wn_dev_std.cli.types import SubparserRegistry
from wn_dev_std.standards import render_python_standard


def register(subparsers: SubparserRegistry) -> None:
    """Register the command with the root parser."""
    parser = subparsers.add_parser(
        "standard",
        help="Print the current Python standard summary",
        description="Print the current Wavenumber Python package standard.",
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=("text", "json"),
        default="text",
        help="Output format",
    )
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Run the command."""
    print(render_python_standard(_output_format(args)))
    return 0


def _output_format(args: argparse.Namespace) -> Literal["text", "json"]:
    value = cast(str, args.output_format)
    if value in ("text", "json"):
        return value
    raise TypeError("expected output_format to be a string")
