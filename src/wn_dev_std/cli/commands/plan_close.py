"""`plan close` command."""

from __future__ import annotations

import argparse
from pathlib import Path

from wn_dev_std.cli.commands.plan_common import add_root_argument, context_from_args, string_attr
from wn_dev_std.cli.types import SubparserRegistry
from wn_dev_std.plan_closeout import (
    PlanCloseoutAssessment,
    PlanCloseoutError,
    assess_plan_closeout,
    delete_closed_plan,
)


def register(subparsers: SubparserRegistry) -> None:
    """Register the subcommand."""
    parser = subparsers.add_parser(
        "close",
        help="Check closeout readiness and remove a completed plan",
        description=(
            "Check that work, durable-document review, test-runtime review, and external "
            "review are complete; optionally delete the temporary plan and attached logs."
        ),
    )
    parser.add_argument("plan_id", help="Plan id to close")
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Confirm durable outcomes are recorded and delete the plan and attached logs",
    )
    add_root_argument(parser)
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Run `plan close`."""
    context = context_from_args(args)
    try:
        assessment = assess_plan_closeout(context, string_attr(args, "plan_id"))
    except PlanCloseoutError as exc:
        print(str(exc))
        return 1

    _print_assessment(assessment)
    if not assessment.ready:
        print("No files deleted. Complete the checklist, then run this command again.")
        return 1
    if not bool(getattr(args, "delete", False)):
        print(f"No files deleted. To finish: dev-std plan close {assessment.plan_id} --delete")
        return 0
    return _delete_plan(assessment, context.catalog.root)


def _print_assessment(assessment: PlanCloseoutAssessment) -> None:
    state = "ready" if assessment.ready else "not ready"
    print(f"Plan {assessment.plan_id} is {state} for closeout.")
    print("Closeout requirements:")
    print(
        "- Move durable outcomes into design docs, ADRs, requirements, tests, "
        "contracts, or release notes."
    )
    print("- Complete design-doc-intent-audit, test-runtime-impact-audit, and external-review.")
    if assessment.ready:
        print(f"- All {assessment.step_count} steps are done.")
        print(f"- All {assessment.exit_criterion_count} exit criteria are met.")
        print("- No active plan depends on this plan.")
        return
    for blocker in assessment.blockers:
        print(f"- BLOCKED: {blocker}")


def _delete_plan(assessment: PlanCloseoutAssessment, root: Path) -> int:
    try:
        deleted_paths = delete_closed_plan(assessment)
    except PlanCloseoutError as exc:
        print(str(exc))
        return 1
    print("Deleted temporary closeout files:")
    for path in deleted_paths:
        print(f"- {_relative_path(root, path)}")
    print("Next: dev-std audit . --scope docs.plans")
    return 0


def _relative_path(root: Path, path: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")
