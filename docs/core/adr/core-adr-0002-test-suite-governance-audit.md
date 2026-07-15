+++
type = "adr"
id = "core-adr-0002"
domain = "core"
status = "accepted"
title = "Dev Std Audits Rack Test Manifests Locally"
created = "2026-07-15"
issue_refs = ["wavenumber-eng/wn-dev-std#19", "wavenumber-eng/wn-dev-std#22", "wavenumber-eng/wn-rack#4"]
requirement_refs = ["core-req-0002"]
design_refs = ["docs/core/design/test-suite-governance-audit.html", "docs/design/audit-standard.html"]

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/test_governance.py"
+++

# Dev Std Audits Rack Test Manifests Locally

`dev-std audit --scope tests` performs a local, read-only Rack manifest audit
for repositories that opt into test-suite governance. The audit compares
configured test roots, Rack strata, stratum manifests, discovered test files,
and signoff strata so stale `rack.toml` or `STRATUM.toml` metadata fails before
release-facing review.

This is an interim ownership decision. Rack remains responsible for test
execution and should own a native failing audit command, but that command is not
available in the current Rack release. Until Rack exposes that capability,
dev-std owns the committed-manifest validation needed by downstream governance.
Future dev-std work should delegate this check to Rack once the linked Rack
issue is implemented.
