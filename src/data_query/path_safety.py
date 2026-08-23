"""Filesystem safety checks for report output destinations."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path


def _identity(path: Path) -> Path:
    """Return a normalized absolute identity without requiring the path to exist."""

    return path.expanduser().resolve(strict=False)


def find_output_path_collision(input_path: Path, outputs: Mapping[str, Path | None]) -> str | None:
    """Return a descriptive error when outputs would overwrite input or each other."""

    input_identity = _identity(input_path)
    seen: dict[Path, str] = {}

    for label, path in outputs.items():
        if path is None:
            continue
        identity = _identity(path)
        if identity == input_identity:
            return f"{label} must not overwrite input database"
        previous = seen.get(identity)
        if previous is not None:
            return f"output paths must be distinct: {previous} and {label}"
        seen[identity] = label

    return None
