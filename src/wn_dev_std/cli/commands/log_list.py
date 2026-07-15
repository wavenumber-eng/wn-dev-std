"""`log list` command."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from wn_dev_std.cli.commands.log_text import (
    LOG_ENTRY_VALUE_INDENT,
    role_style,
)
from wn_dev_std.cli.commands.plan_common import (
    add_format_argument,
    add_root_argument,
    context_from_args,
    optional_string_attr,
    output_format,
    print_catalog_failures,
)
from wn_dev_std.cli.commands.text_format import (
    MAX_TEXT_WIDTH,
    normalized_width,
    output_width,
    should_use_color,
    style,
    wrap_indented_text,
)
from wn_dev_std.cli.types import SubparserRegistry
from wn_dev_std.plan_hygiene import LogRecord, PlanCatalog, read_document_body
from wn_dev_std.plan_reader import PlanReadContext


def register(subparsers: SubparserRegistry) -> None:
    """Register the subcommand."""
    parser = subparsers.add_parser(
        "list",
        help="List logs",
        description="List compliant work logs, optionally filtered to one plan.",
    )
    parser.add_argument(
        "plan_id",
        nargs="?",
        help="Optional plan id whose logs should be listed",
    )
    add_root_argument(parser)
    add_format_argument(parser)
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Run `log list`."""
    context = context_from_args(args)
    if print_catalog_failures(context):
        return 1
    plan_id = optional_string_attr(args, "plan_id")
    if plan_id is not None and not _has_plan(context.catalog, plan_id):
        print(f"plan not found: {plan_id}")
        return 1
    logs = _logs_for_plan(context.catalog.logs, plan_id)
    if output_format(args) == "json":
        print(json.dumps(_logs_payload(context, plan_id, logs), indent=2, sort_keys=True))
        return 0
    print(
        _format_log_list_text(
            context,
            plan_id,
            logs,
            use_color=should_use_color(),
            width=output_width(),
        )
    )
    return 0


def _logs_payload(
    context: PlanReadContext,
    plan_id: str | None,
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
        "step_id": log.step_id,
        "created": log.created,
        "path": log.relative_path,
        "body": read_document_body(catalog.root, log.relative_path),
    }


def _format_log_list_text(
    context: PlanReadContext,
    plan_id: str | None,
    logs: tuple[LogRecord, ...],
    *,
    use_color: bool = False,
    width: int = MAX_TEXT_WIDTH,
) -> str:
    if not logs:
        return (
            f"No compliant logs found for plan {plan_id}"
            if plan_id is not None
            else f"No compliant logs found under {context.catalog.root}"
        )
    formatted_width = normalized_width(width)
    if plan_id is not None:
        grouped = _logs_by_step(logs)
        plan_label = role_style(plan_id, "plan", use_color)
        lines = [
            f"Logs for {plan_label} under {context.catalog.root}:",
            "",
            "Summary:",
            f"  logs: {len(logs)}",
            f"  steps: {len(grouped)}",
            "",
            style("By Step", "cyan", use_color),
            style("-------", "cyan", use_color),
        ]
        for index, (step_id, step_logs) in enumerate(grouped.items()):
            if index:
                lines.append("")
            lines.extend(_format_step_log_group(step_id, step_logs, use_color, formatted_width))
    else:
        grouped_by_plan = _logs_by_plan(logs)
        lines = [
            f"Logs under {context.catalog.root}:",
            "",
            "Summary:",
            f"  plans: {len(grouped_by_plan)}",
            f"  logs: {len(logs)}",
            f"  steps: {len(_unique_step_keys(logs))}",
            "",
            style("By Plan", "cyan", use_color),
            style("-------", "cyan", use_color),
        ]
        for index, (group_plan_id, plan_logs) in enumerate(grouped_by_plan.items()):
            if index:
                lines.append("")
            lines.extend(
                _format_plan_log_group(group_plan_id, plan_logs, use_color, formatted_width)
            )
    return "\n".join(lines) + "\n"


def _logs_for_plan(logs: Sequence[LogRecord], plan_id: str | None) -> tuple[LogRecord, ...]:
    if plan_id is None:
        return tuple(logs)
    return tuple(log for log in logs if log.plan_id == plan_id)


def _logs_by_plan(logs: Sequence[LogRecord]) -> dict[str, list[LogRecord]]:
    grouped: dict[str, list[LogRecord]] = {}
    for log in logs:
        if log.plan_id not in grouped:
            grouped[log.plan_id] = []
        grouped[log.plan_id].append(log)
    return grouped


def _logs_by_step(logs: Sequence[LogRecord]) -> dict[str, list[LogRecord]]:
    grouped: dict[str, list[LogRecord]] = {}
    for log in logs:
        if log.step_id not in grouped:
            grouped[log.step_id] = []
        grouped[log.step_id].append(log)
    return grouped


def _unique_step_keys(logs: Sequence[LogRecord]) -> set[tuple[str, str]]:
    return {(log.plan_id, log.step_id) for log in logs}


def _format_plan_log_group(
    plan_id: str,
    logs: Sequence[LogRecord],
    use_color: bool,
    width: int,
) -> list[str]:
    grouped = _logs_by_step(logs)
    lines = [
        f"  - {role_style(plan_id, 'plan', use_color)}",
        f"    logs: {len(logs)}",
        f"    steps: {len(grouped)}",
        "    by step:",
    ]
    for index, (step_id, step_logs) in enumerate(grouped.items()):
        if index:
            lines.append("")
        lines.extend(
            _format_step_log_group(
                step_id,
                step_logs,
                use_color,
                width,
                base_indent="      ",
            )
        )
    return lines


def _format_step_log_group(
    step_id: str,
    logs: Sequence[LogRecord],
    use_color: bool,
    width: int,
    *,
    base_indent: str = "  ",
) -> list[str]:
    child_indent = base_indent + "  "
    entry_indent = child_indent + "  "
    entry_field_indent = entry_indent + "  "
    value_indent = entry_field_indent + "  "
    lines = [
        f"{base_indent}- {role_style(step_id, 'step', use_color)}",
        f"{child_indent}logs: {len(logs)}",
        f"{child_indent}entries:",
    ]
    for log in logs:
        lines.extend(
            _format_log_entry(
                log,
                use_color,
                width,
                entry_indent=entry_indent,
                field_indent=entry_field_indent,
                value_indent=value_indent,
            )
        )
    return lines


def _format_log_entry(
    log: LogRecord,
    use_color: bool,
    width: int,
    *,
    entry_indent: str = "      ",
    field_indent: str = "        ",
    value_indent: str = LOG_ENTRY_VALUE_INDENT,
) -> list[str]:
    return [
        f"{entry_indent}- {role_style(log.log_id, 'log', use_color)}",
        f"{field_indent}created: {log.created}",
        f"{field_indent}path:",
        *wrap_indented_text(log.relative_path, indent=value_indent, width=width),
    ]


def _has_plan(catalog: PlanCatalog, plan_id: str) -> bool:
    return any(plan.plan_id == plan_id for plan in catalog.plans)
