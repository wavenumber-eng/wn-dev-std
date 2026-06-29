"""Plan and work-log hygiene checks."""

from __future__ import annotations

import re
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import cast


@dataclass(frozen=True, slots=True)
class PlanHygieneReport:
    """Plan hygiene check result."""

    passed: bool
    detail: str


@dataclass(frozen=True, slots=True)
class PlanStepRecord:
    """Parsed plan step record."""

    step_id: str
    title: str
    status: str
    depends_on: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PlanExitCriterionRecord:
    """Parsed plan exit criterion record."""

    criterion_id: str
    title: str
    status: str


@dataclass(frozen=True, slots=True)
class PlanRecord:
    """Parsed plan document record."""

    plan_id: str
    relative_path: str
    status: str
    created: str
    depends_on: tuple[str, ...]
    steps: tuple[PlanStepRecord, ...]
    exit_criteria: tuple[PlanExitCriterionRecord, ...]


@dataclass(frozen=True, slots=True)
class LogRecord:
    """Parsed plan log document record."""

    log_id: str
    plan_id: str
    relative_path: str
    created: str


@dataclass(frozen=True, slots=True)
class PlanCatalog:
    """Validated plan and work-log catalog."""

    root: Path
    plan_roots: tuple[str, ...]
    plans: tuple[PlanRecord, ...]
    logs: tuple[LogRecord, ...]
    failures: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PlanAuditConfig:
    """Resolved plan audit configuration."""

    roots: tuple[str, ...]
    ignore: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PlanAuditState:
    """Mutable collections for one plan audit run."""

    failures: list[str]
    plans: list[PlanRecord]
    logs: list[LogRecord]


DEFAULT_PLAN_ROOTS = ("docs/plans",)
PLAN_DOCUMENT_TYPES = ("plan", "plan_log")
PLAN_STATUSES = ("active", "pending", "blocked")
PLAN_STEP_STATUSES = ("pending", "active", "blocked", "done")
PLAN_EXIT_CRITERION_STATUSES = ("pending", "met", "blocked")
PLAN_LIKE_NAME_TOKENS = ("plan", "roadmap")
LOG_LIKE_NAME_TOKENS = (
    "plan_log",
    "worklog",
    "work_log",
    "work-log",
    "logbook",
    "log_book",
    "log-book",
)
LOG_LIKE_DIRECTORY_NAMES = {
    "log",
    "logs",
    "worklog",
    "worklogs",
    "work_log",
    "work_logs",
    "work-log",
    "work-logs",
}
DOCUMENT_SUFFIXES = (".md", ".txt", ".html")
MARKDOWN_SUFFIX = ".md"
EXCLUDED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "rack_results",
}


def check_plan_hygiene_policy(
    root: Path,
    raw_config: Mapping[str, object] | None,
) -> PlanHygieneReport:
    """Check plan and work-log documents for the standard metadata contract."""
    catalog = load_plan_catalog(root, raw_config)
    if catalog.failures:
        return PlanHygieneReport(False, _summarize_failures(catalog.failures))

    existing_roots: list[Path] = []
    for item in catalog.plan_roots:
        plan_root = catalog.root / item
        if plan_root.exists():
            existing_roots.append(plan_root)
    if not existing_roots:
        return PlanHygieneReport(True, "no configured plan roots found")
    return PlanHygieneReport(
        True,
        f"{len(catalog.plans)} plan(s) and {len(catalog.logs)} log(s) across "
        f"{len(existing_roots)} plan root(s)",
    )


def load_plan_catalog(
    root: Path,
    raw_config: Mapping[str, object] | None,
) -> PlanCatalog:
    """Load and validate plan and work-log documents under a root."""
    resolved_root = root.resolve()
    config = _resolve_plan_config(raw_config)
    configured_roots = tuple((resolved_root / item).resolve() for item in config.roots)
    ignored_roots = tuple((resolved_root / item).resolve() for item in config.ignore)
    state = PlanAuditState(
        failures=[],
        plans=[],
        logs=[],
    )
    for path in _candidate_document_paths(resolved_root):
        _process_document(path, resolved_root, configured_roots, ignored_roots, state)
    state.failures.extend(_reference_failures(state.plans, state.logs))
    return PlanCatalog(
        resolved_root,
        config.roots,
        tuple(sorted(state.plans, key=lambda item: item.plan_id)),
        tuple(sorted(state.logs, key=lambda item: (item.plan_id, item.created, item.log_id))),
        tuple(state.failures),
    )


