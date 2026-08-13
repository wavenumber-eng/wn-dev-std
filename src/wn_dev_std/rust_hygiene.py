"""Syntax-aware Rust source-shape and structural-complexity checks."""

from __future__ import annotations

import json
import tomllib
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import tree_sitter_rust
from tree_sitter import Language, Node, Parser

from wn_dev_std.checks_types import CheckResult
from wn_dev_std.rust_cargo_workspace import mapping_value, workspace_member_manifests
from wn_dev_std.rust_hygiene_exceptions import exception_shape_failures
from wn_dev_std.rust_hygiene_syntax import is_test_attribute, node_text

MAX_PARAMETERS = 7
MAX_FUNCTION_LINES = 100
MAX_TEST_FUNCTION_LINES = 150
MAX_FILE_LINES = 1000
MAX_CYCLOMATIC_COMPLEXITY = 10
MAX_NESTING = 4
MAX_COGNITIVE_COMPLEXITY = 15
CANONICAL_LIMITS = {
    "max_parameters": MAX_PARAMETERS,
    "max_function_lines": MAX_FUNCTION_LINES,
    "max_test_function_lines": MAX_TEST_FUNCTION_LINES,
    "max_file_lines": MAX_FILE_LINES,
    "max_cyclomatic_complexity": MAX_CYCLOMATIC_COMPLEXITY,
    "max_nesting": MAX_NESTING,
}
CANONICAL_EXCLUDE_PARTS = {
    ".git",
    "_build",
    "bindings",
    "build",
    "generated",
    "node_modules",
    "target",
    "third_party",
    "vendor",
}
REQUIRED_CLIPPY_LINTS = {
    "too_many_arguments",
    "too_many_lines",
    "cognitive_complexity",
    "allow_attributes_without_reason",
}
CONTROL_NODES = {
    "if_expression",
    "while_expression",
    "for_expression",
    "loop_expression",
    "match_expression",
}


@dataclass(frozen=True, slots=True)
class RustViolation:
    """One canonical Rust structural-policy violation."""

    path: str
    item: str
    rule: str
    value: int
    limit: int

    @property
    def key(self) -> tuple[str, str, str]:
        """Return the stable ratchet and exception identity."""
        return (self.path, self.item, self.rule)

    def detail(self) -> str:
        """Render a compact failure detail."""
        return f"{self.path}:{self.item} {self.rule}={self.value} exceeds {self.limit}"


@dataclass(frozen=True, slots=True)
class RustHygieneConfig:
    """Validated Rust structural-hygiene configuration."""

    mode: str
    baseline: str | None
    limits: Mapping[str, int]
    source_roots: tuple[str, ...]
    exclude_parts: frozenset[str]
    exceptions: tuple[Mapping[str, object], ...]


def check_rust_hygiene_policy(
    root: Path,
    config: Mapping[str, object] | None,
) -> CheckResult:
    """Validate Rust structural policy and scan owned Rust with Tree-sitter."""
    config_path_value = _hygiene_config_path(config)
    path_failure = _bounded_path_failure(config_path_value, "rust.hygiene.config")
    if path_failure is not None:
        return CheckResult(
            "Rust structural hygiene",
            False,
            path_failure,
        )
    config_path = root / config_path_value
    if not config_path.exists():
        return CheckResult(
            "Rust structural hygiene",
            False,
            f"{config_path_value} is required; copy docs/templates/rust/rust-hygiene.toml",
        )

    loaded = _load_hygiene_config(config_path)
    if isinstance(loaded, str):
        return CheckResult("Rust structural hygiene", False, loaded)
    policy, failures = loaded
    failures.extend(_clippy_config_failures(root))
    failures.extend(_cargo_clippy_lint_failures(root))
    failures.extend(_rack_gate_failures(root))
    failures.extend(_source_root_failures(root, config, policy))
    if failures:
        return CheckResult("Rust structural hygiene", False, "; ".join(failures))

    violations_or_error = scan_rust_hygiene(root, policy)
    if isinstance(violations_or_error, str):
        return CheckResult("Rust structural hygiene", False, violations_or_error)
    violations = violations_or_error
    unexcepted, exception_failures = _apply_exceptions(violations, policy.exceptions)
    if exception_failures:
        return CheckResult("Rust structural hygiene", False, "; ".join(exception_failures))

    ratchet_failures, warning = _ratchet_failures(root, policy, unexcepted)
    if ratchet_failures:
        return CheckResult("Rust structural hygiene", False, "; ".join(ratchet_failures))
    detail = _success_detail(policy, warning)
    return CheckResult("Rust structural hygiene", True, detail, warning=warning)


