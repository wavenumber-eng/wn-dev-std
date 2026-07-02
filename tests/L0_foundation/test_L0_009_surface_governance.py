from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from wn_dev_std.checks import CheckResult, run_audit_checks


def test_docs_surfaces_audit_passes_valid_manifest(tmp_path: Path) -> None:
    write_surface_repo(tmp_path)

    result = scope_result(tmp_path)

    assert result.passed
    assert "1 governed surface" in result.detail


def test_docs_surfaces_audit_fails_active_surface_without_verification(
    tmp_path: Path,
) -> None:
    write_surface_repo(tmp_path, include_verification=False)

    result = scope_result(tmp_path)

    assert not result.passed
    assert "needs verification_refs or exception" in result.detail


def test_docs_surfaces_audit_fails_missing_local_test_target(tmp_path: Path) -> None:
    write_surface_repo(tmp_path, test_target="tests/test_missing.py::test_core")

    result = scope_result(tmp_path)

    assert not result.passed
    assert "missing local target" in result.detail
    assert "tests/test_missing.py::test_core" in result.detail


def test_docs_surfaces_audit_fails_local_ref_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.py"
    outside.write_text("VALUE = 1\n", encoding="utf-8")
    write_surface_repo(tmp_path, test_target="../outside.py::test_core")

    result = scope_result(tmp_path)

    assert not result.passed
    assert "escapes repository root" in result.detail


def test_docs_surfaces_audit_allows_issue_linked_exception(tmp_path: Path) -> None:
    write_surface_repo(
        tmp_path,
        include_verification=False,
        include_exception=True,
    )

    result = scope_result(tmp_path)

    assert result.passed


def test_docs_surfaces_audit_fails_unknown_domain_when_registry_exists(
    tmp_path: Path,
) -> None:
    write_surface_repo(tmp_path, surface_domain="missing")

    result = scope_result(tmp_path)

    assert not result.passed
    assert "unknown domain 'missing'" in result.detail


def test_docs_surfaces_audit_allows_external_verification_refs(tmp_path: Path) -> None:
    write_surface_repo(tmp_path, verification_kind="external_cpp_test")

    result = scope_result(tmp_path)

    assert result.passed


def test_docs_surfaces_audit_fails_external_ref_without_repo(tmp_path: Path) -> None:
    write_surface_repo(
        tmp_path,
        verification_kind="external_cpp_test",
        verification_repo="",
    )

    result = scope_result(tmp_path)

    assert not result.passed
    assert "external refs require repo" in result.detail


def test_docs_surfaces_audit_passes_parity_relationship(tmp_path: Path) -> None:
    write_parity_repo(tmp_path)

    result = scope_result(tmp_path)

    assert result.passed


def test_docs_surfaces_audit_fails_unknown_parity_surface(tmp_path: Path) -> None:
    write_parity_repo(tmp_path, target_surface_ref="core.cpp.missing")

    result = scope_result(tmp_path)

    assert not result.passed
    assert "unknown target_surface_ref 'core.cpp.missing'" in result.detail


def test_docs_surfaces_audit_fails_untracked_accepted_divergence(
    tmp_path: Path,
) -> None:
    write_parity_repo(
        tmp_path,
        parity_mode="accepted_divergence",
        fixture_coverage="accepted_divergence",
        include_parity_exception_ref=False,
    )

    result = scope_result(tmp_path)

    assert not result.passed
    assert "accepted divergence requires exception_ref or issue_refs" in result.detail


def test_docs_surfaces_audit_allows_exception_tracked_divergence(
    tmp_path: Path,
) -> None:
    write_parity_repo(
        tmp_path,
        parity_mode="accepted_divergence",
        fixture_coverage="accepted_divergence",
        include_parity_exception_ref=True,
    )

    result = scope_result(tmp_path)

    assert result.passed


def test_docs_surfaces_audit_passes_registered_used_fixture(tmp_path: Path) -> None:
    write_surface_repo(tmp_path, include_fixture_catalog=True)

    result = scope_result(tmp_path)

    assert result.passed


def test_docs_surfaces_audit_fails_unregistered_discovered_fixture(
    tmp_path: Path,
) -> None:
    write_surface_repo(tmp_path, include_fixture_catalog=True)
    write_file(tmp_path / "tests" / "fixtures" / "extra.json", "{}\n")

    result = scope_result(tmp_path)

    assert not result.passed
    assert "discovered unregistered fixture 'tests/fixtures/extra.json'" in result.detail


