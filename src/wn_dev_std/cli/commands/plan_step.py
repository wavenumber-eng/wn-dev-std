"""`plan step` command."""

from __future__ import annotations

import argparse
import json
from typing import cast

from wn_dev_std.cli.commands.plan_common import (
    add_depends_on_argument,
    add_format_argument,
    add_root_argument,
    context_from_args,
    find_plan,
    output_format,
    print_catalog_failures,
    string_attr,
    string_list_attr,
)
from wn_dev_std.cli.types import SubparserRegistry
from wn_dev_std.plan_hygiene import PLAN_STEP_STATUSES, PlanStepRecord
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
    _register_list(step_parsers)
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


def _register_list(subparsers: SubparserRegistry) -> None:
    parser = subparsers.add_parser(
        "list",
        help="List plan steps",
        description="List structured step ids for a compliant plan.",
    )
    parser.add_argument("plan_id", help="Plan id whose steps should be listed")
    add_root_argument(parser)
    add_format_argument(parser)
    parser.set_defaults(handler=run_list)


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


def run_list(args: argparse.Namespace) -> int:
    """Run `plan step list`."""
    context = context_from_args(args)
    if print_catalog_failures(context):
        return 1
    plan_id = string_attr(args, "plan_id")
    plan = find_plan(context.catalog, plan_id)
    if plan is None:
        print(f"plan not found: {plan_id}")
        return 1
    if output_format(args) == "json":
        print(json.dumps(_step_list_payload(plan_id, plan.steps), indent=2, sort_keys=True))
        return 0
    print(_format_step_list_text(plan_id, plan.steps))
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


def _step_list_payload(
    plan_id: str,
    steps: tuple[PlanStepRecord, ...],
) -> dict[str, object]:
    return {
        "plan_id": plan_id,
        "steps": [
            {
                "id": step.step_id,
                "title": step.title,
                "status": step.status,
                "depends_on": list(step.depends_on),
            }
            for step in steps
        ],
    }


def _format_step_list_text(plan_id: str, steps: tuple[PlanStepRecord, ...]) -> str:
    if not steps:
        return f"No compliant steps found for plan {plan_id}"
    lines = [f"Steps for {plan_id}:"]
    for step in steps:
        depends = "" if not step.depends_on else f" depends_on={','.join(step.depends_on)}"
        lines.append(f"- {step.step_id} [{step.status}] {step.title}{depends}")
    return "\n".join(lines)
