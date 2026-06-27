"""Plan and work-log hygiene checks."""

from __future__ import annotations

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
class PlanRecord:
    """Parsed plan document record."""

    plan_id: str
    relative_path: str
    depends_on: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LogRecord:
    """Parsed plan log document record."""

    log_id: str
    plan_id: str
    relative_path: str


@dataclass(frozen=True, slots=True)
class PlanAuditConfig:
    """Resolved plan audit configuration."""

    roots: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PlanAuditState:
    """Mutable collections for one plan audit run."""

    failures: list[str]
    plans: list[PlanRecord]
    logs: list[LogRecord]


DEFAULT_PLAN_ROOTS = ("docs/plans",)
PLAN_DOCUMENT_TYPES = ("plan", "plan_log")
PLAN_STATUSES = ("active", "pending", "blocked")
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
    resolved_root = root.resolve()
    config = _resolve_plan_config(raw_config)
    configured_roots = tuple((resolved_root / item).resolve() for item in config.roots)
    state = PlanAuditState(
        failures=[],
        plans=[],
        logs=[],
    )
    for path in _candidate_document_paths(resolved_root):
        _process_document(path, resolved_root, configured_roots, state)

    state.failures.extend(_reference_failures(state.plans, state.logs))
    if state.failures:
        return PlanHygieneReport(False, _summarize_failures(state.failures))

    existing_roots = [path for path in configured_roots if path.exists()]
    if not existing_roots:
        return PlanHygieneReport(True, "no configured plan roots found")
    return PlanHygieneReport(
        True,
        f"{len(state.plans)} plan(s) and {len(state.logs)} log(s) across "
        f"{len(existing_roots)} plan root(s)",
    )


def _process_document(
    path: Path,
    root: Path,
    configured_roots: Sequence[Path],
    state: PlanAuditState,
) -> None:
    relative_path = path.relative_to(root).as_posix()
    inside_plan_root = any(_is_relative_to(path, plan_root) for plan_root in configured_roots)
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
    if _is_plan_or_log_like_path(path):
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
    roots = _string_tuple(raw_roots)
    if roots:
        return PlanAuditConfig(roots)
    return PlanAuditConfig(DEFAULT_PLAN_ROOTS)


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
    _require_created(metadata, relative_path, failures)
    depends_on = _optional_string_tuple(metadata.get("depends_on"), relative_path, failures)

    if status == "complete":
        failures.append(f"{relative_path}: complete plans must be closed out and removed")
    elif status and status not in PLAN_STATUSES:
        failures.append(f"{relative_path}: invalid status {status!r}")

    if not plan_id:
        return None
    return PlanRecord(plan_id, relative_path, depends_on)


def _log_record(
    relative_path: str,
    metadata: Mapping[str, object],
    failures: list[str],
) -> LogRecord | None:
    log_id = _required_string(metadata, "id", relative_path, failures)
    plan_id = _required_string(metadata, "plan_id", relative_path, failures)
    _require_created(metadata, relative_path, failures)
    if not log_id or not plan_id:
        return None
    return LogRecord(log_id, plan_id, relative_path)


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


def _require_created(
    metadata: Mapping[str, object],
    relative_path: str,
    failures: list[str],
) -> None:
    value = metadata.get("created")
    if isinstance(value, str) and value.strip():
        return
    if isinstance(value, date | datetime):
        return
    failures.append(f"{relative_path}: missing created")


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
    stem = path.stem.lower()
    return any(token in stem for token in PLAN_LIKE_NAME_TOKENS)


def _is_log_like_path(path: Path) -> bool:
    stem = path.stem.lower()
    if any(token in stem for token in LOG_LIKE_NAME_TOKENS):
        return True
    return any(part.lower() in LOG_LIKE_DIRECTORY_NAMES for part in path.parts)


def _is_plan_or_log_like_path(path: Path) -> bool:
    return _is_plan_like_path(path) or _is_log_like_path(path)


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
