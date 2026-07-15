"""`plan list` command."""

from __future__ import annotations

import argparse
import json
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from wn_dev_std.cli.commands.plan_common import (
    add_format_argument,
    add_root_argument,
    context_from_args,
    output_format,
    print_catalog_failures,
)
from wn_dev_std.cli.commands.text_format import (
    MAX_TEXT_WIDTH,
    ansi_style,
    normalized_width,
    output_width,
    should_use_color,
    wrap_indented_text,
)
from wn_dev_std.cli.commands.text_format import (
    style as color_style,
)
from wn_dev_std.cli.types import SubparserRegistry
from wn_dev_std.plan_hygiene import (
    PLAN_EXIT_CRITERION_STATUSES,
    LogRecord,
    PlanExitCriterionRecord,
    PlanRecord,
    PlanStepRecord,
)
from wn_dev_std.plan_reader import PlanReadContext

ANSI_BADGE_STYLES = {
    "active": "\033[1;37;42m",
    "blocked": "\033[1;37;41m",
    "pending": "\033[30;43m",
    "default": "\033[30;47m",
}
ANSI_ROLE_STYLES = {
    "plan": "\033[30;47m",
    "step": "\033[1;33m",
}
STEP_SECTION_COLORS = {
    "active": "green",
    "done": "cyan",
    "pending": "yellow",
    "blocked": "red",
}
STEP_BULLET_INDENT = "      "
STEP_TITLE_INDENT = "        "
STEP_DEPENDENCY_INDENT = "        "
STEP_DEPENDENCY_ITEM_INDENT = "          "


@dataclass(frozen=True, slots=True)
class PlanListSection:
    """Display metadata for one plan-list text section."""

    key: str
    title: str
    summary_label: str
    color: str


PLAN_LIST_SECTIONS = (
    PlanListSection("active", "Current", "active", "green"),
    PlanListSection("dependent", "Waiting On Dependencies", "waiting", "yellow"),
    PlanListSection("parked", "Parked / Pending", "parked", "cyan"),
    PlanListSection("blocked", "Blocked", "blocked", "red"),
)


def register(subparsers: SubparserRegistry) -> None:
    """Register the subcommand."""
    parser = subparsers.add_parser(
        "list",
        help="List compliant plans",
        description="List compliant plan documents.",
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
    print(_format_plan_list_text(context, use_color=should_use_color(), width=output_width()))
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
        "exit_criteria": [_exit_criterion_payload(criterion) for criterion in plan.exit_criteria],
    }


def _step_payload(step: PlanStepRecord) -> dict[str, object]:
    return {
        "id": step.step_id,
        "title": step.title,
        "status": step.status,
        "depends_on": list(step.depends_on),
    }


def _exit_criterion_payload(criterion: PlanExitCriterionRecord) -> dict[str, object]:
    return {
        "id": criterion.criterion_id,
        "title": criterion.title,
        "status": criterion.status,
    }


def _format_plan_list_text(
    context: PlanReadContext,
    *,
    use_color: bool = False,
    width: int = MAX_TEXT_WIDTH,
) -> str:
    if not context.catalog.plans:
        return f"No compliant plans found under {context.catalog.root}"
    formatted_width = normalized_width(width)
    grouped = _group_plans(context.catalog.plans)
    status_by_plan_id = {plan.plan_id: plan.status for plan in context.catalog.plans}
    latest_log_by_plan_id = _latest_logs_by_plan_id(context.catalog.logs)
    lines = [
        f"Plans under {context.catalog.root}:",
        "",
        "Summary:",
        *_format_group_summary_lines(grouped),
    ]
    for section in PLAN_LIST_SECTIONS:
        plans = grouped[section.key]
        if not plans:
            continue
        lines.extend(["", color_style(section.title, section.color, use_color)])
        lines.append(color_style("-" * len(section.title), section.color, use_color))
        for index, plan in enumerate(plans):
            if index:
                lines.append("")
            lines.extend(
                _format_plan_entry(
                    plan,
                    latest_log_by_plan_id.get(plan.plan_id),
                    status_by_plan_id,
                    use_color,
                    formatted_width,
                )
            )
    return "\n".join(lines) + "\n"


def _exit_criteria_summary(
    criteria: tuple[PlanExitCriterionRecord, ...],
) -> str:
    return _status_summary(
        tuple(criterion.status for criterion in criteria),
        PLAN_EXIT_CRITERION_STATUSES,
    )


def _group_plans(plans: Sequence[PlanRecord]) -> dict[str, list[PlanRecord]]:
    grouped: dict[str, list[PlanRecord]] = {section.key: [] for section in PLAN_LIST_SECTIONS}
    for plan in plans:
        grouped[_plan_section_key(plan)].append(plan)
    return grouped


def _plan_section_key(plan: PlanRecord) -> str:
    if plan.status == "blocked":
        return "blocked"
    if plan.depends_on:
        return "dependent"
    if plan.status == "active":
        return "active"
    return "parked"


def _format_group_summary_lines(grouped: dict[str, list[PlanRecord]]) -> list[str]:
    return [
        f"  {section.summary_label}: {len(grouped[section.key])}" for section in PLAN_LIST_SECTIONS
    ]


