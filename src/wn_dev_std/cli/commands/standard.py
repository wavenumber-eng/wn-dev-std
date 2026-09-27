"""Implementation of the `standard` command."""

from __future__ import annotations

import argparse
from typing import Literal, cast

from wn_dev_std.capability_standards import render_capability
from wn_dev_std.cli.types import SubparserRegistry
from wn_dev_std.standard_model import CapabilityName, ProfileName
from wn_dev_std.standards import render_standard


def register(subparsers: SubparserRegistry) -> None:
    """Register the command with the root parser."""
    parser = subparsers.add_parser(
        "standard",
        help="Print a standard profile summary",
        description="Print a project standard profile.",
    )
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument(
        "--profile",
        choices=(
            "python-package",
            "python-native-wasm",
            "cpp-library",
            "csharp-app",
            "javascript-web-app",
            "python-js-app",
            "typescript-web-app",
            "python-ts-app",
            "rust-app",
            "rust-firmware",
            "zephyr-firmware",
        ),
        default=None,
        help="Standard profile to render",
    )
    selection.add_argument(
        "--capability",
        choices=(
            "typespec-contracts",
            "activity-application",
            "backend-integration",
            "lit-web-application",
        ),
        default=None,
        help="Cross-cutting standard capability to render",
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
    capability = _capability(args)
    if capability is not None:
        print(render_capability(capability, _output_format(args)))
    else:
        print(render_standard(_profile(args), _output_format(args)))
    return 0


def _profile(args: argparse.Namespace) -> ProfileName:
    value = getattr(args, "profile", None)
    if value is None:
        return "python-package"
    if value in (
        "python-package",
        "python-native-wasm",
        "cpp-library",
        "csharp-app",
        "javascript-web-app",
        "python-js-app",
        "typescript-web-app",
        "python-ts-app",
        "rust-app",
        "rust-firmware",
        "zephyr-firmware",
    ):
        return value
    raise TypeError("expected profile to be a supported standard profile")


def _capability(args: argparse.Namespace) -> CapabilityName | None:
    value = getattr(args, "capability", None)
    if value is None:
        return None
    if value in (
        "typespec-contracts",
        "activity-application",
        "backend-integration",
        "lit-web-application",
    ):
        return value
    raise TypeError("expected capability to be a supported standard capability")


def _output_format(args: argparse.Namespace) -> Literal["text", "json"]:
    value = cast(str, args.output_format)
    if value in ("text", "json"):
        return value
    raise TypeError("expected output_format to be a string")
