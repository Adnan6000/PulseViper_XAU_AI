from __future__ import annotations

import importlib
from pathlib import Path
import subprocess
import sys
from typing import Any

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(REPO_ROOT),
    )


GATE_ID = (
    "GATE_15D_C_B2D_G3_FORWARD_SAMPLE_CONTROLLER"
)

SCHEMA_VERSION = "1.0.0"

BASE_AUTHORITY_COMMIT = (
    "6ba4d5725656a3173fe5fa19c2e555dcbd94325c"
)

CANONICAL_INSTRUMENT = "XAUUSD"

REQUIRED_FUTURE_M5_BARS = 12

PERFORMANCE_EVALUATION_AUTHORIZED = False
PNL_EVALUATION_AUTHORIZED = False
LIVE_AUTHORIZED = False
EXECUTION_AUTHORIZED = False

RAW_MT5_CALLS = (
    "initialize",
    "shutdown",
)


OBSERVATION_LEDGER_PATH = (
    REPO_ROOT
    / "01_Data/Shadow/"
      "xauusd_frozen_c04_shadow_observations.jsonl"
)

ANCHOR_LEDGER_PATH = (
    REPO_ROOT
    / "01_Data/Shadow/"
      "xauusd_frozen_c04_forward_outcome_anchors.jsonl"
)

OUTCOME_LEDGER_PATH = (
    REPO_ROOT
    / "01_Data/Shadow/"
      "xauusd_frozen_c04_forward_outcomes.jsonl"
)


_observer: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_shadow_observer"
)

_anchor: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_anchor"
)

_outcome: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_ledger"
)

_maturer: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_maturer"
)

_acq: Any = importlib.import_module(
    "02_AI.Adapters.mt5_read_only_forward_acquisition_adapter"
)

mt5: Any = importlib.import_module(
    "MetaTrader5"
)


ObservationLedger: Any = (
    _observer.FrozenC04ObservationLedger
)

AnchorLedger: Any = (
    _anchor.FrozenC04ForwardOutcomeAnchorLedger
)

OutcomeLedger: Any = (
    _outcome.FrozenC04ForwardOutcomeLedger
)

MT5ReadOnlyCapabilityFacade: Any = (
    _acq.MT5ReadOnlyCapabilityFacade
)

MT5ReadOnlyForwardAcquisitionAdapter: Any = (
    _acq.MT5ReadOnlyForwardAcquisitionAdapter
)


class G3ControllerError(
    RuntimeError
):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise G3ControllerError(
            reason
        )


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
            + " ".join(args)
            + ":"
            + process.stderr.strip()
        ),
    )

    return process.stdout.rstrip(
        "\r\n"
    )


def verify_repository_authority() -> dict[str, Any]:

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

    origin_main = git_output(
        "rev-parse",
        "origin/main",
    )

    require(
        branch == "main",
        (
            "UNEXPECTED_BRANCH:"
            + branch
        ),
    )

    require(
        head == origin_main,
        (
            "HEAD_ORIGIN_MAIN_DIVERGENCE:"
            + head
            + "!="
            + origin_main
        ),
    )

    ancestor = git_process(
        "merge-base",
        "--is-ancestor",
        BASE_AUTHORITY_COMMIT,
        head,
    )

    require(
        ancestor.returncode == 0,
        "BASE_AUTHORITY_NOT_ANCESTOR",
    )

    status = git_output(
        "status",
        "--porcelain",
        "--untracked-files=all",
    )

    require(
        status.strip() == "",
        (
            "WORKTREE_NOT_CLEAN:"
            + status.replace(
                "\n",
                "|",
            )
        ),
    )

    return {
        "branch": branch,
        "head": head,
        "origin_main": origin_main,
        "clean_worktree": True,
    }


def verify_runtime_authorities() -> None:

    require(
        bool(
            _anchor.verify_authorities()
        ),
        "ANCHOR_AUTHORITY_INVALID",
    )

    require(
        bool(
            _maturer.verify_authorities()
        ),
        "MATURER_AUTHORITY_INVALID",
    )

    require(
        bool(
            _outcome.verify_authorities()
        ),
        "OUTCOME_LEDGER_AUTHORITY_INVALID",
    )

    require(
        _maturer.MATURATION_VERSION
        ==
        "FROZEN_C04_FORWARD_OUTCOME_MATURER_V2",
        "MATURATION_VERSION_MISMATCH",
    )

    require(
        _outcome.OUTCOME_LEDGER_VERSION
        ==
        "FROZEN_C04_FORWARD_OUTCOME_LEDGER_V2",
        "OUTCOME_LEDGER_VERSION_MISMATCH",
    )

    require(
        _maturer.EXPECTED_HORIZON_BARS
        ==
        REQUIRED_FUTURE_M5_BARS,
        "HORIZON_AUTHORITY_MISMATCH",
    )

    require(
        PERFORMANCE_EVALUATION_AUTHORIZED
        is False,
        "PERFORMANCE_AUTHORIZATION_VIOLATION",
    )

    require(
        PNL_EVALUATION_AUTHORIZED
        is False,
        "PNL_AUTHORIZATION_VIOLATION",
    )

    require(
        LIVE_AUTHORIZED
        is False,
        "LIVE_AUTHORIZATION_VIOLATION",
    )

    require(
        EXECUTION_AUTHORIZED
        is False,
        "EXECUTION_AUTHORIZATION_VIOLATION",
    )


