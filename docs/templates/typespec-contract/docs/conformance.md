# Conformance Vectors

`fixtures/catalog-snapshot.valid.json` must be accepted and
`fixtures/catalog-snapshot.invalid.json` must be rejected by both the Node/Ajv
and Python/jsonschema consumers.

Add vectors when a compatibility-visible rule changes. Keep expected rejection
specific enough that a permissive or wrong schema cannot pass accidentally.
