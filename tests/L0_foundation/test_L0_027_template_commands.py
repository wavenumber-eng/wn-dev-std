from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from wn_dev_std import template_library

ROOT = Path(__file__).resolve().parents[2]


def test_template_list_reports_version_matched_references() -> None:
    result = run_cli("template", "list", "--format", "json")

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert [item["name"] for item in payload["templates"]] == [
        "typespec-contract",
        "lit-activity-web",
    ]


def test_template_copy_creates_project_owned_lit_reference(tmp_path: Path) -> None:
    destination = tmp_path / "web-app"

    result = run_cli("template", "copy", "lit-activity-web", str(destination))

    assert result.returncode == 0, result.stdout + result.stderr
    assert (destination / "package-lock.json").is_file()
    assert (destination / "src" / "activity" / "engine.ts").is_file()
    assert (destination / "public" / "backgrounds" / "manifest.json").is_file()
    assert not (destination / "node_modules").exists()
    assert not (destination / "dist").exists()


def test_template_copy_refuses_existing_destination(tmp_path: Path) -> None:
    destination = tmp_path / "existing"
    destination.mkdir()
    marker = destination / "keep.txt"
    marker.write_text("keep\n", encoding="utf-8")

    result = run_cli("template", "copy", "typespec-contract", str(destination))

    assert result.returncode == 1
    assert "destination already exists" in result.stdout
    assert marker.read_text(encoding="utf-8") == "keep\n"


def test_template_copy_refuses_destination_nested_under_checkout_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = tmp_path / "repository"
    module_path = repository / "src" / "wn_dev_std" / "template_library.py"
    source = repository / "docs" / "templates" / "typespec-contract"
    source.mkdir(parents=True)
    (source / "README.md").write_text("reference\n", encoding="utf-8")
    monkeypatch.setattr(template_library, "__file__", str(module_path))
    destination = source / "recursive-copy"

    with pytest.raises(ValueError, match="destination must be outside"):
        template_library.copy_template("typespec-contract", destination)

    assert not destination.exists()


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "wn_dev_std", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
