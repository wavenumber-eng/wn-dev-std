"""Generate browseable HTML for governance documents."""

from __future__ import annotations

import html
import os
import shutil
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from wn_dev_std.doc_governance import GovernanceCatalog, load_governance_catalog
from wn_dev_std.governance_markdown import render_governance_markdown
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
METADATA_FIELD_PRIORITY = ("id", "status")


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
    docs = (*docs, *_catalog_documents(resolved_root))
    link_index = _link_index(docs)
    default_css = _copy_default_css(resolved_output)
    all_css_hrefs = (default_css, *css_hrefs)
    pages = tuple(
        _write_document_page(
            resolved_root,
            resolved_output,
            doc,
            docs,
            link_index,
            all_css_hrefs,
        )
        for doc in docs
    )
    _write_index_page(resolved_output, pages, all_css_hrefs)
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


def _catalog_documents(root: Path) -> tuple[GovernanceHtmlDocument, ...]:
    catalog_specs = (
        ("artifact_catalog", "artifacts", "Artifact Governance Catalog", "artifacts"),
        ("vendor_catalog", "vendors", "Vendor Governance Catalog", "vendors"),
        ("release_catalog", "release", "Release Governance Catalog", "channels"),
    )
    docs: list[GovernanceHtmlDocument] = []
    for kind, record_id, title, table_key in catalog_specs:
        path = root / "docs" / "governance" / f"{record_id}.toml"
        if not path.exists():
            continue
        payload = _load_toml_catalog(path)
        docs.append(
            GovernanceHtmlDocument(
                kind,
                record_id,
                "governance",
                "active",
                title,
                path.relative_to(root).as_posix(),
                {
                    "id": record_id,
                    "status": "active",
                    "type": kind,
                    "source": path.relative_to(root).as_posix(),
                },
                _catalog_markdown(title, table_key, payload),
            )
        )
    return tuple(docs)


def _load_toml_catalog(path: Path) -> Mapping[str, object]:
    with path.open("rb") as handle:
        return cast(Mapping[str, object], tomllib.load(handle))


def _catalog_markdown(
    title: str,
    table_key: str,
    payload: Mapping[str, object],
) -> str:
    rows = _catalog_rows(payload.get(table_key))
    if not rows:
        return f"## {title}\n\nNo `{table_key}` entries are registered."
    columns = _catalog_columns(rows)
    lines = [
        f"## {title}",
        "",
        f"Registered `{table_key}` entries.",
        "",
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_catalog_cell(row.get(column)) for column in columns) + " |")
    return "\n".join(lines)


def _catalog_rows(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, list):
        return ()
    rows: list[Mapping[str, object]] = []
    for item in cast(list[object], value):
        if isinstance(item, dict):
            rows.append(cast(Mapping[str, object], item))
    return tuple(rows)


def _catalog_columns(rows: Sequence[Mapping[str, object]]) -> tuple[str, ...]:
    priority = ("id", "kind", "status", "tracked", "included_in_release", "owner")
    keys: list[str] = []
    for key in priority:
        if any(key in row for row in rows):
            keys.append(key)
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    return tuple(keys)


def _catalog_cell(value: object) -> str:
    if isinstance(value, list):
        rendered_items = [_catalog_list_item(item) for item in cast(list[object], value)]
        return ", ".join(rendered_items)
    if isinstance(value, dict):
        typed_value = cast(Mapping[str, object], value)
        return ", ".join(f"{key}={item}" for key, item in typed_value.items())
    if value is None:
        return ""
    return str(value)


def _catalog_list_item(item: object) -> str:
    if not isinstance(item, dict):
        return str(item)
    typed_item = cast(Mapping[str, object], item)
    for key in ("id", "target", "kind"):
        value = typed_item.get(key)
        if value is not None:
            return str(value)
    return "table"


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
    docs: Sequence[GovernanceHtmlDocument],
    link_index: Mapping[str, str],
    css_hrefs: Sequence[str],
) -> GovernanceHtmlPage:
    output_path = output_root / doc.kind / f"{_safe_filename(doc.record_id)}.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        _document_html(root, output_root, output_path, doc, docs, link_index, css_hrefs),
        encoding="utf-8",
    )
    return GovernanceHtmlPage(doc.kind, doc.record_id, doc.source_path, output_path)


