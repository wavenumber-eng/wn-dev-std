"""Promoted release-artifact declaration and payload checks."""

from __future__ import annotations

import fnmatch
import hashlib
import re
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import cast

from wn_dev_std.artifact_policy import (
    ARTIFACT_EXTENSIONS,
    ARTIFACT_KINDS,
    RUNTIME_ARTIFACT_KINDS,
)
from wn_dev_std.audit_config import AuditMode

SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


@dataclass(frozen=True, slots=True)
class PromotedArtifact:
    """Release-channel artifact declaration normalized for validation."""

    label: str
    artifact_id: str
    kind: str
    required: bool
    patterns: tuple[str, ...]
    version: str
    source_commit: str
    sha256: str


def validate_promoted_artifacts(
    root: Path,
    channel_label: str,
    channel: Mapping[str, object],
    failures: list[str],
    mode: AuditMode,
    pyproject: Mapping[str, object] | None,
) -> tuple[PromotedArtifact, ...]:
    """Validate promoted artifacts declared under one release channel."""
    promoted_artifacts = _validate_promoted_artifact_entries(
        root,
        channel_label,
        channel,
        failures,
    )
    if mode == "release":
        _validate_release_payloads(root, promoted_artifacts, failures, pyproject)
    return promoted_artifacts


def validate_uncataloged_promoted_payloads(
    root: Path,
    catalog_label: str,
    artifacts: Sequence[PromotedArtifact],
    failures: list[str],
) -> None:
    """Validate uncataloged release payloads against catalog-wide declarations."""
    if not artifacts:
        return
    all_patterns = tuple(pattern for artifact in artifacts for pattern in artifact.patterns)
    promoted_files = _promoted_files(root, artifacts)
    _validate_uncataloged_payloads(catalog_label, promoted_files, all_patterns, failures)


def _validate_promoted_artifact_entries(
    root: Path,
    channel_label: str,
    channel: Mapping[str, object],
    failures: list[str],
) -> tuple[PromotedArtifact, ...]:
    entries = _promoted_artifact_tables(channel, channel_label, failures)
    seen_ids: set[str] = set()
    artifacts: list[PromotedArtifact] = []
    for index, artifact in enumerate(entries, start=1):
        artifact_record = _validate_promoted_artifact(
            root,
            f"{channel_label}: promoted_artifacts[{index}]",
            artifact,
            seen_ids,
            failures,
        )
        if artifact_record is not None:
            artifacts.append(artifact_record)
    return tuple(artifacts)


def _validate_promoted_artifact(
    root: Path,
    label: str,
    artifact: Mapping[str, object],
    seen_ids: set[str],
    failures: list[str],
) -> PromotedArtifact | None:
    artifact_id = _required_string(artifact, "id", label, failures)
    _validate_unique_id(label, artifact_id, seen_ids, failures)
    kind = _required_string(artifact, "kind", label, failures)
    if kind and kind not in ARTIFACT_KINDS:
        failures.append(f"{label}: unknown kind {kind!r}")
    required = _bool_value(artifact.get("required"), label, "required", failures, default=True)
    patterns = _promoted_artifact_patterns(root, label, artifact, failures)
    _validate_optional_sha256(label, artifact, failures)
    _validate_optional_string(label, artifact, "version", failures)
    _validate_optional_string(label, artifact, "source_commit", failures)
    _validate_optional_string(label, artifact, "destination", failures)
    _validate_runtime_artifact_metadata(root, label, artifact, kind, failures)
    if not artifact_id or not patterns:
        return None
    return PromotedArtifact(
        label,
        artifact_id,
        kind,
        required,
        patterns,
        _string_value(artifact.get("version")),
        _string_value(artifact.get("source_commit")),
        _string_value(artifact.get("sha256")),
    )


def _promoted_artifact_tables(
    channel: Mapping[str, object],
    channel_label: str,
    failures: list[str],
) -> tuple[Mapping[str, object], ...]:
    value = channel.get("promoted_artifacts")
    if value is None:
        return ()
    if not isinstance(value, list):
        failures.append(f"{channel_label}: promoted_artifacts must be an array of tables")
        return ()

    entries: list[Mapping[str, object]] = []
    for index, item in enumerate(cast(list[object], value), start=1):
        if isinstance(item, dict):
            entries.append(cast(Mapping[str, object], item))
        else:
            failures.append(f"{channel_label}: promoted_artifacts[{index}] must be a table")
    return tuple(entries)


def _promoted_artifact_patterns(
    root: Path,
    label: str,
    artifact: Mapping[str, object],
    failures: list[str],
) -> tuple[str, ...]:
    patterns = _declared_patterns(label, artifact, failures)
    if not patterns:
        return ()
    failure_count = len(failures)
    _validate_pattern_containment(root, label, patterns, failures)
    _validate_pattern_roots(label, patterns, failures)
    return () if len(failures) != failure_count else patterns


