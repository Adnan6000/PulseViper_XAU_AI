"""
Offline tests for Gate 15C frozen C04 forward outcome contract.
"""

from __future__ import annotations

import importlib
from typing import Any

import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_contract"
)


def test_01_contract_identity() -> None:
    assert (
        module.CONTRACT_VERSION
        ==
        "FROZEN_C04_FORWARD_OUTCOME_CONTRACT_V1"
    )

    assert (
        module.CONTRACT_STATUS
        ==
        "DEFINED_NOT_YET_MATURED_OR_EVALUATED"
    )

    assert (
        module.MODEL_TARGET_CONTRACT
        ==
        "CLEAN_DIRECTIONAL_EXCURSION_V2"
    )


def test_02_base_timeframe_and_horizon() -> None:
    assert module.BASE_TIMEFRAME == "M5"
    assert module.BASE_TIMEFRAME_MINUTES == 5
    assert module.HORIZON_BARS == 12
    assert module.HORIZON_MINUTES == 60

    assert (
        module.BASE_TIMEFRAME_MINUTES
        *
        module.HORIZON_BARS
        ==
        module.HORIZON_MINUTES
    )


def test_03_reference_price_and_volatility() -> None:
    assert (
        module.REFERENCE_PRICE
        ==
        "DECISION_M5_CLOSE"
    )

    assert (
        module.REFERENCE_VOLATILITY
        ==
        "DECISION_M5_ATR14"
    )

    assert (
        module.FUTURE_PATH_SOURCE
        ==
        "NEXT_12_COMPLETED_M5_BARS_HIGH_LOW"
    )


def test_04_frozen_excursion_thresholds() -> None:
    assert module.PROFIT_ATR == pytest.approx(
        1.25
    )

    assert module.MAX_ADVERSE_ATR == pytest.approx(
        0.75
    )


def test_05_exact_class_mapping() -> None:
    assert module.CLASS_MAPPING == {
        "SHORT": -1,
        "NO_TRADE": 0,
        "LONG": 1,
    }


def test_06_exact_v2_rule_semantics() -> None:
    assert (
        module.LONG_RULE
        ==
        (
            "MAX_UP_EXCURSION_GTE_1_25_ATR_"
            "AND_MAX_DOWN_EXCURSION_LTE_0_75_ATR"
        )
    )

    assert (
        module.SHORT_RULE
        ==
        (
            "MAX_DOWN_EXCURSION_GTE_1_25_ATR_"
            "AND_MAX_UP_EXCURSION_LTE_0_75_ATR"
        )
    )

    assert (
        module.NO_TRADE_RULE
        ==
        "ALL_OTHER_FUTURE_PATHS"
    )


def test_07_future_data_is_outcome_only() -> None:
    assert (
        module.FUTURE_DATA_POLICY
        ==
        "OUTCOME_ONLY_NEVER_FEATURE_OR_INFERENCE_INPUT"
    )


def test_08_contract_fingerprint_is_frozen() -> None:
    assert (
        module.compute_contract_fingerprint()
        ==
        (
            "01fe52a2f068fcc8fb2fc5b89dd7e19d"
            "c974fc2d967cfb791e75c3415804ce87"
        )
    )

    assert (
        module.EXPECTED_CONTRACT_FINGERPRINT_SHA256
        ==
        module.compute_contract_fingerprint()
    )


def test_09_contract_validation_passes() -> None:
    assert (
        module.verify_frozen_contract()
        is True
    )

    assert (
        module.validate_contract_document(
            module.canonical_contract_document()
        )
        is True
    )


def test_10_contract_tampering_fails_closed() -> None:
    document = (
        module.canonical_contract_document()
    )

    document[
        "horizon_bars"
    ] = 13

    with pytest.raises(
        module.FrozenC04ForwardOutcomeContractError,
        match=(
            "FORWARD_OUTCOME_CONTRACT_DOCUMENT_MISMATCH"
        ),
    ):
        module.validate_contract_document(
            document
        )


def test_11_gate_15c_does_not_authorize_evaluation() -> None:
    assert (
        module.PERFORMANCE_EVALUATION_AUTHORIZED
        is False
    )

    assert (
        module.PNL_EVALUATION_AUTHORIZED
        is False
    )

    assert (
        module.TRANSACTION_COST_EVALUATION_AUTHORIZED
        is False
    )

    with pytest.raises(
        module.ForwardOutcomeEvaluationNotAuthorizedError,
        match=(
            "FORWARD_OUTCOME_EVALUATION_NOT_AUTHORIZED"
        ),
    ):
        module.evaluate_outcome()


def test_12_no_model_or_feature_change_authority() -> None:
    assert (
        module.MODEL_CHANGE_AUTHORIZED
        is False
    )

    assert (
        module.FEATURE_CHANGE_AUTHORIZED
        is False
    )


def test_13_holdouts_remain_unauthorized() -> None:
    assert (
        module.VALIDATION_PARTITION_ACCESS_AUTHORIZED
        is False
    )

    assert (
        module.TEST_PARTITION_ACCESS_AUTHORIZED
        is False
    )


def test_14_live_and_execution_remain_false() -> None:
    assert module.LIVE_AUTHORIZED is False
    assert module.EXECUTION_AUTHORIZED is False


def test_15_source_authorities_are_explicit() -> None:
    assert (
        "02_AI/Dataset/training_matrix_builder.py"
        in module.SOURCE_AUTHORITIES
    )

    assert (
        "02_AI/Dataset/training_target_relabeler.py"
        in module.SOURCE_AUTHORITIES
    )


def test_16_source_semantics_match_frozen_contract() -> None:
    builder = (
        module.SOURCE_SEMANTICS[
            "training_matrix_builder"
        ]
    )

    relabeler = (
        module.SOURCE_SEMANTICS[
            "training_target_relabeler"
        ]
    )

    protocol = (
        module.SOURCE_SEMANTICS[
            "research_protocol"
        ]
    )

    assert (
        builder[
            "base_timeframe_default"
        ]
        ==
        "M5"
    )

    assert (
        builder[
            "target_horizon_bars_default"
        ]
        ==
        12
    )

    assert (
        builder[
            "entry_reference"
        ]
        ==
        "CURRENT_BAR_CLOSE"
    )

    assert (
        builder[
            "atr_reference"
        ]
        ==
        "CURRENT_BAR_ATR14"
    )

    assert (
        relabeler[
            "target_contract"
        ]
        ==
        "CLEAN_DIRECTIONAL_EXCURSION_V2"
    )

    assert relabeler[
        "profit_atr"
    ] == pytest.approx(
        1.25
    )

    assert relabeler[
        "max_adverse_atr"
    ] == pytest.approx(
        0.75
    )

    assert (
        protocol[
            "target_horizon_bars"
        ]
        ==
        12
    )

    assert (
        protocol[
            "purge_rows"
        ]
        ==
        12
    )