# Host Lifecycle And Navigation

The activity kernel owns stack semantics. A host adapter translates platform
events without moving browser or native APIs into the kernel.

`src/browser/browser-history.ts` records activity depth in browser history.
Browser back requests activity back. A dirty, in-flight, or blocked activity
rejects the request and the adapter restores the current history entry.
Programmatic pop also moves browser history without handling the same event
twice.

Forward navigation is not an instruction to resurrect an old JavaScript
object. A real routed application supplies `restoreForward` to decode a stable
route, query an authoritative snapshot, and create fresh activity input. If no
restorer exists, the reference returns to the current supported state.

`src/browser/browser-lifecycle.ts` uses the engine's cached leave state for the
synchronous `beforeunload` contract. Application close still calls the async
`requestExit` path when the host provides one. Native desktop hosts map the same
idea to window close, application quit, and suspend/resume events.

On frame disposal, the kernel aborts `context.signal`. Every request, stream,
timer, observer, and subscription must use that signal or implement explicit
disposal. After reconnection, streams query an authoritative snapshot before
applying incremental events.