def read_document_body(root: Path, relative_path: str) -> str:
    """Read a Markdown document body without TOML front matter."""
    path = root / relative_path
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "+++":
        return text
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "+++":
            return "\n".join(lines[index + 1 :]).strip()
    return ""


def _process_document(
    path: Path,
    root: Path,
    configured_roots: Sequence[Path],
    ignored_roots: Sequence[Path],
    state: PlanAuditState,
) -> None:
    relative_path = path.relative_to(root).as_posix()
    inside_plan_root = any(_is_relative_to(path, plan_root) for plan_root in configured_roots)
    inside_ignored_root = any(_is_relative_to(path, ignored_root) for ignored_root in ignored_roots)
    if inside_ignored_root and not inside_plan_root:
        return

    metadata, parse_error = _parse_front_matter(path)
    metadata_type = _metadata_type(metadata) if parse_error is None else ""
    plan_or_log_like = _is_plan_or_log_like_path(path)

    if parse_error is not None:
        _record_parse_error(relative_path, parse_error, inside_plan_root, plan_or_log_like, state)
        return
    if inside_plan_root:
        _process_plan_root_document(path, relative_path, metadata, metadata_type, state)
        return
    if metadata_type in PLAN_DOCUMENT_TYPES:
        state.failures.append(
            f"{relative_path}: plan/log document is outside configured plan roots"
        )
    elif plan_or_log_like:
        state.failures.append(f"{relative_path}: rogue plan/log-like document")


def _record_parse_error(
    relative_path: str,
    parse_error: str,
    inside_plan_root: bool,
    plan_or_log_like: bool,
    state: PlanAuditState,
) -> None:
    if inside_plan_root or plan_or_log_like:
        state.failures.append(f"{relative_path}: {parse_error}")


def _process_plan_root_document(
    path: Path,
    relative_path: str,
    metadata: Mapping[str, object] | None,
    metadata_type: str,
    state: PlanAuditState,
) -> None:
    if metadata_type in PLAN_DOCUMENT_TYPES:
        _collect_record(path, relative_path, metadata, state.plans, state.logs, state.failures)
        return
    if path.name.lower() == "readme.md":
        return
    if path.suffix.lower() == MARKDOWN_SUFFIX:
        _record_missing_front_matter(path, relative_path, state)


def _record_missing_front_matter(
    path: Path,
    relative_path: str,
    state: PlanAuditState,
) -> None:
    if path.suffix.lower() != MARKDOWN_SUFFIX:
        state.failures.append(f"{relative_path}: plan/log documents must be Markdown")
    else:
        state.failures.append(f"{relative_path}: missing TOML front matter")


def _resolve_plan_config(config: Mapping[str, object] | None) -> PlanAuditConfig:
    documentation = _mapping_value(config.get("documentation") if config else None)
    plans = _mapping_value(documentation.get("plans") if documentation else None)
    raw_roots = plans.get("roots") if plans else None
    raw_ignore = plans.get("ignore") if plans else None
    roots = _string_tuple(raw_roots)
    ignore = _string_tuple(raw_ignore)
    if not roots:
        roots = DEFAULT_PLAN_ROOTS
    return PlanAuditConfig(roots, ignore)


def _candidate_document_paths(root: Path) -> list[Path]:
    paths: list[Path] = []
    for suffix in DOCUMENT_SUFFIXES:
        for path in root.rglob(f"*{suffix}"):
            if _is_excluded(path, root):
                continue
            paths.append(path)
    return sorted(paths)


