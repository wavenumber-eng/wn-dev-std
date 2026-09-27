+++
type = "requirement"
id = "core-req-0012"
domain = "core"
status = "implemented"
title = "Lit Web Applications Isolate Shell And Theme Policy"
created = "2026-09-27"
plan_refs = ["contract-and-application-standards"]
adr_refs = ["core-adr-0012"]
design_refs = [
  "docs/design/web-application-standard.html",
  "docs/design/typescript-standard.html",
]

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/web_application_standard_data.py"

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/application_policy.py"

[[implementation_refs]]
kind = "local_file"
target = "docs/templates/web/lit-activity/src/shell/reference-app.ts"

[[implementation_refs]]
kind = "local_file"
target = "docs/templates/web/lit-activity/src/theme/primitives.css"

[[implementation_refs]]
kind = "local_file"
target = "docs/templates/web/lit-activity/public/backgrounds/manifest.json"

[[implementation_refs]]
kind = "local_file"
target = "docs/templates/web/lit-activity/public/fonts/manifest.json"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_026_application_policy.py::test_strict_design_language_rejects_raw_feature_literals"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_026_application_policy.py::test_design_language_accepts_narrow_inline_exception"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L99_signoff/test_L99_006_templates.py::test_copy_owned_templates_pass_clean_signoff"
+++

# Lit Web Applications Isolate Shell And Theme Policy

The canonical web template must use TypeScript and Lit while preserving native
semantic controls and a documented Shadow DOM or light DOM policy.

Shell profiles must own global regions and background behavior. Activities and
features may select profiles but must not manipulate shell implementation
details directly.

Theme files must separate primitive values, semantic roles, component rules,
layout rules, and variants. Feature styles must consume theme roles for curated
design-bearing properties. Greenfield mode is strict; existing projects may
declare a reviewed ratchet with scope, review policy, and removal trigger.
Inline design-literal exceptions require a non-empty rationale.

The public template must use approved Wavenumber background snapshots with
source, redistribution authorization, checksums, release inclusion, and update
policy. It must use JetBrains Mono and include its OFL-1.1 license. It must not
redistribute Berkeley Mono or product-specific logos.

Background rotation must preload images, retain a solid fallback, clean up
timers, preserve contrast, honor reduced motion, and support profile or user
disablement.
