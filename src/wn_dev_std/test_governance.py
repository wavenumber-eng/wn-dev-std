"""Rack test-suite governance checks."""

from __future__ import annotations

import re
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast


@dataclass(frozen=True, slots=True)
class TestSuiteGovernanceReport:
    """Test-suite governance check result."""

    passed: bool
    detail: str


DEFAULT_SIGNOFF_STRATA = ("L99_signoff",)
IGNORED_TEST_DIR_NAMES = {"__pycache__", "rack_results"}
STRATUM_DIR_PATTERN = re.compile(r"^L\d+")


def has_test_governance_config(config: Mapping[str, object] | None) -> bool:
    """Return whether the project opted into strict test-suite governance."""
    return _tests_config(config) is not None


def check_test_suite_governance(
    root: Path,
    config: Mapping[str, object] | None,
) -> TestSuiteGovernanceReport:
    """Validate configured Rack test roots against real test files."""
    test_config = _tests_config(config)
    if test_config is None:
        return TestSuiteGovernanceReport(
            False,
            'missing [tests] config with roots = ["tests"]',
        )

    configured_roots = _string_list(test_config, "roots")
    configured_signoff_strata = _string_list(
        test_config,
        "signoff_strata",
        default=DEFAULT_SIGNOFF_STRATA,
    )
    failures: list[str] = []
    if not configured_roots:
        failures.append("[tests].roots must list at least one test root")
    if not configured_signoff_strata:
        failures.append("[tests].signoff_strata must list at least one signoff stratum")

    roots = _valid_relative_paths(configured_roots, "[tests].roots", failures)
    for test_root_relative in roots:
        _validate_test_root(
            root,
            test_root_relative,
            configured_signoff_strata,
            failures,
        )

    if failures:
        return TestSuiteGovernanceReport(False, "; ".join(failures))
    joined_roots = ", ".join(path.as_posix() for path in roots)
    return TestSuiteGovernanceReport(
        True,
        f"Rack test manifests match discovered tests under {joined_roots}",
    )


def _tests_config(config: Mapping[str, object] | None) -> Mapping[str, object] | None:
    if config is None:
        return None
    tests_raw = config.get("tests")
    if not isinstance(tests_raw, dict):
        return None
    return cast(Mapping[str, object], tests_raw)


def _string_list(
    config: Mapping[str, object],
    key: str,
    *,
    default: Sequence[str] = (),
) -> tuple[str, ...]:
    value = config.get(key)
    if value is None:
        return tuple(default)
    if not isinstance(value, list):
        return ()
    items: list[str] = []
    for item in cast(list[object], value):
        if isinstance(item, str) and item.strip():
            items.append(item.strip())
    return tuple(items)


def _valid_relative_paths(
    values: Sequence[str],
    label: str,
    failures: list[str],
) -> tuple[Path, ...]:
    paths: list[Path] = []
    for value in values:
        path = Path(value)
        if path.is_absolute() or ".." in path.parts:
            failures.append(f"{label} entry {value!r} must be a relative path inside the root")
            continue
        paths.append(path)
    return tuple(paths)


def _validate_test_root(
    root: Path,
    test_root_relative: Path,
    signoff_strata: Sequence[str],
    failures: list[str],
) -> None:
    test_root = root / test_root_relative
    test_root_label = test_root_relative.as_posix()
    rack_config = _test_root_rack_config(test_root, test_root_label, failures)
    if rack_config is None:
        return

    strata = _rack_strata_order(rack_config)
    if not strata:
        failures.append(f"{test_root_label}/rack.toml must declare [strata].order")
        return
    _validate_unique_values(strata, f"{test_root_label}/rack.toml [strata].order", failures)
    stratum_subtest_counts = _validate_declared_strata(test_root, test_root_label, strata, failures)
    _validate_signoff_strata(
        test_root, test_root_label, signoff_strata, strata, stratum_subtest_counts, failures
    )


def _test_root_rack_config(
    test_root: Path,
    test_root_label: str,
    failures: list[str],
) -> Mapping[str, object] | None:
    if not test_root.exists():
        failures.append(f"{test_root_label} does not exist")
        return None
    if not test_root.is_dir():
        failures.append(f"{test_root_label} is not a directory")
        return None

    rack_path = test_root / "rack.toml"
    if not rack_path.exists():
        failures.append(f"{test_root_label}/rack.toml is required")
        return None
    return _load_toml(rack_path, failures)


def _validate_declared_strata(
    test_root: Path,
    test_root_label: str,
    strata: tuple[str, ...],
    failures: list[str],
) -> dict[str, int]:
    declared_strata = set(strata)
    for extra in _extra_stratum_dirs(test_root, declared_strata):
        failures.append(
            f"{test_root_label}/{extra.name} looks like a stratum but is missing from rack.toml"
        )

    stratum_subtest_counts: dict[str, int] = {}
    for stratum in strata:
        stratum_subtest_counts[stratum] = _validate_stratum(
            test_root,
            test_root_label,
            stratum,
            failures,
        )
    return stratum_subtest_counts


def _validate_signoff_strata(
    test_root: Path,
    test_root_label: str,
    signoff_strata: Sequence[str],
    strata: tuple[str, ...],
    stratum_subtest_counts: Mapping[str, int],
    failures: list[str],
) -> None:
    declared_strata = set(strata)
    for signoff_stratum in signoff_strata:
        if signoff_stratum not in declared_strata:
            failures.append(
                f"{test_root_label}/rack.toml missing signoff stratum {signoff_stratum}"
            )
            continue
        if stratum_subtest_counts.get(signoff_stratum, 0) < 1:
            failures.append(f"{test_root_label}/{signoff_stratum} must declare signoff subtests")
        _validate_signoff_concern(test_root, test_root_label, signoff_stratum, failures)


