+++
type = "adr"
id = "core-adr-0003"
domain = "core"
status = "accepted"
title = "Test Strategy Documents Are Audited"
created = "2026-07-15"
issue_refs = ["wavenumber-eng/wn-dev-std#19"]
requirement_refs = ["core-req-0003"]
design_refs = ["docs/core/design/test-strategy-doc-audit.html", "docs/design/audit-standard.html", "docs/test-strategy.html"]

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/test_strategy_doc_governance.py"
+++

# Test Strategy Documents Are Audited

Dev-std requires a high-level test strategy document in addition to Rack
manifests. Rack records executable strata and subtests, but complex repositories
also need a human-readable map of the suite architecture: execution lanes,
runtime parity expectations, governed surfaces, fixtures, assets, oracle tools,
coverage evidence, and known missing or orphaned material.

The canonical package or workspace document is `docs/test-strategy.html`.
`dev-std audit --scope docs.test_strategy` validates that the document exists,
is accepted, and covers the minimum strategy topics reviewers need before they
inspect Rack manifests, generated evidence, or project-specific test tooling.
