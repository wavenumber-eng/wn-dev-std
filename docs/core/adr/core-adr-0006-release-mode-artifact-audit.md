+++
type = "adr"
id = "core-adr-0006"
domain = "core"
status = "accepted"
title = "Release Artifact Inspection Uses Explicit Audit Mode"
created = "2026-07-18"
issue_refs = ["wavenumber-eng/wn-dev-std#13"]
plan_refs = ["issue-13-release-mode-artifact-audit"]
requirement_refs = ["core-req-0006"]
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
+++

# Release Artifact Inspection Uses Explicit Audit Mode

Default artifact and vendor governance remains source-controlled and
tracked-file-first. Normal developer checks do not fail merely because a local
build produced ignored files under `build/`, `output/`, `rack_results/`, or a
staging `dist/` tree.

The decision is to add an explicit audit mode rather than a separate release
command or a new top-level scope. The CLI shape is:

```bash
dev-std audit . --scope docs.release --mode release
```

The default mode continues to run the current catalog-shape and tracked-file
checks. In the first slice, release mode augments only the selected
`docs.release` governance check with local produced-file inspection. Other
scopes accept the mode but keep normal behavior. `dev-std audit . --mode
release` and `--scope all --mode release` run release payload inspection
because `docs.release` is selected by the full audit.

Release-channel artifact expectations live in `docs/governance/release.toml`
under each `[[channels]]` entry because required and optional payloads are
channel-specific. The nested table is
`[[channels.promoted_artifacts]]`. Each entry names the artifact identity,
required/optional policy, local path or bounded glob, artifact kind,
optional channel-relative sub-destination, and release metadata assertions such
as checksum, version, source commit, target triple, build profile, ABI/runtime
notes, and license references.

Date-versioned packages use bounded glob patterns such as
`dist/wn_dev_std-*.whl` for normal release outputs. Literal `version`,
`source_commit`, and `sha256` declarations are for pinned or already promoted
payloads. When declared, `version` is compared against the package version from
`pyproject.toml`, `source_commit` is prefix-matched against `git rev-parse
HEAD`, and `sha256` is computed from the matched file. A single `sha256`
declaration requires an exact path or a glob that resolves to exactly one file.

Default release governance shape-validates `[[channels.promoted_artifacts]]`
without reading payload files. That catches bad ids, unsupported artifact
kinds, non-boolean `required` values, path escapes, unbounded patterns, and bad
license refs during normal development.

Release mode inspects only configured promoted artifact roots and files. It
fails required missing payloads, uncataloged promoted payloads inside configured
release roots, stale declared checksums, mismatched version or source commit
metadata, invalid path escapes, and missing required metadata for native or
WASM bundles. It does not publish, upload, sign, or mutate artifacts.
Missing-required and metadata checks are evaluated per channel. Uncataloged
payload detection is evaluated once against the catalog-wide promoted-artifact
pattern set so PyPI, GitHub Release, and other channels can share a staging
root such as `dist/` without flagging each other's declared payloads.

Promoted roots are derived from the static directory prefix before the first
wildcard in a declared path or pattern. Exact file declarations use their parent
directory. File matching uses repository-relative POSIX paths with the same
`fnmatch` semantics as existing artifact catalog coverage.

Workspace roots remain aggregation boundaries. A workspace release-mode audit
runs member package release checks, with each member resolving its own release
catalog and artifact paths relative to the member root.

This shape keeps routine edit-loop audits fast while giving release signoff a
strict path for actual payload evidence.
