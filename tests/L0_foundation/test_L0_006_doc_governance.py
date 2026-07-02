from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from wn_dev_std.checks import CheckResult, run_audit_checks


def test_docs_adr_audit_passes_canonical_domain_adr(tmp_path: Path) -> None:
    write_file(
        tmp_path / "docs" / "core" / "adr" / "core-adr-0001-record-decisions.md",
        dedent(
            """
            +++
            type = "adr"
            id = "core-adr-0001"
            domain = "core"
            status = "accepted"
            title = "Record Durable Decisions"
            created = "2026-07-02"
            design_refs = ["docs/core/design/index.html"]
            +++

            # Record Durable Decisions

            Accepted ADRs describe standing decisions.
            """
        ).lstrip(),
    )
    write_file(tmp_path / "docs" / "core" / "design" / "index.html", "<html></html>\n")

    result = scope_result(tmp_path, "docs.adrs")

    assert result.passed
    assert "1 ADR document" in result.detail


def test_docs_adr_audit_fails_stale_accepted_adr_language(tmp_path: Path) -> None:
    write_file(
        tmp_path / "docs" / "viz" / "adr" / "viz-adr-0001-view-state.md",
        dedent(
            """
            +++
            type = "adr"
            id = "viz-adr-0001"
            domain = "viz"
            status = "accepted"
            title = "View State"
            created = "2026-07-02"
            +++

            # View State

            Current visualizer metadata must be audited before v1.1 exit.
            """
        ).lstrip(),
    )

    result = scope_result(tmp_path, "docs.adrs")

    assert not result.passed
    assert "stale active-work language" in result.detail


def test_docs_adr_audit_fails_wrong_domain_prefix_and_filename(tmp_path: Path) -> None:
    write_file(
        tmp_path / "docs" / "pcb" / "adr" / "wrong-name.md",
        dedent(
            """
            +++
            type = "adr"
            id = "core-adr-0001"
            domain = "pcb"
            status = "accepted"
            title = "Layer Keys"
            created = "2026-07-02"
            +++
            """
        ).lstrip(),
    )

    result = scope_result(tmp_path, "docs.adrs")

    assert not result.passed
    assert "id must start with 'pcb-adr-'" in result.detail
    assert "filename must start with id" in result.detail


def test_docs_requirement_audit_passes_verified_requirement(tmp_path: Path) -> None:
    write_file(
        tmp_path / "docs" / "transforms" / "requirements" / "transforms-req-0001-static-mapping.md",
        dedent(
            """
            +++
            type = "requirement"
            id = "transforms-req-0001"
            domain = "transforms"
            status = "active"
            title = "Static Mapping Documentation"
            created = "2026-07-02"
            adr_refs = ["transforms-adr-0001"]

            [[verification_refs]]
            kind = "local_pytest"
            target = "tests/test_transform_docs.py::test_docs_exist"
            +++

            # Static Mapping Documentation
            """
        ).lstrip(),
    )
    write_file(tmp_path / "tests" / "test_transform_docs.py", "def test_docs_exist(): pass\n")

    result = scope_result(tmp_path, "docs.requirements")

    assert result.passed


def test_docs_requirement_audit_fails_active_requirement_without_verification(
    tmp_path: Path,
) -> None:
    write_file(
        tmp_path / "docs" / "alx" / "requirements" / "alx-req-0001-part-key.md",
        dedent(
            """
            +++
            type = "requirement"
            id = "alx-req-0001"
            domain = "alx"
            status = "active"
            title = "Part Key"
            created = "2026-07-02"
            +++
            """
        ).lstrip(),
    )

    result = scope_result(tmp_path, "docs.requirements")

    assert not result.passed
    assert "needs verification_refs" in result.detail


def test_docs_requirement_audit_fails_bad_local_verification_target(
    tmp_path: Path,
) -> None:
    write_file(
        tmp_path / "docs" / "core" / "requirements" / "core-req-0001-demo.md",
        dedent(
            """
            +++
            type = "requirement"
            id = "core-req-0001"
            domain = "core"
            status = "active"
            title = "Demo"
            created = "2026-07-02"

            [[verification_refs]]
            kind = "local_pytest"
            target = "tests/test_missing.py::test_demo"
            +++
            """
        ).lstrip(),
    )

    result = scope_result(tmp_path, "docs.requirements")

    assert not result.passed
    assert "missing local target" in result.detail


