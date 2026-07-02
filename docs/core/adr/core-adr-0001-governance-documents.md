+++
type = "adr"
id = "core-adr-0001"
domain = "core"
status = "accepted"
title = "Governance Documents Are Audited Contracts"
created = "2026-07-02"
design_refs = ["docs/design/documentation-standard.html", "docs/design/audit-standard.html"]

[[verification_refs]]
kind = "local_pytest"
target = "tests/L99_signoff/test_L99_004_repo_hygiene.py::test_adr_requirement_traceability_policy_is_documented_and_clean"
+++

# Governance Documents Are Audited Contracts

ADR, requirement, domain, traceability, and generated governance documents are
treated as auditable contract surfaces. Empty governance inventories are a
failure signal when the corresponding audit scope is enabled, because a passing
empty scan hides missing documentation rather than proving compliance.

The durable source format for ADRs and requirements is Markdown with TOML front
matter. Generated HTML is a review and navigation artifact.
