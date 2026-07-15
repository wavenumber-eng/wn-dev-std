"""Test-strategy-document governance checks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class TestStrategyDocGovernanceReport:
    """Test-strategy-document governance check result."""

    passed: bool
    detail: str


TEST_STRATEGY_DOC_PATH = Path("docs/test-strategy.html")
REQUIRED_TOPIC_GROUPS = {
    "scope/architecture": ("scope", "strategy", "suite", "architecture", "workspace", "package"),
    "rack/signoff": ("rack", "strata", "stratum", "signoff"),
    "lanes/parity/surfaces": ("lane", "parity", "surface", "runtime", "python", "c++"),
    "fixtures/assets/oracles": ("fixture", "asset", "oracle", "case", "data"),
    "coverage/gaps/evidence": ("coverage", "evidence", "missing", "orphan", "manifest"),
}


def check_test_strategy_doc_policy(root: Path) -> TestStrategyDocGovernanceReport:
    """Check for a canonical package/workspace test strategy document."""
    resolved_root = root.resolve()
    path = resolved_root / TEST_STRATEGY_DOC_PATH
    if not path.exists():
        return TestStrategyDocGovernanceReport(
            False,
            "missing canonical test strategy doc: docs/test-strategy.html",
        )
    if not path.is_file():
        return TestStrategyDocGovernanceReport(
            False,
            "docs/test-strategy.html is not a file",
        )

    failures = _validate_html_test_strategy_doc(path)
    if failures:
        return TestStrategyDocGovernanceReport(
            False,
            f"{path.relative_to(resolved_root).as_posix()}: " + "; ".join(failures),
        )
    return TestStrategyDocGovernanceReport(
        True,
        f"{path.relative_to(resolved_root).as_posix()} passed test-strategy governance",
    )


def _validate_html_test_strategy_doc(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    failures: list[str] = []
    if not re.search(r"\bdata-doc=[\"']test-strategy[\"']", text):
        failures.append('missing data-doc="test-strategy"')
    status = _html_attr(text, "data-doc-status")
    if status != "accepted":
        failures.append('data-doc-status must be "accepted"')
    failures.extend(_missing_topic_failures(text))
    return failures


def _missing_topic_failures(text: str) -> list[str]:
    normalized = _visible_text(text).lower()
    failures: list[str] = []
    for topic, tokens in REQUIRED_TOPIC_GROUPS.items():
        if not any(token in normalized for token in tokens):
            failures.append(f"missing test strategy topic {topic}")
    return failures


def _visible_text(text: str) -> str:
    return re.sub(r"<[^>]+>", " ", text)


def _html_attr(text: str, name: str) -> str:
    match = re.search(rf"\b{re.escape(name)}=[\"']([^\"']+)[\"']", text)
    return match.group(1).strip().lower() if match else ""
