+++
type = "requirement"
id = "core-req-0003"
domain = "core"
status = "implemented"
title = "Audit Requires Canonical Test Strategy Documentation"
created = "2026-07-15"
issue_refs = ["wavenumber-eng/wn-dev-std#19"]
adr_refs = ["core-adr-0003"]
design_refs = ["docs/core/design/test-strategy-doc-audit.html", "docs/design/audit-standard.html", "docs/test-strategy.html"]

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/test_strategy_doc_governance.py"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_017_test_strategy_doc_governance.py::test_docs_test_strategy_fails_missing_canonical_doc"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_017_test_strategy_doc_governance.py::test_docs_test_strategy_passes_html_strategy_doc"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_017_test_strategy_doc_governance.py::test_docs_test_strategy_fails_missing_required_topic"
+++

# Audit Requires Canonical Test Strategy Documentation

The audit must expose a `docs.test_strategy` scope that requires
`docs/test-strategy.html`. The document must declare
`data-doc="test-strategy"` and `data-doc-status="accepted"`, and it must cover
the high-level package or workspace test scope, Rack/signoff structure, lanes or
parity expectations, fixtures/assets/oracles, and coverage evidence or known
gaps.

This requirement complements Rack manifest governance. It does not replace
`tests/rack.toml` or `STRATUM.toml`; it makes the overall testing model
reviewable when the supporting code, generated data, oracle tooling, or parity
matrix is too complex to understand from Rack metadata alone.
