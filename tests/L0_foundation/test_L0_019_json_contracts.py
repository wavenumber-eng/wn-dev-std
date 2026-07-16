from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from wn_dev_std.json_contracts import validate_json_schema_file


def test_json_contracts_report_path_addressed_schema_errors(tmp_path: Path) -> None:
    schema_path = tmp_path / "contracts" / "example.schema.json"
    instance_path = tmp_path / "contracts" / "example.json"
    write_file(
        schema_path,
        """
        {
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "type": "object",
          "additionalProperties": false,
          "required": ["commands"],
          "properties": {
            "commands": {
              "type": "array",
              "items": {
                "type": "object",
                "additionalProperties": false,
                "properties": {
                  "aliases": { "type": "array" },
                  "status": { "enum": ["public"] }
                }
              }
            }
          }
        }
        """,
    )
    write_file(
        instance_path,
        """
        {
          "commands": [
            {
              "aliases": "b",
              "status": "private",
              "unexpected": true
            }
          ]
        }
        """,
    )

    failures = validate_json_schema_file(
        instance_path,
        schema_path,
        instance_label="contracts/example.json",
        schema_label="contracts/example.schema.json",
    )

    assert "contracts/example.json: commands[0].aliases must be array" in failures
    assert "contracts/example.json: commands[0].status must be one of 'public'" in failures
    assert "contracts/example.json: commands[0] has unsupported field 'unexpected'" in failures


def test_json_contracts_report_invalid_schema_documents(tmp_path: Path) -> None:
    schema_path = tmp_path / "contracts" / "broken.schema.json"
    instance_path = tmp_path / "contracts" / "example.json"
    write_file(
        schema_path,
        """
        {
          "$schema": "https://json-schema.org/draft/2020-12/schema",
          "type": 3
        }
        """,
    )
    write_file(instance_path, "{}")

    failures = validate_json_schema_file(
        instance_path,
        schema_path,
        schema_label="contracts/broken.schema.json",
    )

    assert len(failures) == 1
    assert failures[0].startswith("contracts/broken.schema.json: invalid JSON Schema:")


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(text).lstrip(), encoding="utf-8")
