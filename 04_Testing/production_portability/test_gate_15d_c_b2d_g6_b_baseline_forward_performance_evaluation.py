from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


RUNNER_PATH = (
    Path(__file__).resolve().parent
    / "run_xauusd_gate_15d_c_b2d_g6_b_baseline_forward_performance_evaluation.py"
)


spec = importlib.util.spec_from_file_location(
    "g6b",
    RUNNER_PATH,
)

assert spec is not None
assert spec.loader is not None

g6b: Any = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(
    g6b
)


def test_01_base_authority_is_g6a_publication() -> None:

    assert (
        g6b.BASE_AUTHORITY_COMMIT
        ==
        "b6c19f6a9fa652efcd1af566996dc77a32e1c279"
    )


def test_02_contract_fingerprint_is_frozen() -> None:

    assert (
        g6b.EXPECTED_CONTRACT_FINGERPRINT
        ==
        "32d8af41e2e1d128df664c8fc81bcf52a6a2b341f491a05d65179f740460875c"
    )


def test_03_baseline_count_is_exactly_30() -> None:

    assert (
        g6b.EXPECTED_BASELINE_SAMPLE_COUNT
        ==
        30
    )


def test_04_safe_divide_zero_policy() -> None:

    assert (
        g6b.safe_divide(
            1.0,
            0.0,
        )
        ==
        0.0
    )


def test_05_week_start_is_monday_utc() -> None:

    assert (
        g6b.week_start_utc(
            "2026-10-02T01:00:00Z"
        )
        ==
        "2026-09-28T00:00:00Z"
    )


def test_06_perfect_metrics() -> None:

    rows = [
        {
            "logical_observation_id": "a",
            "decision_time_utc": "2026-09-28T01:00:00Z",
            "predicted_class": -1,
            "outcome_class": -1,
            "probabilities": (
                0.9,
                0.05,
                0.05,
            ),
        },
        {
            "logical_observation_id": "b",
            "decision_time_utc": "2026-09-28T02:00:00Z",
            "predicted_class": 0,
            "outcome_class": 0,
            "probabilities": (
                0.05,
                0.9,
                0.05,
            ),
        },
        {
            "logical_observation_id": "c",
            "decision_time_utc": "2026-09-28T03:00:00Z",
            "predicted_class": 1,
            "outcome_class": 1,
            "probabilities": (
                0.05,
                0.05,
                0.9,
            ),
        },
    ]

    result = g6b.evaluate_rows(
        rows
    )

    assert (
        result[
            "exact_class_accuracy"
        ]
        ==
        1.0
    )

    assert (
        result[
            "macro_f1"
        ]
        ==
        1.0
    )

    assert (
        result[
            "balanced_accuracy"
        ]
        ==
        1.0
    )


def test_07_confusion_matrix_orientation() -> None:

    rows = [
        {
            "logical_observation_id": "a",
            "decision_time_utc": "2026-09-28T01:00:00Z",
            "predicted_class": 1,
            "outcome_class": -1,
            "probabilities": (
                0.1,
                0.2,
                0.7,
            ),
        }
    ]

    result = g6b.evaluate_rows(
        rows
    )

    assert (
        result[
            "confusion_matrix"
        ][
            "SHORT"
        ][
            "LONG"
        ]
        ==
        1
    )


def test_08_missing_classes_follow_zero_policy() -> None:

    rows = [
        {
            "logical_observation_id": "a",
            "decision_time_utc": "2026-09-28T01:00:00Z",
            "predicted_class": 1,
            "outcome_class": 1,
            "probabilities": (
                0.1,
                0.1,
                0.8,
            ),
        }
    ]

    result = g6b.evaluate_rows(
        rows
    )

    assert (
        result[
            "per_class"
        ][
            "SHORT"
        ][
            "recall"
        ]
        ==
        0.0
    )

    assert (
        result[
            "per_class"
        ][
            "NO_TRADE"
        ][
            "recall"
        ]
        ==
        0.0
    )


def test_09_brier_score_is_nonnegative() -> None:

    rows = [
        {
            "logical_observation_id": "a",
            "decision_time_utc": "2026-09-28T01:00:00Z",
            "predicted_class": 1,
            "outcome_class": 1,
            "probabilities": (
                0.1,
                0.2,
                0.7,
            ),
        }
    ]

    result = g6b.evaluate_rows(
        rows
    )

    assert (
        result[
            "multiclass_brier_score"
        ]
        >=
        0.0
    )


def test_10_log_loss_is_nonnegative() -> None:

    rows = [
        {
            "logical_observation_id": "a",
            "decision_time_utc": "2026-09-28T01:00:00Z",
            "predicted_class": 1,
            "outcome_class": 1,
            "probabilities": (
                0.1,
                0.2,
                0.7,
            ),
        }
    ]

    result = g6b.evaluate_rows(
        rows
    )

    assert (
        result[
            "multiclass_log_loss"
        ]
        >=
        0.0
    )


def test_11_weekly_cohorts_split_on_monday() -> None:

    rows = [
        {
            "logical_observation_id": "a",
            "decision_time_utc": "2026-10-02T01:00:00Z",
            "predicted_class": 1,
            "outcome_class": 1,
            "probabilities": (
                0.1,
                0.1,
                0.8,
            ),
        },
        {
            "logical_observation_id": "b",
            "decision_time_utc": "2026-10-05T01:00:00Z",
            "predicted_class": 1,
            "outcome_class": 1,
            "probabilities": (
                0.1,
                0.1,
                0.8,
            ),
        },
    ]

    result = (
        g6b.evaluate_weekly_cohorts(
            rows
        )
    )

    assert len(
        result
    ) == 2

    assert (
        result[0][
            "week_start_utc"
        ]
        ==
        "2026-09-28T00:00:00Z"
    )

    assert (
        result[1][
            "week_start_utc"
        ]
        ==
        "2026-10-05T00:00:00Z"
    )


def test_12_g5_hash_match_is_mandatory() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "RUNTIME_LEDGER_NOT_EXACT_G5_BASELINE"
        in text
    )


def test_13_observation_outcome_linkage_is_checked() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "OUTCOME_SOURCE_OBSERVATION_FINGERPRINT_MISMATCH"
        in text
    )

    assert (
        "DECISION_TIME_LINKAGE_MISMATCH"
        in text
    )


def test_14_observation_semantic_fingerprint_is_checked() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "OBSERVATION_SEMANTIC_FINGERPRINT_MISMATCH"
        in text
    )


def test_15_no_pnl_or_execution_authority() -> None:

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


def test_16_no_training_or_tuning() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        '"retraining_performed": False'
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


def test_17_no_mt5_access() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert "MetaTrader5" not in text
    assert "order_send(" not in text
    assert "order_check(" not in text


def test_18_no_pass_fail_verdict() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        '"pass_fail_threshold_defined": False'
        in text
    )

    assert (
        '"production_promotion_decision_authorized": False'
        in text
    )


def test_19_ledgers_must_remain_unchanged() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "RUNTIME_LEDGER_CHANGED_DURING_EVALUATION"
        in text
    )

    assert (
        '"ledger_write_performed": False'
        in text
    )