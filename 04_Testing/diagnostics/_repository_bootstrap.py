"""
===============================================================================
File        : _repository_bootstrap.py
Project     : PulseViper XAU AI
Purpose     : Standalone diagnostic repository-root bootstrap
===============================================================================
"""

from __future__ import annotations

import sys
from pathlib import Path


def _is_repository_root(
    candidate: Path,
) -> bool:

    return (
        (
            candidate
            / "pyproject.toml"
        ).is_file()
        and
        (
            candidate
            / "02_AI"
        ).is_dir()
        and
        (
            candidate
            / "04_Testing"
        ).is_dir()
        and
        (
            candidate
            / "05_Documentation"
        ).is_dir()
    )


def find_repository_root(
    start: Path,
) -> Path:

    resolved_start = start.resolve()

    for candidate in (
        resolved_start,
        *resolved_start.parents,
    ):

        if _is_repository_root(
            candidate
        ):
            return candidate

    raise RuntimeError(
        "REPOSITORY_ROOT_NOT_FOUND"
    )


def ensure_repository_root_on_sys_path(
    start: Path,
) -> Path:

    repository_root = (
        find_repository_root(
            start
        )
    )

    root_string = str(
        repository_root
    )

    if root_string not in sys.path:
        sys.path.insert(
            0,
            root_string,
        )

    return repository_root
