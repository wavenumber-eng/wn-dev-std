from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

from pytest import MonkeyPatch

from wn_dev_std import governance_checks
from wn_dev_std.audit_config import AUDIT_SCOPES, scope_is_selected
from wn_dev_std.checks import run_audit_checks
from wn_dev_std.checks_types import CheckResult
from wn_dev_std.doc_governance import DocGovernanceReport
from wn_dev_std.standards import STANDARD_VERSION


def test_config_without_standard_version_fails_even_for_scoped_audit(tmp_path: Path) -> None:
    write_file(tmp_path / "dev-std.toml", 'profile = "python-package"\n')

    results = run_audit_checks(tmp_path, ("docs.plans",))

    config = next(result for result in results if result.name == "standard config")
    assert not config.passed
    assert "missing standard_version" in config.detail
    assert any(result.name == "docs.plans" for result in results)


def test_config_standard_version_must_match_installed_standard(tmp_path: Path) -> None:
    write_file(
        tmp_path / "dev-std.toml",
        'standard_version = "2026.7.1"\nprofile = "python-package"\n',
    )

    results = run_audit_checks(tmp_path, ("docs.plans",))

    config = next(result for result in results if result.name == "standard config")
    assert not config.passed
    assert "2026.7.1" in config.detail
    assert STANDARD_VERSION in config.detail


def test_enabled_scopes_are_default_when_cli_scope_is_omitted(tmp_path: Path) -> None:
    write_file(
        tmp_path / "dev-std.toml",
        dedent(
            """
            standard_version = "{standard_version}"
            profile = "python-package"
            enabled_scopes = ["docs.plans"]
            """
        )
        .format(standard_version=STANDARD_VERSION)
        .lstrip(),
    )

    results = run_audit_checks(tmp_path)

    assert [result.name for result in results] == ["standard config", "docs.plans"]
    assert all(result.passed for result in results)


def test_explicit_scope_overrides_configured_enabled_scopes(tmp_path: Path) -> None:
    write_file(
        tmp_path / "dev-std.toml",
        dedent(
            """
            standard_version = "{standard_version}"
            profile = "python-package"
            enabled_scopes = ["docs.plans"]
            """
        )
        .format(standard_version=STANDARD_VERSION)
        .lstrip(),
    )

    results = run_audit_checks(tmp_path, ("docs.build",))

    assert [result.name for result in results] == ["standard config", "docs.build"]
    assert not results[1].passed


def test_invalid_enabled_scope_fails_loudly(tmp_path: Path) -> None:
    write_file(
        tmp_path / "dev-std.toml",
        dedent(
            """
            standard_version = "{standard_version}"
            profile = "python-package"
            enabled_scopes = ["docs.nope"]
            """
        )
        .format(standard_version=STANDARD_VERSION)
        .lstrip(),
    )

    config = next(
        result for result in run_audit_checks(tmp_path) if result.name == "standard config"
    )

    assert not config.passed
    assert "docs.nope" in config.detail
    assert "valid scopes" in config.detail


def test_workspace_audit_aggregates_registered_members(tmp_path: Path) -> None:
    write_workspace_config(tmp_path, ["app", "tool"])
    write_member_config(tmp_path / "app")
    write_member_config(tmp_path / "tool")

    results = run_audit_checks(tmp_path)

    assert all(result.passed for result in results), [result.to_dict() for result in results]
    member_checks = [result for result in results if result.member is not None]
    assert {result.member for result in member_checks} == {"app", "tool"}
    assert all(result.name in {"standard config", "docs.plans"} for result in member_checks)


def test_workspace_member_without_config_fails(tmp_path: Path) -> None:
    write_workspace_config(tmp_path, ["app"])
    (tmp_path / "app").mkdir()

    results = run_audit_checks(tmp_path)

    missing = next(result for result in results if result.name == "workspace member")
    assert not missing.passed
    assert missing.member == "app"
    assert "no dev-std config marker" in missing.detail