def _success_detail(policy: RustHygieneConfig, warning: bool) -> str:
    detail = (
        "Tree-sitter Rust hygiene passes canonical parameter, size, cyclomatic, and nesting limits"
    )
    exception_detail = (
        f" with {len(policy.exceptions)} reviewed exception(s)" if policy.exceptions else ""
    )
    warning_detail = "; ratchet contains resolved entries that should be pruned" if warning else ""
    return detail + exception_detail + warning_detail


def scan_rust_hygiene(
    root: Path,
    policy: RustHygieneConfig,
) -> tuple[RustViolation, ...] | str:
    """Return structural violations for owned Rust source."""
    parser = Parser(Language(tree_sitter_rust.language()))
    violations: list[RustViolation] = []
    seen: set[Path] = set()
    for source_root_value in policy.source_roots:
        source_root = (root / source_root_value).resolve()
        for path in sorted(source_root.rglob("*.rs")):
            resolved = path.resolve()
            if resolved in seen or _is_excluded(root, resolved, policy.exclude_parts):
                continue
            seen.add(resolved)
            source = resolved.read_bytes()
            relative = resolved.relative_to(root.resolve()).as_posix()
            line_count = len(source.splitlines())
            file_limit = policy.limits["max_file_lines"]
            if line_count > file_limit:
                violations.append(
                    RustViolation(relative, "<file>", "max_file_lines", line_count, file_limit)
                )
            tree = parser.parse(source)
            if tree.root_node.has_error:
                return f"{relative} contains Rust syntax errors; structural scan cannot continue"
            _collect_function_violations(
                tree.root_node,
                source,
                relative,
                policy.limits,
                violations,
            )
    if not seen:
        return "Rust structural hygiene found no owned .rs files in configured source_roots"
    return tuple(violations)


def _collect_function_violations(
    node: Node,
    source: bytes,
    relative: str,
    limits: Mapping[str, int],
    violations: list[RustViolation],
) -> None:
    if node.type == "function_item" and node.child_by_field_name("body") is not None:
        item = _qualified_function_name(node, source)
        parameters = node.child_by_field_name("parameters")
        parameter_count = _parameter_count(parameters)
        _append_violation(
            violations,
            relative,
            item,
            "max_parameters",
            parameter_count,
            limits["max_parameters"],
        )
        line_count = node.end_point.row - node.start_point.row + 1
        line_rule = (
            "max_test_function_lines" if _is_test_function(node, source) else "max_function_lines"
        )
        _append_violation(
            violations,
            relative,
            item,
            line_rule,
            line_count,
            limits[line_rule],
        )
        body = cast(Node, node.child_by_field_name("body"))
        _append_violation(
            violations,
            relative,
            item,
            "max_cyclomatic_complexity",
            _cyclomatic_complexity(body, source),
            limits["max_cyclomatic_complexity"],
        )
        _append_violation(
            violations,
            relative,
            item,
            "max_nesting",
            _max_nesting(body),
            limits["max_nesting"],
        )
    for child in node.named_children:
        _collect_function_violations(child, source, relative, limits, violations)


def _append_violation(
    violations: list[RustViolation],
    path: str,
    item: str,
    rule: str,
    value: int,
    limit: int,
) -> None:
    if value > limit:
        violations.append(RustViolation(path, item, rule, value, limit))


def _parameter_count(parameters: Node | None) -> int:
    if parameters is None:
        return 0
    return sum(
        child.type in {"parameter", "self_parameter", "variadic_parameter"}
        for child in parameters.named_children
    )


def _cyclomatic_complexity(body: Node, source: bytes) -> int:
    complexity = 1
    for node in _walk(body):
        if node.type in {"if_expression", "while_expression", "for_expression", "loop_expression"}:
            complexity += 1
        elif node.type == "match_expression":
            match_body = node.child_by_field_name("body")
            arms = (
                sum(child.type == "match_arm" for child in match_body.named_children)
                if match_body is not None
                else 0
            )
            complexity += max(0, arms - 1)
        elif node.type == "binary_expression":
            text = source[node.start_byte : node.end_byte]
            if b"&&" in text or b"||" in text:
                complexity += 1
    return complexity