def test_docs_surfaces_audit_fails_unused_active_fixture(tmp_path: Path) -> None:
    write_surface_repo(tmp_path, include_fixture_catalog=True, include_unused_fixture=True)

    result = scope_result(tmp_path)

    assert not result.passed
    assert "unused active fixture 'tests/fixtures/unused.json'" in result.detail


def test_docs_surfaces_audit_fails_fixture_path_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.json"
    outside.write_text("{}\n", encoding="utf-8")
    write_surface_repo(
        tmp_path,
        include_fixture_catalog=True,
        fixture_ref_target="fixture.core",
        fixture_catalog_path="../outside.json",
    )

    result = scope_result(tmp_path)

    assert not result.passed
    assert "fixture path escapes repository root" in result.detail


def test_docs_surfaces_audit_fails_fixture_discovery_root_escape(tmp_path: Path) -> None:
    write_surface_repo(
        tmp_path,
        include_fixture_catalog=True,
        fixture_discovery_root="../outside-fixtures",
    )

    result = scope_result(tmp_path)

    assert not result.passed
    assert "fixture discovery root escapes repository" in result.detail


def test_docs_surfaces_audit_allows_archived_missing_fixture(tmp_path: Path) -> None:
    write_surface_repo(tmp_path, include_fixture_catalog=True, include_archived_fixture=True)

    result = scope_result(tmp_path)

    assert result.passed


def test_docs_surfaces_audit_allows_logical_fixture_case_refs(tmp_path: Path) -> None:
    write_surface_repo(
        tmp_path,
        include_fixture_catalog=True,
        fixture_ref_kind="fixture_case",
        fixture_ref_target="case:synthetic:roundtrip:001",
        fixture_catalog_kind="fixture_case",
        fixture_catalog_id="case:synthetic:roundtrip:001",
        fixture_catalog_path="",
    )

    result = scope_result(tmp_path)

    assert result.passed


def test_docs_surfaces_audit_fails_missing_logical_fixture_case_ref(tmp_path: Path) -> None:
    write_surface_repo(
        tmp_path,
        include_fixture_catalog=True,
        fixture_ref_kind="fixture_case",
        fixture_ref_target="case:synthetic:roundtrip:missing",
        fixture_catalog_kind="fixture_case",
        fixture_catalog_id="case:synthetic:roundtrip:001",
        fixture_catalog_path="",
    )

    result = scope_result(tmp_path)

    assert not result.passed
    assert "unregistered surface fixture 'case:synthetic:roundtrip:missing'" in result.detail


def test_docs_surfaces_audit_allows_mixed_logical_and_physical_fixtures(
    tmp_path: Path,
) -> None:
    write_surface_repo(
        tmp_path,
        include_fixture_catalog=True,
        include_extra_logical_fixture=True,
        fixture_ref_kind="fixture_case",
        fixture_ref_target="case:synthetic:roundtrip:001",
        fixture_catalog_kind="fixture_case",
        fixture_catalog_id="case:synthetic:roundtrip:001",
        fixture_catalog_path="",
    )

    result = scope_result(tmp_path)

    assert result.passed


def scope_result(root: Path) -> CheckResult:
    results = run_audit_checks(root, ("docs.surfaces",))
    assert len(results) == 1
    return results[0]


