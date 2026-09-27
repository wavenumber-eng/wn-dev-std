"""TypeSpec contract-governance standard data."""

from __future__ import annotations

TYPESPEC_CONTRACT_RULE_ITEMS = (
    (
        "authority",
        "TypeSpec owns cross-language and cross-process structure",
        "Keep APIs, events, configuration, commands, and durable payloads authoritative once.",
    ),
    (
        "scope",
        "cross-cutting contract units",
        "Contract governance composes with every project profile and does not depend on a UI.",
    ),
    (
        "structure-behavior",
        "generated structure plus handwritten behavior",
        "Generate data shape boilerplate while keeping effects and domain behavior explicit.",
    ),
    (
        "toolchain",
        "pinned compiler libraries and emitters",
        "Make contract generation reproducible across machines and releases.",
    ),
    (
        "projections",
        "generate only required consumer projections",
        "Avoid unused language output while proving every claimed projection with a consumer.",
    ),
    (
        "generated-ownership",
        "never hand-edit generated projections",
        "Keep TypeSpec as authority and document regeneration, freshness, and release inclusion.",
    ),
    (
        "compatibility",
        "versioned roots and stable discriminators",
        "Make durable evolution and variant identity reviewable across runtimes.",
    ),
    (
        "conformance",
        "shared vectors across independent consumers",
        "Catch projection drift with the same accepted and rejected payloads in multiple runtimes.",
    ),
    (
        "exceptions",
        "scoped rationale and review trigger",
        "Upstream authorities and lossy constructs must not create silent competing contracts.",
    ),
    (
        "signoff",
        "compile generate freshness consume conform",
        "Repository audit checks declarations while project signoff executes contract tooling.",
    ),
)

TYPESPEC_CONTRACT_REQUIRED_DOCS = (
    "docs/design/typespec-contract-standard.html",
    "docs/contracts/",
)
