"""Centralized backend-client integration standard data."""

from __future__ import annotations

BACKEND_INTEGRATION_RULE_ITEMS = (
    (
        "client.layers",
        "contracts transports feature clients stores workflows views",
        "Keep wire shapes, protocol mechanics, semantic operations, state, and UI intent separate.",
    ),
    (
        "client.centralization",
        "no raw network construction in features",
        "Centralize URLs, credentials, headers, decoding, retries, streams, and sockets.",
    ),
    (
        "transport.http",
        "finite commands and queries",
        "Use request/response semantics as the default for bounded work.",
    ),
    (
        "transport.sse",
        "server-to-client progress and event streams",
        "Prefer a reconnectable one-way stream when the client does not send stream messages.",
    ),
    (
        "transport.websocket",
        "genuinely bidirectional low-latency protocols",
        "Accept the lifecycle cost only when both peers need ongoing messages.",
    ),
    (
        "transport.polling",
        "simple latency-tolerant updates",
        "Keep infrequent status refreshes simpler than a persistent stream.",
    ),
    (
        "stream.recovery",
        "authoritative snapshot plus resumable events",
        "Define identity, ordering, correlation, backoff, heartbeat, and resynchronization.",
    ),
    (
        "request.safety",
        "deadlines cancellation retry and idempotency",
        "Make ownership of failure and repeated commands explicit.",
    ),
    (
        "loopback.security",
        "explicit origin authentication and CSRF posture",
        "Local HTTP still crosses a browser trust boundary and must not rely on locality alone.",
    ),
    (
        "portability",
        "application capabilities hide transport",
        "Allow HTTP, IPC, native, local-loopback, and cloud implementations behind one client API.",
    ),
)

BACKEND_INTEGRATION_REQUIRED_DOCS = ("docs/design/backend-client-standard.html",)
