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
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Run the command."""
    output_format = _output_format(args)
    if output_format == "json":
        print(json.dumps(version_report(), indent=2, sort_keys=True))
        return 0
    return run_text()


def run_text() -> int:
    """Print the default text version report."""
    report = version_report()
    print(f"wn-dev-std {report['wn-dev-std']}")
    print(f"python {report['python']}")
    print(f"wn-rack {report['wn-rack']}")
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
