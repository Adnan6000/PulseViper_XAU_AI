from __future__ import annotations

import importlib
import math
from pathlib import Path
import sys
from typing import Any, cast

import pandas as pd


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


RUNNER_VERSION = (
    "R03_PENDING_MATURITY_R2_OUTAGE_RECOVERY_V1"
)

MIN_M5_HISTORY_BARS = 1000
MAX_M5_HISTORY_BARS = 5000
RECOVERY_BUFFER_BARS = 48
M5_MINUTES = 5

PERFORMANCE_EVALUATION_AUTHORIZED = False
PNL_EVALUATION_AUTHORIZED = False
LIVE_AUTHORIZED = False
EXECUTION_AUTHORIZED = False


_controller: Any = importlib.import_module(
    "02_AI.Models."
    "r03_prospective_collection_controller"
)

_acquisition: Any = importlib.import_module(
    "02_AI.Adapters."
    "mt5_read_only_forward_acquisition_adapter"
)

_r1: Any = importlib.import_module(
    "04_Testing.production_portability."
    "run_xauusd_gate_15d_c_b2d_g7_h_e_c_r1_r03_pending_maturity"
)

mt5: Any = importlib.import_module(
    "MetaTrader5"
)


class R03OutageRecoveryError(RuntimeError):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise R03OutageRecoveryError(
            reason
        )


def utc_timestamp(
    value: Any,
) -> pd.Timestamp:

    try:
        parsed = pd.Timestamp(
            value
        )
    except Exception as exc:
        raise R03OutageRecoveryError(
            "INVALID_TIMESTAMP"
        ) from exc

    require(
        parsed is not pd.NaT,
        "INVALID_TIMESTAMP_NAT",
    )

    timestamp = parsed

    require(
        timestamp.tzinfo is not None,
        "TIMESTAMP_MUST_BE_TIMEZONE_AWARE",
    )

    converted = timestamp.tz_convert(
        "UTC"
    )

    require(
        converted is not pd.NaT,
        "TIMESTAMP_UTC_CONVERSION_FAILED",
    )

    return cast(
        pd.Timestamp,
        converted,
    )


def required_m5_history_bars(
    *,
    pending_decision_time_utc: Any,
    now_utc: Any,
) -> int:
    """
    Size the completed-M5 recovery window conservatively.

    Wall-clock age deliberately overestimates required bars across
    weekends/market closures. That is safe: a larger read-only window
    cannot create future leakage because position 0 remains forbidden.
    """

    decision_time = utc_timestamp(
        pending_decision_time_utc
    )

    now = utc_timestamp(
        now_utc
    )

    require(
        now >= decision_time,
        "CURRENT_TIME_PRECEDES_PENDING_DECISION",
    )

    decision_bar_open = (
        decision_time
        -
        pd.Timedelta(
            minutes=M5_MINUTES
        )
    )

    elapsed_minutes = (
        now
        -
        decision_bar_open
    ).total_seconds() / 60.0

    elapsed_bars = int(
        math.ceil(
            elapsed_minutes
            /
            M5_MINUTES
        )
    )

    requested = max(
        MIN_M5_HISTORY_BARS,
        elapsed_bars
        +
        RECOVERY_BUFFER_BARS,
    )

    require(
        requested
        <=
        MAX_M5_HISTORY_BARS,
        (
            "PENDING_SAMPLE_TOO_OLD_FOR_RECOVERY_WINDOW:"
            f"required={requested}:"
            f"max={MAX_M5_HISTORY_BARS}"
        ),
    )

    return requested


