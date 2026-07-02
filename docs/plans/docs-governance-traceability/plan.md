+++
type = "plan"
id = "docs-governance-traceability"
status = "active"
created = "2026-07-02"
issue_refs = ["wavenumber-eng/wn-dev-std#9"]

[[steps]]
id = "contract"
title = "Define ADR, requirement, design-doc, and traceability governance contract"
status = "done"

[[steps]]
id = "cli-audit"
title = "Implement scoped audit commands for durable governance docs"
status = "done"
depends_on = ["contract"]

[[steps]]
id = "traceability"
title = "Implement typed local and external reference validation"
status = "done"
depends_on = ["contract"]

[[steps]]
id = "generated-docs"
title = "Define generated HTML expectations for ADRs and requirements"
status = "done"
depends_on = ["contract"]

[[steps]]
id = "proving-target"
title = "Use a data_models-style fixture to prove useful failure signals"
status = "done"
depends_on = ["cli-audit", "traceability"]

[[steps]]
id = "signoff-guidance"
title = "Document signoff integration and staged adoption guidance"
status = "done"
depends_on = ["cli-audit", "traceability", "generated-docs"]

[[steps]]
id = "inventory-commands"
title = "Add ADR and requirement inventory/read commands consistent with plan/log commands plus rogue legacy detection"
status = "done"
depends_on = ["cli-audit", "traceability"]

[[steps]]
id = "domain-registry"
title = "Add minimal docs domain registry and docs.domains audit scope"
status = "done"
depends_on = ["cli-audit", "traceability"]

[[steps]]
id = "governed-surfaces"
title = "Define governed surface, implementation ref, verification ref, fixture/data ref, and exception manifests"
status = "pending"
depends_on = ["domain-registry", "traceability"]

[[steps]]
id = "parity-evidence"
title = "Support cross-language parity and fixture/data coverage relationships for porting work"
status = "pending"
depends_on = ["governed-surfaces"]

[[steps]]
id = "rack-evidence-interface"
title = "Define optional Rack runtime evidence export/link contract for traceability audits"
status = "pending"
depends_on = ["governed-surfaces"]

[[steps]]
id = "marker-discovery"
title = "Prefer dev-std.toml root discovery while preserving wn-dev-std.toml compatibility"
status = "done"
depends_on = ["cli-audit"]

[[steps]]
id = "bootstrap-guidance"
title = "Document minimal bootstrap and generic signoff wiring for governance audits"
status = "pending"
depends_on = ["inventory-commands", "domain-registry", "marker-discovery"]

[[steps]]
id = "dev-std-marker"
title = "Prefer dev-std.toml as the package marker while preserving wn-dev-std.toml compatibility"
status = "done"
depends_on = ["marker-discovery"]

[[steps]]
id = "html-generation"
title = "Generate HTML pages for plans, logs, ADRs, and requirements with configurable output and style hooks"
status = "pending"
depends_on = ["inventory-commands", "domain-registry"]

[[steps]]
id = "review-release"
title = "Review behavior and decide whether to release this dev-std slice"
status = "active"
depends_on = ["generated-docs", "proving-target", "signoff-guidance", "inventory-commands", "domain-registry", "governed-surfaces", "parity-evidence", "rack-evidence-interface", "marker-discovery", "bootstrap-guidance", "dev-std-marker", "html-generation"]

[[steps]]
id = "external-review"
title = "Run data_models proving pass and obtain Altium Monkey C++ porting/governance review before release"
status = "pending"
depends_on = ["review-release"]

[[exit_criteria]]
id = "contract-docs"
title = "Signed-off dev-std design docs describe ADR, requirement, design-doc, and traceability governance"
status = "met"

[[exit_criteria]]
id = "adr-audit"
title = "Audit can validate ADR metadata, status, domain/id/filename consistency, and stale active-plan language"
status = "met"

[[exit_criteria]]
id = "requirements-audit"
title = "Audit can validate requirement metadata, status, verification refs, and implementation/test traceability"
status = "met"

[[exit_criteria]]
id = "design-link-audit"
title = "Audit can validate design-doc links, generated HTML links, and stale raw-source links where prohibited"
status = "met"

[[exit_criteria]]
id = "external-refs"
title = "Typed external refs can represent tests and implementation artifacts in sibling repos or other languages"
status = "met"

