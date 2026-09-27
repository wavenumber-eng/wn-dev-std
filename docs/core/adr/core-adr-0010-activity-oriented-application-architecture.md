+++
type = "adr"
id = "core-adr-0010"
domain = "core"
status = "accepted"
title = "Workflow Applications Use Independent Activities"
created = "2026-09-27"
plan_refs = ["contract-and-application-standards"]
requirement_refs = ["core-req-0010"]
design_refs = [
  "docs/design/activity-application-standard.html",
  "docs/design/typescript-standard.html",
]
+++

# Workflow Applications Use Independent Activities

The decision is to standardize a small platform-neutral activity model
for Wavenumber applications that contain composable, stack-oriented workflows.
The reference implementation will use TypeScript and Lit, but the activity
kernel must not depend on Lit, the DOM, browser history, HTTP, CSS, or any
feature implementation.

An activity is an independently registered unit of behavior with typed input,
typed completion, owned transient state, and frame-scoped resources. Activities
compose through public definitions and push, pop, or switch operations. They do
not reach into sibling stores, rendered views, private state, or implementation
modules.

The model is loosely inspired by Android activities, intents, results, and its
back stack. It deliberately does not reproduce Android manifests, implicit
intent resolution, operating-system process ownership, or the full Android
lifecycle.

Registration belongs to an application composition root. Activities never
self-register and never use a global service locator. Hosts provide lifecycle,
history, rendering, and shutdown adapters while feature code remains portable.

The initial lifecycle semantics are:

- push retains the caller and opens a child with typed input;
- pop completes a non-root frame with a successful typed result;
- cancel completes a non-root frame with a distinct cancellation outcome;
- an unexpected failure is not a successful result and reaches the host error
  boundary after frame cleanup;
- pop or cancel on the root frame is invalid; application exit uses a host
  operation;
- switch is legal only for a root frame with no waiting caller;
- lifecycle transitions are serialized and non-reentrant;
- every created frame is disposed exactly once, including failed activation;
- frame disposal aborts owned requests, streams, timers, and subscriptions.

The activity architecture is a recommended reference for workflow-heavy
applications, not a requirement for static sites or every user interface.
Native desktop, embedded, terminal, and other hosts may implement the same
conceptual contract with different adapters.

Lit is the preferred greenfield web component authoring library when stateful
custom elements are warranted. It remains a recommendation rather than a
universal requirement.
