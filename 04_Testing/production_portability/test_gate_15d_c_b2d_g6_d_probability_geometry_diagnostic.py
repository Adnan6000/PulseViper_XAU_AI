from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


RUNNER_PATH = (
    Path(__file__).resolve().parent
    / "run_xauusd_gate_15d_c_b2d_g6_d_probability_geometry_diagnostic.py"
)


spec = importlib.util.spec_from_file_location(
    "g6d",
    RUNNER_PATH,
)

assert spec is not None
assert spec.loader is not None

g6d: Any = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(
    g6d
)


def synthetic_row(
    *,
    predicted: int,
    outcome: int,
    short: float,
    no_trade: float,
    long: float,
) -> dict[str, Any]:

    probabilities = {
        -1: short,
        0: no_trade,
        1: long,
    }

    ranked = sorted(
        probabilities.items(),
        key=lambda item: (
            item[1],
            item[0],
        ),
        reverse=True,
    )

    winner = float(
        ranked[0][1]
    )

    runner_up = float(
        ranked[1][1]
    )

    import math

    entropy = 0.0

    for probability in probabilities.values():

        if probability > 0.0:
            entropy -= (
                probability
                *
                math.log(
                    probability
                )
            )

    uniform = (
        1.0
        /
        3.0
    )

    return {
        "logical_observation_id": "x",
        "decision_time_utc": "2026-10-01T00:00:00Z",
        "predicted_class": predicted,
        "outcome_class": outcome,
        "probability_short": short,
        "probability_no_trade": no_trade,
        "probability_long": long,
        "rank_1_class": int(
            ranked[0][0]
        ),
        "rank_2_class": int(
            ranked[1][0]
        ),
        "rank_3_class": int(
            ranked[2][0]
        ),
        "winner_probability": winner,
        "runner_up_probability": runner_up,
        "confidence_margin": (
            winner
            -
            runner_up
        ),
        "entropy": entropy,
        "normalized_entropy": (
            entropy
            /
            math.log(
                3.0
            )
        ),
        "l1_uniform_distance": sum(
            abs(
                value
                -
                uniform
            )
            for value
            in probabilities.values()
        ),
        "l2_uniform_distance": math.sqrt(
            sum(
                (
                    value
                    -
                    uniform
                )
                ** 2
                for value
                in probabilities.values()
            )
        ),
        "correct": (
            predicted
            ==
            outcome
        ),
    }


def test_01_base_authority_is_g6c_publication() -> None:

    assert (
        g6d.BASE_AUTHORITY_COMMIT
        ==
        "78d1b094700a7635c75851492d33340b64894351"
    )


def test_02_sample_count_is_30() -> None:

    assert (
        g6d.EXPECTED_SAMPLE_COUNT
        ==
        30
    )


def test_03_uniform_probability_is_one_third() -> None:

    assert abs(
        g6d.UNIFORM_PROBABILITY
        -
        (
            1.0
            /
            3.0
        )
    ) < 1e-15


def test_04_mean_empty_is_zero() -> None:

    assert (
        g6d.mean(
            []
        )
        ==
        0.0
    )


def test_05_median_empty_is_zero() -> None:

    assert (
        g6d.median(
            []
        )
        ==
        0.0
    )


def test_06_uniform_vector_has_max_entropy() -> None:

    row = synthetic_row(
        predicted=1,
        outcome=1,
        short=1.0 / 3.0,
        no_trade=1.0 / 3.0,
        long=1.0 / 3.0,
    )

    assert abs(
        row[
            "normalized_entropy"
        ]
        -
        1.0
    ) < 1e-12

    assert abs(
        row[
            "l2_uniform_distance"
        ]
    ) < 1e-12


def test_07_rank_frequency_counts_argmax() -> None:

    rows = [
        synthetic_row(
            predicted=1,
            outcome=1,
            short=0.2,
            no_trade=0.3,
            long=0.5,
        )
        for _ in range(
            30
        )
    ]

    result = g6d.rank_frequency(
        rows
    )

    assert (
        result[
            "rank_1"
        ][
            "LONG"
        ]
        ==
        30
    )


def test_08_probability_summary() -> None:

    rows = [
        synthetic_row(
            predicted=1,
            outcome=1,
            short=0.2,
            no_trade=0.3,
            long=0.5,
        )
        for _ in range(
            30
        )
    ]

    result = (
        g6d.summarize_probability_vector(
            rows
        )
    )

    assert (
        result[
            "LONG"
        ][
            "mean"
        ]
        ==
        0.5
    )


def test_09_summary_by_true_outcome() -> None:

    rows = [
        synthetic_row(
            predicted=1,
            outcome=-1,
            short=0.3,
            no_trade=0.3,
            long=0.4,
        )
        for _ in range(
            30
        )
    ]

    result = g6d.summarize_by_outcome(
        rows
    )

    assert (
        result[
            "SHORT"
        ][
            "sample_count"
        ]
        ==
        30
    )


def test_10_summary_by_prediction() -> None:

    rows = [
        synthetic_row(
            predicted=1,
            outcome=0,
            short=0.3,
            no_trade=0.3,
            long=0.4,
        )
        for _ in range(
            30
        )
    ]

    result = g6d.summarize_by_prediction(
        rows
    )

    assert (
        result[
            "LONG"
        ][
            "sample_count"
        ]
        ==
        30
    )


def test_11_diagnostic_requires_30_rows() -> None:

    rows = [
        synthetic_row(
            predicted=1,
            outcome=1,
            short=0.2,
            no_trade=0.3,
            long=0.5,
        )
    ]

    try:

        g6d.diagnostic_summary(
            rows
        )

    except g6d.G6DDiagnosticError as exc:

        assert (
            "UNEXPECTED_DIAGNOSTIC_SAMPLE_COUNT"
            in str(
                exc
            )
        )

    else:

        raise AssertionError(
            "Expected diagnostic to fail"
        )


def test_12_exact_g5_hash_binding_required() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "RUNTIME_LEDGER_NOT_EXACT_G5_BASELINE"
        in text
    )


def test_13_g6c_authority_required() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "G6C_STATUS_NOT_PASS"
        in text
    )

    assert (
        "G6C_MISSED_SHORT_COUNT_MISMATCH"
        in text
    )


def test_14_argmax_consistency_checked() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "ARGMAX_PREDICTION_MISMATCH"
        in text
    )


def test_15_uniform_geometry_is_calculated() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "normalized_entropy"
        in text
    )

    assert (
        "l1_uniform_distance"
        in text
    )

    assert (
        "l2_uniform_distance"
        in text
    )


def test_16_no_training_or_calibration() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        '"probability_calibration_performed": False'
        in text
    )

    assert (
        '"retraining_performed": False'
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


def test_17_no_mt5_or_execution_api() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert "MetaTrader5" not in text
    assert "order_send(" not in text
    assert "order_check(" not in text
    assert "positions_get(" not in text


def test_18_no_pnl_or_live_execution() -> None:

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


def test_20_no_promotion_interpretation() -> None:

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