def _max_nesting(body: Node) -> int:
    maximum = 0

    def visit(node: Node, depth: int) -> None:
        nonlocal maximum
        if node.type == "function_item":
            return
        next_depth = depth + 1 if node.type in CONTROL_NODES else depth
        maximum = max(maximum, next_depth)
        for child in node.named_children:
            visit(child, next_depth)

    for child in body.named_children:
        visit(child, 0)
    return maximum


def _walk(node: Node) -> Iterable[Node]:
    for child in node.named_children:
        yield child
        if child.type != "function_item":
            yield from _walk(child)


def _qualified_function_name(node: Node, source: bytes) -> str:
    name_node = node.child_by_field_name("name")
    name = node_text(name_node, source) or "<anonymous>"
    prefixes: list[str] = []
    parent = node.parent
    while parent is not None:
        if parent.type == "impl_item":
            trait = node_text(parent.child_by_field_name("trait"), source)
            target = node_text(parent.child_by_field_name("type"), source)
            prefixes.append(f"{trait} for {target}" if trait else target)
        elif parent.type in {"trait_item", "mod_item", "function_item"}:
            prefixes.append(node_text(parent.child_by_field_name("name"), source))
        parent = parent.parent
    return "::".join([part for part in reversed(prefixes) if part] + [name])


def _is_test_function(node: Node, source: bytes) -> bool:
    path = node
    while path is not None:
        if path.type == "mod_item":
            module_name = node_text(path.child_by_field_name("name"), source)
            if module_name == "tests":
                return True
        sibling = path.prev_named_sibling
        while sibling is not None and sibling.type == "attribute_item":
            if is_test_attribute(sibling, source):
                return True
            sibling = sibling.prev_named_sibling
        path = path.parent
    return False


def _load_hygiene_config(path: Path) -> tuple[RustHygieneConfig, list[str]] | str:
    try:
        with path.open("rb") as handle:
            data = cast(Mapping[str, object], tomllib.load(handle))
    except tomllib.TOMLDecodeError as exc:
        return f"{path.name} is invalid TOML: {exc}"
    failures: list[str] = []
    if data.get("schema") != 1:
        failures.append("schema must be 1")
    mode, baseline, mode_failures = _mode_and_baseline(data)
    failures.extend(mode_failures)
    limits, limit_failures = _hygiene_limits(data)
    failures.extend(limit_failures)
    source_roots, exclude_parts, path_failures = _hygiene_paths(data)
    failures.extend(path_failures)
    exceptions, exception_failures = _hygiene_exceptions(data)
    failures.extend(exception_failures)
    failures.extend(exception_shape_failures(exceptions, CANONICAL_LIMITS.keys()))
    return (
        RustHygieneConfig(
            mode=mode,
            baseline=baseline,
            limits=limits,
            source_roots=source_roots,
            exclude_parts=exclude_parts,
            exceptions=exceptions,
        ),
        failures,
    )


def _mode_and_baseline(data: Mapping[str, object]) -> tuple[str, str | None, list[str]]:
    failures: list[str] = []
    mode = _string(data.get("mode"))
    if mode not in {"strict", "ratchet"}:
        failures.append("mode must be strict or ratchet")
        mode = "strict"
    baseline = _string(data.get("baseline"))
    if mode == "ratchet" and baseline is None:
        failures.append("ratchet mode requires baseline")
    if mode == "strict" and baseline is not None:
        failures.append("strict mode must not declare baseline")
    return mode, baseline, failures


def _hygiene_limits(data: Mapping[str, object]) -> tuple[dict[str, int], list[str]]:
    failures: list[str] = []
    limits_table = _mapping(data.get("limits"))
    limits: dict[str, int] = {}
    for key, canonical in CANONICAL_LIMITS.items():
        value = limits_table.get(key) if limits_table is not None else None
        if type(value) is not int or value <= 0:
            failures.append(f"limits.{key} must be a positive integer <= {canonical}")
            limits[key] = canonical
        elif value > canonical:
            failures.append(f"limits.{key} must be <= {canonical}")
            limits[key] = value
        else:
            limits[key] = value
    return limits, failures


