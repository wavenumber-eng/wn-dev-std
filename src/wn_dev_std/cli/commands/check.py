"""Implementation of the `check` command."""

from __future__ import annotations

import argparse
from pathlib import Path

from wn_dev_std.checks import format_results, run_basic_checks
from wn_dev_std.cli.types import SubparserRegistry


def register(subparsers: SubparserRegistry) -> None:
    """Register the command with the root parser."""
    parser = subparsers.add_parser(
        "check",
        help="Run basic repository conformance checks",
        description="Run basic Wavenumber repository conformance checks.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Repository root to check",
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
    path = Path(_string_attr(args, "path"))
    output_format = _string_attr(args, "output_format")
    results = run_basic_checks(path)
    print(format_results(results, output_format))
    return 0 if all(result.passed for result in results) else 1


def _string_attr(args: argparse.Namespace, name: str) -> str:
    value = getattr(args, name)
    if isinstance(value, str):
        return value
    raise TypeError(f"expected {name} to be a string")
