# Changelog

## 2026.7.16

- Delegate the `tests` audit scope to Rack native audit from
  `wn-rack>=2026.7.16` instead of maintaining a duplicate Rack manifest parser.
- Keep dev-std-owned test-suite policy for explicit configured roots, mapped
  Rack audit failures, upgrade guidance when Rack audit support is missing, and
  the `signoff` concern on configured signoff strata.
- Add CLI command governance and reusable JSON Schema contract validation for
  command manifests and future schema-backed contracts.
- Document the Rack/dev-std test-audit ownership boundary and the deferred
  strict Rack metadata migration.

## 2026.7.15

- Improve plan, log, ADR, and requirement CLI text output with padded terminal
  spacing, scan-friendly sections, wrapped descriptions, and clearer status
  summaries while keeping JSON output machine-readable.
- Add Rack-backed test-suite governance and a required
  `docs/test-strategy.html` audit so packages document their high-level test
  architecture beyond Rack manifests.
- Add required plan closeout review of new test runtime impact before external
  review, with migration guidance for existing active plans.
- Add governance-first CI guidance and wire this repository's CI/release
  workflows to run `dev-std audit .` before expensive validation.
- Expand the config schema to match the implemented config surface, including
  workspace roots, configured scopes, Rack test governance, plan ignores,
  generated governance output, compatibility pruning, and PR hygiene.
- Retire the issue-19 temporary plan chain after independent review and full
  signoff.

## 2026.7.14

- Add `standard_version` config alignment checks, configured audit scopes,
  workspace member aggregation, and optional PyPI upstream-version warnings.
- Run only the checks needed for requested audit scopes so large workspace
  audits do not pay setup cost for unrelated governance areas.
- Keep upstream-version probes warning-only when PyPI or an intermediary
  returns malformed HTTP protocol responses.
- Move browser/web policy checks into a dedicated module without changing
  their behavior.
- Document pinned PyPI `wn-dev-std` usage for downstream governance CI and
  repair the local release policy guidance.
- Add the JSON Contract Standard for root `type`/`version`, nested `kind`,
  schema-labeled compatibility files, JSON Schema artifacts, and Pydantic
  usage.
- Require active plans to include a closeout governance-doc audit and external
  review as both steps and exit criteria, and order final review after the
  design-doc/ADR/requirement alignment checkpoint.
- Fail attempted plan closeout states such as `done`, `closed`, `complete`,
  and `finished` with guidance to move durable information into design docs,
  ADRs, requirements, tests, or release notes before deleting the active plan.
- Document vendor-manifest compatibility, signoff checklist expectations,
  Python 3.12 pin rationale, and squash/no-linear-history PR policy.
- Close the completed standards-governance issues and leave release-mode
  artifact audit and CLI/config-validation tooling for follow-up slices.

## 2026.7.2

- Add durable governance audits for ADRs, requirements, domains, governed
  surfaces, traceability refs, generated governance links, artifacts, vendors,
  release channels, and build docs.
- Add canonical `docs/build.html` / `docs/build.md` build-document governance
  with required setup, invocation, output, and signoff coverage.
- Add artifact, vendor, and release governance catalogs under
  `docs/governance/`, with tracked-file-first audits that avoid local build
  output false positives.
- Add generated governance HTML and link resolution for plans, logs, ADRs,
  requirements, and governance catalogs.
- Add ADR and requirement create/list/show commands and stricter plan/log
  lifecycle checks with structured steps, exit criteria, and step-linked logs.

## 2026.7.1

- Make the `zephyr-firmware` formatter policy inherit the upstream C++
  clang-format baseline instead of using a separate Attach/right-pointer
  formatter.
- Update the Zephyr clang-format template and conformance tests so firmware
  projects use Allman braces, left pointer alignment, sorted includes, and
  preserved include blocks consistently with C++ projects.

## 2026.6.29

- Add `[documentation.plans].ignore` for project-relative legacy paths that
  should be skipped by the plan/log hygiene audit during migration.
- Keep configured plan roots strict even when an ignored path overlaps a plan
  root.
- Document the plan-ignore migration setting.

## 2026.6.28

- Add structured plan exit criteria as a first-class plan metadata surface.
- Require active/pending/blocked plans to declare `[[exit_criteria]]`.
- Report exit-criteria status from `dev-std plan list` and
  `dev-std plan show`.
