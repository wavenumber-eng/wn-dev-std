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


def scope_result(root: Path) -> CheckResult:
    results = run_audit_checks(root, ("docs.surfaces",))
    assert len(results) == 1
    return results[0]


def write_surface_repo(
    root: Path,
    *,
    include_verification: bool = True,
    include_exception: bool = False,
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
        kind = "fixture_file"
        target = "tests/fixtures/core.json"
        coverage_mode = "regression"
        rationale = "Exercises a stable fixture."
        {verification}
        {exception}
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


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
