from __future__ import annotations

import json
from pathlib import Path

from test_L0_021_rust_policy import (
    named_result,
    run_language_checks,
    workspace_manifest,
    write_file,
    write_minimal_rust_project,
    write_workspace_member_manifest,
)


def test_syntax_aware_hygiene_covers_rust_function_forms(tmp_path: Path) -> None:
    write_minimal_rust_project(tmp_path)
    write_file(
        tmp_path / "src" / "main.rs",
        """macro_rules! make_function { ($name:ident) => { fn $name() {} }; }

#[inline]
async fn generic<T: Copy>(a: T, b: T, c: T, d: T, e: T, f: T, g: T) {}

trait Run { fn run(&self); }
struct App;
impl Run for App {
    fn run(&self) {}
}
impl App {
    fn method(&self, a: i32, b: i32, c: i32, d: i32, e: i32, f: i32) {}
}

#[cfg(test)]
mod tests {
    #[test]
    fn attributed_test() {}
}

fn main() { make_function!(from_macro); }
""",
    )

    hygiene = named_result(run_language_checks(tmp_path), "Rust structural hygiene")

    assert hygiene.passed, hygiene.detail


def test_parameter_limit_passes_at_seven_and_fails_at_eight(tmp_path: Path) -> None:
    write_minimal_rust_project(tmp_path)
    write_file(
        tmp_path / "src" / "main.rs",
        "fn boundary(a:i32,b:i32,c:i32,d:i32,e:i32,f:i32,g:i32) {}\n",
    )
    assert named_result(run_language_checks(tmp_path), "Rust structural hygiene").passed

    write_file(
        tmp_path / "src" / "main.rs",
        "fn boundary(a:i32,b:i32,c:i32,d:i32,e:i32,f:i32,g:i32,h:i32) {}\n",
    )
    hygiene = named_result(run_language_checks(tmp_path), "Rust structural hygiene")

    assert not hygiene.passed
    assert "max_parameters=8 exceeds 7" in hygiene.detail


def test_production_and_test_function_line_limits_have_distinct_boundaries(
    tmp_path: Path,
) -> None:
    write_minimal_rust_project(tmp_path)
    write_file(tmp_path / "src" / "main.rs", rust_function("production", 100))
    assert named_result(run_language_checks(tmp_path), "Rust structural hygiene").passed

    write_file(tmp_path / "src" / "main.rs", rust_function("production", 101))
    hygiene = named_result(run_language_checks(tmp_path), "Rust structural hygiene")
    assert not hygiene.passed
    assert "max_function_lines=101 exceeds 100" in hygiene.detail

    write_file(tmp_path / "src" / "main.rs", "fn main() {}\n")
    write_file(tmp_path / "tests" / "long.rs", "#[test]\n" + rust_function("test_case", 150))
    assert named_result(run_language_checks(tmp_path), "Rust structural hygiene").passed

    write_file(tmp_path / "tests" / "long.rs", "#[test]\n" + rust_function("test_case", 151))
    hygiene = named_result(run_language_checks(tmp_path), "Rust structural hygiene")
    assert not hygiene.passed
    assert "max_test_function_lines=151 exceeds 150" in hygiene.detail


def test_file_line_limit_passes_at_1000_and_fails_at_1001(tmp_path: Path) -> None:
    write_minimal_rust_project(tmp_path)
    write_file(tmp_path / "src" / "main.rs", "fn main() {}\n" + "// pad\n" * 999)
    assert named_result(run_language_checks(tmp_path), "Rust structural hygiene").passed

    write_file(tmp_path / "src" / "main.rs", "fn main() {}\n" + "// pad\n" * 1000)
    hygiene = named_result(run_language_checks(tmp_path), "Rust structural hygiene")

    assert not hygiene.passed
    assert "max_file_lines=1001 exceeds 1000" in hygiene.detail


