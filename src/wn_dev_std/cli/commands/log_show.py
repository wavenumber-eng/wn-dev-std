"""`log show` command."""

from __future__ import annotations

import argparse
import json

from wn_dev_std.cli.commands.log_text import (
    role_style,
    wrap_body_text,
)
from wn_dev_std.cli.commands.plan_common import (
    add_format_argument,
    add_root_argument,
    context_from_args,
    output_format,
    print_catalog_failures,
    string_attr,
)
from wn_dev_std.cli.commands.text_format import (
    FIELD_VALUE_INDENT,
    MAX_TEXT_WIDTH,
    normalized_width,
    output_width,
    should_use_color,
    wrap_indented_text,
)
from wn_dev_std.cli.types import SubparserRegistry
from wn_dev_std.plan_hygiene import LogRecord, read_document_body
from wn_dev_std.plan_reader import PlanReadContext


def register(subparsers: SubparserRegistry) -> None:
    """Register the subcommand."""
    parser = subparsers.add_parser(
        "show",
        help="Show a compliant plan log",
        description="Show a compliant plan work log.",
    )
    parser.add_argument("log_id", help="Log id to show")
    add_root_argument(parser)
    add_format_argument(parser)
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Run `log show`."""
    context = context_from_args(args)
    if print_catalog_failures(context):
        return 1
    log_id = string_attr(args, "log_id")
    log = _find_log(context, log_id)
    if log is None:
        print(f"log not found: {log_id}")
        return 1
    body = read_document_body(context.catalog.root, log.relative_path)
    if output_format(args) == "json":
        print(json.dumps(_log_payload(log, body), indent=2, sort_keys=True))
        return 0
    print(
        _format_log_show_text(
            log,
            body,
            use_color=should_use_color(),
            width=output_width(),
        )
    )
    return 0


def _find_log(context: PlanReadContext, log_id: str) -> LogRecord | None:
    for log in context.catalog.logs:
        if log.log_id == log_id:
            return log
    return None


def _log_payload(log: LogRecord, body: str) -> dict[str, object]:
    return {
        "id": log.log_id,
        "plan_id": log.plan_id,
        "step_id": log.step_id,
        "created": log.created,
        "path": log.relative_path,
        "body": body,
    }


def _format_log_show_text(
    log: LogRecord,
    body: str,
    *,
    use_color: bool = False,
    width: int = MAX_TEXT_WIDTH,
) -> str:
    formatted_width = normalized_width(width)
    lines = [
        "Log:",
        f"  - {role_style(log.log_id, 'log', use_color)}",
        f"    created: {log.created}",
        "    plan:",
        *wrap_indented_text(
            role_style(log.plan_id, "plan", use_color),
            indent=FIELD_VALUE_INDENT,
            width=formatted_width,
        ),
        "    step:",
        *wrap_indented_text(
            role_style(log.step_id, "step", use_color),
            indent=FIELD_VALUE_INDENT,
            width=formatted_width,
        ),
        "    path:",
        *wrap_indented_text(log.relative_path, indent=FIELD_VALUE_INDENT, width=formatted_width),
    ]
    if body:
        lines.extend(["", *wrap_body_text(body, width=formatted_width)])
    return "\n".join(lines) + "\n"
