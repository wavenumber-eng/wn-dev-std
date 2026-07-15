+++
type = "adr"
id = "core-adr-0004"
domain = "core"
status = "accepted"
title = "Plan Closeout Requires Test Runtime Review"
created = "2026-07-15"
issue_refs = ["wavenumber-eng/wn-dev-std#19"]
requirement_refs = ["core-req-0004"]
design_refs = ["docs/core/design/closeout-test-runtime-impact-audit.html", "docs/design/audit-standard.html", "docs/test-strategy.html"]

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/plan_hygiene.py"
+++

# Plan Closeout Requires Test Runtime Review

Active plans must include a `test-runtime-impact-audit` closeout step before
external review. The step records the executor's review of new or changed tests,
Rack manifest changes, observed runtime impact, optimization efforts, and
slower-lane decisions for tests that are too expensive for the normal edit loop.

This check is structural rather than a timing benchmark. Dev-std can require
the plan step, exit criterion, and external-review dependency consistently. The
executor and reviewer are responsible for using the step log to document the
actual test list, timing evidence, and optimization judgment for the repository.
