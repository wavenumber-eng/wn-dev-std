+++
type = "adr"
id = "core-adr-0007"
domain = "core"
status = "accepted"
title = "TypeScript Is The Greenfield Browser Standard"
created = "2026-07-18"
plan_refs = ["typescript-greenfield-standard"]
requirement_refs = ["core-req-0007"]
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
+++

# TypeScript Is The Greenfield Browser Standard

The decision is to make TypeScript the default for new Wavenumber browser,
frontend, and JavaScript-facing library projects.

The existing `javascript-web-app` and `python-js-app` profiles remain available
for no-build projects and existing checked-JavaScript ports. They are
compatibility profiles, not the target for new shared browser runtimes or
libraries.

New greenfield projects should use `typescript-web-app`. Python packages or
services that serve a TypeScript browser runtime should use `python-ts-app`.
Those profiles require TypeScript source, strict compiler guardrails, a
committed Node toolchain surface, and signoff commands that run typecheck and
lint.

The TypeScript audit deliberately validates configuration and repository shape
instead of parsing TypeScript source in Python. Actual type errors,
TypeScript-aware lint rules, explicit public boundary annotations, and framework
specific checks belong in the project's `typecheck` and `lint` scripts. This
keeps `dev-std` responsible for the standards contract while letting the
TypeScript compiler and TypeScript-aware linters own source semantics.

The first implementation resolves the `tsconfig extends` question with a
local-file rule. The audit resolves project-relative and file-relative local
`extends` targets and merges inherited `compilerOptions`. Package-based
`extends` values are not inspected because the audit does not install
dependencies. A project may keep a package-based baseline only with an explicit
TypeScript exception that documents the reviewed source and trigger for
rechecking the inherited config.

The first implementation also treats `exactOptionalPropertyTypes: true` as part
of the greenfield guardrail baseline. It is stricter than many existing
JavaScript ports, but it closes common optional-property ambiguity in new code.
Existing ports can use the JavaScript compatibility profiles or the TypeScript
migration exception path until their object-shape contracts are cleaned up.

`skipLibCheck: true` and `allowJs: true` are not accepted silently in TypeScript
profiles. `skipLibCheck: true` needs a documented exception because it hides
third-party declaration drift. `allowJs: true` and owned JavaScript source need
a migration record because they are temporary porting state.

`target`, `module`, and `moduleResolution` are documented as profile posture,
not universal guardrails. Browser apps commonly use ES module output and bundler
resolution, while Node-targeting libraries may need NodeNext module behavior.
The audit enforces the strict guardrail options and leaves runtime posture to
the profile documentation and project build scripts.