def test_workspace_rejects_member_that_escapes_root(tmp_path: Path) -> None:
    write_workspace_config(tmp_path, ["../outside"])

    results = run_audit_checks(tmp_path)

    invalid = next(result for result in results if result.name == "workspace member")
    assert not invalid.passed
    assert "must not contain '..'" in invalid.detail


def test_workspace_rejects_duplicate_members(tmp_path: Path) -> None:
    write_workspace_config(tmp_path, ["app", "app"])
    write_member_config(tmp_path / "app")

    results = run_audit_checks(tmp_path)

    duplicate = next(
        result
        for result in results
        if result.name == "workspace member" and "duplicate" in result.detail
    )
    assert not duplicate.passed


def test_workspace_rejects_duplicate_member_path_aliases(tmp_path: Path) -> None:
    write_workspace_config(tmp_path, ["app", "./app"])
    write_member_config(tmp_path / "app")

    results = run_audit_checks(tmp_path)

    duplicate = next(
        result
        for result in results
        if result.name == "workspace member" and "duplicates" in result.detail
    )
    assert not duplicate.passed
    assert duplicate.member == "./app"


def test_workspace_member_must_not_be_workspace(tmp_path: Path) -> None:
    write_workspace_config(tmp_path, ["nested"])
    write_workspace_config(tmp_path / "nested", [])

    results = run_audit_checks(tmp_path)

    nested = next(result for result in results if result.name == "workspace member")
    assert not nested.passed
    assert "must not be kind='workspace'" in nested.detail


def test_workspace_json_output_includes_member(tmp_path: Path) -> None:
    write_workspace_config(tmp_path, ["app"])
    write_member_config(tmp_path / "app")

    result = run_cli(tmp_path, "audit", ".", "--format", "json")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    checks = payload["checks"]
    assert any(check.get("member") == "app" for check in checks)


def test_scoped_audit_skips_unselected_governance_checks(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    write_member_config(tmp_path)

    def fail_if_called(_root: Path) -> DocGovernanceReport:
        raise AssertionError("unselected governance check ran")

    monkeypatch.setattr(
        governance_checks,
        "GOVERNANCE_CHECKS",
        (governance_checks.GovernanceCheck("docs.links", "docs.links", fail_if_called),),
    )

    results = run_audit_checks(tmp_path, ("docs.plans",))

    assert [result.name for result in results] == ["standard config", "docs.plans"]


def test_each_explicit_scope_matches_filtered_full_audit() -> None:
    full_results = run_audit_checks(Path("."), ("all",))
    always_on = tuple(result for result in full_results if result.name == "standard config")
    auditable_results = tuple(result for result in full_results if result.name != "standard config")

    for scope in AUDIT_SCOPES:
        scoped_results = run_audit_checks(Path("."), (scope,))
        expected_results = (
            full_results
            if scope == "all"
            else (*always_on, *_filter_results(auditable_results, scope))
        )

        assert _result_dicts(scoped_results) == _result_dicts(expected_results), scope


def write_workspace_config(root: Path, members: list[str]) -> None:
    quoted_members = ", ".join(repr(member).replace("'", '"') for member in members)
    write_file(
        root / "dev-std.toml",
        dedent(
            f"""
            standard_version = "{STANDARD_VERSION}"
            kind = "workspace"

            [workspace]
            members = [{quoted_members}]
            """
        ).lstrip(),
    )


def write_member_config(root: Path) -> None:
    write_file(
        root / "dev-std.toml",
        dedent(
            """
            standard_version = "{standard_version}"
            profile = "python-package"
            enabled_scopes = ["docs.plans"]
            """
        )
        .format(standard_version=STANDARD_VERSION)
        .lstrip(),
    )


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def run_cli(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "wn_dev_std", *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def _filter_results(results: tuple[CheckResult, ...], scope: str) -> tuple[CheckResult, ...]:
    return tuple(result for result in results if scope_is_selected(result.scope, (scope,)))


def _result_dicts(results: tuple[CheckResult, ...]) -> list[dict[str, object]]:
    return [result.to_dict() for result in results]