def _write_index_page(
    output_root: Path,
    pages: Sequence[GovernanceHtmlPage],
    css_hrefs: Sequence[str],
) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    items = "\n".join(
        '<li class="dev-std-gov-index-item">'
        f'<a href="{html.escape(_relative_href(output_root / "index.html", page.output_path))}">'
        f"{html.escape(page.kind)}: {html.escape(page.record_id)}</a>"
        f" <code>{html.escape(page.source_path)}</code></li>"
        for page in pages
    )
    output_path = output_root / "index.html"
    css = _css_links(output_root, output_path, css_hrefs)
    text = (
        '<!doctype html>\n<html lang="en">\n<head>\n'
        '  <meta charset="utf-8">\n'
        "  <title>Governance Index</title>\n"
        f"{css}</head>\n"
        '<body data-dev-std-gov-index="true">\n'
        '  <main class="dev-std-gov-page dev-std-gov-index-page">\n'
        '    <header class="dev-std-gov-header">\n'
        '      <h1 class="dev-std-gov-title">Governance Index</h1>\n'
        "    </header>\n"
        '    <section id="dev-std-gov-index" '
        'class="dev-std-gov-section dev-std-gov-index-section">\n'
        f'      <ul class="dev-std-gov-index-items">\n{items}\n      </ul>\n'
        "    </section>\n"
        "  </main>\n"
        "</body>\n</html>\n"
    )
    output_path.write_text(text, encoding="utf-8")


def _document_html(
    root: Path,
    output_root: Path,
    output_path: Path,
    doc: GovernanceHtmlDocument,
    docs: Sequence[GovernanceHtmlDocument],
    link_index: Mapping[str, str],
    css_hrefs: Sequence[str],
) -> str:
    data_attrs = _data_attrs(doc)
    metadata_rows = _metadata_rows(root, output_path, doc, link_index)
    plan_steps = _plan_steps_html(output_path, doc, docs)
    css = _css_links(output_root, output_path, css_hrefs)
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n'
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"  <title>{html.escape(doc.title)}</title>\n"
        f"{css}</head>\n"
        f"<body {data_attrs}>\n"
        f'  <main id="dev-std-gov-page" class="dev-std-gov-page dev-std-gov-page-{doc.kind}">\n'
        '    <header id="dev-std-gov-summary" class="dev-std-gov-header dev-std-gov-summary">\n'
        f'      <h1 class="dev-std-gov-title">{html.escape(doc.title)}</h1>\n'
        f'      <p class="dev-std-gov-source"><code>{html.escape(doc.source_path)}</code></p>\n'
        "    </header>\n"
        '    <section id="dev-std-gov-meta" class="dev-std-gov-section dev-std-gov-meta" '
        'data-dev-std-gov-section="metadata">\n'
        '      <h2 class="dev-std-gov-section-title">Metadata</h2>\n'
        f'      <table class="dev-std-gov-meta-table">\n{metadata_rows}\n      </table>\n'
        "    </section>\n"
        '    <section id="dev-std-gov-body" class="dev-std-gov-section dev-std-gov-doc-body" '
        'data-dev-std-gov-section="body">\n'
        '      <h2 class="dev-std-gov-section-title">Body</h2>\n'
        f"      {render_governance_markdown(doc.body)}\n"
        "    </section>\n"
        f"{plan_steps}"
        "  </main>\n"
        "</body>\n</html>\n"
    )


