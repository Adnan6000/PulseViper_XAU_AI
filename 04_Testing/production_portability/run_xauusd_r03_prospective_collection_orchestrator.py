from __future__ import annotations

import importlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, TextIO

import msvcrt


REPO_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(REPO_ROOT),
    )


ORCHESTRATOR_VERSION = (
    "R03_PROSPECTIVE_COLLECTION_ORCHESTRATOR_V1"
)

PRECHECK_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_r03_market_freshness_precheck.py"
)

CAPTURE_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_h_e_d_"
    "r03_reusable_capture.py"
)

MATURITY_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_h_e_c_r1_"
    "r03_pending_maturity.py"
)


_controller: Any = importlib.import_module(
    "02_AI.Models."
    "r03_prospective_collection_controller"
)


PERFORMANCE_EVALUATION_AUTHORIZED = False
PNL_EVALUATION_AUTHORIZED = False
LIVE_AUTHORIZED = False
EXECUTION_AUTHORIZED = False


class R03CollectionOrchestratorError(
    RuntimeError
):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise R03CollectionOrchestratorError(
            reason
        )


def python_executable() -> str:

    return sys.executable


def run_child(
    relative_path: str,
) -> subprocess.CompletedProcess[str]:

    path = (
        REPO_ROOT
        /
        relative_path
    )

    require(
        path.is_file(),
        f"CHILD_RUNNER_MISSING:{relative_path}",
    )

    process = subprocess.run(
        [
            python_executable(),
            str(path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    stdout = (
        process.stdout
        .rstrip(
            "\r\n"
        )
    )

    stderr = (
        process.stderr
        .rstrip(
            "\r\n"
        )
    )

    if stdout:
        print(
            stdout
        )

    if stderr:
        print(
            "CHILD_STDERR="
            +
            stderr.replace(
                "\n",
                " | ",
            )
        )

    return process


def market_ready() -> bool:

    process = run_child(
        PRECHECK_REL
    )

    if (
        process.returncode == 0
        and
        "R03_MARKET_PRECHECK_STATUS=READY"
        in
        process.stdout
    ):
        return True

    return False


def lock_directory() -> Path:

    local_app_data = os.environ.get(
        "LOCALAPPDATA"
    )

    if local_app_data:

        root = Path(
            local_app_data
        )

    else:

        root = Path(
            tempfile.gettempdir()
        )

    directory = (
        root
        /
        "PulseViper"
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return directory


def acquire_process_lock() -> tuple[
    TextIO,
    Path,
]:

    path = (
        lock_directory()
        /
        "r03_prospective_collection.lock"
    )

    handle = path.open(
        "a+",
        encoding="utf-8",
    )

    handle.seek(
        0
    )

    if handle.read(
        1
    ) == "":

        handle.seek(
            0
        )

        handle.write(
            "1"
        )

        handle.flush()

    handle.seek(
        0
    )

    try:

        msvcrt.locking(
            handle.fileno(),
            msvcrt.LK_NBLCK,
            1,
        )

    except OSError as exc:

        handle.close()

        raise R03CollectionOrchestratorError(
            "ORCHESTRATOR_ALREADY_RUNNING"
        ) from exc

    return (
        handle,
        path,
    )


def release_process_lock(
    handle: TextIO,
) -> None:

    try:

        handle.seek(
            0
        )

        msvcrt.locking(
            handle.fileno(),
            msvcrt.LK_UNLCK,
            1,
        )

    finally:

        handle.close()


def print_state(
    *,
    prefix: str,
    state: Any,
) -> None:

    print(
        f"{prefix}_OBSERVATIONS="
        f"{state.observation_count}"
    )

    print(
        f"{prefix}_MATURED_OUTCOMES="
        f"{state.matured_outcome_count}"
    )

    print(
        f"{prefix}_PENDING="
        f"{state.pending_count}"
    )

    print(
        f"{prefix}_DISTINCT_UTC_DATES="
        f"{state.distinct_matured_observation_utc_dates}"
    )

    print(
        f"{prefix}_NEXT_ACTION="
        f"{state.next_action}"
    )


def execute_capture() -> None:

    process = run_child(
        CAPTURE_REL
    )

    require(
        process.returncode == 0,
        (
            "CAPTURE_RUNNER_FAILED:"
            f"{process.returncode}"
        ),
    )

    require(
        "GATE_15D_C_B2D_G7_H_E_D_STATUS=CAPTURED"
        in
        process.stdout,
        "CAPTURE_SUCCESS_SIGNATURE_MISSING",
    )

    after = (
        _controller.inspect_state(
            repo_root=REPO_ROOT
        )
    )

    require(
        after.pending_count == 1,
        (
            "POST_CAPTURE_PENDING_NOT_ONE:"
            f"{after.pending_count}"
        ),
    )

    require(
        after.next_action
        ==
        _controller.ACTION_CHECK_PENDING_MATURITY,
        (
            "POST_CAPTURE_NEXT_ACTION_INVALID:"
            f"{after.next_action}"
        ),
    )


def run_cycle() -> int:

    before = (
        _controller.inspect_state(
            repo_root=REPO_ROOT
        )
    )

    print_state(
        prefix="STATE_BEFORE",
        state=before,
    )

    if (
        before.next_action
        ==
        _controller.ACTION_COLLECTION_TARGET_REACHED
    ):

        print(
            "R03_ORCHESTRATOR_STATUS=TARGET_REACHED"
        )

        print(
            "COLLECTION_AUTOMATION_ACTION=NONE"
        )

        return 0

    if (
        before.next_action
        ==
        _controller.ACTION_REVIEW_ORPHAN_ANCHOR
    ):

        raise R03CollectionOrchestratorError(
            "ORPHAN_ANCHOR_REQUIRES_MANUAL_REVIEW"
        )

    if not market_ready():

        print(
            "R03_ORCHESTRATOR_STATUS=MARKET_NOT_READY"
        )

        print(
            "COLLECTION_AUTOMATION_ACTION=NONE"
        )

        return 0

    if (
        before.next_action
        ==
        _controller.ACTION_CAPTURE_NEW_OBSERVATION
    ):

        execute_capture()

        after = (
            _controller.inspect_state(
                repo_root=REPO_ROOT
            )
        )

        print(
            "R03_ORCHESTRATOR_STATUS=CAPTURED"
        )

        print_state(
            prefix="STATE_AFTER",
            state=after,
        )

        return 0

    require(
        before.next_action
        ==
        _controller.ACTION_CHECK_PENDING_MATURITY,
        (
            "UNSUPPORTED_CONTROLLER_ACTION:"
            f"{before.next_action}"
        ),
    )

    maturity = run_child(
        MATURITY_REL
    )

    require(
        maturity.returncode == 0,
        (
            "MATURITY_RUNNER_FAILED:"
            f"{maturity.returncode}"
        ),
    )

    if (
        "GATE_15D_C_B2D_G7_H_E_C_R1_STATUS=WAIT"
        in
        maturity.stdout
    ):

        after_wait = (
            _controller.inspect_state(
                repo_root=REPO_ROOT
            )
        )

        require(
            after_wait.pending_count == 1,
            "WAIT_STATE_LOST_PENDING_OBSERVATION",
        )

        print(
            "R03_ORCHESTRATOR_STATUS=WAIT"
        )

        print_state(
            prefix="STATE_AFTER",
            state=after_wait,
        )

        return 0

    require(
        "GATE_15D_C_B2D_G7_H_E_C_R1_STATUS=MATURED"
        in
        maturity.stdout,
        "MATURITY_SUCCESS_SIGNATURE_MISSING",
    )

    after_maturity = (
        _controller.inspect_state(
            repo_root=REPO_ROOT
        )
    )

    require(
        after_maturity.pending_count == 0,
        (
            "POST_MATURITY_PENDING_NOT_ZERO:"
            f"{after_maturity.pending_count}"
        ),
    )

    if (
        after_maturity.next_action
        ==
        _controller.ACTION_COLLECTION_TARGET_REACHED
    ):

        print(
            "R03_ORCHESTRATOR_STATUS=MATURED_TARGET_REACHED"
        )

        print_state(
            prefix="STATE_AFTER",
            state=after_maturity,
        )

        return 0

    require(
        after_maturity.next_action
        ==
        _controller.ACTION_CAPTURE_NEW_OBSERVATION,
        (
            "POST_MATURITY_CAPTURE_NOT_AUTHORIZED:"
            f"{after_maturity.next_action}"
        ),
    )

    # Re-check freshness before immediately starting
    # the next non-overlapping prospective sample.
    if not market_ready():

        print(
            "R03_ORCHESTRATOR_STATUS=MATURED_MARKET_NOT_READY_FOR_NEXT_CAPTURE"
        )

        print_state(
            prefix="STATE_AFTER",
            state=after_maturity,
        )

        return 0

    execute_capture()

    final_state = (
        _controller.inspect_state(
            repo_root=REPO_ROOT
        )
    )

    print(
        "R03_ORCHESTRATOR_STATUS=MATURED_AND_CAPTURED_NEXT"
    )

    print_state(
        prefix="STATE_AFTER",
        state=final_state,
    )

    return 0


def main() -> int:

    lock_handle: TextIO | None = None

    try:

        (
            lock_handle,
            lock_path,
        ) = acquire_process_lock()

        print(
            "R03_ORCHESTRATOR_VERSION="
            +
            ORCHESTRATOR_VERSION
        )

        print(
            "PROCESS_LOCK="
            +
            str(
                lock_path
            )
        )

        return run_cycle()

    except R03CollectionOrchestratorError as exc:

        if (
            str(
                exc
            )
            ==
            "ORCHESTRATOR_ALREADY_RUNNING"
        ):

            print(
                "R03_ORCHESTRATOR_STATUS=SKIPPED_ALREADY_RUNNING"
            )

            return 0

        print(
            "R03_ORCHESTRATOR_STATUS=BLOCKED"
        )

        print(
            "ERROR="
            +
            str(
                exc
            )
        )

        print(
            "PERFORMANCE_EVALUATED=false"
        )

        print(
            "PNL_EVALUATED=false"
        )

        print(
            "LIVE_AUTHORIZED=false"
        )

        print(
            "EXECUTION_AUTHORIZED=false"
        )

        return 2

    except Exception as exc:

        print(
            "R03_ORCHESTRATOR_STATUS=BLOCKED"
        )

        print(
            "ERROR_TYPE="
            +
            type(
                exc
            ).__name__
        )

        print(
            "ERROR="
            +
            str(
                exc
            )
        )

        print(
            "PERFORMANCE_EVALUATED=false"
        )

        print(
            "PNL_EVALUATED=false"
        )

        print(
            "LIVE_AUTHORIZED=false"
        )

        print(
            "EXECUTION_AUTHORIZED=false"
        )

        return 2

    finally:

        if lock_handle is not None:

            release_process_lock(
                lock_handle
            )


if __name__ == "__main__":

    raise SystemExit(
        main()
    )