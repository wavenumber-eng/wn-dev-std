+++
type = "requirement"
id = "core-req-0007"
domain = "core"
status = "implemented"
title = "Greenfield TypeScript Projects Use Strict Guardrails"
created = "2026-07-18"
plan_refs = ["typescript-greenfield-standard"]
adr_refs = ["core-adr-0007"]
design_refs = [
  "docs/design/typescript-standard.html",
  "docs/design/javascript-standard.html",
  "docs/design/audit-standard.html",
  "docs/design/cli.html",
]

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/typescript_policy.py"

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/typescript_standard_data.py"

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/standard_model.py"

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/check_profiles.py"

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/standards.py"

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/checks.py"

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/cli/commands/standard.py"

[[implementation_refs]]
kind = "local_file"
target = "docs/contracts/wn_dev_std_config.schema.v0.json"

[[implementation_refs]]
kind = "local_file"
target = "docs/contracts/interface_manifest.v0.json"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_002_public_interfaces.py::test_default_typescript_web_standard_contains_guardrail_rules"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_002_public_interfaces.py::test_default_python_ts_standard_contains_python_and_typescript_rules"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_002_public_interfaces.py::test_default_standard_selects_profiles"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_002_public_interfaces.py::test_render_typescript_web_standard_json_round_trips"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_020_typescript_policy.py::test_typescript_web_profile_language_checks_pass_for_minimal_repo"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_020_typescript_policy.py::test_typescript_profile_accepts_schema_url_and_jsonc_syntax"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_020_typescript_policy.py::test_typescript_command_surface_requires_typecheck_not_install_lifecycle"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L99_signoff/test_L99_002_docs_contracts.py::test_config_schema_matches_runtime_config_surface"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L99_signoff/test_L99_004_repo_hygiene.py::test_typescript_policy_is_documented"
+++

# Greenfield TypeScript Projects Use Strict Guardrails

New Wavenumber browser, frontend, and JavaScript-facing library projects must
use TypeScript as the default typed contract surface. The standard must make
common gross errors difficult to commit by validating the project profile,
compiler configuration, owned source shape, command surface, and signoff wiring.

The implementation must add greenfield TypeScript profiles for browser apps and
Python-served browser apps. Those profiles must require owned TypeScript source
under `src/`, a committed Node package manifest and lockfile, a typecheck
configuration, and declared `typecheck`, `lint`, `test`, `build`, and `signoff`
commands.

TypeScript profile audits must require strict compiler guardrails. At minimum,
the effective typecheck config must enable `strict`, `noUncheckedIndexedAccess`,
`exactOptionalPropertyTypes`, `noPropertyAccessFromIndexSignature`,
`noImplicitOverride`, `noImplicitReturns`, `noFallthroughCasesInSwitch`,
`useUnknownInCatchVariables`, `forceConsistentCasingInFileNames`,
`isolatedModules`, `verbatimModuleSyntax`, and `noEmit`.

The audit must treat TypeScript config inheritance as auditable only when the
`extends` target resolves to a local file inside the project root. Package-based
`extends` values may pass only with an explicit TypeScript exception because the
audit does not install or inspect package-manager dependencies.

Greenfield TypeScript profile audits must reject `allowJs: true`, owned
JavaScript source under `src/`, and `skipLibCheck: true` unless the project
declares the corresponding TypeScript migration or exception metadata in
`dev-std.toml` or `[tool.wn_dev_std]`.

The standard must require public TypeScript surfaces to expose explicit typed
boundaries: exported functions, callbacks, event handlers, service payloads,
config objects, async results, and package exports need TypeScript-visible
parameter and return shapes. The audit must not implement a fragile Python
TypeScript parser for this source-level rule; projects satisfy it through a
TypeScript-aware lint script and the required `typecheck` lane.

Existing `javascript-web-app` and `python-js-app` projects remain valid
compatibility profiles. They may continue to use checked JavaScript, JSDoc,
`jsconfig.json`, `tsconfig.json`, and `// @ts-check` while they port. That
migration lane must not redefine the greenfield target: new code should move to
TypeScript instead of expanding checked-JS source.
