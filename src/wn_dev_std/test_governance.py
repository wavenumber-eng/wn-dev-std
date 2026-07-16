"""Rack test-suite governance checks."""

from __future__ import annotations

import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Protocol, cast


@dataclass(frozen=True, slots=True)
class TestSuiteGovernanceReport:
    """Test-suite governance check result."""

    passed: bool
    detail: str


class _RackAuditFailure(Protocol):
    code: str
    message: str
    path: str | None


class _RackAuditReport(Protocol):
    passed: bool
    failures: Sequence[_RackAuditFailure]


class _RackAuditSuite(Protocol):
    def __call__(
        self,
        root: Path,
        *,
        strict: bool,
        signoff_strata: Sequence[str],
        target_stratum: str | None = None,
    ) -> _RackAuditReport: ...


DEFAULT_SIGNOFF_STRATA = ("L99_signoff",)
RACK_AUDIT_MIN_VERSION = "2026.7.16"


def has_test_governance_config(config: Mapping[str, object] | None) -> bool:
    """Return whether the project opted into strict test-suite governance."""
    return _tests_config(config) is not None


def check_test_suite_governance(
    root: Path,
    config: Mapping[str, object] | None,
) -> TestSuiteGovernanceReport:
    """Validate configured Rack test roots through Rack native audit."""
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
    rack_audit_suite = _load_rack_audit_suite(failures)
    if rack_audit_suite is not None:
        for test_root_relative in roots:
            _audit_test_root(
                root,
                test_root_relative,
                configured_signoff_strata,
                rack_audit_suite,
                failures,
            )

    if failures:
        return TestSuiteGovernanceReport(False, "; ".join(failures))
    joined_roots = ", ".join(path.as_posix() for path in roots)
    return TestSuiteGovernanceReport(
        True,
        f"Rack native audit passed for configured test roots under {joined_roots}",
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


def _load_rack_audit_suite(failures: list[str]) -> _RackAuditSuite | None:
    try:
        rack_module = import_module("rack")
    except ImportError as exc:
        failures.append(f"wn-rack>={RACK_AUDIT_MIN_VERSION} is required for tests audit: {exc}")
        return None

    audit_suite = getattr(rack_module, "audit_suite", None)
    if not callable(audit_suite):
        failures.append(
            f"wn-rack>={RACK_AUDIT_MIN_VERSION} is required for tests audit; "
            "installed rack package does not expose rack.audit_suite"
        )
        return None
    return cast(_RackAuditSuite, audit_suite)


def _audit_test_root(
    root: Path,
    test_root_relative: Path,
    signoff_strata: Sequence[str],
    audit_suite: _RackAuditSuite,
    failures: list[str],
) -> None:
    test_root = root / test_root_relative
    test_root_label = test_root_relative.as_posix()
    try:
        report = audit_suite(
            test_root,
            strict=False,
            signoff_strata=signoff_strata,
            target_stratum=None,
        )
    except Exception as exc:
        failures.append(f"{test_root_label}: Rack native audit failed to run: {exc}")
        return

    if report.passed:
        _validate_signoff_concerns(test_root, test_root_label, signoff_strata, failures)
        return
    for failure in report.failures:
        failures.append(_format_rack_failure(test_root_label, failure))


def _format_rack_failure(test_root_label: str, failure: _RackAuditFailure) -> str:
    path = failure.path
    location = f"{test_root_label}/{path}" if path else test_root_label
    return f"{location}: [{failure.code}] {failure.message}"


def _validate_signoff_concerns(
    test_root: Path,
    test_root_label: str,
    signoff_strata: Sequence[str],
    failures: list[str],
) -> None:
    for signoff_stratum in signoff_strata:
        stratum_path = test_root / signoff_stratum / "STRATUM.toml"
        if not stratum_path.exists():
            continue
        try:
            with stratum_path.open("rb") as handle:
                stratum_config = cast(Mapping[str, object], tomllib.load(handle))
        except tomllib.TOMLDecodeError:
            continue
        concerns_raw = stratum_config.get("concerns")
        concerns: set[str] = (
            {item for item in cast(list[object], concerns_raw) if isinstance(item, str)}
            if isinstance(concerns_raw, list)
            else set()
        )
        if "signoff" not in concerns:
            failures.append(
                f"{test_root_label}/{signoff_stratum}/STRATUM.toml: "
                f"[missing_signoff_concern] {signoff_stratum} must declare signoff concern"
            )
