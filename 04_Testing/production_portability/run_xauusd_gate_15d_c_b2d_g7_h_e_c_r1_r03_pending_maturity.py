from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


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


GATE_ID = (
    "GATE_15D_C_B2D_G7_H_E_C_R1_"
    "R03_PENDING_MATURITY"
)

FREEZE_BASE_AUTHORITY_COMMIT = (
    "2ad29322d7032e2ba11cba984554788ae5975ab8"
)

FREEZE_EVIDENCE_REL = (
    "04_Testing/evidence/research/"
    "portable_331/remediation/"
    "xauusd_gate_15d_c_b2d_g7_h_e_c_r1_"
    "r03_pending_maturity_runner_freeze.json"
)

RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_h_e_c_r1_"
    "r03_pending_maturity.py"
)

FREEZE_RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_h_e_c_r1_"
    "r03_pending_maturity_freeze.py"
)

TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g7_h_e_c_r1_"
    "r03_pending_maturity_freeze.py"
)

FREEZE_EVIDENCE_PATH = (
    REPO_ROOT
    /
    FREEZE_EVIDENCE_REL
)


_controller: Any = importlib.import_module(
    "02_AI.Models."
    "r03_prospective_collection_controller"
)

_acquisition: Any = importlib.import_module(
    "02_AI.Adapters."
    "mt5_read_only_forward_acquisition_adapter"
)

mt5: Any = importlib.import_module(
    "MetaTrader5"
)


OBSERVATION_LEDGER_REL = str(
    _controller
    .OBSERVATION_LEDGER_RELATIVE_PATH
)

ANCHOR_LEDGER_REL = str(
    _controller
    .ANCHOR_LEDGER_RELATIVE_PATH
)

OUTCOME_LEDGER_REL = str(
    _controller
    .OUTCOME_LEDGER_RELATIVE_PATH
)


PERFORMANCE_EVALUATION_AUTHORIZED = False
PNL_EVALUATION_AUTHORIZED = False
LIVE_AUTHORIZED = False
EXECUTION_AUTHORIZED = False


class G7HECR1MaturityError(
    RuntimeError
):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise G7HECR1MaturityError(
            reason
        )


def sha256_file(
    path: Path,
) -> str:

    require(
        path.is_file(),
        f"FILE_MISSING:{path}",
    )

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as handle:

        while True:

            chunk = handle.read(
                1024 * 1024
            )

            if not chunk:
                break

            digest.update(
                chunk
            )

    return digest.hexdigest()


