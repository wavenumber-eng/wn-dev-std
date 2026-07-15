# wn-dev-std

`wn-dev-std` is a development standards reference package. It gives projects
strict baselines for packaging, tests, documentation, governance, release
hygiene, and agent-readable repo structure.

The repository is also a working example. It installs as a Python package and
exposes a small CLI whose code, docs, contracts, tests, and release metadata are
kept in sync by Rack signoff.

## Status

This repository is a model/reference package and is published to PyPI as
`wn-dev-std`. Python, C++, C#, JavaScript, mixed Python/native/WASM, and Zephyr
profiles are present. C and Rust profiles will reuse the same base rules as
they are added.

## Start Here

Agents and maintainers should start with the design docs, not by inferring
policy from source layout:

- [Audit Standard](docs/design/audit-standard.html): signoff scopes and how
  `dev-std audit` is intended to fail.
- [Documentation Standard](docs/design/documentation-standard.html): ADR,
  requirement, plan, log, domain, surface, fixture, and generated HTML rules.
- [CLI Design](docs/design/cli.html): public command surface.
- [CI Standard](docs/design/ci-standard.html): governance-first CI gating for
  GitHub Actions and GitLab CI.
- [Artifact And Vendor Governance](docs/design/artifact-vendor-governance.html):
  build outputs, release channels, vendored code, and generated source.
- [JSON Contract Standard](docs/design/json-contract-standard.html): JSON
  object identity, schema-labeled files, JSON Schema artifacts, and Pydantic
  usage.
- [Architecture](docs/architecture.html): Rack, strata, and release signoff
  model.

Every package that adopts this standard should run `dev-std audit .` from its
package signoff path. In Rack-based repositories, wire that invocation into
`L99_signoff` so local testing and CI fail when governance or documentation
drifts.

## Install

For normal tool use:

```bash
uv tool install git+https://github.com/wavenumber-eng/wn-dev-std.git
dev-std --version
```

or from PyPI:

```bash
uv tool install wn-dev-std
dev-std --version
```

For one-shot use:

```bash
uvx --from git+https://github.com/wavenumber-eng/wn-dev-std.git dev-std --help
```

For local development:

```bash
uv sync --all-extras
uv run dev-std audit .
uv run rack run --all
```

The installed command is `dev-std`. The older `wn-dev-std` command remains as a
compatibility alias for existing repositories and CI jobs.

This package currently pins Python to `>=3.12,<3.13`. The pin is intentional for
the standards reference package: it keeps Ruff, Pyright, Rack signoff, CLI
behavior, and generated metadata on one interpreter baseline. Downstream
projects can define their own runtime window when their compatibility contract
requires it.

## Rack Model

Projects using this standard should use the Rack model for validation structure.
Rack keeps test and signoff intent explicit through suite manifests, ordered
strata, lanes, concerns, dependencies, and durable result artifacts.