def test_complexity_and_nesting_limits_fail_immediately_beyond_boundary(
    tmp_path: Path,
) -> None:
    write_minimal_rust_project(tmp_path)
    write_file(tmp_path / "src" / "main.rs", branch_function(9))
    assert named_result(run_language_checks(tmp_path), "Rust structural hygiene").passed

    write_file(tmp_path / "src" / "main.rs", branch_function(10))
    hygiene = named_result(run_language_checks(tmp_path), "Rust structural hygiene")
    assert not hygiene.passed
    assert "max_cyclomatic_complexity=11 exceeds 10" in hygiene.detail

    write_file(tmp_path / "src" / "main.rs", nested_function(4))
    assert named_result(run_language_checks(tmp_path), "Rust structural hygiene").passed

    write_file(tmp_path / "src" / "main.rs", nested_function(5))
    hygiene = named_result(run_language_checks(tmp_path), "Rust structural hygiene")
    assert not hygiene.passed
    assert "max_nesting=5 exceeds 4" in hygiene.detail


def test_generated_vendor_and_build_output_are_excluded_without_hiding_owned_rust(
    tmp_path: Path,
) -> None:
    write_minimal_rust_project(tmp_path)
    over_limit = "fn generated(a:i32,b:i32,c:i32,d:i32,e:i32,f:i32,g:i32,h:i32) {}\n"
    for part in ("generated", "vendor", "third_party", "target", "build", "bindings"):
        write_file(tmp_path / "src" / part / "ignored.rs", over_limit)
    write_file(tmp_path / "src" / "owned" / "kept.rs", "fn owned() {}\n")

    hygiene = named_result(run_language_checks(tmp_path), "Rust structural hygiene")

    assert hygiene.passed, hygiene.detail


def test_reviewed_exception_requires_reason_and_stale_entries_fail(tmp_path: Path) -> None:
    write_minimal_rust_project(tmp_path)
    write_file(
        tmp_path / "src" / "main.rs",
        "fn legacy(a:i32,b:i32,c:i32,d:i32,e:i32,f:i32,g:i32,h:i32) {}\n",
    )
    append_hygiene(
        tmp_path,
        """
[[exceptions]]
id = "legacy-api"
path = "src/main.rs"
item = "legacy"
rule = "max_parameters"
max_value = 8
reason = "Matches a reviewed wire protocol callback."
review_trigger = "Remove when protocol v2 ships."
""",
    )
    assert named_result(run_language_checks(tmp_path), "Rust structural hygiene").passed

    config = (tmp_path / "rust-hygiene.toml").read_text(encoding="utf-8")
    config_without_maximum = config.replace("max_value = 8\n", "")
    write_file(tmp_path / "rust-hygiene.toml", config_without_maximum)
    hygiene = named_result(run_language_checks(tmp_path), "Rust structural hygiene")
    assert not hygiene.passed
    assert "exceptions[1].max_value must be a positive integer" in hygiene.detail

    config_without_reason = config.replace(
        'reason = "Matches a reviewed wire protocol callback."\n',
        "",
    )
    write_file(tmp_path / "rust-hygiene.toml", config_without_reason)
    hygiene = named_result(run_language_checks(tmp_path), "Rust structural hygiene")
    assert not hygiene.passed
    assert "exceptions[1].reason is required" in hygiene.detail

    write_file(tmp_path / "src" / "main.rs", "fn legacy() {}\n")
    write_file(tmp_path / "rust-hygiene.toml", config)
    hygiene = named_result(run_language_checks(tmp_path), "Rust structural hygiene")
    assert not hygiene.passed
    assert "stale Rust hygiene exception" in hygiene.detail


def test_trait_methods_have_trait_qualified_exception_identities(tmp_path: Path) -> None:
    write_minimal_rust_project(tmp_path)
    parameters = "&self,a:i32,b:i32,c:i32,d:i32,e:i32,f:i32,g:i32"
    write_file(
        tmp_path / "src" / "main.rs",
        f"trait A {{ fn run({parameters}) {{}} }}\ntrait B {{ fn run({parameters}) {{}} }}\n",
    )
    append_hygiene(
        tmp_path,
        """
[[exceptions]]
id = "trait-a-run"
path = "src/main.rs"
item = "A::run"
rule = "max_parameters"
max_value = 8
reason = "Trait A preserves its reviewed callback contract."
review_trigger = "Remove with callback contract v2."
""",
    )

    hygiene = named_result(run_language_checks(tmp_path), "Rust structural hygiene")

    assert not hygiene.passed
    assert "B::run max_parameters=8 exceeds 7" in hygiene.detail
    assert "A::run max_parameters" not in hygiene.detail


