from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


RUNNER_PATH = (
    Path(__file__).resolve().parent
    / "run_xauusd_gate_15d_c_b2d_g6_e_probability_discrimination_diagnostic.py"
)


spec = importlib.util.spec_from_file_location(
    "g6e",
    RUNNER_PATH,
)

assert spec is not None
assert spec.loader is not None

g6e: Any = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(
    g6e
)


def test_01_base_authority_is_g6d() -> None:

    assert (
        g6e.BASE_AUTHORITY_COMMIT
        ==
        "e1639f68cb686aafd949b6e402d576e4a0885257"
    )


def test_02_sample_count_is_30() -> None:

    assert (
        g6e.EXPECTED_SAMPLE_COUNT
        ==
        30
    )


def test_03_pairwise_auc_perfect() -> None:

    value = g6e.pairwise_auc(
        [
            0.8,
            0.9,
        ],
        [
            0.1,
            0.2,
        ],
    )

    assert (
        value
        ==
        1.0
    )


def test_04_pairwise_auc_inverse() -> None:

    value = g6e.pairwise_auc(
        [
            0.1,
            0.2,
        ],
        [
            0.8,
            0.9,
        ],
    )

    assert (
        value
        ==
        0.0
    )


def test_05_pairwise_auc_tie() -> None:

    value = g6e.pairwise_auc(
        [
            0.5,
        ],
        [
            0.5,
        ],
    )

    assert (
        value
        ==
        0.5
    )


def test_06_class_probability_short() -> None:

    row = {
        "probability_short": 0.2,
        "probability_no_trade": 0.3,
        "probability_long": 0.5,
    }

    assert (
        g6e.class_probability(
            row,
            -1,
        )
        ==
        0.2
    )


def test_07_class_probability_no_trade() -> None:

    row = {
        "probability_short": 0.2,
        "probability_no_trade": 0.3,
        "probability_long": 0.5,
    }

    assert (
        g6e.class_probability(
            row,
            0,
        )
        ==
        0.3
    )


def test_08_class_probability_long() -> None:

    row = {
        "probability_short": 0.2,
        "probability_no_trade": 0.3,
        "probability_long": 0.5,
    }

    assert (
        g6e.class_probability(
            row,
            1,
        )
        ==
        0.5
    )


def test_09_true_rank_summary() -> None:

    rows = []

    for index in range(
        10
    ):

        rows.append(
            {
                "logical_observation_id": str(
                    index
                ),
                "decision_time_utc": "2026-10-01T00:00:00Z",
                "outcome_class": 1,
                "probability_short": 0.1,
                "probability_no_trade": 0.2,
                "probability_long": 0.7,
                "true_class_probability": 0.7,
                "true_class_rank": 1,
            }
        )

    for index in range(
        10,
        20,
    ):

        rows.append(
            {
                "logical_observation_id": str(
                    index
                ),
                "decision_time_utc": "2026-10-01T00:00:00Z",
                "outcome_class": 0,
                "probability_short": 0.1,
                "probability_no_trade": 0.7,
                "probability_long": 0.2,
                "true_class_probability": 0.7,
                "true_class_rank": 1,
            }
        )

    for index in range(
        20,
        30,
    ):

        rows.append(
            {
                "logical_observation_id": str(
                    index
                ),
                "decision_time_utc": "2026-10-01T00:00:00Z",
                "outcome_class": -1,
                "probability_short": 0.7,
                "probability_no_trade": 0.2,
                "probability_long": 0.1,
                "true_class_probability": 0.7,
                "true_class_rank": 1,
            }
        )

    result = g6e.diagnostic_summary(
        rows
    )

    assert (
        result[
            "true_class_rank_1_count"
        ]
        ==
        30
    )

    assert (
        result[
            "mean_true_class_rank"
        ]
        ==
        1.0
    )


def test_10_summary_requires_30_rows() -> None:

    try:

        g6e.diagnostic_summary(
            []
        )

    except g6e.G6EDiagnosticError as exc:

        assert (
            "UNEXPECTED_DIAGNOSTIC_SAMPLE_COUNT"
            in str(
                exc
            )
        )

    else:

        raise AssertionError(
            "Expected diagnostic failure"
        )


def test_11_exact_g5_hash_required() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "RUNTIME_LEDGER_NOT_EXACT_G5_BASELINE"
        in text
    )


def test_12_g6d_authority_required() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "G6D_DIAGNOSTIC_MISSING"
        in text
    )

    assert (
        "G6D_SAMPLE_COUNT_MISMATCH"
        in text
    )


def test_13_linkage_is_checked() -> None:

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


def test_14_no_training() -> None:

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
        '"model_reselection_performed": False'
        in text
    )


def test_15_no_calibration_or_threshold_tuning() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        '"probability_calibration_performed": False'
        in text
    )

    assert (
        '"threshold_tuning_performed": False'
        in text
    )


def test_16_no_mt5() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert "MetaTrader5" not in text
    assert "order_send(" not in text
    assert "order_check(" not in text


def test_17_no_pnl_live_execution() -> None:

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


def test_18_no_promotion_interpretation() -> None:

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


def test_19_ledgers_are_read_only() -> None:

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


def test_20_macro_auc_is_reported() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "MACRO_PAIRWISE_AUC="
        in text
    )

    assert (
        "MACRO_MEAN_PROBABILITY_SEPARATION="
        in text
    )