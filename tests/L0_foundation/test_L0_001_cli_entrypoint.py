from __future__ import annotations

import subprocess
import sys
from pathlib import Path

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
    assert "wn-dev-std 2026.6.7" in result.stdout
    assert "python " in result.stdout
    assert "wn-rack " in result.stdout


def test_cli_version_command_reports_same_version() -> None:
    result = run_cli("version")
    assert result.returncode == 0
    assert "wn-dev-std 2026.6.7" in result.stdout


def test_cli_help_lists_public_commands() -> None:
    result = run_cli("--help")
    assert result.returncode == 0
    for command in ("check", "standard", "version"):
        assert command in result.stdout


def test_cli_command_help_starts_for_public_commands() -> None:
    for command in ("check", "standard", "version"):
        result = run_cli(command, "--help")
        assert result.returncode == 0
        assert command in result.stdout


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
