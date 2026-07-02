"""`requirement create` command."""

from __future__ import annotations

import argparse
from pathlib import Path

from wn_dev_std.cli.commands.governance_common import (
    add_root_argument,
    context_from_args,
    optional_string_attr,
    print_catalog_failures,
    string_attr,
)
from wn_dev_std.cli.types import SubparserRegistry
from wn_dev_std.doc_governance import REQUIREMENT_STATUSES
from wn_dev_std.governance_mutation import GovernanceMutationError, create_requirement


def register(subparsers: SubparserRegistry) -> None:
    """Register the subcommand."""
    parser = subparsers.add_parser(
        "create",
        help="Create a compliant requirement",
        description="Create a compliant Wavenumber requirement document.",
    )
    parser.add_argument("requirement_id", help="Requirement id, for example core-req-0001")
    parser.add_argument("--domain", required=True, help="Governance domain")
    parser.add_argument("--title", required=True, help="Requirement title")
    parser.add_argument(
        "--status",
        choices=REQUIREMENT_STATUSES,
        default="draft",
        help="Requirement status",
    )
    parser.add_argument("--created", help="Creation date or timestamp")
    body_group = parser.add_mutually_exclusive_group()
    body_group.add_argument("--body", help="Initial Markdown body")
    body_group.add_argument("--body-file", help="Path to initial Markdown body")
    add_root_argument(parser)
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Run `requirement create`."""
    context = context_from_args(args)
    if print_catalog_failures(context):
        return 1
    try:
        result = create_requirement(
            context,
            string_attr(args, "requirement_id"),
            string_attr(args, "title"),
            domain=string_attr(args, "domain"),
            status=string_attr(args, "status"),
            created=optional_string_attr(args, "created"),
            body=_body_text(args),
        )
    except (GovernanceMutationError, OSError) as exc:
        print(str(exc))
        return 1
    print(f"{result.detail}: {result.path}")
    return 0


def _body_text(args: argparse.Namespace) -> str | None:
    body = optional_string_attr(args, "body")
    if body is not None:
        return body
    body_file = optional_string_attr(args, "body_file")
    if body_file is None:
        return None
    return Path(body_file).read_text(encoding="utf-8")
