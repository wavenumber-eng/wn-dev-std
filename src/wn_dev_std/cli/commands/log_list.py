"""`log list` command."""

from __future__ import annotations

import argparse
import json

from wn_dev_std.cli.commands.plan_common import (
    add_format_argument,
    add_root_argument,
    context_from_args,
    output_format,
    print_catalog_failures,
    string_attr,
)
from wn_dev_std.cli.types import SubparserRegistry
from wn_dev_std.plan_hygiene import LogRecord, PlanCatalog, read_document_body
from wn_dev_std.plan_reader import PlanReadContext


def register(subparsers: SubparserRegistry) -> None:
    """Register the subcommand."""
    parser = subparsers.add_parser(
        "list",
        help="List logs for a plan",
        description="List compliant work logs for a plan.",
    )
    parser.add_argument("plan_id", help="Plan id whose logs should be listed")
    add_root_argument(parser)
    add_format_argument(parser)
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Run `log list`."""
    context = context_from_args(args)
    if print_catalog_failures(context):
        return 1
    plan_id = string_attr(args, "plan_id")
    if not _has_plan(context.catalog, plan_id):
        print(f"plan not found: {plan_id}")
        return 1
    logs = tuple(log for log in context.catalog.logs if log.plan_id == plan_id)
    if output_format(args) == "json":
        print(json.dumps(_logs_payload(context, plan_id, logs), indent=2, sort_keys=True))
        return 0
    print(_format_log_list_text(context, plan_id, logs))
    return 0


def _logs_payload(
    context: PlanReadContext,
    plan_id: str,
    logs: tuple[LogRecord, ...],
) -> dict[str, object]:
    return {
        "root": str(context.catalog.root),
        "marker": context.discovered_root.marker,
        "plan_id": plan_id,
        "logs": [_log_payload(context.catalog, log) for log in logs],
    }


def _log_payload(catalog: PlanCatalog, log: LogRecord) -> dict[str, object]:
    return {
        "id": log.log_id,
        "plan_id": log.plan_id,
        "created": log.created,
        "path": log.relative_path,
        "body": read_document_body(catalog.root, log.relative_path),
    }


def _format_log_list_text(
    context: PlanReadContext,
    plan_id: str,
    logs: tuple[LogRecord, ...],
) -> str:
    if not logs:
        return f"No compliant logs found for plan {plan_id}"
    lines = [f"Logs for {plan_id} under {context.catalog.root}:"]
    for log in logs:
        lines.append(f"- {log.log_id} [{log.created}] {log.relative_path}")
    return "\n".join(lines)


def _has_plan(catalog: PlanCatalog, plan_id: str) -> bool:
    return any(plan.plan_id == plan_id for plan in catalog.plans)
