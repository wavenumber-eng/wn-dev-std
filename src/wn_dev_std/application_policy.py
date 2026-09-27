"""Opt-in activity-oriented web application audit policy."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from wn_dev_std.checks_types import CheckResult
from wn_dev_std.policy_paths import declared_path as _declared_path
from wn_dev_std.policy_paths import is_within as _within

EXACT_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
IMPORT_RE = re.compile(r"(?:from\s+|import\s*)[\"']([^\"']+)[\"']")
RAW_COLOR_RE = re.compile(
    r"#[0-9a-f]{3,8}\b|\b(?:rgb|hsl|hwb|lab|lch|oklab|oklch|color(?:-mix)?)a?\s*\(",
    re.IGNORECASE,
)
RAW_DESIGN_UNIT_RE = re.compile(
    r"(?<![\w.-])(?:\d*\.)?\d+(?:px|r?em|ex|ch|cap|ic|r?lh|v[whib]|vmin|vmax|cm|mm|in|pt|pc|q)\b",
    re.IGNORECASE,
)
RAW_TIME_RE = re.compile(r"(?<![\w.-])(?:\d*\.)?\d+(?:ms|s)\b", re.IGNORECASE)
CSS_DECLARATION_RE = re.compile(
    r"(?P<property>-{0,2}[a-z][\w-]*)\s*:\s*(?P<value>[^;{}]+?)\s*(?:;|(?=}))",
    re.IGNORECASE,
)
COLOR_PROPERTIES = frozenset(
    {
        "accent-color",
        "background",
        "background-color",
        "border-color",
        "caret-color",
        "color",
        "column-rule-color",
        "fill",
        "outline-color",
        "stroke",
        "text-decoration-color",
    }
)
SAFE_COLOR_WORDS = frozenset(
    {
        "auto",
        "currentcolor",
        "dashed",
        "dotted",
        "double",
        "groove",
        "hidden",
        "inherit",
        "initial",
        "inset",
        "none",
        "outset",
        "revert",
        "revert-layer",
        "ridge",
        "solid",
        "transparent",
        "unset",
    }
)
NETWORK_PRIMITIVE_RE = re.compile(r"\b(?:fetch|WebSocket|EventSource)\b")
LIT_CSS_TEMPLATE_RE = re.compile(r"\bcss\s*`(?P<css>.*?)`", re.DOTALL)


def check_application_policy(
    root: Path,
    config: Mapping[str, object] | None,
) -> tuple[CheckResult, ...]:
    """Validate a declared web-application architecture without running project commands."""
    if config is None or "web_application" not in config:
        return ()
    application = _mapping(config.get("web_application"))
    if application is None:
        return (
            CheckResult(
                "Web application structure",
                False,
                "web_application must be a table",
                "application",
            ),
        )

    structure_failures: list[str] = []
    boundary_failures: list[str] = []
    transport_failures: list[str] = []
    design_failures: list[str] = []
    signoff_failures: list[str] = []

    paths = _application_paths(root, application, structure_failures)
    _check_framework(root, application, structure_failures)
    _check_activity_boundaries(paths.get("activity_core"), boundary_failures)
    _check_transport_ownership(paths, transport_failures)
    _check_design_language(root, application, paths, design_failures)
    _check_signoff(application, signoff_failures)

    return (
        _result("Web application structure", structure_failures),
        _result("Activity kernel boundaries", boundary_failures),
        _result("Backend transport ownership", transport_failures),
        _result("Design language policy", design_failures),
        _result("Application signoff", signoff_failures),
    )


def _application_paths(
    root: Path,
    application: Mapping[str, object],
    failures: list[str],
) -> dict[str, Path]:
    expected = {
        "activity_core": True,
        "composition_root": False,
        "feature_root": True,
        "transport_root": True,
        "shell_root": True,
        "theme_root": True,
        "browser_root": True,
    }
    result: dict[str, Path] = {}
    for key, directory in expected.items():
        value = _declared_path(
            root,
            application.get(key),
            f"web_application.{key}",
            failures,
            directory=directory,
        )
        if value is not None:
            result[key] = value
    result.update(_source_paths(root, application, failures))
    _check_application_shape(application, failures)
    return result


def _source_paths(
    root: Path,
    application: Mapping[str, object],
    failures: list[str],
) -> dict[str, Path]:
    source_roots: list[Path] = []
    source_items = _string_list(
        application.get("source_roots"),
        "web_application.source_roots",
        failures,
    )
    for index, item in enumerate(source_items):
        source = _declared_path(
            root,
            item,
            f"web_application.source_roots[{index}]",
            failures,
            directory=True,
        )
        if source is not None:
            source_roots.append(source)
    if not source_roots:
        failures.append("web_application.source_roots requires at least one existing directory")
    return {f"source_root:{index}": source for index, source in enumerate(source_roots)}


def _check_application_shape(
    application: Mapping[str, object],
    failures: list[str],
) -> None:
    if _string(application.get("dom_policy")) not in {"shadow", "light", "documented-mixed"}:
        failures.append("web_application.dom_policy must be shadow, light, or documented-mixed")
    if _string(application.get("architecture")) != "activity":
        failures.append("web_application.architecture must be 'activity' for this capability")


def _check_framework(
    root: Path,
    application: Mapping[str, object],
    failures: list[str],
) -> None:
    framework = _string(application.get("framework"))
    if framework != "lit":
        failures.append("web_application.framework must be 'lit' for the canonical capability")
        return
    manifest = root / "package.json"
    if not manifest.is_file():
        failures.append("package.json is required to prove the Lit dependency pin")
        return
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"cannot parse package.json: {exc}")
        return
    version = _package_dependencies(payload).get("lit")
    if version is None:
        failures.append("package.json must declare lit")
    elif EXACT_VERSION_RE.fullmatch(version) is None:
        failures.append(f"lit version {version!r} must be exact")


def _check_activity_boundaries(activity_root: Path | None, failures: list[str]) -> None:
    if activity_root is None:
        return
    for path in _typescript_source_files(activity_root):
        _check_activity_source(path, activity_root, failures)


def _check_activity_source(path: Path, activity_root: Path, failures: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    forbidden_tokens = (
        "window.",
        "document.",
        "globalThis.history",
        "fetch",
        "WebSocket",
        "EventSource",
    )
    for token in forbidden_tokens:
        if token in text:
            failures.append(f"{path.name} activity kernel contains forbidden dependency {token!r}")
    for match in IMPORT_RE.finditer(text):
        specifier = match.group(1)
        if specifier == "lit" or not specifier.startswith("."):
            failures.append(f"{path.name} activity kernel imports {specifier!r}")
            continue
        target = (path.parent / specifier).resolve()
        if not _within(activity_root, target):
            failures.append(f"{path.name} activity kernel imports outside activity_core")


def _check_transport_ownership(paths: Mapping[str, Path], failures: list[str]) -> None:
    transport_root = paths.get("transport_root")
    if transport_root is None:
        return
    source_roots = tuple(path for key, path in paths.items() if key.startswith("source_root:"))
    for source_root in source_roots:
        for path in _typescript_source_files(source_root):
            if _within(transport_root, path):
                continue
            text = path.read_text(encoding="utf-8")
            if NETWORK_PRIMITIVE_RE.search(text):
                failures.append(
                    f"{path.relative_to(source_root).as_posix()} constructs a network primitive "
                    "outside transport_root"
                )


def _check_design_language(
    root: Path,
    application: Mapping[str, object],
    paths: Mapping[str, Path],
    failures: list[str],
) -> None:
    design = _mapping(application.get("design_system"))
    if design is None:
        failures.append("web_application.design_system is required")
        return
    mode = _string(design.get("mode"))
    if mode not in {"strict", "ratchet"}:
        failures.append("web_application.design_system.mode must be strict or ratchet")
    token_files = set(_design_paths(root, design, "token_files", False, failures))
    style_roots = _design_paths(root, design, "style_roots", True, failures)
    exception_paths = _exception_paths(root, design, failures)
    if mode == "ratchet":
        _check_ratchet_evidence(exception_paths, failures)
    if mode != "strict":
        return
    _check_strict_styles(root, style_roots, token_files, failures)
    theme_root = paths.get("theme_root")
    if theme_root is None:
        return
    if any(not _within(theme_root, token) for token in token_files):
        failures.append("design-system token_files must be inside theme_root")


def _design_paths(
    root: Path,
    design: Mapping[str, object],
    key: str,
    directory: bool,
    failures: list[str],
) -> list[Path]:
    result: list[Path] = []
    items = _string_list(
        design.get(key),
        f"web_application.design_system.{key}",
        failures,
    )
    for index, item in enumerate(items):
        path = _declared_path(
            root,
            item,
            f"web_application.design_system.{key}[{index}]",
            failures,
            directory=directory,
        )
        if path is not None:
            result.append(path)
    if not result:
        failures.append(f"web_application.design_system.{key} requires at least one existing path")
    return result


def _check_strict_styles(
    root: Path,
    style_roots: Sequence[Path],
    token_files: set[Path],
    failures: list[str],
) -> None:
    for style_root in style_roots:
        for path in _source_files(style_root, ".css"):
            if path in token_files:
                continue
            relative = path.relative_to(root).as_posix()
            text = _without_inline_exceptions(path.read_text(encoding="utf-8"), relative, failures)
            _check_design_declarations(text, relative, failures)
        for path in _typescript_source_files(style_root):
            text = path.read_text(encoding="utf-8")
            relative = path.relative_to(root).as_posix()
            for index, match in enumerate(LIT_CSS_TEMPLATE_RE.finditer(text), start=1):
                label = f"{relative} Lit css template {index}"
                css = _without_inline_exceptions(match.group("css"), label, failures)
                _check_design_declarations(css, label, failures)


def _exception_paths(
    root: Path,
    design: Mapping[str, object],
    failures: list[str],
) -> tuple[Path, ...]:
    result: list[Path] = []
    references = _string_list(
        design.get("exception_refs"),
        "web_application.design_system.exception_refs",
        failures,
    )
    for reference in references:
        path = _declared_path(
            root,
            reference,
            "web_application.design_system.exception_ref",
            failures,
        )
        if path is not None:
            result.append(path)
    return tuple(result)


def _check_ratchet_evidence(paths: Sequence[Path], failures: list[str]) -> None:
    if not paths:
        failures.append("ratchet mode requires an existing exception_ref")
        return
    for path in paths:
        text = path.read_text(encoding="utf-8").lower()
        missing = [term for term in ("scope", "removal trigger", "review") if term not in text]
        if missing:
            failures.append(f"{path.name} ratchet evidence is missing: {', '.join(missing)}")


def _check_design_declarations(text: str, relative: str, failures: list[str]) -> None:
    for match in CSS_DECLARATION_RE.finditer(text):
        property_name = match.group("property").lower()
        if property_name.startswith("--"):
            continue
        value = match.group("value").strip()
        reason = _raw_design_literal(property_name, value)
        if reason is not None:
            failures.append(f"{relative} contains {reason} in {property_name}")


def _raw_design_literal(property_name: str, value: str) -> str | None:
    checks = (
        _raw_color_literal,
        _raw_font_literal,
        _raw_shadow_literal,
        _raw_layer_literal,
        _raw_motion_literal,
        _raw_dimension_literal,
    )
    for check in checks:
        reason = check(property_name, value)
        if reason is not None:
            return reason
    return None


def _raw_color_literal(property_name: str, value: str) -> str | None:
    if _is_color_property(property_name) and _has_raw_color(value):
        return "a raw color outside token_files"
    return None


def _raw_font_literal(property_name: str, value: str) -> str | None:
    if property_name == "font-family" and not _is_governed_value(value):
        return "a raw font family outside token_files"
    return None


def _raw_shadow_literal(property_name: str, value: str) -> str | None:
    if property_name in {"box-shadow", "text-shadow"} and not _is_governed_value(value):
        return "a raw shadow outside token_files"
    return None


def _raw_layer_literal(property_name: str, value: str) -> str | None:
    if property_name == "z-index" and _has_nonzero_number(value):
        return "a raw layer value outside token_files"
    return None


def _raw_motion_literal(property_name: str, value: str) -> str | None:
    if _is_motion_property(property_name) and RAW_TIME_RE.search(value):
        return "a raw motion duration outside token_files"
    return None


def _raw_dimension_literal(property_name: str, value: str) -> str | None:
    if _is_dimension_property(property_name) and RAW_DESIGN_UNIT_RE.search(value):
        return "a raw design dimension outside token_files"
    return None


def _is_color_property(property_name: str) -> bool:
    border_shorthand = re.fullmatch(
        r"border(?:-(?:top|right|bottom|left|block(?:-(?:start|end))?|inline(?:-(?:start|end))?))?",
        property_name,
    )
    return (
        property_name in COLOR_PROPERTIES
        or property_name in {"outline", "text-decoration"}
        or border_shorthand is not None
        or property_name.endswith(("-color", "-fill", "-stroke"))
    )


def _has_raw_color(value: str) -> bool:
    if RAW_COLOR_RE.search(value):
        return True
    without_tokens = re.sub(r"var\([^)]*\)", "", value, flags=re.IGNORECASE)
    without_functions = re.sub(
        r"\b(?:linear-gradient|radial-gradient|conic-gradient|url|image-set)\s*\(",
        "(",
        without_tokens,
        flags=re.IGNORECASE,
    )
    words = re.findall(r"[a-z][a-z-]*", without_functions.lower())
    return any(word not in SAFE_COLOR_WORDS for word in words)


def _is_governed_value(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized.startswith("var(") or normalized in {
        "inherit",
        "initial",
        "none",
        "revert",
        "revert-layer",
        "unset",
    }


def _has_nonzero_number(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized.startswith("var(") or normalized in {"auto", "inherit", "initial", "unset"}:
        return False
    return any(float(number) != 0 for number in re.findall(r"-?(?:\d*\.)?\d+", normalized))


def _is_motion_property(property_name: str) -> bool:
    return property_name.startswith(("animation", "transition"))


def _is_dimension_property(property_name: str) -> bool:
    return property_name.startswith(
        (
            "border-",
            "bottom",
            "column-gap",
            "column-width",
            "flex-basis",
            "font-size",
            "gap",
            "height",
            "inset",
            "left",
            "letter-spacing",
            "margin",
            "max-height",
            "max-width",
            "min-height",
            "min-width",
            "outline-offset",
            "outline-width",
            "padding",
            "right",
            "row-gap",
            "top",
            "width",
        )
    )


def _check_signoff(application: Mapping[str, object], failures: list[str]) -> None:
    commands = _mapping(application.get("commands"))
    if commands is None:
        failures.append("web_application.commands is required")
        return
    for key in ("boundaries", "typecheck", "test", "build", "signoff"):
        if _string(commands.get(key)) is None:
            failures.append(f"web_application.commands.{key} must be a non-empty string")


def _without_inline_exceptions(text: str, relative: str, failures: list[str]) -> str:
    lines = text.splitlines()
    excluded: set[int] = set()
    for index, line in enumerate(lines):
        marker = "design-literal-exception:"
        if marker not in line:
            continue
        reason = line.split(marker, 1)[1].strip().strip("*/# ")
        if not reason:
            failures.append(f"{relative} has a design-literal exception without a rationale")
            continue
        excluded.add(index)
        if index + 1 < len(lines):
            excluded.add(index + 1)
        if index > 0 and ":" in lines[index - 1]:
            excluded.add(index - 1)
    return "\n".join(line for index, line in enumerate(lines) if index not in excluded)


def _result(name: str, failures: Sequence[str]) -> CheckResult:
    if failures:
        return CheckResult(name, False, "; ".join(failures), "application")
    return CheckResult(name, True, "declared application policy passed", "application")


def _source_files(root: Path, suffix: str) -> tuple[Path, ...]:
    return tuple(path for path in root.rglob(f"*{suffix}") if path.is_file())


def _typescript_source_files(root: Path) -> tuple[Path, ...]:
    return tuple(
        path for path in root.rglob("*") if path.is_file() and path.suffix in {".ts", ".tsx"}
    )


def _package_dependencies(payload: object) -> dict[str, str]:
    if not isinstance(payload, dict):
        return {}
    result: dict[str, str] = {}
    package = cast(dict[object, object], payload)
    for key in ("dependencies", "devDependencies"):
        table = package.get(key)
        if isinstance(table, dict):
            for name, version in cast(dict[object, object], table).items():
                if isinstance(name, str) and isinstance(version, str):
                    result[name] = version
    return result


def _mapping(value: object) -> Mapping[str, object] | None:
    if not isinstance(value, dict):
        return None
    return cast(Mapping[str, object], value)


def _string(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _string_list(value: object, label: str, failures: list[str]) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        failures.append(f"{label} must be an array of non-empty strings")
        return ()
    result: list[str] = []
    for index, item in enumerate(cast(list[object], value)):
        if not isinstance(item, str) or not item.strip():
            failures.append(f"{label}[{index}] must be a non-empty string")
            continue
        result.append(item.strip())
    return tuple(result)
