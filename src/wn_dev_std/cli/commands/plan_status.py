"""`plan status` command."""

from __future__ import annotations

import argparse

from wn_dev_std.cli.commands.plan_common import (
    add_root_argument,
    context_from_args,
    print_catalog_failures,
    string_attr,
)
from wn_dev_std.cli.types import SubparserRegistry
from wn_dev_std.plan_hygiene import PLAN_STATUSES
from wn_dev_std.plan_mutation import PlanMutationError, set_plan_status


def register(subparsers: SubparserRegistry) -> None:
    """Register the subcommand."""
    parser = subparsers.add_parser(
        "status",
        help="Set a plan status",
        description="Set a compliant plan document status.",
    )
    parser.add_argument("plan_id", help="Plan id to update")
    parser.add_argument("status", choices=PLAN_STATUSES, help="New plan status")
    add_root_argument(parser)
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Run `plan status`."""
    context = context_from_args(args)
    if print_catalog_failures(context):
        return 1
    try:
        result = set_plan_status(context, string_attr(args, "plan_id"), string_attr(args, "status"))
    except PlanMutationError as exc:
        print(str(exc))
        return 1
    print(f"{result.detail}: {result.path}")
    return 0
