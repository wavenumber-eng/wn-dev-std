from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from wn_dev_std.governance_html import generate_governance_html


def test_generate_governance_html_writes_pages_with_data_tags(tmp_path: Path) -> None:
    write_governance_repo(tmp_path)

    report = generate_governance_html(
        tmp_path,
        tmp_path / "docs" / "generated" / "governance",
        css_hrefs=("governance.css",),
    )

    assert len(report.pages) == 3
    index = tmp_path / "docs" / "generated" / "governance" / "index.html"
    plan_page = tmp_path / "docs" / "generated" / "governance" / "plan" / "demo-plan.html"
    adr_page = tmp_path / "docs" / "generated" / "governance" / "adr" / "core-adr-0001.html"
    req_page = tmp_path / "docs" / "generated" / "governance" / "requirement" / "core-req-0001.html"
    assert index.exists()
    assert (tmp_path / "docs" / "generated" / "governance" / "governance.css").exists()
    assert plan_page.exists()
    assert adr_page.exists()
    assert req_page.exists()
    text = req_page.read_text(encoding="utf-8")
    assert 'data-governance-type="requirement"' in text
    assert 'data-governance-id="core-req-0001"' in text
    assert 'data-governance-source="docs/core/requirements/core-req-0001-demo.md"' in text
    assert '<link rel="stylesheet" href="governance.css">' in text
    assert '<main id="governance-page" class="governance-page governance-page-requirement">' in text
    assert 'id="governance-metadata"' in text
    assert 'data-governance-field="status"' in text
    assert 'class="governance-metadata-value governance-metadata-value-string"' in text
    assert "../adr/core-adr-0001.html" in text
    assert 'class="governance-evidence-table"' in text
    assert 'class="governance-evidence-key">target</th>' in text
    assert '<div class="governance-body">' in text
    assert '<h1 class="governance-heading governance-heading-1">Demo Requirement</h1>' in text


def test_generate_governance_html_fails_noncompliant_catalog(tmp_path: Path) -> None:
    write_file(
        tmp_path / "docs" / "plans" / "bad-plan.md",
        "# Missing front matter\n",
    )

    try:
        generate_governance_html(tmp_path, tmp_path / "out")
    except ValueError as exc:
        assert "governance catalog is not compliant" in str(exc)
    else:
        raise AssertionError("expected ValueError for noncompliant catalog")


def write_governance_repo(root: Path) -> None:
    write_file(root / "dev-std.toml", 'profile = "python-package"\n')
    write_file(root / "tests" / "test_demo.py", "def test_demo():\n    assert True\n")
    write_file(
        root / "docs" / "plans" / "demo-plan.md",
        dedent(
            """
            +++
            type = "plan"
            id = "demo-plan"
            status = "active"
            created = "2026-07-02"
            issue_refs = ["wavenumber-eng/example#1"]

            [[exit_criteria]]
            id = "review"
            title = "Review is complete"
            status = "pending"
            +++

            # Demo Plan
            """
        ).lstrip(),
    )
    write_file(
        root / "docs" / "core" / "adr" / "core-adr-0001-demo.md",
        dedent(
            """
            +++
            type = "adr"
            id = "core-adr-0001"
            domain = "core"
            status = "accepted"
            title = "Demo Decision"
            created = "2026-07-02"
            +++

            # Demo Decision
            """
        ).lstrip(),
    )
    write_file(
        root / "docs" / "core" / "requirements" / "core-req-0001-demo.md",
        dedent(
            """
            +++
            type = "requirement"
            id = "core-req-0001"
            domain = "core"
            status = "active"
            title = "Demo Requirement"
            created = "2026-07-02"
            adr_refs = ["core-adr-0001"]

            [[verification_refs]]
            kind = "local_pytest"
            target = "tests/test_demo.py::test_demo"
            +++

            # Demo Requirement
            """
        ).lstrip(),
    )


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
