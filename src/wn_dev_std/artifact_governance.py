"""Artifact, vendor, and release governance checks."""

from __future__ import annotations

import fnmatch
import subprocess
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from wn_dev_std.root_discovery import load_pyproject, load_standard_config


@dataclass(frozen=True, slots=True)
class GovernancePolicyReport:
    """Artifact/vendor/release governance check result."""

    passed: bool
    detail: str


DEFAULT_ARTIFACTS_PATH = Path("docs/governance/artifacts.toml")
DEFAULT_VENDORS_PATH = Path("docs/governance/vendors.toml")
DEFAULT_RELEASE_PATH = Path("docs/governance/release.toml")

VENDOR_ROOTS = ("vendor", "third_party", "third-party")
TRANSIENT_ROOTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "build-wasm",
    "node_modules",
    "output",
    "rack_results",
    "temp",
}
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
VENDOR_KINDS = {"source", "generated_source", "binary", "runtime_asset", "archive"}
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


def check_vendor_governance_policy(root: Path) -> GovernancePolicyReport:
    """Check vendored-code catalog coverage."""
    resolved_root = root.resolve()
    catalog_path = _configured_catalog_path(resolved_root, "vendors", DEFAULT_VENDORS_PATH)
    candidates = _vendor_candidates(resolved_root)
    if not catalog_path.exists():
        if candidates:
            return _missing_catalog_report("vendor", resolved_root, catalog_path, candidates)
        return GovernancePolicyReport(True, "no vendored source candidates found")

    failures: list[str] = []
    payload = _load_toml(catalog_path, failures)
    vendors = _table_array(payload.get("vendors"))
    path_patterns = _validate_vendor_entries(resolved_root, catalog_path, vendors, failures)
    _validate_candidates_covered("vendor", candidates, path_patterns, failures)
    if failures:
        return _failure("vendor", failures)
    return GovernancePolicyReport(True, f"{len(vendors)} vendor entr(y/ies) passed governance")


def _validate_vendor_entries(
    root: Path,
    catalog_path: Path,
    vendors: Sequence[Mapping[str, object]],
    failures: list[str],
) -> tuple[str, ...]:
    if not vendors:
        failures.append(f"{_rel(root, catalog_path)}: missing [[vendors]] entries")
        return ()
    seen_ids: set[str] = set()
    path_patterns: list[str] = []
    for index, vendor in enumerate(vendors, start=1):
        label = f"{_rel(root, catalog_path)}: vendors[{index}]"
        vendor_id = _required_string(vendor, "id", label, failures)
        _validate_unique_id(label, vendor_id, seen_ids, failures)
        kind = _required_string(vendor, "kind", label, failures)
        if kind and kind not in VENDOR_KINDS:
            failures.append(f"{label}: unknown kind {kind!r}")
        for key in ("name", "upstream_url", "version", "license", "owner", "update_command"):
            _required_string(vendor, key, label, failures)
        patterns = _required_string_array(vendor, "paths", label, failures)
        consumers = _required_string_array(vendor, "consumers", label, failures)
        if not consumers:
            failures.append(f"{label}: consumers must not be empty")
        _validate_patterns_within_root(root, label, patterns, failures)
        path_patterns.extend(patterns)
    return tuple(path_patterns)


def check_artifact_governance_policy(root: Path) -> GovernancePolicyReport:
    """Check artifact catalog coverage for tracked artifact-like files."""
    resolved_root = root.resolve()
    catalog_path = _configured_catalog_path(resolved_root, "artifacts", DEFAULT_ARTIFACTS_PATH)
    candidates = _artifact_candidates(resolved_root)
    if not catalog_path.exists():
        if candidates:
            return _missing_catalog_report("artifact", resolved_root, catalog_path, candidates)
        return GovernancePolicyReport(True, "no tracked artifact candidates found")

    failures: list[str] = []
    payload = _load_toml(catalog_path, failures)
    artifacts = _table_array(payload.get("artifacts"))
    path_patterns = _validate_artifact_entries(resolved_root, catalog_path, artifacts, failures)
    _validate_candidates_covered("artifact", candidates, path_patterns, failures)
    if failures:
        return _failure("artifact", failures)
    return GovernancePolicyReport(True, f"{len(artifacts)} artifact entr(y/ies) passed governance")


