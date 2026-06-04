from __future__ import annotations

import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from wn_dev_std.checks import REQUIRED_ROOT_FILES

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


def test_cpp_tooling_policy_is_documented_and_templated() -> None:
    cpp_doc = (ROOT / "docs" / "design" / "cpp-standard.html").read_text(encoding="utf-8")
    clang_format = (ROOT / "docs" / "templates" / "cpp" / ".clang-format").read_text(
        encoding="utf-8"
    )
    clang_tidy = (ROOT / "docs" / "templates" / "cpp" / ".clang-tidy").read_text(encoding="utf-8")
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
    assert "clang-analyzer-*" in clang_tidy
