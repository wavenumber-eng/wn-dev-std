# Backend Integration

Generated contracts own wire shapes. Shared transports own protocol mechanics.
Feature clients expose semantic operations. Stores own feature state. Activities
compose workflows. Components render and report intent.

This template's `src/contracts/generated/project-service.ts` is a clearly
marked compile-ready fixture. Replace it with a generated, freshness-checked
TypeScript projection from a TypeSpec contract package before using a real API.
Feature clients import through `src/contracts/index.ts`; they do not declare
parallel wire interfaces.

Use HTTP for finite commands and queries, SSE for server-to-client progress or
events, WebSockets for bidirectional or latency-sensitive protocols, and polling
for infrequent latency-tolerant status.

Centralize normalized errors, URLs, credentials, deadlines, cancellation,
retry/idempotency, reconnect/backoff, heartbeat, backpressure, versions, and
loopback origin/authentication/CSRF policy. Reconnectable streams need an
authoritative snapshot and resynchronization path.
