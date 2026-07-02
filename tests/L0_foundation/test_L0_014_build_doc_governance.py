from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from wn_dev_std.checks import CheckResult, run_audit_checks


def test_docs_build_fails_missing_canonical_build_doc(tmp_path: Path) -> None:
    result = scope_result(tmp_path)

    assert not result.passed
    assert "missing canonical build doc" in result.detail


def test_docs_build_passes_html_build_doc(tmp_path: Path) -> None:
    write_file(
        tmp_path / "docs" / "build.html",
        """
        <!doctype html>
        <html><body data-doc="build" data-doc-status="accepted">
          <h1>Build</h1>
          <h2>Tools And Setup</h2><p>Install required tools.</p>
          <h2>Commands And Invocation</h2><p>Run the build command.</p>
          <h2>Outputs And Artifacts</h2><p>Artifacts are written to dist.</p>
          <h2>Validation And Signoff</h2><p>Run tests and signoff.</p>
        </body></html>
        """,
    )

    result = scope_result(tmp_path)

    assert result.passed


def test_docs_build_passes_markdown_build_doc(tmp_path: Path) -> None:
    write_file(
        tmp_path / "docs" / "build.md",
        """
        +++
        type = "build_doc"
        id = "build"
        title = "Build"
        status = "accepted"
        +++

        # Build

        Tools and setup are documented here.
        Run the build command from the package root.
        Outputs and artifacts are written under dist.
        Tests and signoff validate the package.
        """,
    )

    result = scope_result(tmp_path)

    assert result.passed


def test_docs_build_rejects_index_form(tmp_path: Path) -> None:
    write_file(
        tmp_path / "docs" / "build" / "index.html",
        """
        <!doctype html>
        <html><body data-doc="build" data-doc-status="accepted">
          <h1>Build</h1>
          <p>Tools setup, run build command, output artifacts, test signoff.</p>
        </body></html>
        """,
    )

    result = scope_result(tmp_path)

    assert not result.passed
    assert "missing canonical build doc" in result.detail


def test_docs_build_fails_html_without_metadata(tmp_path: Path) -> None:
    write_file(
        tmp_path / "docs" / "build.html",
        """
        <!doctype html>
        <html><body>
          <h1>Build</h1>
          <p>Tools setup, run build command, output artifacts, test signoff.</p>
        </body></html>
        """,
    )

    result = scope_result(tmp_path)

    assert not result.passed
    assert 'missing data-doc="build"' in result.detail
    assert 'data-doc-status must be "accepted"' in result.detail


def test_docs_build_fails_missing_required_topic(tmp_path: Path) -> None:
    write_file(
        tmp_path / "docs" / "build.html",
        """
        <!doctype html>
        <html><body data-doc="build" data-doc-status="accepted">
          <h1>Build</h1>
          <p>Tools setup and run build command.</p>
        </body></html>
        """,
    )

    result = scope_result(tmp_path)

    assert not result.passed
    assert "missing build topic outputs/artifacts" in result.detail
    assert "missing build topic validation/signoff" in result.detail


def scope_result(root: Path) -> CheckResult:
    results = run_audit_checks(root, ("docs.build",))
    assert len(results) == 1
    return results[0]


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(text).lstrip(), encoding="utf-8", newline="\n")
