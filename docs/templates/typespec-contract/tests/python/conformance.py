"""Independent Python consumer for the shared contract vectors."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ID = "https://schemas.example.invalid/catalog/snapshot/v1.json"


def load_json(path: Path) -> object:
    """Load one JSON document."""
    return json.loads(path.read_text(encoding="utf-8"))


def snapshot_schema() -> object:
    """Find the generated schema by stable identity rather than filename."""
    for path in sorted((ROOT / "generated" / "schema").glob("*.json")):
        document = load_json(path)
        if isinstance(document, dict) and document.get("$id") == SCHEMA_ID:
            return document
    raise RuntimeError("catalog snapshot schema was not generated")


def main() -> None:
    """Validate the shared accepted and rejected payloads."""
    validator = Draft202012Validator(snapshot_schema())
    valid = load_json(ROOT / "fixtures" / "catalog-snapshot.valid.json")
    invalid = load_json(ROOT / "fixtures" / "catalog-snapshot.invalid.json")
    if list(validator.iter_errors(valid)):
        raise SystemExit("valid vector did not conform")
    if not list(validator.iter_errors(invalid)):
        raise SystemExit("invalid vector unexpectedly conformed")


if __name__ == "__main__":
    main()
