+++
type = "requirement"
id = "core-req-0002"
domain = "core"
status = "implemented"
title = "Test Suite Governance Audit Verifies Rack Manifests"
created = "2026-07-15"
issue_refs = ["wavenumber-eng/wn-dev-std#19", "wavenumber-eng/wn-dev-std#22", "wavenumber-eng/wn-rack#4"]
adr_refs = ["core-adr-0002"]
design_refs = ["docs/core/design/test-suite-governance-audit.html", "docs/design/audit-standard.html"]

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/test_governance.py"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_016_test_suite_governance.py::test_tests_scope_passes_when_rack_manifests_match_reality"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_016_test_suite_governance.py::test_tests_scope_fails_when_discovered_test_is_missing_from_manifest"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_016_test_suite_governance.py::test_tests_scope_fails_when_manifest_declares_missing_test_file"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_016_test_suite_governance.py::test_tests_scope_requires_signoff_stratum"
+++

# Test Suite Governance Audit Verifies Rack Manifests

When a repository opts into test-suite governance, `dev-std audit --scope tests`
must validate the configured Rack test roots against the committed test layout.
The audit must require a configured test root, require `rack.toml`, require each
declared Rack stratum to have a matching directory and `STRATUM.toml`, fail
discovered `test_*.py` files missing from `[[subtests]]`, fail declared subtest
files missing from disk, and require each configured signoff stratum to exist
with signoff coverage.

The first implementation may perform this validation inside dev-std. Once Rack
provides a native failing audit command, dev-std should replace the local
manifest comparison with Rack-owned validation or a direct Rack audit adapter.
