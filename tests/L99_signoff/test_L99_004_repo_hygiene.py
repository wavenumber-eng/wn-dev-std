from __future__ import annotations

import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from wn_dev_std.checks import REQUIRED_ROOT_FILES, run_basic_checks

ROOT = Path(__file__).resolve().parents[2]


def test_required_open_source_hygiene_files_exist() -> None:
    for relative_path in REQUIRED_ROOT_FILES:
        assert (ROOT / relative_path).exists(), relative_path
    assert (ROOT / "SECURITY.md").exists()
    assert (ROOT / "CODE_OF_CONDUCT.md").exists()


def test_secret_and_local_result_paths_are_ignored() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in (".env", ".venv/", "dist/", "rack_results/"):
        assert pattern in gitignore
    assert not (ROOT / ".env").exists()


def test_sdist_excludes_temporary_plans_and_research() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        pyproject = cast(Mapping[str, object], tomllib.load(handle))
    tool = cast(Mapping[str, object], pyproject["tool"])
    hatch = cast(Mapping[str, object], tool["hatch"])
    build = cast(Mapping[str, object], hatch["build"])
    targets = cast(Mapping[str, object], build["targets"])
    sdist = cast(Mapping[str, object], targets["sdist"])
    exclude = cast(Sequence[str], sdist["exclude"])
    assert "docs/plans/**" in exclude
    assert "docs/research/**" in exclude


def test_binary_distribution_policy_is_documented() -> None:
    setup_doc = (ROOT / "docs" / "setup.html").read_text(encoding="utf-8")
    mixed_mode_doc = (ROOT / "docs" / "design" / "mixed-mode.html").read_text(encoding="utf-8")
    assert "dist/native/windows-x64/" in setup_doc
    assert "dist/wasm/browser/" in setup_doc
    assert "dist/native/windows-x64/" in mixed_mode_doc
    assert "dist/wasm/browser/" in mixed_mode_doc
    assert "installed-wheel validation" in mixed_mode_doc


def test_rack_and_signoff_quality_model_is_documented() -> None:
    architecture = (ROOT / "docs" / "architecture.html").read_text(encoding="utf-8")
    for expected in (
        "Quality Model",
        "Rack answers",
        "Signoff answers",
        "Every project needs a signoff gate",
        "L99_signoff",
        "complexity, file",
        r"C:\ELI\prj\wavenumber-eng\wn-dev-std\tests",
        "fast edit-loop check",
        "release-facing gate",
        "baselines can make existing debt visible",
    ):
        assert expected in architecture


def test_readme_documents_public_rack_package_and_project_model() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for expected in (
        "https://pypi.org/project/wn-rack/",
        "uv add --dev wn-rack",
        "All Wavenumber projects should use the Rack model",
        "Non-Python projects should still follow the same model",
        "Every project needs a signoff gate",
        "L99_signoff",
        "complexity, file size, function size",
        r"C:\ELI\prj\wavenumber-eng\wn-dev-std\tests",
        "tests/rack.toml",
    ):
        assert expected in readme


def test_cpp_tooling_policy_is_documented_and_templated() -> None:
    cpp_doc = (ROOT / "docs" / "design" / "cpp-standard.html").read_text(encoding="utf-8")
    clang_format = (ROOT / "docs" / "templates" / "cpp" / ".clang-format").read_text(
        encoding="utf-8"
    )
    clang_tidy = (ROOT / "docs" / "templates" / "cpp" / ".clang-tidy").read_text(encoding="utf-8")
    signoff = (ROOT / "docs" / "templates" / "cpp" / "signoff.toml").read_text(encoding="utf-8")
    for expected in (
        "BasedOnStyle: LLVM",
        "BreakBeforeBraces: Allman",
        "IndentWidth: 4",
        "ColumnLimit: 100",
        "PointerAlignment: Left",
        "SortIncludes: true",
        "IncludeBlocks: Preserve",
    ):
        assert expected in cpp_doc
        assert expected in clang_format
    assert "CMAKE_EXPORT_COMPILE_COMMANDS=ON" in cpp_doc
    assert "max_cyclomatic_complexity = 10" in cpp_doc
    assert "max_cyclomatic_complexity = 10" in signoff
    assert 'lizard = "fail"' in signoff
    assert "clang-analyzer-*" in clang_tidy
    assert "google-runtime-int" in clang_tidy


