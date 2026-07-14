"""Audit result assembly for documentation governance checks."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from wn_dev_std.artifact_governance import (
    check_artifact_governance_policy,
    check_release_governance_policy,
    check_vendor_governance_policy,
)
from wn_dev_std.audit_config import scope_is_selected
from wn_dev_std.build_doc_governance import check_build_doc_policy
from wn_dev_std.checks_types import CheckResult
from wn_dev_std.doc_governance import (
    check_adr_policy,
    check_link_policy,
    check_requirement_policy,
    check_traceability_policy,
)
from wn_dev_std.domain_governance import check_domain_governance_policy
from wn_dev_std.surface_governance import check_surface_governance_policy


class _GovernanceReport(Protocol):
    @property
    def passed(self) -> bool:
        """Return whether the governance check passed."""
        ...

    @property
    def detail(self) -> str:
        """Return the governance check detail."""
        ...


@dataclass(frozen=True, slots=True)
class GovernanceCheck:
    """Lazy governance check descriptor."""

    name: str
    scope: str
    runner: Callable[[Path], _GovernanceReport]


GOVERNANCE_CHECKS = (
    GovernanceCheck("docs.adrs", "docs.adrs", check_adr_policy),
    GovernanceCheck("docs.artifacts", "docs.artifacts", check_artifact_governance_policy),
    GovernanceCheck("docs.build", "docs.build", check_build_doc_policy),
    GovernanceCheck("docs.domains", "docs.domains", check_domain_governance_policy),
    GovernanceCheck("docs.release", "docs.release", check_release_governance_policy),
    GovernanceCheck("docs.requirements", "docs.requirements", check_requirement_policy),
    GovernanceCheck("docs.surfaces", "docs.surfaces", check_surface_governance_policy),
    GovernanceCheck("docs.traceability", "docs.traceability", check_traceability_policy),
    GovernanceCheck("docs.vendors", "docs.vendors", check_vendor_governance_policy),
    GovernanceCheck("docs.links", "docs.links", check_link_policy),
)


def governance_doc_checks(root: Path, scopes: Sequence[str] = ("all",)) -> list[CheckResult]:
    """Run durable governance-document checks."""
    results: list[CheckResult] = []
    for check in GOVERNANCE_CHECKS:
        if not scope_is_selected(check.scope, scopes):
            continue
        report = check.runner(root)
        results.append(CheckResult(check.name, report.passed, report.detail, check.scope))
    return results