def _validate_artifact_entries(
    root: Path,
    catalog_path: Path,
    artifacts: Sequence[Mapping[str, object]],
    failures: list[str],
) -> tuple[str, ...]:
    if not artifacts:
        failures.append(f"{_rel(root, catalog_path)}: missing [[artifacts]] entries")
        return ()
    seen_ids: set[str] = set()
    path_patterns: list[str] = []
    for index, artifact in enumerate(artifacts, start=1):
        label = f"{_rel(root, catalog_path)}: artifacts[{index}]"
        artifact_id = _required_string(artifact, "id", label, failures)
        _validate_unique_id(label, artifact_id, seen_ids, failures)
        kind = _required_string(artifact, "kind", label, failures)
        if kind and kind not in ARTIFACT_KINDS:
            failures.append(f"{label}: unknown kind {kind!r}")
        for key in ("tracked", "produced_by", "included_in_release", "retention"):
            _required_string(artifact, key, label, failures)
        _validate_artifact_kind_metadata(root, label, artifact, kind, failures)
        patterns = _required_string_array(artifact, "paths", label, failures)
        _validate_patterns_within_root(root, label, patterns, failures)
        _validate_ref_tables(root, label, artifact, "verification_refs", failures)
        path_patterns.extend(patterns)
    return tuple(path_patterns)


def check_release_governance_policy(root: Path) -> GovernancePolicyReport:
    """Check release-channel catalog coverage."""
    resolved_root = root.resolve()
    pyproject = load_pyproject(resolved_root)
    config = load_standard_config(resolved_root, pyproject)
    distribution = _string_value(config.get("distribution") if config else None)
    catalog_path = _configured_catalog_path(resolved_root, "release", DEFAULT_RELEASE_PATH)
    if not distribution or distribution == "none":
        if catalog_path.exists():
            return _validate_release_catalog(resolved_root, catalog_path, distribution)
        return GovernancePolicyReport(True, "release governance not required")
    if not catalog_path.exists():
        return _failure(
            "release",
            [
                f"distribution {distribution!r} requires {_rel(resolved_root, catalog_path)}",
            ],
        )
    return _validate_release_catalog(resolved_root, catalog_path, distribution)


def _validate_release_catalog(
    root: Path,
    catalog_path: Path,
    distribution: str,
) -> GovernancePolicyReport:
    failures: list[str] = []
    payload = _load_toml(catalog_path, failures)
    channels = _table_array(payload.get("channels"))
    if not channels:
        failures.append(f"{_rel(root, catalog_path)}: missing [[channels]] entries")
    for index, channel in enumerate(channels, start=1):
        _validate_release_channel(root, catalog_path, index, channel, failures)
    if _requires_matching_release_kind(distribution, channels):
        failures.append(
            f"{_rel(root, catalog_path)}: distribution {distribution!r} requires "
            "matching release channel kind"
        )
    if failures:
        return _failure("release", failures)
    return GovernancePolicyReport(True, f"{len(channels)} release channel(s) passed governance")


def _validate_release_channel(
    root: Path,
    catalog_path: Path,
    index: int,
    channel: Mapping[str, object],
    failures: list[str],
) -> None:
    label = f"{_rel(root, catalog_path)}: channels[{index}]"
    kind = _required_string(channel, "kind", label, failures)
    if kind and kind not in RELEASE_KINDS:
        failures.append(f"{label}: unknown kind {kind!r}")
    for key in ("id", "status", "owner", "process_doc", "build_doc"):
        _required_string(channel, key, label, failures)
    for key in ("process_doc", "build_doc"):
        doc_path = _string_value(channel.get(key))
        if doc_path:
            _validate_local_path(root, label, doc_path, failures)
    _validate_ref_tables(root, label, channel, "verification_refs", failures)
    _validate_ref_tables(root, label, channel, "artifact_refs", failures, validate_target=False)


