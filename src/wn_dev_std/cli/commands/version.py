"""Implementation of version reporting."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from importlib import metadata
from typing import Literal, cast

from wn_dev_std import __version__
from wn_dev_std.cli.types import SubparserRegistry
from wn_dev_std.version_check import UpstreamVersionCheck, check_pypi_version


def register(subparsers: SubparserRegistry) -> None:
    """Register the command with the root parser."""
    parser = subparsers.add_parser(
        "version",
        help="Print version information",
        description="Print wn-dev-std and major dependency versions.",
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=("text", "json"),
        default="text",
        help="Output format",
    )
    parser.add_argument(
        "--check-upstream",
        action="store_true",
        help="Warn when a newer wn-dev-std release is available on PyPI",
    )
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Run the command."""
    output_format = _output_format(args)
    upstream = _upstream_check(args)
    if output_format == "json":
        report: dict[str, object] = dict(version_report())
        if upstream is not None:
            report["upstream"] = _upstream_payload(upstream)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    return run_text(upstream)


def run_text(upstream: UpstreamVersionCheck | None = None) -> int:
    """Print the default text version report."""
    report = version_report()
    print(f"wn-dev-std {report['wn-dev-std']}")
    print(f"python {report['python']}")
    print(f"wn-rack {report['wn-rack']}")
    if upstream is not None:
        marker = "WARN" if upstream.warning is not None or upstream.is_outdated else "PASS"
        print(f"[{marker}] upstream version: {upstream.detail}")
    return 0


def version_report() -> dict[str, str]:
    """Return version data for the tool and major internal dependencies."""
    return {
        "wn-dev-std": __version__,
        "python": f"{platform.python_implementation()} {sys.version.split()[0]}",
        "wn-rack": _package_version("wn-rack"),
    }


def _package_version(distribution: str) -> str:
    try:
        return metadata.version(distribution)
    except metadata.PackageNotFoundError:
        return "not installed"


def _output_format(args: argparse.Namespace) -> Literal["text", "json"]:
    value = cast(str, args.output_format)
    if value in ("text", "json"):
        return value
    raise TypeError("expected output_format to be a string")


def _upstream_check(args: argparse.Namespace) -> UpstreamVersionCheck | None:
    if bool(getattr(args, "check_upstream", False)):
        return check_pypi_version(__version__)
    return None


def _upstream_payload(upstream: UpstreamVersionCheck) -> dict[str, object]:
    return {
        "source": "pypi",
        "installed": upstream.installed,
        "latest": upstream.latest,
        "outdated": upstream.is_outdated,
        "warning": upstream.warning,
        "detail": upstream.detail,
    }
