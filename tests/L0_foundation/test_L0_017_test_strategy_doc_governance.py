from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from wn_dev_std.checks import CheckResult, run_audit_checks


def test_docs_test_strategy_fails_missing_canonical_doc(tmp_path: Path) -> None:
    result = scope_result(tmp_path)

    assert not result.passed
    assert "missing canonical test strategy doc" in result.detail


def test_docs_test_strategy_passes_html_strategy_doc(tmp_path: Path) -> None:
    write_file(
        tmp_path / "docs" / "test-strategy.html",
        """
        <!doctype html>
        <html><body data-doc="test-strategy" data-doc-status="accepted">
          <h1>Test Strategy</h1>
          <h2>Scope And Architecture</h2>
          <p>The package test suite strategy covers the workspace boundary.</p>
          <h2>Rack And Signoff</h2>
          <p>Rack strata include L99_signoff release gates.</p>
          <h2>Lanes, Parity, And Surfaces</h2>
          <p>Python and C++ parity lanes or public surfaces are documented.</p>
          <h2>Fixtures, Assets, And Oracles</h2>
          <p>Fixture data, assets, cases, and oracle tools are cataloged.</p>
          <h2>Coverage, Gaps, And Evidence</h2>
          <p>Coverage evidence identifies missing manifest or orphan gaps.</p>
        </body></html>
        """,
    )

    result = scope_result(tmp_path)

    assert result.passed


def test_docs_test_strategy_rejects_index_form(tmp_path: Path) -> None:
    write_file(
        tmp_path / "docs" / "test-strategy" / "index.html",
        """
        <!doctype html>
        <html><body data-doc="test-strategy" data-doc-status="accepted">
          <p>Rack signoff lanes parity surface fixture asset oracle coverage evidence.</p>
        </body></html>
        """,
    )

    result = scope_result(tmp_path)

    assert not result.passed
    assert "missing canonical test strategy doc" in result.detail


def test_docs_test_strategy_fails_html_without_metadata(tmp_path: Path) -> None:
    write_file(
        tmp_path / "docs" / "test-strategy.html",
        """
        <!doctype html>
        <html><body>
          <p>Strategy suite architecture Rack signoff lanes parity surface
          fixture asset oracle coverage evidence missing manifest.</p>
        </body></html>
        """,
    )

    result = scope_result(tmp_path)

    assert not result.passed
    assert 'missing data-doc="test-strategy"' in result.detail
    assert 'data-doc-status must be "accepted"' in result.detail


def test_docs_test_strategy_fails_missing_required_topic(tmp_path: Path) -> None:
    write_file(
        tmp_path / "docs" / "test-strategy.html",
        """
        <!doctype html>
        <html><body data-doc="test-strategy" data-doc-status="accepted">
          <p>Strategy suite architecture Rack signoff coverage evidence.</p>
        </body></html>
        """,
    )

    result = scope_result(tmp_path)

    assert not result.passed
    assert "missing test strategy topic lanes/parity/surfaces" in result.detail
    assert "missing test strategy topic fixtures/assets/oracles" in result.detail


def scope_result(root: Path) -> CheckResult:
    results = run_audit_checks(root, ("docs.test_strategy",))
    return next(result for result in results if result.scope == "docs.test_strategy")


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(text).lstrip(), encoding="utf-8", newline="\n")