[[exit_criteria]]
id = "data-models-fixture"
title = "A data_models-style proving fixture produces expected failures for stale ADRs, missing verification, bad links, and incomplete external refs"
status = "met"

[[exit_criteria]]
id = "signoff-integration"
title = "Documentation shows how existing repos can add the checks in signoff without requiring immediate global conversion"
status = "met"

[[exit_criteria]]
id = "inventory-read-commands"
title = "ADR and requirement list/show commands match plan/log text and JSON inventory conventions"
status = "met"

[[exit_criteria]]
id = "plan-log-read-consistency"
title = "Plan/log/ADR/requirement list/show commands share consistent text and JSON output structure"
status = "met"

[[exit_criteria]]
id = "rogue-legacy-detection"
title = "ADR/requirement audits fail rogue or legacy-looking documents that lack compliant metadata"
status = "met"

[[exit_criteria]]
id = "domain-registry"
title = "docs.domains validates registered domains, purpose/status metadata, owned roots, and file-to-domain traceability without assuming language-specific layout"
status = "met"

[[exit_criteria]]
id = "domain-html"
title = "Each registered domain has generated or hand-authored HTML coverage with standard data tags, intent/status, source links, ADRs, requirements, and verification links"
status = "met"

[[exit_criteria]]
id = "domain-registry-tests"
title = "Domain registry tests cover missing domains, invalid ADR/requirement domain refs, missing domain HTML, unowned files under owned roots, optional multi-domain file groups, and ignored generated/vendor paths"
status = "met"

[[exit_criteria]]
id = "governed-surfaces"
title = "Governed surface manifests can declare public APIs, workflows, transforms, serializers, schemas, CLI commands, WASM endpoints, and other surfaces that require verification or exceptions"
status = "pending"

[[exit_criteria]]
id = "verification-fixtures"
title = "Verification refs can link governed surfaces to local or external tests, coverage modes, fixture/data refs, oracle/reference lanes, and sufficiency rationale"
status = "pending"

[[exit_criteria]]
id = "typed-exceptions"
title = "Exceptions are typed, issue-linked where appropriate, auditable, and distinguish accepted divergence from missing or deferred work"
status = "pending"

[[exit_criteria]]
id = "port-parity"
title = "Traceability model supports cross-language/source-to-target parity relationships, including exact parity, semantic parity, subset/superset fixture coverage, and accepted divergence"
status = "pending"

[[exit_criteria]]
id = "fixture-data-hygiene"
title = "Fixture/data refs distinguish registered fixtures, physical discovered data, ignored/generated/archived data, missing backing files, orphaned fixtures, and unused corpus files"
status = "pending"

[[exit_criteria]]
id = "rack-evidence-interface"
title = "Docs define an optional Rack evidence export/link interface for test ids, lanes, concerns, case ids, fixtures used, artifacts produced, results, and run metadata"
status = "pending"

[[exit_criteria]]
id = "minimal-bootstrap"
title = "Docs show the canonical minimal files and command sequence needed to enable governance audits in an existing repo"
status = "pending"

[[exit_criteria]]
id = "generic-signoff"
title = "Docs show a generic signoff invocation that surfaces governance failures without repo-specific custom code"
status = "pending"

[[exit_criteria]]
id = "dev-std-marker"
title = "Root discovery and docs prefer dev-std.toml while still accepting wn-dev-std.toml for existing repos"
status = "met"

[[exit_criteria]]
id = "html-generation"
title = "dev-std can generate HTML pages for plans, logs, ADRs, and requirements with data attributes, standard styles, configurable output roots, cross-links, and optional consumer CSS injection"
status = "pending"

[[exit_criteria]]
id = "html-generation-tests"
title = "HTML generation tests verify output paths, source metadata data-tags, escaped content, standard style linkage, cross-links, and custom CSS override/link injection"
status = "pending"

[[exit_criteria]]
id = "review-tests"
title = "Focused unit tests, full pytest, ruff, pyright, and scoped governance audits pass before review"
status = "pending"

[[exit_criteria]]
id = "data-models-proving"
title = "Governance audits are tested against toolz/data_models first and produce useful actionable signals before release"
status = "pending"

[[exit_criteria]]
id = "altium-monkey-cpp-review"
title = "Altium Monkey C++ porting/governance agent reviews the traceability, parity, and generated-report model before final commit/tag/release"
status = "pending"

[[exit_criteria]]
id = "review"
title = "User review is complete and release decision is made"
status = "pending"
+++

