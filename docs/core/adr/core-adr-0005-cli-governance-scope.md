+++
type = "adr"
id = "core-adr-0005"
domain = "core"
status = "accepted"
title = "CLI Governance Uses Dedicated Inventory Scope"
created = "2026-07-16"
issue_refs = ["wavenumber-eng/wn-dev-std#7"]
requirement_refs = ["core-req-0005"]
design_refs = ["docs/design/cli-standard.html", "docs/core/design/cli-governance-audit.html", "docs/design/audit-standard.html"]

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/cli_governance.py"

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/json_contracts.py"
+++

# CLI Governance Uses Dedicated Inventory Scope

CLI command sets need signoff checks that generic surface governance does not
model directly: command paths, aliases, nested subcommands, parser/help parity,
design-document structure, and config/output contract linkage.

The standard therefore adds a dedicated `docs.cli` scope. The scope remains
connected to `docs.surfaces` rather than replacing it. CLI manifests should
link commands to governed surfaces or use the same typed evidence semantics so
behavior verification, fixture coverage, parity, and exceptions do not diverge
into a weaker parallel model.

The richer CLI contract is a non-breaking evolution of the existing command
manifest. Existing `command_manifest.v0.json` files remain valid; richer
portable command metadata uses an a0 schema.

The a0 manifest structure is enforced with the standard JSON Schema contract
validator. CLI-specific audit code handles repository-aware semantics such as
design-doc resolution, parser inventory parity, path containment, and evidence
disposition.
