from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from textwrap import dedent
from typing import Protocol, cast

from config_fixtures import standard_config, standard_pyproject_tool_config

from wn_dev_std.cli.commands import log_list, plan_list
from wn_dev_std.plan_hygiene import LogRecord
from wn_dev_std.plan_reader import PlanReadContext, load_plan_read_context
from wn_dev_std.root_discovery import discover_project_root, load_standard_config


class PlanListTextFormatter(Protocol):
    def __call__(
        self,
        context: PlanReadContext,
        *,
        use_color: bool = False,
        width: int = 100,
    ) -> str:
        """Format plan-list text."""
        ...


class LogListTextFormatter(Protocol):
    def __call__(
        self,
        context: PlanReadContext,
        plan_id: str | None,
        logs: tuple[LogRecord, ...],
        *,
        use_color: bool = False,
        width: int = 100,
    ) -> str:
        """Format log-list text."""
        ...


def test_root_discovery_prefers_dev_std_standalone_config(tmp_path: Path) -> None:
    write_file(
        tmp_path / "dev-std.toml",
        standard_config(),
    )
    nested = tmp_path / "docs" / "plans"
    nested.mkdir(parents=True)

    discovered = discover_project_root(nested)

    assert discovered.root == tmp_path
    assert discovered.marker == "dev-std.toml"
    assert discovered.found_standard_config


def test_root_discovery_accepts_legacy_standalone_config(tmp_path: Path) -> None:
    write_file(
        tmp_path / "wn-dev-std.toml",
        standard_config(),
    )
    nested = tmp_path / "docs" / "plans"
    nested.mkdir(parents=True)

    discovered = discover_project_root(nested)

    assert discovered.root == tmp_path
    assert discovered.marker == "wn-dev-std.toml"
    assert discovered.found_standard_config


def test_root_discovery_prefers_dev_std_when_both_standalone_configs_exist(
    tmp_path: Path,
) -> None:
    write_file(
        tmp_path / "dev-std.toml",
        standard_config(),
    )
    write_file(
        tmp_path / "wn-dev-std.toml",
        standard_config("cpp-library"),
    )
    nested = tmp_path / "docs" / "plans"
    nested.mkdir(parents=True)

    discovered = discover_project_root(nested)

    assert discovered.root == tmp_path
    assert discovered.marker == "dev-std.toml"
    assert discovered.found_standard_config


def test_standard_config_loading_prefers_dev_std_over_legacy_marker(tmp_path: Path) -> None:
    write_file(
        tmp_path / "dev-std.toml",
        standard_config(),
    )
    write_file(
        tmp_path / "wn-dev-std.toml",
        standard_config("cpp-library"),
    )

    config = load_standard_config(tmp_path)

    assert config is not None
    assert config["profile"] == "python-package"


