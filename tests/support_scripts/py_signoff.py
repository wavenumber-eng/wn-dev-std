"""Strict AST-based Python hygiene signoff for the reference package."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PRODUCTION_ROOTS = (ROOT / "src" / "wn_dev_std",)
TEST_ROOTS = (ROOT / "tests" / "L0_foundation", ROOT / "tests" / "L99_signoff")
EXCLUDED_PARTS = {"__pycache__", ".venv", "rack_results"}

MAX_PRODUCTION_FILE_LINES = 800
MAX_TEST_FILE_LINES = 1200
MAX_PRODUCTION_FUNCTION_LINES = 80
MAX_TEST_FUNCTION_LINES = 120
MAX_PRODUCTION_CLASS_LINES = 300
MAX_TEST_CLASS_LINES = 400
MAX_PRODUCTION_COMPLEXITY = 8
MAX_TEST_COMPLEXITY = 10
_COMPLEXITY_BRANCH_NODES: tuple[type[ast.AST], ...] = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.Try,
    ast.ExceptHandler,
    ast.IfExp,
    ast.Match,
)


@dataclass(frozen=True, slots=True)
class Violation:
    """A single signoff violation."""

    path: Path
    line: int
    message: str

    def render(self) -> str:
        """Render the violation relative to the repository root."""
        return f"{self.path.relative_to(ROOT)}:{self.line}: {self.message}"


def main() -> int:
    """Run the Python signoff checks."""
    violations: list[Violation] = []
    for root in PRODUCTION_ROOTS:
        violations.extend(_scan_tree(root, production=True))
    for root in TEST_ROOTS:
        violations.extend(_scan_tree(root, production=False))

    if violations:
        for violation in violations:
            print(violation.render())
        return 1

    print("Python signoff passed")
    return 0


def _scan_tree(root: Path, production: bool) -> list[Violation]:
    violations: list[Violation] = []
    for path in sorted(root.rglob("*.py")):
        if _is_excluded(path):
            continue
        violations.extend(_scan_file(path, production))
    return violations


def _scan_file(path: Path, production: bool) -> list[Violation]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    tree = ast.parse(text, filename=str(path))
    violations = _check_file_length(path, lines, production)
    violations.extend(_check_defs(path, tree, production))
    if production:
        violations.extend(_check_no_any(path, tree))
        violations.extend(_check_duplicate_function_bodies(path, tree))
    return violations


def _check_file_length(path: Path, lines: list[str], production: bool) -> list[Violation]:
    max_lines = MAX_PRODUCTION_FILE_LINES if production else MAX_TEST_FILE_LINES
    if len(lines) <= max_lines:
        return []
    return [Violation(path, max_lines + 1, f"file has {len(lines)} lines; max is {max_lines}")]


def _check_defs(path: Path, tree: ast.AST, production: bool) -> list[Violation]:
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            violations.extend(_check_class(path, node, production))
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            violations.extend(_check_function(path, node, production))
    return violations


def _check_class(path: Path, node: ast.ClassDef, production: bool) -> list[Violation]:
    max_lines = MAX_PRODUCTION_CLASS_LINES if production else MAX_TEST_CLASS_LINES
    line_count = _line_count(node)
    if line_count <= max_lines:
        return []
    return [
        Violation(
            path,
            node.lineno,
            f"class {node.name} has {line_count} lines; max is {max_lines}",
        )
    ]


def _check_function(
    path: Path,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    production: bool,
) -> list[Violation]:
    violations: list[Violation] = []
    max_lines = MAX_PRODUCTION_FUNCTION_LINES if production else MAX_TEST_FUNCTION_LINES
    max_complexity = MAX_PRODUCTION_COMPLEXITY if production else MAX_TEST_COMPLEXITY

    line_count = _line_count(node)
    if line_count > max_lines:
        violations.append(
            Violation(
                path,
                node.lineno,
                f"function {node.name} has {line_count} lines; max is {max_lines}",
            )
        )

    complexity = _complexity(node)
    if complexity > max_complexity:
        violations.append(
            Violation(
                path,
                node.lineno,
                f"function {node.name} complexity is {complexity}; max is {max_complexity}",
            )
        )

    violations.extend(_check_annotations(path, node))
    return violations


def _check_annotations(path: Path, node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[Violation]:
    violations: list[Violation] = []
    for arg in _function_args(node):
        if arg.arg in {"self", "cls"}:
            continue
        if arg.annotation is None:
            violations.append(
                Violation(
                    path,
                    arg.lineno,
                    f"argument {arg.arg} in {node.name} lacks annotation",
                )
            )
    if node.returns is None:
        violations.append(
            Violation(
                path,
                node.lineno,
                f"function {node.name} lacks return annotation",
            )
        )
    return violations


def _function_args(node: ast.FunctionDef | ast.AsyncFunctionDef) -> tuple[ast.arg, ...]:
    args = node.args
    return (
        *args.posonlyargs,
        *args.args,
        *args.kwonlyargs,
        *([args.vararg] if args.vararg is not None else []),
        *([args.kwarg] if args.kwarg is not None else []),
    )


def _check_no_any(path: Path, tree: ast.AST) -> list[Violation]:
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if _is_any_reference(node):
            violations.append(
                Violation(path, _node_line(node), "typing.Any is not allowed in production code")
            )
    return violations


def _is_any_reference(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return node.id == "Any"
    if isinstance(node, ast.Attribute):
        return node.attr == "Any"
    return False


def _check_duplicate_function_bodies(path: Path, tree: ast.AST) -> list[Violation]:
    seen: dict[str, str] = {}
    violations: list[Violation] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        body_key = ast.dump(ast.Module(body=node.body, type_ignores=[]), include_attributes=False)
        if body_key in seen and len(node.body) > 1:
            violations.append(
                Violation(
                    path,
                    node.lineno,
                    f"function {node.name} duplicates body of {seen[body_key]}",
                )
            )
        seen[body_key] = node.name
    return violations


def _complexity(node: ast.AST) -> int:
    score = 1
    for child in ast.walk(node):
        if isinstance(child, _COMPLEXITY_BRANCH_NODES):
            score += 1
        elif isinstance(child, ast.BoolOp):
            score += max(0, len(child.values) - 1)
    return score


def _line_count(node: ast.AST) -> int:
    end_line = getattr(node, "end_lineno", None)
    start_line = getattr(node, "lineno", None)
    if isinstance(end_line, int) and isinstance(start_line, int):
        return end_line - start_line + 1
    return 1


def _node_line(node: ast.AST) -> int:
    line = getattr(node, "lineno", 1)
    if isinstance(line, int):
        return line
    return 1


def _is_excluded(path: Path) -> bool:
    return any(part in EXCLUDED_PARTS for part in path.parts)


if __name__ == "__main__":
    raise SystemExit(main())