def _hygiene_paths(
    data: Mapping[str, object],
) -> tuple[tuple[str, ...], frozenset[str], list[str]]:
    failures: list[str] = []
    paths = _mapping(data.get("paths"))
    source_roots = _string_array(paths.get("source_roots") if paths else None)
    if not source_roots:
        failures.append("paths.source_roots must contain at least one relative source root")
    exclude_parts = frozenset(_string_array(paths.get("exclude_parts") if paths else None))
    missing_excludes = sorted(CANONICAL_EXCLUDE_PARTS - exclude_parts)
    if missing_excludes:
        failures.append("paths.exclude_parts must include " + ", ".join(missing_excludes))
    for value in (*source_roots, *exclude_parts):
        failure = _bounded_path_failure(value, f"path value {value!r}")
        if failure is not None:
            failures.append(failure)
    return source_roots, exclude_parts, failures


def _hygiene_exceptions(
    data: Mapping[str, object],
) -> tuple[tuple[Mapping[str, object], ...], list[str]]:
    failures: list[str] = []
    raw_exceptions_value = data.get("exceptions", [])
    exceptions: tuple[Mapping[str, object], ...] = ()
    if isinstance(raw_exceptions_value, list):
        raw_exceptions = cast(list[object], raw_exceptions_value)
        exceptions = tuple(
            cast(Mapping[str, object], item) for item in raw_exceptions if isinstance(item, dict)
        )
        if len(exceptions) != len(raw_exceptions):
            failures.append("each [[exceptions]] entry must be a table")
    else:
        failures.append("exceptions must be an array of tables")
    return exceptions, failures


def _clippy_config_failures(root: Path) -> list[str]:
    path = root / "clippy.toml"
    if not path.exists():
        return ["clippy.toml is required"]
    try:
        with path.open("rb") as handle:
            data = cast(Mapping[str, object], tomllib.load(handle))
    except tomllib.TOMLDecodeError as exc:
        return [f"clippy.toml is invalid TOML: {exc}"]
    expected = {
        "too-many-arguments-threshold": MAX_PARAMETERS,
        "too-many-lines-threshold": MAX_FUNCTION_LINES,
        "cognitive-complexity-threshold": MAX_COGNITIVE_COMPLEXITY,
    }
    failures: list[str] = []
    for key, maximum in expected.items():
        value = data.get(key)
        if type(value) is not int or value > maximum:
            failures.append(f"clippy.toml {key} must be an integer <= {maximum}")
    return failures


def _cargo_clippy_lint_failures(root: Path) -> list[str]:
    cargo = _load_toml(root / "Cargo.toml")
    if isinstance(cargo, str):
        return [cargo]
    failures: list[str] = []
    workspace = mapping_value(cargo, "workspace")
    members = workspace_member_manifests(root, workspace, failures)
    workspace_lints = mapping_value(cargo, "workspace.lints.clippy")
    if mapping_value(cargo, "package") is not None:
        _append_clippy_lint_failures(
            mapping_value(cargo, "lints.clippy"),
            "package",
            failures,
        )
    for member in members:
        effective = _effective_member_clippy_lints(member.manifest, workspace_lints)
        _append_clippy_lint_failures(
            effective,
            f"workspace member {member.key}",
            failures,
        )
    if mapping_value(cargo, "package") is None and not members:
        _append_clippy_lint_failures(workspace_lints, "workspace", failures)
    return failures


def _effective_member_clippy_lints(
    manifest: Mapping[str, object],
    workspace_lints: Mapping[str, object] | None,
) -> Mapping[str, object] | None:
    local = mapping_value(manifest, "lints.clippy")
    lints = mapping_value(manifest, "lints")
    inherits = lints is not None and lints.get("workspace") is True
    return workspace_lints if local is None and inherits else local


def _append_clippy_lint_failures(
    lints: Mapping[str, object] | None,
    label: str,
    failures: list[str],
) -> None:
    for lint in sorted(REQUIRED_CLIPPY_LINTS):
        value = lints.get(lint) if lints is not None else None
        level = _lint_level(value)
        if level not in {"deny", "forbid"}:
            failures.append(f"{label} lints.clippy.{lint} must be deny or forbid")