def load_runtime_state() -> dict[str, Any]:

    observations = ObservationLedger(
        OBSERVATION_LEDGER_PATH
    )

    anchors = AnchorLedger(
        ANCHOR_LEDGER_PATH
    )

    outcomes = OutcomeLedger(
        OUTCOME_LEDGER_PATH
    )

    require(
        observations.validate_integrity(),
        "OBSERVATION_LEDGER_INTEGRITY_FAILED",
    )

    require(
        anchors.validate_integrity(),
        "ANCHOR_LEDGER_INTEGRITY_FAILED",
    )

    require(
        outcomes.validate_integrity(),
        "OUTCOME_LEDGER_INTEGRITY_FAILED",
    )

    observation_records = (
        observations.read_all()
    )

    anchor_records = (
        anchors.read_all()
    )

    outcome_records = (
        outcomes.read_all()
    )

    observation_by_id = {
        record.logical_observation_id: record
        for record in observation_records
    }

    anchor_by_id = {
        record.logical_observation_id: record
        for record in anchor_records
    }

    outcome_by_id = {
        record.logical_observation_id: record
        for record in outcome_records
    }

    anchored_ids = (
        set(observation_by_id)
        &
        set(anchor_by_id)
    )

    matured_ids = (
        anchored_ids
        &
        set(outcome_by_id)
    )

    pending_ids = (
        anchored_ids
        -
        set(outcome_by_id)
    )

    eligible_pending: list[
        tuple[Any, Any]
    ] = []

    for logical_id in pending_ids:

        observation = (
            observation_by_id[
                logical_id
            ]
        )

        anchor = (
            anchor_by_id[
                logical_id
            ]
        )

        if not bool(
            observation.is_true_forward_eligible
        ):
            continue

        eligible_pending.append(
            (
                observation,
                anchor,
            )
        )

    eligible_pending.sort(
        key=lambda pair: (
            pair[1].decision_time_utc
        )
    )

    unanchored_observation_count = len(
        set(observation_by_id)
        -
        set(anchor_by_id)
    )

    return {
        "observation_count": len(
            observation_records
        ),
        "anchor_count": len(
            anchor_records
        ),
        "outcome_count": len(
            outcome_records
        ),
        "anchored_count": len(
            anchored_ids
        ),
        "matured_count": len(
            matured_ids
        ),
        "pending_count": len(
            eligible_pending
        ),
        "unanchored_observation_count": (
            unanchored_observation_count
        ),
        "pending": eligible_pending,
    }


def evaluate_oldest_pending(
    pending: list[
        tuple[Any, Any]
    ],
) -> dict[str, Any]:

    require(
        bool(pending),
        "NO_PENDING_SAMPLE",
    )

    observation, anchor = (
        pending[0]
    )

    initialized = bool(
        mt5.initialize()
    )

    require(
        initialized,
        "MT5_INITIALIZE_FAILED",
    )

    try:

        facade = (
            MT5ReadOnlyCapabilityFacade(
                mt5
            )
        )

        acquisition = (
            MT5ReadOnlyForwardAcquisitionAdapter(
                facade,
                is_synthetic=False,
                include_native_d1=False,
                timestamp_basis="AUTO",
            )
        )

        broker_symbol = (
            acquisition.resolve_broker_symbol()
        )

        require(
            broker_symbol
            ==
            observation.broker_symbol,
            (
                "BROKER_SYMBOL_MISMATCH:"
                + str(broker_symbol)
                + "!="
                + str(
                    observation.broker_symbol
                )
            ),
        )

        snapshot = (
            acquisition.acquire_snapshot(
                enforce_forward_boundaries=True
            )
        )

        require(
            snapshot.is_synthetic
            is False,
            "SNAPSHOT_MUST_BE_GENUINE",
        )

        require(
            snapshot.canonical_instrument
            ==
            CANONICAL_INSTRUMENT,
            "CANONICAL_INSTRUMENT_MISMATCH",
        )

        m5 = (
            snapshot.market_data[
                "M5"
            ].copy()
        )

        decision_open = pd.Timestamp(
            anchor.decision_bar_open_time_utc
        )

        positions = (
            m5.index[
                m5["time"]
                ==
                decision_open
            ]
            .tolist()
        )

        require(
            len(positions) == 1,
            (
                "DECISION_BAR_MATCH_COUNT:"
                + str(
                    len(positions)
                )
            ),
        )

        decision_pos = int(
            positions[0]
        )

        available = max(
            0,
            len(m5)
            -
            decision_pos
            -
            1,
        )

        ready = (
            available
            >=
            REQUIRED_FUTURE_M5_BARS
        )

        return {
            "logical_observation_id": (
                observation.logical_observation_id
            ),
            "decision_time_utc": (
                observation.decision_time_utc
            ),
            "broker_symbol": (
                observation.broker_symbol
            ),
            "available_future_m5_bars": (
                available
            ),
            "required_future_m5_bars": (
                REQUIRED_FUTURE_M5_BARS
            ),
            "missing_future_m5_bars": max(
                0,
                REQUIRED_FUTURE_M5_BARS
                -
                available,
            ),
            "ready": ready,
            "next_action": (
                "RUN_G2_APPEND"
                if ready
                else
                "WAIT_FOR_MATURATION"
            ),
        }

    finally:

        mt5.shutdown()


