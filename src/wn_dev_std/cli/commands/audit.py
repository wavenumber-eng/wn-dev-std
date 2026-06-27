"""Implementation of the `audit` command."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import cast

from wn_dev_std.checks import AUDIT_SCOPES, format_results, run_audit_checks
from wn_dev_std.cli.types import SubparserRegistry


def register(subparsers: SubparserRegistry) -> None:
    """Register the command with the root parser."""
    parser = subparsers.add_parser(
        "audit",
        help="Run repository audit checks",
        description="Run Wavenumber repository audit checks.",
    )
    add_audit_arguments(parser)
    parser.set_defaults(handler=run)


def add_audit_arguments(parser: argparse.ArgumentParser) -> None:
    """Add common audit arguments to a command parser."""
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Repository root to audit",
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=("text", "json"),
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--scope",
        dest="scopes",
        choices=AUDIT_SCOPES,
        action="append",
        default=None,
        help="Audit scope to run; may be passed more than once",
    )


def run(args: argparse.Namespace) -> int:
    """Run the command."""
    path = Path(_string_attr(args, "path"))
    output_format = _string_attr(args, "output_format")
    scopes = _scope_tuple(args)
    results = run_audit_checks(path, scopes)
    print(format_results(results, output_format))
    return 0 if all(result.passed for result in results) else 1


def _scope_tuple(args: argparse.Namespace) -> tuple[str, ...]:
    value = cast(list[object] | None, args.scopes)
    if value is None:
        return ("all",)
    scopes: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise TypeError("expected scope values to be strings")
        scopes.append(item)
    return tuple(scopes)


def _string_attr(args: argparse.Namespace, name: str) -> str:
    value = getattr(args, name)
    if isinstance(value, str):
        return value
    raise TypeError(f"expected {name} to be a string")
