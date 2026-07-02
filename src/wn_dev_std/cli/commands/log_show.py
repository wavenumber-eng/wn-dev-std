"""`log show` command."""

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
from wn_dev_std.plan_hygiene import LogRecord, read_document_body
from wn_dev_std.plan_reader import PlanReadContext


def register(subparsers: SubparserRegistry) -> None:
    """Register the subcommand."""
    parser = subparsers.add_parser(
        "show",
        help="Show a compliant plan log",
        description="Show a compliant Wavenumber plan work log.",
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
    print(_format_log_show_text(log, body))
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


def _format_log_show_text(log: LogRecord, body: str) -> str:
    lines = [
        f"Log: {log.log_id}",
        f"Plan: {log.plan_id}",
        f"Step: {log.step_id}",
        f"Created: {log.created}",
        f"Path: {log.relative_path}",
    ]
    if body:
        lines.extend(["", body])
    return "\n".join(lines)
