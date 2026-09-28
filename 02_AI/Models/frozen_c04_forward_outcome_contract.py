"""
===============================================================================
Module      : frozen_c04_forward_outcome_contract.py
Project     : PulseViper XAU AI
Purpose     : Gate 15C — Frozen C04 Forward Outcome Contract
===============================================================================

This module freezes the forward outcome definition that corresponds to the
already-frozen C04 model target.

It does NOT:
- read future market data
- calculate an outcome
- calculate accuracy / win rate / PnL / return / drawdown
- access MT5
- access validation/test holdouts
- retrain/refit/calibrate/tune/reselect the model
- authorize live trading
- authorize execution

Frozen source semantics
-----------------------
Model target contract:
    CLEAN_DIRECTIONAL_EXCURSION_V2

Base timeframe:
    M5

Forward horizon:
    12 completed future M5 bars = 60 minutes

Reference price:
    close of the decision M5 bar

Reference volatility:
    ATR14 of the decision M5 bar

LONG:
    max future upside excursion >= 1.25 ATR
    AND
    max future downside excursion <= 0.75 ATR

SHORT:
    max future downside excursion >= 1.25 ATR
    AND
    max future upside excursion <= 0.75 ATR

NO_TRADE:
    all other future paths

IMPORTANT:
This Gate freezes the definition only.
Actual forward outcome maturation/evaluation remains unauthorized here.
===============================================================================
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


# =============================================================================
# Contract Identity
# =============================================================================

CONTRACT_VERSION: str = (
    "FROZEN_C04_FORWARD_OUTCOME_CONTRACT_V1"
)

CONTRACT_STATUS: str = (
    "DEFINED_NOT_YET_MATURED_OR_EVALUATED"
)

MODEL_TARGET_CONTRACT: str = (
    "CLEAN_DIRECTIONAL_EXCURSION_V2"
)

CANONICAL_INSTRUMENT: str = "XAUUSD"

BASE_TIMEFRAME: str = "M5"

BASE_TIMEFRAME_MINUTES: int = 5

HORIZON_BARS: int = 12

HORIZON_MINUTES: int = 60


# =============================================================================
# Frozen Target Semantics
# =============================================================================

REFERENCE_PRICE: str = (
    "DECISION_M5_CLOSE"
)

REFERENCE_VOLATILITY: str = (
    "DECISION_M5_ATR14"
)

FUTURE_PATH_SOURCE: str = (
    "NEXT_12_COMPLETED_M5_BARS_HIGH_LOW"
)

PROFIT_ATR: float = 1.25

MAX_ADVERSE_ATR: float = 0.75

CLASS_MAPPING: dict[str, int] = {
    "SHORT": -1,
    "NO_TRADE": 0,
    "LONG": 1,
}

LONG_RULE: str = (
    "MAX_UP_EXCURSION_GTE_1_25_ATR_"
    "AND_MAX_DOWN_EXCURSION_LTE_0_75_ATR"
)

SHORT_RULE: str = (
    "MAX_DOWN_EXCURSION_GTE_1_25_ATR_"
    "AND_MAX_UP_EXCURSION_LTE_0_75_ATR"
)

NO_TRADE_RULE: str = (
    "ALL_OTHER_FUTURE_PATHS"
)

FUTURE_DATA_POLICY: str = (
    "OUTCOME_ONLY_NEVER_FEATURE_OR_INFERENCE_INPUT"
)


# =============================================================================
# Authority Boundaries
# =============================================================================

PERFORMANCE_EVALUATION_AUTHORIZED: bool = False

PNL_EVALUATION_AUTHORIZED: bool = False

TRANSACTION_COST_EVALUATION_AUTHORIZED: bool = False

MODEL_CHANGE_AUTHORIZED: bool = False

FEATURE_CHANGE_AUTHORIZED: bool = False

VALIDATION_PARTITION_ACCESS_AUTHORIZED: bool = False

TEST_PARTITION_ACCESS_AUTHORIZED: bool = False

LIVE_AUTHORIZED: bool = False

EXECUTION_AUTHORIZED: bool = False


# =============================================================================
# Source Authorities
# =============================================================================

SOURCE_AUTHORITIES: tuple[str, ...] = (
    "02_AI/Dataset/training_matrix_builder.py",
    "02_AI/Dataset/training_target_relabeler.py",
    (
        "04_Testing/research/portable_331/train/"
        "design_xauusd_portable_331_train_model_research_protocol.py"
    ),
)

SOURCE_SEMANTICS: dict[str, Any] = {
    "training_matrix_builder": {
        "base_timeframe_default": "M5",
        "target_horizon_bars_default": 12,
        "entry_reference": "CURRENT_BAR_CLOSE",
        "atr_reference": "CURRENT_BAR_ATR14",
        "future_window": "INDEX_PLUS_1_THROUGH_INDEX_PLUS_12",
    },
    "training_target_relabeler": {
        "target_contract": (
            "CLEAN_DIRECTIONAL_EXCURSION_V2"
        ),
        "profit_atr": 1.25,
        "max_adverse_atr": 0.75,
    },
    "research_protocol": {
        "target_horizon_bars": 12,
        "purge_rows": 12,
    },
}


# =============================================================================
# Errors
# =============================================================================

class FrozenC04ForwardOutcomeContractError(
    RuntimeError
):
    """Fail-closed contract validation error."""


class ForwardOutcomeEvaluationNotAuthorizedError(
    FrozenC04ForwardOutcomeContractError
):
    """Raised if Gate 15C is asked to evaluate future outcomes."""


# =============================================================================
# Canonical Contract
# =============================================================================

def canonical_contract_document() -> dict[str, Any]:
    """
    Return the immutable semantic core used for contract fingerprinting.

    Do not add runtime timestamps, Git SHAs, evidence paths, or mutable
    environment information here.
    """

    return {
        "contract_version": (
            CONTRACT_VERSION
        ),
        "model_target_contract": (
            MODEL_TARGET_CONTRACT
        ),
        "canonical_instrument": (
            CANONICAL_INSTRUMENT
        ),
        "base_timeframe": (
            BASE_TIMEFRAME
        ),
        "horizon_bars": (
            HORIZON_BARS
        ),
        "horizon_minutes": (
            HORIZON_MINUTES
        ),
        "reference_price": (
            REFERENCE_PRICE
        ),
        "reference_volatility": (
            REFERENCE_VOLATILITY
        ),
        "future_path_source": (
            FUTURE_PATH_SOURCE
        ),
        "profit_atr": (
            PROFIT_ATR
        ),
        "max_adverse_atr": (
            MAX_ADVERSE_ATR
        ),
        "class_mapping": dict(
            CLASS_MAPPING
        ),
        "long_rule": (
            LONG_RULE
        ),
        "short_rule": (
            SHORT_RULE
        ),
        "no_trade_rule": (
            NO_TRADE_RULE
        ),
        "future_data_policy": (
            FUTURE_DATA_POLICY
        ),
        "performance_evaluation_authorized": (
            PERFORMANCE_EVALUATION_AUTHORIZED
        ),
        "pnl_evaluation_authorized": (
            PNL_EVALUATION_AUTHORIZED
        ),
        "live_authorized": (
            LIVE_AUTHORIZED
        ),
        "execution_authorized": (
            EXECUTION_AUTHORIZED
        ),
    }


def canonical_json_bytes(
    document: Mapping[str, Any],
) -> bytes:
    return json.dumps(
        document,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
        ensure_ascii=True,
        allow_nan=False,
    ).encode(
        "utf-8"
    )


def compute_contract_fingerprint() -> str:
    return hashlib.sha256(
        canonical_json_bytes(
            canonical_contract_document()
        )
    ).hexdigest()


EXPECTED_CONTRACT_FINGERPRINT_SHA256: str = (
    "01fe52a2f068fcc8fb2fc5b89dd7e19dc974fc2d967cfb791e75c3415804ce87"
)


# =============================================================================
# Validation
# =============================================================================

def validate_contract_document(
    document: Mapping[str, Any],
) -> bool:

    expected = (
        canonical_contract_document()
    )

    if dict(
        document
    ) != expected:
        raise (
            FrozenC04ForwardOutcomeContractError(
                "FORWARD_OUTCOME_CONTRACT_DOCUMENT_MISMATCH"
            )
        )

    actual_fingerprint = hashlib.sha256(
        canonical_json_bytes(
            document
        )
    ).hexdigest()

    if (
        actual_fingerprint
        !=
        EXPECTED_CONTRACT_FINGERPRINT_SHA256
    ):
        raise (
            FrozenC04ForwardOutcomeContractError(
                (
                    "FORWARD_OUTCOME_CONTRACT_"
                    "FINGERPRINT_MISMATCH:"
                    f"{actual_fingerprint}"
                )
            )
        )

    if (
        HORIZON_BARS
        *
        BASE_TIMEFRAME_MINUTES
        !=
        HORIZON_MINUTES
    ):
        raise (
            FrozenC04ForwardOutcomeContractError(
                "FORWARD_OUTCOME_HORIZON_DURATION_MISMATCH"
            )
        )

    if CLASS_MAPPING != {
        "SHORT": -1,
        "NO_TRADE": 0,
        "LONG": 1,
    }:
        raise (
            FrozenC04ForwardOutcomeContractError(
                "FORWARD_OUTCOME_CLASS_MAPPING_MISMATCH"
            )
        )

    if (
        PERFORMANCE_EVALUATION_AUTHORIZED
        or
        PNL_EVALUATION_AUTHORIZED
        or
        TRANSACTION_COST_EVALUATION_AUTHORIZED
        or
        MODEL_CHANGE_AUTHORIZED
        or
        FEATURE_CHANGE_AUTHORIZED
        or
        VALIDATION_PARTITION_ACCESS_AUTHORIZED
        or
        TEST_PARTITION_ACCESS_AUTHORIZED
        or
        LIVE_AUTHORIZED
        or
        EXECUTION_AUTHORIZED
    ):
        raise (
            FrozenC04ForwardOutcomeContractError(
                "GATE_15C_AUTHORIZATION_BOUNDARY_VIOLATION"
            )
        )

    return True


def verify_frozen_contract() -> bool:
    document = (
        canonical_contract_document()
    )

    if (
        compute_contract_fingerprint()
        !=
        EXPECTED_CONTRACT_FINGERPRINT_SHA256
    ):
        raise (
            FrozenC04ForwardOutcomeContractError(
                "FROZEN_FORWARD_OUTCOME_CONTRACT_HASH_CHANGED"
            )
        )

    return validate_contract_document(
        document
    )


def evaluate_outcome(
    *args: Any,
    **kwargs: Any,
) -> Any:
    """
    Gate 15C freezes the definition only.

    Actual future-data maturation and outcome calculation must be implemented
    in a later explicitly authorized gate.
    """

    del args
    del kwargs

    raise (
        ForwardOutcomeEvaluationNotAuthorizedError(
            (
                "GATE_15C_CONTRACT_DEFINED_BUT_"
                "FORWARD_OUTCOME_EVALUATION_NOT_AUTHORIZED"
            )
        )
    )