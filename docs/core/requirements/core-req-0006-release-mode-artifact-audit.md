+++
type = "requirement"
id = "core-req-0006"
domain = "core"
status = "implemented"
title = "Release Mode Validates Promoted Artifacts"
created = "2026-07-18"
issue_refs = ["wavenumber-eng/wn-dev-std#13"]
plan_refs = ["issue-13-release-mode-artifact-audit"]
adr_refs = ["core-adr-0006"]
design_refs = [
  "docs/design/artifact-vendor-governance.html",
  "docs/design/audit-standard.html",
  "docs/design/cli.html",
  "docs/core/design/release-mode-artifact-audit.html",
]

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/artifact_governance.py"

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/release_artifacts.py"

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/artifact_policy.py"

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/cli/commands/audit.py"

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/checks.py"

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/governance_checks.py"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_001_cli_entrypoint.py::test_audit_help_documents_release_mode"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_013_artifact_vendor_governance.py::test_docs_release_default_mode_shape_validates_promoted_artifacts"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_013_artifact_vendor_governance.py::test_docs_release_default_mode_does_not_require_payload_files"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_013_artifact_vendor_governance.py::test_docs_release_release_mode_fails_missing_required_payload"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_013_artifact_vendor_governance.py::test_docs_release_release_mode_passes_bounded_glob_payload"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_013_artifact_vendor_governance.py::test_docs_release_release_mode_fails_uncataloged_payload"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_013_artifact_vendor_governance.py::test_docs_release_release_mode_allows_shared_root_payloads_across_channels"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_013_artifact_vendor_governance.py::test_docs_release_release_mode_validates_sha256"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_013_artifact_vendor_governance.py::test_docs_release_release_mode_accepts_matching_declared_metadata"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_013_artifact_vendor_governance.py::test_docs_release_release_mode_fails_version_mismatch"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_013_artifact_vendor_governance.py::test_docs_release_release_mode_fails_source_commit_mismatch"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_013_artifact_vendor_governance.py::test_docs_release_release_mode_runs_when_all_is_selected"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_013_artifact_vendor_governance.py::test_docs_artifacts_release_mode_keeps_default_behavior"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_013_artifact_vendor_governance.py::test_workspace_release_mode_runs_per_member_catalog"
+++

# Release Mode Validates Promoted Artifacts

`dev-std` must provide an explicit release-mode audit for produced or promoted
release payloads. The audit must be opt-in from normal development checks so
ignored local build output such as `build/`, `output/`, `rack_results/`, and
ordinary `dist/` staging paths do not fail default source-governance audits.

Release mode must inspect configured release-channel artifact declarations and
fail when required local payloads are missing, when promoted files are not
cataloged, or when declared release metadata does not match the produced file
or the audited source tree.

At minimum, the release-mode contract must cover:

- required versus optional promoted artifacts by release channel
- exact local paths or bounded glob patterns for files selected for release
- checksum validation when a checksum is declared
- version validation against the audited package version when declared
- source-commit prefix validation against the audited Git HEAD when declared
- target, build-profile, ABI/runtime, channel-relative destination, and license
  notes for platform or runtime-specific payloads

Default release governance must validate promoted-artifact declaration shape
without reading local payload files. Release-mode inspection must use the same
bounded pattern semantics for declared files and uncataloged-payload detection.
Uncataloged-payload detection must evaluate the catalog-wide promoted-artifact
pattern set so channels that share a promoted root do not flag each other's
cataloged payloads.

The audit must not upload artifacts or replace channel-specific publishing
tools. It must be a signoff gate that proves the local release payload set is
consistent with the authored release catalog before publication.
