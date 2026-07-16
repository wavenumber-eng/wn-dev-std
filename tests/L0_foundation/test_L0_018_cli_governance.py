from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from wn_dev_std.checks import CheckResult, run_audit_checks
from wn_dev_std.standards import STANDARD_VERSION


def test_docs_cli_accepts_aggregate_design_doc_and_surface_refs(tmp_path: Path) -> None:
    write_cli_repo(tmp_path)

    result = scope_result(tmp_path)

    assert result.passed
    assert "1 CLI command" in result.detail


def test_docs_cli_fails_missing_design_section(tmp_path: Path) -> None:
    write_cli_repo(tmp_path, design_command="other")

    result = scope_result(tmp_path)

    assert not result.passed
    assert "missing data-command='build'" in result.detail


def test_docs_cli_fails_nested_leaf_name_without_canonical_path(tmp_path: Path) -> None:
    write_cli_repo(
        tmp_path,
        commands=[
            command_entry(name="list", data_command="plan list"),
            command_entry(name="list", data_command="log list"),
        ],
        design_sections=("plan list", "log list"),
    )

    result = scope_result(tmp_path)

    assert not result.passed
    assert "duplicate command identity 'list'" in result.detail


def test_docs_cli_inventory_provider_detects_parser_drift(tmp_path: Path) -> None:
    write_cli_repo(
        tmp_path,
        config_extra=dedent(
            """
            [documentation.cli.inventory_provider]
            kind = "static_json"
            path = "docs/contracts/parser_inventory.json"
            """
        ),
    )
    write_file(
        tmp_path / "docs" / "contracts" / "parser_inventory.json",
        '{ "command_paths": ["build", "release"] }\n',
    )

    result = scope_result(tmp_path)

    assert not result.passed
    assert "inventory provider commands missing from manifest: release" in result.detail


def test_docs_cli_fails_invalid_enforced_status_without_disabling_evidence(
    tmp_path: Path,
) -> None:
    write_cli_repo(
        tmp_path,
        commands=[command_entry(include_surface_ref=False)],
        config_extra='enforced_statuses = ["pubic"]',
    )

    result = scope_result(tmp_path)

    assert not result.passed
    assert "documentation.cli.enforced_statuses[1]: invalid status 'pubic'" in result.detail
    assert "enforced command needs surface_ref" in result.detail


def test_docs_cli_fails_invalid_enforced_status_for_v0_manifest(tmp_path: Path) -> None:
    write_v0_cli_repo(
        tmp_path,
        config_extra='enforced_statuses = ["pubic"]',
    )

    result = scope_result(tmp_path)

    assert not result.passed
    assert "documentation.cli.enforced_statuses[1]: invalid status 'pubic'" in result.detail


def test_docs_cli_a0_path_rejects_legacy_payload_and_keeps_a0_evidence_rules(
    tmp_path: Path,
) -> None:
    write_cli_repo(
        tmp_path,
        commands=[command_entry(include_surface_ref=False)],
    )
    write_file(
        tmp_path / "docs" / "contracts" / "command_manifest.a0.json",
        legacy_schema_manifest([command_entry(include_surface_ref=False)]),
    )

    result = scope_result(tmp_path)

    assert not result.passed
    assert "a0 manifest path requires schema 'wn_dev_std.command_manifest.a0'" in result.detail
    assert "migration command when one exists" in result.detail
    assert "document missing required property 'schema'" in result.detail


def test_docs_cli_fails_manifest_path_escape_without_crashing(tmp_path: Path) -> None:
    write_file(
        tmp_path / "dev-std.toml",
        dedent(
            f"""
            standard_version = "{STANDARD_VERSION}"
            profile = "python-package"

            [documentation.cli]
            manifest_path = "../outside_manifest.json"
            """
        ).lstrip(),
    )

    result = scope_result(tmp_path)

    assert not result.passed
    assert "documentation.cli.manifest_path escapes repository root" in result.detail


def test_docs_cli_fails_contract_ref_that_normalizes_outside_contracts(
    tmp_path: Path,
) -> None:
    write_cli_repo(
        tmp_path,
        commands=[
            command_entry(
                extra_fields=(
                    '"config_contracts": ['
                    '{"path": "docs/contracts/../other/schema.json", "mode": "json_schema"}'
                    "]"
                )
            )
        ],
    )
    write_contract_schema(tmp_path / "docs" / "other" / "schema.json")

    result = scope_result(tmp_path)

    assert not result.passed
    assert "contract path must live under docs/contracts" in result.detail


def test_docs_cli_fails_contract_ref_missing_mode(tmp_path: Path) -> None:
    write_cli_repo(
        tmp_path,
        commands=[
            command_entry(
                extra_fields=('"config_contracts": [{"path": "docs/contracts/build.schema.json"}]')
            )
        ],
    )
    write_contract_schema(tmp_path / "docs" / "contracts" / "build.schema.json")

    result = scope_result(tmp_path)

    assert not result.passed
    assert "commands[0].config_contracts[0] missing required property 'mode'" in result.detail


