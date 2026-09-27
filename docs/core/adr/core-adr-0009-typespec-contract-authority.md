+++
type = "adr"
id = "core-adr-0009"
domain = "core"
status = "accepted"
title = "TypeSpec Is The Structural Contract Authority"
created = "2026-09-27"
plan_refs = ["contract-and-application-standards"]
requirement_refs = ["core-req-0009"]
design_refs = [
  "docs/design/typespec-contract-standard.html",
  "docs/design/json-contract-standard.html",
]
+++

# TypeSpec Is The Structural Contract Authority

The decision is to use TypeSpec as the central structural authority
for new Wavenumber-owned contracts that cross a language or process boundary.
This is a cross-cutting contract decision, not a web, GUI, frontend, or
application-framework decision.

The same authority model applies to local and cloud APIs, events, worker
messages, configuration files, command envelopes, persistent interchange
objects, native applications, CLIs, libraries, and data pipelines. A project
does not need a user interface to adopt or require TypeSpec.

Generated JSON Schema, OpenAPI, Python, Rust, TypeScript, and other projections
are derived views of the TypeSpec authority. They must not become separately
edited definitions. Projects generate only the projections their real
consumers need and provide evidence that those consumers compile, validate, or
run conformance vectors against them.

TypeSpec owns structural vocabulary: named types, fields, optionality, unions,
discriminators, operations, status shapes, and compatible evolution.
Handwritten code retains ownership of behavior, effects, transactions,
resolution, orchestration, and invariants that are not faithfully structural.

The policy is independent of primary-language profiles. It will be activated
through declared contract units in dev-std configuration, allowing one
repository to own multiple contract packages and language consumers without
creating profiles for every language combination.

Upstream-owned formats remain authoritative upstream. A Wavenumber project may
generate adapters, validators, or local views for such a format, but it must not
silently establish a competing TypeSpec authority.

The first implementation will publish a projection support matrix. It will not
claim that a Python, Rust, or TypeScript emitter is supported until that emitter
is independently packageable, reproducible, and exercised by consumer evidence.

Version-matched templates should be obtainable from the installed governance
tool, not only from an unversioned checkout. The intended distribution contract
is packaged template resources exposed by a copy command, with the source tree
remaining directly browsable at the corresponding release tag.
