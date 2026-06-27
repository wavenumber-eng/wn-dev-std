"""`plan list` command."""

from __future__ import annotations

import argparse
import json

from wn_dev_std.cli.commands.plan_common import (
    add_format_argument,
    add_root_argument,
    context_from_args,
    output_format,
    print_catalog_failures,
)
from wn_dev_std.cli.types import SubparserRegistry
from wn_dev_std.plan_hygiene import PlanRecord, PlanStepRecord
from wn_dev_std.plan_reader import PlanReadContext


def register(subparsers: SubparserRegistry) -> None:
    """Register the subcommand."""
    parser = subparsers.add_parser(
        "list",
        help="List compliant plans",
        description="List compliant Wavenumber plan documents.",
    )
    add_root_argument(parser)
    add_format_argument(parser)
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Run `plan list`."""
    context = context_from_args(args)
    if print_catalog_failures(context):
        return 1
    if output_format(args) == "json":
        print(json.dumps(_plans_payload(context), indent=2, sort_keys=True))
        return 0
    print(_format_plan_list_text(context))
    return 0


def _plans_payload(context: PlanReadContext) -> dict[str, object]:
    return {
        "root": str(context.catalog.root),
        "marker": context.discovered_root.marker,
        "plans": [_plan_payload(plan) for plan in context.catalog.plans],
    }


def _plan_payload(plan: PlanRecord) -> dict[str, object]:
    return {
        "id": plan.plan_id,
        "status": plan.status,
        "created": plan.created,
        "path": plan.relative_path,
        "depends_on": list(plan.depends_on),
        "steps": [_step_payload(step) for step in plan.steps],
    }


def _step_payload(step: PlanStepRecord) -> dict[str, object]:
    return {
        "id": step.step_id,
        "title": step.title,
        "status": step.status,
        "depends_on": list(step.depends_on),
    }


def _format_plan_list_text(context: PlanReadContext) -> str:
    if not context.catalog.plans:
        return f"No compliant plans found under {context.catalog.root}"
    lines = [f"Plans under {context.catalog.root}:"]
    for plan in context.catalog.plans:
        depends = "" if not plan.depends_on else f" depends_on={','.join(plan.depends_on)}"
        step_count = "" if not plan.steps else f" steps={_step_summary(plan.steps)}"
        lines.append(f"- {plan.plan_id} [{plan.status}] {plan.relative_path}{depends}{step_count}")
    return "\n".join(lines)


def _step_summary(steps: tuple[PlanStepRecord, ...]) -> str:
    counts: dict[str, int] = {}
    for step in steps:
        counts[step.status] = counts.get(step.status, 0) + 1
    return ",".join(f"{status}:{counts[status]}" for status in sorted(counts))
