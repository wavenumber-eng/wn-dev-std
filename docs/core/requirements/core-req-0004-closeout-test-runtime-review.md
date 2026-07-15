+++
type = "requirement"
id = "core-req-0004"
domain = "core"
status = "implemented"
title = "Plan Audit Requires Test Runtime Impact Closeout"
created = "2026-07-15"
issue_refs = ["wavenumber-eng/wn-dev-std#19"]
adr_refs = ["core-adr-0004"]
design_refs = ["docs/core/design/closeout-test-runtime-impact-audit.html", "docs/design/audit-standard.html", "docs/test-strategy.html"]

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/plan_hygiene.py"

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/plan_mutation.py"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_003_plan_hygiene.py::test_docs_plans_audit_fails_when_external_review_does_not_depend_on_runtime_audit"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_003_plan_hygiene.py::test_docs_plans_audit_allows_project_specific_runtime_audit_step_title"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_003_plan_hygiene.py::test_docs_plans_audit_fails_plan_without_runtime_audit_exit_criterion"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_005_plan_mutation_commands.py::test_plan_create_writes_compliant_plan"
+++

# Plan Audit Requires Test Runtime Impact Closeout

The `docs.plans` audit must require active, pending, and blocked plans to
include a `test-runtime-impact-audit` step and a matching
`test-runtime-impact-audit` exit criterion. Generated plans use the recommended
titles `Audit new test runtime impact` and
`New tests are listed and runtime impact is reviewed`, but the audit treats the
ids as canonical so project-specific wording can remain readable.

The `external-review` step must depend on `test-runtime-impact-audit` so
independent review happens after the executor has listed new tests, reviewed
`docs/test-strategy.html`, and documented runtime impact or optimization
decisions for newly added tests.
