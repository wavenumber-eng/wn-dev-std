"""Stage clean template resources for wheel inclusion."""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path
from runpy import run_path
from typing import Any, cast

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

_SAFETY = run_path(str(Path(__file__).with_name("template_safety.py")))
IGNORED_WORKING_DIRECTORIES = cast(tuple[str, ...], _SAFETY["IGNORED_WORKING_DIRECTORIES"])
sensitive_template_files = cast(
    Callable[[Path], tuple[Path, ...]],
    _SAFETY["sensitive_template_files"],
)

TEMPLATE_MAPPINGS = (
    ("docs/templates/typespec-contract", "wn_dev_std/templates/typespec-contract"),
    ("docs/templates/web/lit-activity", "wn_dev_std/templates/lit-activity-web"),
)


class CleanTemplateBuildHook(BuildHookInterface):
    """Copy only source-controlled template material into wheel resources."""

    PLUGIN_NAME = "clean-template-resources"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the hook and its per-build staging reference."""
        super().__init__(*args, **kwargs)
        self._staging_root: Path | None = None

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        """Reject sensitive inputs and create a filtered wheel-resource tree."""
        del version
        for source_name, _target_name in TEMPLATE_MAPPINGS:
            source = Path(self.root, source_name)
            offenders = sensitive_template_files(source)
            if offenders:
                relative = ", ".join(path.relative_to(source).as_posix() for path in offenders)
                raise RuntimeError(f"template source contains sensitive file(s): {relative}")
        if self.target_name != "wheel":
            return
        self._staging_root = Path(tempfile.mkdtemp(prefix="wn-dev-std-templates-"))
        force_include = cast(dict[str, str], build_data["force_include"])
        for source_name, target_name in TEMPLATE_MAPPINGS:
            source = Path(self.root, source_name)
            staged = self._staging_root / Path(source_name).name
            shutil.copytree(
                source,
                staged,
                ignore=shutil.ignore_patterns(*IGNORED_WORKING_DIRECTORIES),
            )
            force_include[str(staged)] = target_name

    def finalize(self, version: str, build_data: dict[str, Any], artifact_path: str) -> None:
        """Remove the transient resource tree after the artifact is complete."""
        del version, build_data, artifact_path
        if self._staging_root is not None:
            shutil.rmtree(self._staging_root)
            self._staging_root = None


def get_build_hook() -> type[BuildHookInterface]:
    """Expose the custom hook class to Hatchling."""
    return CleanTemplateBuildHook
