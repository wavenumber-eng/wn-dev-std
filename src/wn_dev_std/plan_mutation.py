"""Non-destructive plan and work-log mutations."""

from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import cast

from wn_dev_std.plan_hygiene import PLAN_STATUSES, PLAN_STEP_STATUSES, PlanRecord
from wn_dev_std.plan_reader import PlanReadContext


@dataclass(frozen=True, slots=True)
class PlanMutationResult:
    """Result from a plan mutation."""

    path: Path
    detail: str


@dataclass(frozen=True, slots=True)
class StepBlock:
    """Line range for one step table in TOML front matter."""

    start: int
    end: int
    step_id: str


class PlanMutationError(RuntimeError):
    """Raised when a requested plan mutation cannot be applied."""


SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


def create_plan(
    context: PlanReadContext,
    plan_id: str,
    title: str,
    status: str = "active",
    created: str | None = None,
    depends_on: tuple[str, ...] = (),
    plan_root: str | None = None,
    body: str | None = None,
) -> PlanMutationResult:
    """Create a new canonical plan document."""
    _ensure_catalog_compliant(context)
    _validate_path_safe_id("plan id", plan_id)
    _validate_status(status, PLAN_STATUSES, "plan status")
    if _find_plan(context, plan_id) is not None:
        raise PlanMutationError(f"plan already exists: {plan_id}")
    _validate_plan_dependencies(context, depends_on)

    relative_root = _selected_plan_root(context, plan_root)
    path = context.catalog.root / relative_root / plan_id / "plan.md"
    _ensure_path_inside_root(context.catalog.root, path)
    if path.exists():
        raise PlanMutationError(f"plan path already exists: {path}")

    created_value = created or date.today().isoformat()
    front_matter = [
        'type = "plan"',
        f"id = {_toml_string(plan_id)}",
        f"status = {_toml_string(status)}",
        f"created = {_toml_string(created_value)}",
    ]
    if depends_on:
        front_matter.append(f"depends_on = {_toml_string_array(depends_on)}")
    front_matter.extend(
        [
            "",
            "[[steps]]",
            'id = "work"',
            'title = "Execute plan work"',
            'status = "pending"',
            "",
            "[[exit_criteria]]",
            'id = "signoff"',
            'title = "Focused signoff passes"',
            'status = "pending"',
        ]
    )
    text = _front_matter_document(front_matter, _plan_body(title, body))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return PlanMutationResult(path, f"created plan {plan_id}")


def set_plan_status(
    context: PlanReadContext,
    plan_id: str,
    status: str,
) -> PlanMutationResult:
    """Set a plan's top-level status."""
    _ensure_catalog_compliant(context)
    _validate_status(status, PLAN_STATUSES, "plan status")
    plan = _required_plan(context, plan_id)
    _validate_plan_status_transition(plan, status)
    path = context.catalog.root / plan.relative_path
    front_matter, body = _split_front_matter(path)
    updated = _set_top_level_value(front_matter, "status", _toml_string(status))
    _write_front_matter_document(path, updated, body)
    return PlanMutationResult(path, f"set plan {plan_id} status to {status}")


def add_plan_step(
    context: PlanReadContext,
    plan_id: str,
    step_id: str,
    title: str,
    status: str = "pending",
    depends_on: tuple[str, ...] = (),
) -> PlanMutationResult:
    """Add a step to a plan."""
    _ensure_catalog_compliant(context)
    _validate_step_id(step_id)
    _validate_status(status, PLAN_STEP_STATUSES, "step status")
    plan = _required_plan(context, plan_id)
    if any(step.step_id == step_id for step in plan.steps):
        raise PlanMutationError(f"step already exists: {step_id}")
    _validate_step_transition(plan, step_id, status, depends_on)

    path = context.catalog.root / plan.relative_path
    front_matter, body = _split_front_matter(path)
    if front_matter and front_matter[-1].strip():
        front_matter.append("")
    front_matter.extend(
        [
            "[[steps]]",
            f"id = {_toml_string(step_id)}",
            f"title = {_toml_string(title)}",
            f"status = {_toml_string(status)}",
        ]
    )
    if depends_on:
        front_matter.append(f"depends_on = {_toml_string_array(depends_on)}")
    _write_front_matter_document(path, front_matter, body)
    return PlanMutationResult(path, f"added step {step_id} to plan {plan_id}")


def set_plan_step_status(
    context: PlanReadContext,
    plan_id: str,
    step_id: str,
    status: str,
) -> PlanMutationResult:
    """Set an existing step's status."""
    _ensure_catalog_compliant(context)
    _validate_status(status, PLAN_STEP_STATUSES, "step status")
    plan = _required_plan(context, plan_id)
    existing_step = next((step for step in plan.steps if step.step_id == step_id), None)
    if existing_step is None:
        raise PlanMutationError(f"step not found: {step_id}")
    _validate_step_transition(plan, step_id, status, existing_step.depends_on)

    path = context.catalog.root / plan.relative_path
    front_matter, body = _split_front_matter(path)
    block = _required_step_block(front_matter, step_id)
    updated = _set_value_in_range(front_matter, block.start, block.end, "status", status)
    _write_front_matter_document(path, updated, body)
    return PlanMutationResult(path, f"set step {step_id} status to {status}")


