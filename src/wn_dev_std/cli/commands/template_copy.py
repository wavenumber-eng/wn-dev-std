"""`template copy` command."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import cast

from wn_dev_std.cli.types import SubparserRegistry
from wn_dev_std.template_library import TemplateName, copy_template


def register(subparsers: SubparserRegistry) -> None:
    """Register the subcommand."""
    parser = subparsers.add_parser(
        "copy",
        help="Copy a template into a new project-owned directory",
        description="Copy a template into a new project-owned directory without overwriting files.",
    )
    parser.add_argument("name", choices=("typespec-contract", "lit-activity-web"))
    parser.add_argument("destination", type=Path)
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Run `template copy`."""
    name = cast(TemplateName, args.name)
    destination = cast(Path, args.destination)
    try:
        copied = copy_template(name, destination)
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        print(f"template copy failed: {exc}")
        return 1
    print(f"Copied {name} to {copied}")
    print("The copy is project-owned; rename sample identities and review dev-std.toml before use.")
    return 0
