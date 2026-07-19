"""TypeScript and browser TypeScript audit checks."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from wn_dev_std.checks_types import CheckResult

GENERATED_OR_EXTERNAL_PARTS = {
    "__fixtures__",
    "_build",
    "fixtures",
    "generated",
    "lib",
    "node_modules",
    "test_fixtures",
    "vendor",
}
IMPLEMENTATION_TS_SUFFIXES = (".ts", ".tsx")
OWNED_JS_SUFFIXES = (".js", ".mjs", ".cjs", ".jsx")
LOCKFILES = (
    "package-lock.json",
    "npm-shrinkwrap.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lock",
    "bun.lockb",
)
REQUIRED_PACKAGE_SCRIPTS = (
    "build",
    "typecheck",
    "lint",
    "test",
    "signoff",
)
SIGNOFF_SCRIPT_MARKERS = ("typecheck", "lint", "test")
REQUIRED_TRUE_COMPILER_OPTIONS = (
    "strict",
    "noUncheckedIndexedAccess",
    "exactOptionalPropertyTypes",
    "noPropertyAccessFromIndexSignature",
    "noImplicitOverride",
    "noImplicitReturns",
    "noFallthroughCasesInSwitch",
    "useUnknownInCatchVariables",
    "forceConsistentCasingInFileNames",
    "isolatedModules",
    "verbatimModuleSyntax",
    "noEmit",
)
STRICT_SUBOPTIONS = (
    "noImplicitAny",
    "strictNullChecks",
    "strictFunctionTypes",
    "strictBindCallApply",
    "strictPropertyInitialization",
    "noImplicitThis",
    "alwaysStrict",
)


@dataclass(frozen=True, slots=True)
class TypeScriptConfigResult:
    """Resolved TypeScript config state for audit checks."""

    path: Path
    compiler_options: Mapping[str, object]
    failures: tuple[str, ...]
    warnings: tuple[str, ...]
    has_package_extends_exception: bool


@dataclass(slots=True)
class _JsonStringState:
    in_string: bool = False
    escape: bool = False


def check_typescript_policy(
    root: Path,
    config: Mapping[str, object] | None,
) -> list[CheckResult]:
    """Return TypeScript profile policy checks."""
    return [
        _check_typescript_source_policy(root, config),
        _check_typescript_config_policy(root, config),
        _check_typescript_command_surface_policy(root),
        _check_typescript_css_token_policy(root),
    ]


def _check_typescript_source_policy(
    root: Path,
    config: Mapping[str, object] | None,
) -> CheckResult:
    owned_ts = _owned_source_files(root, IMPLEMENTATION_TS_SUFFIXES)
    owned_ts = [path for path in owned_ts if not path.name.endswith(".d.ts")]
    if not owned_ts:
        return CheckResult(
            "TypeScript source",
            False,
            "at least one owned .ts or .tsx implementation file is required under src/",
        )

    owned_js = _owned_source_files(root, OWNED_JS_SUFFIXES)
    if not owned_js:
        return CheckResult(
            "TypeScript source",
            True,
            f"{len(owned_ts)} owned TypeScript implementation file(s) found",
        )

    migration_failure = _migration_failure(root, config)
    if migration_failure is not None:
        return CheckResult(
            "TypeScript source",
            False,
            "owned JavaScript source requires [typescript.migration] allow_js = true: "
            + ", ".join(_relative_paths(root, owned_js[:5]))
            + "; "
            + migration_failure,
        )
    return CheckResult(
        "TypeScript source",
        True,
        f"{len(owned_ts)} owned TypeScript implementation file(s); "
        f"{len(owned_js)} migration JavaScript file(s) allowed",
        warning=True,
    )


def _check_typescript_config_policy(
    root: Path,
    config: Mapping[str, object] | None,
) -> CheckResult:
    typecheck_config = _typecheck_config_path(root, config)
    if isinstance(typecheck_config, str):
        return CheckResult("TypeScript config", False, typecheck_config)
    if not typecheck_config.exists():
        return CheckResult(
            "TypeScript config",
            False,
            f"{_rel(root, typecheck_config)} is required for TypeScript profiles",
        )

    result = _load_typescript_config(root, typecheck_config, config, ())
    failures = list(result.failures)
    failures.extend(_compiler_option_failures(result.compiler_options, result))
    failures.extend(_allow_js_failures(root, config, result.compiler_options))
    failures.extend(_skip_lib_check_failures(root, config, result.compiler_options))
    if failures:
        return CheckResult("TypeScript config", False, "; ".join(failures))

    detail = f"{_rel(root, result.path)} enables TypeScript guardrails"
    if result.warnings:
        return CheckResult(
            "TypeScript config",
            True,
            detail + "; " + "; ".join(result.warnings),
            warning=True,
        )
    return CheckResult("TypeScript config", True, detail)


def _check_typescript_command_surface_policy(root: Path) -> CheckResult:
    package_json = root / "package.json"
    if not package_json.exists():
        return CheckResult("TypeScript command surface", False, "package.json is required")

    package_data, package_error = _load_json_mapping(package_json)
    if package_error is not None:
        return CheckResult("TypeScript command surface", False, package_error)

    scripts: Mapping[str, object] = {}
    scripts_raw = package_data.get("scripts")
    if isinstance(scripts_raw, dict):
        scripts = cast(Mapping[str, object], scripts_raw)

    lockfile = _committed_lockfile(root)
    failures = _package_script_failures(scripts, lockfile)
    if failures:
        return CheckResult("TypeScript command surface", False, "; ".join(failures))
    return CheckResult(
        "TypeScript command surface",
        True,
        f"package.json scripts and {lockfile} expose TypeScript signoff",
    )


def _check_typescript_css_token_policy(root: Path) -> CheckResult:
    owned_css = _owned_source_files(root, (".css",))
    if not owned_css:
        return CheckResult("TypeScript CSS tokens", True, "no owned CSS files found")
    token_files = [
        path.relative_to(root).as_posix() for path in owned_css if _css_uses_custom_properties(path)
    ]
    if token_files:
        return CheckResult("TypeScript CSS tokens", True, "CSS custom properties are present")
    return CheckResult(
        "TypeScript CSS tokens",
        False,
        "owned CSS must define or consume CSS custom properties for design constants",
    )


def _committed_lockfile(root: Path) -> str | None:
    return next((name for name in LOCKFILES if (root / name).exists()), None)


def _package_script_failures(
    scripts: Mapping[str, object],
    lockfile: str | None,
) -> list[str]:
    failures: list[str] = []
    missing_scripts = [name for name in REQUIRED_PACKAGE_SCRIPTS if name not in scripts]
    if lockfile is None:
        failures.append("committed package-manager lockfile is required")
    if missing_scripts:
        failures.append("package.json scripts missing " + ", ".join(missing_scripts))
    signoff_failure = _signoff_script_failure(scripts, missing_scripts)
    if signoff_failure is not None:
        failures.append(signoff_failure)
    return failures


def _signoff_script_failure(
    scripts: Mapping[str, object],
    missing_scripts: Sequence[str],
) -> str | None:
    signoff = scripts.get("signoff")
    if not isinstance(signoff, str):
        if "signoff" in missing_scripts:
            return None
        return "package.json scripts.signoff must be a string"
    missing_markers = [marker for marker in SIGNOFF_SCRIPT_MARKERS if marker not in signoff.lower()]
    if not missing_markers:
        return None
    return "package.json signoff script must invoke " + ", ".join(SIGNOFF_SCRIPT_MARKERS)


def _owned_source_files(root: Path, suffixes: tuple[str, ...]) -> list[Path]:
    src = root / "src"
    if not src.exists():
        return []
    files: list[Path] = []
    for suffix in suffixes:
        for path in src.rglob(f"*{suffix}"):
            relative_parts = set(path.relative_to(root).parts)
            if GENERATED_OR_EXTERNAL_PARTS & relative_parts:
                continue
            if path.name.endswith(".min.js") or path.name.endswith(".min.css"):
                continue
            files.append(path)
    return sorted(files)


def _extended_compiler_options(
    root: Path,
    resolved_path: Path,
    data: Mapping[str, object],
    config: Mapping[str, object] | None,
    seen: tuple[Path, ...],
) -> TypeScriptConfigResult:
    failures: list[str] = []
    warnings: list[str] = []
    compiler_options: dict[str, object] = {}
    has_package_extends_exception = False
    for extends_value in _extends_values(data.get("extends")):
        base_result = _load_extended_config(root, resolved_path, extends_value, config, seen)
        failures.extend(base_result.failures)
        warnings.extend(base_result.warnings)
        compiler_options.update(base_result.compiler_options)
        has_package_extends_exception = (
            has_package_extends_exception or base_result.has_package_extends_exception
        )
    return TypeScriptConfigResult(
        resolved_path,
        compiler_options,
        tuple(failures),
        tuple(warnings),
        has_package_extends_exception,
    )


def _load_extended_config(
    root: Path,
    resolved_path: Path,
    extends_value: str,
    config: Mapping[str, object] | None,
    seen: tuple[Path, ...],
) -> TypeScriptConfigResult:
    base_path_or_error = _resolve_local_extends(root, resolved_path.parent, extends_value)
    if isinstance(base_path_or_error, str):
        if base_path_or_error != "package extends":
            return TypeScriptConfigResult(
                resolved_path,
                {},
                (f"{_rel(root, resolved_path)} extends {extends_value!r}: {base_path_or_error}",),
                (),
                False,
            )
        return _package_extends_result(root, resolved_path, extends_value, config)
    return _load_typescript_config(root, base_path_or_error, config, (*seen, resolved_path))


def _package_extends_result(
    root: Path,
    resolved_path: Path,
    extends_value: str,
    config: Mapping[str, object] | None,
) -> TypeScriptConfigResult:
    exception_ref = _exception_ref(config, "package_extends")
    if exception_ref is None:
        return TypeScriptConfigResult(
            resolved_path,
            {},
            (
                f"{_rel(root, resolved_path)} extends {extends_value!r}, "
                "which is not a local auditable tsconfig; add "
                "[typescript.exceptions].package_extends or use a local extends file",
            ),
            (),
            False,
        )
    return TypeScriptConfigResult(
        resolved_path,
        {},
        (),
        (f"package-based tsconfig extends {extends_value!r} is covered by {exception_ref}",),
        True,
    )


def _load_typescript_config(
    root: Path,
    path: Path,
    config: Mapping[str, object] | None,
    seen: tuple[Path, ...],
) -> TypeScriptConfigResult:
    resolved_path = path.resolve()
    if resolved_path in seen:
        return TypeScriptConfigResult(
            resolved_path,
            {},
            (f"{_rel(root, resolved_path)} has circular tsconfig extends",),
            (),
            False,
        )

    data, parse_error = _load_json_mapping(resolved_path)
    if parse_error is not None:
        return TypeScriptConfigResult(resolved_path, {}, (parse_error,), (), False)

    base = _extended_compiler_options(root, resolved_path, data, config, seen)
    failures = list(base.failures)
    warnings = list(base.warnings)
    compiler_options = dict(base.compiler_options)

    own_options = data.get("compilerOptions")
    if isinstance(own_options, dict):
        compiler_options.update(cast(Mapping[str, object], own_options))
    elif own_options is not None:
        failures.append(f"{_rel(root, resolved_path)} compilerOptions must be an object")

    return TypeScriptConfigResult(
        resolved_path,
        compiler_options,
        tuple(failures),
        tuple(warnings),
        base.has_package_extends_exception,
    )


def _extends_values(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str) and value.strip():
        return (value.strip(),)
    if isinstance(value, list):
        raw_items = cast(list[object], value)
        return tuple(item.strip() for item in raw_items if isinstance(item, str) and item.strip())
    return ()


def _resolve_local_extends(root: Path, base_dir: Path, value: str) -> Path | str:
    raw_path = Path(value)
    if not value.startswith(".") and not raw_path.is_absolute():
        return "package extends"
    candidate_base = raw_path if raw_path.is_absolute() else base_dir / raw_path
    candidates = (
        candidate_base,
        candidate_base.with_suffix(".json"),
        candidate_base / "tsconfig.json",
    )
    for candidate in candidates:
        resolved = candidate.resolve()
        if not _is_within_root(root, resolved):
            return f"{value!r} resolves outside the project root"
        if resolved.exists() and resolved.is_file():
            return resolved
    return f"{value!r} does not resolve to a local tsconfig file"


def _compiler_option_failures(
    options: Mapping[str, object],
    result: TypeScriptConfigResult,
) -> list[str]:
    failures: list[str] = []
    allow_unverified_inherited = result.has_package_extends_exception
    for option in REQUIRED_TRUE_COMPILER_OPTIONS:
        value = options.get(option)
        if value is True:
            continue
        if value is None and allow_unverified_inherited:
            continue
        failures.append(f"compilerOptions.{option} must be true")
    for option in STRICT_SUBOPTIONS:
        if options.get(option) is False:
            failures.append(f"compilerOptions.{option} must not disable strict mode")
    return failures


def _allow_js_failures(
    root: Path,
    config: Mapping[str, object] | None,
    options: Mapping[str, object],
) -> list[str]:
    if options.get("allowJs") is not True:
        return []
    migration_failure = _migration_failure(root, config)
    if migration_failure is None:
        return []
    return ["compilerOptions.allowJs requires TypeScript migration metadata: " + migration_failure]


def _skip_lib_check_failures(
    root: Path,
    config: Mapping[str, object] | None,
    options: Mapping[str, object],
) -> list[str]:
    if options.get("skipLibCheck") is not True:
        return []
    exception_ref = _exception_ref(config, "skip_lib_check")
    if exception_ref is None:
        return ["compilerOptions.skipLibCheck requires [typescript.exceptions].skip_lib_check"]
    missing_ref = _missing_local_ref(root, exception_ref)
    if missing_ref is not None:
        return [missing_ref]
    return []


def _migration_failure(root: Path, config: Mapping[str, object] | None) -> str | None:
    migration = _typescript_subconfig(config, "migration")
    if migration is None or migration.get("allow_js") is not True:
        return "set allow_js = true plus tracking_ref and remove_when in [typescript.migration]"
    tracking_ref = _non_empty_string(migration.get("tracking_ref"))
    remove_when = _non_empty_string(migration.get("remove_when"))
    missing: list[str] = []
    if tracking_ref is None:
        missing.append("tracking_ref")
    if remove_when is None:
        missing.append("remove_when")
    if missing:
        return "[typescript.migration] missing " + ", ".join(missing)
    if tracking_ref is not None:
        missing_ref = _missing_local_ref(root, tracking_ref)
        if missing_ref is not None:
            return missing_ref
    return None


def _exception_ref(config: Mapping[str, object] | None, key: str) -> str | None:
    exceptions = _typescript_subconfig(config, "exceptions")
    if exceptions is None:
        return None
    value = _non_empty_string(exceptions.get(key))
    if value is None:
        return None
    return value


def _typescript_subconfig(
    config: Mapping[str, object] | None,
    key: str,
) -> Mapping[str, object] | None:
    typescript = config.get("typescript") if config is not None else None
    if not isinstance(typescript, dict):
        return None
    value = cast(Mapping[str, object], typescript).get(key)
    if not isinstance(value, dict):
        return None
    return cast(Mapping[str, object], value)


def _typecheck_config_path(
    root: Path,
    config: Mapping[str, object] | None,
) -> Path | str:
    configured = _typescript_config_value(config, "config")
    relative_path = configured or "tsconfig.json"
    path = Path(relative_path)
    if path.is_absolute() or ".." in path.parts:
        return f"TypeScript config path {relative_path!r} must stay inside the project root"
    return (root / path).resolve()


def _typescript_config_value(config: Mapping[str, object] | None, key: str) -> str | None:
    typescript = config.get("typescript") if config is not None else None
    if not isinstance(typescript, dict):
        return None
    return _non_empty_string(cast(Mapping[str, object], typescript).get(key))


def _load_json_mapping(path: Path) -> tuple[Mapping[str, object], str | None]:
    try:
        text = path.read_text(encoding="utf-8")
        raw_data = json.loads(_strip_json_comments_and_trailing_commas(text))
    except OSError as exc:
        return {}, f"{path.as_posix()}: could not read file: {exc}"
    except json.JSONDecodeError as exc:
        return {}, f"{path.as_posix()}: invalid JSON or JSONC: {exc.msg}"
    if not isinstance(raw_data, dict):
        return {}, f"{path.as_posix()}: expected a JSON object"
    return cast(Mapping[str, object], raw_data), None


def _strip_json_comments_and_trailing_commas(text: str) -> str:
    without_comments = _strip_json_comments(text)
    return _strip_json_trailing_commas(without_comments)


def _strip_json_comments(text: str) -> str:
    output: list[str] = []
    string_state = _JsonStringState()
    index = 0
    while index < len(text):
        if _consume_json_string_char(string_state, text[index], output):
            index += 1
            continue

        if _starts_at(text, index, "//"):
            index = _skip_json_line_comment(text, index)
            continue
        if _starts_at(text, index, "/*"):
            index = _skip_json_block_comment(text, index, output)
            continue
        output.append(text[index])
        index += 1
    return "".join(output)


def _strip_json_trailing_commas(text: str) -> str:
    output: list[str] = []
    string_state = _JsonStringState()
    index = 0
    while index < len(text):
        char = text[index]
        if _consume_json_string_char(string_state, char, output):
            index += 1
            continue
        if char == "," and _next_json_token_closes_container(text, index):
            index += 1
            continue
        output.append(char)
        index += 1
    return "".join(output)


def _consume_json_string_char(
    state: _JsonStringState,
    char: str,
    output: list[str],
) -> bool:
    if state.in_string:
        _update_json_string_state(state, char)
        output.append(char)
        return True
    if char == '"':
        state.in_string = True
        output.append(char)
        return True
    return False


def _update_json_string_state(state: _JsonStringState, char: str) -> None:
    if state.escape:
        state.escape = False
    elif char == "\\":
        state.escape = True
    elif char == '"':
        state.in_string = False


def _starts_at(text: str, index: int, token: str) -> bool:
    return text.startswith(token, index)


def _skip_json_line_comment(text: str, index: int) -> int:
    index += 2
    while index < len(text) and text[index] not in "\r\n":
        index += 1
    return index


def _skip_json_block_comment(text: str, index: int, output: list[str]) -> int:
    index += 2
    while index < len(text):
        if text[index] in "\r\n":
            output.append(text[index])
        if _starts_at(text, index, "*/"):
            return index + 2
        index += 1
    return index


def _next_json_token_closes_container(text: str, comma_index: int) -> bool:
    index = comma_index + 1
    while index < len(text) and text[index].isspace():
        index += 1
    return index < len(text) and text[index] in "}]"


def _css_uses_custom_properties(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if "var(--" in text:
        return True
    return any(line.lstrip().startswith("--") and ":" in line for line in text.splitlines())


def _missing_local_ref(root: Path, value: str) -> str | None:
    if _is_external_ref(value):
        return None
    path_text = _local_ref_path(value)
    if not path_text:
        return None
    path = Path(path_text)
    if path.is_absolute() or ".." in path.parts:
        return f"TypeScript exception ref {value!r} must stay inside the project root"
    resolved = (root / path).resolve()
    if not _is_within_root(root, resolved):
        return f"TypeScript exception ref {value!r} resolves outside the project root"
    if not resolved.exists():
        return f"TypeScript exception ref {value!r} does not exist"
    return None


def _is_external_ref(value: str) -> bool:
    if "://" in value:
        return True
    return "#" in value and not value.startswith(("docs/", "src/", "tests/"))


def _local_ref_path(value: str) -> str:
    return value.split("#", 1)[0]


def _non_empty_string(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _relative_paths(root: Path, paths: Sequence[Path]) -> list[str]:
    return [path.relative_to(root).as_posix() for path in paths]


def _is_within_root(root: Path, path: Path) -> bool:
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return False
    return True


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()
