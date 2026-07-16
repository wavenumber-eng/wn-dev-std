+++
type = "plan"
id = "rack-native-test-audit-adoption"
status = "active"
created = "2026-07-16"

[[steps]]
id = "settle-rack-audit-contract"
title = "Settle Rack native audit contract"
status = "done"

[[steps]]
id = "bootstrap-rack-dev-std"
title = "Bootstrap Rack against latest dev-std"
status = "done"
depends_on = ["settle-rack-audit-contract"]

[[steps]]
id = "implement-rack-native-audit"
title = "Implement Rack native test-suite audit"
status = "done"
depends_on = ["settle-rack-audit-contract"]

[[steps]]
id = "dogfood-rack-audit"
title = "Dogfood Rack audit with latest dev-std checks"
status = "done"
depends_on = ["bootstrap-rack-dev-std", "implement-rack-native-audit"]

[[steps]]
id = "release-rack-capability"
title = "Publish Rack audit capability"
status = "done"
depends_on = ["dogfood-rack-audit"]

[[steps]]
id = "adopt-rack-in-dev-std"
title = "Delegate dev-std tests audit to Rack"
status = "active"
depends_on = ["release-rack-capability"]

[[steps]]
id = "update-dev-std-governance-docs"
title = "Update dev-std governance docs and contracts"
status = "pending"
depends_on = ["adopt-rack-in-dev-std"]

[[steps]]
id = "design-doc-intent-audit"
title = "Audit design docs, ADRs, and requirements against implementation"
status = "pending"
depends_on = ["update-dev-std-governance-docs"]

[[steps]]
id = "test-runtime-impact-audit"
title = "Audit new test runtime impact"
status = "pending"
depends_on = ["implement-rack-native-audit", "adopt-rack-in-dev-std"]

[[steps]]
id = "dev-std-signoff"
title = "Run dev-std local signoff"
status = "pending"
depends_on = ["design-doc-intent-audit", "test-runtime-impact-audit"]

[[steps]]
id = "external-review"
title = "Obtain independent external review"
status = "pending"
depends_on = ["design-doc-intent-audit", "test-runtime-impact-audit", "dev-std-signoff"]

[[exit_criteria]]
id = "rack-audit-contract"
title = "Rack exposes a stable failing audit command or API for manifest-vs-test-suite drift"
status = "met"

[[exit_criteria]]
id = "rack-latest-dev-std-bootstrap"
title = "Rack dogfoods latest dev-std CLI audit through a documented temporary unreleased-version lane"
status = "met"

[[exit_criteria]]
id = "dev-std-rack-delegation"
title = "dev-std tests-scope audit delegates to Rack native audit instead of owning duplicate Rack semantics"
status = "pending"

[[exit_criteria]]
id = "release-order"
title = "Release sequencing uses development-only pins and requires a published Rack audit version before dev-std release"
status = "met"

[[exit_criteria]]
id = "design-doc-intent-audit"
title = "Design docs, ADRs, requirements, and release notes match implementation"
status = "pending"

[[exit_criteria]]
id = "test-runtime-impact-audit"
title = "New tests are listed and runtime impact is reviewed"
status = "pending"

[[exit_criteria]]
id = "signoff"
title = "Focused local signoff passes"
status = "pending"

[[exit_criteria]]
id = "external-review"
title = "Independent external review is complete"
status = "pending"
+++

# Adopt Rack Native Test Audit

Plan the cross-repo work needed for Rack to own native test-suite audit behavior and for dev-std to delegate its tests-scope audit to that Rack capability.

## Context

- wavenumber-eng/wn-dev-std#22 tracks the follow-up to replace dev-std's local Rack manifest drift audit with a Rack-native audit once Rack exposes one.
- wavenumber-eng/wn-rack#4 tracks the Rack-side feature: a failing audit/check command for `tests/rack.toml`, stratum directories, `STRATUM.toml`, discovered test files, declared subtests, duplicate ids/files, signoff strata, and optional strict metadata.
- dev-std currently has bootstrap coverage in `src/wn_dev_std/test_governance.py`. That code is acceptable as a local first pass, but it should not become the long-term source of Rack semantics.
- Rack should use the latest dev-std CLI audit and command-manifest policy during this work, but the current dev-std implementation has not been released. The plan therefore uses a temporary development lane for Rack and removes it before release-facing closure.

## Design Direction

Rack owns Rack semantics. dev-std should specify that projects use Rack for test orchestration and should verify that Rack's native audit passes, but dev-std should not hand-maintain an independent Rack manifest parser once Rack provides a stable audit surface.

Prefer a Rack public Python API if Rack exposes one. If Rack only exposes a CLI surface at first, require a deterministic command such as `rack audit --format json` or an equivalent machine-readable mode so dev-std can map Rack failures into normal audit results without scraping prose. Any machine-readable CLI output consumed by dev-std must have a versioned output contract and committed JSON Schema.