def _rack_gate_failures(root: Path) -> list[str]:
    path = root / "tests" / "rack.toml"
    if not path.exists():
        return ["tests/rack.toml is required for Rust structural signoff"]
    text = path.read_text(encoding="utf-8").lower()
    if "dev-std audit" not in text or "--scope language" not in text:
        return ["tests/rack.toml must declare a failing dev-std audit . --scope language lane"]
    return []


def _source_root_failures(
    root: Path,
    config: Mapping[str, object] | None,
    policy: RustHygieneConfig,
) -> list[str]:
    scan_roots, failures = _validated_scan_roots(root, policy.source_roots)
    failures.extend(_configured_source_root_failures(root, config, scan_roots))
    failures.extend(_workspace_source_root_failures(root, scan_roots))
    return failures


def _validated_scan_roots(
    root: Path,
    source_roots: Sequence[str],
) -> tuple[list[Path], list[str]]:
    failures: list[str] = []
    scan_roots: list[Path] = []
    for value in source_roots:
        path = (root / value).resolve()
        if not _is_within(root, path):
            failures.append(f"paths.source_roots entry {value!r} resolves outside the repository")
        elif not path.is_dir():
            failures.append(f"paths.source_roots entry {value!r} must be a directory")
        else:
            scan_roots.append(path)
    return scan_roots, failures


def _configured_source_root_failures(
    root: Path,
    config: Mapping[str, object] | None,
    scan_roots: Sequence[Path],
) -> list[str]:
    rust = _mapping(config.get("rust")) if config is not None else None
    configured = _string(rust.get("source_root")) if rust is not None else None
    expected_roots = (
        ((root / (configured or "src")).resolve(), "rust.source_root"),
        ((root / "tests").resolve(), "Rust integration tests"),
    )
    return [
        f"paths.source_roots must cover {label}"
        for expected, label in expected_roots
        if not any(_is_within(scan_root, expected) for scan_root in scan_roots)
    ]


def _workspace_source_root_failures(root: Path, scan_roots: Sequence[Path]) -> list[str]:
    failures: list[str] = []
    cargo = _load_toml(root / "Cargo.toml")
    if isinstance(cargo, str):
        return failures
    workspace_failures: list[str] = []
    workspace = mapping_value(cargo, "workspace")
    for member in workspace_member_manifests(root, workspace, workspace_failures):
        for part in ("src", "tests"):
            member_source = (root / member.key / part).resolve()
            covered = any(_is_within(scan_root, member_source) for scan_root in scan_roots)
            if member_source.exists() and not covered:
                failures.append(
                    f"paths.source_roots must cover workspace member {member.key}/{part}"
                )
    return failures


def _apply_exceptions(
    violations: Sequence[RustViolation],
    exceptions: Sequence[Mapping[str, object]],
) -> tuple[tuple[RustViolation, ...], list[str]]:
    exception_keys = {
        (_string(item.get("path")), _string(item.get("item")), _string(item.get("rule"))): item
        for item in exceptions
    }
    matched: set[tuple[str | None, str | None, str | None]] = set()
    remaining: list[RustViolation] = []
    failures: list[str] = []
    for violation in violations:
        key = violation.key
        exception = exception_keys.get(key)
        if exception is None:
            remaining.append(violation)
            continue
        matched.add(key)
        max_value = exception.get("max_value")
        if type(max_value) is int and violation.value > max_value:
            failures.append(
                f"Rust hygiene exception {_string(exception.get('id'))!r} exceeded: "
                f"{violation.path}:{violation.item} {violation.rule}={violation.value} "
                f"exceeds accepted maximum {max_value}"
            )
    failures.extend(
        [
            f"stale Rust hygiene exception {_string(item.get('id'))!r} matches no violation"
            for key, item in exception_keys.items()
            if key not in matched
        ]
    )
    return tuple(remaining), failures


def _ratchet_failures(
    root: Path,
    policy: RustHygieneConfig,
    violations: Sequence[RustViolation],
) -> tuple[list[str], bool]:
    if policy.mode == "strict":
        return ([violation.detail() for violation in violations], False)
    if policy.baseline is None:
        return (["ratchet baseline is required"], False)
    path_failure = _bounded_path_failure(policy.baseline, "Rust hygiene baseline")
    if path_failure is not None:
        return ([path_failure], False)
    baseline_path = root / policy.baseline
    loaded = _load_baseline(baseline_path)
    if isinstance(loaded, str):
        return ([loaded], False)
    return _evaluate_ratchet(loaded, violations)


