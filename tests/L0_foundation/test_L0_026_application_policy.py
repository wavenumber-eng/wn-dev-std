from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

import pytest
from config_fixtures import standard_config

from wn_dev_std.checks import run_audit_checks
from wn_dev_std.checks_types import CheckResult


def test_application_capability_passes_for_canonical_layout(tmp_path: Path) -> None:
    write_minimal_application(tmp_path)

    results = run_audit_checks(tmp_path, ("application",))

    assert all(result.passed for result in results), [result.to_dict() for result in results]
    assert named_result(results, "Web application structure").passed
    assert named_result(results, "Activity kernel boundaries").passed
    assert named_result(results, "Backend transport ownership").passed
    assert named_result(results, "Design language policy").passed
    assert named_result(results, "Application signoff").passed


def test_application_capability_requires_exact_lit_version(tmp_path: Path) -> None:
    write_minimal_application(tmp_path, lit_version="^3.3.3")

    result = named_result(run_audit_checks(tmp_path, ("application",)), "Web application structure")

    assert not result.passed
    assert "lit version '^3.3.3' must be exact" in result.detail


def test_application_capability_rejects_non_table_declaration(tmp_path: Path) -> None:
    write_file(
        tmp_path / "dev-std.toml",
        standard_config("typescript-web-app", 'web_application = "invalid"'),
    )

    result = named_result(run_audit_checks(tmp_path, ("application",)), "Web application structure")

    assert not result.passed
    assert result.detail == "web_application must be a table"


def test_application_capability_rejects_malformed_string_array_members(tmp_path: Path) -> None:
    write_minimal_application(tmp_path)
    config = (tmp_path / "dev-std.toml").read_text(encoding="utf-8")
    write_file(
        tmp_path / "dev-std.toml",
        config.replace('source_roots = ["src"]', 'source_roots = ["src", 7]').replace(
            'token_files = ["src/theme/primitives.css"]',
            'token_files = ["src/theme/primitives.css", 7]',
        ),
    )

    results = run_audit_checks(tmp_path, ("application",))

    assert (
        "source_roots[1] must be a non-empty string"
        in named_result(results, "Web application structure").detail
    )
    assert (
        "token_files[1] must be a non-empty string"
        in named_result(results, "Design language policy").detail
    )


def test_activity_kernel_must_remain_rendering_independent(tmp_path: Path) -> None:
    write_minimal_application(tmp_path)
    write_file(tmp_path / "src" / "activity" / "index.ts", 'import { html } from "lit";\n')

    result = named_result(
        run_audit_checks(tmp_path, ("application",)), "Activity kernel boundaries"
    )

    assert not result.passed
    assert "activity kernel imports 'lit'" in result.detail


def test_activity_kernel_checks_tsx_sources(tmp_path: Path) -> None:
    write_minimal_application(tmp_path)
    write_file(tmp_path / "src" / "activity" / "leak.tsx", 'import { html } from "lit";\n')

    result = named_result(
        run_audit_checks(tmp_path, ("application",)), "Activity kernel boundaries"
    )

    assert not result.passed
    assert "activity kernel imports 'lit'" in result.detail


def test_network_primitives_belong_to_transport_root(tmp_path: Path) -> None:
    write_minimal_application(tmp_path)
    write_file(tmp_path / "src" / "features" / "parts.ts", 'fetch("/api/parts");\n')

    result = named_result(
        run_audit_checks(tmp_path, ("application",)), "Backend transport ownership"
    )

    assert not result.passed
    assert "outside transport_root" in result.detail


def test_network_ownership_checks_tsx_sources(tmp_path: Path) -> None:
    write_minimal_application(tmp_path)
    write_file(tmp_path / "src" / "features" / "leak.tsx", 'fetch("/api/parts");\n')

    result = named_result(
        run_audit_checks(tmp_path, ("application",)), "Backend transport ownership"
    )

    assert not result.passed
    assert "leak.tsx constructs a network primitive outside transport_root" in result.detail


def test_strict_design_language_rejects_raw_feature_literals(tmp_path: Path) -> None:
    write_minimal_application(tmp_path)
    write_file(tmp_path / "src" / "features" / "parts.css", ".part { color: #ff0000; }\n")

    result = named_result(run_audit_checks(tmp_path, ("application",)), "Design language policy")

    assert not result.passed
    assert "raw color outside token_files" in result.detail


def test_strict_design_language_checks_inline_lit_css_templates(tmp_path: Path) -> None:
    write_minimal_application(tmp_path)
    write_file(
        tmp_path / "src" / "features" / "parts.ts",
        'import { css } from "lit";\nexport const styles = css`color: #ff0000;`;\n',
    )

    result = named_result(run_audit_checks(tmp_path, ("application",)), "Design language policy")

    assert not result.passed
    assert "Lit css template 1 contains a raw color" in result.detail


