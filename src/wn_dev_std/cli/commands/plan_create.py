"""`plan create` command."""

from __future__ import annotations

import argparse

from wn_dev_std.cli.commands.plan_common import (
    add_depends_on_argument,
    add_root_argument,
    context_from_args,
    optional_string_attr,
    print_catalog_failures,
    string_attr,
    string_list_attr,
)
from wn_dev_std.cli.types import SubparserRegistry
from wn_dev_std.plan_hygiene import PLAN_STATUSES
from wn_dev_std.plan_mutation import PlanMutationError, create_plan


def register(subparsers: SubparserRegistry) -> None:
    """Register the subcommand."""
    parser = subparsers.add_parser(
        "create",
        help="Create a compliant plan",
        description="Create a compliant plan document.",
    )
    parser.add_argument("plan_id", help="Plan id to create")
    parser.add_argument("--title", required=True, help="Plan title")
    parser.add_argument("--status", choices=PLAN_STATUSES, default="active", help="Plan status")
    parser.add_argument("--created", help="Creation date or timestamp")
    parser.add_argument("--plan-root", help="Configured plan root to write into")
    parser.add_argument("--body", help="Initial Markdown body after the title")
    add_depends_on_argument(parser)
    add_root_argument(parser)
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Run `plan create`."""
    context = context_from_args(args)
    if print_catalog_failures(context):
        return 1
    try:
        result = create_plan(
            context,
            string_attr(args, "plan_id"),
            string_attr(args, "title"),
            status=string_attr(args, "status"),
            created=optional_string_attr(args, "created"),
            depends_on=string_list_attr(args, "depends_on"),
            plan_root=optional_string_attr(args, "plan_root"),
            body=optional_string_attr(args, "body"),
        )
    except PlanMutationError as exc:
        print(str(exc))
        return 1
    print(f"{result.detail}: {result.path}")
    return 0
