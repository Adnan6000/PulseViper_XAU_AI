from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


RUNNER_PATH = (
    Path(__file__).resolve().parent
    / "run_xauusd_gate_15d_c_b2d_g6_c_forward_error_confidence_diagnostic.py"
)


spec = importlib.util.spec_from_file_location(
    "g6c",
    RUNNER_PATH,
)

assert spec is not None
assert spec.loader is not None

g6c: Any = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(
    g6c
)


def test_01_base_authority_is_g6b_publication() -> None:

    assert (
        g6c.BASE_AUTHORITY_COMMIT
        ==
        "ddc028899f382a2ea24520ea1ed0347d06906c00"
    )


def test_02_sample_count_is_frozen_30() -> None:

    assert (
        g6c.EXPECTED_SAMPLE_COUNT
        ==
        30
    )


def test_03_contract_fingerprint_is_frozen() -> None:

    assert (
        g6c.EXPECTED_CONTRACT_FINGERPRINT
        ==
        "32d8af41e2e1d128df664c8fc81bcf52a6a2b341f491a05d65179f740460875c"
    )


def test_04_high_confidence_threshold_is_diagnostic_only() -> None:

    assert (
        g6c.HIGH_CONFIDENCE_ERROR_THRESHOLD
        ==
        0.50
    )

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        '"high_confidence_error_threshold_is_trading_threshold": False'
        in text
    )


def test_05_mean_empty_is_zero() -> None:

    assert (
        g6c.mean(
            []
        )
        ==
        0.0
    )


def test_06_mean_values() -> None:

    assert (
        g6c.mean(
            [
                1.0,
                2.0,
                3.0,
            ]
        )
        ==
        2.0
    )


def test_07_diagnostic_counts_false_long() -> None:

    rows = [
        {
            "logical_observation_id": "a",
            "decision_time_utc": "2026-10-01T00:00:00Z",
            "predicted_class": 1,
            "predicted_label": "LONG",
            "outcome_class": -1,
            "outcome_label": "SHORT",
            "probability_short": 0.20,
            "probability_no_trade": 0.20,
            "probability_long": 0.60,
            "winner_probability": 0.60,
            "runner_up_class": 0,
            "runner_up_probability": 0.20,
            "confidence_margin": 0.40,
            "correct": False,
            "high_confidence_error": True,
        }
    ] * 30

    result = g6c.diagnostic_summary(
        rows
    )

    assert (
        result[
            "false_long_count"
        ]
        ==
        30
    )


def test_08_diagnostic_counts_missed_short() -> None:

    rows = [
        {
            "logical_observation_id": str(index),
            "decision_time_utc": "2026-10-01T00:00:00Z",
            "predicted_class": 1,
            "predicted_label": "LONG",
            "outcome_class": -1,
            "outcome_label": "SHORT",
            "probability_short": 0.20,
            "probability_no_trade": 0.20,
            "probability_long": 0.60,
            "winner_probability": 0.60,
            "runner_up_class": 0,
            "runner_up_probability": 0.20,
            "confidence_margin": 0.40,
            "correct": False,
            "high_confidence_error": True,
        }
        for index in range(
            30
        )
    ]

    result = g6c.diagnostic_summary(
        rows
    )

    assert (
        result[
            "missed_short_count"
        ]
        ==
        30
    )


def test_09_diagnostic_counts_missed_no_trade() -> None:

    rows = [
        {
            "logical_observation_id": str(index),
            "decision_time_utc": "2026-10-01T00:00:00Z",
            "predicted_class": 1,
            "predicted_label": "LONG",
            "outcome_class": 0,
            "outcome_label": "NO_TRADE",
            "probability_short": 0.20,
            "probability_no_trade": 0.20,
            "probability_long": 0.60,
            "winner_probability": 0.60,
            "runner_up_class": 0,
            "runner_up_probability": 0.20,
            "confidence_margin": 0.40,
            "correct": False,
            "high_confidence_error": True,
        }
        for index in range(
            30
        )
    ]

    result = g6c.diagnostic_summary(
        rows
    )

    assert (
        result[
            "missed_no_trade_count"
        ]
        ==
        30
    )