def _declared_patterns(
    label: str,
    artifact: Mapping[str, object],
    failures: list[str],
) -> tuple[str, ...]:
    path_value = _string_value(artifact.get("path"))
    has_paths = "paths" in artifact
    if path_value and has_paths:
        failures.append(f"{label}: declare either path or paths, not both")
        return ()
    if path_value:
        return _exact_path_pattern(label, path_value, failures)
    if has_paths:
        return tuple(
            _normalize_pattern(pattern)
            for pattern in _required_string_array(
                artifact,
                "paths",
                label,
                failures,
            )
        )
    failures.append(f"{label}: missing path or paths")
    return ()


def _exact_path_pattern(label: str, path_value: str, failures: list[str]) -> tuple[str, ...]:
    if _contains_wildcard(path_value):
        failures.append(f"{label}: path must be exact; use paths for glob patterns")
        return ()
    return (_normalize_pattern(path_value),)


def _validate_pattern_containment(
    root: Path,
    label: str,
    patterns: Sequence[str],
    failures: list[str],
) -> None:
    for pattern in patterns:
        static_prefix = _static_prefix(pattern).rstrip("/")
        if not static_prefix:
            continue
        candidate = (root / static_prefix).resolve()
        if not _is_within_root(root, candidate):
            failures.append(f"{label}: path pattern escapes repository root {pattern!r}")


def _validate_pattern_roots(
    label: str,
    patterns: Sequence[str],
    failures: list[str],
) -> None:
    for pattern in patterns:
        if _promoted_root_relative(pattern) == "":
            failures.append(
                f"{label}: promoted artifact path must include a static directory prefix "
                f"{pattern!r}"
            )


def _validate_optional_sha256(
    label: str,
    artifact: Mapping[str, object],
    failures: list[str],
) -> None:
    sha256 = _validate_optional_string(label, artifact, "sha256", failures)
    if sha256 and SHA256_RE.fullmatch(sha256) is None:
        failures.append(f"{label}: sha256 must be a 64-character hexadecimal digest")


def _validate_runtime_artifact_metadata(
    root: Path,
    label: str,
    artifact: Mapping[str, object],
    kind: str,
    failures: list[str],
) -> None:
    _validate_license_refs(root, label, artifact, failures)
    if kind not in RUNTIME_ARTIFACT_KINDS:
        return
    _required_string(artifact, "target", label, failures)
    _required_string(artifact, "build_profile", label, failures)
    if kind == "runtime_wasm":
        _required_string(artifact, "runtime", label, failures)
    else:
        _required_string(artifact, "abi", label, failures)
    if "license_refs" not in artifact:
        failures.append(f"{label}: missing license_refs")


def _validate_license_refs(
    root: Path,
    label: str,
    artifact: Mapping[str, object],
    failures: list[str],
) -> None:
    if "license_refs" not in artifact:
        return
    refs = _required_string_array(artifact, "license_refs", label, failures)
    for ref in refs:
        _validate_local_path(root, f"{label}: license_refs", ref, failures)


def _validate_release_payloads(
    root: Path,
    artifacts: Sequence[PromotedArtifact],
    failures: list[str],
    pyproject: Mapping[str, object] | None,
) -> None:
    if not artifacts:
        return
    promoted_files = _promoted_files(root, artifacts)
    _validate_declared_payloads(root, artifacts, promoted_files, pyproject, failures)


def _validate_declared_payloads(
    root: Path,
    artifacts: Sequence[PromotedArtifact],
    promoted_files: Sequence[str],
    pyproject: Mapping[str, object] | None,
    failures: list[str],
) -> None:
    for artifact in artifacts:
        matched_paths = tuple(
            path for path in promoted_files if _matches_any(path, artifact.patterns)
        )
        if artifact.required and not matched_paths:
            failures.append(f"{artifact.label}: missing required promoted artifact")
            continue
        if matched_paths:
            _validate_promoted_metadata(root, artifact, matched_paths, pyproject, failures)


def _validate_uncataloged_payloads(
    channel_label: str,
    promoted_files: Sequence[str],
    all_patterns: Sequence[str],
    failures: list[str],
) -> None:
    uncataloged = [
        path
        for path in promoted_files
        if _is_release_payload_candidate(path) and not _matches_any(path, all_patterns)
    ]
    if uncataloged:
        failures.append(
            f"{channel_label}: uncataloged promoted artifact candidate(s): {_sample(uncataloged)}"
        )


