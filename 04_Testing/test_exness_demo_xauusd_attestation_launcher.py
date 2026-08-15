from __future__ import annotations

import ast
import os
import subprocess
import sys

from pathlib import Path


PROJECT_ROOT = (
    Path(
        __file__
    )
    .resolve()
    .parents[
        1
    ]
)

LAUNCHER = (
    PROJECT_ROOT
    /
    "04_Testing"
    /
    "run_exness_demo_xauusd_context_attestation.py"
)


def test_launcher_exists():

    assert LAUNCHER.is_file()


def test_launcher_imports_operation_after_project_bootstrap():

    source = LAUNCHER.read_text(
        encoding="utf-8"
    )

    assert (
        "PROJECT_ROOT"
        in source
    )

    assert (
        "sys.path.insert"
        in source
    )

    assert (
        "exness_demo_xauusd_context_"
        in source
    )


def test_launcher_help_works_without_pythonpath(
    tmp_path,
):

    environment = dict(
        os.environ
    )

    environment.pop(
        "PYTHONPATH",
        None,
    )

    result = subprocess.run(
        [
            sys.executable,
            str(
                LAUNCHER
            ),
            "--help",
        ],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    assert (
        result.returncode
        ==
        0
    )

    combined = (
        result.stdout
        +
        result.stderr
    )

    assert (
        "--symbol"
        in combined
    )

    assert (
        "--probe-bars"
        in combined
    )

    assert (
        "--account-scope-id"
        in combined
    )


def test_launcher_has_no_execution_authority():

    tree = ast.parse(
        LAUNCHER.read_text(
            encoding="utf-8"
        )
    )

    forbidden = {
        "order_send",
        "order_check",
        "positions_get",
        "positions_total",
        "orders_get",
        "copy_ticks_range",
    }

    called: set[str] = set()

    for node in ast.walk(
        tree
    ):

        if not isinstance(
            node,
            ast.Call,
        ):

            continue

        if isinstance(
            node.func,
            ast.Attribute,
        ):

            called.add(
                node.func.attr
            )

        elif isinstance(
            node.func,
            ast.Name,
        ):

            called.add(
                node.func.id
            )

    assert called.isdisjoint(
        forbidden
    )