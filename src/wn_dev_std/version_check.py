"""Optional upstream version checks."""

from __future__ import annotations

import http.client
import json
import urllib.error
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast


@dataclass(frozen=True, slots=True)
class UpstreamVersionCheck:
    """Result from a non-failing upstream version check."""

    installed: str
    latest: str | None
    warning: str | None

    @property
    def is_outdated(self) -> bool:
        """Return whether the installed version is older than the upstream version."""
        if self.latest is None:
            return False
        return _version_tuple(self.installed) < _version_tuple(self.latest)

    @property
    def detail(self) -> str:
        """Return a human-readable check detail."""
        if self.warning is not None:
            return self.warning
        if self.latest is None:
            return "upstream version was not checked"
        if self.is_outdated:
            return (
                f"wn-dev-std {self.latest} is available on PyPI; "
                f"installed version is {self.installed}"
            )
        return f"installed wn-dev-std {self.installed} matches latest PyPI version"


def check_pypi_version(
    installed: str,
    *,
    package: str = "wn-dev-std",
    timeout_seconds: float = 3.0,
) -> UpstreamVersionCheck:
    """Check PyPI for the latest released package version."""
    try:
        latest = latest_pypi_version(package, timeout_seconds=timeout_seconds)
    except (
        OSError,
        TimeoutError,
        urllib.error.URLError,
        http.client.HTTPException,
        json.JSONDecodeError,
    ) as exc:
        return UpstreamVersionCheck(
            installed,
            None,
            f"unable to check PyPI for {package} within {timeout_seconds:g}s: {exc}",
        )
    return UpstreamVersionCheck(installed, latest, None)


def latest_pypi_version(package: str, *, timeout_seconds: float = 3.0) -> str:
    """Return the latest package version reported by the PyPI JSON API."""
    request = urllib.request.Request(
        f"https://pypi.org/pypi/{package}/json",
        headers={
            "Accept": "application/json",
            "User-Agent": "wn-dev-std",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        payload: object = json.load(response)
    if not isinstance(payload, dict):
        raise json.JSONDecodeError("expected JSON object", "", 0)
    typed_payload = cast(Mapping[str, object], payload)
    info = typed_payload.get("info")
    if not isinstance(info, dict):
        raise json.JSONDecodeError("expected info object", "", 0)
    typed_info = cast(Mapping[str, object], info)
    version = typed_info.get("version")
    if not isinstance(version, str) or not version:
        raise json.JSONDecodeError("expected info.version string", "", 0)
    return version


def _version_tuple(version: str) -> tuple[int, ...]:
    parts: list[int] = []
    for item in version.split("."):
        try:
            parts.append(int(item))
        except ValueError:
            break
    return tuple(parts)
