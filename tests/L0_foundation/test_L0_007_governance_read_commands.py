from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from textwrap import dedent


def test_adr_list_and_show_match_plan_read_conventions(tmp_path: Path) -> None:
    write_governance_repo(tmp_path)

    listed = run_cli(tmp_path, "adr", "list", "--format", "json")
    shown = run_cli(tmp_path, "adr", "show", "core-adr-0001", "--format", "json")

    assert listed.returncode == 0
    assert shown.returncode == 0
    list_payload = json.loads(listed.stdout)
    show_payload = json.loads(shown.stdout)
    assert list_payload["marker"] == "dev-std.toml"
    assert list_payload["adrs"][0]["id"] == "core-adr-0001"
    assert list_payload["adrs"][0]["path"] == "docs/core/adr/core-adr-0001-record.md"
    assert show_payload["id"] == "core-adr-0001"
    assert show_payload["body"] == "# Record\n\nAccepted decision."


def test_requirement_list_and_show_match_plan_read_conventions(tmp_path: Path) -> None:
    write_governance_repo(tmp_path)

    listed = run_cli(tmp_path, "requirement", "list")
    shown = run_cli(tmp_path, "requirement", "show", "core-req-0001")

    assert listed.returncode == 0
    assert shown.returncode == 0
    assert "Requirements under" in listed.stdout
    assert "core-req-0001 [active]" in listed.stdout
    assert "Requirement: core-req-0001" in shown.stdout
    assert "Verification exists." in shown.stdout


def test_governance_read_commands_fail_on_legacy_adr_markdown(tmp_path: Path) -> None:
    write_file(tmp_path / "dev-std.toml", 'profile = "python-package"\n')
    write_file(tmp_path / "docs" / "core" / "adr" / "legacy-adr.md", "# Legacy\n")

    result = run_cli(tmp_path, "adr", "list")

    assert result.returncode == 1
    assert "governance catalog is not compliant" in result.stdout
    assert "ADR missing TOML front matter" in result.stdout


def test_governance_read_commands_fail_on_legacy_requirement_markdown(
    tmp_path: Path,
) -> None:
    write_file(tmp_path / "dev-std.toml", 'profile = "python-package"\n')
    write_file(
        tmp_path / "docs" / "core" / "requirements" / "legacy-requirement.md",
        "# Legacy\n",
    )

    result = run_cli(tmp_path, "requirement", "list")

    assert result.returncode == 1
    assert "governance catalog is not compliant" in result.stdout
    assert "requirement missing TOML front matter" in result.stdout


def run_cli(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "wn_dev_std", *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def write_governance_repo(root: Path) -> None:
    write_file(root / "dev-std.toml", 'profile = "python-package"\n')
    write_file(
        root / "docs" / "core" / "adr" / "core-adr-0001-record.md",
        dedent(
            """
            +++
            type = "adr"
            id = "core-adr-0001"
            domain = "core"
            status = "accepted"
            title = "Record"
            created = "2026-07-02"
            +++

            # Record

            Accepted decision.
            """
        ).lstrip(),
    )
    write_file(
        root / "docs" / "core" / "requirements" / "core-req-0001-verify.md",
        dedent(
            """
            +++
            type = "requirement"
            id = "core-req-0001"
            domain = "core"
            status = "active"
            title = "Verify"
            created = "2026-07-02"

            [[verification_refs]]
            kind = "local_pytest"
            target = "tests/test_verify.py::test_verify"
            +++

            # Verify

            Verification exists.
            """
        ).lstrip(),
    )
    write_file(root / "tests" / "test_verify.py", "def test_verify(): pass\n")


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