def test_docs_cli_fails_a0_schema_shape_errors(tmp_path: Path) -> None:
    write_cli_repo(
        tmp_path,
        commands=[
            command_entry(
                extra_fields=('"aliases": "b", "requires_extras": "cli", "compatibility": "stable"')
            )
        ],
    )

    result = scope_result(tmp_path)

    assert not result.passed
    assert "commands[0].aliases must be array" in result.detail
    assert "commands[0].requires_extras must be array" in result.detail
    assert "commands[0].compatibility must be object" in result.detail


def test_docs_cli_fails_a0_payload_under_legacy_v0_path(tmp_path: Path) -> None:
    write_v0_cli_repo(tmp_path)
    write_file(
        tmp_path / "docs" / "contracts" / "command_manifest.v0.json",
        manifest([command_entry()]),
    )

    result = scope_result(tmp_path)

    assert not result.passed
    assert "a0 manifest payload belongs in command_manifest.a0.json" in result.detail
    assert "migration command when one exists" in result.detail


def scope_result(root: Path) -> CheckResult:
    results = run_audit_checks(root, ("docs.cli",))
    return next(result for result in results if result.scope == "docs.cli")


def write_cli_repo(
    root: Path,
    *,
    commands: list[str] | None = None,
    design_command: str = "build",
    design_sections: tuple[str, ...] | None = None,
    config_extra: str = "",
) -> None:
    write_file(
        root / "dev-std.toml",
        dedent(
            f"""
            standard_version = "{STANDARD_VERSION}"
            profile = "python-package"

            [documentation.cli]
            manifest_path = "docs/contracts/command_manifest.a0.json"
            {config_extra}
            """
        ).lstrip(),
    )
    section_commands = design_sections if design_sections is not None else (design_command,)
    write_file(root / "docs" / "design" / "cli.html", design_doc(section_commands))
    write_file(
        root / "docs" / "contracts" / "command_manifest.a0.json",
        manifest(commands or [command_entry()]),
    )


def write_v0_cli_repo(
    root: Path,
    *,
    config_extra: str = "",
) -> None:
    write_file(
        root / "dev-std.toml",
        dedent(
            f"""
            standard_version = "{STANDARD_VERSION}"
            profile = "python-package"

            [documentation.cli]
            manifest_path = "docs/contracts/command_manifest.v0.json"
            {config_extra}
            """
        ).lstrip(),
    )
    write_file(root / "docs" / "design" / "cli.html", design_doc(("build",)))
    write_file(
        root / "docs" / "contracts" / "command_manifest.v0.json",
        dedent(
            """
            {
              "schema_version": "2026.6.27",
              "commands": [
                {
                  "name": "build",
                  "description": "Build project artifacts.",
                  "design_doc": "docs/design/cli.html",
                  "data_command": "build"
                }
              ]
            }
            """
        ).lstrip(),
    )


def command_entry(
    *,
    name: str = "build",
    data_command: str = "build",
    include_surface_ref: bool = True,
    extra_fields: str = "",
) -> str:
    path = ", ".join(f'"{part}"' for part in name.split())
    fields = [
        f'"path": [{path}]',
        f'"name": "{name}"',
        '"status": "public"',
        '"summary": "Build project artifacts."',
        '"design_doc": "docs/design/cli.html"',
        f'"data_command": "{data_command}"',
    ]
    if include_surface_ref:
        fields.append(f'"surface_ref": "core.cli.{data_command.replace(" ", ".")}"')
    if extra_fields:
        fields.append(extra_fields)
    body = ",\n          ".join(fields)
    return "{\n          " + body + "\n        }"


def manifest(commands: list[str]) -> str:
    return (
        '{\n  "schema": "wn_dev_std.command_manifest.a0",\n  "commands": [\n    '
        + ",\n    ".join(commands)
        + "\n  ]\n}\n"
    )


def legacy_schema_manifest(commands: list[str]) -> str:
    return (
        '{\n  "schema_version": "2026.6.27",\n  "commands": [\n    '
        + ",\n    ".join(commands)
        + "\n  ]\n}\n"
    )


def design_doc(section_commands: tuple[str, ...]) -> str:
    sections = "\n".join(
        f'<section data-command="{command}"><h2>{command}</h2></section>'
        for command in section_commands
    )
    return dedent(
        f"""
        <!doctype html>
        <html lang="en">
        <body data-doc-status="accepted">
        {sections}
        </body>
        </html>
        """
    ).lstrip()


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_contract_schema(path: Path) -> None:
    write_file(
        path,
        dedent(
            """
            {
              "$schema": "https://json-schema.org/draft/2020-12/schema",
              "title": "Build Config",
              "type": "object"
            }
            """
        ).lstrip(),
    )
