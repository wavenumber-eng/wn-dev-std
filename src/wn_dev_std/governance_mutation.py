"""Mutation helpers for durable governance documents."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Protocol

from wn_dev_std.doc_governance import ADR_STATUSES, REQUIREMENT_STATUSES


class GovernanceCatalogLike(Protocol):
    """Catalog shape needed by governance mutation helpers."""

    @property
    def root(self) -> Path:
        """Governance catalog root."""
        ...


class GovernanceMutationContext(Protocol):
    """Context shape needed by governance mutation helpers."""

    @property
    def catalog(self) -> GovernanceCatalogLike:
        """Governance catalog."""
        ...


@dataclass(frozen=True, slots=True)
class GovernanceMutationResult:
    """Result of a governance document mutation."""

    path: Path
    detail: str


class GovernanceMutationError(ValueError):
    """Raised when a governance mutation cannot be applied."""


def create_adr(
    context: GovernanceMutationContext,
    record_id: str,
    title: str,
    *,
    domain: str,
    status: str = "proposed",
    created: str | None = None,
    body: str | None = None,
) -> GovernanceMutationResult:
    """Create a compliant ADR document."""
    _validate_status(status, ADR_STATUSES)
    path = _governance_path(_catalog_root(context), domain, "adr", record_id, title)
    text = _document_text(
        "adr",
        record_id,
        domain,
        status,
        title,
        created,
        body,
    )
    return _write_new(path, text, "created ADR")


def create_requirement(
    context: GovernanceMutationContext,
    record_id: str,
    title: str,
    *,
    domain: str,
    status: str = "draft",
    created: str | None = None,
    body: str | None = None,
) -> GovernanceMutationResult:
    """Create a compliant requirement document."""
    _validate_status(status, REQUIREMENT_STATUSES)
    path = _governance_path(_catalog_root(context), domain, "requirements", record_id, title)
    text = _document_text(
        "requirement",
        record_id,
        domain,
        status,
        title,
        created,
        body,
    )
    return _write_new(path, text, "created requirement")


def _validate_status(status: str, statuses: tuple[str, ...]) -> None:
    if status not in statuses:
        raise GovernanceMutationError(f"invalid status {status!r}; expected " + ", ".join(statuses))


def _catalog_root(context: GovernanceMutationContext) -> Path:
    return context.catalog.root


def _governance_path(
    root: Path,
    domain: str,
    directory_name: str,
    record_id: str,
    title: str,
) -> Path:
    _validate_nonempty("domain", domain)
    _validate_nonempty("id", record_id)
    _validate_nonempty("title", title)
    return root / "docs" / domain / directory_name / f"{record_id}-{_slug(title)}.md"


def _document_text(
    record_type: str,
    record_id: str,
    domain: str,
    status: str,
    title: str,
    created: str | None,
    body: str | None,
) -> str:
    created_value = created or date.today().isoformat()
    body_text = body.strip() if body and body.strip() else f"# {title}"
    return (
        "+++\n"
        f'type = "{_toml_string(record_type)}"\n'
        f'id = "{_toml_string(record_id)}"\n'
        f'domain = "{_toml_string(domain)}"\n'
        f'status = "{_toml_string(status)}"\n'
        f'title = "{_toml_string(title)}"\n'
        f'created = "{_toml_string(created_value)}"\n'
        "+++\n\n"
        f"{body_text}\n"
    )


def _write_new(path: Path, text: str, detail: str) -> GovernanceMutationResult:
    if path.exists():
        raise GovernanceMutationError(f"governance document already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return GovernanceMutationResult(path, detail)


def _validate_nonempty(name: str, value: str) -> None:
    if not value.strip():
        raise GovernanceMutationError(f"missing {name}")


def _toml_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _slug(value: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "-" for char in value.strip())
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "document"
