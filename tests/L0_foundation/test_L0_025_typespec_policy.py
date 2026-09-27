from __future__ import annotations

import json
import tomllib
from pathlib import Path
from textwrap import dedent
from typing import Any, cast

from config_fixtures import standard_config

from wn_dev_std.checks import run_audit_checks
from wn_dev_std.checks_types import CheckResult
from wn_dev_std.typespec_policy import check_typespec_policy


def test_typespec_contract_capability_passes_for_non_web_project(tmp_path: Path) -> None:
    write_minimal_contract_project(tmp_path, profile="rust-app")

    results = run_audit_checks(tmp_path, ("contracts",))

    assert all(result.passed for result in results), [result.to_dict() for result in results]
    assert named_result(results, "TypeSpec contract units").passed
    assert named_result(results, "TypeSpec toolchain").passed
    assert named_result(results, "TypeSpec projections").passed
    assert named_result(results, "TypeSpec signoff").passed


def test_typespec_contract_capability_requires_declared_paths(tmp_path: Path) -> None:
    write_minimal_contract_project(tmp_path)
    (tmp_path / "contracts" / "library" / "main.tsp").unlink()

    result = named_result(run_audit_checks(tmp_path, ("contracts",)), "TypeSpec contract units")

    assert not result.passed
    assert "entrypoint does not exist" in result.detail


def test_typespec_contract_capability_requires_exact_tool_versions(tmp_path: Path) -> None:
    write_minimal_contract_project(tmp_path, compiler_version="^1.0.0")

    result = named_result(run_audit_checks(tmp_path, ("contracts",)), "TypeSpec toolchain")

    assert not result.passed
    assert "must be exact" in result.detail


def test_required_projection_needs_supported_consumer_evidence(tmp_path: Path) -> None:
    write_minimal_contract_project(
        tmp_path,
        projection_support="experimental",
        consumer_evidence=False,
    )

    result = named_result(run_audit_checks(tmp_path, ("contracts",)), "TypeSpec projections")

    assert not result.passed
    assert "required projection must be supported" in result.detail
    assert "requires consumer_evidence" in result.detail


def test_typespec_contract_capability_rejects_duplicate_unit_ids(tmp_path: Path) -> None:
    write_minimal_contract_project(tmp_path, duplicate_unit=True)

    result = named_result(run_audit_checks(tmp_path, ("contracts",)), "TypeSpec contract units")

    assert not result.passed
    assert "duplicates contract unit id" in result.detail


def test_typespec_contract_capability_rejects_non_table_declaration(tmp_path: Path) -> None:
    write_file(
        tmp_path / "dev-std.toml",
        standard_config("python-package", 'contracts = "invalid"'),
    )

    result = named_result(run_audit_checks(tmp_path, ("contracts",)), "TypeSpec contract units")

    assert not result.passed
    assert result.detail == "contracts must be a table"


def test_typespec_contract_capability_rejects_malformed_nested_array_members(
    tmp_path: Path,
) -> None:
    write_minimal_contract_project(tmp_path)
    config = tomllib.loads((tmp_path / "dev-std.toml").read_text(encoding="utf-8"))
    contracts = cast(dict[str, Any], config["contracts"])
    units = cast(list[Any], contracts["units"])
    unit = cast(dict[str, Any], units[0])
    units.append("invalid")
    cast(list[Any], unit["projections"]).append("invalid")
    unit["exceptions"] = ["invalid"]
    cast(list[Any], unit["emitter_packages"]).append(7)

    results = check_typespec_policy(tmp_path, config)

    assert (
        "contracts.units[1] must be a table"
        in named_result(results, "TypeSpec contract units").detail
    )
    assert (
        "emitter_packages[1] must be a non-empty string"
        in named_result(results, "TypeSpec toolchain").detail
    )
    assert "projections[1] must be a table" in named_result(results, "TypeSpec projections").detail
    assert (
        "exceptions[0] must be a table" in named_result(results, "TypeSpec contract units").detail
    )


def write_minimal_contract_project(
    root: Path,
    *,
    profile: str = "python-package",
    compiler_version: str = "1.0.0",
    projection_support: str = "supported",
    consumer_evidence: bool = True,
    duplicate_unit: bool = False,
) -> None:
    evidence = 'consumer_evidence = ["library-runtime:test"]\n' if consumer_evidence else ""
    unit = dedent(
        f"""
        [[contracts.units]]
        id = "library-domain"
        authority = "typespec"
        root = "contracts/library"
        entrypoint = "contracts/library/main.tsp"
        config = "contracts/library/tspconfig.yaml"
        compatibility = "versioned"
        toolchain_manifest = "package.json"
        lockfile = "package-lock.json"
        emitter_packages = ["@typespec/json-schema"]
        generated_policy = "docs/contracts/generated-policy.md"

        [contracts.units.commands]
        generate = "npm run generate"
        freshness = "npm run check:generated"
        conformance = "npm test"

        [[contracts.units.projections]]
        kind = "json-schema"
        output = "generated/schema"
        required = true
        support = "{projection_support}"
        {evidence.rstrip()}
        """
    ).strip()
    extra_units = "\n\n" + unit if duplicate_unit else ""
    config = standard_config(
        profile,
        f"""
        [contracts]
        {unit}{extra_units}
        """,
    )
    write_file(root / "dev-std.toml", config)
    write_file(
        root / "package.json",
        json.dumps(
            {
                "private": True,
                "devDependencies": {
                    "@typespec/compiler": compiler_version,
                    "@typespec/json-schema": "1.0.0",
                },
            }
        )
        + "\n",
    )
    write_file(root / "package-lock.json", "{}\n")
    write_file(root / "contracts" / "library" / "main.tsp", "model Item { id: string; }\n")
    write_file(root / "contracts" / "library" / "tspconfig.yaml", "emit: []\n")
    write_file(root / "docs" / "contracts" / "generated-policy.md", "# Generated\n")
    write_file(root / "generated" / "schema" / "Item.json", "{}\n")


def named_result(results: tuple[CheckResult, ...], name: str) -> CheckResult:
    return next(result for result in results if result.name == name)


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