@pytest.mark.parametrize(
    ("declaration", "expected"),
    (
        ("color: red", "raw color"),
        ("margin: 2em", "raw design dimension"),
        ('font-family: "Comic Sans MS"', "raw font family"),
        ("z-index: 9999", "raw layer value"),
        ("transition: opacity 1s ease", "raw motion duration"),
        ("box-shadow: 0 1px 3px black", "raw shadow"),
    ),
)
def test_strict_design_language_parses_curated_property_literals(
    tmp_path: Path,
    declaration: str,
    expected: str,
) -> None:
    write_minimal_application(tmp_path)
    write_file(tmp_path / "src" / "features" / "parts.css", f".part {{ {declaration}; }}\n")

    result = named_result(run_audit_checks(tmp_path, ("application",)), "Design language policy")

    assert not result.passed
    assert expected in result.detail


def test_design_language_accepts_narrow_inline_exception(tmp_path: Path) -> None:
    write_minimal_application(tmp_path)
    write_file(
        tmp_path / "src" / "theme" / "layout.css",
        dedent(
            """
            @media (max-width: 48rem) {
              /* design-literal-exception: CSS variables cannot define media-query breakpoints. */
              .layout { display: block; }
            }
            """
        ).strip()
        + "\n",
    )

    result = named_result(run_audit_checks(tmp_path, ("application",)), "Design language policy")

    assert result.passed, result.detail


def test_design_language_rejects_empty_inline_exception_rationale(tmp_path: Path) -> None:
    write_minimal_application(tmp_path)
    write_file(
        tmp_path / "src" / "features" / "parts.css",
        "/* design-literal-exception: */\n.part { margin: 2em; }\n",
    )

    result = named_result(run_audit_checks(tmp_path, ("application",)), "Design language policy")

    assert not result.passed
    assert "without a rationale" in result.detail


def test_ratchet_design_language_requires_reviewed_scope_and_removal_trigger(
    tmp_path: Path,
) -> None:
    write_minimal_application(tmp_path)
    config = (tmp_path / "dev-std.toml").read_text(encoding="utf-8")
    (tmp_path / "dev-std.toml").write_text(
        config.replace('mode = "strict"', 'mode = "ratchet"'),
        encoding="utf-8",
    )

    result = named_result(run_audit_checks(tmp_path, ("application",)), "Design language policy")

    assert not result.passed
    assert "ratchet mode requires an existing exception_ref" in result.detail


def write_minimal_application(root: Path, *, lit_version: str = "3.3.3") -> None:
    config = standard_config(
        "typescript-web-app",
        dedent(
            """
            [typescript]
            config = "tsconfig.json"

            [web_application]
            framework = "lit"
            architecture = "activity"
            activity_core = "src/activity"
            composition_root = "src/application/create-application.ts"
            feature_root = "src/features"
            transport_root = "src/transport"
            shell_root = "src/shell"
            theme_root = "src/theme"
            browser_root = "src/browser"
            source_roots = ["src"]
            dom_policy = "documented-mixed"

            [web_application.design_system]
            mode = "strict"
            style_roots = ["src"]
            token_files = ["src/theme/primitives.css"]
            exception_refs = []

            [web_application.commands]
            boundaries = "npm run lint"
            typecheck = "npm run typecheck"
            test = "npm test"
            build = "npm run build"
            signoff = "npm run signoff"
            """
        ),
    )
    write_file(root / "dev-std.toml", config)
    write_file(
        root / "package.json",
        json.dumps({"private": True, "dependencies": {"lit": lit_version}}) + "\n",
    )
    write_file(root / "tsconfig.json", '{"compilerOptions":{"strict":true}}\n')
    write_file(root / "src" / "activity" / "index.ts", "export type Activity = unknown;\n")
    write_file(root / "src" / "application" / "create-application.ts", "export {};\n")
    write_file(root / "src" / "features" / "index.ts", "export {};\n")
    write_file(root / "src" / "transport" / "http.ts", "export const transport = true;\n")
    write_file(root / "src" / "shell" / "index.ts", "export {};\n")
    write_file(root / "src" / "browser" / "index.ts", "export {};\n")
    write_file(root / "src" / "theme" / "primitives.css", ":root { --space: 8px; }\n")
    write_file(root / "src" / "theme" / "components.css", ".panel { padding: var(--space); }\n")


def named_result(results: tuple[CheckResult, ...], name: str) -> CheckResult:
    return next(result for result in results if result.name == name)


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
