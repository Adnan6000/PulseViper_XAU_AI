from __future__ import annotations

import importlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping

import MetaTrader5 as mt5


ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


adapter_module: Any = importlib.import_module(
    "02_AI.Adapters.xauusd_broker_adapter"
)


BrokerCostAdapter = (
    adapter_module.BrokerCostAdapter
)

CANONICAL_GOLD_SYMBOL = (
    adapter_module.CANONICAL_GOLD_SYMBOL
)


ANALYSIS_VERSION = (
    "XAUUSD_BROKER_ADAPTER_MT5_INTEGRATION_V1"
)

MAX_TICK_AGE_SECONDS = 180


def _is_sha256(
    value: Any,
) -> bool:

    return bool(
        isinstance(
            value,
            str,
        )
        and
        re.fullmatch(
            r"[0-9a-f]{64}",
            value,
        )
        is not None
    )


def _require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise RuntimeError(
            reason
        )


def _as_mapping(
    value: Any,
    reason: str,
) -> Mapping[str, Any]:

    if not isinstance(
        value,
        Mapping,
    ):
        raise RuntimeError(
            reason
        )

    return value


def _validate_snapshot(
    snapshot: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:

    canonical = _as_mapping(
        snapshot.get(
            "canonical_instrument"
        ),
        "CANONICAL_INSTRUMENT_DOCUMENT_MISSING",
    )

    resolution = _as_mapping(
        snapshot.get(
            "resolution"
        ),
        "RESOLUTION_DOCUMENT_MISSING",
    )

    broker_identity = _as_mapping(
        snapshot.get(
            "broker_identity"
        ),
        "BROKER_IDENTITY_DOCUMENT_MISSING",
    )

    contract = _as_mapping(
        snapshot.get(
            "contract"
        ),
        "CONTRACT_DOCUMENT_MISSING",
    )

    fingerprint = _as_mapping(
        snapshot.get(
            "contract_fingerprint"
        ),
        "CONTRACT_FINGERPRINT_DOCUMENT_MISSING",
    )

    tick = _as_mapping(
        snapshot.get(
            "tick"
        ),
        "TICK_DOCUMENT_MISSING",
    )

    spread = _as_mapping(
        snapshot.get(
            "spread"
        ),
        "SPREAD_DOCUMENT_MISSING",
    )

    safety = _as_mapping(
        snapshot.get(
            "safety"
        ),
        "SAFETY_DOCUMENT_MISSING",
    )

    canonical_symbol = str(
        canonical.get(
            "canonical_symbol",
            "",
        )
    )

    broker_symbol = str(
        resolution.get(
            "broker_symbol",
            "",
        )
    )

    contract_symbol = str(
        contract.get(
            "name",
            "",
        )
    )

    broker_server = str(
        broker_identity.get(
            "server",
            "",
        )
    )

    _require(
        canonical_symbol
        ==
        CANONICAL_GOLD_SYMBOL,
        "CANONICAL_SYMBOL_MISMATCH",
    )

    _require(
        bool(
            broker_symbol
        ),
        "BROKER_SYMBOL_EMPTY",
    )

    _require(
        contract_symbol
        ==
        broker_symbol,
        "RESOLUTION_CONTRACT_SYMBOL_MISMATCH",
    )

    _require(
        bool(
            broker_server
        ),
        "BROKER_SERVER_EMPTY",
    )

    _require(
        str(
            contract.get(
                "currency_profit",
                "",
            )
        ).upper()
        ==
        "USD",
        "RESOLVED_GOLD_QUOTE_CURRENCY_IS_NOT_USD",
    )

    _require(
        _is_sha256(
            fingerprint.get(
                "sha256"
            )
        ),
        "INVALID_CONTRACT_FINGERPRINT_SHA256",
    )

    _require(
        bool(
            safety.get(
                "read_only_market_adapter",
                False,
            )
        ),
        "ADAPTER_NOT_MARKED_READ_ONLY",
    )

    _require(
        safety.get(
            "orders_sent"
        )
        is False,
        "ORDERS_SENT_SAFETY_CONTRACT_FAILED",
    )

    _require(
        safety.get(
            "positions_modified"
        )
        is False,
        "POSITIONS_MODIFIED_SAFETY_CONTRACT_FAILED",
    )

    _require(
        safety.get(
            "risk_engine_modified"
        )
        is False,
        "RISK_ENGINE_SAFETY_CONTRACT_FAILED",
    )

    _require(
        safety.get(
            "sizing_modified"
        )
        is False,
        "SIZING_SAFETY_CONTRACT_FAILED",
    )

    _require(
        safety.get(
            "live_authorized"
        )
        is False,
        "LIVE_AUTHORIZATION_MUST_REMAIN_FALSE",
    )

    tick_fresh = bool(
        tick.get(
            "fresh",
            False,
        )
    )

    tick_valid = bool(
        tick.get(
            "valid_bid_ask",
            False,
        )
    )

    costs_usable = bool(
        spread.get(
            "usable_for_runtime_costs",
            False,
        )
    )

    if costs_usable:

        _require(
            tick_valid,
            "USABLE_COSTS_REQUIRE_VALID_BID_ASK",
        )

        _require(
            tick_fresh,
            "USABLE_COSTS_REQUIRE_FRESH_TICK",
        )

        _require(
            spread.get(
                "spread_price"
            )
            is not None,
            "USABLE_COSTS_REQUIRE_SPREAD_PRICE",
        )

        _require(
            spread.get(
                "spread_ticks"
            )
            is not None,
            "USABLE_COSTS_REQUIRE_SPREAD_TICKS",
        )

        _require(
            spread.get(
                "spread_bps"
            )
            is not None,
            "USABLE_COSTS_REQUIRE_SPREAD_BPS",
        )

        integration_status = (
            "PASS_FRESH_RUNTIME_COSTS"
        )

    else:

        _require(
            not tick_fresh,
            "FRESH_TICK_MUST_NOT_PRODUCE_UNUSABLE_COSTS",
        )

        integration_status = (
            "PASS_SYMBOL_CONTRACT_STALE_COSTS"
        )

    return {
        "integration_status": (
            integration_status
        ),
        "canonical_symbol": (
            canonical_symbol
        ),
        "broker_symbol": (
            broker_symbol
        ),
        "broker_server": (
            broker_server
        ),
        "contract_fingerprint_sha256": (
            fingerprint.get(
                "sha256"
            )
        ),
        "candidate_count": (
            resolution.get(
                "candidate_count"
            )
        ),
        "rejected_gold_like_count": (
            resolution.get(
                "rejected_gold_like_count"
            )
        ),
        "tick_valid_bid_ask": (
            tick_valid
        ),
        "tick_fresh": (
            tick_fresh
        ),
        "tick_age_seconds": (
            tick.get(
                "tick_age_seconds"
            )
        ),
        "runtime_costs_usable": (
            costs_usable
        ),
        "spread_price": (
            spread.get(
                "spread_price"
            )
        ),
        "spread_ticks": (
            spread.get(
                "spread_ticks"
            )
        ),
        "spread_bps": (
            spread.get(
                "spread_bps"
            )
        ),
        "spread_atr14": (
            spread.get(
                "spread_atr14"
            )
        ),
    }


def run_integration(
) -> dict[str, Any]:

    initialized = (
        mt5.initialize()
    )

    if not initialized:

        raise RuntimeError(
            (
                "MT5_INITIALIZE_FAILED:"
                f"{mt5.last_error()}"
            )
        )

    try:

        terminal = (
            mt5.terminal_info()
        )

        account = (
            mt5.account_info()
        )

        _require(
            terminal is not None,
            "MT5_TERMINAL_INFO_UNAVAILABLE",
        )

        _require(
            account is not None,
            "MT5_ACCOUNT_INFO_UNAVAILABLE",
        )

        _require(
            bool(
                getattr(
                    terminal,
                    "connected",
                    False,
                )
            ),
            "MT5_TERMINAL_NOT_CONNECTED",
        )

        adapter = (
            BrokerCostAdapter(
                mt5,
                max_tick_age_seconds=(
                    MAX_TICK_AGE_SECONDS
                ),
            )
        )

        snapshot = (
            adapter.snapshot(
                include_m5_atr=True
            )
        )

        validation = (
            _validate_snapshot(
                snapshot
            )
        )

        return {
            "valid": True,
            "reason": (
                "OK_XAUUSD_BROKER_ADAPTER_MT5_INTEGRATION"
            ),
            "analysis_version": (
                ANALYSIS_VERSION
            ),
            "validation": (
                validation
            ),
            "snapshot": (
                snapshot
            ),
            "scientific_policy": {
                "real_mt5_used": True,
                "market_metadata_read_only": True,
                "symbol_resolution_tested": True,
                "contract_snapshot_tested": True,
                "tick_freshness_tested": True,
                "normalized_runtime_costs_tested": True,
                "model_dataset_loaded": False,
                "train_used": False,
                "validation_used": False,
                "test_used": False,
                "model_artifacts_written": False,
                "orders_sent": False,
                "positions_modified": False,
                "risk_engine_modified": False,
                "sizing_modified": False,
                "live_authorized": False,
            },
            "next_decision_contract": {
                "if_fresh_runtime_costs": (
                    "ADAPTER_READY_FOR_RESEARCH_DATA_PIPELINE_WIRING"
                ),
                "if_stale_runtime_costs": (
                    "SYMBOL_AND_CONTRACT_ADAPTER_PASS; "
                    "RECHECK_COST_SNAPSHOT_WHEN_GOLD_MARKET_IS_ACTIVE"
                ),
                "execution_integration_allowed": False,
                "test_dataset_evaluation_allowed": False,
            },
        }

    finally:

        mt5.shutdown()


def main() -> int:

    try:

        result = (
            run_integration()
        )

    except Exception as exc:

        try:

            mt5.shutdown()

        except Exception:

            pass

        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "XAUUSD_BROKER_ADAPTER_MT5_INTEGRATION_FAILED"
                    ),
                    "analysis_version": (
                        ANALYSIS_VERSION
                    ),
                    "error_type": (
                        type(
                            exc
                        ).__name__
                    ),
                    "error": (
                        str(
                            exc
                        )
                    ),
                    "orders_sent": False,
                    "positions_modified": False,
                    "risk_engine_modified": False,
                    "sizing_modified": False,
                    "model_artifacts_written": False,
                    "test_dataset_used": False,
                    "live_authorized": False,
                },
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
        )

        return 2

    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    )

    return 0


if __name__ == "__main__":

    raise SystemExit(
        main()
    )