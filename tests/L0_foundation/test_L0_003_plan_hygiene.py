from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from wn_dev_std.checks import CheckResult, run_audit_checks


def test_docs_plans_audit_passes_valid_plan_and_log(tmp_path: Path) -> None:
    write_plan(tmp_path, "docs/plans/pcb-a0/plan.md", "pcb-a0", "active")
    write_log(tmp_path, "docs/plans/pcb-a0/log/2026-06-27T120000Z.md", "pcb-a0-log", "pcb-a0")

    result = docs_plans_result(tmp_path)

    assert result.passed
    assert "1 plan(s) and 1 log(s)" in result.detail


def test_docs_plans_audit_passes_pending_plan_with_dependency(tmp_path: Path) -> None:
    write_plan(tmp_path, "docs/plans/pcb-a0/plan.md", "pcb-a0", "active")
    write_plan(
        tmp_path,
        "docs/plans/matz/plan.md",
        "matz-rework",
        "pending",
        depends_on=("pcb-a0",),
    )

    result = docs_plans_result(tmp_path)

    assert result.passed
    assert "2 plan(s)" in result.detail


def test_docs_plans_audit_passes_plan_with_steps(tmp_path: Path) -> None:
    write_plan(
        tmp_path,
        "docs/plans/pcb-a0/plan.md",
        "pcb-a0",
        "active",
        steps=(
            ("audit", "Audit models", "done", ()),
            ("fix", "Fix model issues", "active", ("audit",)),
            ("verify", "Run signoff", "pending", ("fix",)),
        ),
    )

    result = docs_plans_result(tmp_path)

    assert result.passed


def test_docs_plans_audit_fails_plan_like_file_without_front_matter(tmp_path: Path) -> None:
    write_file(tmp_path / "docs" / "plans" / "pcb_a0_plan.md", "# PCB A0\n")

    result = docs_plans_result(tmp_path)

    assert not result.passed
    assert "missing TOML front matter" in result.detail


def test_docs_plans_audit_fails_completed_plan(tmp_path: Path) -> None:
    write_plan(tmp_path, "docs/plans/pcb-a0/plan.md", "pcb-a0", "complete")

    result = docs_plans_result(tmp_path)

    assert not result.passed
    assert "complete plans must be closed out and removed" in result.detail


def test_docs_plans_audit_fails_duplicate_plan_ids(tmp_path: Path) -> None:
    write_plan(tmp_path, "docs/plans/pcb-a0/plan.md", "pcb-a0", "active")
    write_plan(tmp_path, "docs/plans/matz/plan.md", "pcb-a0", "pending")

    result = docs_plans_result(tmp_path)

    assert not result.passed
    assert "duplicate plan ids: pcb-a0" in result.detail


def test_docs_plans_audit_fails_missing_dependency(tmp_path: Path) -> None:
    write_plan(
        tmp_path,
        "docs/plans/matz/plan.md",
        "matz-rework",
        "pending",
        depends_on=("pcb-a0",),
    )

    result = docs_plans_result(tmp_path)

    assert not result.passed
    assert "missing depends_on targets: pcb-a0" in result.detail


def test_docs_plans_audit_fails_duplicate_step_ids(tmp_path: Path) -> None:
    write_plan(
        tmp_path,
        "docs/plans/pcb-a0/plan.md",
        "pcb-a0",
        "active",
        steps=(
            ("audit", "Audit models", "done", ()),
            ("audit", "Audit again", "pending", ()),
        ),
    )

    result = docs_plans_result(tmp_path)

    assert not result.passed
    assert "duplicate step ids: audit" in result.detail


def test_docs_plans_audit_fails_missing_step_dependency(tmp_path: Path) -> None:
    write_plan(
        tmp_path,
        "docs/plans/pcb-a0/plan.md",
        "pcb-a0",
        "active",
        steps=(("verify", "Run signoff", "pending", ("missing",)),),
    )

    result = docs_plans_result(tmp_path)

    assert not result.passed
    assert "missing depends_on targets: missing" in result.detail


def test_docs_plans_audit_fails_multiple_active_steps(tmp_path: Path) -> None:
    write_plan(
        tmp_path,
        "docs/plans/pcb-a0/plan.md",
        "pcb-a0",
        "active",
        steps=(
            ("audit", "Audit models", "active", ()),
            ("fix", "Fix model issues", "active", ()),
        ),
    )

    result = docs_plans_result(tmp_path)

    assert not result.passed
    assert "more than one active step" in result.detail


def test_docs_plans_audit_fails_active_plan_with_all_steps_done(tmp_path: Path) -> None:
    write_plan(
        tmp_path,
        "docs/plans/pcb-a0/plan.md",
        "pcb-a0",
        "active",
        steps=(("audit", "Audit models", "done", ()),),
    )

    result = docs_plans_result(tmp_path)

    assert not result.passed
    assert "all steps are done but plan is still active" in result.detail


def test_docs_plans_audit_fails_pending_plan_with_active_step(tmp_path: Path) -> None:
    write_plan(
        tmp_path,
        "docs/plans/pcb-a0/plan.md",
        "pcb-a0",
        "pending",
        steps=(("audit", "Audit models", "active", ()),),
    )

    result = docs_plans_result(tmp_path)

    assert not result.passed
    assert "pending plan cannot have active steps" in result.detail


