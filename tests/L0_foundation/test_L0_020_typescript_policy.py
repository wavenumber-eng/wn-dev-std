from __future__ import annotations

from pathlib import Path
from textwrap import dedent

from config_fixtures import standard_config

from wn_dev_std.checks import run_audit_checks
from wn_dev_std.checks_types import CheckResult


def test_typescript_web_profile_language_checks_pass_for_minimal_repo(tmp_path: Path) -> None:
    write_minimal_typescript_project(tmp_path)

    results = run_language_checks(tmp_path)

    assert all(result.passed for result in results), [result.to_dict() for result in results]


def test_python_ts_profile_runs_python_and_typescript_checks(tmp_path: Path) -> None:
    write_minimal_typescript_project(tmp_path, profile="python-ts-app")
    write_file(
        tmp_path / "pyproject.toml",
        dedent(
            """
            [project]
            name = "example"
            version = "0.1.0"

            [build-system]
            requires = ["hatchling"]
            build-backend = "hatchling.build"
            """
        ).lstrip(),
    )
    write_file(tmp_path / "uv.lock", "placeholder\n")

    results = run_audit_checks(tmp_path, ("repo", "language"))

    assert named_result(results, "build backend").passed
    assert named_result(results, "uv lock").passed
    assert named_result(results, "TypeScript config").passed
    assert all(result.passed for result in results), [result.to_dict() for result in results]


def test_typescript_profile_requires_tsconfig(tmp_path: Path) -> None:
    write_minimal_typescript_project(tmp_path)
    (tmp_path / "tsconfig.json").unlink()

    config = named_result(run_language_checks(tmp_path), "TypeScript config")

    assert not config.passed
    assert "tsconfig.json is required" in config.detail


def test_typescript_profile_rejects_disabled_guardrail(tmp_path: Path) -> None:
    write_minimal_typescript_project(
        tmp_path,
        tsconfig=tsconfig_json({"strict": False, "exactOptionalPropertyTypes": False}),
    )

    config = named_result(run_language_checks(tmp_path), "TypeScript config")

    assert not config.passed
    assert "compilerOptions.strict must be true" in config.detail
    assert "compilerOptions.exactOptionalPropertyTypes must be true" in config.detail


def test_typescript_profile_rejects_allow_js_without_migration_metadata(
    tmp_path: Path,
) -> None:
    write_minimal_typescript_project(tmp_path, tsconfig=tsconfig_json({"allowJs": True}))

    config = named_result(run_language_checks(tmp_path), "TypeScript config")

    assert not config.passed
    assert "compilerOptions.allowJs requires TypeScript migration metadata" in config.detail


def test_typescript_profile_accepts_schema_url_and_jsonc_syntax(tmp_path: Path) -> None:
    write_minimal_typescript_project(
        tmp_path,
        tsconfig=dedent(
            """
            {
              "$schema": "https://json.schemastore.org/tsconfig",
              "compilerOptions": {
                // Keep URL-like string values intact while removing comments.
                "baseUrl": "https://example.invalid//assets",
                "strict": true,
                "noUncheckedIndexedAccess": true,
                "exactOptionalPropertyTypes": true,
                "noPropertyAccessFromIndexSignature": true,
                "noImplicitOverride": true,
                "noImplicitReturns": true,
                "noFallthroughCasesInSwitch": true,
                "useUnknownInCatchVariables": true,
                "forceConsistentCasingInFileNames": true,
                "isolatedModules": true,
                "verbatimModuleSyntax": true,
                "noEmit": true,
              },
              /* trailing commas are valid JSONC */
            }
            """
        ).lstrip(),
    )

    config = named_result(run_language_checks(tmp_path), "TypeScript config")

    assert config.passed, config.detail


def test_typescript_command_surface_requires_typecheck_not_install_lifecycle(
    tmp_path: Path,
) -> None:
    write_minimal_typescript_project(tmp_path)
    package_json = (tmp_path / "package.json").read_text(encoding="utf-8")
    package_json = package_json.replace(
        '    "typecheck": "tsc -p tsconfig.json --noEmit",\n',
        "",
    )
    write_file(tmp_path / "package.json", package_json)

    command = named_result(run_language_checks(tmp_path), "TypeScript command surface")

    assert not command.passed
    assert "typecheck" in command.detail
    assert "install" not in command.detail
    assert "update" not in command.detail


def test_typescript_profile_rejects_owned_javascript_without_migration_metadata(
    tmp_path: Path,
) -> None:
    write_minimal_typescript_project(tmp_path)
    write_file(tmp_path / "src" / "legacy.js", "window.Legacy = {};\n")

    source = named_result(run_language_checks(tmp_path), "TypeScript source")

    assert not source.passed
    assert "owned JavaScript source requires [typescript.migration]" in source.detail
    assert "src/legacy.js" in source.detail


def test_typescript_profile_allows_owned_javascript_with_migration_metadata(
    tmp_path: Path,
) -> None:
    write_minimal_typescript_project(
        tmp_path,
        extra_config="""
        [typescript.migration]
        allow_js = true
        tracking_ref = "docs/plans/typescript-port/plan.md"
        remove_when = "All owned src JavaScript has been converted."
        """,
        tsconfig=tsconfig_json({"allowJs": True}),
    )
    write_file(tmp_path / "src" / "legacy.js", "window.Legacy = {};\n")
    write_file(tmp_path / "docs" / "plans" / "typescript-port" / "plan.md", "# Port\n")

    results = run_language_checks(tmp_path)
    source = named_result(results, "TypeScript source")

    assert all(result.passed for result in results), [result.to_dict() for result in results]
    assert source.warning


