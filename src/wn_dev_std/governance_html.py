"""Generate browseable HTML for governance documents."""

from __future__ import annotations

import html
import os
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from wn_dev_std.doc_governance import GovernanceCatalog, load_governance_catalog
from wn_dev_std.plan_hygiene import PlanCatalog, load_plan_catalog
from wn_dev_std.root_discovery import load_pyproject, load_standard_config


@dataclass(frozen=True, slots=True)
class GovernanceHtmlPage:
    """Generated governance HTML page."""

    kind: str
    record_id: str
    source_path: str
    output_path: Path


@dataclass(frozen=True, slots=True)
class GovernanceHtmlReport:
    """Generated governance HTML report."""

    output_root: Path
    pages: tuple[GovernanceHtmlPage, ...]


@dataclass(frozen=True, slots=True)
class GovernanceHtmlDocument:
    """Parsed governance document ready for rendering."""

    kind: str
    record_id: str
    domain: str
    status: str
    title: str
    source_path: str
    metadata: Mapping[str, object]
    body: str


REF_KEYS = (
    "issue_refs",
    "plan_refs",
    "adr_refs",
    "requirement_refs",
    "design_refs",
    "schema_refs",
)


def generate_governance_html(
    root: Path,
    output_root: Path,
    *,
    css_hrefs: Sequence[str] = (),
) -> GovernanceHtmlReport:
    """Generate governance HTML pages from compliant source documents."""
    resolved_root = root.resolve()
    resolved_output = output_root.resolve()
    plan_catalog = _load_plan_catalog(resolved_root)
    governance_catalog = load_governance_catalog(resolved_root)
    _raise_for_catalog_failures(plan_catalog, governance_catalog)
    docs = _documents_from_catalogs(plan_catalog, governance_catalog)
    link_index = _link_index(docs)
    pages = tuple(
        _write_document_page(resolved_root, resolved_output, doc, link_index, css_hrefs)
        for doc in docs
    )
    _write_index_page(resolved_output, pages, css_hrefs)
    return GovernanceHtmlReport(resolved_output, pages)


def _load_plan_catalog(root: Path) -> PlanCatalog:
    pyproject = load_pyproject(root)
    config = load_standard_config(root, pyproject)
    return load_plan_catalog(root, config)


def _raise_for_catalog_failures(
    plan_catalog: PlanCatalog,
    governance_catalog: GovernanceCatalog,
) -> None:
    failures = tuple(plan_catalog.failures) + tuple(governance_catalog.failures)
    if failures:
        raise ValueError("governance catalog is not compliant: " + "; ".join(failures))


def _documents_from_catalogs(
    plan_catalog: PlanCatalog,
    governance_catalog: GovernanceCatalog,
) -> tuple[GovernanceHtmlDocument, ...]:
    docs: list[GovernanceHtmlDocument] = []
    for plan in plan_catalog.plans:
        docs.append(
            _document_from_source(plan_catalog.root, "plan", plan.plan_id, plan.relative_path)
        )
    for log in plan_catalog.logs:
        docs.append(
            _document_from_source(plan_catalog.root, "plan_log", log.log_id, log.relative_path)
        )
    for adr in governance_catalog.adrs:
        docs.append(
            _document_from_source(governance_catalog.root, "adr", adr.record_id, adr.relative_path)
        )
    for requirement in governance_catalog.requirements:
        docs.append(
            _document_from_source(
                governance_catalog.root,
                "requirement",
                requirement.record_id,
                requirement.relative_path,
            )
        )
    return tuple(sorted(docs, key=lambda item: (item.kind, item.record_id)))


def _document_from_source(
    root: Path,
    kind: str,
    record_id: str,
    relative_path: str,
) -> GovernanceHtmlDocument:
    metadata, body = _parse_front_matter(root / relative_path)
    return GovernanceHtmlDocument(
        kind,
        record_id,
        _string_value(metadata.get("domain")),
        _string_value(metadata.get("status")),
        _string_value(metadata.get("title")) or record_id,
        relative_path,
        metadata,
        body,
    )


def _parse_front_matter(path: Path) -> tuple[Mapping[str, object], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "+++":
        return {}, text
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "+++":
            raw_front_matter = "\n".join(lines[1:index])
            metadata = cast(Mapping[str, object], tomllib.loads(raw_front_matter))
            body = "\n".join(lines[index + 1 :]).strip()
            return metadata, body
    return {}, ""


def _write_document_page(
    root: Path,
    output_root: Path,
    doc: GovernanceHtmlDocument,
    link_index: Mapping[str, str],
    css_hrefs: Sequence[str],
) -> GovernanceHtmlPage:
    output_path = output_root / doc.kind / f"{_safe_filename(doc.record_id)}.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        _document_html(root, output_path, doc, link_index, css_hrefs), encoding="utf-8"
    )
    return GovernanceHtmlPage(doc.kind, doc.record_id, doc.source_path, output_path)


