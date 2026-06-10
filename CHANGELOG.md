# Changelog

## 2026.6.10

- Allow local root `.env` files to pass `wn-dev-std check` only when Git reports
  them as untracked and ignored.
- Require C/C++ profiles to expose a Lizard-based native complexity gate under
  `tests/`.

## 2026.6.9

- Add the C/C++ fixed-width integer spelling rule to the `cpp-library`
  standard.
- Require C/C++ profiles to configure clang-tidy `google-runtime-int` as an
  error so owned code uses `std::int32_t`, `std::uint32_t`, `std::int64_t`, and
  `std::uint64_t` instead of `short`, `long`, or `long long`.

## 2026.6.7

- Codify HTML design-doc status markers with `draft`, `proposal`,
  `accepted`, and `superseded` states.
- Add a `wn-dev-std check` design-doc status gate that fails unmarked or
  invalid HTML design docs and reports draft/proposal docs for release signoff.
- Add the documentation standard design page and mark the reference design docs
  as accepted.

## 2026.6.4

- Add the initial working `wn-dev-std` Python package and CLI.
- Define the first strict Python development baseline with Rack, Ruff, Pyright,
  Hatchling, committed lockfiles, HTML design docs, JSON contracts, and
  release metadata signoff.
- Add the initial `cpp-library` profile with CMake, Ninja, clang-format,
  clang-tidy, CTest, warnings, sanitizer, ABI, and public/private header rules.
- Add the initial `python-native-wasm` mixed-mode profile modeled on Geometer
  for packages with CMake/C++, platform wheels, and WASM artifacts.
- Add the initial `csharp-app` profile for SDK-style C# application and
  host-plugin projects.
- Add `javascript-web-app` and `python-js-app` profiles for no-build browser
  apps, CSS/JS hygiene ratchets, and FastAPI-style Python-served frontends.
- Codify checked JavaScript/JSDoc, deterministic `node:test` coverage,
  CSS custom-property tokens, owned `wn-*` Web Components, JS-to-WASM wrapper
  tests, and simple command verbs for no-build web projects.
- Add configurable compatibility-pruning checks for retired environment
  variables, setup aliases, and other legacy surfaces.
- Add CI and model release-validation workflows for public Python packages,
  without publishing `wn-dev-std` itself to PyPI.
