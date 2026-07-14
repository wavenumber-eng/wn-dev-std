"""Implementation of the `audit` command."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import cast

from wn_dev_std import __version__
from wn_dev_std.audit_config import AUDIT_SCOPES
from wn_dev_std.checks import format_results, run_audit_checks
from wn_dev_std.checks_types import CheckResult
from wn_dev_std.cli.types import SubparserRegistry
from wn_dev_std.version_check import UpstreamVersionCheck, check_pypi_version


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
    parser.add_argument(
        "--check-upstream-version",
        action="store_true",
        help="Warn when a newer wn-dev-std release is available on PyPI",
    )


def run(args: argparse.Namespace) -> int:
    """Run the command."""
    path = Path(_string_attr(args, "path"))
    output_format = _string_attr(args, "output_format")
    scopes = _scope_tuple(args)
    results = run_audit_checks(path, scopes)
    if bool(getattr(args, "check_upstream_version", False)):
        upstream = check_pypi_version(__version__)
        results = (*results, upstream_check_result(upstream))
    print(format_results(results, output_format))
    return 0 if all(result.passed for result in results) else 1


def _scope_tuple(args: argparse.Namespace) -> tuple[str, ...] | None:
    value = cast(list[object] | None, args.scopes)
    if value is None:
        return None
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


def upstream_check_result(upstream: UpstreamVersionCheck) -> CheckResult:
    """Convert an upstream version probe into a non-failing audit result."""
    return CheckResult(
        "upstream version",
        True,
        upstream.detail,
        "repo",
        warning=upstream.warning is not None or upstream.is_outdated,
    )