def _write_index_page(
    output_root: Path,
    pages: Sequence[GovernanceHtmlPage],
    css_hrefs: Sequence[str],
) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    items = "\n".join(
        "<li>"
        f'<a href="{html.escape(_relative_href(output_root / "index.html", page.output_path))}">'
        f"{html.escape(page.kind)}: {html.escape(page.record_id)}</a>"
        f" <code>{html.escape(page.source_path)}</code></li>"
        for page in pages
    )
    css = _css_links(css_hrefs)
    text = (
        '<!doctype html>\n<html lang="en">\n<head>\n'
        '  <meta charset="utf-8">\n'
        "  <title>Governance Index</title>\n"
        f"{css}</head>\n"
        '<body data-governance-index="true">\n'
        "  <h1>Governance Index</h1>\n"
        f"  <ul>\n{items}\n  </ul>\n"
        "</body>\n</html>\n"
    )
    (output_root / "index.html").write_text(text, encoding="utf-8")


def _document_html(
    root: Path,
    output_path: Path,
    doc: GovernanceHtmlDocument,
    link_index: Mapping[str, str],
    css_hrefs: Sequence[str],
) -> str:
    data_attrs = _data_attrs(doc)
    metadata_rows = _metadata_rows(root, output_path, doc, link_index)
    css = _css_links(css_hrefs)
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n'
        '  <meta charset="utf-8">\n'
        f"  <title>{html.escape(doc.title)}</title>\n"
        f"{css}</head>\n"
        f"<body {data_attrs}>\n"
        f"  <h1>{html.escape(doc.title)}</h1>\n"
        f"  <p><code>{html.escape(doc.source_path)}</code></p>\n"
        f"  <table>\n{metadata_rows}\n  </table>\n"
        f'  <pre class="governance-body">{html.escape(doc.body)}</pre>\n'
        "</body>\n</html>\n"
    )


def _data_attrs(doc: GovernanceHtmlDocument) -> str:
    attrs = {
        "data-governance-type": doc.kind,
        "data-governance-id": doc.record_id,
        "data-governance-source": doc.source_path,
        "data-governance-status": doc.status,
        "data-governance-domain": doc.domain,
    }
    return " ".join(f'{key}="{html.escape(value)}"' for key, value in attrs.items() if value)


def _metadata_rows(
    root: Path,
    output_path: Path,
    doc: GovernanceHtmlDocument,
    link_index: Mapping[str, str],
) -> str:
    rows: list[str] = []
    for key, value in sorted(doc.metadata.items()):
        rows.append(
            "    <tr>"
            f"<th>{html.escape(key)}</th>"
            f"<td>{_metadata_value_html(root, output_path, key, value, link_index)}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def _metadata_value_html(
    root: Path,
    output_path: Path,
    key: str,
    value: object,
    link_index: Mapping[str, str],
) -> str:
    if key in REF_KEYS and isinstance(value, list):
        items = [
            _ref_html(root, output_path, str(item), link_index)
            for item in cast(list[object], value)
        ]
        return "<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>"
    return f"<code>{html.escape(str(value))}</code>"


def _ref_html(
    root: Path,
    output_path: Path,
    value: str,
    link_index: Mapping[str, str],
) -> str:
    if value in link_index:
        return f'<a href="{html.escape(link_index[value])}">{html.escape(value)}</a>'
    if value.startswith("docs/") or value.startswith("tests/") or value.startswith("src/"):
        target = root / value
        href = _relative_href(output_path, target) if target.exists() else value
        return f'<a href="{html.escape(href)}">{html.escape(value)}</a>'
    return html.escape(value)


def _link_index(docs: Sequence[GovernanceHtmlDocument]) -> dict[str, str]:
    return {doc.record_id: f"../{doc.kind}/{_safe_filename(doc.record_id)}.html" for doc in docs}


def _css_links(css_hrefs: Sequence[str]) -> str:
    if not css_hrefs:
        return ""
    return "".join(f'  <link rel="stylesheet" href="{html.escape(href)}">\n' for href in css_hrefs)


def _safe_filename(value: str) -> str:
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in value)


def _relative_href(source: Path, target: Path) -> str:
    base = source.parent if source.suffix else source
    return os.path.relpath(target, base).replace("\\", "/")


def _string_value(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""
