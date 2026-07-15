from __future__ import annotations

import http.client
import subprocess
import sys
import tomllib
import urllib.request
from pathlib import Path

from pytest import MonkeyPatch

from wn_dev_std import __version__
from wn_dev_std.cli.commands.audit import upstream_check_result
from wn_dev_std.standards import STANDARD_VERSION
from wn_dev_std.version_check import UpstreamVersionCheck, check_pypi_version

ROOT = Path(__file__).resolve().parents[2]


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "wn_dev_std", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_cli_global_version_reports_tool_and_dependency_versions() -> None:
    result = run_cli("--version")
    assert result.returncode == 0
    assert f"wn-dev-std {__version__}" in result.stdout
    assert "python " in result.stdout
    assert "wn-rack " in result.stdout


def test_cli_version_command_reports_same_version() -> None:
    result = run_cli("version")
    assert result.returncode == 0
    assert f"wn-dev-std {__version__}" in result.stdout


def test_cli_stdout_is_padded_before_and_after_output() -> None:
    for args in (
        ("version",),
        ("standard", "--format", "json"),
        ("--help",),
    ):
        result = run_cli(*args)

        assert result.returncode == 0
        assert result.stdout.startswith("\n")
        assert result.stdout.endswith("\n\n")


def test_audit_upstream_result_warns_only_for_outdated_or_unavailable() -> None:
    current = upstream_check_result(UpstreamVersionCheck(STANDARD_VERSION, STANDARD_VERSION, None))
    outdated = upstream_check_result(UpstreamVersionCheck(STANDARD_VERSION, "9999.1.1", None))
    unavailable = upstream_check_result(UpstreamVersionCheck(STANDARD_VERSION, None, "timeout"))

    assert not current.warning
    assert outdated.warning
    assert unavailable.warning


def test_upstream_version_http_protocol_failure_is_warning_only(
    monkeypatch: MonkeyPatch,
) -> None:
    def raise_bad_status_line(*_args: object, **_kwargs: object) -> object:
        raise http.client.BadStatusLine("bad proxy response")

    monkeypatch.setattr(urllib.request, "urlopen", raise_bad_status_line)

    result = check_pypi_version(__version__)

    assert result.warning is not None
    assert "unable to check PyPI" in result.detail


def test_cli_help_lists_public_commands() -> None:
    result = run_cli("--help")
    assert result.returncode == 0
    for command in (
        "adr",
        "audit",
        "check",
        "governance",
        "log",
        "plan",
        "requirement",
        "standard",
        "version",
    ):
        assert command in result.stdout


def test_pyproject_exposes_dev_std_and_legacy_cli_aliases() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)
    scripts = pyproject["project"]["scripts"]
    assert scripts["dev-std"] == "wn_dev_std.cli.main:main"
    assert scripts["wn-dev-std"] == "wn_dev_std.cli.main:main"


def test_cli_command_help_starts_for_public_commands() -> None:
    for command in (
        "adr",
        "audit",
        "check",
        "governance",
        "log",
        "plan",
        "requirement",
        "standard",
        "version",
    ):
        result = run_cli(command, "--help")
        assert result.returncode == 0
        assert command in result.stdout


def test_governance_subcommand_help_lists_html() -> None:
    result = run_cli("governance", "--help")

    assert result.returncode == 0
    assert "html" in result.stdout


def test_governance_read_subcommand_help_lists_show() -> None:
    for command in ("adr", "requirement"):
        result = run_cli(command, "--help")
        assert result.returncode == 0
        for subcommand in ("list", "show"):
            assert subcommand in result.stdout


def test_log_subcommand_help_lists_show() -> None:
    result = run_cli("log", "--help")

    assert result.returncode == 0
    for subcommand in ("create", "list", "show"):
        assert subcommand in result.stdout


def test_audit_docs_plans_scope_runs() -> None:
    result = run_cli("audit", "--scope", "docs.plans")
    assert result.returncode == 0
    assert "docs.plans" in result.stdout


def test_audit_docs_governance_scopes_run() -> None:
    for scope in (
        "docs.adrs",
        "docs.artifacts",
        "docs.build",
        "docs.domains",
        "docs.release",
        "docs.requirements",
        "docs.surfaces",
        "docs.test_strategy",
        "docs.traceability",
        "docs.vendors",
        "docs.links",
        "tests",
    ):
        result = run_cli("audit", "--scope", scope)
        assert result.returncode == 0
        assert scope in result.stdout


def test_audit_default_all_includes_governance_scopes() -> None:
    result = run_cli("audit", "--format", "json")

    assert result.returncode == 0
    for scope in (
        "docs.adrs",
        "docs.artifacts",
        "docs.build",
        "docs.domains",
        "docs.release",
        "docs.requirements",
        "docs.surfaces",
        "docs.test_strategy",
        "docs.traceability",
        "docs.vendors",
        "docs.links",
        "tests",
    ):
        assert f'"scope": "{scope}"' in result.stdout


def test_check_remains_audit_compatibility_alias() -> None:
    audit = run_cli("audit", "--scope", "docs.plans", "--format", "json")
    check = run_cli("check", "--scope", "docs.plans", "--format", "json")
    assert audit.returncode == check.returncode == 0
    assert audit.stdout == check.stdout


def test_standard_json_command_is_machine_readable() -> None:
    result = run_cli("standard", "--format", "json")
    assert result.returncode == 0
    assert '"name": "python-package"' in result.stdout


def test_standard_profile_can_render_mixed_mode_json() -> None:
    result = run_cli("standard", "--profile", "python-native-wasm", "--format", "json")
    assert result.returncode == 0
    assert '"name": "python-native-wasm"' in result.stdout
    assert "dist/native/<platform>/" in result.stdout


def test_standard_profile_can_render_cpp_json() -> None:
    result = run_cli("standard", "--profile", "cpp-library", "--format", "json")
    assert result.returncode == 0
    assert '"name": "cpp-library"' in result.stdout
    assert '"value": "ninja"' in result.stdout


def test_standard_profile_can_render_csharp_json() -> None:
    result = run_cli("standard", "--profile", "csharp-app", "--format", "json")
    assert result.returncode == 0
    assert '"name": "csharp-app"' in result.stdout
    assert "CA1502/CA1505/CA1506" in result.stdout


def test_standard_profile_can_render_javascript_web_json() -> None:
    result = run_cli("standard", "--profile", "javascript-web-app", "--format", "json")
    assert result.returncode == 0
    assert '"name": "javascript-web-app"' in result.stdout
    assert "no-build browser runtime first" in result.stdout


def test_standard_profile_can_render_python_js_json() -> None:
    result = run_cli("standard", "--profile", "python-js-app", "--format", "json")
    assert result.returncode == 0
    assert '"name": "python-js-app"' in result.stdout
    assert "javascript-web-app" in result.stdout


def test_standard_profile_can_render_zephyr_json() -> None:
    result = run_cli("standard", "--profile", "zephyr-firmware", "--format", "json")
    assert result.returncode == 0
    assert '"name": "zephyr-firmware"' in result.stdout
    assert "cyclomatic_complexity <= 10" in result.stdout