- Make newly created plans include a default pending signoff exit criterion.
- Configure `wn-dev-std` as a PyPI-published package.

## 2026.6.27

- Add `dev-std log show` for reading one compliant plan work log by globally
  unique log id.
- Release the first plan/log hygiene workflow slice with stricter plan-root
  Markdown metadata checks, structured plan steps, log attachment validation,
  and read/write helper commands.
- Document package-scoped plan audits, root discovery, active plan lifecycle,
  and the intended non-destructive boundary for plan/log commands.

## 2026.6.22

- Add a public PR hygiene standard for linked issues, Conventional Commit PR
  titles and commit subjects, emoji rejection, and AI-vendor attribution
  rejection.
- Add reusable GitHub workflow and pull request template files under
  `docs/templates/github/`.
- Add an opt-in `[pr_hygiene]` conformance check that verifies downstream repos
  have installed the public PR hygiene workflow and template.

## 2026.6.14

- Allow JavaScript profiles to use a foldered canonical standard design doc at
  `docs/design/standards/javascript.html` while preserving the legacy
  `docs/design/javascript-standard.html` path.
- Add `[documentation.standard_docs].javascript` for projects with deliberate
  custom design-doc layouts.
- Document the configuration schema and add regression tests for legacy,
  foldered, configured, and missing JavaScript standard doc paths.

## 2026.6.12

- Add the `zephyr-firmware` profile with west-based build-loop expectations,
  app-owned source signoff, target-toolchain notes, and embedded C/C++
  complexity gates.
- Add reusable C/C++ and Zephyr `signoff.toml` templates.
- Make canonical native new-code complexity explicit:
  `max_cyclomatic_complexity = 10`.
- Add native signoff configuration checks for complexity, file size, function
  size, clang-format mode, clang-tidy mode, and Lizard enforcement.
- Document the Rack/signoff quality model, including the public `wn-rack` PyPI
  package and the expectation that every project has an `L99_signoff` gate.

## 2026.6.10

- Allow local root `.env` files to pass `wn-dev-std check` only when Git reports
  them as untracked and ignored.
- Require C/C++ profiles to expose a Lizard-based native complexity gate under
  `tests/`.

## 2026.6.9

- Add the C/C++ fixed-width integer spelling rule to the `cpp-library`
  standard.
- Require C/C++ profiles to configure clang-tidy `google-runtime-int` as an
  error so owned code uses `std::int32_t`, `std::uint32_t`, `std::int64_t`, and
  `std::uint64_t` instead of `short`, `long`, or `long long`.

## 2026.6.7

- Codify HTML design-doc status markers with `draft`, `proposal`,
  `accepted`, and `superseded` states.
- Add a `wn-dev-std check` design-doc status gate that fails unmarked or
  invalid HTML design docs and reports draft/proposal docs for release signoff.
- Add the documentation standard design page and mark the reference design docs
  as accepted.

## 2026.6.4

- Add the initial working `wn-dev-std` Python package and CLI.
- Define the first strict Python development baseline with Rack, Ruff, Pyright,
  Hatchling, committed lockfiles, HTML design docs, JSON contracts, and
  release metadata signoff.
- Add the initial `cpp-library` profile with CMake, Ninja, clang-format,
  clang-tidy, CTest, warnings, sanitizer, ABI, and public/private header rules.
- Add the initial `python-native-wasm` mixed-mode profile modeled on Geometer
  for packages with CMake/C++, platform wheels, and WASM artifacts.
- Add the initial `csharp-app` profile for SDK-style C# application and
  host-plugin projects.
- Add `javascript-web-app` and `python-js-app` profiles for no-build browser
  apps, CSS/JS hygiene ratchets, and FastAPI-style Python-served frontends.
- Codify checked JavaScript/JSDoc, deterministic `node:test` coverage,
  CSS custom-property tokens, owned `wn-*` Web Components, JS-to-WASM wrapper
  tests, and simple command verbs for no-build web projects.
- Add configurable compatibility-pruning checks for retired environment
  variables, setup aliases, and other legacy surfaces.
- Add CI and model release-validation workflows for public Python packages,
  without publishing `wn-dev-std` itself to PyPI.
