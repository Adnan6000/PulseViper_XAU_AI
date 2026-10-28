from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


RUNNER_VERSION = "R03_SESSION_GAP_RECOVERY_R3_DIAGNOSTIC_V1"

HISTORY_BARS = 7000

EXPECTED_PENDING_ID = (
    "febaf847ef5cd078cfc0e8223eb2120c81969a91645998968e9a1083caa1c1f8"
)

LEDGER_WRITES_AUTHORIZED = False
TERMINAL_DISPOSITION_AUTHORIZED = False
PERFORMANCE_EVALUATION_AUTHORIZED = False
PNL_EVALUATION_AUTHORIZED = False
LIVE_AUTHORIZED = False
EXECUTION_AUTHORIZED = False


controller: Any = importlib.import_module(
    "02_AI.Models.r03_prospective_collection_controller"
)

acquisition_module: Any = importlib.import_module(
    "02_AI.Adapters.mt5_read_only_forward_acquisition_adapter"
)

policy: Any = importlib.import_module(
    "04_Testing.production_portability.r03_session_gap_policy_r3"
)


class R03RecoveryDiagnosticError(RuntimeError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise R03RecoveryDiagnosticError(reason)


def inspect_pending() -> tuple[Any, Any, Any]:
    state = controller.inspect_state(repo_root=REPO_ROOT)

    require(
        state.pending_count == 1,
        f"EXPECTED_ONE_PENDING:{state.pending_count}",
    )

    require(
        state.next_action
        == controller.ACTION_CHECK_PENDING_MATURITY,
        f"UNEXPECTED_NEXT_ACTION:{state.next_action}",
    )

    pending_id = state.pending_logical_observation_id

    require(
        pending_id == EXPECTED_PENDING_ID,
        f"UNEXPECTED_PENDING_ID:{pending_id}",
    )

    observations = controller.read_observations(
        repo_root=REPO_ROOT
    )

    anchors = controller.read_anchors(
        repo_root=REPO_ROOT
    )

    observation = observations.get(pending_id)
    anchor = anchors.get(pending_id)

    require(
        observation is not None,
        "PENDING_OBSERVATION_MISSING",
    )

    require(
        anchor is not None,
        "PENDING_ANCHOR_MISSING",
    )

    require(
        observation.logical_observation_id
        == anchor.logical_observation_id,
        "OBSERVATION_ANCHOR_ID_MISMATCH",
    )

    require(
        observation.source_snapshot_id
        == anchor.source_snapshot_id,
        "OBSERVATION_ANCHOR_SNAPSHOT_MISMATCH",
    )

    require(
        observation.semantic_record_fingerprint
        == anchor.semantic_observation_fingerprint,
        "OBSERVATION_ANCHOR_FINGERPRINT_MISMATCH",
    )

    return state, observation, anchor


def assess_snapshot(
    *,
    state: Any,
    observation: Any,
    anchor: Any,
    snapshot: Any,
    broker_symbol: str,
) -> dict[str, Any]:

    require(
        snapshot.is_synthetic is False,
        "SYNTHETIC_SNAPSHOT_FORBIDDEN",
    )

    require(
        snapshot.canonical_instrument == "XAUUSD",
        "CANONICAL_INSTRUMENT_MISMATCH",
    )

    require(
        snapshot.broker_symbol == broker_symbol,
        "BROKER_SYMBOL_MISMATCH",
    )

    require(
        snapshot.authority is not None,
        "SNAPSHOT_AUTHORITY_MISSING",
    )

    market_data = snapshot.market_data

    require(
        isinstance(market_data, dict),
        "SNAPSHOT_MARKET_DATA_INVALID",
    )

    m5 = market_data.get("M5")

    require(
        isinstance(m5, pd.DataFrame),
        "M5_FRAME_MISSING",
    )

    require(
        "time" in m5.columns,
        "M5_TIME_COLUMN_MISSING",
    )

    decision = pd.Timestamp(
        anchor.decision_time_utc
    )

    decision_open = pd.Timestamp(
        anchor.decision_bar_open_time_utc
    )

    require(
        decision.tzinfo is not None
        and decision_open.tzinfo is not None,
        "ANCHOR_TIME_NOT_TIMEZONE_AWARE",
    )

    decision = decision.tz_convert("UTC")
    decision_open = decision_open.tz_convert("UTC")

    require(
        decision_open + pd.Timedelta(minutes=5)
        == decision,
        "ANCHOR_DECISION_TIME_MAPPING_INVALID",
    )

    times = pd.DatetimeIndex(
        pd.to_datetime(
            m5["time"],
            utc=True,
        )
    )

    require(
        int((times == decision_open).sum()) == 1,
        "DECISION_BAR_NOT_UNIQUE_IN_SNAPSHOT",
    )

    assessment = policy.assess_session_gap(
        decision_time_utc=decision,
        completed_m5_times=times,
    )

    after = controller.inspect_state(
        repo_root=REPO_ROOT
    )

    require(
        after.to_dict() == state.to_dict(),
        "LEDGER_STATE_CHANGED_DURING_DIAGNOSTIC",
    )

    return {
        "runner_version": RUNNER_VERSION,
        "status": assessment.status,
        "broker_symbol": broker_symbol,
        "pending_logical_observation_id": (
            observation.logical_observation_id
        ),
        "decision_time_utc": decision.isoformat(),
        "decision_bar_open_utc": decision_open.isoformat(),
        "m5_history_rows": len(m5),
        "assessment": assessment.to_dict(),
        "state_before": state.to_dict(),
        "state_after": after.to_dict(),
        "ledger_writes_authorized": False,
        "terminal_disposition_authorized": False,
        "performance_evaluated": False,
        "pnl_evaluated": False,
        "live_authorized": False,
        "execution_authorized": False,
    }


def run_diagnostic(
    *,
    mt5_api: Any,
) -> dict[str, Any]:

    state, observation, anchor = inspect_pending()

    initialized = False

    try:
        initialized = bool(mt5_api.initialize())

        require(
            initialized,
            "MT5_INITIALIZE_FAILED",
        )

        facade = (
            acquisition_module.MT5ReadOnlyCapabilityFacade(
                mt5_api
            )
        )

        acquisition = (
            acquisition_module.MT5ReadOnlyForwardAcquisitionAdapter(
                facade,
                is_synthetic=False,
                include_native_d1=False,
                timestamp_basis="AUTO",
                min_history_bars={
                    "M5": HISTORY_BARS,
                },
            )
        )

        broker_symbol = acquisition.resolve_broker_symbol()

        snapshot = acquisition.acquire_snapshot(
            enforce_forward_boundaries=True
        )

        return assess_snapshot(
            state=state,
            observation=observation,
            anchor=anchor,
            snapshot=snapshot,
            broker_symbol=broker_symbol,
        )

    finally:
        if initialized:
            mt5_api.shutdown()


def main() -> int:
    print("R03_RECOVERY_R3_VERSION=" + RUNNER_VERSION)

    try:
        mt5_api = importlib.import_module("MetaTrader5")

        result = run_diagnostic(
            mt5_api=mt5_api,
        )

    except Exception as exc:
        print("R03_RECOVERY_R3_STATUS=BLOCKED")
        print("ERROR_TYPE=" + type(exc).__name__)
        print("ERROR=" + str(exc))
        print("LEDGERS_WRITTEN=false")
        print("TERMINAL_DISPOSITION_AUTHORIZED=false")
        print("LIVE_AUTHORIZED=false")
        print("EXECUTION_AUTHORIZED=false")
        return 2

    print(
        "R03_RECOVERY_R3_STATUS="
        + str(result["status"])
    )

    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())