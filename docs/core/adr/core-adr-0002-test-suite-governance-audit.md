+++
type = "adr"
id = "core-adr-0002"
domain = "core"
status = "accepted"
title = "Dev Std Delegates Rack Test Manifest Audit To Rack"
created = "2026-07-15"
issue_refs = ["wavenumber-eng/wn-dev-std#19", "wavenumber-eng/wn-dev-std#22", "wavenumber-eng/wn-rack#4"]
requirement_refs = ["core-req-0002"]
design_refs = ["docs/core/design/test-suite-governance-audit.html", "docs/design/audit-standard.html"]

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/test_governance.py"
+++

# Dev Std Delegates Rack Test Manifest Audit To Rack

`dev-std audit --scope tests` delegates Rack manifest/layout validation to
Rack's native audit surface from `wn-rack>=2026.7.16`. Dev-std still owns the
standard-facing policy wrapper: repositories must explicitly configure test
roots and signoff strata, the audit must map Rack failures into dev-std audit
results, and configured signoff strata must carry the `signoff` concern.

Rack owns the Rack-specific semantics: `rack.toml`, stratum directories,
`STRATUM.toml`, discovered test files, declared subtest files, duplicate entries,
and signoff stratum existence. Dev-std must not maintain a parallel
implementation of those semantics now that Rack exposes a failing audit command
and Python API.

The first delegation uses Rack's non-strict audit mode so the dev-std behavior
matches the existing manifest-drift contract. Rack's strict `test_cases` and
`test_case_type` metadata checks remain available for later policy adoption
after runtime and migration impact are reviewed.