def test_docs_plans_audit_fails_orphan_log(tmp_path: Path) -> None:
    write_log(
        tmp_path,
        "docs/plans/pcb-a0/log/2026-06-27T120000Z.md",
        "pcb-a0-log",
        "pcb-a0",
    )

    result = docs_plans_result(tmp_path)

    assert not result.passed
    assert "unknown plan_id 'pcb-a0'" in result.detail


def test_docs_plans_audit_fails_log_file_without_front_matter(tmp_path: Path) -> None:
    write_plan(tmp_path, "docs/plans/pcb-a0/plan.md", "pcb-a0", "active")
    write_file(tmp_path / "docs" / "plans" / "pcb-a0" / "logs" / "2026-06-27.md", "notes\n")

    result = docs_plans_result(tmp_path)

    assert not result.passed
    assert "missing TOML front matter" in result.detail


def test_docs_plans_audit_fails_rogue_plan_like_file(tmp_path: Path) -> None:
    write_file(tmp_path / "docs" / "design" / "migration_plan.md", "# Migration Plan\n")

    result = docs_plans_result(tmp_path)

    assert not result.passed
    assert "rogue plan/log-like document" in result.detail


def test_docs_plans_audit_does_not_flag_planar_as_plan_like(tmp_path: Path) -> None:
    write_file(tmp_path / "docs" / "models" / "geom_planar_region.html", "<html></html>\n")

    result = docs_plans_result(tmp_path)

    assert result.passed


def test_docs_plans_audit_fails_rogue_log_like_file(tmp_path: Path) -> None:
    write_file(tmp_path / "docs" / "logs" / "2026-06-27.md", "notes\n")

    result = docs_plans_result(tmp_path)

    assert not result.passed
    assert "rogue plan/log-like document" in result.detail


def test_docs_plans_audit_uses_configured_plan_roots(tmp_path: Path) -> None:
    write_file(
        tmp_path / "wn-dev-std.toml",
        dedent(
            """
            [documentation.plans]
            roots = ["viz/docs/plans", "data_models/docs/pcb/plans"]
            """
        ).lstrip(),
    )
    write_plan(tmp_path, "viz/docs/plans/viz-roadmap.md", "viz-roadmap", "active")
    write_plan(tmp_path, "data_models/docs/pcb/plans/pcb-a0-plan.md", "pcb-a0", "active")

    result = docs_plans_result(tmp_path)

    assert result.passed
    assert "2 plan(s)" in result.detail


def test_docs_plans_scope_does_not_require_python_build_backend(tmp_path: Path) -> None:
    write_file(
        tmp_path / "pyproject.toml",
        dedent(
            """
            [project]
            name = "workspace-root"
            version = "0.1.0"
            """
        ).lstrip(),
    )

    results = run_audit_checks(tmp_path, ("docs.plans",))

    assert [result.name for result in results] == ["docs.plans"]
    assert results[0].passed


def test_configured_plan_roots_are_allowed_locations_not_required_folders(tmp_path: Path) -> None:
    write_file(
        tmp_path / "wn-dev-std.toml",
        dedent(
            """
            [documentation.plans]
            roots = ["docs/domain/plans"]
            """
        ).lstrip(),
    )

    result = docs_plans_result(tmp_path)

    assert result.passed
    assert "no configured plan roots found" in result.detail


def docs_plans_result(root: Path) -> CheckResult:
    results = run_audit_checks(root, ("docs.plans",))
    return next(result for result in results if result.name == "docs.plans")


def write_plan(
    root: Path,
    relative_path: str,
    plan_id: str,
    status: str,
    *,
    depends_on: tuple[str, ...] = (),
    steps: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (),
) -> None:
    front_matter = [
        'type = "plan"',
        f'id = "{plan_id}"',
        f'status = "{status}"',
        'created = "2026-06-27"',
    ]
    if depends_on:
        quoted = ", ".join(f'"{item}"' for item in depends_on)
        front_matter.append(f"depends_on = [{quoted}]")
    for step_id, title, step_status, step_depends_on in steps:
        front_matter.extend(
            [
                "",
                "[[steps]]",
                f'id = "{step_id}"',
                f'title = "{title}"',
                f'status = "{step_status}"',
            ]
        )
        if step_depends_on:
            quoted = ", ".join(f'"{item}"' for item in step_depends_on)
            front_matter.append(f"depends_on = [{quoted}]")
    write_file(
        root / relative_path,
        "+++\n" + "\n".join(front_matter) + f"\n+++\n\n# {plan_id}\n",
    )


def write_log(root: Path, relative_path: str, log_id: str, plan_id: str) -> None:
    write_file(
        root / relative_path,
        dedent(
            f"""
            +++
            type = "plan_log"
            id = "{log_id}"
            plan_id = "{plan_id}"
            created = "2026-06-27T12:00:00-04:00"
            +++

            Log body.
            """
        ).lstrip(),
    )


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
