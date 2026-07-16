+++
type = "requirement"
id = "core-req-0002"
domain = "core"
status = "implemented"
title = "Test Suite Governance Audit Delegates To Rack"
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

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_016_test_suite_governance.py::test_tests_scope_requires_signoff_concern"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_016_test_suite_governance.py::test_tests_scope_fails_closed_when_rack_audit_surface_is_missing"
+++

# Test Suite Governance Audit Delegates To Rack

When a repository opts into test-suite governance, `dev-std audit --scope tests`
must require explicit configured Rack test roots and signoff strata, then
delegate Rack manifest/layout validation to Rack's native audit surface from
`wn-rack>=2026.7.16`.

Rack owns validation of `rack.toml`, declared strata, `STRATUM.toml`, discovered
`test_*.py` files, declared subtest files, duplicate manifest entries, and
signoff stratum existence. Dev-std owns the standards boundary around that
surface: configured test roots must be explicit and root-relative, Rack audit
failures must be mapped into normal dev-std audit output, missing Rack audit
support must fail closed with upgrade guidance, and configured signoff strata
must declare the `signoff` concern.