def run_controller() -> dict[str, Any]:

    repository = (
        verify_repository_authority()
    )

    verify_runtime_authorities()

    state = (
        load_runtime_state()
    )

    pending = state[
        "pending"
    ]

    if not pending:

        return {
            "status": "PASS",
            "repository": repository,
            "observation_count": (
                state[
                    "observation_count"
                ]
            ),
            "anchor_count": (
                state[
                    "anchor_count"
                ]
            ),
            "outcome_count": (
                state[
                    "outcome_count"
                ]
            ),
            "matured_count": (
                state[
                    "matured_count"
                ]
            ),
            "pending_count": 0,
            "unanchored_observation_count": (
                state[
                    "unanchored_observation_count"
                ]
            ),
            "next_action": (
                "RUN_G1_CAPTURE"
            ),
            "mt5_initialized": False,
            "market_data_acquired": False,
            "performance_evaluated": False,
            "pnl_evaluated": False,
            "live_authorized": False,
            "execution_authorized": False,
        }

    readiness = (
        evaluate_oldest_pending(
            pending
        )
    )

    return {
        "status": "PASS",
        "repository": repository,
        "observation_count": (
            state[
                "observation_count"
            ]
        ),
        "anchor_count": (
            state[
                "anchor_count"
            ]
        ),
        "outcome_count": (
            state[
                "outcome_count"
            ]
        ),
        "matured_count": (
            state[
                "matured_count"
            ]
        ),
        "pending_count": (
            state[
                "pending_count"
            ]
        ),
        "unanchored_observation_count": (
            state[
                "unanchored_observation_count"
            ]
        ),
        **readiness,
        "mt5_initialized": True,
        "market_data_acquired": True,
        "performance_evaluated": False,
        "pnl_evaluated": False,
        "live_authorized": False,
        "execution_authorized": False,
    }


def main() -> int:

    try:

        result = (
            run_controller()
        )

    except Exception as exc:

        print(
            "GATE_15D_C_B2D_G3_STATUS=BLOCKED"
        )

        print(
            "ERROR_TYPE="
            + type(exc).__name__
        )

        print(
            "ERROR="
            + str(exc)
        )

        print(
            "PERFORMANCE_EVALUATED=false"
        )

        print(
            "LIVE_AUTHORIZED=false"
        )

        print(
            "EXECUTION_AUTHORIZED=false"
        )

        return 2

    print(
        "GATE_15D_C_B2D_G3_STATUS=PASS"
    )

    print(
        "OBSERVATION_COUNT="
        + str(
            result[
                "observation_count"
            ]
        )
    )

    print(
        "ANCHOR_COUNT="
        + str(
            result[
                "anchor_count"
            ]
        )
    )

    print(
        "OUTCOME_COUNT="
        + str(
            result[
                "outcome_count"
            ]
        )
    )

    print(
        "MATURED_COUNT="
        + str(
            result[
                "matured_count"
            ]
        )
    )

    print(
        "PENDING_COUNT="
        + str(
            result[
                "pending_count"
            ]
        )
    )

    print(
        "UNANCHORED_OBSERVATION_COUNT="
        + str(
            result[
                "unanchored_observation_count"
            ]
        )
    )

    if (
        result[
            "pending_count"
        ]
        >
        0
    ):

        print(
            "TARGET_LOGICAL_OBSERVATION_ID="
            + str(
                result[
                    "logical_observation_id"
                ]
            )
        )

        print(
            "AVAILABLE_FUTURE_M5_BARS="
            + str(
                result[
                    "available_future_m5_bars"
                ]
            )
        )

        print(
            "REQUIRED_FUTURE_M5_BARS="
            + str(
                result[
                    "required_future_m5_bars"
                ]
            )
        )

        print(
            "MISSING_FUTURE_M5_BARS="
            + str(
                result[
                    "missing_future_m5_bars"
                ]
            )
        )

    print(
        "NEXT_ACTION="
        + str(
            result[
                "next_action"
            ]
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

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
