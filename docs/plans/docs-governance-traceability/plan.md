+++
type = "plan"
id = "docs-governance-traceability"
status = "active"
created = "2026-07-02"
issue_refs = ["wavenumber-eng/wn-dev-std#9"]

[[steps]]
id = "contract"
title = "Define ADR, requirement, design-doc, and traceability governance contract"
status = "active"

[[steps]]
id = "cli-audit"
title = "Implement scoped audit commands for durable governance docs"
status = "pending"
depends_on = ["contract"]

[[steps]]
id = "traceability"
title = "Implement typed local and external reference validation"
status = "pending"
depends_on = ["contract"]

[[steps]]
id = "generated-docs"
title = "Define generated HTML expectations for ADRs and requirements"
status = "pending"
depends_on = ["contract"]

[[steps]]
id = "proving-target"
title = "Use a data_models-style fixture to prove useful failure signals"
status = "pending"
depends_on = ["cli-audit", "traceability"]

[[steps]]
id = "signoff-guidance"
title = "Document signoff integration and staged adoption guidance"
status = "pending"
depends_on = ["cli-audit", "traceability", "generated-docs"]

[[exit_criteria]]
id = "contract-docs"
title = "Signed-off dev-std design docs describe ADR, requirement, design-doc, and traceability governance"
status = "pending"

[[exit_criteria]]
id = "adr-audit"
title = "Audit can validate ADR metadata, status, domain/id/filename consistency, and stale active-plan language"
status = "pending"

[[exit_criteria]]
id = "requirements-audit"
title = "Audit can validate requirement metadata, status, verification refs, and implementation/test traceability"
status = "pending"

[[exit_criteria]]
id = "design-link-audit"
title = "Audit can validate design-doc links, generated HTML links, and stale raw-source links where prohibited"
status = "pending"

[[exit_criteria]]
id = "external-refs"
title = "Typed external refs can represent tests and implementation artifacts in sibling repos or other languages"
status = "pending"

[[exit_criteria]]
id = "data-models-fixture"
title = "A data_models-style proving fixture produces expected failures for stale ADRs, missing verification, bad links, and incomplete external refs"
status = "pending"

[[exit_criteria]]
id = "signoff-integration"
title = "Documentation shows how existing repos can add the checks in signoff without requiring immediate global conversion"
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

## Adoption Boundary

This plan must not force an immediate conversion of every existing repo. It should provide useful failure reports and staged integration guidance so a repo can opt into checks by scope.

Toolz/data_models should be used as a realistic proving target, but broad data_models cleanup belongs in follow-up toolz plans after this dev-std capability exists.