def write_surface_repo(
    root: Path,
    *,
    include_verification: bool = True,
    include_exception: bool = False,
    include_fixture_catalog: bool = False,
    include_unused_fixture: bool = False,
    include_archived_fixture: bool = False,
    include_extra_logical_fixture: bool = False,
    fixture_ref_kind: str = "fixture_file",
    fixture_ref_target: str = "tests/fixtures/core.json",
    fixture_catalog_kind: str = "fixture_file",
    fixture_catalog_id: str = "fixture.core",
    fixture_catalog_path: str = "tests/fixtures/core.json",
    fixture_discovery_root: str = "tests/fixtures",
    surface_domain: str = "core",
    test_target: str = "tests/test_core.py::test_core",
    verification_kind: str = "local_pytest",
    verification_repo: str = "wavenumber-eng/example",
) -> None:
    write_file(root / "dev-std.toml", 'profile = "python-package"\n')
    write_file(root / "src" / "core" / "api.py", "def list_core():\n    return []\n")
    write_file(root / "tests" / "test_core.py", "def test_core():\n    assert True\n")
    write_file(root / "tests" / "fixtures" / "core.json", "{}\n")
    write_file(root / "docs" / "domains" / "core.html", '<html data-domain="core"></html>\n')
    write_file(
        root / "docs" / "governance" / "domain_registry.toml",
        dedent(
            """
            [[domains]]
            id = "core"
            title = "Core"
            status = "active"
            purpose = "Own core behavior."
            html = "docs/domains/core.html"
            """
        ).lstrip(),
    )
    write_file(
        root / "docs" / "governance" / "governed_surfaces.toml",
        surface_manifest(
            include_verification=include_verification,
            include_exception=include_exception,
            include_fixture_catalog=include_fixture_catalog,
            include_unused_fixture=include_unused_fixture,
            include_archived_fixture=include_archived_fixture,
            include_extra_logical_fixture=include_extra_logical_fixture,
            fixture_ref_kind=fixture_ref_kind,
            fixture_ref_target=fixture_ref_target,
            fixture_catalog_kind=fixture_catalog_kind,
            fixture_catalog_id=fixture_catalog_id,
            fixture_catalog_path=fixture_catalog_path,
            fixture_discovery_root=fixture_discovery_root,
            surface_domain=surface_domain,
            test_target=test_target,
            verification_kind=verification_kind,
            verification_repo=verification_repo,
        ),
    )


def surface_manifest(
    *,
    include_verification: bool,
    include_exception: bool,
    include_fixture_catalog: bool,
    include_unused_fixture: bool,
    include_archived_fixture: bool,
    include_extra_logical_fixture: bool,
    fixture_ref_kind: str,
    fixture_ref_target: str,
    fixture_catalog_kind: str,
    fixture_catalog_id: str,
    fixture_catalog_path: str,
    fixture_discovery_root: str,
    surface_domain: str,
    test_target: str,
    verification_kind: str,
    verification_repo: str,
) -> str:
    verification = verification_block(
        test_target,
        verification_kind,
        verification_repo,
    )
    if not include_verification:
        verification = ""
    fixtures = fixture_catalog_block(
        include_unused_fixture,
        include_archived_fixture,
        include_extra_logical_fixture,
        fixture_catalog_kind,
        fixture_catalog_id,
        fixture_catalog_path,
        fixture_discovery_root,
    )
    if not include_fixture_catalog:
        fixtures = ""
    exception = ""
    if include_exception:
        exception = dedent(
            """

            [[exceptions]]
            id = "core.api.list_core.deferred"
            surface_ref = "core.api.list_core"
            status = "deferred"
            rationale = "Tracked until matching native lane exists."
            issue_refs = ["wavenumber-eng/example#12"]
            """
        )
    extra_fixture_ref = ""
    if include_extra_logical_fixture:
        extra_fixture_ref = dedent(
            """

            [[surfaces.fixture_refs]]
            kind = "fixture_file"
            target = "tests/fixtures/core.json"
            coverage_mode = "regression"
            rationale = "Exercises a path-backed fixture beside logical cases."
            """
        )
    return dedent(
        f"""
        [[surfaces]]
        id = "core.api.list_core"
        domain = "{surface_domain}"
        kind = "public_function"
        status = "active"
        purpose = "List core records."
        implementation_refs = ["src/core/api.py#list_core"]

        [[surfaces.fixture_refs]]
        kind = "{fixture_ref_kind}"
        target = "{fixture_ref_target}"
        coverage_mode = "regression"
        rationale = "Exercises a stable fixture."
        {extra_fixture_ref}
        {verification}
        {exception}
        {fixtures}
        """
    ).lstrip()


def verification_block(target: str, kind: str, repo: str) -> str:
    repo_line = f'repo = "{repo}"' if kind.startswith("external_") and repo else ""
    return dedent(
        f"""

        [[surfaces.verification_refs]]
        kind = "{kind}"
        target = "{target}"
        {repo_line}
        coverage_mode = "regression"
        rationale = "Covers the public surface."
        """
    )


