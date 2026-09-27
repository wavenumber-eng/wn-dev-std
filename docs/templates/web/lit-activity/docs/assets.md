# Public Asset Provenance

The background files are approved Wavenumber-standard reference assets copied
from `install/assets/branding/backgrounds` with explicit redistribution
authorization for this public template. Checksums are recorded in
`public/backgrounds/manifest.json`. These are versioned snapshots; Install
remains the live editable branding authority. Stock-licensed images are
excluded because a reusable public template requires explicit raw asset
redistribution rights, not only product-use rights.

Run `npm run sanitize:assets` after adding approved JPEGs to remove APP1
EXIF/XMP and APP13 Photoshop/IPTC metadata while preserving image data and ICC
profiles. `npm run audit:assets` is non-mutating and release-blocking. Recompute
the manifest checksums after sanitization.

JetBrains Mono is distributed under SIL Open Font License 1.1. The template
includes the license and a pinned WOFF2 snapshot with checksum. Berkeley Mono is
not included because its Wavenumber license is private.
