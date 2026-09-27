+++
type = "adr"
id = "core-adr-0012"
domain = "core"
status = "accepted"
title = "Lit Applications Separate Shell And Design Language"
created = "2026-09-27"
plan_refs = ["contract-and-application-standards"]
requirement_refs = ["core-req-0012"]
design_refs = [
  "docs/design/web-application-standard.html",
  "docs/design/typescript-standard.html",
]
+++

# Lit Applications Separate Shell And Design Language

The decision is to recommend Lit for new TypeScript browser applications that
need reusable stateful custom elements, lifecycle, templating, or stable
component contracts. Native semantic HTML remains the default for ordinary
controls, and documented alternatives remain valid.

The application shell owns global navigation, headers, panels, overlays,
notifications, backgrounds, and layout profiles. Feature workflows request a
named shell profile instead of manipulating global regions.

Theme primitives and semantic tokens own colors, spacing, radii, typography,
shadows, layers, control dimensions, and motion. Feature styles consume those
roles. Strict greenfield checks target a curated set of design-bearing CSS
properties and do not reject zero, percentages, unitless values, runtime
geometry, data visualization, currentColor, transparent, inheritance, or
reviewed exceptions.

The canonical public theme uses the approved Wavenumber dark industrial
language, gold accent, square zero-radius controls, compact density, panels, and
rotating backgrounds. It uses JetBrains Mono under OFL-1.1 with a system
monospace fallback. Berkeley Mono remains a private licensed substitution made
through typography tokens and is not redistributed.