def _validate_promoted_metadata(
    root: Path,
    artifact: PromotedArtifact,
    matched_paths: Sequence[str],
    pyproject: Mapping[str, object] | None,
    failures: list[str],
) -> None:
    if artifact.version:
        _validate_promoted_version(artifact, pyproject, failures)
    if artifact.source_commit:
        _validate_promoted_source_commit(root, artifact, failures)
    if artifact.sha256:
        _validate_promoted_sha256(root, artifact, matched_paths, failures)


def _validate_promoted_version(
    artifact: PromotedArtifact,
    pyproject: Mapping[str, object] | None,
    failures: list[str],
) -> None:
    version = _project_version(pyproject)
    if not version:
        failures.append(
            f"{artifact.label}: version declared but pyproject project.version is missing"
        )
        return
    if artifact.version != version:
        failures.append(
            f"{artifact.label}: version {artifact.version!r} does not match project version "
            f"{version!r}"
        )


def _validate_promoted_source_commit(
    root: Path,
    artifact: PromotedArtifact,
    failures: list[str],
) -> None:
    head = _git_head(root)
    if not head:
        failures.append(f"{artifact.label}: source_commit declared but git HEAD is unavailable")
        return
    if not head.startswith(artifact.source_commit):
        failures.append(
            f"{artifact.label}: source_commit {artifact.source_commit!r} does not match HEAD "
            f"{head[:12]}"
        )


def _validate_promoted_sha256(
    root: Path,
    artifact: PromotedArtifact,
    matched_paths: Sequence[str],
    failures: list[str],
) -> None:
    if len(matched_paths) != 1:
        failures.append(f"{artifact.label}: sha256 requires exactly one matched artifact")
        return
    path = root / matched_paths[0]
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual.lower() != artifact.sha256.lower():
        failures.append(f"{artifact.label}: sha256 does not match {matched_paths[0]}")


def _promoted_files(root: Path, artifacts: Sequence[PromotedArtifact]) -> tuple[str, ...]:
    roots = sorted(
        {
            promoted_root
            for artifact in artifacts
            for pattern in artifact.patterns
            if (promoted_root := _promoted_root_relative(pattern))
        }
    )
    paths: set[str] = set()
    for promoted_root in roots:
        paths.update(_files_under(root, promoted_root))
    return tuple(sorted(paths))


def _files_under(root: Path, promoted_root: str) -> set[str]:
    root_path = root / promoted_root
    if not root_path.exists() or not root_path.is_dir():
        return set()
    return {_rel(root, path) for path in root_path.rglob("*") if path.is_file()}


def _is_release_payload_candidate(path: str) -> bool:
    lower = path.lower()
    if lower.endswith(".tar.gz"):
        return True
    return Path(path).suffix.lower() in ARTIFACT_EXTENSIONS


def _project_version(pyproject: Mapping[str, object] | None) -> str:
    if pyproject is None:
        return ""
    project = pyproject.get("project")
    if not isinstance(project, dict):
        return ""
    return _string_value(cast(Mapping[str, object], project).get("version"))


def _git_head(root: Path) -> str:
    if not (root / ".git").exists():
        return ""
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return ""
    return completed.stdout.strip()


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


def _bool_value(
    value: object,
    label: str,
    key: str,
    failures: list[str],
    *,
    default: bool,
) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    failures.append(f"{label}: {key} must be true or false")
    return default


def _validate_optional_string(
    label: str,
    item: Mapping[str, object],
    key: str,
    failures: list[str],
) -> str:
    if key not in item:
        return ""
    value = _string_value(item.get(key))
    if not value:
        failures.append(f"{label}: {key} must be a non-empty string")
    return value


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


def _validate_local_path(root: Path, label: str, target: str, failures: list[str]) -> None:
    path_text = target.split("::", 1)[0].split("#", 1)[0]
    path = (root / path_text).resolve()
    if not _is_within_root(root, path):
        failures.append(f"{label}: local target escapes repository root {target!r}")
        return
    if not path.exists():
        failures.append(f"{label}: missing local target {target!r}")


def _matches_any(path: str, patterns: Sequence[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def _contains_wildcard(value: str) -> bool:
    return any(marker in value for marker in ("*", "?", "["))


def _normalize_pattern(pattern: str) -> str:
    return pattern.replace("\\", "/").strip()


def _static_prefix(pattern: str) -> str:
    positions = [position for marker in ("*", "?", "[") if (position := pattern.find(marker)) >= 0]
    if not positions:
        return pattern
    return pattern[: min(positions)]


def _promoted_root_relative(pattern: str) -> str:
    normalized = _normalize_pattern(pattern)
    if not _contains_wildcard(normalized):
        root = PurePosixPath(normalized).parent.as_posix()
        return "" if root in {"", "."} else root

    prefix = _static_prefix(normalized)
    if not prefix:
        return ""
    root = prefix.rstrip("/") if prefix.endswith("/") else PurePosixPath(prefix).parent.as_posix()
    return "" if root in {"", "."} else root


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
