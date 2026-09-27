"""Platform-neutral activity application standard data."""

from __future__ import annotations

ACTIVITY_APPLICATION_RULE_ITEMS = (
    (
        "activity.contract",
        "Activity<Input, Output> with explicit completion",
        "Make independent workflow inputs, results, cancellation, and failures reviewable.",
    ),
    (
        "activity.navigation",
        "typed push pop cancel and root switch",
        "Compose nested work without sibling implementation dependencies or global state.",
    ),
    (
        "activity.registration",
        "composition-root factories",
        "Activities never self-register or discover dependencies through a global locator.",
    ),
    (
        "activity.isolation",
        "public definitions only across features",
        "Keep implementations, stores, views, and private state free of cross-feature tentacles.",
    ),
    (
        "activity.lifecycle",
        "serialized transitions and exactly-once disposal",
        "Make initialization, activation, leave policy, cancellation, and cleanup deterministic.",
    ),
    (
        "activity.state",
        "local first with explicit promotion",
        "Reserve global state for genuine session, capability, connectivity, and preference data.",
    ),
    (
        "activity.portability",
        "rendering-independent kernel plus host adapters",
        "Allow web, native desktop, embedded, terminal, and test hosts to share the model.",
    ),
    (
        "web.lit",
        "preferred for stateful TypeScript web components",
        "Use a small standards-based component layer when lifecycle and reuse justify it.",
    ),
    (
        "web.shell",
        "named shell profiles outside activities",
        "Keep headers, panels, overlays, navigation, and backgrounds under shell ownership.",
    ),
    (
        "web.theme",
        "swappable semantic tokens",
        "Keep feature components independent of hard-coded design language values.",
    ),
)

ACTIVITY_APPLICATION_REQUIRED_DOCS = (
    "docs/design/activity-application-standard.html",
    "docs/design/typescript-standard.html",
)
