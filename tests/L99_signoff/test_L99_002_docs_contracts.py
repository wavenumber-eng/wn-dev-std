from __future__ import annotations

import importlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

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


def test_command_manifest_matches_cli_and_design_doc() -> None:
    manifest = load_json_mapping(ROOT / "docs" / "contracts" / "command_manifest.v0.json")
    commands = object_sequence(manifest["commands"])
    help_text = build_parser().format_help()
    design_doc = (ROOT / "docs" / "design" / "cli.html").read_text(encoding="utf-8")

    for command in commands:
        name = cast(str, command["name"])
        module = cast(str, command["module"])
        assert name in help_text
        assert f'data-command="{name}"' in design_doc
        imported = importlib.import_module(module)
        assert hasattr(imported, "register")


def test_interface_manifest_matches_exports_and_design_doc() -> None:
    manifest = load_json_mapping(ROOT / "docs" / "contracts" / "interface_manifest.v0.json")
    interfaces = object_sequence(manifest["interfaces"])
    design_doc = (ROOT / "docs" / "design" / "python-standard.html").read_text(encoding="utf-8")

    for item in interfaces:
        name = cast(str, item["name"])
        module_name, symbol_name = name.rsplit(".", 1)
        module = importlib.import_module(module_name)
        assert hasattr(module, symbol_name)
        assert f'data-interface="{name}"' in design_doc


def test_config_and_exception_schemas_are_json_schema_documents() -> None:
    for name in ("wn_dev_std_config.schema.v0.json", "exceptions.schema.v0.json"):
        schema = load_json_mapping(ROOT / "docs" / "contracts" / name)
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert isinstance(schema["title"], str)
