from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from config_fixtures import standard_config

from wn_dev_std.checks import run_audit_checks
from wn_dev_std.checks_types import CheckResult


def test_tests_scope_passes_when_rack_manifests_match_reality(tmp_path: Path) -> None:
    write_valid_test_governance_repo(tmp_path)

    result = tests_result(tmp_path)

    assert result.passed
    assert "Rack test manifests match discovered tests" in result.detail


def test_tests_scope_requires_dev_std_test_config(tmp_path: Path) -> None:
    write_file(tmp_path / "dev-std.toml", standard_config())

    result = tests_result(tmp_path)

    assert not result.passed
    assert "missing [tests] config" in result.detail


def test_tests_scope_fails_when_discovered_test_is_missing_from_manifest(
    tmp_path: Path,
) -> None:
    write_valid_test_governance_repo(tmp_path)
    write_file(
        tmp_path / "tests" / "L0_foundation" / "test_L0_002_extra.py",
        "def test_x():\n    pass\n",
    )

    result = tests_result(tmp_path)

    assert not result.passed
    assert "missing discovered test files: test_L0_002_extra.py" in result.detail


def test_tests_scope_fails_when_manifest_declares_missing_test_file(tmp_path: Path) -> None:
    write_valid_test_governance_repo(tmp_path)
    (tmp_path / "tests" / "L0_foundation" / "test_L0_001_demo.py").unlink()

    result = tests_result(tmp_path)

    assert not result.passed
    assert "declares missing test files: test_L0_001_demo.py" in result.detail


def test_tests_scope_requires_signoff_stratum(tmp_path: Path) -> None:
    write_valid_test_governance_repo(tmp_path)
    write_file(
        tmp_path / "tests" / "rack.toml",
        dedent(
            """
            [rack]
            name = "Demo"

            [strata]
            order = ["L0_foundation"]
            """
        ).lstrip(),
    )

    result = tests_result(tmp_path)

    assert not result.passed
    assert "missing signoff stratum L99_signoff" in result.detail


def write_valid_test_governance_repo(root: Path) -> None:
    write_file(
        root / "dev-std.toml",
        standard_config(
            extra="""
            [tests]
            roots = ["tests"]
            signoff_strata = ["L99_signoff"]
            """,
        ),
    )
    write_file(
        root / "tests" / "rack.toml",
        dedent(
            """
            [rack]
            name = "Demo"

            [strata]
            order = ["L0_foundation", "L99_signoff"]
            """
        ).lstrip(),
    )
    write_stratum(root, "L0_foundation", "L0_001", "test_L0_001_demo.py", ["contracts"])
    write_stratum(root, "L99_signoff", "L99_001", "test_L99_001_signoff.py", ["signoff"])
    write_file(
        root / "tests" / "L0_foundation" / "test_L0_001_demo.py",
        "def test_demo():\n    pass\n",
    )
    write_file(
        root / "tests" / "L99_signoff" / "test_L99_001_signoff.py",
        "def test_signoff():\n    pass\n",
    )


def write_stratum(
    root: Path,
    stratum: str,
    subtest_id: str,
    file_name: str,
    concerns: list[str],
) -> None:
    quoted_concerns = ", ".join(repr(concern).replace("'", '"') for concern in concerns)
    write_file(
        root / "tests" / stratum / "STRATUM.toml",
        dedent(
            f"""
            name = "{stratum}"
            order = 0
            description = "Demo stratum"
            enabled = true
            concerns = [{quoted_concerns}]

            [[subtests]]
            id = "{subtest_id}"
            file = "{file_name}"
            name = "Demo"
            description = "Demo"
            concerns = [{quoted_concerns}]
            """
        ).lstrip(),
    )


def tests_result(root: Path) -> CheckResult:
    return next(
        result
        for result in run_audit_checks(root, ("tests",))
        if result.name == "test suite governance"
    )


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
