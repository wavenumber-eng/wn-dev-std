"""GitHub pull-request hygiene policy checks and reusable constants."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast


@dataclass(frozen=True, slots=True)
class PrHygieneCheck:
    """Result payload for the public PR hygiene policy."""

    passed: bool
    detail: str


DEFAULT_PR_HYGIENE_WORKFLOW = ".github/workflows/pr-hygiene.yml"
DEFAULT_PULL_REQUEST_TEMPLATE = ".github/pull_request_template.md"
DEFAULT_CONVENTIONAL_COMMIT_TYPES = (
    "build",
    "chore",
    "ci",
    "deps",
    "docs",
    "feat",
    "fix",
    "perf",
    "refactor",
    "release",
    "revert",
    "style",
    "test",
)
AI_ATTRIBUTION_PATTERNS = (
    r"\bclaude\b",
    r"\banthropic\b",
    r"\bgenerated\s+with\b",
    r"\bco-authored-by:\s*(claude|anthropic)\b",
)
REQUIRED_WORKFLOW_TOKENS = (
    ("pull_request:", "pull_request trigger"),
    ("contents: read", "read-only contents permission"),
    ("issues: read", "issue lookup permission"),
    ("pull-requests: read", "pull-request metadata permission"),
    ("actions/github-script@", "github-script step"),
    ("Linked issue:", "Linked issue PR-body gate"),
    ("github.rest.issues.get", "same-repo issue existence check"),
    ("github.rest.pulls.listCommits", "commit enumeration"),
    ("Extended_Pictographic", "emoji/pictographic rejection"),
    ("must use Conventional Commit form", "Conventional Commit message"),
    ("subject.length > 72", "72-character commit subject limit"),
    ("starts with WIP", "WIP rejection"),
    ("response.data.pull_request", "issue-vs-PR rejection"),
    (r"\bclaude\b", "Claude attribution rejection"),
    (r"\banthropic\b", "Anthropic attribution rejection"),
    (r"\bgenerated\s+with\b", "generated-with attribution rejection"),
    (r"\bco-authored-by:\s*(claude|anthropic)\b", "AI co-author rejection"),
)
REQUIRED_PULL_REQUEST_TEMPLATE_TOKENS = (
    ("Linked issue:", "Linked issue prompt"),
    ("Summary", "summary prompt"),
    ("Validation", "validation prompt"),
    ("Conventional Commit", "Conventional Commit title guidance"),
)


def conventional_subject_pattern(
    types: tuple[str, ...] = DEFAULT_CONVENTIONAL_COMMIT_TYPES,
) -> str:
    """Return the Conventional Commit subject regex for the allowed type set."""
    escaped_types = "|".join(re.escape(item) for item in types)
    return rf"^({escaped_types})(\([A-Za-z0-9._-]+\))?!?: .+$"


def is_conventional_subject(
    subject: str,
    types: tuple[str, ...] = DEFAULT_CONVENTIONAL_COMMIT_TYPES,
) -> bool:
    """Return whether a subject uses the configured Conventional Commit shape."""
    return re.fullmatch(conventional_subject_pattern(types), subject) is not None


def check_pr_hygiene_policy(root: Path, raw_config: object) -> PrHygieneCheck:
    """Check that a repository has installed the public PR hygiene policy."""
    config = _config_mapping(raw_config)
    if config is None:
        return _fail("pr_hygiene must be a TOML table")
    if _bool_value(config.get("enabled"), default=True) is False:
        return PrHygieneCheck(True, "public PR hygiene check is disabled")

    workflow_path = _string_value(
        config.get("workflow"),
        default=DEFAULT_PR_HYGIENE_WORKFLOW,
    )
    template_path = _string_value(
        config.get("pull_request_template"),
        default=DEFAULT_PULL_REQUEST_TEMPLATE,
    )
    require_template = _bool_value(config.get("require_pull_request_template"), default=True)

    failures = _workflow_failures(root, workflow_path)
    if require_template:
        failures.extend(_pull_request_template_failures(root, template_path))
    if failures:
        return _fail(_summarize_failures(failures))
    return PrHygieneCheck(
        True,
        f"public PR hygiene workflow is installed at {workflow_path}",
    )


def _workflow_failures(root: Path, relative_path: str) -> list[str]:
    path = root / relative_path
    if not path.exists():
        return [f"missing {relative_path}"]
    text = path.read_text(encoding="utf-8")
    failures = _missing_tokens(text, REQUIRED_WORKFLOW_TOKENS, "workflow")
    pattern = conventional_subject_pattern()
    if pattern not in text:
        failures.append("workflow missing canonical Conventional Commit regex")
    return failures


def _pull_request_template_failures(root: Path, relative_path: str) -> list[str]:
    path = root / relative_path
    if not path.exists():
        return [f"missing {relative_path}"]
    text = path.read_text(encoding="utf-8")
    return _missing_tokens(text, REQUIRED_PULL_REQUEST_TEMPLATE_TOKENS, "pull request template")


def _missing_tokens(
    text: str,
    tokens: tuple[tuple[str, str], ...],
    source: str,
) -> list[str]:
    return [f"{source} missing {label}" for token, label in tokens if token not in text]


def _config_mapping(raw_config: object) -> Mapping[str, object] | None:
    if isinstance(raw_config, dict):
        return cast(Mapping[str, object], raw_config)
    return None


def _string_value(value: object, *, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def _bool_value(value: object, *, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    return default


def _fail(detail: str) -> PrHygieneCheck:
    return PrHygieneCheck(False, detail)


def _summarize_failures(failures: list[str], limit: int = 10) -> str:
    shown = failures[:limit]
    extra = "" if len(failures) <= limit else f"; +{len(failures) - limit} more"
    return "public PR hygiene policy is incomplete: " + "; ".join(shown) + extra
