# Bazel C++ Starter

Source of truth: `docs/design/cpp-standard.html`.

Copy these files into a new native project, replace the module and target
metadata, select and pin a maintained compile-database rule or aspect, and
merge the Rack subtests into `tests/rack.toml`.

`MODULE.bazel.lock` is intentionally not supplied as a fake starter file: its
content must be generated from the project's actual module graph. After
dependencies are declared, generate it with the pinned Bazel version by running
`bazel mod deps --lockfile_mode=update`. Commit that generated lockfile for
local and CI reproducibility.
Bazel output trees are transient and must not be committed.
