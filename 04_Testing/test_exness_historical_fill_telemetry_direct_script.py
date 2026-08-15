"""
Regression test for direct-script project-root bootstrap.

The historical operation must be runnable as:

    python 04_Testing/exness_historical_fill_telemetry_operation.py --help

without requiring PYTHONPATH manipulation.
"""

from __future__ import annotations

import subprocess
import sys

from pathlib import Path

import pytest


pytestmark = pytest.mark.offline


def test_direct_script_help_bootstraps_project_root() -> None:

    project_root = (
        Path(
            __file__
        )
        .resolve()
        .parents[
            1
        ]
    )

    script = (
        project_root
        /
        "04_Testing"
        /
        "exness_historical_fill_telemetry_operation.py"
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(
                script
            ),
            "--help",
        ],
        cwd=project_root,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert completed.returncode == 0

    stdout_lower = (
        completed
        .stdout
        .lower()
    )

    stderr_lower = (
        completed
        .stderr
        .lower()
    )

    assert (
        "historical xau entry-fill audit"
        in stdout_lower
    )

    assert (
        "modulenotfounderror"
        not in stderr_lower
    )

    assert (
        "no module named '02_ai'"
        not in stderr_lower
    )