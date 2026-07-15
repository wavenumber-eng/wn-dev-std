from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from textwrap import dedent
from typing import Protocol, cast

from config_fixtures import standard_config

from wn_dev_std.cli.commands import governance_list_common
from wn_dev_std.cli.commands.governance_text import (
    ADR_LIST_SECTIONS,
    REQUIREMENT_LIST_SECTIONS,
    GovernanceListSection,
)
from wn_dev_std.doc_governance import GovernanceRecord, load_governance_catalog


class GovernanceListTextFormatter(Protocol):
    def __call__(
        self,
        root: object,
        title: str,
        records: tuple[GovernanceRecord, ...],
        sections: tuple[GovernanceListSection, ...],
        *,
        use_color: bool = False,
        width: int = 100,
    ) -> str:
        """Format governance-list text."""
        ...


def test_adr_list_and_show_match_plan_read_conventions(tmp_path: Path) -> None:
    write_governance_repo(tmp_path)

    listed = run_cli(tmp_path, "adr", "list", "--format", "json")
    shown = run_cli(tmp_path, "adr", "show", "core-adr-0001", "--format", "json")
    listed_text = run_cli(tmp_path, "adr", "list")
    shown_text = run_cli(tmp_path, "adr", "show", "core-adr-0001")

    assert listed.returncode == 0
    assert shown.returncode == 0
    assert listed_text.returncode == 0
    assert shown_text.returncode == 0
    list_payload = json.loads(listed.stdout)
    show_payload = json.loads(shown.stdout)
    assert list_payload["marker"] == "dev-std.toml"
    assert list_payload["adrs"][0]["id"] == "core-adr-0001"
    assert list_payload["adrs"][0]["path"] == "docs/core/adr/core-adr-0001-record.md"
    assert show_payload["id"] == "core-adr-0001"
    assert show_payload["body"] == "# Record\n\nAccepted decision."
    assert (
        "ADRs under " in listed_text.stdout
        and "\n\nSummary:\n  proposed: 0\n  accepted: 1\n  deprecated: 0\n  superseded: 0\n"
        in listed_text.stdout
    )
    assert "\nAccepted\n--------\n" in listed_text.stdout
    assert "  - core-adr-0001 [accepted]\n    created: 2026-07-02" in listed_text.stdout
    assert "    title:\n      Record" in listed_text.stdout
    assert "    path:\n      docs/core/adr/core-adr-0001-record.md" in listed_text.stdout
    assert "\x1b[" not in listed_text.stdout
    assert all(
        len(line) <= 100
        for line in listed_text.stdout.splitlines()
        if not line.startswith("ADRs under ")
    )
    assert listed_text.stdout.endswith("\n\n")
    assert "ADR:\n  - core-adr-0001 [accepted]\n    created: 2026-07-02" in shown_text.stdout
    assert "    domain: core\n    title:\n      Record" in shown_text.stdout
    assert "\n# Record\n\nAccepted decision.\n\n" in shown_text.stdout


def test_adr_list_text_colorizes_record_ids_and_statuses_when_requested(
    tmp_path: Path,
) -> None:
    write_governance_repo(tmp_path)
    catalog = load_governance_catalog(tmp_path)
    formatter = cast(
        GovernanceListTextFormatter,
        vars(governance_list_common)["_format_pretty_record_list_text"],
    )

    text = formatter(
        catalog.root, "ADRs", catalog.adrs, ADR_LIST_SECTIONS, use_color=True, width=80
    )

    assert "\x1b[32mAccepted\x1b[0m\n\x1b[32m--------\x1b[0m" in text
    assert "\x1b[30;47mcore-adr-0001\x1b[0m" in text
    assert "\x1b[1;37;42m[accepted]\x1b[0m" in text


def test_requirement_list_and_show_match_plan_read_conventions(tmp_path: Path) -> None:
    write_governance_repo(tmp_path)

    listed_json = run_cli(tmp_path, "requirement", "list", "--format", "json")
    shown_json = run_cli(tmp_path, "requirement", "show", "core-req-0001", "--format", "json")
    listed = run_cli(tmp_path, "requirement", "list")
    shown = run_cli(tmp_path, "requirement", "show", "core-req-0001")

    assert listed_json.returncode == 0
    assert shown_json.returncode == 0
    assert listed.returncode == 0
    assert shown.returncode == 0
    list_payload = json.loads(listed_json.stdout)
    show_payload = json.loads(shown_json.stdout)
    assert list_payload["requirements"][0]["id"] == "core-req-0001"
    assert (
        list_payload["requirements"][0]["path"] == "docs/core/requirements/core-req-0001-verify.md"
    )
    assert show_payload["id"] == "core-req-0001"
    assert show_payload["body"] == "# Verify\n\nVerification exists."
    assert (
        "Requirements under " in listed.stdout
        and "\n\nSummary:\n  draft: 0\n  active: 1\n  implemented: 0\n  deprecated: 0\n"
        in listed.stdout
    )
    assert "  superseded: 0\n" in listed.stdout
    assert "\nActive\n------\n" in listed.stdout
    assert "  - core-req-0001 [active]\n    created: 2026-07-02" in listed.stdout
    assert "    title:\n      Verify" in listed.stdout
    assert "    path:\n      docs/core/requirements/core-req-0001-verify.md" in listed.stdout
    assert "\x1b[" not in listed.stdout
    assert all(
        len(line) <= 100
        for line in listed.stdout.splitlines()
        if not line.startswith("Requirements under ")
    )
    assert listed.stdout.endswith("\n\n")
    assert "Requirement:\n  - core-req-0001 [active]\n    created: 2026-07-02" in shown.stdout
    assert "    domain: core\n    title:\n      Verify" in shown.stdout
    assert "Verification exists." in shown.stdout


def test_requirement_list_text_colorizes_record_ids_and_statuses_when_requested(
    tmp_path: Path,
) -> None:
    write_governance_repo(tmp_path)
    catalog = load_governance_catalog(tmp_path)
    formatter = cast(
        GovernanceListTextFormatter,
        vars(governance_list_common)["_format_pretty_record_list_text"],
    )

    text = formatter(
        catalog.root,
        "Requirements",
        catalog.requirements,
        REQUIREMENT_LIST_SECTIONS,
        use_color=True,
        width=80,
    )

    assert "\x1b[32mActive\x1b[0m\n\x1b[32m------\x1b[0m" in text
    assert "\x1b[30;47mcore-req-0001\x1b[0m" in text
    assert "\x1b[1;37;42m[active]\x1b[0m" in text


def test_governance_read_commands_fail_on_legacy_adr_markdown(tmp_path: Path) -> None:
    write_file(
        tmp_path / "dev-std.toml",
        standard_config(),
    )
    write_file(tmp_path / "docs" / "core" / "adr" / "legacy-adr.md", "# Legacy\n")

    result = run_cli(tmp_path, "adr", "list")

    assert result.returncode == 1
    assert "governance catalog is not compliant" in result.stdout
    assert "ADR missing TOML front matter" in result.stdout


def test_governance_read_commands_fail_on_legacy_requirement_markdown(
    tmp_path: Path,
) -> None:
    write_file(
        tmp_path / "dev-std.toml",
        standard_config(),
    )
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
    write_file(
        root / "dev-std.toml",
        standard_config(),
    )
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
