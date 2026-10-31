
from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
from typing import Any, Callable, Mapping


VERSION = "R03_V2_MT5_ORCHESTRATOR_V3"

ROOT = Path(__file__).resolve().parents[2]

LANE: Any = importlib.import_module(
    "04_Testing.production_portability.r03_v2_collection_lane"
)

GAP: Any = importlib.import_module(
    "04_Testing.production_portability.r03_v2_session_gap_terminal"
)

ACQUISITION: Any = importlib.import_module(
    "02_AI.Adapters.mt5_read_only_forward_acquisition_adapter"
)

PIPELINE: Any = importlib.import_module(
    "02_AI.Features.portable_feature_pipeline"
)

LEGACY: Any = importlib.import_module(
    "04_Testing.production_portability."
    "run_xauusd_gate_15d_c_b2d_g1_"
    "genuine_anchored_forward_capture"
)

RUNTIME: Any = importlib.import_module(
    "02_AI.Models.frozen_r03_prospective_runtime"
)

MATURER: Any = importlib.import_module(
    "02_AI.Models.frozen_r03_prospective_outcome_maturer"
)

STRICT_GAP_ERRORS = frozenset({
    "FIRST_FUTURE_M5_BAR_NOT_CONTIGUOUS",
    "LAST_FUTURE_M5_BAR_NOT_CONTIGUOUS",
    "FUTURE_M5_HORIZON_HAS_GAP",
})

SUCCESSFUL_EVIDENCE_ACTIONS = frozenset({
    "TERMINAL_EVIDENCE_RECORDED",
    "TERMINAL_EVIDENCE_ALREADY_PRESENT",
})

UNCONFIRMED_EVIDENCE_ACTIONS = frozenset({
    "WAIT_HORIZON_NOT_ELAPSED",
    "STRICT_M5_HORIZON_COMPLETE",
    "INSUFFICIENT_HISTORICAL_COVERAGE",
})

EXPECTED_COLLECTION_ACTIONS = frozenset({
    "CAPTURED_RESEARCH_ONLY",
    "MATURED_RESEARCH_ONLY",
    "WAIT",
    "SESSION_GAP_EVIDENCE_RECORDED",
    "SESSION_GAP_EVIDENCE_ALREADY_PRESENT",
})


class OrchestratorError(RuntimeError):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:
    if not condition:
        raise OrchestratorError(reason)


def blocked_result(
    action: str,
    state: Any,
) -> dict[str, Any]:
    return {
        "action": action,
        "state": state.to_dict(),
        "live_authorized": False,
        "execution_authorized": False,
    }


def acquire_genuine_snapshot() -> Any:
    """
    Read genuine XAUUSD broker data only.

    Does not call broker order-placement APIs.
    MT5 connection is closed before returning.
    """
    mt5: Any = importlib.import_module(
        "MetaTrader5"
    )

    initialized = False

    try:
        initialized = bool(mt5.initialize())

        require(
            initialized,
            "MT5_INITIALIZATION_FAILED",
        )

        facade = (
            ACQUISITION.MT5ReadOnlyCapabilityFacade(
                mt5
            )
        )

        adapter = (
            ACQUISITION.MT5ReadOnlyForwardAcquisitionAdapter(
                facade,
                is_synthetic=False,
                include_native_d1=False,
                timestamp_basis="AUTO",
            )
        )

        broker_symbol = adapter.resolve_broker_symbol()

        require(
            bool(str(broker_symbol).strip()),
            "BROKER_SYMBOL_MISSING",
        )

        LEGACY.verify_bid_ask(
            facade,
            broker_symbol,
        )

        snapshot = adapter.acquire_snapshot(
            enforce_forward_boundaries=True
        )

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
            "BROKER_SYMBOL_CHANGED",
        )

        require(
            snapshot.authority is not None,
            "SNAPSHOT_AUTHORITY_MISSING",
        )

        return snapshot

    finally:
        if initialized:
            mt5.shutdown()


