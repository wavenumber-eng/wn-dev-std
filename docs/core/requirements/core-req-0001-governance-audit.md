+++
type = "requirement"
id = "core-req-0001"
domain = "core"
status = "active"
title = "Governance Audits Report Missing Required Inventories"
created = "2026-07-02"
adr_refs = ["core-adr-0001"]
design_refs = ["docs/design/audit-standard.html", "docs/design/documentation-standard.html"]

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_006_doc_governance.py::test_docs_adr_audit_fails_when_no_adrs_exist"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_006_doc_governance.py::test_docs_requirement_audit_fails_when_no_requirements_exist"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_006_doc_governance.py::test_docs_domain_audit_fails_when_no_domain_registry_exists"
+++

# Governance Audits Report Missing Required Inventories

The ADR, requirement, and domain audit scopes must fail when their corresponding
inventory is absent. The design-doc audit scope must fail when no HTML design
documents exist. These failures keep missing governance surfaces visible during
repo setup and migration.
