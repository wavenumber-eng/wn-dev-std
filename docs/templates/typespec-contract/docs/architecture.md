# Contract Architecture

The TypeSpec sources under `contracts/`, rooted at `contracts/main.tsp`, are the
structural authority. TypeSpec emits JSON Schema and OpenAPI; OpenAPI then
drives the generated TypeScript declaration. Node and Python consume the same
JSON fixtures independently.

Dependency direction:

`TypeSpec -> JSON Schema/OpenAPI -> generated language views -> handwritten consumers`

Generated code does not flow back into TypeSpec. Handwritten domain behavior
does not belong in generated files.