The public Rack package is [`wn-rack`](https://pypi.org/project/wn-rack/). The
distribution name is `wn-rack`; the command is `rack`.

Python projects should add `wn-rack` to their development or test dependency
group, then commit a `tests/rack.toml` suite manifest:

```bash
uv add --dev wn-rack
```

Non-Python projects should still follow the same model: keep `tests/rack.toml`
and stratum manifests in the repository, then run Rack from the project's
standard Python/tooling environment or CI image.

In this repository, the working Rack/signoff example lives under `tests/`, with
the suite manifest at `tests/rack.toml`.

Every project needs a signoff gate. In Rack suites this is generally an
`L99_signoff` stratum that runs the release-facing checks for the repository.
The exact checks vary by profile, but signoff should include measurable gates
such as complexity, file size, function size, formatting, static analysis,
documentation status, contract checks, release metadata, and any project-local
ratchets. `dev-std audit .` should be one of those gates for any package using
dev-std governance.

## Use Cases

- Start a new strict Python package with known development-standard defaults.
- Check whether a repository has required public project hygiene files.
- Provide agents with a concrete example of Rack, signoff, docs, contracts, and
  release metadata working together.
- Explain the quality model behind Rack orchestration and release signoff.
- Serve as the base vocabulary for future C/C++/C#/JS/Rust/Zephyr standards.

## CLI Examples

Show version and major internal dependency versions:

```bash
dev-std version
dev-std --version
```

Print the current Python standard summary:

```bash
dev-std standard
dev-std standard --format json
dev-std standard --profile cpp-library
dev-std standard --profile python-native-wasm
dev-std standard --profile csharp-app
dev-std standard --profile javascript-web-app
dev-std standard --profile python-js-app
dev-std standard --profile zephyr-firmware
```

Run the repository audit checks against the current repo:

```bash
dev-std audit .
dev-std audit . --format json
dev-std audit . --scope docs.plans
dev-std audit . --scope docs.test_strategy
dev-std audit . --scope tests
dev-std audit . --check-upstream-version
```

Configured repositories must declare the standard version they target:

```toml
standard_version = "2026.7.15"
profile = "python-package"

[tests]
roots = ["tests"]
signoff_strata = ["L99_signoff"]
```

When the config has `enabled_scopes`, `dev-std audit .` runs those scopes by
default and still runs the unfiltered config-version check. Passing a targeted
scope set is partial governance adoption, not full profile conformance:

```toml
standard_version = "2026.7.15"
profile = "zephyr-firmware"
enabled_scopes = ["docs.plans"]
```

Workspace roots aggregate explicitly registered package/application policy
boundaries. Members are policy boundaries, not every build target:

```toml
standard_version = "2026.7.15"
kind = "workspace"

[workspace]
members = ["bom_cruncher", "lib_cruncher", "panel-monkey"]
```

GitHub Actions should run this governance gate before expensive platform jobs,
and every expensive job should be gated on that first result. GitLab pipelines
should use the same shape with a first `governance` stage and later jobs using
`needs: ["governance"]`. Use a pinned PyPI release that matches
`standard_version`:

```bash
uvx --from wn-dev-std==2026.7.15 dev-std audit .
```

The `check` command is a compatibility alias for `audit`:

```bash
dev-std check .
```

Read and update compliant active plans and attached logs from anywhere inside a
package:

```bash
dev-std plan list
dev-std plan show pcb-a0
dev-std plan create pcb-a0 --title "PCB A0"
dev-std plan status pcb-a0 blocked
dev-std plan step add pcb-a0 audit --title "Audit old plans"
dev-std plan step list pcb-a0
dev-std log list
dev-std log list pcb-a0
dev-std log show pcb-a0-2026-06-27-001
dev-std log create pcb-a0 audit --body "Captured cleanup notes."
dev-std log create pcb-a0 audit --body-file notes.md
dev-std adr create core-adr-0001 --domain core --title "Record Decisions"
dev-std requirement create core-req-0001 --domain core --title "Audit Requirements"
```

CLI output leaves a blank padding line before the first content line and a
blank padding line after the final content line, including JSON and help output.

ADR and requirement text reads follow the same pretty-print conventions as plan
lists: `adr list` and `requirement list` start with the discovered root, an
indented status summary, status sections, and record entries with colored TTY
status badges and record ids. Titles and paths render on indented continuation
lines to keep terminal rows narrow, while JSON output remains the stable
machine-readable form.

Generate governance browse pages and resolve stable governance refs in
hand-authored HTML docs:

```bash
dev-std gov html --output docs/generated/governance
dev-std gov resolve --output docs/generated/governance --write
dev-std audit . --scope docs.links
```

## Python Baseline

Pure Python packages use:

- `uv` for environment, locking, and tool workflows
- `wn-rack` from PyPI as the standard test/signoff orchestrator
- committed `uv.lock`
- `pyproject.toml` with Hatchling
- Rack for test orchestration
- Ruff and Pyright
- strict typing
- HTML design docs with explicit `data-doc-status` markers and JSON contracts
- JSON object contracts with root `type` plus `version` for durable payloads,
  `kind` for nested variants, and documented JSON Schema artifacts
- date-based releases
- GitHub Release published events for release validation
- optional PyPI trusted publishing for projects that choose that distribution
- CI on Ubuntu, Windows, and macOS

## C++ Baseline

The first native profile is `cpp-library`, modeled on the Geometer and
`altium_monkey_cpp` C++ conventions.

C++ projects use:

- CMake, CTest, and `CMakePresets.json`
- Ninja as the default generator
- `CMAKE_EXPORT_COMPILE_COMMANDS=ON`
- committed `.clang-format` and `.clang-tidy`
- clang-format style based on LLVM, Allman braces, 4-space indentation, 100
  columns, left pointer alignment, sorted includes, and preserved include
  blocks
- fixed-width integer spellings in owned C/C++ code
  (`std::int32_t`, `std::uint32_t`, `std::int64_t`, `std::uint64_t`) instead
  of `short`, `long`, or `long long`
- compiler warnings on owned code, with release-facing CI treating warnings as
  errors where feasible
- Rack strata for native foundation, algorithms, CLI/API integration, and L99
  release signoff

## Zephyr Firmware Baseline

The first embedded profile is `zephyr-firmware`. It inherits the C/C++ native
rules and adds Zephyr-specific build-loop expectations:

- app-local `build` scripts that enable `CMAKE_EXPORT_COMPILE_COMMANDS=ON`
- application-owned source roots checked first, excluding Zephyr, west modules,
  generated files, vendor code, and build outputs
- `signoff.toml` with Lizard as the failing complexity gate
- canonical new-code `max_cyclomatic_complexity = 10`
- clang-format in the prebuild report/fail lane
- clang-tidy in the postbuild report/fail lane using the active compile
  database
- documented target-toolchain gaps, such as Xtensa clang-tidy support

## Mixed-Mode Baseline

The first mixed-mode profile is `python-native-wasm`, modeled on Geometer-style
packages that combine Python wrappers, CMake/C++ native builds, platform wheels,
and WASM runtime artifacts.

Mixed-mode packages add:

- CMake and CTest for native builds
- grouped committed runtime artifacts under `dist/native/<platform>/` and
  `dist/wasm/<target>/`
- documented custom wheel hooks when platform wheels bundle executables
- native validation before package validation
- installed-wheel smoke tests that prove the bundled executable is used
- separate CI lanes for Python, native, platform wheels, WASM, and release
  validation

## JavaScript Web Baseline

The first browser profile is `javascript-web-app`, with `python-js-app` for
FastAPI-style packages that serve the browser runtime.

Web apps use:

- no-build HTML, CSS, and browser JavaScript by default
- optional Node tooling only when dependencies, bundling, or browser test
  infrastructure justify it
- checked JavaScript through `jsconfig.json`, `tsconfig.json`, JSDoc, or
  per-file `// @ts-check`
- deterministic `node:test` coverage for algorithmic JavaScript, parsers, CAD
  state, and data transforms
- CSS custom properties for design constants before hard-coded color, spacing,
  z-index, radius, or typography values spread through files
- owned `wn-*` Web Components for repeated stateful UI primitives such as
  dialogs, toast regions, panels, toolbars, and property rows
- JS-to-WASM wrapper tests for browser-facing WebAssembly, with Wasmer or
  Wasmtime optional for core WASM checks when useful
- standard command verbs: `install`, `update`, `build`, `test`, and `signoff`
- explicit ES module or manifest-ordered IIFE ownership
- isolated `vendor/`, `lib/`, `_build/`, `node_modules/`, and minified assets
- JS and CSS hygiene ratchets for file size, complexity, nesting, generated
  asset placement, and whitespace
- Rack signoff for browser smoke tests and Python-to-browser API contracts

## Compatibility Pruning

Projects that are retiring old names, environment variables, setup shims, or
compatibility aliases can opt into a repository scan in `dev-std.toml`:

```toml
[compatibility_pruning]
root = ".."
forbidden_patterns = [
  "\\bWN_LIBZ_ROOT\\b",
  "\\bwn_pcb\\b",
]
excluded_parts = ["test_cases", "fixtures"]
```

The check is intentionally configurable because legacy cleanup is project
specific. It should be part of L99 signoff when a repo has known old surfaces to
prune, with generated files and captured fixtures excluded explicitly.

## Public PR Hygiene

Public repositories can opt into the shared PR hygiene gate by copying:

- `docs/templates/github/pr-hygiene.yml` to
  `.github/workflows/pr-hygiene.yml`
- `docs/templates/github/pull_request_template.md` to
  `.github/pull_request_template.md`

Then enable local conformance validation:

```toml
[pr_hygiene]
enabled = true
```

In `pyproject.toml`, use `[tool.wn_dev_std.pr_hygiene]` instead. The workflow
requires a filled `Linked issue:` line that points at an existing same-repo
issue, Conventional Commit form for PR titles and commit subjects, commit
subjects of 72 characters or fewer, and no `WIP`, emoji, or AI-vendor
attribution in PR metadata or commit messages.

Public repos should merge through reviewed PRs with required CI and a squash
merge into `main`. Do not use merge commits or accumulated local branch history
to create a non-linear public `main` history unless a project-specific release
exception documents why the history must be preserved.

## Design Doc Status

HTML design docs under `docs/design` must declare `data-doc-status` with one of
`draft`, `proposal`, `accepted`, or `superseded`. The check fails unmarked or
invalid design docs and reports draft/proposal pages for release review.

JavaScript profiles accept either `docs/design/javascript-standard.html` or the
foldered path `docs/design/standards/javascript.html` for the canonical
JavaScript standard design doc. Projects with a different deliberate layout may
configure it:

```toml
[documentation.standard_docs]
javascript = "docs/design/standards/javascript.html"
```

## Plan And Log Hygiene

Active plans and attached work logs are temporary Markdown documents with TOML
front matter. The `docs.plans` audit scope checks approved plan roots, plan/log
metadata, dependency references, orphan logs, and rogue plan-like or log-like
files outside approved roots. Approved roots are allowed locations, not required
folders, so packages with no active plans do not need empty placeholders. Plan
documents use `type = "plan"` and work logs use `type = "plan_log"`.
Plans must declare `[[exit_criteria]]` entries so closeout state is
machine-readable.
Every active/pending/blocked plan must include `design-doc-intent-audit`,
`test-runtime-impact-audit`, and `external-review` as both `[[steps]]` ids and
`[[exit_criteria]]` ids. The design-doc audit step verifies required design docs
still match the user's intent and the implemented behavior. The runtime-impact
audit step lists new or changed tests, reviews `docs/test-strategy.html`, and
records optimization or slower-lane decisions when new tests add meaningful
runtime. Its matching exit criterion is `New tests are listed and runtime
impact is reviewed`. The external-review step records independent review after
those closeout checks.
This is a current-standard migration requirement: existing active plans must add
the runtime-impact step and exit criterion before `docs.plans` or full audit
passes with this tool version. Repositories that cannot migrate immediately
should keep CI pinned to the previous reviewed `wn-dev-std` release or defer the
`docs.plans` scope until their active plan catalog is updated.
Markdown names with a standalone `log` token, such as `v1_1_log.md`, are treated
as log-like and must either be compliant `plan_log` files or be renamed and
classified as durable documentation. Completed work is closed out into durable
artifacts and removed; `complete` is not a valid resting status for active plan
files.
Multi-step plans may declare `[[steps]]` metadata with `pending`, `active`,
`blocked`, or `done` status values.
Exit criteria use `pending`, `met`, or `blocked` status values. Steps describe
execution progress; exit criteria describe the conditions that must be true
before the plan can be retired. `dev-std plan list` groups the text view into
current, dependency-waiting, parked/pending, and blocked sections, with TTY
color unless `NO_COLOR` is set. Section headings have divider rules, official
states render as background-color badges in TTY output, plan ids render as black
text on white, and step ids use a different treatment so dependency chains and
step lists are easier to scan. The text view starts with the discovered root,
then a blank line, then an indented summary block with one state count per line.
Each plan item shows the plan id and official state, created date, nested latest
attached log detail with its step id, supporting path, nested dependency detail,
grouped step lists with colored headings, step titles on indented continuation
lines, nested step-dependency bullets, and explicit exit-criteria status counts.
`dev-std plan list --format json` remains the stable
machine-readable form. `dev-std plan list` and `dev-std plan show` report
exit-criterion status, and `docs.plans` fails active plans with no exit criteria
or plans whose criteria are all met while the plan still remains active.

```toml
[documentation.plans]
roots = ["docs/plans"]
ignore = ["docs/work_tickets", "src/fum_bringup"]
```

`ignore` entries are project-relative files or directories that the
plan/log audit skips while legacy material is being migrated. Ignore entries do
not suppress checks inside configured plan roots; active plan roots remain
strict.

The `plan` and `log` commands discover the package root by walking upward to
`dev-std.toml`, legacy `wn-dev-std.toml`, a `pyproject.toml` with
`[tool.wn_dev_std]`, or a `.git` fallback boundary. Read and mutation commands
only operate on a compliant plan
catalog. The first mutation slice is non-destructive: create plans, set plan
status, add/update step status, list step ids, and create step-attached logs.
Use `log create <plan-id> <step-id> --body` for short one-line notes. Use
`--body-file` for longer Markdown bodies so shell command-line length, newline,
and quoting limits do not shape the log content. Bare `log list` lists logs
across all plans, grouped by plan and then by step; `log list <plan-id>` keeps a
focused per-plan view grouped by step. Both text views include an indented
summary, nested log entries, wrapped path fields, and TTY color for plan, step,
and log ids unless `NO_COLOR` is set. `log show` reads one attached log body by
globally unique log id and renders its metadata as a compact nested block before
the body. Plan deletion, retirement, and migration
helpers are intentionally left for a later tool pass.

## Documentation

- [Setup](docs/setup.html)
- [Architecture](docs/architecture.html), including the Rack/signoff quality model
- [CLI Design](docs/design/cli.html)
- [CI Standard](docs/design/ci-standard.html)
- [Audit Standard](docs/design/audit-standard.html)
- [Documentation Standard](docs/design/documentation-standard.html)
- [Artifact And Vendor Governance](docs/design/artifact-vendor-governance.html)
- [JSON Contract Standard](docs/design/json-contract-standard.html)
- [Build Documentation](docs/build.html)
- [Test Strategy](docs/test-strategy.html)
- [Python Standard Design](docs/design/python-standard.html)
- [C++ Standard](docs/design/cpp-standard.html)
- [Mixed Mode Standard](docs/design/mixed-mode.html)
- [JavaScript Web App Standard](docs/design/javascript-standard.html)
- [Release Notes](docs/releases/2026-07-15.md)

## License

MIT. See [LICENSE](LICENSE).