def test_zephyr_policy_is_documented_and_templated() -> None:
    zephyr_doc = (ROOT / "docs" / "design" / "zephyr-standard.html").read_text(encoding="utf-8")
    clang_format = (ROOT / "docs" / "templates" / "zephyr" / ".clang-format").read_text(
        encoding="utf-8"
    )
    signoff = (ROOT / "docs" / "templates" / "zephyr" / "signoff.toml").read_text(encoding="utf-8")
    for expected in (
        "zephyr-firmware",
        "CMAKE_EXPORT_COMPILE_COMMANDS=ON",
        "max_cyclomatic_complexity = 10",
        "Xtensa",
    ):
        assert expected in zephyr_doc
    assert "BreakBeforeBraces: Attach" in clang_format
    assert "SortIncludes: Never" in clang_format
    assert 'profile = "zephyr-firmware"' in signoff
    assert "max_cyclomatic_complexity = 10" in signoff


def test_javascript_web_policy_is_documented() -> None:
    web_doc = (ROOT / "docs" / "design" / "javascript-standard.html").read_text(encoding="utf-8")
    for expected in (
        "jsconfig.json",
        "// @ts-check",
        "JSDoc",
        "node:test",
        "node --test",
        "CSS custom properties",
        "Web Components",
        "wn-*",
        "Wasmer",
        "Wasmtime",
        "install",
        "update",
        "build",
        "test",
        "signoff",
    ):
        assert expected in web_doc


def test_compatibility_pruning_policy_is_documented() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    python_doc = (ROOT / "docs" / "design" / "python-standard.html").read_text(encoding="utf-8")
    for text in (readme, python_doc):
        assert "compatibility_pruning" in text
        assert "forbidden_patterns" in text
        assert "excluded_parts" in text


def test_public_pr_hygiene_policy_is_documented_and_installed() -> None:
    workflow_template = (ROOT / "docs" / "templates" / "github" / "pr-hygiene.yml").read_text(
        encoding="utf-8"
    )
    workflow = (ROOT / ".github" / "workflows" / "pr-hygiene.yml").read_text(encoding="utf-8")
    pr_template = (ROOT / ".github" / "pull_request_template.md").read_text(encoding="utf-8")
    pr_template_source = (
        ROOT / "docs" / "templates" / "github" / "pull_request_template.md"
    ).read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    python_doc = (ROOT / "docs" / "design" / "python-standard.html").read_text(encoding="utf-8")

    assert workflow == workflow_template
    assert pr_template == pr_template_source
    for text in (workflow, readme, python_doc):
        assert "Linked issue:" in text
        assert "Conventional Commit" in text
        assert "Claude" in text or ("AI-vendor" in text and "attribution" in text)

    hygiene_check = next(
        result for result in run_basic_checks(ROOT) if result.name == "public PR hygiene"
    )
    assert hygiene_check.passed


def test_design_doc_status_policy_is_documented_and_clean() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    standard_doc = (ROOT / "docs" / "design" / "documentation-standard.html").read_text(
        encoding="utf-8"
    )
    for text in (readme, standard_doc):
        assert "data-doc-status" in text
        assert "draft" in text
        assert "proposal" in text
        assert "accepted" in text
        assert "superseded" in text

    status_check = next(
        result for result in run_basic_checks(ROOT) if result.name == "design doc status"
    )
    assert status_check.passed
    assert "draft/proposal docs" not in status_check.detail
