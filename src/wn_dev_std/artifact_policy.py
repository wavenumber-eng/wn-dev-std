"""Shared artifact and release-governance policy constants."""

from __future__ import annotations

ARTIFACT_EXTENSIONS = {
    ".7z",
    ".a",
    ".bin",
    ".dll",
    ".dylib",
    ".elf",
    ".exe",
    ".hex",
    ".lib",
    ".msi",
    ".msix",
    ".nupkg",
    ".so",
    ".tar",
    ".tgz",
    ".wasm",
    ".whl",
    ".zip",
}
ARTIFACT_KINDS = {
    "app_package",
    "fixture_data",
    "generated_source",
    "oracle_artifact",
    "package_distribution",
    "public_reference_asset",
    "release_evidence",
    "runtime_binary",
    "runtime_wasm",
    "transient_output",
    "vendored_runtime_artifact",
}
RELEASE_KINDS = {
    "app_plugin",
    "github_release",
    "internal",
    "native_bundle",
    "object_store",
    "package_manager",
    "pypi",
    "wasm_bundle",
}
RUNTIME_ARTIFACT_KINDS = {"runtime_binary", "runtime_wasm", "vendored_runtime_artifact"}
