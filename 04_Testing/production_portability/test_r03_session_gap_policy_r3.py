from __future__ import annotations

import importlib

import pandas as pd
import pytest


policy = importlib.import_module(
    "04_Testing.production_portability."
    "r03_session_gap_policy_r3"
)


DECISION = "2026-10-05T20:35:00Z"


def test_contiguous_12_bars_are_eligible():
    times = pd.date_range(
        DECISION,
        periods=12,
        freq="5min",
    )

    result = policy.assess_session_gap(
        decision_time_utc=DECISION,
        completed_m5_times=times,
    )

    assert result.status == policy.STATUS_ELIGIBLE
    assert result.missing_timestamps_utc == ()
    assert result.outcome_maturation_authorized is False


def test_actual_october_5_session_gap():
    first_session = pd.date_range(
        "2026-10-05T20:35:00Z",
        periods=5,
        freq="5min",
    )

    second_session = pd.date_range(
        "2026-10-05T22:00:00Z",
        periods=7,
        freq="5min",
    )

    times = first_session.append(second_session)

    result = policy.assess_session_gap(
        decision_time_utc=DECISION,
        completed_m5_times=times,
    )

    assert result.status == policy.STATUS_GAP
    assert result.available_future_bars == 12
    assert result.actual_last_utc == (
        "2026-10-05T22:30:00+00:00"
    )
    assert len(result.missing_timestamps_utc) == 7
    assert result.terminal_disposition_authorized is False


def test_insufficient_future_bars():
    times = pd.date_range(
        DECISION,
        periods=4,
        freq="5min",
    )

    result = policy.assess_session_gap(
        decision_time_utc=DECISION,
        completed_m5_times=times,
    )

    assert result.status == policy.STATUS_INSUFFICIENT


def test_duplicate_timestamp_blocked():
    times = pd.DatetimeIndex([
        "2026-10-05T20:35:00Z",
        "2026-10-05T20:35:00Z",
    ])

    with pytest.raises(
        policy.R03SessionGapPolicyError,
        match="DUPLICATE_M5_TIMESTAMP",
    ):
        policy.assess_session_gap(
            decision_time_utc=DECISION,
            completed_m5_times=times,
        )


def test_unsorted_history_blocked():
    times = pd.DatetimeIndex([
        "2026-10-05T20:40:00Z",
        "2026-10-05T20:35:00Z",
    ])

    with pytest.raises(
        policy.R03SessionGapPolicyError,
        match="UNSORTED_M5_HISTORY",
    ):
        policy.assess_session_gap(
            decision_time_utc=DECISION,
            completed_m5_times=times,
        )


def test_no_trading_or_disposition_authorization():
    times = pd.date_range(
        DECISION,
        periods=12,
        freq="5min",
    )

    result = policy.assess_session_gap(
        decision_time_utc=DECISION,
        completed_m5_times=times,
    )

    document = result.to_dict()

    assert document["outcome_maturation_authorized"] is False
    assert document["terminal_disposition_authorized"] is False
    assert document["live_authorized"] is False
    assert document["execution_authorized"] is False