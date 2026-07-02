from __future__ import annotations

import subprocess
import sys
import tomllib
from pathlib import Path

from wn_dev_std import __version__

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


def test_cli_help_lists_public_commands() -> None:
    result = run_cli("--help")
    assert result.returncode == 0
    for command in ("audit", "check", "log", "plan", "standard", "version"):
        assert command in result.stdout


def test_pyproject_exposes_dev_std_and_legacy_cli_aliases() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        pyproject = tomllib.load(handle)
    scripts = pyproject["project"]["scripts"]
    assert scripts["dev-std"] == "wn_dev_std.cli.main:main"
    assert scripts["wn-dev-std"] == "wn_dev_std.cli.main:main"


def test_cli_command_help_starts_for_public_commands() -> None:
    for command in ("audit", "check", "log", "plan", "standard", "version"):
        result = run_cli(command, "--help")
        assert result.returncode == 0
        assert command in result.stdout


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
        "docs.requirements",
        "docs.traceability",
        "docs.links",
    ):
        result = run_cli("audit", "--scope", scope)
        assert result.returncode == 0
        assert scope in result.stdout


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
