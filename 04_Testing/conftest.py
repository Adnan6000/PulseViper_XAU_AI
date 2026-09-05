"""
===============================================================================
File        : conftest.py
Project     : PulseViper XAU AI
Purpose     : Pytest repository-root discovery and path configuration
===============================================================================
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


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


def _find_repository_root(
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


PROJECT_ROOT = (
    _find_repository_root(
        Path(__file__).resolve().parent
    )
)

PROJECT_ROOT_STRING = str(
    PROJECT_ROOT
)

if (
    PROJECT_ROOT_STRING
    not in sys.path
):
    sys.path.insert(
        0,
        PROJECT_ROOT_STRING,
    )


@pytest.fixture(
    scope="session",
)
def repo_root() -> Path:

    return PROJECT_ROOT
