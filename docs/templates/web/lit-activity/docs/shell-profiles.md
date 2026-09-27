# Shell Profiles

The shell owns global regions. The composition/host selects one of these
profiles; an activity never manipulates shell elements directly:

- `workspace`: header, root navigation, content, status notifications, and background;
- `focused`: compact header and content with distractions hidden;
- `background-only`: content over ambient background without chrome;
- `bare`: content only, useful for embedded or utility flows.

Add a profile in `src/shell/shell-profile.ts`, update shell rendering tests, and keep
feature controllers free of shell element references.

Activity definitions request a profile by name. The host validates that name
and applies it to the active frame; the selector in this reference is a
developer override for previewing all profiles. `background-only` and `bare`
render no header or status chrome, while `bare` also disables the ambient
background. When a developer override hides the header, the reference keeps a
small shell-preview recovery control visible. It can restore the activity's
requested profile, so previewing a chrome-free profile cannot strand the
reviewer. This control is preview tooling, not part of a production
`background-only` or `bare` profile; production activities using those
profiles must provide their own visible completion or cancellation path.