# Docs Governance Traceability

This plan extends `dev-std` from temporary plan/log hygiene into durable governance-document hygiene. The immediate target is a general audit surface for ADRs, requirements, design docs, links, and traceability so repositories can detect drift before it becomes manual archaeology.

The first proving target is a data_models-style fixture because that domain has known useful failure signals: stale ADR language, raw Markdown links from generated HTML, requirements without verification, missing or inconsistent generated documentation, and cross-repo test ownership.

## Intended Model

Plans remain temporary execution artifacts. Completed plans are removed after their durable output has landed in code, requirements, ADRs, design docs, generated docs, tests, or issues.

ADRs are durable decisions. Accepted ADRs should describe the standing decision and context, not open work for a named plan or release. Proposed ADRs may carry open questions, but those questions must be visible in metadata or audit output.

Requirements are durable obligations. Active or implemented requirements must have verification refs or an explicit unresolved signal that can be tracked.

Design docs describe the current shape of the system. Hand-authored HTML remains valid where it gives us structured `data-*` hooks, but generated browsing output should be linked from indexes instead of raw source files when the generated page exists.

Traceability refs must be typed enough for machines to validate shape and for agents to understand ownership without reading a large body of prose. Local refs should resolve. External refs should identify the repo, kind, and target even when the local checkout is not present.

## Initial CLI Shape

The plan should preserve the existing `audit` umbrella and add scoped checks incrementally:

- `dev-std audit docs.adrs`
- `dev-std audit docs.requirements`
- `dev-std audit docs.design`
- `dev-std audit docs.links`
- `dev-std audit docs.traceability`

The existing plan/log commands should remain focused on temporary execution artifacts. ADR and requirement read/list commands can be added later if the audit model proves useful.

ADR and requirement inventory commands should follow the same read-command
conventions as <code>plan list</code>, <code>plan show</code>,
<code>log list</code>, and <code>log show</code>: root discovery, catalog
compliance before read operations, human-readable text output by default, and
machine-readable JSON with a consistent top-level shape. The goal is one
predictable inventory surface across plans, logs, ADRs, and requirements.

## Adoption Boundary

This plan must not force an immediate conversion of every existing repo. It should provide useful failure reports and staged integration guidance so a repo can opt into checks by scope.

Toolz/data_models should be used as a realistic proving target, but broad data_models cleanup belongs in follow-up toolz plans after this dev-std capability exists.

## Bootstrap Goal

Existing repositories need a small, repeatable path to turn governance audits on.
The canonical bootstrap should document the minimum files and commands needed to
get useful failure signals without custom repo code. A repo should be able to add
 a `dev-std.toml` or `[tool.wn_dev_std]` marker, declare the relevant docs
roots and governance roots, then run a generic command such as:

```text
dev-std audit . --scope docs.plans --scope docs.adrs --scope docs.requirements --scope docs.traceability --scope docs.links --scope docs.domains
```

The initial adoption posture should prefer explicit failures and inventories over
silent permissiveness. Repos can then decide whether to fix immediately, add
tracked issues, or stage strict domain/source ownership checks after the minimal
registry is in place.

`dev-std.toml` is the preferred standalone marker for new packages.
`wn-dev-std.toml` remains a compatibility marker for existing repositories until
they migrate.

## Domain Registry Goal

The domain registry is a traceability tool, not a mandatory source tree shape.
It should let a package declare the domains it uses, the purpose and status of
each domain, the owned roots that are candidates for coverage checks, and the
file groups that associate files with one primary domain plus optional
supporting domains. Language and classification metadata are allowed but
freeform. The initial audit should be inclusion-first: only configured owned
roots are checked for unowned files, with explicit ignore patterns for generated,
vendor, transient, or build-output paths.

When a domain registry exists, ADR and requirement metadata must reference a
registered domain. Without a registry, ADR/requirement audits may fall back to
path-derived domains so small packages can adopt the basics before adding full
domain coverage.

Each registered domain should have a browseable HTML coverage page. The page may
be generated from the registry or hand-authored, but it must include standard
data attributes for domain id, status, source registry path, and generation
state. It should document domain purpose and status, list owned roots and file
groups, and link to source files, ADRs, requirements, verification refs,
implementation refs, and generated governance pages where available. Source file
links should be repo-relative by default and may use a configured source URL base
for GitHub/static-site output.

## Governed Surface And Evidence Goal