def test_10_pair_counts_are_descriptive() -> None:

    rows = [
        {
            "logical_observation_id": str(index),
            "decision_time_utc": "2026-10-01T00:00:00Z",
            "predicted_class": 1,
            "predicted_label": "LONG",
            "outcome_class": -1,
            "outcome_label": "SHORT",
            "probability_short": 0.20,
            "probability_no_trade": 0.20,
            "probability_long": 0.60,
            "winner_probability": 0.60,
            "runner_up_class": 0,
            "runner_up_probability": 0.20,
            "confidence_margin": 0.40,
            "correct": False,
            "high_confidence_error": True,
        }
        for index in range(
            30
        )
    ]

    result = g6c.diagnostic_summary(
        rows
    )

    assert (
        result[
            "prediction_outcome_pair_counts"
        ][
            "LONG->SHORT"
        ]
        ==
        30
    )


def test_11_correct_and_incorrect_confidence_are_separate() -> None:

    rows: list[dict[str, Any]] = []

    for index in range(
        15
    ):

        rows.append(
            {
                "logical_observation_id": f"c{index}",
                "decision_time_utc": "2026-10-01T00:00:00Z",
                "predicted_class": 1,
                "predicted_label": "LONG",
                "outcome_class": 1,
                "outcome_label": "LONG",
                "probability_short": 0.10,
                "probability_no_trade": 0.10,
                "probability_long": 0.80,
                "winner_probability": 0.80,
                "runner_up_class": 0,
                "runner_up_probability": 0.10,
                "confidence_margin": 0.70,
                "correct": True,
                "high_confidence_error": False,
            }
        )

    for index in range(
        15
    ):

        rows.append(
            {
                "logical_observation_id": f"i{index}",
                "decision_time_utc": "2026-10-01T01:00:00Z",
                "predicted_class": 1,
                "predicted_label": "LONG",
                "outcome_class": 0,
                "outcome_label": "NO_TRADE",
                "probability_short": 0.20,
                "probability_no_trade": 0.30,
                "probability_long": 0.50,
                "winner_probability": 0.50,
                "runner_up_class": 0,
                "runner_up_probability": 0.30,
                "confidence_margin": 0.20,
                "correct": False,
                "high_confidence_error": True,
            }
        )

    result = g6c.diagnostic_summary(
        rows
    )

    assert (
        result[
            "mean_winner_probability_correct"
        ]
        ==
        0.8
    )

    assert (
        result[
            "mean_winner_probability_incorrect"
        ]
        ==
        0.5
    )


def test_12_exact_g5_hash_binding_is_required() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "RUNTIME_LEDGER_NOT_EXACT_G5_BASELINE"
        in text
    )


def test_13_g6b_authority_is_required() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "G6B_STATUS_NOT_PASS"
        in text
    )

    assert (
        "G6B_SAMPLE_COUNT_MISMATCH"
        in text
    )


def test_14_observation_outcome_linkage_is_checked() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "OUTCOME_OBSERVATION_FINGERPRINT_MISMATCH"
        in text
    )

    assert (
        "DECISION_TIME_LINKAGE_MISMATCH"
        in text
    )


def test_15_no_training_or_calibration() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        '"retraining_performed": False'
        in text
    )

    assert (
        '"refitting_performed": False'
        in text
    )

    assert (
        '"calibration_performed": False'
        in text
    )

    assert (
        '"model_reselection_performed": False'
        in text
    )

    assert (
        '"threshold_tuning_performed": False'
        in text
    )


def test_16_no_mt5_or_execution_api() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert "MetaTrader5" not in text
    assert "order_send(" not in text
    assert "order_check(" not in text
    assert "positions_get(" not in text


def test_17_no_pnl_or_live_execution() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        '"pnl_evaluated": False'
        in text
    )

    assert (
        '"live_authorized": False'
        in text
    )

    assert (
        '"execution_authorized": False'
        in text
    )


def test_18_no_promotion_verdict() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        '"performance_interpreted_for_promotion": False'
        in text
    )

    assert (
        '"pass_fail_threshold_defined": False'
        in text
    )


def test_19_ledgers_remain_read_only() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "RUNTIME_LEDGER_CHANGED_DURING_DIAGNOSTIC"
        in text
    )

    assert (
        '"ledger_write_performed": False'
        in text
    )