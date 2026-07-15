from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from config_fixtures import standard_config


def test_adr_create_writes_compliant_adr(tmp_path: Path) -> None:
    write_file(
        tmp_path / "dev-std.toml",
        standard_config(),
    )

    result = run_cli(
        tmp_path,
        "adr",
        "create",
        "core-adr-0001",
        "--domain",
        "core",
        "--title",
        "Record Decisions",
        "--created",
        "2026-07-02",
        "--body",
        "# Record Decisions\n\nAccepted context.",
    )

    assert result.returncode == 0
    path = tmp_path / "docs" / "core" / "adr" / "core-adr-0001-record-decisions.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert 'type = "adr"' in text
    assert 'status = "proposed"' in text
    assert "# Record Decisions" in text
    listed = run_cli(tmp_path, "adr", "list", "--format", "json")
    assert listed.returncode == 0
    payload = json.loads(listed.stdout)
    assert payload["adrs"][0]["id"] == "core-adr-0001"


def test_requirement_create_writes_compliant_draft_from_body_file(tmp_path: Path) -> None:
    write_file(
        tmp_path / "dev-std.toml",
        standard_config(),
    )
    body = tmp_path / "body.md"
    body.write_text("# Audit Requirements\n\nDraft requirement.", encoding="utf-8")

    result = run_cli(
        tmp_path,
        "requirement",
        "create",
        "core-req-0001",
        "--domain",
        "core",
        "--title",
        "Audit Requirements",
        "--created",
        "2026-07-02",
        "--body-file",
        str(body),
    )

    assert result.returncode == 0
    path = tmp_path / "docs" / "core" / "requirements" / "core-req-0001-audit-requirements.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert 'type = "requirement"' in text
    assert 'status = "draft"' in text
    assert "Draft requirement." in text
    shown = run_cli(tmp_path, "requirement", "show", "core-req-0001")
    assert shown.returncode == 0
    assert "Requirement:\n  - core-req-0001 [draft]" in shown.stdout
    assert "Draft requirement." in shown.stdout


def test_adr_create_rejects_duplicate_document(tmp_path: Path) -> None:
    write_file(
        tmp_path / "dev-std.toml",
        standard_config(),
    )
    args = (
        "adr",
        "create",
        "core-adr-0001",
        "--domain",
        "core",
        "--title",
        "Record Decisions",
        "--created",
        "2026-07-02",
    )

    first = run_cli(tmp_path, *args)
    second = run_cli(tmp_path, *args)

    assert first.returncode == 0
    assert second.returncode == 1
    assert "already exists" in second.stdout


def run_cli(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "wn_dev_std", *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