The dev-std default should remain "latest standard wins." After dev-std raises its minimum Rack version to the first release with native audit, missing Rack audit support should fail with upgrade guidance rather than silently falling back to the old local implementation. A temporary fallback is acceptable only while this plan is active and documented as a migration bridge.

## Release Bootstrap

The cross-repo dependency should be handled in this order:

1. Develop Rack against the current dev-std checkout or an explicit development-only dev-std commit pin so Rack can dogfood unreleased CLI audit behavior without pretending the version is available on PyPI.
2. Implement and sign off Rack native audit in the Rack repository.
3. Publish a Rack release containing native audit. A short-lived Rack commit pin is acceptable only for development validation, not for the dev-std release path.
4. Update dev-std to require the Rack release that contains native audit.
5. Replace dev-std's bootstrap Rack semantics with a thin adapter around the Rack audit surface.
6. Release dev-std after the Rack dependency is real and the temporary unreleased-version lane is removed or documented as closed.

This prevents a circular release dependency: Rack can use unreleased dev-std as a development tool, but released dev-std should depend only on a released Rack capability.

The Rack release produced by this plan uses Wavenumber date-versioning. The
current Rack release target is `2026.7.16`, not semantic versioning.

## Rack CLI Governance Dogfood

Rack should adopt the new `docs.cli` governance while this dev-std version is
still unreleased. Do not require an unreleased PyPI package in Rack's durable
project metadata.

Implementation-time validation should use the local/source checkout, for
example:

```powershell
uv run --project <dev-std-checkout> dev-std audit <wn-rack-checkout> --scope docs.cli
```

Rack dogfood artifacts should include:

- a dev-std config marker in `wn-rack`;
- `docs/contracts/command_manifest.a0.json`;
- a CLI design doc or aggregate command design sections for `rack list`,
  `rack run`, `rack status`, `rack report`, `rack refresh`,
  `rack inventory`, `rack audit`, and `rack new`;
- a deterministic inventory provider. Rack likely needs to refactor parser
  construction into a `build_parser()` function so `docs.cli` can inspect the
  parser without arbitrary command execution.

After `wn-dev-std` is released, Rack can add a normal CI/dev dependency on the
released version and run `dev-std audit . --scope docs.cli` without the local
source checkout.

## Rack Work

- Define the Rack audit command/API name, exit-code behavior, and output contract.
- Validate `tests/rack.toml` stratum order against real stratum directories.
- Require every configured stratum directory to contain `STRATUM.toml`.
- Compare discovered `test_*.py` files with `[[subtests]].file` declarations.
- Fail declared subtests whose files do not exist.
- Reject duplicate subtest ids and duplicate declared files.
- Identify signoff strata by explicit config or established convention, including `L99_signoff`.
- Add optional strict mode for missing `test_cases` and `test_case_type` once the base audit is stable.
- Add Rack tests that prove the command fails on drift and passes on a synchronized suite.

Recommended command/API shape:

```text
rack audit [stratum] [--strict] [--format text|json]
```

```python
audit_suite(root: Path, *, strict: bool = False, signoff_strata: Sequence[str] = ("L99_signoff",)) -> AuditReport
```

The API should return structured failures so dev-std can consume Rack without
parsing terminal prose. If dev-std consumes `--format json`, Rack must publish a
versioned output contract such as `rack_audit_report.a0.json` /
`rack_audit_report.a0.schema.json`; the payload should carry stable identity
fields and the schema should be validated by Rack tests.

## dev-std Work

- Raise the `wn-rack` dependency once Rack native audit is published in a Rack release.
- Replace or wrap `src/wn_dev_std/test_governance.py` so dev-std calls Rack's native audit surface for the `tests` audit scope.
- Preserve dev-std-specific policy only where it is not Rack-owned, such as requiring configured test roots and mapping Rack audit results into dev-std audit output.
- Update `docs/design/audit-standard.html`, `docs/core/requirements/core-req-0002-test-suite-governance-audit.md`, and `docs/core/adr/core-adr-0002-test-suite-governance-audit.md` to state the ownership boundary.
- Update tests to verify delegation and upgrade guidance instead of duplicating Rack's full matrix.
- Record release notes for the new Rack minimum version and the migration from local bootstrap audit to Rack native audit.

## Verification

Rack verification should include its native audit unit tests, a Rack self-audit, and a dev-std audit run using the temporary latest-dev-std lane.

dev-std verification should include:

```bash
uv run rack run --all
uv run dev-std audit .
uv run python -m build
uv run twine check dist/*
uv run ruff check src tests
uv run ruff format --check .
uv run pyright
uv lock --check
```

Before closing this plan, run `uv run dev-std audit . --scope docs.plans` after the final log entry and keep the plan at external review until the cross-repo sequencing has been reviewed.

## Open Questions

- Should Rack expose both `rack audit` and `rack check`, or only `rack audit`
  with `check` left to downstream standards tools?
- Should strict inventory metadata checks be enabled by default or only under
  `--strict`?
- Should dev-std call Rack through Python API, subprocess CLI, or support both?
- Should dev-std retain a local fallback during development only, or should the
  next dev-std release require the published Rack version with native audit?