def test_reviewed_exception_fails_when_measured_value_grows(tmp_path: Path) -> None:
    write_minimal_rust_project(tmp_path)
    write_file(
        tmp_path / "src" / "main.rs",
        "fn legacy(a:i32,b:i32,c:i32,d:i32,e:i32,f:i32,g:i32,h:i32) {}\n",
    )
    append_hygiene(
        tmp_path,
        """
[[exceptions]]
id = "legacy-api"
path = "src/main.rs"
item = "legacy"
rule = "max_parameters"
max_value = 8
reason = "The reviewed callback currently has eight parameters."
review_trigger = "Remove with callback contract v2."
""",
    )
    assert named_result(run_language_checks(tmp_path), "Rust structural hygiene").passed

    parameters = ",".join(f"p{index}:i32" for index in range(20))
    write_file(tmp_path / "src" / "main.rs", f"fn legacy({parameters}) {{}}\n")
    hygiene = named_result(run_language_checks(tmp_path), "Rust structural hygiene")

    assert not hygiene.passed
    assert "max_parameters=20 exceeds accepted maximum 8" in hygiene.detail


def test_cfg_test_substrings_do_not_relax_production_function_limit(tmp_path: Path) -> None:
    write_minimal_rust_project(tmp_path)
    write_file(
        tmp_path / "src" / "main.rs",
        "#[cfg(not(test))]\n"
        + rust_function("not_a_test", 101)
        + "#[cfg_attr(test, inline)]\n"
        + rust_function("conditional_attribute", 101),
    )

    hygiene = named_result(run_language_checks(tmp_path), "Rust structural hygiene")

    assert not hygiene.passed
    assert "not_a_test max_function_lines=101 exceeds 100" in hygiene.detail
    assert "conditional_attribute max_function_lines=101 exceeds 100" in hygiene.detail
    assert "max_test_function_lines" not in hygiene.detail


def test_exact_cfg_and_namespaced_test_attributes_receive_test_limit(tmp_path: Path) -> None:
    write_minimal_rust_project(tmp_path)
    write_file(
        tmp_path / "src" / "main.rs",
        "#[cfg(test)]\n"
        + rust_function("test_helper", 150)
        + '#[tokio::test(flavor = "current_thread")]\n'
        + "async "
        + rust_function("async_test", 150),
    )

    hygiene = named_result(run_language_checks(tmp_path), "Rust structural hygiene")

    assert hygiene.passed, hygiene.detail


def test_nested_function_branches_do_not_count_toward_outer_complexity(tmp_path: Path) -> None:
    write_minimal_rust_project(tmp_path)
    inner_branches = "        if value > 0 {}\n" * 10
    write_file(
        tmp_path / "src" / "main.rs",
        "fn outer(value: i32) {\n"
        "    fn inner(value: i32) {\n" + inner_branches + "    }\n"
        "    inner(value);\n"
        "}\n",
    )

    hygiene = named_result(run_language_checks(tmp_path), "Rust structural hygiene")

    assert not hygiene.passed
    assert "outer::inner max_cyclomatic_complexity=11 exceeds 10" in hygiene.detail
    assert "src/main.rs:outer max_cyclomatic_complexity" not in hygiene.detail


def test_ratcheted_baseline_allows_only_non_growing_existing_debt(tmp_path: Path) -> None:
    write_minimal_rust_project(tmp_path)
    write_file(
        tmp_path / "src" / "main.rs",
        "fn legacy(a:i32,b:i32,c:i32,d:i32,e:i32,f:i32,g:i32,h:i32) {}\n",
    )
    config = (tmp_path / "rust-hygiene.toml").read_text(encoding="utf-8")
    config = config.replace(
        'mode = "strict"',
        'mode = "ratchet"\nbaseline = "rust-hygiene-baseline.json"',
    )
    write_file(tmp_path / "rust-hygiene.toml", config)
    baseline = {
        "schema": 1,
        "violations": [
            {
                "path": "src/main.rs",
                "item": "legacy",
                "rule": "max_parameters",
                "value": 8,
            }
        ],
    }
    write_file(tmp_path / "rust-hygiene-baseline.json", json.dumps(baseline))
    assert named_result(run_language_checks(tmp_path), "Rust structural hygiene").passed

    write_file(
        tmp_path / "src" / "main.rs",
        "fn legacy(a:i32,b:i32,c:i32,d:i32,e:i32,f:i32,g:i32,h:i32,i:i32) {}\n",
    )
    hygiene = named_result(run_language_checks(tmp_path), "Rust structural hygiene")
    assert not hygiene.passed
    assert "increased Rust hygiene debt" in hygiene.detail

    write_file(
        tmp_path / "src" / "main.rs",
        "fn legacy(a:i32,b:i32,c:i32,d:i32,e:i32,f:i32,g:i32,h:i32) {}\n"
        "fn new_debt(a:i32,b:i32,c:i32,d:i32,e:i32,f:i32,g:i32,h:i32) {}\n",
    )
    hygiene = named_result(run_language_checks(tmp_path), "Rust structural hygiene")
    assert not hygiene.passed
    assert "new Rust hygiene debt" in hygiene.detail


