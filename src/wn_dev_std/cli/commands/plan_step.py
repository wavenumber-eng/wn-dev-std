"""`plan step` command."""

from __future__ import annotations

import argparse
from typing import cast

from wn_dev_std.cli.commands.plan_common import (
    add_depends_on_argument,
    add_root_argument,
    context_from_args,
    print_catalog_failures,
    string_attr,
    string_list_attr,
)
from wn_dev_std.cli.types import SubparserRegistry
from wn_dev_std.plan_hygiene import PLAN_STEP_STATUSES
from wn_dev_std.plan_mutation import PlanMutationError, add_plan_step, set_plan_step_status


def register(subparsers: SubparserRegistry) -> None:
    """Register the subcommand."""
    parser = subparsers.add_parser(
        "step",
        help="Update plan steps",
        description="Add and update structured plan steps.",
    )
    step_parsers = parser.add_subparsers(dest="step_command", metavar="<step-command>")
    _register_add(step_parsers)
    _register_status(step_parsers)
    parser.set_defaults(handler=run_help, parser=parser)


def _register_add(subparsers: SubparserRegistry) -> None:
    parser = subparsers.add_parser(
        "add",
        help="Add a plan step",
        description="Add a structured step to a compliant plan.",
    )
    parser.add_argument("plan_id", help="Plan id to update")
    parser.add_argument("step_id", help="Step id to add")
    parser.add_argument("--title", required=True, help="Step title")
    parser.add_argument(
        "--status",
        choices=PLAN_STEP_STATUSES,
        default="pending",
        help="Initial step status",
    )
    add_depends_on_argument(parser)
    add_root_argument(parser)
    parser.set_defaults(handler=run_add)


def _register_status(subparsers: SubparserRegistry) -> None:
    parser = subparsers.add_parser(
        "status",
        help="Set a step status",
        description="Set an existing structured step status.",
    )
    parser.add_argument("plan_id", help="Plan id to update")
    parser.add_argument("step_id", help="Step id to update")
    parser.add_argument("status", choices=PLAN_STEP_STATUSES, help="New step status")
    add_root_argument(parser)
    parser.set_defaults(handler=run_status)


def run_help(args: argparse.Namespace) -> int:
    """Print command help when no subcommand is selected."""
    parser = cast(argparse.ArgumentParser, args.parser)
    parser.print_help()
    return 0


def run_add(args: argparse.Namespace) -> int:
    """Run `plan step add`."""
    context = context_from_args(args)
    if print_catalog_failures(context):
        return 1
    try:
        result = add_plan_step(
            context,
            string_attr(args, "plan_id"),
            string_attr(args, "step_id"),
            string_attr(args, "title"),
            status=string_attr(args, "status"),
            depends_on=string_list_attr(args, "depends_on"),
        )
    except PlanMutationError as exc:
        print(str(exc))
        return 1
    print(f"{result.detail}: {result.path}")
    return 0


def run_status(args: argparse.Namespace) -> int:
    """Run `plan step status`."""
    context = context_from_args(args)
    if print_catalog_failures(context):
        return 1
    try:
        result = set_plan_step_status(
            context,
            string_attr(args, "plan_id"),
            string_attr(args, "step_id"),
            string_attr(args, "status"),
        )
    except PlanMutationError as exc:
        print(str(exc))
        return 1
    print(f"{result.detail}: {result.path}")
    return 0