def git_process(
    *args: str,
) -> subprocess.CompletedProcess[str]:

    return subprocess.run(
        [
            "git",
            *args,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def git_output(
    *args: str,
) -> str:

    process = git_process(
        *args
    )

    require(
        process.returncode == 0,
        (
            "GIT_COMMAND_FAILED:"
            +
            " ".join(
                args
            )
        ),
    )

    return process.stdout.rstrip(
        "\r\n"
    )


def status_paths() -> set[str]:

    raw = git_output(
        "status",
        "--porcelain",
        "--untracked-files=all",
    )

    output: set[str] = set()

    for line in raw.splitlines():

        if len(line) < 4:
            continue

        value = (
            line[3:]
            .strip()
            .replace(
                "\\",
                "/",
            )
        )

        if " -> " in value:
            value = value.split(
                " -> ",
                1,
            )[1]

        output.add(
            value
        )

    return output


def verify_freeze_authority() -> dict[
    str,
    Any,
]:

    require(
        FREEZE_EVIDENCE_PATH.is_file(),
        "MATURITY_FREEZE_EVIDENCE_MISSING",
    )

    raw = json.loads(
        FREEZE_EVIDENCE_PATH.read_text(
            encoding="utf-8"
        )
    )

    require(
        isinstance(
            raw,
            dict,
        ),
        "MATURITY_FREEZE_EVIDENCE_INVALID",
    )

    require(
        raw.get(
            "status"
        )
        ==
        "PASS",
        "MATURITY_FREEZE_NOT_PASS",
    )

    require(
        raw.get(
            "base_authority_commit"
        )
        ==
        FREEZE_BASE_AUTHORITY_COMMIT,
        "MATURITY_FREEZE_BASE_MISMATCH",
    )

    hashes = raw.get(
        "candidate_artifact_hashes"
    )

    require(
        isinstance(
            hashes,
            dict,
        ),
        "MATURITY_FREEZE_HASHES_MISSING",
    )

    expected_paths = {
        RUNNER_REL,
        FREEZE_RUNNER_REL,
        TEST_REL,
    }

    require(
        set(
            hashes.keys()
        )
        ==
        expected_paths,
        "MATURITY_FREEZE_PATH_SET_MISMATCH",
    )

    for relative in sorted(
        expected_paths
    ):

        expected = hashes.get(
            relative
        )

        require(
            isinstance(
                expected,
                str,
            )
            and
            len(
                expected
            )
            ==
            64,
            (
                "MATURITY_ARTIFACT_HASH_INVALID:"
                f"{relative}"
            ),
        )

        require(
            sha256_file(
                REPO_ROOT
                /
                relative
            )
            ==
            expected,
            (
                "MATURITY_ARTIFACT_CHANGED:"
                f"{relative}"
            ),
        )

    return raw


def verify_repository() -> dict[
    str,
    str,
]:

    fetch = git_process(
        "fetch",
        "origin",
    )

    require(
        fetch.returncode == 0,
        "GIT_FETCH_ORIGIN_FAILED",
    )

    branch = git_output(
        "branch",
        "--show-current",
    )

    head = git_output(
        "rev-parse",
        "HEAD",
    )

    origin = git_output(
        "rev-parse",
        "origin/main",
    )

    require(
        branch == "main",
        (
            "UNEXPECTED_BRANCH:"
            f"{branch}"
        ),
    )

    require(
        head == origin,
        (
            "HEAD_ORIGIN_MAIN_DIVERGENCE:"
            f"{head}!="
            f"{origin}"
        ),
    )

    ancestor = git_process(
        "merge-base",
        "--is-ancestor",
        FREEZE_BASE_AUTHORITY_COMMIT,
        head,
    )

    require(
        ancestor.returncode == 0,
        "MATURITY_BASE_NOT_ANCESTOR",
    )

    allowed = {
        OBSERVATION_LEDGER_REL,
        ANCHOR_LEDGER_REL,
        OUTCOME_LEDGER_REL,
    }

    unexpected = (
        status_paths()
        -
        allowed
    )

    require(
        not unexpected,
        (
            "UNEXPECTED_LOCAL_PATHS:"
            f"{sorted(unexpected)}"
        ),
    )

    _ = verify_freeze_authority()

    return {
        "branch": branch,
        "head": head,
        "origin_main": origin,
    }


def run_gate() -> dict[
    str,
    Any,
]:

    repository = verify_repository()

    before = (
        _controller.inspect_state(
            repo_root=REPO_ROOT
        )
    )

    require(
        before.next_action
        ==
        _controller.ACTION_CHECK_PENDING_MATURITY,
        (
            "PENDING_MATURITY_NOT_AUTHORIZED:"
            f"{before.next_action}"
        ),
    )

    require(
        before.pending_count == 1,
        (
            "PENDING_COUNT_NOT_ONE:"
            f"{before.pending_count}"
        ),
    )

    require(
        before.pending_logical_observation_id
        is not None,
        "PENDING_LOGICAL_OBSERVATION_ID_MISSING",
    )

    initialized = False

    try:

        initialized = bool(
            mt5.initialize()
        )

        require(
            initialized,
            "MT5_INITIALIZE_FAILED",
        )

        read_only_api = (
            _acquisition
            .MT5ReadOnlyCapabilityFacade(
                mt5
            )
        )

        acquisition = (
            _acquisition
            .MT5ReadOnlyForwardAcquisitionAdapter(
                read_only_api,
                is_synthetic=False,
                include_native_d1=False,
                timestamp_basis="AUTO",
            )
        )

        broker_symbol = (
            acquisition
            .resolve_broker_symbol()
        )

        snapshot = (
            acquisition
            .acquire_snapshot(
                enforce_forward_boundaries=True
            )
        )

        require(
            snapshot.is_synthetic
            is False,
            "MATURITY_SNAPSHOT_NOT_GENUINE",
        )

        require(
            snapshot.canonical_instrument
            ==
            "XAUUSD",
            "CANONICAL_INSTRUMENT_MISMATCH",
        )

        require(
            snapshot.broker_symbol
            ==
            broker_symbol,
            "BROKER_SYMBOL_CHANGED_DURING_MATURITY",
        )

        require(
            snapshot.authority
            is not None,
            "MATURITY_SNAPSHOT_AUTHORITY_MISSING",
        )

        result = (
            _controller
            .mature_pending_from_snapshot(
                snapshot=snapshot,
                repo_root=REPO_ROOT,
            )
        )

        action = str(
            result.get(
                "action"
            )
        )

        if (
            action
            ==
            "WAIT_FOR_MORE_COMPLETED_M5_BARS"
        ):

            after = (
                _controller.inspect_state(
                    repo_root=REPO_ROOT
                )
            )

            require(
                after.pending_count
                ==
                1,
                "WAIT_CHANGED_PENDING_COUNT",
            )

            require(
                after.matured_outcome_count
                ==
                before.matured_outcome_count,
                "WAIT_CHANGED_OUTCOME_COUNT",
            )

            return {
                "status": "WAIT",
                "repository": repository,
                "broker_symbol": broker_symbol,
                "logical_observation_id": (
                    result.get(
                        "logical_observation_id"
                    )
                ),
                "reason": (
                    result.get(
                        "reason"
                    )
                ),
                "state_before": (
                    before.to_dict()
                ),
                "state_after": (
                    after.to_dict()
                ),
                "performance_evaluated": False,
                "pnl_evaluated": False,
                "live_authorized": False,
                "execution_authorized": False,
            }

        require(
            action
            ==
            "MATURED_PENDING_OUTCOME",
            (
                "UNEXPECTED_MATURITY_ACTION:"
                f"{action}"
            ),
        )

        after = (
            _controller.inspect_state(
                repo_root=REPO_ROOT
            )
        )

        require(
            after.pending_count
            ==
            0,
            "MATURATION_PENDING_COUNT_NOT_ZERO",
        )

        require(
            after.matured_outcome_count
            ==
            (
                before.matured_outcome_count
                +
                1
            ),
            "MATURATION_OUTCOME_COUNT_NOT_INCREMENTED",
        )

        return {
            "status": "MATURED",
            "repository": repository,
            "broker_symbol": broker_symbol,
            "logical_observation_id": (
                result.get(
                    "logical_observation_id"
                )
            ),
            "outcome_class": (
                result.get(
                    "outcome_class"
                )
            ),
            "outcome_label": (
                result.get(
                    "outcome_label"
                )
            ),
            "up_excursion_atr": (
                result.get(
                    "up_excursion_atr"
                )
            ),
            "down_excursion_atr": (
                result.get(
                    "down_excursion_atr"
                )
            ),
            "outcome_appended": (
                result.get(
                    "outcome_appended"
                )
            ),
            "outcome_idempotent_duplicate": (
                result.get(
                    "outcome_idempotent_duplicate"
                )
            ),
            "state_before": (
                before.to_dict()
            ),
            "state_after": (
                after.to_dict()
            ),
            "performance_evaluated": False,
            "pnl_evaluated": False,
            "live_authorized": False,
            "execution_authorized": False,
        }

    finally:

        if initialized:

            try:
                mt5.shutdown()
            except Exception:
                pass


def main() -> int:

    try:

        result = run_gate()

    except Exception as exc:

        print(
            "GATE_15D_C_B2D_G7_H_E_C_R1_STATUS=BLOCKED"
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

    status = str(
        result[
            "status"
        ]
    )

    if status == "WAIT":

        print(
            "GATE_15D_C_B2D_G7_H_E_C_R1_STATUS=WAIT"
        )

        print(
            "GENUINE_MT5_ACQUISITION=true"
        )

        print(
            "LOGICAL_OBSERVATION_ID="
            +
            str(
                result[
                    "logical_observation_id"
                ]
            )
        )

        print(
            "REASON="
            +
            str(
                result[
                    "reason"
                ]
            )
        )

        print(
            "OUTCOME_APPENDED=false"
        )

        print(
            "PENDING_OUTCOMES=1"
        )

    else:

        print(
            "GATE_15D_C_B2D_G7_H_E_C_R1_STATUS=MATURED"
        )

        print(
            "GENUINE_MT5_ACQUISITION=true"
        )

        print(
            "LOGICAL_OBSERVATION_ID="
            +
            str(
                result[
                    "logical_observation_id"
                ]
            )
        )

        print(
            "OUTCOME_CLASS="
            +
            str(
                result[
                    "outcome_class"
                ]
            )
        )

        print(
            "OUTCOME_LABEL="
            +
            str(
                result[
                    "outcome_label"
                ]
            )
        )

        print(
            "UP_EXCURSION_ATR="
            +
            str(
                result[
                    "up_excursion_atr"
                ]
            )
        )

        print(
            "DOWN_EXCURSION_ATR="
            +
            str(
                result[
                    "down_excursion_atr"
                ]
            )
        )

        print(
            "OUTCOME_APPENDED="
            +
            str(
                result[
                    "outcome_appended"
                ]
            ).lower()
        )

        print(
            "PENDING_OUTCOMES=0"
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

    return 0


if __name__ == "__main__":

    raise SystemExit(
        main()
    )