def test_clippy_thresholds_lints_and_failing_rack_lane_are_pinned(tmp_path: Path) -> None:
    write_minimal_rust_project(tmp_path)
    write_file(
        tmp_path / "clippy.toml",
        "too-many-arguments-threshold = 8\n"
        "too-many-lines-threshold = 100\n"
        "cognitive-complexity-threshold = 15\n",
    )
    hygiene = named_result(run_language_checks(tmp_path), "Rust structural hygiene")
    assert not hygiene.passed
    assert "too-many-arguments-threshold" in hygiene.detail

    write_minimal_rust_project(tmp_path)
    cargo = (tmp_path / "Cargo.toml").read_text(encoding="utf-8")
    write_file(tmp_path / "Cargo.toml", cargo.replace('too_many_lines = "deny"\n', ""))
    hygiene = named_result(run_language_checks(tmp_path), "Rust structural hygiene")
    assert not hygiene.passed
    assert "lints.clippy.too_many_lines" in hygiene.detail

    write_minimal_rust_project(tmp_path)
    rack = (tmp_path / "tests" / "rack.toml").read_text(encoding="utf-8")
    write_file(
        tmp_path / "tests" / "rack.toml",
        rack.replace("dev-std audit . --scope language", "echo report-only"),
    )
    hygiene = named_result(run_language_checks(tmp_path), "Rust structural hygiene")
    assert not hygiene.passed
    assert "failing dev-std audit" in hygiene.detail


def test_workspace_member_integration_tests_must_be_in_owned_roots(tmp_path: Path) -> None:
    write_minimal_rust_project(
        tmp_path,
        cargo_toml=workspace_manifest(),
        source_root="crates/app/src",
        extra_config='[rust]\nsource_root = "crates/app/src"\n',
    )
    write_workspace_member_manifest(tmp_path, inherit_metadata=True, inherit_lints=True)
    write_file(tmp_path / "crates" / "app" / "tests" / "integration.rs", "#[test]\nfn works() {}\n")

    hygiene = named_result(run_language_checks(tmp_path), "Rust structural hygiene")
    assert not hygiene.passed
    assert "workspace member crates/app/tests" in hygiene.detail

    policy = (tmp_path / "rust-hygiene.toml").read_text(encoding="utf-8")
    write_file(
        tmp_path / "rust-hygiene.toml",
        policy.replace(
            'source_roots = ["crates/app/src", "tests"]',
            'source_roots = ["crates/app/src", "crates/app/tests", "tests"]',
        ),
    )
    assert named_result(run_language_checks(tmp_path), "Rust structural hygiene").passed


def rust_function(name: str, total_lines: int) -> str:
    body_lines = total_lines - 2
    return f"fn {name}() {{\n" + "    let _value = 1;\n" * body_lines + "}\n"


def branch_function(branches: int) -> str:
    return "fn branches(value: i32) {\n" + "    if value > 0 {}\n" * branches + "}\n"


def nested_function(depth: int) -> str:
    lines = ["fn nested() {"]
    lines.extend("    " * level + "if true {" for level in range(1, depth + 1))
    lines.extend("    " * level + "}" for level in range(depth, 0, -1))
    lines.append("}")
    return "\n".join(lines) + "\n"


def append_hygiene(root: Path, text: str) -> None:
    config = (root / "rust-hygiene.toml").read_text(encoding="utf-8")
    write_file(root / "rust-hygiene.toml", config + text)