def run_recovery() -> dict[str, Any]:

    # Reuse immutable H-E-C-R1 repository/freeze authority.
    repository = (
        _r1.verify_repository()
    )

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

    pending_id = (
        before.pending_logical_observation_id
    )

    require(
        pending_id is not None,
        "PENDING_ID_MISSING",
    )

    observations = (
        _controller.read_observations(
            repo_root=REPO_ROOT
        )
    )

    observation = observations.get(
        pending_id
    )

    require(
        observation is not None,
        "PENDING_OBSERVATION_RECORD_MISSING",
    )

    pending_decision_time = str(
        observation.decision_time_utc
    )

    now_utc = pd.Timestamp.now(
        tz="UTC"
    )

    m5_history_bars = (
        required_m5_history_bars(
            pending_decision_time_utc=(
                pending_decision_time
            ),
            now_utc=now_utc,
        )
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
                min_history_bars={
                    "M5": (
                        m5_history_bars
                    ),
                },
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
            "RECOVERY_SNAPSHOT_NOT_GENUINE",
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
            "BROKER_SYMBOL_CHANGED",
        )

        m5 = snapshot.market_data.get(
            "M5"
        )

        require(
            isinstance(
                m5,
                pd.DataFrame,
            ),
            "RECOVERY_M5_FRAME_MISSING",
        )

        decision_open = (
            utc_timestamp(
                pending_decision_time
            )
            -
            pd.Timedelta(
                minutes=5
            )
        )

        matching_bars = int(
            (
                pd.to_datetime(
                    m5["time"],
                    utc=True,
                )
                ==
                decision_open
            ).sum()
        )

        require(
            matching_bars == 1,
            (
                "RECOVERY_DECISION_BAR_NOT_UNIQUE:"
                f"{matching_bars}"
            ),
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

        after = (
            _controller.inspect_state(
                repo_root=REPO_ROOT
            )
        )

        if (
            action
            ==
            "WAIT_FOR_MORE_COMPLETED_M5_BARS"
        ):

            require(
                after.pending_count == 1,
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
                "pending_logical_observation_id": (
                    pending_id
                ),
                "pending_decision_time_utc": (
                    pending_decision_time
                ),
                "requested_m5_history_bars": (
                    m5_history_bars
                ),
                "reason": result.get(
                    "reason"
                ),
                "state_before": (
                    before.to_dict()
                ),
                "state_after": (
                    after.to_dict()
                ),
            }

        require(
            action
            ==
            "MATURED_PENDING_OUTCOME",
            (
                "UNEXPECTED_RECOVERY_ACTION:"
                f"{action}"
            ),
        )

        require(
            after.pending_count == 0,
            "RECOVERY_PENDING_NOT_ZERO",
        )

        require(
            after.matured_outcome_count
            ==
            before.matured_outcome_count
            +
            1,
            "RECOVERY_OUTCOME_COUNT_NOT_INCREMENTED",
        )

        return {
            "status": "MATURED",
            "repository": repository,
            "broker_symbol": broker_symbol,
            "pending_logical_observation_id": (
                pending_id
            ),
            "pending_decision_time_utc": (
                pending_decision_time
            ),
            "requested_m5_history_bars": (
                m5_history_bars
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
            "state_before": (
                before.to_dict()
            ),
            "state_after": (
                after.to_dict()
            ),
        }

    finally:

        if initialized:

            try:
                mt5.shutdown()
            except Exception:
                pass


def main() -> int:

    print(
        "R03_PENDING_MATURITY_R2_VERSION="
        +
        RUNNER_VERSION
    )

    try:

        result = run_recovery()

    except Exception as exc:

        print(
            "R03_PENDING_MATURITY_R2_STATUS=BLOCKED"
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
            "LEDGERS_WRITTEN=false"
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

    print(
        "R03_PENDING_MATURITY_R2_STATUS="
        +
        str(
            result["status"]
        )
    )

    print(
        "BROKER_SYMBOL="
        +
        str(
            result["broker_symbol"]
        )
    )

    print(
        "LOGICAL_OBSERVATION_ID="
        +
        str(
            result[
                "pending_logical_observation_id"
            ]
        )
    )

    print(
        "PENDING_DECISION_TIME_UTC="
        +
        str(
            result[
                "pending_decision_time_utc"
            ]
        )
    )

    print(
        "REQUESTED_M5_HISTORY_BARS="
        +
        str(
            result[
                "requested_m5_history_bars"
            ]
        )
    )

    if result["status"] == "WAIT":

        print(
            "REASON="
            +
            str(
                result["reason"]
            )
        )

        print(
            "OUTCOME_APPENDED=false"
        )

    else:

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