def build_features(snapshot: Any) -> Any:
    normalized, _, _ = (
        LEGACY.normalize_market_timestamp_resolution(
            snapshot.market_data
        )
    )

    normalized_id = (
        ACQUISITION.compute_canonical_snapshot_id(
            normalized
        )
    )

    require(
        normalized_id == snapshot.source_snapshot_id,
        "NORMALIZATION_CHANGED_SNAPSHOT_ID",
    )

    result = (
        PIPELINE.PortableFeaturePipeline().generate(
            normalized,
            symbol=snapshot.canonical_instrument,
        )
    )

    require(
        result.feature_count == RUNTIME.FEATURE_COUNT,
        "FEATURE_COUNT_MISMATCH",
    )

    require(
        result.feature_columns_sha256
        == RUNTIME.FEATURE_COLUMNS_SHA256,
        "FEATURE_COLUMN_HASH_MISMATCH",
    )

    require(
        result.row_count > 0,
        "EMPTY_FEATURE_RESULT",
    )

    return result


def verify_snapshot_authority(
    snapshot: Any,
) -> None:
    binder = RUNTIME.R03ProspectiveRuntimeBinder(
        inference_adapter=(
            RUNTIME.R03FrozenArtifactInferenceAdapter(
                repo_root=ROOT
            )
        )
    )

    binder.verify_genuine_snapshot_authority(
        snapshot
    )


def is_strict_gap_error(
    exc: BaseException,
) -> bool:
    """
    Only exact frozen continuity errors
    may reach the terminal evidence recorder.
    """

    if not isinstance(
        exc,
        MATURER.R03OutcomeMaturationError,
    ):
        return False

    return str(exc) in STRICT_GAP_ERRORS


def process_maturity(
    *,
    snapshot: Any,
) -> dict[str, Any]:
    """
    Try the frozen maturer first.

    If it detects a strict M5 discontinuity,
    obtain separate broker-history corroboration.

    Truncated history is NOT gap evidence.
    """

    try:
        result = LANE.mature_from_snapshot(
            snapshot=snapshot
        )

    except MATURER.R03OutcomeMaturationError as exc:
        if not is_strict_gap_error(exc):
            raise

        evidence_result = GAP.record_pending_gap(
            snapshot=snapshot
        )

        require(
            isinstance(evidence_result, Mapping),
            "GAP_RESULT_INVALID",
        )

        evidence_action = str(
            evidence_result.get("action", "")
        )

        require(
            evidence_action in (
                SUCCESSFUL_EVIDENCE_ACTIONS
                | UNCONFIRMED_EVIDENCE_ACTIONS
            ),
            f"UNEXPECTED_GAP_ACTION:{evidence_action}",
        )

        # A snapshot without enough historical coverage
        # cannot prove the allegedly missing bars.
        #
        # Crucially, this is NOT converted to a
        # terminal disposition or a matured outcome.
        if evidence_action == "STRICT_M5_HORIZON_COMPLETE":
            raise OrchestratorError(
                "FROZEN_MATURER_GAP_NOT_CORROBORATED:"
                + evidence_action
            ) from exc

        if evidence_action in (
            UNCONFIRMED_EVIDENCE_ACTIONS
        ):
            return {
                "action": (
                    "BLOCKED_UNCONFIRMED_M5_GAP"
                ),
                "reason": evidence_action,
                "frozen_maturer_reason": str(exc),
                "evidence_appended": False,
                "capture_slot_released": False,
                "outcome_matured": False,
                "live_authorized": False,
                "execution_authorized": False,
            }

        require(
            evidence_result.get(
                "capture_slot_released"
            ) is False,
            "UNAUTHORIZED_SLOT_RELEASE",
        )

        require(
            evidence_result.get(
                "evidence_appended"
            ) in (True, False, None),
            "INVALID_EVIDENCE_APPEND_FLAG",
        )

        return {
            "action": (
                "SESSION_GAP_EVIDENCE_RECORDED"
                if evidence_action
                == "TERMINAL_EVIDENCE_RECORDED"
                else (
                    "SESSION_GAP_EVIDENCE_ALREADY_PRESENT"
                )
            ),
            "frozen_maturer_reason": str(exc),
            "gap_evidence": dict(evidence_result),
            "capture_slot_released": False,
            "outcome_matured": False,
            "live_authorized": False,
            "execution_authorized": False,
        }

    require(
        isinstance(result, Mapping),
        "MATURATION_RESULT_INVALID",
    )

    require(
        result.get("action") in {
            "MATURED_RESEARCH_ONLY",
            "WAIT",
        },
        "UNEXPECTED_MATURATION_ACTION",
    )

    return dict(result)


