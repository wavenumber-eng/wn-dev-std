from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import cast

import pytest

from build_hooks.template_safety import sensitive_template_files
from wn_dev_std.checks import run_audit_checks

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize(
    ("relative_source", "scope"),
    (
        ("docs/templates/typespec-contract", "contracts"),
        ("docs/templates/web/lit-activity", "application"),
    ),
)
def test_copy_owned_templates_pass_clean_signoff(
    tmp_path: Path,
    relative_source: str,
    scope: str,
) -> None:
    source = ROOT / relative_source
    project = tmp_path / source.name
    shutil.copytree(
        source,
        project,
        ignore=shutil.ignore_patterns(
            "node_modules",
            "dist",
            "coverage",
            ".cache",
            ".pytest_cache",
            ".ruff_cache",
            ".venv",
            "__pycache__",
        ),
    )

    audit = run_audit_checks(project, (scope,))
    assert audit and all(result.passed for result in audit), [result.to_dict() for result in audit]
    run_command((npm_executable(), "ci"), project)
    run_command((npm_executable(), "run", "signoff"), project)
    if scope == "contracts":
        contract = project / "contracts" / "models.tsp"
        contract.write_text(
            contract.read_text(encoding="utf-8") + "\n// stale-output probe\n", encoding="utf-8"
        )
        result = subprocess.run(
            (npm_executable(), "run", "verify:generated"),
            cwd=project,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "generated outputs are stale" in result.stdout + result.stderr


def test_distribution_policy_excludes_template_working_directories() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    for pattern in ("**/node_modules/**", "**/dist/**", "**/.venv/**", "**/coverage/**"):
        assert f'"{pattern}"' in text


def test_template_resource_build_rejects_sensitive_working_files(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
    (tmp_path / ".env.example").write_text("TOKEN=replace-me\n", encoding="utf-8")
    (tmp_path / "signing.pem").write_text("not-a-real-key\n", encoding="utf-8")

    assert {path.name for path in sensitive_template_files(tmp_path)} == {".env", "signing.pem"}
    assert sensitive_template_files(ROOT / "docs" / "templates" / "typespec-contract") == ()
    assert sensitive_template_files(ROOT / "docs" / "templates" / "web" / "lit-activity") == ()


@pytest.mark.parametrize(
    "relative_manifest",
    (
        "docs/templates/web/lit-activity/public/backgrounds/manifest.json",
        "docs/templates/web/lit-activity/public/fonts/manifest.json",
    ),
)
def test_template_asset_manifests_match_shipped_bytes(relative_manifest: str) -> None:
    manifest_path = ROOT / relative_manifest
    payload = cast(
        Mapping[str, object],
        json.loads(manifest_path.read_text(encoding="utf-8")),
    )
    files = payload.get("files")
    assert isinstance(files, dict)
    typed_files = cast(dict[object, object], files)
    actual_files = {
        path.name
        for path in manifest_path.parent.iterdir()
        if path.is_file() and path != manifest_path
    }
    assert set(typed_files) == actual_files, f"{relative_manifest}: asset inventory mismatch"
    for name, expected in typed_files.items():
        assert isinstance(name, str)
        assert isinstance(expected, str)
        actual = f"sha256:{hashlib.sha256((manifest_path.parent / name).read_bytes()).hexdigest()}"
        assert actual == expected, f"{relative_manifest}: checksum mismatch for {name}"


def test_repository_docs_cover_template_maintenance_and_self_application() -> None:
    build = (ROOT / "docs" / "build.html").read_text(encoding="utf-8")
    architecture = (ROOT / "docs" / "architecture.html").read_text(encoding="utf-8")
    contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")

    for expected in (
        "docs/templates/typespec-contract",
        "docs/templates/web/lit-activity",
        "npm ci",
        "npm run dev",
        "npm run signoff",
        "uv run rack run --all",
        "uv run python -m build",
        "uv run twine check dist/*",
        "build_hooks/template_resources.py",
    ):
        assert expected in build
    assert "Self-Application" in architecture
    assert "new root contract family" in architecture
    assert "npm run signoff" in contributing


def run_command(command: tuple[str, ...], cwd: Path) -> None:
    result = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def npm_executable() -> str:
    executable = shutil.which("npm")
    assert executable is not None, "npm is required to validate shipped Node templates"
    return executable
