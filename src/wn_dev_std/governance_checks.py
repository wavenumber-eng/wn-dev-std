"""Audit result assembly for documentation governance checks."""

from __future__ import annotations

from pathlib import Path

from wn_dev_std.checks_types import CheckResult
from wn_dev_std.doc_governance import (
    check_adr_policy,
    check_link_policy,
    check_requirement_policy,
    check_traceability_policy,
)
from wn_dev_std.domain_governance import check_domain_governance_policy
from wn_dev_std.surface_governance import check_surface_governance_policy


def governance_doc_checks(root: Path) -> list[CheckResult]:
    """Run durable governance-document checks."""
    adr_result = check_adr_policy(root)
    domain_result = check_domain_governance_policy(root)
    requirement_result = check_requirement_policy(root)
    surface_result = check_surface_governance_policy(root)
    traceability_result = check_traceability_policy(root)
    link_result = check_link_policy(root)
    return [
        CheckResult("docs.adrs", adr_result.passed, adr_result.detail, "docs.adrs"),
        CheckResult(
            "docs.domains",
            domain_result.passed,
            domain_result.detail,
            "docs.domains",
        ),
        CheckResult(
            "docs.requirements",
            requirement_result.passed,
            requirement_result.detail,
            "docs.requirements",
        ),
        CheckResult(
            "docs.surfaces",
            surface_result.passed,
            surface_result.detail,
            "docs.surfaces",
        ),
        CheckResult(
            "docs.traceability",
            traceability_result.passed,
            traceability_result.detail,
            "docs.traceability",
        ),
        CheckResult("docs.links", link_result.passed, link_result.detail, "docs.links"),
    ]