The Altium Monkey Python-to-C++ porting work shows that domain ownership is not
enough by itself. Mature projects also need a generic way to declare governed
surfaces: public API classes and methods, parser/serializer behavior, CLI
commands, WASM endpoints, transforms, importers/exporters, workflow behaviors,
file-format records, schemas, and generated contract surfaces. A governed
surface is something signoff expects to be verified or explicitly excepted.

The model should support source-to-test and test-to-source queries. A reviewer
should be able to ask what tests cover a surface, what fixture/data inputs those
tests use, which implementation lanes are covered, which requirements or ADRs
explain the behavior, and which exceptions remain. The reverse query should also
work: given a test or fixture, identify the surfaces and domains it verifies.

Implementation refs, verification refs, fixture/data refs, and exceptions should
be typed committed text manifests, not generated SQLite as the authored source of
truth. Generated SQLite, JSON, or HTML indexes are useful report artifacts, but
the reviewed contract should remain diffable in Git.

Verification refs should describe coverage mode, such as exact parity, semantic
parity, oracle comparison, roundtrip preservation, regression, smoke, static
audit, generated-doc validation, or schema validation. Fixture/data refs should
be first-class because port parity often depends more on which input surfaces
were tested than on line coverage. The model should distinguish declared fixture
intent from runtime-observed fixture use, and registered fixture catalogs from
physically discovered files.

Exceptions should be typed and auditable. Examples include not applicable,
python-only, native-only, WASM-only, covered elsewhere, deferred, accepted
divergence, and missing capability. Exceptions should carry rationale, owner or
tracking issue when appropriate, and review/expiration metadata when temporary.

## Port Parity Goal

The traceability model must support language-neutral porting work. It should
not assume Python/C++, same-basename tests, Altium strata, or a particular
source layout. It should support implementation lanes such as Python, C++,
WASM, JavaScript/TypeScript, Rust, CLI, or external tools through typed refs and
freeform language/runtime metadata.

For parity, a project should be able to state that implementation lane A and
implementation lane B must use equal, subset, superset, semantically equivalent,
or intentionally divergent fixture/data surfaces for a governed behavior. This
is the generic form behind the current Altium Monkey asset-alignment checks and
should be reusable by data_models and future ports.

## Rack Evidence Goal

`wn-dev-std` should own committed governance contracts and audits. `wn-rack`
should own runtime test evidence. The two need a stable interface so projects
can opt into stronger checks later. The minimum useful Rack evidence export or
link should include test id, runtime, lane/concerns, case id, fixture/data ids
used, artifact ids produced, result status, run id/timestamp, and whether the
evidence was declared, statically inferred, or runtime observed.

Initial dev-std audits can validate declared refs without requiring Rack runtime
evidence. A stricter future mode can verify that declared tests actually ran
over the required fixture/data sets.

## Proving And Review Gate

Before final release, the governance work should be exercised against
toolz/data_models first so we see real failures and confirm the output is useful
for cleanup planning. After that proving pass, the Altium Monkey C++ porting
agent should review the traceability, parity, fixture/data, and generated-report
model. That agent has current context on Python-to-C++ parity, private test
metadata, corpus fixture alignment, and the governance cleanup that will follow
in Altium Monkey. His signoff is an explicit release gate because the same
porting strategy should later apply to data_models, viz, pcb_cruncher, and other
multi-language or ported tools.

## Generated Governance HTML

`dev-std` should be able to project plan, log, ADR, and requirement Markdown
sources into HTML browse pages. The generated pages should include standard
`data-*` attributes for source path, governance type, id, domain, status, and
generation metadata so downstream audits and static sites can reason over them.

Output location and styling must be configurable. Consumers should be able to
choose an output root, link or copy the standard dev-std stylesheet, and inject
additional CSS links or inline style hooks for repo-specific presentation. The
data_models documentation style is the target direction, but dev-std should keep
the generator generic and allow projects to layer their own CSS without editing
generated files.

Generated governance pages should cross-link related artifacts from their
metadata. Plans should link attached logs and referenced issues. Logs should link
their owning plan. ADRs should link referenced requirements, design docs,
schemas, issues, superseding/superseded ADRs, and implementation evidence when
present. Requirements should link ADRs, verification refs, implementation refs,
design docs, schemas, issues, and related requirements. Cross-links should be
resolved to generated HTML pages when possible and fall back to clearly labeled
external or unresolved references when they cannot be resolved locally.
