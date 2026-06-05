# Changelog

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
- Add CI and model release-validation workflows for public Python packages,
  without publishing `wn-dev-std` itself to PyPI.