def _requires_matching_release_kind(
    distribution: str,
    channels: Sequence[Mapping[str, object]],
) -> bool:
    if not distribution or distribution == "internal":
        return False
    return all(_string_value(channel.get("kind")) != distribution for channel in channels)


def _configured_catalog_path(root: Path, key: str, default: Path) -> Path:
    pyproject = load_pyproject(root)
    config = load_standard_config(root, pyproject)
    if config is None:
        return root / default
    governance = config.get("governance")
    if not isinstance(governance, dict):
        return root / default
    typed_governance = cast(Mapping[str, object], governance)
    catalogs = typed_governance.get("catalogs")
    if not isinstance(catalogs, dict):
        return root / default
    value = cast(Mapping[str, object], catalogs).get(key)
    if not isinstance(value, str) or not value.strip():
        return root / default
    path = (root / value).resolve()
    if not _is_within_root(root, path):
        return root / default
    return path


def _vendor_candidates(root: Path) -> tuple[str, ...]:
    candidates: list[str] = []
    for path in _tracked_file_paths(root):
        parts = path.split("/")
        if parts and parts[0] in VENDOR_ROOTS:
            candidates.append(path)
    return tuple(sorted(candidates))


def _artifact_candidates(root: Path) -> tuple[str, ...]:
    candidates: list[str] = []
    for path in _tracked_file_paths(root):
        if _is_public_release_asset(path):
            candidates.append(path)
            continue
        if _is_transient_path(path):
            continue
        if _is_vendor_path(path):
            continue
        if _is_artifact_candidate(path):
            candidates.append(path)
    return tuple(sorted(candidates))


def _is_artifact_candidate(path: str) -> bool:
    lower = path.lower()
    suffix = Path(path).suffix.lower()
    if suffix in ARTIFACT_EXTENSIONS:
        return True
    if _is_public_release_asset(path):
        return True
    if "/generated/" in lower and lower.startswith(("src/", "source/", "python/")):
        return True
    return lower.startswith("dist/") and lower not in {"dist/readme.md", "dist/.gitkeep"}


def _validate_artifact_kind_metadata(
    root: Path,
    label: str,
    artifact: Mapping[str, object],
    kind: str,
    failures: list[str],
) -> None:
    if kind != "generated_source":
        return
    source_of_truth = _required_string(artifact, "source_of_truth", label, failures)
    _required_string(artifact, "regeneration_command", label, failures)
    if source_of_truth:
        _validate_local_path(root, label, source_of_truth, failures)


def _is_public_release_asset(path: str) -> bool:
    return path.lower().startswith("public_release/examples/assets/")


def _tracked_file_paths(root: Path) -> tuple[str, ...]:
    if (root / ".git").exists():
        try:
            completed = subprocess.run(
                ["git", "-C", str(root), "ls-files"],
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError):
            return _walk_source_files(root)
        return tuple(
            sorted(
                line.strip().replace("\\", "/")
                for line in completed.stdout.splitlines()
                if line.strip()
            )
        )
    return _walk_source_files(root)


def _walk_source_files(root: Path) -> tuple[str, ...]:
    paths: list[str] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if _is_public_release_asset(rel):
            paths.append(rel)
            continue
        if rel.split("/", 1)[0] == "dist":
            continue
        if _is_transient_path(rel):
            continue
        paths.append(rel)
    return tuple(sorted(paths))


def _load_toml(path: Path, failures: list[str]) -> Mapping[str, object]:
    try:
        with path.open("rb") as handle:
            return cast(Mapping[str, object], tomllib.load(handle))
    except tomllib.TOMLDecodeError as exc:
        failures.append(f"{path.name}: invalid TOML: {exc}")
        return {}


def _validate_candidates_covered(
    noun: str,
    candidates: Sequence[str],
    patterns: Sequence[str],
    failures: list[str],
) -> None:
    uncovered = [path for path in candidates if not _matches_any(path, patterns)]
    if uncovered:
        failures.append(f"uncataloged {noun} candidate(s): {_sample(uncovered)}")


