"""Reusable JSON contract validation helpers."""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import cast

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

type JsonValue = str | int | float | bool | None | Mapping[str, JsonValue] | Sequence[JsonValue]
type JsonObject = Mapping[str, JsonValue]

SIMPLE_VALIDATION_MESSAGES = {
    "minItems": "must not be empty",
    "minLength": "must be a non-empty string",
    "uniqueItems": "must contain unique items",
}


def validate_json_schema_file(
    instance_path: Path,
    schema_path: Path,
    *,
    instance_label: str | None = None,
    schema_label: str | None = None,
) -> tuple[str, ...]:
    """Validate a JSON instance file against a JSON Schema file."""
    failures: list[str] = []
    instance = _load_json_document(
        instance_path,
        instance_label or instance_path.as_posix(),
        failures,
    )
    schema = _load_json_mapping(schema_path, schema_label or schema_path.as_posix(), failures)
    if failures:
        return tuple(failures)

    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        return (f"{schema_label or schema_path.as_posix()}: invalid JSON Schema: {exc.message}",)

    validator = Draft202012Validator(schema)
    iter_errors = cast(
        Callable[[JsonValue], Iterable[ValidationError]],
        getattr(validator, "iter_errors"),  # noqa: B009 - contains jsonschema's unknown type.
    )
    errors = sorted(
        iter_errors(instance),
        key=lambda error: tuple(str(part) for part in cast(Sequence[object], error.absolute_path)),
    )
    label = instance_label or instance_path.as_posix()
    return tuple(f"{label}: {_format_validation_error(error)}" for error in errors)


def _load_json_document(path: Path, label: str, failures: list[str]) -> JsonValue:
    try:
        return cast(JsonValue, json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"{label}: invalid JSON: {exc}")
        return None


def _load_json_mapping(
    path: Path,
    label: str,
    failures: list[str],
) -> JsonObject:
    document = _load_json_document(path, label, failures)
    if isinstance(document, dict):
        return cast(JsonObject, document)
    if not failures:
        failures.append(f"{label}: JSON Schema document must be an object")
    return {}


def _format_validation_error(error: ValidationError) -> str:
    path = _json_path(tuple(error.absolute_path))
    validator = str(error.validator)
    if validator == "type":
        return f"{path} must be {_expected_type_name(cast(object, error.validator_value))}"
    if validator == "required":
        return f"{path} missing required property {_quoted_required_property(error.message)}"
    if validator == "additionalProperties":
        return f"{path} has unsupported field {_quoted_additional_property(error.message)}"
    if validator == "const":
        return f"{path} must equal {error.validator_value!r}"
    if validator == "enum":
        return f"{path} must be one of {_enum_values(cast(object, error.validator_value))}"
    if validator in {"anyOf", "oneOf"}:
        return f"{path} must satisfy one schema alternative"
    if validator in SIMPLE_VALIDATION_MESSAGES:
        return f"{path} {SIMPLE_VALIDATION_MESSAGES[validator]}"
    return f"{path}: {error.message}"


def _json_path(parts: Sequence[object]) -> str:
    if not parts:
        return "document"
    text = ""
    for part in parts:
        if isinstance(part, int):
            text += f"[{part}]"
        elif text:
            text += f".{part}"
        else:
            text = str(part)
    return text


def _expected_type_name(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " or ".join(str(item) for item in cast(list[object], value))
    return str(value)


def _quoted_required_property(message: str) -> str:
    match = re.match(r"'([^']+)' is a required property", message)
    return repr(match.group(1)) if match else message


def _quoted_additional_property(message: str) -> str:
    match = re.search(r"\('([^']+)' was unexpected\)", message)
    return repr(match.group(1)) if match else message


def _enum_values(value: object) -> str:
    if not isinstance(value, list):
        return str(value)
    return ", ".join(repr(item) for item in cast(list[object], value))
