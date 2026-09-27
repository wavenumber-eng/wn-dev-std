+++
type = "adr"
id = "core-adr-0011"
domain = "core"
status = "accepted"
title = "Backend Access Uses Centralized Semantic Clients"
created = "2026-09-27"
plan_refs = ["contract-and-application-standards"]
requirement_refs = ["core-req-0011"]
design_refs = ["docs/design/backend-client-standard.html"]
+++

# Backend Access Uses Centralized Semantic Clients

The decision is to separate generated wire contracts, shared transport
mechanics, feature-scoped semantic clients, stores, workflows, and rendered
views. Raw URL construction, authentication headers, fetch calls, EventSource,
and WebSocket construction do not belong in feature workflows or UI code.

This decision is independent of the activity architecture. Activity-based
applications consume semantic clients, but services, CLIs, native applications,
and other clients can use the same layering without adopting activities.

HTTP is the default for bounded commands and queries. SSE is preferred for
server-to-client progress or event streams. WebSockets are reserved for
genuinely bidirectional or low-latency protocols. Polling remains appropriate
for simple, infrequent, latency-tolerant updates.

Persistent streams supplement rather than replace authoritative queries. A
reconnectable protocol defines snapshots, event identity, ordering,
correlation, version negotiation, resynchronization, backoff, heartbeat,
backpressure, terminal behavior, and cancellation.

Local-loopback HTTP remains a security boundary. Its design explicitly covers
allowed origins, authentication or capability tokens, CSRF, port discovery,
protocol versions, and lifecycle ownership.
