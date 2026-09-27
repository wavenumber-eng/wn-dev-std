# State Management

Use the narrowest owner:

| State | Owner |
| --- | --- |
| Draft fields, selection, validation, local progress | Activity frame |
| State shared within one feature | Feature store |
| Header, panels, overlays, background | Shell |
| Identity, capabilities, connectivity, preferences | Application session |
| Saved records and authoritative snapshots | Backend/domain |

Pushing a child retains the caller frame and its state. Returning a result is
the normal way to communicate with the caller. Do not promote transient state
to a global store merely to cross an activity boundary.

Promote state only when its lifetime and ownership genuinely broaden. Record
the reason near the promoted store or service.

Use these questions in order:

1. Does the value exist only while one activity frame is on the stack? Keep it
   on that activity.
2. Must sibling activities in one feature share it across separate frames?
   Inject a feature-scoped store.
3. Does the shell need it regardless of the active workflow? It may be shell
   state.
4. Does the entire application need one authoritative value, such as identity
   or connectivity? It may be session state.
5. Is the value durable or shared with another process? The backend/domain is
   authoritative; keep only a client-side snapshot and resynchronization rule.

Activity A must not reach into Activity B's fields, store, view, or DOM. A may
import B's public definition, push B with input, and consume B's completed or
cancelled outcome. That narrow result channel prevents workflow "tentacles"
and keeps activity composition usable in web, native desktop, and other hosts.

Leave state is separate from stored data:

- `clean`: host back, root switch, or exit may proceed;
- `dirty`: unsaved user-owned state needs confirmation or an explicit action;
- `in-flight`: validation or commit is underway and cancellation policy must be explicit;
- `blocked`: the workflow cannot leave through implicit back yet.

Explicit completion or cancellation remains an activity action. Host-initiated
back and shutdown consult leave state first.