def test_typescript_profile_resolves_local_tsconfig_extends(tmp_path: Path) -> None:
    write_minimal_typescript_project(tmp_path, tsconfig='{"extends": "./tsconfig.strict.json"}\n')
    write_file(tmp_path / "tsconfig.strict.json", tsconfig_json())

    config = named_result(run_language_checks(tmp_path), "TypeScript config")

    assert config.passed


def test_typescript_profile_rejects_package_tsconfig_extends_without_exception(
    tmp_path: Path,
) -> None:
    write_minimal_typescript_project(
        tmp_path,
        tsconfig='{"extends": "@tsconfig/strictest/tsconfig.json"}\n',
    )

    config = named_result(run_language_checks(tmp_path), "TypeScript config")

    assert not config.passed
    assert "not a local auditable tsconfig" in config.detail


def test_typescript_profile_allows_package_tsconfig_extends_with_exception(
    tmp_path: Path,
) -> None:
    write_minimal_typescript_project(
        tmp_path,
        extra_config="""
        [typescript.exceptions]
        package_extends = "docs/design/typescript-config-exception.html"
        """,
        tsconfig='{"extends": "@tsconfig/strictest/tsconfig.json"}\n',
    )
    write_file(
        tmp_path / "docs" / "design" / "typescript-config-exception.html",
        '<!doctype html><html><body data-doc-status="accepted">Exception</body></html>\n',
    )

    config = named_result(run_language_checks(tmp_path), "TypeScript config")

    assert config.passed
    assert config.warning
    assert "@tsconfig/strictest" in config.detail


def test_typescript_profile_rejects_skip_lib_check_without_exception(
    tmp_path: Path,
) -> None:
    write_minimal_typescript_project(tmp_path, tsconfig=tsconfig_json({"skipLibCheck": True}))

    config = named_result(run_language_checks(tmp_path), "TypeScript config")

    assert not config.passed
    assert "compilerOptions.skipLibCheck requires" in config.detail


def test_typescript_profile_accepts_skip_lib_check_with_exception(tmp_path: Path) -> None:
    write_minimal_typescript_project(
        tmp_path,
        extra_config="""
        [typescript.exceptions]
        skip_lib_check = "docs/design/third-party-types.html"
        """,
        tsconfig=tsconfig_json({"skipLibCheck": True}),
    )
    write_file(
        tmp_path / "docs" / "design" / "third-party-types.html",
        '<!doctype html><html><body data-doc-status="accepted">Exception</body></html>\n',
    )

    config = named_result(run_language_checks(tmp_path), "TypeScript config")

    assert config.passed


def run_language_checks(root: Path) -> tuple[CheckResult, ...]:
    return run_audit_checks(root, ("language",))


def named_result(results: tuple[CheckResult, ...], name: str) -> CheckResult:
    return next(result for result in results if result.name == name)


def write_minimal_typescript_project(
    root: Path,
    *,
    profile: str = "typescript-web-app",
    extra_config: str = "",
    tsconfig: str | None = None,
) -> None:
    for relative_path in (
        ".gitattributes",
        ".gitignore",
        "AGENTS.md",
        "README.md",
        "tests/rack.toml",
    ):
        write_file(root / relative_path, "placeholder\n")
    write_file(
        root / "dev-std.toml",
        standard_config(
            profile,
            f"""
            distribution = "internal"
            languages = ["typescript", "css", "html"]
            strict = true
            artifact_policy = "transient-dist"
            {dedent(extra_config).strip()}
            """,
        ),
    )
    write_file(
        root / "package.json",
        dedent(
            """
            {
              "scripts": {
                "build": "tsc -p tsconfig.json",
                "typecheck": "tsc -p tsconfig.json --noEmit",
                "lint": "eslint src --ext .ts,.tsx",
                "test": "node --test",
                "signoff": "npm run typecheck && npm run lint && npm test"
              },
              "devDependencies": {
                "typescript": "^5.9.0"
              }
            }
            """
        ).lstrip(),
    )
    write_file(root / "package-lock.json", "{}\n")
    write_file(root / "tsconfig.json", tsconfig or tsconfig_json())
    write_file(
        root / "src" / "app.ts",
        (
            "export type AppEvent = { readonly kind: 'ready' };\n"
            "export function handleEvent(event: AppEvent): string {\n"
            "  return event.kind;\n"
            "}\n"
        ),
    )
    write_file(
        root / "src" / "style.css",
        ":root { --wn-color-text: #111; }\nbody { color: var(--wn-color-text); }\n",
    )


def tsconfig_json(overrides: dict[str, object] | None = None) -> str:
    options: dict[str, object] = {
        "strict": True,
        "noUncheckedIndexedAccess": True,
        "exactOptionalPropertyTypes": True,
        "noPropertyAccessFromIndexSignature": True,
        "noImplicitOverride": True,
        "noImplicitReturns": True,
        "noFallthroughCasesInSwitch": True,
        "useUnknownInCatchVariables": True,
        "forceConsistentCasingInFileNames": True,
        "isolatedModules": True,
        "verbatimModuleSyntax": True,
        "noEmit": True,
    }
    if overrides:
        options.update(overrides)
    rendered_options = ",\n".join(
        f'    "{key}": {json_value(value)}' for key, value in options.items()
    )
    return '{\n  "compilerOptions": {\n' + rendered_options + "\n  }\n}\n"


def json_value(value: object) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, str):
        return '"' + value + '"'
    raise TypeError(f"unsupported JSON test value: {value!r}")


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
