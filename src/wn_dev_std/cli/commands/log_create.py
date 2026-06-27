"""`log create` command."""

from __future__ import annotations

import argparse

from wn_dev_std.cli.commands.plan_common import (
    add_root_argument,
    context_from_args,
    optional_string_attr,
    print_catalog_failures,
    string_attr,
)
from wn_dev_std.cli.types import SubparserRegistry
from wn_dev_std.plan_mutation import PlanMutationError, create_plan_log


def register(subparsers: SubparserRegistry) -> None:
    """Register the subcommand."""
    parser = subparsers.add_parser(
        "create",
        help="Create a plan log",
        description="Create a compliant work log attached to a plan.",
    )
    parser.add_argument("plan_id", help="Plan id to log against")
    parser.add_argument("--body", required=True, help="Markdown log body")
    parser.add_argument("--id", dest="log_id", help="Log id")
    parser.add_argument("--created", help="Creation timestamp")
    add_root_argument(parser)
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Run `log create`."""
    context = context_from_args(args)
    if print_catalog_failures(context):
        return 1
    try:
        result = create_plan_log(
            context,
            string_attr(args, "plan_id"),
            string_attr(args, "body"),
            log_id=optional_string_attr(args, "log_id"),
            created=optional_string_attr(args, "created"),
        )
    except PlanMutationError as exc:
        print(str(exc))
        return 1
    print(f"{result.detail}: {result.path}")
    return 0