def create_plan_log(
    context: PlanReadContext,
    plan_id: str,
    step_id: str,
    body: str,
    log_id: str | None = None,
    created: str | None = None,
) -> PlanMutationResult:
    """Create a log entry attached to a plan."""
    _ensure_catalog_compliant(context)
    plan = _required_plan(context, plan_id)
    if not any(step.step_id == step_id for step in plan.steps):
        raise PlanMutationError(f"step not found: {step_id}")
    created_value = created or datetime.now().astimezone().isoformat(timespec="seconds")
    resolved_log_id = log_id or f"{plan_id}-{_safe_file_stem(created_value)}"
    if not resolved_log_id.strip():
        raise PlanMutationError("log id must not be empty")
    if any(log.log_id == resolved_log_id for log in context.catalog.logs):
        raise PlanMutationError(f"log already exists: {resolved_log_id}")

    plan_path = context.catalog.root / plan.relative_path
    log_dir = plan_path.parent / "logs"
    path = _unique_path(log_dir / f"{_safe_file_stem(created_value)}.md")
    front_matter = [
        'type = "plan_log"',
        f"id = {_toml_string(resolved_log_id)}",
        f"plan_id = {_toml_string(plan_id)}",
        f"step_id = {_toml_string(step_id)}",
        f"created = {_toml_string(created_value)}",
    ]
    text = _front_matter_document(front_matter, _log_body(body, step_id))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return PlanMutationResult(path, f"created log {resolved_log_id} for plan {plan_id}")


def _ensure_catalog_compliant(context: PlanReadContext) -> None:
    if context.catalog.failures:
        raise PlanMutationError("plan catalog is not compliant")


def _find_plan(context: PlanReadContext, plan_id: str) -> PlanRecord | None:
    return next((plan for plan in context.catalog.plans if plan.plan_id == plan_id), None)


def _required_plan(context: PlanReadContext, plan_id: str) -> PlanRecord:
    plan = _find_plan(context, plan_id)
    if plan is None:
        raise PlanMutationError(f"plan not found: {plan_id}")
    return plan


def _selected_plan_root(context: PlanReadContext, requested: str | None) -> str:
    if requested is None:
        if not context.catalog.plan_roots:
            raise PlanMutationError("no configured plan roots")
        return context.catalog.plan_roots[0]
    normalized = requested.replace("\\", "/").strip("/")
    if normalized not in context.catalog.plan_roots:
        raise PlanMutationError(f"plan root is not configured: {requested}")
    return normalized


def _validate_status(status: str, allowed: tuple[str, ...], label: str) -> None:
    if status not in allowed:
        raise PlanMutationError(f"invalid {label}: {status}")


def _validate_path_safe_id(label: str, value: str) -> None:
    if not SAFE_ID_PATTERN.fullmatch(value):
        raise PlanMutationError(f"{label} must use only letters, numbers, '.', '_', or '-'")


def _validate_step_id(step_id: str) -> None:
    if not step_id.strip():
        raise PlanMutationError("step id must not be empty")


def _validate_plan_dependencies(context: PlanReadContext, depends_on: tuple[str, ...]) -> None:
    known_plan_ids = {plan.plan_id for plan in context.catalog.plans}
    missing = [item for item in depends_on if item not in known_plan_ids]
    if missing:
        raise PlanMutationError("missing plan dependency target(s): " + ", ".join(missing))


def _validate_plan_status_transition(plan: PlanRecord, status: str) -> None:
    if status == "pending" and any(step.status == "active" for step in plan.steps):
        raise PlanMutationError("pending plans cannot have active steps")
    if status == "active" and plan.steps and all(step.status == "done" for step in plan.steps):
        raise PlanMutationError("active plans cannot have all steps done")


def _validate_step_transition(
    plan: PlanRecord,
    step_id: str,
    status: str,
    depends_on: tuple[str, ...],
) -> None:
    _validate_step_dependencies(plan, depends_on)
    if status == "active":
        _validate_active_step_transition(plan, step_id)
    if status == "done":
        _validate_done_step_transition(plan, step_id, status)


def _validate_step_dependencies(plan: PlanRecord, depends_on: tuple[str, ...]) -> None:
    known_step_ids = {step.step_id for step in plan.steps}
    missing = [item for item in depends_on if item not in known_step_ids]
    if missing:
        raise PlanMutationError("missing step dependency target(s): " + ", ".join(missing))


