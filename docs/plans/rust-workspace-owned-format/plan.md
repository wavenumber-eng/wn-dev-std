+++
type = "plan"
id = "rust-workspace-owned-format"
status = "active"
created = "2026-10-21"

[[steps]]
id = "work"
title = "Execute plan work"
status = "done"

[[steps]]
id = "design-doc-intent-audit"
title = "Audit design docs, ADRs, and requirements against implementation"
status = "done"
depends_on = ["work"]

[[steps]]
id = "test-runtime-impact-audit"
title = "Audit new test runtime impact"
status = "done"
depends_on = ["work"]

[[steps]]
id = "external-review"
title = "Obtain independent external review"
status = "done"
depends_on = ["work", "design-doc-intent-audit", "test-runtime-impact-audit"]

[[exit_criteria]]
id = "signoff"
title = "Focused signoff passes"
status = "met"

[[exit_criteria]]
id = "design-doc-intent-audit"
title = "Design docs, ADRs, and requirements match implementation"
status = "met"

[[exit_criteria]]
id = "test-runtime-impact-audit"
title = "New tests are listed and runtime impact is reviewed"
status = "met"

[[exit_criteria]]
id = "external-review"
title = "Independent external review is complete"
status = "met"

[[exit_criteria]]
id = "public-delivery"
title = "Separate public release approval and release CI/packaging complete"
status = "pending"

[[steps]]
id = "proof"
title = "Implement bounded workspace ownership and exact selector proof"
status = "done"

[[steps]]
id = "qualification"
title = "Qualify focused regression controls and independent review"
status = "done"

[[steps]]
id = "public-delivery"
title = "Run approved public release CI/packaging and publication"
status = "active"
+++

# Release bounded formatting coverage for explicitly owned Rust workspaces

Extend the existing owned-package formatter proof to a named root package and literal in-root workspace members, requiring one exact Cargo format command selecting every unique owned package. Preserve the canonical full-all lane, existing single-package behavior and all non-format gates. Refuse glob/excluded/redirected/virtual scope, extra manifests, undeclared internal dependency targets and incomplete or foreign selectors; the original candidate left external sibling manifests unread, superseded by the bounded identity check below. Scope: rust_format_policy.py, existing L0_028 tests, owned Rust standard and requirement/ADR wording. The source candidate needs independent review and Rack/static qualification before any separate version, public PR or release approval. Historical ownership issue: https://github.com/wavenumber-eng/wn-dev-std/issues/39; completed public squash is #40.

Owning issue: https://github.com/wavenumber-eng/wn-dev-std/issues/43.
The user approved the public fix and release on 2026-10-26. The existing reviewed
candidate rebased onto current main; full release qualification and publication
are underway for 2026.10.26. Fresh review identified an inherited external-package
workspace redirect gap. The coordinator approved bounded direct external Cargo
identity reads (256 manifests / 4 MiB aggregate / 1 MiB each) without external
dependency traversal or Cargo invocation. Governing docs, controls and release
notes now record that strengthened boundary. No published package or successful
release CI is claimed before actual verification.
