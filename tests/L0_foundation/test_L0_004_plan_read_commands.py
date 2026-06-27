from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

from wn_dev_std.root_discovery import discover_project_root


def test_root_discovery_prefers_standalone_config(tmp_path: Path) -> None:
    write_file(tmp_path / "wn-dev-std.toml", 'profile = "python-package"\n')
    nested = tmp_path / "docs" / "plans"
    nested.mkdir(parents=True)

    discovered = discover_project_root(nested)

    assert discovered.root == tmp_path
    assert discovered.marker == "wn-dev-std.toml"
    assert discovered.found_standard_config


def test_root_discovery_uses_pyproject_tool_config(tmp_path: Path) -> None:
    write_file(
        tmp_path / "pyproject.toml",
        dedent(
            """
            [tool.wn_dev_std]
            profile = "python-package"
            """
        ).lstrip(),
    )
    nested = tmp_path / "src" / "package"
    nested.mkdir(parents=True)

    discovered = discover_project_root(nested)

    assert discovered.root == tmp_path
    assert discovered.marker == "pyproject.toml"
    assert discovered.found_standard_config


def test_root_discovery_uses_git_boundary_as_fallback(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    nested = tmp_path / "src" / "package"
    nested.mkdir(parents=True)

    discovered = discover_project_root(nested)

    assert discovered.root == tmp_path
    assert discovered.marker == ".git"
    assert not discovered.found_standard_config


def test_plan_list_discovers_root_from_nested_directory(tmp_path: Path) -> None:
    write_compliant_plan_repo(tmp_path)
    nested = tmp_path / "docs" / "plans" / "pcb-a0"

    result = run_cli(nested, "plan", "list")

    assert result.returncode == 0
    assert "pcb-a0" in result.stdout
    assert "docs/plans/pcb-a0/plan.md" in result.stdout


def test_plan_list_json_is_machine_readable(tmp_path: Path) -> None:
    write_compliant_plan_repo(tmp_path)

    result = run_cli(tmp_path, "plan", "list", "--format", "json")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["marker"] == "wn-dev-std.toml"
    assert payload["plans"][0]["id"] == "pcb-a0"
    assert payload["plans"][0]["steps"][0]["id"] == "audit"


def test_plan_show_outputs_body(tmp_path: Path) -> None:
    write_compliant_plan_repo(tmp_path)

    result = run_cli(tmp_path, "plan", "show", "pcb-a0")

    assert result.returncode == 0
    assert "Plan: pcb-a0" in result.stdout
    assert "audit [done] Audit existing plans" in result.stdout
    assert "Body for PCB A0." in result.stdout


def test_log_list_outputs_logs_for_plan(tmp_path: Path) -> None:
    write_compliant_plan_repo(tmp_path)

    result = run_cli(tmp_path, "log", "list", "pcb-a0")

    assert result.returncode == 0
    assert "pcb-a0-log" in result.stdout
    assert "docs/plans/pcb-a0/logs/2026-06-27.md" in result.stdout


def test_log_show_outputs_body(tmp_path: Path) -> None:
    write_compliant_plan_repo(tmp_path)

    result = run_cli(tmp_path, "log", "show", "pcb-a0-log")

    assert result.returncode == 0
    assert "Log: pcb-a0-log" in result.stdout
    assert "Plan: pcb-a0" in result.stdout
    assert "docs/plans/pcb-a0/logs/2026-06-27.md" in result.stdout
    assert "Work log body." in result.stdout


def test_log_show_json_is_machine_readable(tmp_path: Path) -> None:
    write_compliant_plan_repo(tmp_path)

    result = run_cli(tmp_path, "log", "show", "pcb-a0-log", "--format", "json")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["id"] == "pcb-a0-log"
    assert payload["plan_id"] == "pcb-a0"
    assert payload["body"] == "Work log body."


def test_plan_read_commands_fail_on_noncompliant_catalog(tmp_path: Path) -> None:
    write_file(tmp_path / "wn-dev-std.toml", 'profile = "python-package"\n')
    write_file(tmp_path / "docs" / "plans" / "pcb-a0-plan.md", "# Missing metadata\n")

    result = run_cli(tmp_path, "plan", "list")

    assert result.returncode == 1
    assert "plan catalog is not compliant" in result.stdout
    assert "missing TOML front matter" in result.stdout


def run_cli(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "wn_dev_std", *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def write_compliant_plan_repo(root: Path) -> None:
    write_file(
        root / "wn-dev-std.toml",
        dedent(
            """
            profile = "python-package"

            [documentation.plans]
            roots = ["docs/plans"]
            """
        ).lstrip(),
    )
    write_file(
        root / "docs" / "plans" / "pcb-a0" / "plan.md",
        dedent(
            """
            +++
            type = "plan"
            id = "pcb-a0"
            status = "active"
            created = "2026-06-27"

            [[steps]]
            id = "audit"
            title = "Audit existing plans"
            status = "done"

            [[steps]]
            id = "release"
            title = "Release package"
            status = "pending"
            depends_on = ["audit"]
            +++

            # PCB A0

            Body for PCB A0.
            """
        ).lstrip(),
    )
    write_file(
        root / "docs" / "plans" / "pcb-a0" / "logs" / "2026-06-27.md",
        dedent(
            """
            +++
            type = "plan_log"
            id = "pcb-a0-log"
            plan_id = "pcb-a0"
            created = "2026-06-27T12:00:00-04:00"
            +++

            Work log body.
            """
        ).lstrip(),
    )


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