def _plan_steps_html(
    output_path: Path,
    doc: GovernanceHtmlDocument,
    docs: Sequence[GovernanceHtmlDocument],
) -> str:
    if doc.kind != "plan":
        return ""
    steps = _metadata_tables(doc.metadata.get("steps"))
    if not steps:
        return ""
    logs = [
        item
        for item in docs
        if item.kind == "plan_log" and _string_value(item.metadata.get("plan_id")) == doc.record_id
    ]
    rows = "".join(_plan_step_html(output_path, step, logs) for step in steps)
    unlinked_logs = [log for log in logs if not _string_value(log.metadata.get("step_id"))]
    if unlinked_logs:
        rows += _plan_unlinked_logs_html(output_path, unlinked_logs)
    return (
        '    <section id="dev-std-gov-plan-steps" '
        'class="dev-std-gov-section dev-std-gov-plan-steps" '
        'data-dev-std-gov-section="plan-steps">\n'
        '      <h2 class="dev-std-gov-section-title">Steps And Logs</h2>\n'
        f"{rows}"
        "    </section>\n"
    )


def _plan_step_html(
    output_path: Path,
    step: Mapping[str, object],
    logs: Sequence[GovernanceHtmlDocument],
) -> str:
    step_id = _string_value(step.get("id"))
    title = _string_value(step.get("title")) or step_id
    status = _string_value(step.get("status"))
    step_logs = [log for log in logs if _string_value(log.metadata.get("step_id")) == step_id]
    log_count = len(step_logs)
    log_word = "log" if log_count == 1 else "logs"
    return (
        '      <article class="dev-std-gov-step" '
        f'data-dev-std-gov-step-id="{html.escape(step_id)}">\n'
        f'        <h3 class="dev-std-gov-step-title">{html.escape(title)}</h3>\n'
        f'        <p class="dev-std-gov-step-status"><code>{html.escape(status)}</code></p>\n'
        '        <details class="dev-std-gov-step-logs" open>\n'
        f"          <summary>{log_count} {log_word}</summary>\n"
        f"{_plan_log_items_html(output_path, step_logs)}"
        "        </details>\n"
        "      </article>\n"
    )


def _plan_unlinked_logs_html(
    output_path: Path,
    logs: Sequence[GovernanceHtmlDocument],
) -> str:
    return (
        '      <article class="dev-std-gov-step dev-std-gov-step-unlinked" '
        'data-dev-std-gov-step-id="">\n'
        '        <h3 class="dev-std-gov-step-title">Unlinked Logs</h3>\n'
        '        <details class="dev-std-gov-step-logs" open>\n'
        f"          <summary>{len(logs)} log(s)</summary>\n"
        f"{_plan_log_items_html(output_path, logs)}"
        "        </details>\n"
        "      </article>\n"
    )


def _plan_log_items_html(
    output_path: Path,
    logs: Sequence[GovernanceHtmlDocument],
) -> str:
    if not logs:
        return '          <p class="dev-std-gov-step-log-empty">No logs.</p>\n'
    items = "".join(_plan_log_item_html(output_path, log) for log in logs)
    return f'          <div class="dev-std-gov-step-log-items">\n{items}          </div>\n'


def _plan_log_item_html(output_path: Path, log: GovernanceHtmlDocument) -> str:
    href = _relative_href(
        output_path,
        output_path.parent.parent / "plan_log" / f"{_safe_filename(log.record_id)}.html",
    )
    created = _string_value(log.metadata.get("created"))
    return (
        '            <section class="dev-std-gov-step-log" '
        f'data-dev-std-gov-log-id="{html.escape(log.record_id)}">\n'
        f'              <h4><a href="{html.escape(href)}">{html.escape(log.record_id)}</a></h4>\n'
        '              <p class="dev-std-gov-step-log-created">'
        f"<code>{html.escape(created)}</code></p>\n"
        '              <div class="dev-std-gov-log-body">'
        f"{render_governance_markdown(log.body)}</div>\n"
        "            </section>\n"
    )


def _data_attrs(doc: GovernanceHtmlDocument) -> str:
    attrs = {
        "data-dev-std-gov-type": doc.kind,
        "data-dev-std-gov-id": doc.record_id,
        "data-dev-std-gov-source": doc.source_path,
        "data-dev-std-gov-status": doc.status,
        "data-dev-std-gov-domain": doc.domain,
    }
    return " ".join(f'{key}="{html.escape(value)}"' for key, value in attrs.items() if value)


