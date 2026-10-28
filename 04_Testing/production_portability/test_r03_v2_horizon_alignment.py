
from __future__ import annotations

import importlib
from collections.abc import Sequence

import pandas as pd


gap = importlib.import_module(
    "04_Testing.production_portability."
    "r03_v2_session_gap_terminal"
)


DECISION = "2026-10-28T12:00:00Z"


def frame(
    timestamps: Sequence[object],
) -> pd.DataFrame:
    return pd.DataFrame({
        "time": timestamps,
    })


def test_future_horizon_starts_after_decision() -> None:
    horizon = gap.expected_horizon(DECISION)

    assert len(horizon) == 12

    assert horizon[0] == pd.Timestamp(
        "2026-10-28T12:05:00Z"
    )

    assert horizon[-1] == pd.Timestamp(
        "2026-10-28T13:00:00Z"
    )

    assert pd.Timestamp(DECISION) not in horizon


def test_complete_12_future_bars() -> None:
    decision = pd.Timestamp(DECISION)
    horizon = gap.expected_horizon(DECISION)

    result = gap.assess_gap(
        decision_time_utc=DECISION,
        completed_m5=frame(
            [decision, *horizon]
        ),
    )

    assert result["status"] == (
        "STRICT_M5_HORIZON_COMPLETE"
    )

    assert result[
        "missing_m5_timestamps_utc"
    ] == []


def test_decision_plus_11_bars_must_wait() -> None:
    decision = pd.Timestamp(DECISION)
    horizon = gap.expected_horizon(DECISION)

    result = gap.assess_gap(
        decision_time_utc=DECISION,
        completed_m5=frame(
            [decision, *horizon[:11]]
        ),
    )

    assert result["status"] == (
        "WAIT_HORIZON_NOT_ELAPSED"
    )

    assert result["horizon_elapsed"] is False


def test_missing_first_future_bar_detected() -> None:
    decision = pd.Timestamp(DECISION)
    horizon = gap.expected_horizon(DECISION)

    result = gap.assess_gap(
        decision_time_utc=DECISION,
        completed_m5=frame(
            [decision, *horizon[1:]]
        ),
    )

    assert result["status"] == (
        "STRICT_M5_GAP_CONFIRMED"
    )

    assert result[
        "missing_m5_timestamps_utc"
    ] == [
        "2026-10-28T12:05:00+00:00"
    ]


def test_missing_last_future_bar_detected() -> None:
    decision = pd.Timestamp(DECISION)
    horizon = gap.expected_horizon(DECISION)

    later = pd.Timestamp(
        "2026-10-28T13:05:00Z"
    )

    result = gap.assess_gap(
        decision_time_utc=DECISION,
        completed_m5=frame(
            [decision, *horizon[:-1], later]
        ),
    )

    assert result["status"] == (
        "STRICT_M5_GAP_CONFIRMED"
    )

    assert result[
        "missing_m5_timestamps_utc"
    ] == [
        "2026-10-28T13:00:00+00:00"
    ]


def test_truncated_history_not_terminal() -> None:
    horizon = gap.expected_horizon(DECISION)

    result = gap.assess_gap(
        decision_time_utc=DECISION,
        completed_m5=frame(
            horizon
        ),
    )

    assert result["status"] == (
        "INSUFFICIENT_HISTORICAL_COVERAGE"
    )

    assert result[
        "missing_m5_timestamps_utc"
    ] == []
