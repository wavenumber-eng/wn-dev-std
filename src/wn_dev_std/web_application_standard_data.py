"""Preferred Lit web-application standard data."""

from __future__ import annotations

LIT_WEB_APPLICATION_RULE_ITEMS = (
    (
        "web.typescript",
        "TypeScript greenfield browser default",
        "Keep browser modules, events, state, and contracts statically reviewable.",
    ),
    (
        "web.lit",
        "preferred stateful component authoring",
        "Use standards-based custom elements with a small lifecycle and rendering layer.",
    ),
    (
        "web.html",
        "native semantic controls first",
        "Preserve accessibility and platform behavior before adding component abstraction.",
    ),
    (
        "web.dom-policy",
        "document Shadow DOM or light DOM",
        "Make style, composition, accessibility, and testing boundaries deliberate.",
    ),
    (
        "web.shell",
        "named profiles own global regions",
        "Keep navigation, headers, panels, overlays, and backgrounds outside features.",
    ),
    (
        "web.theme",
        "primitive and semantic tokens",
        "Allow design language changes without editing feature components.",
    ),
    (
        "web.css-policy",
        "curated design-bearing property enforcement",
        "Reject theme leakage without banning legitimate geometry and unitless values.",
    ),
    (
        "web.accessibility",
        "focus contrast motion and keyboard states",
        "Treat usable interaction states as part of the component contract.",
    ),
    (
        "web.backgrounds",
        "shell-owned preload fallback rotation and cleanup",
        "Keep ambient imagery reliable, optional, and compatible with reduced motion.",
    ),
    (
        "web.typography",
        "open public font plus swappable family token",
        "Keep public redistribution clean while private products can apply licensed fonts.",
    ),
)

LIT_WEB_APPLICATION_REQUIRED_DOCS = (
    "docs/design/web-application-standard.html",
    "docs/design/typescript-standard.html",
)