def _validate_active_step_transition(plan: PlanRecord, step_id: str) -> None:
    active = [step.step_id for step in plan.steps if step.status == "active"]
    other_active = [item for item in active if item != step_id]
    if other_active:
        raise PlanMutationError("another step is already active: " + ", ".join(other_active))
    if plan.status == "pending":
        raise PlanMutationError("pending plans cannot have active steps")


def _validate_done_step_transition(plan: PlanRecord, step_id: str, status: str) -> None:
    if plan.status != "active":
        return
    resulting_statuses = [status]
    resulting_statuses.extend(step.status for step in plan.steps if step.step_id != step_id)
    if resulting_statuses and all(item == "done" for item in resulting_statuses):
        raise PlanMutationError("setting all steps done would leave an active plan")


def _split_front_matter(path: Path) -> tuple[list[str], str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "+++":
        raise PlanMutationError(f"{path}: missing TOML front matter")
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "+++":
            return lines[1:index], "\n".join(lines[index + 1 :]).strip()
    raise PlanMutationError(f"{path}: unterminated TOML front matter")


def _write_front_matter_document(path: Path, front_matter: list[str], body: str) -> None:
    path.write_text(_front_matter_document(front_matter, body), encoding="utf-8")


def _front_matter_document(front_matter: list[str], body: str) -> str:
    document = "+++\n" + "\n".join(front_matter).rstrip() + "\n+++\n"
    if body.strip():
        document += "\n" + body.strip() + "\n"
    return document


def _set_top_level_value(front_matter: list[str], key: str, rendered_value: str) -> list[str]:
    updated = list(front_matter)
    insert_at = len(updated)
    for index, line in enumerate(updated):
        stripped = line.strip()
        if stripped.startswith("["):
            insert_at = min(insert_at, index)
            continue
        if _line_has_key(stripped, key):
            updated[index] = f"{key} = {rendered_value}"
            return updated
    updated.insert(insert_at, f"{key} = {rendered_value}")
    return updated


def _set_value_in_range(
    front_matter: list[str],
    start: int,
    end: int,
    key: str,
    value: str,
) -> list[str]:
    updated = list(front_matter)
    rendered = _toml_string(value)
    for index in range(start, end):
        if _line_has_key(updated[index].strip(), key):
            updated[index] = f"{key} = {rendered}"
            return updated
    updated.insert(end, f"{key} = {rendered}")
    return updated


def _required_step_block(front_matter: list[str], step_id: str) -> StepBlock:
    for block in _step_blocks(front_matter):
        if block.step_id == step_id:
            return block
    raise PlanMutationError(f"step not found in front matter: {step_id}")


def _step_blocks(front_matter: list[str]) -> tuple[StepBlock, ...]:
    starts = [index for index, line in enumerate(front_matter) if line.strip() == "[[steps]]"]
    blocks: list[StepBlock] = []
    for start_index, start in enumerate(starts):
        end = starts[start_index + 1] if start_index + 1 < len(starts) else len(front_matter)
        step_id = _step_id_from_block(front_matter[start:end])
        if step_id:
            blocks.append(StepBlock(start, end, step_id))
    return tuple(blocks)


def _step_id_from_block(lines: list[str]) -> str:
    try:
        parsed = tomllib.loads("\n".join(lines))
    except tomllib.TOMLDecodeError:
        return ""
    steps = parsed.get("steps")
    if not isinstance(steps, list) or not steps:
        return ""
    first_step = cast(list[object], steps)[0]
    if not isinstance(first_step, dict):
        return ""
    raw_id = cast(dict[str, object], first_step).get("id")
    return raw_id.strip() if isinstance(raw_id, str) else ""


def _line_has_key(stripped_line: str, key: str) -> bool:
    return stripped_line.startswith(f"{key} ") or stripped_line.startswith(f"{key}=")


def _plan_body(title: str, body: str | None) -> str:
    lines = [f"# {title.strip()}"]
    if body and body.strip():
        lines.extend(["", body.strip()])
    return "\n".join(lines)


def _log_body(body: str, step_id: str) -> str:
    lines = [f"# Log: {step_id}", "", body.strip()]
    return "\n".join(lines).strip()


def _toml_string(value: str) -> str:
    return json.dumps(value)


def _toml_string_array(values: tuple[str, ...]) -> str:
    return "[" + ", ".join(_toml_string(value) for value in values) + "]"


def _safe_file_stem(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", value.replace(":", ""))
    cleaned = cleaned.strip("-")
    return cleaned or "log"


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    for index in range(2, 1000):
        candidate = path.with_name(f"{path.stem}-{index}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise PlanMutationError(f"could not find unique path for {path}")


def _ensure_path_inside_root(root: Path, path: Path) -> None:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise PlanMutationError(f"path escapes project root: {path}") from exc