def run_cycle(
    *,
    acquire: Callable[
        [], Any
    ] = acquire_genuine_snapshot,
    features: Callable[
        [Any], Any
    ] = build_features,
    verify_snapshot: Callable[
        [Any], None
    ] = verify_snapshot_authority,
) -> dict[str, Any]:
    """
    One research-only orchestrator cycle.

    Read-only state inspection happens before MT5
    acquisition. All V2 ledger writes remain
    authority-gated within the existing lane.
    """

    before = LANE.inspect()

    if before.next_action == LANE.BLOCKED:
        return blocked_result(
            "BLOCKED_PROTOCOL_AUTHORITY",
            before,
        )

    if before.next_action == LANE.ORPHAN:
        return blocked_result(
            "BLOCKED_ORPHAN_ANCHOR",
            before,
        )

    if before.next_action == LANE.TERMINAL_BLOCKED:
        return blocked_result(
            "BLOCKED_TERMINAL_POLICY_AUTHORITY",
            before,
        )

    if before.next_action == LANE.TARGET:
        return blocked_result(
            "COLLECTION_TARGET_REACHED",
            before,
        )

    require(
        before.protocol_authorized is True,
        "PROTOCOL_NOT_AUTHORIZED",
    )

    require(
        before.next_action in {
            LANE.CAPTURE,
            LANE.MATURE,
        },
        f"UNSUPPORTED_ACTION:{before.next_action}",
    )

    # Revalidate immediately before external acquisition.
    require(
        LANE.authority_valid(),
        "AUTHORITY_REVOKED",
    )

    snapshot = acquire()

    verify_snapshot(snapshot)

    if before.next_action == LANE.CAPTURE:
        feature_result = features(snapshot)

        result = LANE.capture_from_snapshot(
            snapshot=snapshot,
            feature_result=feature_result,
        )

    else:
        result = process_maturity(
            snapshot=snapshot
        )

    require(
        isinstance(result, Mapping),
        "COLLECTION_RESULT_INVALID",
    )

    require(
        result.get("action")
        in (
            EXPECTED_COLLECTION_ACTIONS
            | {"BLOCKED_UNCONFIRMED_M5_GAP"}
        ),
        "UNEXPECTED_COLLECTION_RESULT",
    )

    return dict(result)


def execute(
    *,
    acquire: Callable[
        [], Any
    ] = acquire_genuine_snapshot,
    features: Callable[
        [Any], Any
    ] = build_features,
    verify_snapshot: Callable[
        [Any], None
    ] = verify_snapshot_authority,
) -> dict[str, Any]:

    result = run_cycle(
        acquire=acquire,
        features=features,
        verify_snapshot=verify_snapshot,
    )

    return {
        **result,
        "version": VERSION,
        "live_authorized": False,
        "execution_authorized": False,
        "performance_evaluated": False,
        "pnl_evaluated": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--once",
        action="store_true",
        help="Run one authority-gated V2 research cycle",
    )

    args = parser.parse_args()

    try:
        if args.once:
            result = execute()

        else:
            state = LANE.inspect()

            result = {
                "version": VERSION,
                "action": "STATUS_ONLY",
                "state": state.to_dict(),
                "live_authorized": False,
                "execution_authorized": False,
                "performance_evaluated": False,
                "pnl_evaluated": False,
            }

    except Exception as exc:
        print(
            "R03_V2_ORCHESTRATOR_STATUS=BLOCKED"
        )
        print(
            f"ERROR_TYPE={type(exc).__name__}"
        )
        print(f"ERROR={exc}")
        print("LIVE_AUTHORIZED=false")
        print("EXECUTION_AUTHORIZED=false")
        return 2

    print(
        "R03_V2_ORCHESTRATOR_STATUS="
        + str(result.get("action", "UNKNOWN"))
    )

    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
            default=str,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
