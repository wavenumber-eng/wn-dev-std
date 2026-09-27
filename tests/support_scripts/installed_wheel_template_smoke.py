"""Validate template resources through the installed wheel CLI."""

from __future__ import annotations

import subprocess
import sys
import tarfile
import tempfile
import tomllib
import zipfile
from pathlib import Path, PurePosixPath

FORBIDDEN_PARTS = {
    ".cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "coverage",
    "dist",
    "node_modules",
}
EXPECTED_WHEEL_ROOTS = {
    "wn_dev_std/templates/typespec-contract",
    "wn_dev_std/templates/lit-activity-web",
}


def main() -> int:
    """Inspect archives, copy both templates, and audit the installed copies."""
    distribution = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    version = project_version()
    wheel = single_archive(distribution, f"*{version}*.whl")
    source = single_archive(distribution, f"*{version}*.tar.gz")
    with zipfile.ZipFile(wheel) as archive:
        wheel_names = tuple(archive.namelist())
    with tarfile.open(source, "r:gz") as archive:
        source_names = tuple(member.name for member in archive.getmembers())
    assert_clean_archive(wheel, wheel_names)
    assert_clean_archive(source, source_names)
    for expected in EXPECTED_WHEEL_ROOTS:
        if not any(name.startswith(f"{expected}/") for name in wheel_names):
            raise RuntimeError(f"wheel is missing {expected}")

    if len(sys.argv) < 3:
        raise RuntimeError("pass the explicit installed-wheel wn-dev-std executable path")
    cli_path = Path(sys.argv[2]).resolve()
    if not cli_path.is_file():
        raise RuntimeError(f"installed-wheel CLI does not exist: {cli_path}")
    repository_environment = (Path.cwd() / ".venv").resolve()
    if cli_path.is_relative_to(repository_environment):
        raise RuntimeError("installed-wheel smoke must not use the repository virtual environment")
    cli = str(cli_path)
    with tempfile.TemporaryDirectory(prefix="wn-dev-std-wheel-smoke-") as temporary:
        root = Path(temporary)
        targets = (
            ("typespec-contract", root / "contracts", "contracts"),
            ("lit-activity-web", root / "application", "application"),
        )
        for name, target, scope in targets:
            run((cli, "template", "copy", name, str(target)))
            assert_clean_tree(target)
            run((cli, "audit", str(target), "--scope", scope))
    return 0


def single_archive(directory: Path, pattern: str) -> Path:
    matches = tuple(directory.glob(pattern))
    if len(matches) != 1:
        raise RuntimeError(f"expected one {pattern} archive in {directory}, found {len(matches)}")
    return matches[0]


def project_version() -> str:
    with Path("pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)["project"]
    version = project.get("version")
    if not isinstance(version, str):
        raise RuntimeError("pyproject.toml project.version is missing")
    return version


def assert_clean_archive(archive: Path, names: tuple[str, ...]) -> None:
    offenders = [
        name
        for name in names
        if FORBIDDEN_PARTS.intersection(PurePosixPath(name.replace("\\", "/")).parts)
    ]
    if offenders:
        preview = "\n".join(offenders[:20])
        raise RuntimeError(f"{archive.name} contains transient working paths:\n{preview}")


def assert_clean_tree(root: Path) -> None:
    offenders = [path for path in root.rglob("*") if FORBIDDEN_PARTS.intersection(path.parts)]
    if offenders:
        raise RuntimeError(f"copied template contains transient path: {offenders[0]}")


def run(command: tuple[str, ...]) -> None:
    subprocess.run(command, check=True)


if __name__ == "__main__":
    raise SystemExit(main())