def _metadata_rows(
    root: Path,
    output_path: Path,
    doc: GovernanceHtmlDocument,
    link_index: Mapping[str, str],
) -> str:
    rows: list[str] = []
    for key, value in sorted(doc.metadata.items(), key=_metadata_sort_key):
        escaped_key = html.escape(key)
        value_kind = _value_kind(value)
        row_classes = _metadata_row_classes(key, value)
        value_classes = _metadata_value_classes(key, value, value_kind)
        rows.append(
            f'        <tr class="{row_classes}" data-dev-std-gov-field="{escaped_key}">'
            f'<th class="dev-std-gov-meta-key">{escaped_key}</th>'
            f'<td class="{value_classes}">'
            f"{_metadata_value_html(root, output_path, key, value, link_index)}</td>"
            "</tr>"
        )
    return "\n".join(rows)


def _metadata_tables(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, list):
        return ()
    return tuple(
        cast(Mapping[str, object], item)
        for item in cast(list[object], value)
        if isinstance(item, dict)
    )


def _metadata_value_html(
    root: Path,
    output_path: Path,
    key: str,
    value: object,
    link_index: Mapping[str, str],
) -> str:
    if _is_table_array_value(value):
        return _table_array_value_html(root, output_path, cast(list[object], value), link_index)
    if key in REF_KEYS and isinstance(value, list):
        items = [
            _ref_html(root, output_path, str(item), link_index)
            for item in cast(list[object], value)
        ]
        return (
            '<ul class="dev-std-gov-meta-list">'
            + "".join(f'<li class="dev-std-gov-meta-list-item">{item}</li>' for item in items)
            + "</ul>"
        )
    return f"<code>{html.escape(str(value))}</code>"


def _is_table_array_value(value: object) -> bool:
    if not isinstance(value, list):
        return False
    return all(isinstance(item, dict) for item in cast(list[object], value))


def _table_array_value_html(
    root: Path,
    output_path: Path,
    value: list[object],
    link_index: Mapping[str, str],
) -> str:
    items = [cast(Mapping[str, object], item) for item in value if isinstance(item, dict)]
    rows = "".join(_evidence_row_html(root, output_path, item, link_index) for item in items)
    return f'<table class="dev-std-gov-evidence-table"><tbody>{rows}</tbody></table>'


def _evidence_row_html(
    root: Path,
    output_path: Path,
    item: Mapping[str, object],
    link_index: Mapping[str, str],
) -> str:
    cells = "".join(
        "<tr>"
        f'<th class="dev-std-gov-evidence-key dev-std-gov-evidence-key-{_field_class_suffix(key)}">'
        f"{html.escape(key)}</th>"
        f'<td class="{_evidence_value_classes(key, raw_value)}">'
        f"{_evidence_value_html(root, output_path, key, raw_value, link_index)}</td>"
        "</tr>"
        for key, raw_value in sorted(item.items(), key=_metadata_sort_key)
    )
    return f'<tr class="dev-std-gov-evidence-item"><td colspan="2"><table>{cells}</table></td></tr>'


def _evidence_value_html(
    root: Path,
    output_path: Path,
    key: str,
    value: object,
    link_index: Mapping[str, str],
) -> str:
    if key in {"target", "surface_ref", "source_surface_ref", "target_surface_ref"}:
        return _ref_html(root, output_path, str(value), link_index)
    if key.endswith("_refs") and isinstance(value, list):
        items = [
            _ref_html(root, output_path, str(item), link_index)
            for item in cast(list[object], value)
        ]
        return (
            '<ul class="dev-std-gov-meta-list">'
            + "".join(f'<li class="dev-std-gov-meta-list-item">{item}</li>' for item in items)
            + "</ul>"
        )
    return f"<code>{html.escape(str(value))}</code>"


