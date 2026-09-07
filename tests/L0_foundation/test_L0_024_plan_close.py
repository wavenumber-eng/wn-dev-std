from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from config_fixtures import standard_config


def test_plan_help_lists_close_command_and_durable_requirement(tmp_path: Path) -> None:
    plan_help = run_cli(tmp_path, "plan", "--help")
    close_help = run_cli(tmp_path, "plan", "close", "--help")

    assert plan_help.returncode == 0
    assert "close" in plan_help.stdout
    assert close_help.returncode == 0
    assert "durable-document review" in close_help.stdout
    assert "--delete" in close_help.stdout


def test_plan_close_lists_concrete_blockers_without_deleting(tmp_path: Path) -> None:
    write_plan_config(tmp_path)
    write_plan(tmp_path, "pcb-a0", ready=False)

    result = run_cli(tmp_path, "plan", "close", "pcb-a0")

    assert result.returncode == 1
    assert "Plan pcb-a0 is not ready for closeout" in result.stdout
    assert "steps not done: work" in result.stdout
    assert "exit criteria not met: signoff" in result.stdout
    assert "Move durable outcomes into design docs, ADRs, requirements" in result.stdout
    assert "No files deleted" in result.stdout
    assert plan_path(tmp_path, "pcb-a0").exists()


def test_plan_close_ready_preview_gives_exact_finish_command(tmp_path: Path) -> None:
    write_plan_config(tmp_path)
    write_plan(tmp_path, "pcb-a0", ready=True)

    result = run_cli(tmp_path, "plan", "close", "pcb-a0")

    assert result.returncode == 0
    assert "Plan pcb-a0 is ready for closeout" in result.stdout
    assert "All 4 steps are done" in result.stdout
    assert "All 4 exit criteria are met" in result.stdout
    assert "dev-std plan close pcb-a0 --delete" in result.stdout
    assert plan_path(tmp_path, "pcb-a0").exists()


def test_plan_close_delete_removes_only_plan_and_attached_logs(tmp_path: Path) -> None:
    write_plan_config(tmp_path)
    write_plan(tmp_path, "pcb-a0", ready=True)
    log_path = write_log(tmp_path, "pcb-a0")
    retained_path = tmp_path / "docs" / "plans" / "README.md"
    write_file(retained_path, "Plan root index.\n")

    result = run_cli(tmp_path, "plan", "close", "pcb-a0", "--delete")

    assert result.returncode == 0
    assert not plan_path(tmp_path, "pcb-a0").exists()
    assert not log_path.exists()
    assert retained_path.exists()
    assert "Deleted temporary closeout files" in result.stdout
    assert "Next: dev-std audit . --scope docs.plans" in result.stdout
    audit = run_cli(tmp_path, "audit", "--scope", "docs.plans")
    assert audit.returncode == 0


def test_plan_close_blocks_deletion_when_another_plan_depends_on_it(tmp_path: Path) -> None:
    write_plan_config(tmp_path)
    write_plan(tmp_path, "pcb-a0", ready=True)
    write_plan(tmp_path, "next-plan", ready=False, depends_on="pcb-a0")

    result = run_cli(tmp_path, "plan", "close", "pcb-a0", "--delete")

    assert result.returncode == 1
    assert "dependent plans still reference this plan: next-plan" in result.stdout
    assert "No files deleted" in result.stdout
    assert plan_path(tmp_path, "pcb-a0").exists()


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
        root / "dev-std.toml",
        standard_config(
            extra="""
            [documentation.plans]
            roots = ["docs/plans"]
            """,
        ),
    )


def write_plan(root: Path, plan_id: str, *, ready: bool, depends_on: str | None = None) -> None:
    step_status = "done" if ready else "pending"
    criterion_status = "met" if ready else "pending"
    dependency = f'depends_on = ["{depends_on}"]\n' if depends_on else ""
    write_file(
        plan_path(root, plan_id),
        f"""+++
type = "plan"
id = "{plan_id}"
status = "active"
created = "2026-09-06"
{dependency}
[[steps]]
id = "work"
title = "Execute plan work"
status = "{step_status}"

[[steps]]
id = "design-doc-intent-audit"
title = "Audit design docs, ADRs, and requirements against implementation"
status = "{step_status}"
depends_on = ["work"]

[[steps]]
id = "test-runtime-impact-audit"
title = "Audit new test runtime impact"
status = "{step_status}"
depends_on = ["work"]

[[steps]]
id = "external-review"
title = "Obtain independent external review"
status = "{step_status}"
depends_on = ["work", "design-doc-intent-audit", "test-runtime-impact-audit"]

[[exit_criteria]]
id = "signoff"
title = "Focused signoff passes"
status = "{criterion_status}"

[[exit_criteria]]
id = "design-doc-intent-audit"
title = "Design docs, ADRs, and requirements match implementation"
status = "{criterion_status}"

[[exit_criteria]]
id = "test-runtime-impact-audit"
title = "New tests are listed and runtime impact is reviewed"
status = "{criterion_status}"

[[exit_criteria]]
id = "external-review"
title = "Independent external review is complete"
status = "{criterion_status}"
+++

# {plan_id}
""",
    )


def write_log(root: Path, plan_id: str) -> Path:
    path = root / "docs" / "plans" / plan_id / "logs" / "closeout.md"
    write_file(
        path,
        f"""+++
type = "plan_log"
id = "{plan_id}-closeout"
plan_id = "{plan_id}"
step_id = "external-review"
created = "2026-09-06T12:00:00-04:00"
+++

# Closeout
""",
    )
    return path


def plan_path(root: Path, plan_id: str) -> Path:
    return root / "docs" / "plans" / plan_id / "plan.md"


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