def _load_toml(path: Path, failures: list[str]) -> Mapping[str, object] | None:
    try:
        with path.open("rb") as handle:
            return cast(Mapping[str, object], tomllib.load(handle))
    except tomllib.TOMLDecodeError as exc:
        failures.append(f"{path.as_posix()} is invalid TOML: {exc}")
    return None


def _rack_strata_order(rack_config: Mapping[str, object]) -> tuple[str, ...]:
    strata_raw = rack_config.get("strata")
    if not isinstance(strata_raw, dict):
        return ()
    strata = cast(Mapping[str, object], strata_raw)
    order_raw = strata.get("order")
    if not isinstance(order_raw, list):
        return ()
    return tuple(item for item in cast(list[object], order_raw) if isinstance(item, str) and item)


def _validate_unique_values(values: Sequence[str], label: str, failures: list[str]) -> None:
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in values:
        if value in seen:
            duplicates.append(value)
        seen.add(value)
    if duplicates:
        failures.append(f"{label} has duplicate entries: {', '.join(sorted(set(duplicates)))}")


def _extra_stratum_dirs(test_root: Path, declared_strata: set[str]) -> tuple[Path, ...]:
    extras: list[Path] = []
    for child in sorted(test_root.iterdir()):
        if not child.is_dir() or child.name in IGNORED_TEST_DIR_NAMES:
            continue
        if child.name in declared_strata:
            continue
        if STRATUM_DIR_PATTERN.match(child.name) or (child / "STRATUM.toml").exists():
            extras.append(child)
    return tuple(extras)


def _validate_stratum(
    test_root: Path,
    test_root_label: str,
    stratum: str,
    failures: list[str],
) -> int:
    stratum_dir = test_root / stratum
    stratum_label = f"{test_root_label}/{stratum}"
    if not stratum_dir.exists():
        failures.append(f"{stratum_label} directory is missing")
        return 0
    if not stratum_dir.is_dir():
        failures.append(f"{stratum_label} is not a directory")
        return 0

    stratum_path = stratum_dir / "STRATUM.toml"
    if not stratum_path.exists():
        failures.append(f"{stratum_label}/STRATUM.toml is required")
        return 0
    stratum_config = _load_toml(stratum_path, failures)
    if stratum_config is None:
        return 0

    manifest_files = _manifest_subtest_files(stratum_config, stratum_label, failures)
    discovered_files = tuple(path.name for path in sorted(stratum_dir.glob("test_*.py")))
    _validate_unique_values(manifest_files, f"{stratum_label} [[subtests]].file", failures)

    manifest_set = set(manifest_files)
    discovered_set = set(discovered_files)
    missing_from_manifest = sorted(discovered_set - manifest_set)
    missing_from_disk = sorted(manifest_set - discovered_set)
    if missing_from_manifest:
        failures.append(
            f"{stratum_label}/STRATUM.toml missing discovered test files: "
            + ", ".join(missing_from_manifest)
        )
    if missing_from_disk:
        failures.append(
            f"{stratum_label}/STRATUM.toml declares missing test files: "
            + ", ".join(missing_from_disk)
        )
    return len(manifest_files)


def _manifest_subtest_files(
    stratum_config: Mapping[str, object],
    stratum_label: str,
    failures: list[str],
) -> tuple[str, ...]:
    subtests_raw = stratum_config.get("subtests")
    if not isinstance(subtests_raw, list):
        failures.append(f"{stratum_label}/STRATUM.toml must declare [[subtests]]")
        return ()
    files: list[str] = []
    ids: list[str] = []
    for index, item in enumerate(cast(list[object], subtests_raw), start=1):
        if not isinstance(item, dict):
            failures.append(f"{stratum_label}/STRATUM.toml subtest {index} must be a table")
            continue
        subtest = cast(Mapping[str, object], item)
        file_value = subtest.get("file")
        id_value = subtest.get("id")
        if isinstance(id_value, str) and id_value.strip():
            ids.append(id_value.strip())
        else:
            failures.append(f"{stratum_label}/STRATUM.toml subtest {index} missing id")
        if isinstance(file_value, str) and file_value.strip():
            files.append(file_value.strip())
        else:
            failures.append(f"{stratum_label}/STRATUM.toml subtest {index} missing file")
    _validate_unique_values(ids, f"{stratum_label} [[subtests]].id", failures)
    return tuple(files)


def _validate_signoff_concern(
    test_root: Path,
    test_root_label: str,
    signoff_stratum: str,
    failures: list[str],
) -> None:
    stratum_path = test_root / signoff_stratum / "STRATUM.toml"
    if not stratum_path.exists():
        return
    stratum_config = _load_toml(stratum_path, failures)
    if stratum_config is None:
        return
    concerns_raw = stratum_config.get("concerns")
    concerns: set[str] = (
        {item for item in cast(list[object], concerns_raw) if isinstance(item, str)}
        if isinstance(concerns_raw, list)
        else set()
    )
    if "signoff" not in concerns:
        failures.append(f"{test_root_label}/{signoff_stratum} must declare signoff concern")
