from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest
from config_fixtures import standard_config

from wn_dev_std.checks import CheckResult, run_audit_checks


def test_docs_domains_audit_passes_minimal_registry(tmp_path: Path) -> None:
    write_domain_repo(tmp_path)

    result = scope_result(tmp_path)

    assert result.passed
    assert "1 domain(s)" in result.detail


def test_docs_domains_audit_fails_unowned_files_under_owned_roots(tmp_path: Path) -> None:
    write_domain_repo(tmp_path)
    write_file(tmp_path / "src" / "unowned.py", "VALUE = 1\n")

    result = scope_result(tmp_path)

    assert not result.passed
    assert "unowned files under owned_roots" in result.detail
    assert "src/unowned.py" in result.detail


def test_docs_domains_audit_allows_ignored_generated_files(tmp_path: Path) -> None:
    write_domain_repo(tmp_path)
    write_file(tmp_path / "docs" / "generated" / "index.html", "<html></html>\n")

    result = scope_result(tmp_path)

    assert result.passed


def test_docs_domains_audit_handles_ignored_symlink_to_external_file(tmp_path: Path) -> None:
    write_domain_repo(tmp_path)
    external = tmp_path.parent / "external-python"
    external.write_text("# external target\n", encoding="utf-8")
    symlink = tmp_path / ".venv" / "bin" / "python3"
    symlink.parent.mkdir(parents=True)
    try:
        symlink.symlink_to(external)
    except OSError as exc:
        pytest.skip(f"symlink creation unavailable: {exc}")

    result = scope_result(tmp_path)

    assert result.passed


def test_docs_domains_audit_allows_known_supporting_domains(tmp_path: Path) -> None:
    write_domain_repo(tmp_path, include_api_domain=True)
    write_file(tmp_path / "src" / "api" / "surface.py", "VALUE = 1\n")

    result = scope_result(tmp_path)

    assert result.passed


def test_docs_domains_audit_fails_missing_domain_html(tmp_path: Path) -> None:
    write_domain_repo(tmp_path, include_domain_html=False)

    result = scope_result(tmp_path)

    assert not result.passed
    assert "missing html target" in result.detail


def test_docs_domains_audit_fails_domain_html_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside-domain.html"
    outside.write_text(
        '<html><body data-domain="core" data-domain-status="active">'
        "docs/governance/domain_registry.toml</body></html>\n",
        encoding="utf-8",
    )
    write_domain_repo(tmp_path, domain_html="../outside-domain.html")

    result = scope_result(tmp_path)

    assert not result.passed
    assert "html target escapes repository root" in result.detail


def test_docs_domains_audit_fails_unknown_adr_domain(tmp_path: Path) -> None:
    write_domain_repo(tmp_path)
    write_file(
        tmp_path / "docs" / "missing" / "adr" / "missing-adr-0001-record.md",
        dedent(
            """
            +++
            type = "adr"
            id = "missing-adr-0001"
            domain = "missing"
            status = "accepted"
            title = "Record"
            created = "2026-07-02"
            +++

            # Record
            """
        ).lstrip(),
    )

    result = scope_result(tmp_path)

    assert not result.passed
    assert "is not in domain registry" in result.detail


def scope_result(root: Path) -> CheckResult:
    results = run_audit_checks(root, ("docs.domains",))
    return next(result for result in results if result.scope == "docs.domains")


def write_domain_repo(
    root: Path,
    *,
    include_domain_html: bool = True,
    include_api_domain: bool = False,
    domain_html: str = "docs/domains/core.html",
) -> None:
    write_file(
        root / "dev-std.toml",
        standard_config(),
    )
    write_file(root / "src" / "core" / "core.py", "VALUE = 1\n")
    write_file(root / "tests" / "test_core.py", "def test_core(): pass\n")
    if include_domain_html:
        write_file(
            root / "docs" / "domains" / "core.html",
            (
                '<html><body data-domain="core" data-domain-status="active">'
                "docs/governance/domain_registry.toml</body></html>\n"
            ),
        )
        if include_api_domain:
            write_file(
                root / "docs" / "domains" / "api.html",
                (
                    '<html><body data-domain="api" data-domain-status="active">'
                    "docs/governance/domain_registry.toml</body></html>\n"
                ),
            )
    write_file(
        root / "docs" / "core" / "adr" / "core-adr-0001-record.md",
        dedent(
            """
            +++
            type = "adr"
            id = "core-adr-0001"
            domain = "core"
            status = "accepted"
            title = "Record"
            created = "2026-07-02"
            +++

            # Record
            """
        ).lstrip(),
    )
    api_domain = ""
    api_group = ""
    if include_api_domain:
        api_domain = dedent(
            """

            [[domains]]
            id = "api"
            title = "API"
            status = "active"
            purpose = "Own public API surfaces."
            html = "docs/domains/api.html"
            """
        )
        api_group = dedent(
            """

            [[file_groups]]
            primary_domain = "api"
            supporting_domains = ["core"]
            paths = ["src/api/**"]
            """
        )
    write_file(
        root / "docs" / "governance" / "domain_registry.toml",
        dedent(
            f"""
            [domain_governance]
            owned_roots = ["src", "tests", "docs"]
            ignore = ["docs/generated/**"]

            [[domains]]
            id = "core"
            title = "Core"
            status = "active"
            purpose = "Own core source, tests, and governance."
            html = "{domain_html}"

            [[file_groups]]
            primary_domain = "core"
            paths = [
              "src/core/**",
              "tests/**",
              "docs/core/**",
              "docs/domains/**",
              "docs/governance/**",
            ]
            {api_domain}
            {api_group}
            """
        ).lstrip(),
    )


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