def _ref_html(
    root: Path,
    output_path: Path,
    value: str,
    link_index: Mapping[str, str],
) -> str:
    if value in link_index:
        return (
            f'<a class="dev-std-gov-ref dev-std-gov-ref-local" '
            f'href="{html.escape(link_index[value])}">{html.escape(value)}</a>'
        )
    if value.startswith("docs/") or value.startswith("tests/") or value.startswith("src/"):
        file_part = _file_ref_target(value)
        target = root / file_part
        href = _relative_href(output_path, target) if target.exists() else value
        return (
            f'<a class="dev-std-gov-ref dev-std-gov-ref-file" '
            f'href="{html.escape(href)}">{html.escape(value)}</a>'
        )
    return html.escape(value)


def _file_ref_target(value: str) -> str:
    end = len(value)
    for marker in ("::", "#", "?"):
        marker_index = value.find(marker)
        if marker_index >= 0:
            end = min(end, marker_index)
    return value[:end]


def _link_index(docs: Sequence[GovernanceHtmlDocument]) -> dict[str, str]:
    return {doc.record_id: f"../{doc.kind}/{_safe_filename(doc.record_id)}.html" for doc in docs}


def _css_links(output_root: Path, output_path: Path, css_hrefs: Sequence[str]) -> str:
    if not css_hrefs:
        return ""
    return "".join(
        '  <link rel="stylesheet" '
        f'href="{html.escape(_css_href(output_root, output_path, href))}">\n'
        for href in css_hrefs
    )


def _css_href(output_root: Path, output_path: Path, href: str) -> str:
    if _is_external_href(href):
        return href.replace("\\", "/")
    target = output_root / href
    return _relative_href(output_path, target)


def _is_external_href(href: str) -> bool:
    return (
        "://" in href
        or href.startswith(("/", "#"))
        or href.startswith("data:")
        or href.startswith("mailto:")
    )


def _copy_default_css(output_root: Path) -> str:
    output_root.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).resolve().parent / "assets" / "governance.css"
    target = output_root / "governance.css"
    shutil.copyfile(source, target)
    return "governance.css"


def _value_kind(value: object) -> str:
    if isinstance(value, list):
        return "list"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int | float):
        return "number"
    return "string"


def _metadata_sort_key(item: tuple[str, object]) -> tuple[int, str]:
    key, _value = item
    try:
        return (METADATA_FIELD_PRIORITY.index(key), key)
    except ValueError:
        return (len(METADATA_FIELD_PRIORITY), key)


def _metadata_row_classes(key: str, value: object) -> str:
    classes = [
        "dev-std-gov-meta-row",
        f"dev-std-gov-meta-row-{_field_class_suffix(key)}",
    ]
    classes.extend(_status_classes(key, value))
    return " ".join(classes)


def _metadata_value_classes(key: str, value: object, value_kind: str) -> str:
    classes = [
        "dev-std-gov-meta-val",
        f"dev-std-gov-meta-val-{value_kind}",
        f"dev-std-gov-meta-val-{_field_class_suffix(key)}",
    ]
    classes.extend(_status_classes(key, value))
    return " ".join(classes)


def _evidence_value_classes(key: str, value: object) -> str:
    classes = [
        "dev-std-gov-evidence-value",
        f"dev-std-gov-evidence-value-{_field_class_suffix(key)}",
    ]
    classes.extend(_status_classes(key, value))
    return " ".join(classes)


def _status_classes(key: str, value: object) -> list[str]:
    if key != "status" or not isinstance(value, str) or not value:
        return []
    return ["dev-std-gov-status", f"dev-std-gov-status-{_field_class_suffix(value)}"]


def _field_class_suffix(value: str) -> str:
    suffix = "".join(char.lower() if char.isalnum() else "-" for char in value)
    while "--" in suffix:
        suffix = suffix.replace("--", "-")
    return suffix.strip("-") or "empty"


def _safe_filename(value: str) -> str:
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in value)


def _relative_href(source: Path, target: Path) -> str:
    base = source.parent if source.suffix else source
    return os.path.relpath(target, base).replace("\\", "/")


def _string_value(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""
