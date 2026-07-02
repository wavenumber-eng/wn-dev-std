"""Shared CLI typing helpers."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from typing import Protocol


class SubparserRegistry(Protocol):
    """Minimal protocol for argparse subparser registries."""

    def add_parser(
        self,
        name: str,
        *,
        aliases: Sequence[str] = (),
        help: str | None = None,
        description: str | None = None,
    ) -> argparse.ArgumentParser:
        """Add a command parser and return the parser object."""
        ...