def _validate_patterns_within_root(
    root: Path,
    label: str,
    patterns: Sequence[str],
    failures: list[str],
) -> None:
    for pattern in patterns:
        static_prefix = pattern.split("*", 1)[0].rstrip("/")
        if not static_prefix:
            continue
        candidate = (root / static_prefix).resolve()
        if not _is_within_root(root, candidate):
            failures.append(f"{label}: path pattern escapes repository root {pattern!r}")


def _validate_ref_tables(
    root: Path,
    label: str,
    item: Mapping[str, object],
    key: str,
    failures: list[str],
    *,
    validate_target: bool = True,
) -> None:
    refs = _table_array(item.get(key))
    if item.get(key) is not None and not refs:
        failures.append(f"{label}: {key} must be an array of tables")
        return
    for index, ref in enumerate(refs, start=1):
        ref_label = f"{label}: {key}[{index}]"
        kind = _required_string(ref, "kind", ref_label, failures)
        target = _required_string(ref, "target", ref_label, failures)
        _required_string(ref, "rationale", ref_label, failures)
        if validate_target and kind.startswith("local") and target:
            _validate_local_path(root, ref_label, target, failures)


def _validate_local_path(root: Path, label: str, target: str, failures: list[str]) -> None:
    path_text = target.split("::", 1)[0].split("#", 1)[0]
    path = (root / path_text).resolve()
    if not _is_within_root(root, path):
        failures.append(f"{label}: local target escapes repository root {target!r}")
        return
    if not path.exists():
        failures.append(f"{label}: missing local target {target!r}")


def _required_string(
    item: Mapping[str, object],
    key: str,
    label: str,
    failures: list[str],
) -> str:
    value = _string_value(item.get(key))
    if not value:
        failures.append(f"{label}: missing {key}")
    return value


def _required_string_array(
    item: Mapping[str, object],
    key: str,
    label: str,
    failures: list[str],
) -> tuple[str, ...]:
    value = item.get(key)
    if not isinstance(value, list):
        failures.append(f"{label}: missing {key}")
        return ()
    items: list[str] = []
    for raw_item in cast(list[object], value):
        if not isinstance(raw_item, str) or not raw_item.strip():
            failures.append(f"{label}: {key} must contain non-empty strings")
            return ()
        items.append(raw_item.strip())
    if not items:
        failures.append(f"{label}: {key} must not be empty")
    return tuple(items)


def _validate_unique_id(
    label: str,
    item_id: str,
    seen: set[str],
    failures: list[str],
) -> None:
    if not item_id:
        return
    if item_id in seen:
        failures.append(f"{label}: duplicate id {item_id!r}")
    seen.add(item_id)


def _table_array(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, list):
        return ()
    items: list[Mapping[str, object]] = []
    for item in cast(list[object], value):
        if isinstance(item, dict):
            items.append(cast(Mapping[str, object], item))
    return tuple(items)


def _matches_any(path: str, patterns: Sequence[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def _is_vendor_path(path: str) -> bool:
    parts = path.split("/")
    return bool(parts and parts[0] in VENDOR_ROOTS)


def _is_transient_path(path: str) -> bool:
    parts = path.split("/")
    return any(part in TRANSIENT_ROOTS for part in parts)


def _is_within_root(root: Path, path: Path) -> bool:
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _string_value(value: object) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _sample(paths: Sequence[str]) -> str:
    sample = list(paths[:5])
    suffix = "" if len(paths) <= 5 else f", ... ({len(paths)} total)"
    return ", ".join(sample) + suffix


def _failure(noun: str, failures: Sequence[str]) -> GovernancePolicyReport:
    return GovernancePolicyReport(False, f"{noun} governance failed: " + "; ".join(failures))


def _missing_catalog_report(
    noun: str,
    root: Path,
    catalog_path: Path,
    candidates: Sequence[str],
) -> GovernancePolicyReport:
    rel_catalog = catalog_path.relative_to(root).as_posix()
    detail = f"missing {rel_catalog} for {noun} candidates: {_sample(candidates)}"
    if noun == "vendor":
        detail = f"missing {rel_catalog} for vendored files: {_sample(candidates)}"
    return _failure(noun, [detail])
