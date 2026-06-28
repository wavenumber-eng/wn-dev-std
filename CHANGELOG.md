# Changelog

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
