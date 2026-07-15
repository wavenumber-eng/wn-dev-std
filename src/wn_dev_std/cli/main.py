"""Thin command-line entry point for `dev-std`."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Generator, Sequence
from contextlib import contextmanager
from typing import Protocol, TextIO, cast

from wn_dev_std.cli.commands import (
    adr,
    audit,
    check,
    governance,
    log,
    plan,
    requirement,
    standard,
    version,
)


class CommandHandler(Protocol):
    """Callable command handler protocol."""

    def __call__(self, args: argparse.Namespace) -> int:
        """Run a parsed command."""
        ...


class _PaddedStdout:
    """Stdout wrapper that pads human-visible command output."""

    def __init__(self, wrapped: TextIO) -> None:
        self._wrapped = wrapped
        self._started = False
        self._trailing_newlines = 0

    def write(self, text: str) -> int:
        """Write text with one blank line before first command output."""
        if text and not self._started:
            self._wrapped.write("\n")
            self._started = True
            self._trailing_newlines = 1
        written = self._wrapped.write(text)
        self._update_trailing_newlines(text)
        return written

    def flush(self) -> None:
        """Flush the wrapped stream."""
        self._wrapped.flush()

    def isatty(self) -> bool:
        """Delegate TTY detection so command color rules keep working."""
        return self._wrapped.isatty()

    def finish(self) -> None:
        """Ensure one blank padding line after the last output line."""
        if not self._started:
            return
        if self._trailing_newlines < 2:
            self._wrapped.write("\n" * (2 - self._trailing_newlines))
        self._wrapped.flush()

    def _update_trailing_newlines(self, text: str) -> None:
        if not text:
            return
        if not text.endswith("\n"):
            self._trailing_newlines = 0
            return
        trailing_newlines = len(text) - len(text.rstrip("\n"))
        if trailing_newlines == len(text):
            self._trailing_newlines += trailing_newlines
        else:
            self._trailing_newlines = trailing_newlines

    def __getattr__(self, name: str) -> object:
        """Delegate stream attributes such as encoding and errors."""
        return getattr(self._wrapped, name)


@contextmanager
def _padded_stdout() -> Generator[None]:
    original_stdout = sys.stdout
    padded_stdout = _PaddedStdout(original_stdout)
    sys.stdout = cast(TextIO, padded_stdout)
    try:
        yield
    finally:
        padded_stdout.finish()
        sys.stdout = original_stdout


def build_parser() -> argparse.ArgumentParser:
    """Build the public CLI parser."""
    parser = argparse.ArgumentParser(
        description="Development standards reference tool",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print version information and exit",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="<command>")
    adr.register(subparsers)
    audit.register(subparsers)
    check.register(subparsers)
    governance.register(subparsers)
    log.register(subparsers)
    plan.register(subparsers)
    requirement.register(subparsers)
    standard.register(subparsers)
    version.register(subparsers)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface."""
    parser = build_parser()
    with _padded_stdout():
        args = parser.parse_args(argv)

        if args.version:
            return version.run_text()

        handler = cast(CommandHandler | None, getattr(args, "handler", None))
        if handler is None:
            parser.print_help()
            return 0
        return handler(args)