def _format_plan_entry(
    plan: PlanRecord,
    latest_log: LogRecord | None,
    status_by_plan_id: dict[str, str],
    use_color: bool,
    width: int,
) -> list[str]:
    plan_id = _role_style(plan.plan_id, "plan", use_color)
    lines = [
        f"  - {plan_id} {_status_token(plan.status, use_color)}",
        f"    created: {plan.created}",
    ]
    lines.extend(_format_last_log_lines(latest_log, use_color))
    lines.append(f"    path: {plan.relative_path}")
    if plan.depends_on:
        lines.extend(_format_dependency_lines(plan.depends_on, status_by_plan_id, use_color))
    if plan.steps:
        lines.extend(_format_step_sections(plan.steps, use_color, width))
    if plan.exit_criteria:
        lines.append(f"    exit criteria: {_exit_criteria_summary(plan.exit_criteria)}")
    return lines


def _latest_logs_by_plan_id(logs: Sequence[LogRecord]) -> dict[str, LogRecord]:
    latest: dict[str, LogRecord] = {}
    for log in logs:
        current = latest.get(log.plan_id)
        if current is None or (log.created, log.log_id) > (current.created, current.log_id):
            latest[log.plan_id] = log
    return latest


def _format_last_log_lines(log: LogRecord | None, use_color: bool) -> list[str]:
    if log is None:
        return ["    last log: none"]
    step_id = _role_style(log.step_id, "step", use_color)
    return [
        "    last log:",
        f"      - {log.log_id}",
        f"        created: {log.created}",
        f"        step: {step_id}",
    ]


def _format_dependency_lines(
    depends_on: tuple[str, ...],
    status_by_plan_id: dict[str, str],
    use_color: bool,
) -> list[str]:
    lines = ["    waits on:"]
    for plan_id in depends_on:
        status = status_by_plan_id.get(plan_id)
        suffix = "" if status is None else f" {_status_token(status, use_color)}"
        styled_plan_id = _role_style(plan_id, "plan", use_color)
        lines.append(f"      - {styled_plan_id}{suffix}")
    return lines


def _format_step_sections(
    steps: tuple[PlanStepRecord, ...],
    use_color: bool,
    width: int,
) -> list[str]:
    lines: list[str] = []
    active_steps = tuple(step for step in steps if step.status == "active")
    step_groups: list[tuple[str, str, tuple[PlanStepRecord, ...]]] = []
    if active_steps:
        step_groups.append(("active", "active", active_steps))
    step_groups.extend(
        [
            ("completed", "done", tuple(step for step in steps if step.status == "done")),
            ("pending", "pending", tuple(step for step in steps if step.status == "pending")),
        ]
    )
    blocked_steps = tuple(step for step in steps if step.status == "blocked")
    if blocked_steps:
        step_groups.append(("blocked", "blocked", blocked_steps))

    for index, (label, status, group_steps) in enumerate(step_groups):
        if index:
            lines.append("")
        heading = color_style(
            _step_group_heading(label, len(group_steps)),
            STEP_SECTION_COLORS[status],
            use_color,
        )
        lines.append(f"    {heading}:")
        lines.extend(_format_step_items(group_steps, use_color, width))
    return lines


def _step_group_heading(label: str, count: int) -> str:
    suffix = "step" if count == 1 else "steps"
    return f"{label} {suffix}"


def _format_step_items(
    steps: Iterable[PlanStepRecord],
    use_color: bool,
    width: int,
) -> list[str]:
    items = tuple(steps)
    if not items:
        return ["      - none"]
    lines: list[str] = []
    for step in items:
        lines.extend(_format_step_item(step, use_color, width))
    return lines


def _format_step_item(step: PlanStepRecord, use_color: bool, width: int) -> list[str]:
    lines = [f"{STEP_BULLET_INDENT}- {_role_style(step.step_id, 'step', use_color)}"]
    lines.extend(
        wrap_indented_text(
            step.title,
            indent=STEP_TITLE_INDENT,
            width=width,
        )
    )
    if step.depends_on:
        lines.append(f"{STEP_DEPENDENCY_INDENT}depends_on:")
        for step_id in step.depends_on:
            lines.append(
                f"{STEP_DEPENDENCY_ITEM_INDENT}- {_role_style(step_id, 'step', use_color)}"
            )
    return lines


def _status_summary(statuses: Sequence[str], status_order: Sequence[str]) -> str:
    counts: dict[str, int] = {}
    for status in statuses:
        counts[status] = counts.get(status, 0) + 1
    ordered_statuses = [status for status in status_order if status in counts]
    ordered_statuses.extend(sorted(status for status in counts if status not in status_order))
    return ", ".join(f"{counts[status]} {status}" for status in ordered_statuses)


def _status_token(status: str, use_color: bool) -> str:
    token = f"[{status}]"
    if not use_color:
        return token
    style_value = ANSI_BADGE_STYLES.get(status, ANSI_BADGE_STYLES["default"])
    return ansi_style(token, style_value, use_color)


def _role_style(text: str, role: str, use_color: bool) -> str:
    return ansi_style(text, ANSI_ROLE_STYLES[role], use_color)
