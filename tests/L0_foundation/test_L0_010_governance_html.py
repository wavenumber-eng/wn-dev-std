from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from config_fixtures import standard_config

from wn_dev_std.governance_html import generate_governance_html


def test_generate_governance_html_writes_pages_with_data_tags(tmp_path: Path) -> None:
    write_governance_repo(tmp_path)

    report = generate_governance_html(
        tmp_path,
        tmp_path / "docs" / "generated" / "governance",
        css_hrefs=("../styles.css",),
    )

    assert len(report.pages) == 4
    index = tmp_path / "docs" / "generated" / "governance" / "index.html"
    plan_page = tmp_path / "docs" / "generated" / "governance" / "plan" / "demo-plan.html"
    log_page = tmp_path / "docs" / "generated" / "governance" / "plan_log" / "demo-log.html"
    adr_page = tmp_path / "docs" / "generated" / "governance" / "adr" / "core-adr-0001.html"
    req_page = tmp_path / "docs" / "generated" / "governance" / "requirement" / "core-req-0001.html"
    assert index.exists()
    assert (tmp_path / "docs" / "generated" / "governance" / "governance.css").exists()
    assert plan_page.exists()
    assert log_page.exists()
    assert adr_page.exists()
    assert req_page.exists()
    plan_text = plan_page.read_text(encoding="utf-8")
    assert 'id="dev-std-gov-plan-steps"' in plan_text
    assert 'data-dev-std-gov-step-id="implement"' in plan_text
    assert '<details class="dev-std-gov-step-logs" open>' in plan_text
    assert '../plan_log/demo-log.html">demo-log</a>' in plan_text
    assert '<div class="dev-std-gov-log-body">' in plan_text
    assert "Implemented the demo step." in plan_text
    text = req_page.read_text(encoding="utf-8")
    assert 'data-dev-std-gov-type="requirement"' in text
    assert 'data-dev-std-gov-id="core-req-0001"' in text
    assert 'data-dev-std-gov-source="docs/core/requirements/core-req-0001-demo.md"' in text
    assert '<link rel="stylesheet" href="../governance.css">' in text
    assert '<link rel="stylesheet" href="../../styles.css">' in text
    assert (
        '<main id="dev-std-gov-page" class="dev-std-gov-page dev-std-gov-page-requirement">' in text
    )
    assert 'id="dev-std-gov-meta"' in text
    assert text.index('data-dev-std-gov-field="id"') < text.index('data-dev-std-gov-field="status"')
    assert text.index('data-dev-std-gov-field="status"') < text.index(
        'data-dev-std-gov-field="adr_refs"'
    )
    assert 'class="dev-std-gov-meta-row dev-std-gov-meta-row-id"' in text
    assert (
        'class="dev-std-gov-meta-row dev-std-gov-meta-row-status '
        'dev-std-gov-status dev-std-gov-status-active"'
    ) in text
    assert (
        'class="dev-std-gov-meta-val dev-std-gov-meta-val-string '
        'dev-std-gov-meta-val-status dev-std-gov-status dev-std-gov-status-active"'
    ) in text
    assert 'data-dev-std-gov-field="status"' in text
    assert "dev-std-gov-meta-val-string" in text
    assert "../adr/core-adr-0001.html" in text
    assert 'class="dev-std-gov-evidence-table"' in text
    assert 'class="dev-std-gov-evidence-key dev-std-gov-evidence-key-target">target</th>' in text
    assert 'href="../../../../tests/test_demo.py">tests/test_demo.py::test_demo</a>' in text
    assert '<div class="dev-std-gov-body">' in text
    assert '<h1 class="dev-std-gov-h dev-std-gov-h1">Demo Requirement</h1>' in text


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
    write_file(
        root / "dev-std.toml",
        standard_config(),
    )
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

            [[steps]]
            id = "implement"
            title = "Implement demo"
            status = "active"

            [[steps]]
            id = "design-doc-intent-audit"
            title = "Audit design docs, ADRs, and requirements against implementation"
            status = "pending"
            depends_on = ["implement"]

            [[steps]]
            id = "test-runtime-impact-audit"
            title = "Audit new test runtime impact"
            status = "pending"
            depends_on = ["implement"]

            [[steps]]
            id = "external-review"
            title = "Obtain independent external review"
            status = "pending"
            depends_on = ["implement", "design-doc-intent-audit", "test-runtime-impact-audit"]

            [[exit_criteria]]
            id = "review"
            title = "Review is complete"
            status = "pending"

            [[exit_criteria]]
            id = "design-doc-intent-audit"
            title = "Design docs, ADRs, and requirements match implementation"
            status = "pending"

            [[exit_criteria]]
            id = "test-runtime-impact-audit"
            title = "New tests are listed and runtime impact is reviewed"
            status = "pending"

            [[exit_criteria]]
            id = "external-review"
            title = "Independent external review is complete"
            status = "pending"
            +++

            # Demo Plan
            """
        ).lstrip(),
    )
    write_file(
        root / "docs" / "plans" / "demo-log.md",
        dedent(
            """
            +++
            type = "plan_log"
            id = "demo-log"
            plan_id = "demo-plan"
            step_id = "implement"
            created = "2026-07-02T12:00:00-04:00"
            +++

            Implemented the demo step.
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
