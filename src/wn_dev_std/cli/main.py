"""Thin command-line entry point for `dev-std`."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from typing import Protocol, cast

from wn_dev_std.cli.commands import audit, check, standard, version


class CommandHandler(Protocol):
    """Callable command handler protocol."""

    def __call__(self, args: argparse.Namespace) -> int:
        """Run a parsed command."""
        ...


def build_parser() -> argparse.ArgumentParser:
    """Build the public CLI parser."""
    parser = argparse.ArgumentParser(
        description="Wavenumber development standards reference tool",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print version information and exit",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="<command>")
    audit.register(subparsers)
    check.register(subparsers)
    standard.register(subparsers)
    version.register(subparsers)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        return version.run_text()

    handler = cast(CommandHandler | None, getattr(args, "handler", None))
    if handler is None:
        parser.print_help()
        return 0
    return handler(args)