def test_docs_traceability_audit_fails_local_ref_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.py"
    outside.write_text("VALUE = 1\n", encoding="utf-8")
    write_file(
        tmp_path / "docs" / "core" / "requirements" / "core-req-0001-demo.md",
        dedent(
            """
            +++
            type = "requirement"
            id = "core-req-0001"
            domain = "core"
            status = "draft"
            title = "Demo"
            created = "2026-07-02"

            [[implementation_refs]]
            kind = "local_file"
            target = "../outside.py"
            +++
            """
        ).lstrip(),
    )

    result = scope_result(tmp_path, "docs.traceability")

    assert not result.passed
    assert "escapes repository root" in result.detail


def test_docs_governance_audits_ignore_readme_index_pages(tmp_path: Path) -> None:
    write_file(tmp_path / "docs" / "core" / "adr" / "README.md", "# ADR Index\n")
    write_file(
        tmp_path / "docs" / "core" / "requirements" / "README.md",
        "# Requirements Index\n",
    )

    adr_result = scope_result(tmp_path, "docs.adrs")
    requirement_result = scope_result(tmp_path, "docs.requirements")

    assert adr_result.passed
    assert requirement_result.passed


def test_docs_traceability_audit_validates_external_refs(tmp_path: Path) -> None:
    write_file(
        tmp_path / "docs" / "altium" / "requirements" / "altium-req-0001-keepout-mask.md",
        dedent(
            """
            +++
            type = "requirement"
            id = "altium-req-0001"
            domain = "altium"
            status = "implemented"
            title = "Keepout Restriction Mask"
            created = "2026-07-02"
            issue_refs = ["wavenumber-eng/toolz#16"]

            [[verification_refs]]
            kind = "external_cpp_test"
            repo = "wavenumber-eng/altium_monkey"
            target = "tests/cpp/test_keepout.cpp::KeepoutRestrictionMaskMapping"

            [[implementation_refs]]
            kind = "external_source"
            repo = "wavenumber-eng/altium_monkey"
            target = "src/cpp/altium_monkey/pcbdoc.hpp:KeepoutRestrictionMask"
            +++
            """
        ).lstrip(),
    )

    result = scope_result(tmp_path, "docs.traceability")

    assert result.passed


def test_docs_traceability_audit_fails_incomplete_external_ref(tmp_path: Path) -> None:
    write_file(
        tmp_path / "docs" / "altium" / "requirements" / "altium-req-0001-keepout-mask.md",
        dedent(
            """
            +++
            type = "requirement"
            id = "altium-req-0001"
            domain = "altium"
            status = "implemented"
            title = "Keepout Restriction Mask"
            created = "2026-07-02"

            [[verification_refs]]
            kind = "external_cpp_test"
            target = "tests/cpp/test_keepout.cpp::KeepoutRestrictionMaskMapping"
            +++
            """
        ).lstrip(),
    )

    result = scope_result(tmp_path, "docs.traceability")

    assert not result.passed
    assert "external refs require repo" in result.detail


def test_docs_links_audit_fails_missing_local_markdown_link(tmp_path: Path) -> None:
    write_file(
        tmp_path / "docs" / "design" / "index.md",
        "[Missing](missing.html)\n",
    )

    result = scope_result(tmp_path, "docs.links")

    assert not result.passed
    assert "missing local link target" in result.detail


def test_docs_links_audit_passes_existing_local_html_link(tmp_path: Path) -> None:
    write_file(
        tmp_path / "docs" / "design" / "index.html",
        '<a href="detail.html">Detail</a>\n',
    )
    write_file(tmp_path / "docs" / "design" / "detail.html", "<html></html>\n")

    result = scope_result(tmp_path, "docs.links")

    assert result.passed


def test_docs_links_audit_fails_html_link_to_raw_governance_markdown(tmp_path: Path) -> None:
    write_file(
        tmp_path / "docs" / "core" / "design" / "index.html",
        '<a href="../adr/core-adr-0001-decision.md">ADR</a>\n',
    )
    write_file(
        tmp_path / "docs" / "core" / "adr" / "core-adr-0001-decision.md",
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
            """
        ).lstrip(),
    )

    result = scope_result(tmp_path, "docs.links")

    assert not result.passed
    assert "must link generated governance pages" in result.detail


def scope_result(root: Path, scope: str) -> CheckResult:
    results = run_audit_checks(root, (scope,))
    assert len(results) == 1
    return results[0]


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
