from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from textwrap import dedent

from config_fixtures import standard_config

from wn_dev_std.checks import run_audit_checks
from wn_dev_std.governance_links import resolve_governance_links


def test_resolve_governance_links_rewrites_nested_anchor(tmp_path: Path) -> None:
    write_governance_repo(tmp_path)
    design_doc = tmp_path / "docs" / "core" / "design" / "nested" / "index.html"
    write_file(
        design_doc,
        '<a class="decision" data-dev-std-gov-ref="core-adr-0001">Decision</a>\n',
    )

    report = resolve_governance_links(tmp_path, tmp_path / "docs" / "site" / "gov", write=True)

    assert report.passed
    assert report.resolved_count == 1
    assert report.changed_files == ("docs/core/design/nested/index.html",)
    text = design_doc.read_text(encoding="utf-8")
    assert 'href="../../../site/gov/adr/core-adr-0001.html"' in text
    audit = run_audit_checks(tmp_path, ("docs.links",))[0]
    assert audit.passed


def test_resolve_governance_links_fails_missing_id(tmp_path: Path) -> None:
    write_governance_repo(tmp_path)
    write_file(
        tmp_path / "docs" / "core" / "design" / "index.html",
        '<a href="../../site/gov/adr/missing.html" data-dev-std-gov-ref="missing">Missing</a>\n',
    )

    report = resolve_governance_links(tmp_path, tmp_path / "docs" / "site" / "gov")

    assert not report.passed
    assert "unknown governance ref 'missing'" in report.issues[0].message


def test_docs_links_audit_fails_bad_governance_href(tmp_path: Path) -> None:
    write_governance_repo(tmp_path)
    write_file(
        tmp_path / "docs" / "core" / "design" / "index.html",
        '<a href="wrong.html" data-dev-std-gov-ref="core-adr-0001">Decision</a>\n',
    )

    result = next(
        result
        for result in run_audit_checks(tmp_path, ("docs.links",))
        if result.scope == "docs.links"
    )

    assert not result.passed
    assert "should be '../../site/gov/adr/core-adr-0001.html'" in result.detail


def test_docs_links_audit_fails_missing_governance_href(tmp_path: Path) -> None:
    write_governance_repo(tmp_path)
    write_file(
        tmp_path / "docs" / "core" / "design" / "index.html",
        '<a data-dev-std-gov-ref="core-adr-0001">Decision</a>\n',
    )

    result = next(
        result
        for result in run_audit_checks(tmp_path, ("docs.links",))
        if result.scope == "docs.links"
    )

    assert not result.passed
    assert "missing href" in result.detail


def test_governance_resolve_cli_writes_links(tmp_path: Path) -> None:
    write_governance_repo(tmp_path)
    write_file(
        tmp_path / "docs" / "core" / "design" / "index.html",
        '<a data-dev-std-gov-ref="core-req-0001">Requirement</a>\n',
    )

    result = run_cli(
        tmp_path,
        "gov",
        "resolve",
        "--root",
        str(tmp_path),
        "--write",
    )

    assert result.returncode == 0
    assert "Governance links updated" in result.stdout
    text = (tmp_path / "docs" / "core" / "design" / "index.html").read_text(encoding="utf-8")
    assert 'href="../../site/gov/requirement/core-req-0001.html"' in text


def write_governance_repo(root: Path) -> None:
    write_file(
        root / "dev-std.toml",
        standard_config(
            extra="""
            [governance.html]
            output = "docs/site/gov"
            """,
        ),
    )
    write_file(
        root / "docs" / "core" / "adr" / "core-adr-0001-decision.md",
        dedent(
            """
            +++
            type = "adr"
            id = "core-adr-0001"
            domain = "core"
            status = "accepted"
            title = "Decision"
            created = "2026-07-02"
            +++

            # Decision
            """
        ).lstrip(),
    )
    write_file(
        root / "docs" / "core" / "requirements" / "core-req-0001-requirement.md",
        dedent(
            """
            +++
            type = "requirement"
            id = "core-req-0001"
            domain = "core"
            status = "active"
            title = "Requirement"
            created = "2026-07-02"

            [[verification_refs]]
            kind = "local_file"
            target = "docs/core/adr/core-adr-0001-decision.md"
            +++

            # Requirement
            """
        ).lstrip(),
    )
    write_file(root / "docs" / "site" / "gov" / "adr" / "core-adr-0001.html", "<html></html>\n")
    write_file(
        root / "docs" / "site" / "gov" / "requirement" / "core-req-0001.html",
        "<html></html>\n",
    )


def run_cli(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "wn_dev_std", *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
