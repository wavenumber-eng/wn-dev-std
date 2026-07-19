from __future__ import annotations

import argparse
import importlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, cast

from wn_dev_std.audit_config import AUDIT_SCOPES
from wn_dev_std.cli.main import build_parser

ROOT = Path(__file__).resolve().parents[2]


def load_json_mapping(path: Path) -> Mapping[str, object]:
    return cast(Mapping[str, object], json.loads(path.read_text(encoding="utf-8")))


def object_sequence(value: object) -> Sequence[Mapping[str, object]]:
    if isinstance(value, list):
        raw_items = cast(list[object], value)
        items: list[Mapping[str, object]] = []
        for item in raw_items:
            if not isinstance(item, dict):
                raise TypeError("expected list of objects")
            items.append(cast(Mapping[str, object], item))
        return items
    raise TypeError("expected list of objects")


def string_sequence(value: object) -> Sequence[str]:
    if not isinstance(value, list):
        raise TypeError("expected list of strings")
    items: list[str] = []
    for item in cast(list[object], value):
        if not isinstance(item, str):
            raise TypeError("expected list of strings")
        items.append(item)
    return items


def object_mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, dict):
        return cast(Mapping[str, object], value)
    raise TypeError("expected object")


def properties_of(schema: Mapping[str, object]) -> Mapping[str, object]:
    return object_mapping(schema["properties"])


def test_command_manifest_matches_cli_and_design_doc() -> None:
    manifest = load_json_mapping(ROOT / "docs" / "contracts" / "command_manifest.v0.json")
    commands = object_sequence(manifest["commands"])
    manifest_names = {cast(str, command["name"]) for command in commands}
    manifest_aliases = {
        alias for command in commands for alias in string_sequence(command.get("aliases", []))
    }
    parser = build_parser()
    help_text = parser.format_help()
    design_doc = (ROOT / "docs" / "design" / "cli.html").read_text(encoding="utf-8")
    parser_commands = parser_command_names(parser)

    assert parser_commands <= manifest_names | manifest_aliases
    for command in commands:
        name = cast(str, command["name"])
        module = cast(str, command["module"])
        assert name in help_text
        assert f'data-command="{name}"' in design_doc
        for alias in string_sequence(command.get("aliases", [])):
            assert alias in help_text
            assert alias in design_doc
        imported = importlib.import_module(module)
        assert hasattr(imported, "register")


def parser_command_names(parser: argparse.ArgumentParser) -> set[str]:
    actions = cast(Sequence[Any], parser._actions)
    for action in actions:
        choices = getattr(action, "choices", None)
        if isinstance(choices, dict) and choices:
            typed_choices = cast(Mapping[str, object], choices)
            return {key for key in typed_choices}
    raise AssertionError("parser has no subcommand choices")


def test_interface_manifest_matches_exports_and_design_doc() -> None:
    manifest = load_json_mapping(ROOT / "docs" / "contracts" / "interface_manifest.v0.json")
    interfaces = object_sequence(manifest["interfaces"])

    for item in interfaces:
        name = cast(str, item["name"])
        design_doc_path = ROOT / cast(str, item["design_doc"])
        design_doc = design_doc_path.read_text(encoding="utf-8")
        module_name, symbol_name = name.rsplit(".", 1)
        module = importlib.import_module(module_name)
        assert hasattr(module, symbol_name)
        assert f'data-interface="{name}"' in design_doc


def test_config_and_exception_schemas_are_json_schema_documents() -> None:
    for name in ("wn_dev_std_config.schema.v0.json", "exceptions.schema.v0.json"):
        schema = load_json_mapping(ROOT / "docs" / "contracts" / name)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert isinstance(schema["title"], str)


def test_config_schema_matches_runtime_config_surface() -> None:
    schema = load_json_mapping(ROOT / "docs" / "contracts" / "wn_dev_std_config.schema.v0.json")
    properties = properties_of(schema)

    for key in (
        "standard_version",
        "kind",
        "enabled_scopes",
        "workspace",
        "tests",
        "typescript",
        "rust",
        "documentation",
        "governance",
        "compatibility_pruning",
        "pr_hygiene",
    ):
        assert key in properties

    profile_schema = object_mapping(properties["profile"])
    profile_values = set(string_sequence(profile_schema["enum"]))
    assert "typescript-web-app" in profile_values
    assert "python-ts-app" in profile_values
    assert "rust-app" in profile_values
    assert "rust-firmware" in profile_values

    schema_defs = object_mapping(schema["$defs"])
    audit_scope_def = object_mapping(schema_defs["auditScope"])
    assert set(string_sequence(audit_scope_def["enum"])) == set(AUDIT_SCOPES)

    workspace_properties = properties_of(object_mapping(properties["workspace"]))
    assert "members" in workspace_properties

    governance_properties = properties_of(object_mapping(properties["governance"]))
    governance_html_properties = properties_of(object_mapping(governance_properties["html"]))
    assert "output" in governance_html_properties

    documentation_properties = properties_of(object_mapping(properties["documentation"]))
    documentation_governance_properties = properties_of(
        object_mapping(documentation_properties["governance"])
    )
    assert "output" in documentation_governance_properties

    plan_properties = properties_of(object_mapping(documentation_properties["plans"]))
    assert "roots" in plan_properties
    assert "ignore" in plan_properties

    standard_docs_properties = properties_of(
        object_mapping(documentation_properties["standard_docs"])
    )
    assert "javascript" in standard_docs_properties
    assert "typescript" in standard_docs_properties
    assert "rust" in standard_docs_properties

    typescript_properties = properties_of(object_mapping(properties["typescript"]))
    assert "config" in typescript_properties
    migration_properties = properties_of(object_mapping(typescript_properties["migration"]))
    assert "allow_js" in migration_properties
    assert "tracking_ref" in migration_properties
    assert "remove_when" in migration_properties
    exception_properties = properties_of(object_mapping(typescript_properties["exceptions"]))
    assert "package_extends" in exception_properties
    assert "skip_lib_check" in exception_properties

    rust_properties = properties_of(object_mapping(properties["rust"]))
    assert "source_root" in rust_properties
    rust_firmware_properties = properties_of(object_mapping(rust_properties["firmware"]))
    assert "target" in rust_firmware_properties
    assert "memory_layout" in rust_firmware_properties
    assert "runner" in rust_firmware_properties
    rust_exception_properties = properties_of(object_mapping(rust_properties["exceptions"]))
    assert "ambient_toolchain" in rust_exception_properties
    assert "unsafe" in rust_exception_properties

    compatibility_properties = properties_of(object_mapping(properties["compatibility_pruning"]))
    for key in (
        "root",
        "forbidden_patterns",
        "excluded_parts",
        "excluded_paths",
        "excluded_names",
        "suffixes",
        "names",
    ):
        assert key in compatibility_properties