def test_root_discovery_uses_pyproject_tool_config(tmp_path: Path) -> None:
    write_file(
        tmp_path / "pyproject.toml",
        standard_pyproject_tool_config(),
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
    assert payload["marker"] == "dev-std.toml"
    assert payload["plans"][0]["id"] == "pcb-a0"
    assert payload["plans"][0]["steps"][0]["id"] == "audit"
    assert payload["plans"][0]["exit_criteria"][0]["id"] == "signoff"


def test_plan_list_text_groups_plans_by_work_state(tmp_path: Path) -> None:
    write_compliant_plan_repo(tmp_path)
    write_plan_document(tmp_path, "blocked-fab", "blocked", "2026-06-28")
    write_plan_document(tmp_path, "firmware-port", "pending", "2026-06-29")
    write_plan_document(
        tmp_path,
        "release-train",
        "active",
        "2026-06-30",
        depends_on=("pcb-a0",),
    )
    write_plan_document(
        tmp_path,
        "release-validation",
        "active",
        "2026-07-01",
        depends_on=("pcb-a0",),
    )

    result = run_cli(tmp_path, "plan", "list")

    assert result.returncode == 0
    assert (
        "Plans under " in result.stdout
        and "\n\nSummary:\n  active: 1\n  waiting: 2\n  parked: 1\n  blocked: 1\n" in result.stdout
    )
    assert "\nCurrent\n-------\n" in result.stdout
    assert "  - pcb-a0 [active]\n    created: 2026-06-27" in result.stdout
    assert (
        "last log:\n"
        "      - pcb-a0-log\n"
        "        created: 2026-06-27T12:00:00-04:00\n"
        "        step: audit\n"
        "    path: docs/plans/pcb-a0/plan.md" in result.stdout
    )
    assert "\nWaiting On Dependencies\n-----------------------\n" in result.stdout
    assert "waits on:\n      - pcb-a0 [active]" in result.stdout
    assert "\n    exit criteria: 4 pending\n\n  - release-validation [active]" in result.stdout
    assert "\nParked / Pending\n" in result.stdout
    assert "\nBlocked\n" in result.stdout
    assert "last log: none" in result.stdout
    assert "completed step:\n      - audit\n        Audit existing plans" in result.stdout
    assert "\n\n    pending steps:" in result.stdout
    assert (
        "      - release\n        Release package\n        depends_on:\n          - audit"
        in result.stdout
    )
    assert "\x1b[" not in result.stdout
    assert all(
        len(line) <= 100
        for line in result.stdout.splitlines()
        if not line.startswith("Plans under ")
    )
    assert result.stdout.endswith("\n\n")


def test_plan_list_text_colorizes_plan_and_step_ids_when_requested(tmp_path: Path) -> None:
    write_compliant_plan_repo(tmp_path)
    write_plan_document(tmp_path, "firmware-port", "pending", "2026-06-29")
    write_plan_document(
        tmp_path,
        "release-train",
        "active",
        "2026-06-30",
        depends_on=("pcb-a0",),
    )
    context = load_plan_read_context(tmp_path)
    formatter = cast(PlanListTextFormatter, vars(plan_list)["_format_plan_list_text"])

    text = formatter(context, use_color=True, width=80)

    assert "\x1b[32mCurrent\x1b[0m\n\x1b[32m-------\x1b[0m" in text
    assert "\x1b[30;47mpcb-a0\x1b[0m" in text
    assert "\x1b[30;47mpcb-a0\x1b[0m \x1b[1;37;42m[active]\x1b[0m" in text
    assert "\x1b[30;43m[pending]\x1b[0m" in text
    assert "    \x1b[36mcompleted step\x1b[0m:" in text
    assert "    \x1b[33mpending steps\x1b[0m:" in text
    assert "\x1b[1;33maudit\x1b[0m" in text
    assert "        step: \x1b[1;33maudit\x1b[0m" in text
    assert "          - \x1b[1;33maudit\x1b[0m" in text


def test_plan_show_outputs_body(tmp_path: Path) -> None:
    write_compliant_plan_repo(tmp_path)

    result = run_cli(tmp_path, "plan", "show", "pcb-a0")

    assert result.returncode == 0
    assert "Plan: pcb-a0" in result.stdout
    assert "audit [done] Audit existing plans" in result.stdout
    assert "signoff [pending] Focused signoff passes" in result.stdout
    assert "Body for PCB A0." in result.stdout


def test_log_list_outputs_logs_for_plan(tmp_path: Path) -> None:
    write_compliant_plan_repo(tmp_path)

    result = run_cli(tmp_path, "log", "list", "pcb-a0")

    assert result.returncode == 0
    assert (
        "Logs for pcb-a0 under " in result.stdout
        and "\n\nSummary:\n  logs: 1\n  steps: 1\n" in result.stdout
    )
    assert "\nBy Step\n-------\n  - audit\n    logs: 1\n    entries:" in result.stdout
    assert "      - pcb-a0-log\n        created: 2026-06-27T12:00:00-04:00" in result.stdout
    assert "        path:\n          docs/plans/pcb-a0/logs/2026-06-27.md" in result.stdout
    assert "step=audit" not in result.stdout
    assert "\x1b[" not in result.stdout
    assert all(
        len(line) <= 100 for line in result.stdout.splitlines() if not line.startswith("Logs for ")
    )
    assert result.stdout.endswith("\n\n")


def test_log_list_without_plan_lists_all_logs(tmp_path: Path) -> None:
    write_compliant_plan_repo(tmp_path)
    write_plan_document(tmp_path, "release-train", "pending", "2026-06-29")
    write_plan_log_document(
        tmp_path,
        "release-train",
        "release-train-log",
        "work",
        "2026-06-29T12:00:00-04:00",
    )

    result = run_cli(tmp_path, "log", "list")
    listed_json = run_cli(tmp_path, "log", "list", "--format", "json")

    assert result.returncode == 0
    assert listed_json.returncode == 0
    assert (
        "Logs under " in result.stdout
        and "\n\nSummary:\n  plans: 2\n  logs: 2\n  steps: 2\n" in result.stdout
    )
    assert "\nBy Plan\n-------\n  - pcb-a0\n    logs: 1\n    steps: 1" in result.stdout
    assert "  - release-train\n    logs: 1\n    steps: 1" in result.stdout
    assert "      - work\n        logs: 1\n        entries:" in result.stdout
    assert (
        "          - release-train-log\n            created: 2026-06-29T12:00:00-04:00"
        in result.stdout
    )
    assert all(
        len(line) <= 100
        for line in result.stdout.splitlines()
        if not line.startswith("Logs under ")
    )
    payload = json.loads(listed_json.stdout)
    assert payload["plan_id"] is None
    assert [log["id"] for log in payload["logs"]] == ["pcb-a0-log", "release-train-log"]


def test_log_list_text_colorizes_log_plan_and_step_ids_when_requested(tmp_path: Path) -> None:
    write_compliant_plan_repo(tmp_path)
    context = load_plan_read_context(tmp_path)
    logs = tuple(log for log in context.catalog.logs if log.plan_id == "pcb-a0")
    formatter = cast(LogListTextFormatter, vars(log_list)["_format_log_list_text"])

    text = formatter(context, "pcb-a0", logs, use_color=True, width=80)

    assert "Logs for \x1b[30;47mpcb-a0\x1b[0m under " in text
    assert "\x1b[36mBy Step\x1b[0m\n\x1b[36m-------\x1b[0m" in text
    assert "  - \x1b[1;33maudit\x1b[0m" in text
    assert "      - \x1b[30;47mpcb-a0-log\x1b[0m" in text


def test_log_show_outputs_body(tmp_path: Path) -> None:
    write_compliant_plan_repo(tmp_path)

    result = run_cli(tmp_path, "log", "show", "pcb-a0-log")

    assert result.returncode == 0
    assert "Log:\n  - pcb-a0-log\n    created: 2026-06-27T12:00:00-04:00" in result.stdout
    assert "    plan:\n      pcb-a0" in result.stdout
    assert "    step:\n      audit" in result.stdout
    assert "    path:\n      docs/plans/pcb-a0/logs/2026-06-27.md" in result.stdout
    assert "Work log body." in result.stdout


def test_log_show_json_is_machine_readable(tmp_path: Path) -> None:
    write_compliant_plan_repo(tmp_path)

    result = run_cli(tmp_path, "log", "show", "pcb-a0-log", "--format", "json")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["id"] == "pcb-a0-log"
    assert payload["plan_id"] == "pcb-a0"
    assert payload["step_id"] == "audit"
    assert payload["body"] == "Work log body."


def test_plan_read_commands_fail_on_noncompliant_catalog(tmp_path: Path) -> None:
    write_file(
        tmp_path / "dev-std.toml",
        standard_config(),
    )
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
        root / "dev-std.toml",
        standard_config(
            extra="""
            [documentation.plans]
            roots = ["docs/plans"]
            """,
        ),
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

            [[steps]]
            id = "design-doc-intent-audit"
            title = "Audit design docs, ADRs, and requirements against implementation"
            status = "pending"
            depends_on = ["release"]

            [[steps]]
            id = "external-review"
            title = "Obtain independent external review"
            status = "pending"
            depends_on = ["release", "design-doc-intent-audit", "test-runtime-impact-audit"]

            [[steps]]
            id = "test-runtime-impact-audit"
            title = "Audit new test runtime impact"
            status = "pending"
            depends_on = ["release"]

            [[exit_criteria]]
            id = "signoff"
            title = "Focused signoff passes"
            status = "pending"

            [[exit_criteria]]
            id = "design-doc-intent-audit"
            title = "Design docs, ADRs, and requirements match implementation"
            status = "pending"

            [[exit_criteria]]
            id = "test-runtime-impact-audit"
            title = "New tests are listed and runtime impact is reviewed"
            status = "pending"

            [[exit_criteria]]
            id = "external-review"
            title = "Independent external review is complete"
            status = "pending"
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
            step_id = "audit"
            created = "2026-06-27T12:00:00-04:00"
            +++

            Work log body.
            """
        ).lstrip(),
    )


def write_plan_document(
    root: Path,
    plan_id: str,
    status: str,
    created: str,
    *,
    depends_on: tuple[str, ...] = (),
) -> None:
    depends_line = ""
    if depends_on:
        quoted_dependencies = ", ".join(f'"{dependency}"' for dependency in depends_on)
        depends_line = f"depends_on = [{quoted_dependencies}]\n"
    write_file(
        root / "docs" / "plans" / plan_id / "plan.md",
        dedent(
            f"""
            +++
            type = "plan"
            id = "{plan_id}"
            status = "{status}"
            created = "{created}"
            {depends_line}
            [[steps]]
            id = "work"
            title = "Do the work"
            status = "pending"

            [[steps]]
            id = "design-doc-intent-audit"
            title = "Audit design docs, ADRs, and requirements against implementation"
            status = "pending"
            depends_on = ["work"]

            [[steps]]
            id = "external-review"
            title = "Obtain independent external review"
            status = "pending"
            depends_on = ["design-doc-intent-audit", "test-runtime-impact-audit"]

            [[steps]]
            id = "test-runtime-impact-audit"
            title = "Audit new test runtime impact"
            status = "pending"
            depends_on = ["work"]

            [[exit_criteria]]
            id = "signoff"
            title = "Focused signoff passes"
            status = "pending"

            [[exit_criteria]]
            id = "design-doc-intent-audit"
            title = "Design docs, ADRs, and requirements match implementation"
            status = "pending"

            [[exit_criteria]]
            id = "test-runtime-impact-audit"
            title = "New tests are listed and runtime impact is reviewed"
            status = "pending"

            [[exit_criteria]]
            id = "external-review"
            title = "Independent external review is complete"
            status = "pending"
            +++

            # {plan_id}
            """
        ).lstrip(),
    )


def write_plan_log_document(
    root: Path,
    plan_id: str,
    log_id: str,
    step_id: str,
    created: str,
) -> None:
    write_file(
        root / "docs" / "plans" / plan_id / "logs" / f"{created.replace(':', '')}.md",
        dedent(
            f"""
            +++
            type = "plan_log"
            id = "{log_id}"
            plan_id = "{plan_id}"
            step_id = "{step_id}"
            created = "{created}"
            +++

            Additional work log.
            """
        ).lstrip(),
    )


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
