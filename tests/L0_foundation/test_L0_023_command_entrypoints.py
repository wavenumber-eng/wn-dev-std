from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from test_L0_002_public_interfaces import write_file, write_minimal_csharp_project

from wn_dev_std.checks import run_audit_checks, run_basic_checks


def test_csharp_profile_reports_missing_default_build_once(tmp_path: Path) -> None:
    write_minimal_csharp_project(tmp_path)
    (tmp_path / "build.ps1").unlink()

    result_sets = (
        run_basic_checks(tmp_path),
        run_audit_checks(tmp_path, ("repo",)),
        run_audit_checks(tmp_path, ("language",)),
    )
    for results in result_sets:
        failures = [result for result in results if not result.passed]
        assert len(failures) == 1
        assert failures[0].name == "command entrypoints"
        assert failures[0].detail == "commands.build path 'build.ps1' does not exist"


def test_csharp_profile_accepts_configured_command_entrypoints(tmp_path: Path) -> None:
    write_minimal_csharp_project(tmp_path)
    (tmp_path / "build.ps1").unlink()
    write_file(tmp_path / "scripts" / "build" / "build.ps1", "placeholder\n")
    write_file(tmp_path / "scripts" / "test" / "test.ps1", "placeholder\n")
    write_file(tmp_path / "scripts" / "signoff.ps1", "placeholder\n")
    append_config(
        tmp_path,
        """
        [commands]
        build = "scripts/build/build.ps1"
        test = "scripts/test/test.ps1"
        signoff = "scripts/signoff.ps1"
        """,
    )

    results = run_basic_checks(tmp_path)
    command_check = next(result for result in results if result.name == "command entrypoints")

    assert command_check.passed
    assert "build=scripts/build/build.ps1" in command_check.detail
    assert "test=scripts/test/test.ps1" in command_check.detail
    assert "signoff=scripts/signoff.ps1" in command_check.detail
    assert all(result.passed for result in results), [result.to_dict() for result in results]


def test_csharp_profile_reports_missing_configured_build_once(tmp_path: Path) -> None:
    write_minimal_csharp_project(tmp_path)
    (tmp_path / "build.ps1").unlink()
    append_config(
        tmp_path,
        """
        [commands]
        build = "scripts/build/build.ps1"
        """,
    )

    failures = [result for result in run_basic_checks(tmp_path) if not result.passed]

    assert len(failures) == 1
    assert failures[0].name == "command entrypoints"
    assert failures[0].detail == ("commands.build path 'scripts/build/build.ps1' does not exist")


def test_command_entrypoints_reject_absolute_and_parent_traversal_paths(tmp_path: Path) -> None:
    invalid_paths = ("/outside/build.ps1", "../build.ps1", "scripts/../build.ps1")
    for index, configured_path in enumerate(invalid_paths):
        root = tmp_path / str(index)
        write_minimal_csharp_project(root)
        append_config(
            root,
            f"""
            [commands]
            build = "{configured_path}"
            """,
        )

        failures = [result for result in run_basic_checks(root) if not result.passed]

        assert len(failures) == 1
        assert failures[0].name == "command entrypoints"
        assert "relative" in failures[0].detail


def test_command_entrypoints_reject_directory_target(tmp_path: Path) -> None:
    write_minimal_csharp_project(tmp_path)
    (tmp_path / "scripts" / "build").mkdir(parents=True)
    append_config(
        tmp_path,
        """
        [commands]
        build = "scripts/build"
        """,
    )

    failures = [result for result in run_basic_checks(tmp_path) if not result.passed]

    assert len(failures) == 1
    assert failures[0].name == "command entrypoints"
    assert failures[0].detail == "commands.build path 'scripts/build' is not a file"


def test_command_override_does_not_disable_required_root_files(tmp_path: Path) -> None:
    write_minimal_csharp_project(tmp_path)
    (tmp_path / "build.ps1").unlink()
    (tmp_path / "README.md").unlink()
    write_file(tmp_path / "scripts" / "build" / "build.ps1", "placeholder\n")
    append_config(
        tmp_path,
        """
        [commands]
        build = "scripts/build/build.ps1"
        """,
    )

    results = run_basic_checks(tmp_path)
    command_check = next(result for result in results if result.name == "command entrypoints")
    root_files = next(result for result in results if result.name == "root files")

    assert command_check.passed
    assert not root_files.passed
    assert root_files.detail == "missing README.md"


def append_config(root: Path, text: str) -> None:
    config_path = root / "wn-dev-std.toml"
    write_file(
        config_path,
        config_path.read_text(encoding="utf-8") + "\n" + dedent(text).lstrip(),
    )
