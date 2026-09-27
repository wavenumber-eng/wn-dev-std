+++
type = "requirement"
id = "core-req-0011"
domain = "core"
status = "implemented"
title = "Application Clients Centralize Transport Mechanics"
created = "2026-09-27"
plan_refs = ["contract-and-application-standards"]
adr_refs = ["core-adr-0011"]
design_refs = ["docs/design/backend-client-standard.html"]

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/backend_standard_data.py"

[[implementation_refs]]
kind = "local_file"
target = "src/wn_dev_std/application_policy.py"

[[implementation_refs]]
kind = "local_file"
target = "docs/templates/web/lit-activity/src/transport/http-transport.ts"

[[implementation_refs]]
kind = "local_file"
target = "docs/templates/web/lit-activity/src/features/projects/project-client.ts"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L0_foundation/test_L0_026_application_policy.py::test_network_primitives_belong_to_transport_root"

[[verification_refs]]
kind = "local_pytest"
target = "tests/L99_signoff/test_L99_006_templates.py::test_copy_owned_templates_pass_clean_signoff"
+++

# Application Clients Centralize Transport Mechanics

Applications that declare backend-integration governance must centralize raw
HTTP, SSE, WebSocket, polling, URL, authentication, decoding, retry, and
protocol-version mechanics in declared transport roots.

Feature code must access backends through semantic clients. Stores may own
feature state, workflows may compose operations, and components may report
intent, but those layers must not construct raw transports.

The standard and reference must document transport selection, normalized error
handling, deadlines, cancellation, retry and idempotency ownership,
reconnection, backoff, heartbeat, backpressure, snapshots, event identity,
ordering, correlation, resynchronization, terminal behavior, and local-loopback
security.

Structural audit must validate declared boundaries and signoff wiring without
executing arbitrary commands. TypeScript-aware lint and executable tests retain
ownership of source-level import and protocol behavior.