def _is_excluded(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return True
    return bool(EXCLUDED_PARTS.intersection(parts))


def _parse_front_matter(path: Path) -> tuple[Mapping[str, object] | None, str | None]:
    if path.suffix.lower() != MARKDOWN_SUFFIX:
        return None, None
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "+++":
        return None, None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "+++":
            raw_front_matter = "\n".join(lines[1:index])
            try:
                parsed = tomllib.loads(raw_front_matter)
            except tomllib.TOMLDecodeError as exc:
                return None, f"invalid TOML front matter: {exc}"
            return cast(Mapping[str, object], parsed), None
    return None, "unterminated TOML front matter"


def _collect_record(
    path: Path,
    relative_path: str,
    metadata: Mapping[str, object] | None,
    plans: list[PlanRecord],
    logs: list[LogRecord],
    failures: list[str],
) -> None:
    if metadata is None:
        failures.append(f"{relative_path}: missing TOML front matter")
        return
    metadata_type = _metadata_type(metadata)
    if metadata_type == "plan":
        plan = _plan_record(relative_path, metadata, failures)
        if plan is not None:
            plans.append(plan)
        return
    if metadata_type == "plan_log":
        log = _log_record(relative_path, metadata, failures)
        if log is not None:
            logs.append(log)
        return
    failures.append(f"{relative_path}: invalid type {metadata_type!r}")


def _plan_record(
    relative_path: str,
    metadata: Mapping[str, object],
    failures: list[str],
) -> PlanRecord | None:
    plan_id = _required_string(metadata, "id", relative_path, failures)
    status = _required_string(metadata, "status", relative_path, failures)
    created = _created_value(metadata, relative_path, failures)
    depends_on = _optional_string_tuple(metadata.get("depends_on"), relative_path, failures)
    steps = _step_records(metadata.get("steps"), relative_path, failures)
    exit_criteria = _exit_criterion_records(
        metadata.get("exit_criteria"),
        relative_path,
        failures,
    )

    if status == "complete":
        failures.append(f"{relative_path}: complete plans must be closed out and removed")
    elif status and status not in PLAN_STATUSES:
        failures.append(f"{relative_path}: invalid status {status!r}")
    _validate_plan_step_state(relative_path, status, steps, failures)
    _validate_plan_exit_criteria_state(relative_path, status, exit_criteria, failures)

    if not plan_id:
        return None
    return PlanRecord(
        plan_id,
        relative_path,
        status,
        created,
        depends_on,
        steps,
        exit_criteria,
    )


def _log_record(
    relative_path: str,
    metadata: Mapping[str, object],
    failures: list[str],
) -> LogRecord | None:
    log_id = _required_string(metadata, "id", relative_path, failures)
    plan_id = _required_string(metadata, "plan_id", relative_path, failures)
    created = _created_value(metadata, relative_path, failures)
    if not log_id or not plan_id:
        return None
    return LogRecord(log_id, plan_id, relative_path, created)


def _reference_failures(plans: Sequence[PlanRecord], logs: Sequence[LogRecord]) -> list[str]:
    plan_ids = {plan.plan_id for plan in plans}
    return (
        _duplicate_reference_failures(plans, logs)
        + _dependency_reference_failures(plans, plan_ids)
        + _log_reference_failures(logs, plan_ids)
    )


def _duplicate_reference_failures(
    plans: Sequence[PlanRecord],
    logs: Sequence[LogRecord],
) -> list[str]:
    failures: list[str] = []
    duplicate_plan_ids = _duplicates([plan.plan_id for plan in plans])
    duplicate_log_ids = _duplicates([log.log_id for log in logs])
    if duplicate_plan_ids:
        failures.append("duplicate plan ids: " + ", ".join(duplicate_plan_ids))
    if duplicate_log_ids:
        failures.append("duplicate log ids: " + ", ".join(duplicate_log_ids))
    return failures


def _dependency_reference_failures(
    plans: Sequence[PlanRecord],
    plan_ids: set[str],
) -> list[str]:
    failures: list[str] = []
    for plan in plans:
        missing = [plan_id for plan_id in plan.depends_on if plan_id not in plan_ids]
        if missing:
            failures.append(
                f"{plan.relative_path}: missing depends_on targets: " + ", ".join(missing)
            )
    return failures


def _log_reference_failures(logs: Sequence[LogRecord], plan_ids: set[str]) -> list[str]:
    failures: list[str] = []
    for log in logs:
        if log.plan_id not in plan_ids:
            failures.append(f"{log.relative_path}: unknown plan_id {log.plan_id!r}")
    orphaned_logs = [log.relative_path for log in logs if log.plan_id not in plan_ids]
    if orphaned_logs and not plan_ids:
        failures.append("orphan logs without any active plan: " + ", ".join(orphaned_logs))
    return failures


def _metadata_type(metadata: Mapping[str, object] | None) -> str:
    if metadata is None:
        return ""
    value = metadata.get("type")
    return value.strip() if isinstance(value, str) else ""


def _required_string(
    metadata: Mapping[str, object],
    key: str,
    relative_path: str,
    failures: list[str],
) -> str:
    value = metadata.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    failures.append(f"{relative_path}: missing {key}")
    return ""


def _created_value(
    metadata: Mapping[str, object],
    relative_path: str,
    failures: list[str],
) -> str:
    value = metadata.get("created")
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    failures.append(f"{relative_path}: missing created")
    return ""


def _optional_string_tuple(
    value: object,
    relative_path: str,
    failures: list[str],
) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        failures.append(f"{relative_path}: depends_on must be a string array")
        return ()
    items: list[str] = []
    for item in cast(list[object], value):
        if not isinstance(item, str) or not item.strip():
            failures.append(f"{relative_path}: depends_on must contain only non-empty strings")
            return ()
        items.append(item.strip())
    return tuple(items)


def _step_records(
    value: object,
    relative_path: str,
    failures: list[str],
) -> tuple[PlanStepRecord, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        failures.append(f"{relative_path}: steps must be an array of tables")
        return ()

    steps: list[PlanStepRecord] = []
    for index, item in enumerate(cast(list[object], value), start=1):
        if not isinstance(item, dict):
            failures.append(f"{relative_path}: step {index} must be a table")
            continue
        step = _step_record(cast(Mapping[str, object], item), relative_path, index, failures)
        if step is not None:
            steps.append(step)
    _validate_step_references(relative_path, steps, failures)
    return tuple(steps)


def _step_record(
    metadata: Mapping[str, object],
    relative_path: str,
    index: int,
    failures: list[str],
) -> PlanStepRecord | None:
    label = f"step {index}"
    step_id = _required_string(metadata, "id", f"{relative_path}: {label}", failures)
    title = _required_string(metadata, "title", f"{relative_path}: {label}", failures)
    status = _required_string(metadata, "status", f"{relative_path}: {label}", failures)
    depends_on = _optional_string_tuple(
        metadata.get("depends_on"),
        f"{relative_path}: {label}",
        failures,
    )
    if status and status not in PLAN_STEP_STATUSES:
        failures.append(f"{relative_path}: {label}: invalid status {status!r}")
    if not step_id:
        return None
    return PlanStepRecord(step_id, title, status, depends_on)


def _exit_criterion_records(
    value: object,
    relative_path: str,
    failures: list[str],
) -> tuple[PlanExitCriterionRecord, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        failures.append(f"{relative_path}: exit_criteria must be an array of tables")
        return ()

    criteria: list[PlanExitCriterionRecord] = []
    for index, item in enumerate(cast(list[object], value), start=1):
        if not isinstance(item, dict):
            failures.append(f"{relative_path}: exit criterion {index} must be a table")
            continue
        criterion = _exit_criterion_record(
            cast(Mapping[str, object], item),
            relative_path,
            index,
            failures,
        )
        if criterion is not None:
            criteria.append(criterion)
    duplicate_ids = _duplicates([criterion.criterion_id for criterion in criteria])
    if duplicate_ids:
        failures.append(
            f"{relative_path}: duplicate exit criterion ids: " + ", ".join(duplicate_ids)
        )
    return tuple(criteria)


def _exit_criterion_record(
    metadata: Mapping[str, object],
    relative_path: str,
    index: int,
    failures: list[str],
) -> PlanExitCriterionRecord | None:
    label = f"exit criterion {index}"
    criterion_id = _required_string(metadata, "id", f"{relative_path}: {label}", failures)
    title = _required_string(metadata, "title", f"{relative_path}: {label}", failures)
    status = _required_string(metadata, "status", f"{relative_path}: {label}", failures)
    if status and status not in PLAN_EXIT_CRITERION_STATUSES:
        failures.append(f"{relative_path}: {label}: invalid status {status!r}")
    if not criterion_id:
        return None
    return PlanExitCriterionRecord(criterion_id, title, status)


def _validate_step_references(
    relative_path: str,
    steps: Sequence[PlanStepRecord],
    failures: list[str],
) -> None:
    step_ids = [step.step_id for step in steps]
    duplicate_step_ids = _duplicates(step_ids)
    if duplicate_step_ids:
        failures.append(f"{relative_path}: duplicate step ids: " + ", ".join(duplicate_step_ids))
    known_ids = set(step_ids)
    for step in steps:
        missing = [step_id for step_id in step.depends_on if step_id not in known_ids]
        if missing:
            failures.append(
                f"{relative_path}: step {step.step_id}: missing depends_on targets: "
                + ", ".join(missing)
            )


def _validate_plan_step_state(
    relative_path: str,
    plan_status: str,
    steps: Sequence[PlanStepRecord],
    failures: list[str],
) -> None:
    if not steps:
        return
    active_steps = [step.step_id for step in steps if step.status == "active"]
    if len(active_steps) > 1:
        failures.append(f"{relative_path}: more than one active step: " + ", ".join(active_steps))
    if plan_status == "pending" and active_steps:
        failures.append(f"{relative_path}: pending plan cannot have active steps")
    if plan_status == "active" and all(step.status == "done" for step in steps):
        failures.append(f"{relative_path}: all steps are done but plan is still active")


def _validate_plan_exit_criteria_state(
    relative_path: str,
    plan_status: str,
    exit_criteria: Sequence[PlanExitCriterionRecord],
    failures: list[str],
) -> None:
    if plan_status not in PLAN_STATUSES:
        return
    if not exit_criteria:
        failures.append(f"{relative_path}: missing exit_criteria")
        return
    if plan_status == "active" and all(criterion.status == "met" for criterion in exit_criteria):
        failures.append(f"{relative_path}: all exit criteria are met but plan is still active")


def _mapping_value(value: object) -> Mapping[str, object] | None:
    if isinstance(value, dict):
        return cast(Mapping[str, object], value)
    return None


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    items: list[str] = []
    for item in cast(list[object], value):
        if isinstance(item, str) and item.strip():
            items.append(item.strip())
    return tuple(items)


def _duplicates(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def _is_plan_like_path(path: Path) -> bool:
    stem_tokens = set(_name_tokens(path.stem))
    return bool(stem_tokens.intersection(PLAN_LIKE_NAME_TOKENS))


def _is_log_like_path(path: Path) -> bool:
    stem = path.stem.lower()
    stem_tokens = set(_name_tokens(path.stem))
    if path.suffix.lower() == MARKDOWN_SUFFIX and "log" in stem_tokens:
        return True
    if any(token in stem for token in LOG_LIKE_NAME_TOKENS):
        return True
    return any(part.lower() in LOG_LIKE_DIRECTORY_NAMES for part in path.parts)


def _is_plan_or_log_like_path(path: Path) -> bool:
    return _is_plan_like_path(path) or _is_log_like_path(path)


def _name_tokens(name: str) -> tuple[str, ...]:
    return tuple(token for token in re.split(r"[^a-z0-9]+", name.lower()) if token)


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _summarize_failures(failures: Sequence[str], limit: int = 10) -> str:
    shown = list(failures[:limit])
    suffix = "" if len(failures) <= limit else f"; +{len(failures) - limit} more"
    return "plan hygiene failures: " + "; ".join(shown) + suffix
