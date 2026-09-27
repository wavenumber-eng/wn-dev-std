+++
type = "requirement"
id = "core-req-0010"
domain = "core"
status = "implemented"
title = "Activity Applications Preserve Workflow Boundaries"
created = "2026-09-27"
plan_refs = ["contract-and-application-standards"]
adr_refs = ["core-adr-0010"]
design_refs = [
  "docs/design/activity-application-standard.html",
  "docs/design/typescript-standard.html",
]

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/activity_standard_data.py"

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/application_policy.py"

[[implementation_refs]]
kind = "local_file"
target = "docs/templates/web/lit-activity/src/activity/engine.ts"

[[implementation_refs]]
kind = "local_file"
target = "docs/templates/web/lit-activity/src/application/create-application.ts"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_026_application_policy.py::test_application_capability_passes_for_canonical_layout"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_026_application_policy.py::test_activity_kernel_must_remain_rendering_independent"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L99_signoff/test_L99_006_templates.py::test_copy_owned_templates_pass_clean_signoff"
+++

# Activity Applications Preserve Workflow Boundaries

The canonical application reference must define a rendering-independent
activity kernel whose public workflow contract is equivalent to
`Activity<Input, Output>` with explicit completion, cancellation, failure,
leave, and disposal semantics.

Activity definitions may be imported across features. Activity
implementations, stores, rendered views, and private state must not be imported
by sibling features. A composition root must register definitions with
factories and inject shared capabilities.

The reference must demonstrate typed push, pop, and switch workflows; retained
caller state; nested result return; dirty and in-flight leave decisions;
browser back/forward handling; application shutdown; frame cancellation; and
exactly-once disposal.

State guidance must distinguish:

- activity-local transient state;
- frame-owned resources and cancellation;
- feature state shared by activities within one feature;
- shell state;
- session and connectivity state;
- durable domain state.

State may be promoted only when its ownership genuinely broadens. The
application must not use one global store as a default substitute for activity
inputs, outputs, and local state.

Network protocol construction must be centralized outside activities, stores,
and UI components. Generated contract projections own wire shapes, shared
transports own protocol mechanics, feature clients own semantic operations,
stores own feature state, activities compose workflows, and components render
state and report user intent.

The Lit reference must separate the activity kernel, Lit host, browser
adapters, composition root, feature implementations, shell profiles, and theme
system. A second neutral host or test application must prove that the activity
kernel is not browser-bound.

The template documentation must let a developer or coding agent create and
register an activity without studying ALX or another product repository.
