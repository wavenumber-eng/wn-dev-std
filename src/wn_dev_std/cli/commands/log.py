"""Read-only work-log commands."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Literal, cast

from wn_dev_std.cli.types import SubparserRegistry
from wn_dev_std.plan_hygiene import LogRecord, PlanCatalog, read_document_body
from wn_dev_std.plan_reader import PlanReadContext, load_plan_read_context


def register(subparsers: SubparserRegistry) -> None:
    """Register the command with the root parser."""
    parser = subparsers.add_parser(
        "log",
        help="Read compliant plan logs",
        description="Read compliant Wavenumber plan work logs.",
    )
    command_parsers = parser.add_subparsers(dest="log_command", metavar="<log-command>")
    _register_list(command_parsers)
    parser.set_defaults(handler=run_help, parser=parser)


def _register_list(subparsers: SubparserRegistry) -> None:
    parser = subparsers.add_parser(
        "list",
        help="List logs for a plan",
        description="List compliant work logs for a plan.",
    )
    parser.add_argument("plan_id", help="Plan id whose logs should be listed")
    _add_root_argument(parser)
    _add_format_argument(parser)
    parser.set_defaults(handler=run_list)


def run_help(args: argparse.Namespace) -> int:
    """Print command help when no subcommand is selected."""
    parser = cast(argparse.ArgumentParser, args.parser)
    parser.print_help()
    return 0


def run_list(args: argparse.Namespace) -> int:
    """Run `log list`."""
    context = _context_from_args(args)
    if _print_catalog_failures(context):
        return 1
    plan_id = _string_attr(args, "plan_id")
    if not _has_plan(context.catalog, plan_id):
        print(f"plan not found: {plan_id}")
        return 1
    logs = tuple(log for log in context.catalog.logs if log.plan_id == plan_id)
    output_format = _output_format(args)
    if output_format == "json":
        print(json.dumps(_logs_payload(context, plan_id, logs), indent=2, sort_keys=True))
        return 0
    print(_format_log_list_text(context, plan_id, logs))
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
