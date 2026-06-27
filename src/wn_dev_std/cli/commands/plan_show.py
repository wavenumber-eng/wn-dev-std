"""`plan show` command."""

from __future__ import annotations

import argparse
import json

from wn_dev_std.cli.commands.plan_common import (
    add_format_argument,
    add_root_argument,
    context_from_args,
    find_plan,
    output_format,
    print_catalog_failures,
    string_attr,
)
from wn_dev_std.cli.types import SubparserRegistry
from wn_dev_std.plan_hygiene import PlanRecord, PlanStepRecord, read_document_body


def register(subparsers: SubparserRegistry) -> None:
    """Register the subcommand."""
    parser = subparsers.add_parser(
        "show",
        help="Show a compliant plan",
        description="Show a compliant Wavenumber plan document.",
    )
    parser.add_argument("plan_id", help="Plan id to show")
    add_root_argument(parser)
    add_format_argument(parser)
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Run `plan show`."""
    context = context_from_args(args)
    if print_catalog_failures(context):
        return 1
    plan_id = string_attr(args, "plan_id")
    plan = find_plan(context.catalog, plan_id)
    if plan is None:
        print(f"plan not found: {plan_id}")
        return 1
    body = read_document_body(context.catalog.root, plan.relative_path)
    if output_format(args) == "json":
        print(json.dumps(_plan_payload(plan, body), indent=2, sort_keys=True))
        return 0
    print(_format_plan_show_text(plan, body))
    return 0


def _plan_payload(plan: PlanRecord, body: str) -> dict[str, object]:
    return {
        "id": plan.plan_id,
        "status": plan.status,
        "created": plan.created,
        "path": plan.relative_path,
        "depends_on": list(plan.depends_on),
        "steps": [_step_payload(step) for step in plan.steps],
        "body": body,
    }


def _step_payload(step: PlanStepRecord) -> dict[str, object]:
    return {
        "id": step.step_id,
        "title": step.title,
        "status": step.status,
        "depends_on": list(step.depends_on),
    }


def _format_plan_show_text(plan: PlanRecord, body: str) -> str:
    lines = [
        f"Plan: {plan.plan_id}",
        f"Status: {plan.status}",
        f"Created: {plan.created}",
        f"Path: {plan.relative_path}",
    ]
    if plan.depends_on:
        lines.append("Depends on: " + ", ".join(plan.depends_on))
    if plan.steps:
        lines.append("Steps:")
        for step in plan.steps:
            depends = "" if not step.depends_on else f" depends_on={','.join(step.depends_on)}"
            lines.append(f"- {step.step_id} [{step.status}] {step.title}{depends}")
    if body:
        lines.extend(["", body])
    return "\n".join(lines)
