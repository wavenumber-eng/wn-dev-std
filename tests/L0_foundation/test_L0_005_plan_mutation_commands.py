from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from textwrap import dedent


def test_plan_create_writes_compliant_plan(tmp_path: Path) -> None:
    write_plan_config(tmp_path)

    result = run_cli(
        tmp_path,
        "plan",
        "create",
        "pcb-a0",
        "--title",
        "PCB A0",
        "--created",
        "2026-06-27",
    )

    assert result.returncode == 0
    plan_path = tmp_path / "docs" / "plans" / "pcb-a0" / "plan.md"
    assert plan_path.exists()
    assert 'id = "pcb-a0"' in plan_path.read_text(encoding="utf-8")
    audit = run_cli(tmp_path, "audit", "--scope", "docs.plans")
    assert audit.returncode == 0
    assert "1 plan(s)" in audit.stdout


def test_plan_status_updates_front_matter(tmp_path: Path) -> None:
    write_plan_config(tmp_path)
    create_plan(tmp_path)

    result = run_cli(tmp_path, "plan", "status", "pcb-a0", "blocked")

    assert result.returncode == 0
    shown = run_cli(tmp_path, "plan", "show", "pcb-a0")
    assert shown.returncode == 0
    assert "Status: blocked" in shown.stdout


def test_plan_step_add_and_status_update(tmp_path: Path) -> None:
    write_plan_config(tmp_path)
    create_plan(tmp_path)

    first = run_cli(
        tmp_path,
        "plan",
        "step",
        "add",
        "pcb-a0",
        "audit",
        "--title",
        "Audit old plans",
        "--status",
        "active",
    )
    second = run_cli(
        tmp_path,
        "plan",
        "step",
        "add",
        "pcb-a0",
        "release",
        "--title",
        "Release dev standard",
        "--depends-on",
        "audit",
    )
    status = run_cli(tmp_path, "plan", "step", "status", "pcb-a0", "audit", "done")

    assert first.returncode == second.returncode == status.returncode == 0
    shown = run_cli(tmp_path, "plan", "show", "pcb-a0")
    assert shown.returncode == 0
    assert "audit [done] Audit old plans" in shown.stdout
    assert "release [pending] Release dev standard depends_on=audit" in shown.stdout
    audit = run_cli(tmp_path, "audit", "--scope", "docs.plans")
    assert audit.returncode == 0


def test_log_create_writes_attached_log(tmp_path: Path) -> None:
    write_plan_config(tmp_path)
    create_plan(tmp_path)

    result = run_cli(
        tmp_path,
        "log",
        "create",
        "pcb-a0",
        "--id",
        "pcb-a0-log",
        "--created",
        "2026-06-27T12:00:00-04:00",
        "--body",
        "Created the cleanup log.",
    )

    assert result.returncode == 0
    listed = run_cli(tmp_path, "log", "list", "pcb-a0", "--format", "json")
    assert listed.returncode == 0
    payload = json.loads(listed.stdout)
    assert payload["logs"][0]["id"] == "pcb-a0-log"
    assert payload["logs"][0]["body"] == "Created the cleanup log."


def test_mutation_commands_fail_on_noncompliant_catalog(tmp_path: Path) -> None:
    write_plan_config(tmp_path)
    write_file(tmp_path / "docs" / "plans" / "old-plan.md", "# Missing front matter\n")

    result = run_cli(
        tmp_path,
        "plan",
        "create",
        "pcb-a0",
        "--title",
        "PCB A0",
        "--created",
        "2026-06-27",
    )

    assert result.returncode == 1
    assert "plan catalog is not compliant" in result.stdout


def test_plan_status_rejects_pending_plan_with_active_step(tmp_path: Path) -> None:
    write_plan_config(tmp_path)
    create_plan(tmp_path)
    active_step = run_cli(
        tmp_path,
        "plan",
        "step",
        "add",
        "pcb-a0",
        "audit",
        "--title",
        "Audit old plans",
        "--status",
        "active",
    )

    result = run_cli(tmp_path, "plan", "status", "pcb-a0", "pending")

    assert active_step.returncode == 0
    assert result.returncode == 1
    assert "pending plans cannot have active steps" in result.stdout


def test_plan_create_rejects_missing_plan_dependency(tmp_path: Path) -> None:
    write_plan_config(tmp_path)

    result = run_cli(
        tmp_path,
        "plan",
        "create",
        "pcb-a0",
        "--title",
        "PCB A0",
        "--created",
        "2026-06-27",
        "--depends-on",
        "missing-plan",
    )

    assert result.returncode == 1
    assert "missing plan dependency target(s): missing-plan" in result.stdout


def create_plan(root: Path) -> None:
    result = run_cli(
        root,
        "plan",
        "create",
        "pcb-a0",
        "--title",
        "PCB A0",
        "--created",
        "2026-06-27",
    )
    assert result.returncode == 0


def run_cli(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "wn_dev_std", *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def write_plan_config(root: Path) -> None:
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


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
