"""Read-only plan commands."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Literal, cast

from wn_dev_std.cli.types import SubparserRegistry
from wn_dev_std.plan_hygiene import PlanCatalog, PlanRecord, PlanStepRecord, read_document_body
from wn_dev_std.plan_reader import PlanReadContext, load_plan_read_context


def register(subparsers: SubparserRegistry) -> None:
    """Register the command with the root parser."""
    parser = subparsers.add_parser(
        "plan",
        help="Read compliant plans",
        description="Read compliant Wavenumber plan documents.",
    )
    command_parsers = parser.add_subparsers(dest="plan_command", metavar="<plan-command>")
    _register_list(command_parsers)
    _register_show(command_parsers)
    parser.set_defaults(handler=run_help, parser=parser)


def _register_list(subparsers: SubparserRegistry) -> None:
    parser = subparsers.add_parser(
        "list",
        help="List compliant plans",
        description="List compliant Wavenumber plan documents.",
    )
    _add_root_argument(parser)
    _add_format_argument(parser)
    parser.set_defaults(handler=run_list)


def _register_show(subparsers: SubparserRegistry) -> None:
    parser = subparsers.add_parser(
        "show",
        help="Show a compliant plan",
        description="Show a compliant Wavenumber plan document.",
    )
    parser.add_argument("plan_id", help="Plan id to show")
    _add_root_argument(parser)
    _add_format_argument(parser)
    parser.set_defaults(handler=run_show)


def run_help(args: argparse.Namespace) -> int:
    """Print command help when no subcommand is selected."""
    parser = cast(argparse.ArgumentParser, args.parser)
    parser.print_help()
    return 0


def run_list(args: argparse.Namespace) -> int:
    """Run `plan list`."""
    context = _context_from_args(args)
    if _print_catalog_failures(context):
        return 1
    output_format = _output_format(args)
    if output_format == "json":
        print(json.dumps(_plans_payload(context), indent=2, sort_keys=True))
        return 0
    print(_format_plan_list_text(context))
    return 0


def run_show(args: argparse.Namespace) -> int:
    """Run `plan show`."""
    context = _context_from_args(args)
    if _print_catalog_failures(context):
        return 1
    plan_id = _string_attr(args, "plan_id")
    plan = _find_plan(context.catalog, plan_id)
    if plan is None:
        print(f"plan not found: {plan_id}")
        return 1
    body = read_document_body(context.catalog.root, plan.relative_path)
    output_format = _output_format(args)
    if output_format == "json":
        print(json.dumps(_plan_payload(plan, body), indent=2, sort_keys=True))
        return 0
    print(_format_plan_show_text(plan, body))
    return 0


def _context_from_args(args: argparse.Namespace) -> PlanReadContext:
    return load_plan_read_context(Path(_string_attr(args, "root")))


def _add_root_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--root",
        default=".",
        help="Start path for project root discovery",
    )


def _add_format_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=("text", "json"),
        default="text",
        help="Output format",
    )


def _print_catalog_failures(context: PlanReadContext) -> bool:
    if not context.catalog.failures:
        return False
    print("plan catalog is not compliant:")
    for failure in context.catalog.failures:
        print(f"- {failure}")
    return True


def _plans_payload(context: PlanReadContext) -> dict[str, object]:
    return {
        "root": str(context.catalog.root),
        "marker": context.discovered_root.marker,
        "plans": [_plan_payload(plan, None) for plan in context.catalog.plans],
    }


def _plan_payload(plan: PlanRecord, body: str | None) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": plan.plan_id,
        "status": plan.status,
        "created": plan.created,
        "path": plan.relative_path,
        "depends_on": list(plan.depends_on),
        "steps": [_step_payload(step) for step in plan.steps],
    }
    if body is not None:
        payload["body"] = body
    return payload


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


def _find_plan(catalog: PlanCatalog, plan_id: str) -> PlanRecord | None:
    for plan in catalog.plans:
        if plan.plan_id == plan_id:
            return plan
    return None


def _step_summary(steps: tuple[PlanStepRecord, ...]) -> str:
    counts: dict[str, int] = {}
    for step in steps:
        counts[step.status] = counts.get(step.status, 0) + 1
    return ",".join(f"{status}:{counts[status]}" for status in sorted(counts))


def _output_format(args: argparse.Namespace) -> Literal["text", "json"]:
    value = _string_attr(args, "output_format")
    if value in ("text", "json"):
        return value
    raise TypeError("expected output_format to be text or json")


def _string_attr(args: argparse.Namespace, name: str) -> str:
    value = getattr(args, name)
    if isinstance(value, str):
        return value
    raise TypeError(f"expected {name} to be a string")
