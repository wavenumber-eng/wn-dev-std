"""`log create` command."""

from __future__ import annotations

import argparse
from pathlib import Path

from wn_dev_std.cli.commands.plan_common import (
    add_root_argument,
    context_from_args,
    optional_string_attr,
    print_catalog_failures,
    string_attr,
)
from wn_dev_std.cli.types import SubparserRegistry
from wn_dev_std.plan_mutation import PlanMutationError, create_plan_log


def register(subparsers: SubparserRegistry) -> None:
    """Register the subcommand."""
    parser = subparsers.add_parser(
        "create",
        help="Create a plan log",
        description="Create a compliant work log attached to a plan.",
    )
    parser.add_argument("plan_id", help="Plan id to log against")
    parser.add_argument("step_id", help="Plan step id to attach the log to")
    body_group = parser.add_mutually_exclusive_group(required=True)
    body_group.add_argument("--body", help="Markdown log body")
    body_group.add_argument("--body-file", help="Path to a Markdown log body file")
    parser.add_argument("--id", dest="log_id", help="Log id")
    parser.add_argument("--created", help="Creation timestamp")
    add_root_argument(parser)
    parser.set_defaults(handler=run)


def run(args: argparse.Namespace) -> int:
    """Run `log create`."""
    context = context_from_args(args)
    if print_catalog_failures(context):
        return 1
    try:
        body = _body_text(args)
    except OSError as exc:
        print(f"could not read log body file: {exc}")
        return 1
    try:
        result = create_plan_log(
            context,
            string_attr(args, "plan_id"),
            string_attr(args, "step_id"),
            body,
            log_id=optional_string_attr(args, "log_id"),
            created=optional_string_attr(args, "created"),
        )
    except PlanMutationError as exc:
        print(str(exc))
        return 1
    print(f"{result.detail}: {result.path}")
    return 0


def _body_text(args: argparse.Namespace) -> str:
    body = optional_string_attr(args, "body")
    if body is not None:
        return body
    body_file = string_attr(args, "body_file")
    return Path(body_file).read_text(encoding="utf-8")
