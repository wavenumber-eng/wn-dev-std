+++
type = "requirement"
id = "core-req-0005"
domain = "core"
status = "implemented"
title = "CLI Audit Validates Command Governance"
created = "2026-07-16"
issue_refs = ["wavenumber-eng/wn-dev-std#7"]
adr_refs = ["core-adr-0005"]
design_refs = ["docs/design/cli-standard.html", "docs/core/design/cli-governance-audit.html", "docs/design/audit-standard.html"]

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/cli_governance.py"

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/governance_checks.py"

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/json_contracts.py"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_018_cli_governance.py::test_docs_cli_accepts_aggregate_design_doc_and_surface_refs"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_018_cli_governance.py::test_docs_cli_fails_missing_design_section"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_018_cli_governance.py::test_docs_cli_fails_nested_leaf_name_without_canonical_path"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_018_cli_governance.py::test_docs_cli_fails_a0_schema_shape_errors"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_019_json_contracts.py::test_json_contracts_report_path_addressed_schema_errors"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L99_signoff/test_L99_004_repo_hygiene.py::test_runtime_schema_contracts_are_packaged"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L99_signoff/test_L99_002_docs_contracts.py::test_command_manifest_matches_cli_and_design_doc"
+++

# CLI Audit Validates Command Governance

The `docs.cli` audit must validate command-line governance for repositories
that opt into the scope. It must preserve explicitly configured legacy v0 command
manifest paths, support the richer a0 command manifest, enforce public and experimental
command design coverage, validate linked contract documents, and support
deterministic parser/help parity when configured.

The audit must support aggregate command design docs with command sections as
well as per-command design files. Nested commands must use canonical command
paths so leaf command names cannot collide across command groups.

The a0 command manifest must be structurally validated with the reusable JSON
Schema contract helper before repository-aware semantic checks run. The audit
must not reimplement schema-owned field type, enum, required-field, or
additional-property checks in bespoke CLI code.