def fixture_catalog_block(
    include_unused_fixture: bool,
    include_archived_fixture: bool,
    include_extra_logical_fixture: bool,
    fixture_catalog_kind: str,
    fixture_catalog_id: str,
    fixture_catalog_path: str,
    fixture_discovery_root: str,
) -> str:
    unused = ""
    if include_unused_fixture:
        unused = dedent(
            """

            [[fixtures]]
            id = "fixture.unused"
            kind = "json"
            path = "tests/fixtures/unused.json"
            status = "active"
            purpose = "Intentionally unused fixture for audit tests."
            """
        )
    archived = ""
    if include_archived_fixture:
        archived = dedent(
            """

            [[fixtures]]
            id = "fixture.archived"
            kind = "json"
            path = "tests/fixtures/archived.json"
            status = "archived"
            purpose = "Historical fixture retained for provenance."
            """
        )
    extra_logical = ""
    if include_extra_logical_fixture:
        extra_logical = dedent(
            """

            [[fixtures]]
            id = "tests/fixtures/core.json"
            kind = "fixture_file"
            path = "tests/fixtures/core.json"
            status = "active"
            purpose = "Path-backed fixture retained beside logical cases."
            """
        )
    path_line = f'path = "{fixture_catalog_path}"' if fixture_catalog_path else ""
    return dedent(
        f"""

        [fixture_governance]
        discovery_roots = ["{fixture_discovery_root}"]
        ignore = ["tests/fixtures/core.json"]

        [[fixtures]]
        id = "{fixture_catalog_id}"
        kind = "{fixture_catalog_kind}"
        {path_line}
        status = "active"
        purpose = "Core API fixture."
        {unused}
        {archived}
        {extra_logical}
        """
    )


def write_parity_repo(
    root: Path,
    *,
    target_surface_ref: str = "core.cpp.list_core",
    parity_mode: str = "semantic_parity",
    fixture_coverage: str = "equal",
    include_parity_exception_ref: bool = False,
) -> None:
    write_file(root / "dev-std.toml", 'profile = "python-package"\n')
    write_file(root / "src" / "core" / "api.py", "def list_core():\n    return []\n")
    write_file(root / "tests" / "test_core.py", "def test_core():\n    assert True\n")
    write_file(root / "tests" / "fixtures" / "core.json", "{}\n")
    write_file(root / "docs" / "domains" / "core.html", '<html data-domain="core"></html>\n')
    write_file(
        root / "docs" / "governance" / "domain_registry.toml",
        dedent(
            """
            [[domains]]
            id = "core"
            title = "Core"
            status = "active"
            purpose = "Own core behavior."
            html = "docs/domains/core.html"
            """
        ).lstrip(),
    )
    write_file(
        root / "docs" / "governance" / "governed_surfaces.toml",
        parity_manifest(
            target_surface_ref=target_surface_ref,
            parity_mode=parity_mode,
            fixture_coverage=fixture_coverage,
            include_parity_exception_ref=include_parity_exception_ref,
        ),
    )


def parity_manifest(
    *,
    target_surface_ref: str,
    parity_mode: str,
    fixture_coverage: str,
    include_parity_exception_ref: bool,
) -> str:
    exception_ref = (
        'exception_ref = "core.cpp.list_core.divergence"' if include_parity_exception_ref else ""
    )
    return dedent(
        f"""
        [[surfaces]]
        id = "core.py.list_core"
        domain = "core"
        kind = "public_function"
        status = "active"
        purpose = "Python list core records API."
        implementation_refs = ["src/core/api.py#list_core"]

        [[surfaces.verification_refs]]
        kind = "local_pytest"
        target = "tests/test_core.py::test_core"
        coverage_mode = "regression"
        rationale = "Covers the Python surface."

        [[surfaces.fixture_refs]]
        kind = "fixture_file"
        target = "tests/fixtures/core.json"
        coverage_mode = "regression"
        rationale = "Exercises a stable fixture."

        [[surfaces]]
        id = "core.cpp.list_core"
        domain = "core"
        kind = "public_function"
        status = "active"
        purpose = "C++ list core records API."
        implementation_refs = ["src/core/api.py#list_core"]

        [[surfaces.verification_refs]]
        kind = "external_cpp_test"
        repo = "wavenumber-eng/example"
        target = "tests/cpp/test_core.cpp::test_core"
        coverage_mode = "regression"
        rationale = "Covers the C++ surface."

        [[exceptions]]
        id = "core.cpp.list_core.divergence"
        surface_ref = "core.cpp.list_core"
        status = "accepted_divergence"
        rationale = "Documented fixture equivalence is intentionally semantic."

        [[parity_relationships]]
        id = "core.list_core.py_cpp"
        source_surface_ref = "core.py.list_core"
        target_surface_ref = "{target_surface_ref}"
        mode = "{parity_mode}"
        fixture_coverage = "{fixture_coverage}"
        status = "active"
        rationale = "Python and C++ list APIs should cover the same behavior."
        {exception_ref}
        """
    ).lstrip()


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