def _evaluate_ratchet(
    baseline: Mapping[tuple[str, str, str], int],
    violations: Sequence[RustViolation],
) -> tuple[list[str], bool]:
    current_keys = {violation.key for violation in violations}
    failures: list[str] = []
    for violation in violations:
        allowed = baseline.get(violation.key)
        if allowed is None:
            failures.append("new Rust hygiene debt: " + violation.detail())
        elif violation.value > allowed:
            failures.append(
                f"increased Rust hygiene debt: {violation.path}:{violation.item} "
                f"{violation.rule}={violation.value} exceeds baseline {allowed}"
            )
    stale = bool(set(baseline) - current_keys)
    return failures, stale


def _load_baseline(path: Path) -> dict[tuple[str, str, str], int] | str:
    if not path.exists():
        return f"Rust hygiene baseline {path.name} is required"
    loaded = _load_baseline_document(path)
    if isinstance(loaded, str):
        return loaded
    return _baseline_entries(loaded)


def _load_baseline_document(path: Path) -> list[object] | str:
    try:
        data_value: object = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return f"Rust hygiene baseline is invalid JSON: {exc}"
    if not isinstance(data_value, dict):
        return "Rust hygiene baseline must be an object"
    data = cast(Mapping[str, object], data_value)
    if data.get("schema") != 1:
        return "Rust hygiene baseline schema must be 1"
    raw_value = data.get("violations")
    if not isinstance(raw_value, list):
        return "Rust hygiene baseline violations must be an array"
    return cast(list[object], raw_value)


def _baseline_entries(raw: Sequence[object]) -> dict[tuple[str, str, str], int] | str:
    baseline: dict[tuple[str, str, str], int] = {}
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            return f"Rust hygiene baseline violations[{index}] must be an object"
        entry = cast(Mapping[str, object], item)
        parsed = _baseline_entry(entry, index)
        if isinstance(parsed, str):
            return parsed
        key, value = parsed
        if key in baseline:
            return f"Rust hygiene baseline violations[{index}] duplicates {key}"
        baseline[key] = value
    return baseline


def _baseline_entry(
    entry: Mapping[str, object],
    index: int,
) -> tuple[tuple[str, str, str], int] | str:
    path_value = _string(entry.get("path"))
    item_value = _string(entry.get("item"))
    rule = _string(entry.get("rule"))
    value = entry.get("value")
    if (
        path_value is None
        or item_value is None
        or rule not in CANONICAL_LIMITS
        or type(value) is not int
    ):
        return f"Rust hygiene baseline violations[{index}] is incomplete"
    return (path_value, item_value, rule), value


def _hygiene_config_path(config: Mapping[str, object] | None) -> str:
    rust = _mapping(config.get("rust")) if config is not None else None
    hygiene = _mapping(rust.get("hygiene")) if rust is not None else None
    if hygiene is None:
        return "rust-hygiene.toml"
    return _string(hygiene.get("config")) or "rust-hygiene.toml"


def _bounded_path_failure(value: str, label: str) -> str | None:
    path = Path(value)
    if path.is_absolute():
        return f"{label} must be a bounded repository-relative path"
    if ".." in path.parts:
        return f"{label} must be a bounded repository-relative path"
    return None


def _is_excluded(root: Path, path: Path, exclude_parts: frozenset[str]) -> bool:
    try:
        parts = path.relative_to(root.resolve()).parts
    except ValueError:
        return True
    return any(part in exclude_parts for part in parts)


def _is_within(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _load_toml(path: Path) -> Mapping[str, object] | str:
    if not path.exists():
        return f"{path.name} is required"
    try:
        with path.open("rb") as handle:
            return cast(Mapping[str, object], tomllib.load(handle))
    except tomllib.TOMLDecodeError as exc:
        return f"{path.name} is invalid TOML: {exc}"


def _mapping(value: object) -> Mapping[str, object] | None:
    if isinstance(value, dict):
        return cast(Mapping[str, object], value)
    return None


def _string(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _string_array(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(text for item in cast(list[object], value) if (text := _string(item)) is not None)


def _lint_level(value: object) -> str | None:
    direct = _string(value)
    if direct is not None:
        return direct.lower()
    table = _mapping(value)
    level = _string(table.get("level")) if table is not None else None
    return level.lower() if level is not None else None
