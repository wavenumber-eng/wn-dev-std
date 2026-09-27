+++
type = "requirement"
id = "core-req-0009"
domain = "core"
status = "implemented"
title = "Contract Units Declare TypeSpec Structural Authority"
created = "2026-09-27"
plan_refs = ["contract-and-application-standards"]
adr_refs = ["core-adr-0009"]
design_refs = [
  "docs/design/typespec-contract-standard.html",
  "docs/design/json-contract-standard.html",
]

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/typespec_policy.py"

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/typespec_standard_data.py"

[[implementation_refs]]
kind = "local_file"
target = "docs/contracts/wn_dev_std_config.schema.v0.json"

[[implementation_refs]]
kind = "local_file"
target = "docs/templates/typespec-contract/README.md"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_025_typespec_policy.py::test_typespec_contract_capability_passes_for_non_web_project"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_025_typespec_policy.py::test_typespec_contract_capability_requires_exact_tool_versions"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_025_typespec_policy.py::test_required_projection_needs_supported_consumer_evidence"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L99_signoff/test_L99_006_templates.py::test_copy_owned_templates_pass_clean_signoff"
+++

# Contract Units Declare TypeSpec Structural Authority

New Wavenumber-owned contracts that cross a language or process boundary must
declare TypeSpec as their structural authority unless a reviewed exception
identifies an upstream authority or an unsupported or lossy construct.

The policy must be independently adoptable by backend, CLI, configuration,
library, native, data, and web projects. It must not depend on Lit, activities,
CSS, browser APIs, or a frontend profile.

Dev-std configuration must support one or more named contract units. Each unit
must declare:

- authority ownership and scope;
- TypeSpec entry point and compiler configuration;
- pinned compiler, library, and emitter dependencies;
- generated projection kinds and output roots;
- which projections are required for that unit's real consumers;
- deterministic regeneration and freshness commands;
- generated-file publication and editing policy;
- consumer and conformance evidence;
- compatibility/versioning posture;
- documented exceptions with rationale, scope, and review trigger.

The audit must validate declared configuration and repository shape without
installing dependencies or executing arbitrary project commands. Project or
Rack signoff must execute TypeSpec compilation, generation, freshness, and
consumer checks.

The standard must distinguish required, recommended, optional, experimental,
and unsupported projections. It must not require unused language output or
claim support for emitters that the reference template cannot independently
install and validate.

The reference contract template must prove TypeSpec compilation, JSON Schema,
one generated language projection used by executable code, and shared
conformance vectors consumed by a second independent runtime. Additional
Python, Rust, or TypeScript generators may be included only when their tooling
and validation are self-contained.
