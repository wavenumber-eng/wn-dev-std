"""Implementation of the compatibility `check` command."""

from __future__ import annotations

import argparse

from wn_dev_std.cli.commands.audit import add_audit_arguments
from wn_dev_std.cli.commands.audit import run as run_audit
from wn_dev_std.cli.types import SubparserRegistry


def register(subparsers: SubparserRegistry) -> None:
    """Register the command with the root parser."""
    parser = subparsers.add_parser(
        "check",
        help="Compatibility alias for audit",
        description="Run repository audit checks.",
    )
    add_audit_arguments(parser)
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Run the command."""
    return run_audit(args)
