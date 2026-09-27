# Theming

`src/theme/primitives.css` is the only ordinary home for raw palette, spacing,
radius, typography, shadow, layer, control-size, and motion values.
`semantic.css` maps primitives to appearance roles. Component and layout rules
consume governed tokens: semantic roles for appearance and primitive scale
tokens for structural rhythm or dimensions. `variants.css` proves that
appearance mappings can be replaced without editing features.

The light-DOM reference keeps styling in governed `.css` files. Strict checks
also parse the standard Lit `css` tagged-template form in `.ts` and `.tsx`, so
a Shadow DOM component can use normal Lit styles without bypassing token and
raw-literal checks. Aliased or dynamically constructed style mechanisms are
outside this lexical check and require an explicit project lint rule or
reviewed exception.

The public theme uses JetBrains Mono. Private Wavenumber applications may
replace the font-family primitive with licensed Berkeley Mono without changing
components.

The approved background snapshots live under `public/backgrounds/`. The shell
background service owns preloading, fallback, rotation, reduced-motion behavior,
and cleanup.

Native form controls participate in the active theme's `color-scheme`. Select
elements and their option popup also receive explicit semantic surface and text
colors so the default dark theme remains readable on platforms that partially
style native dropdowns. The alternate high-contrast theme switches the native
control scheme to light without changing feature CSS.
