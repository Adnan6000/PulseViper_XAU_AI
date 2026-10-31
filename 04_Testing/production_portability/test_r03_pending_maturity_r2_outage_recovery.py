from __future__ import annotations

import importlib

import pandas as pd
import pytest


_runner = importlib.import_module(
    "04_Testing.production_portability."
    "run_xauusd_r03_pending_maturity_r2_outage_recovery"
)


def test_minimum_window_is_1000() -> None:

    result = (
        _runner.required_m5_history_bars(
            pending_decision_time_utc=(
                "2026-10-06T10:00:00Z"
            ),
            now_utc=(
                "2026-10-06T11:00:00Z"
            ),
        )
    )

    assert result == 1000


def test_long_outage_expands_window() -> None:

    result = (
        _runner.required_m5_history_bars(
            pending_decision_time_utc=(
                "2026-10-01T00:00:00Z"
            ),
            now_utc=(
                "2026-10-05T00:00:00Z"
            ),
        )
    )

    assert result > 1000


def test_window_contains_buffer() -> None:

    decision = pd.Timestamp(
        "2026-10-01T00:00:00Z"
    )

    now = (
        decision
        +
        pd.Timedelta(
            days=5
        )
    )

    result = (
        _runner.required_m5_history_bars(
            pending_decision_time_utc=(
                decision
            ),
            now_utc=now,
        )
    )

    elapsed = (
        (
            now
            -
            (
                decision
                -
                pd.Timedelta(
                    minutes=5
                )
            )
        ).total_seconds()
        /
        300.0
    )

    assert result >= int(elapsed)


def test_future_decision_fails_closed() -> None:

    with pytest.raises(
        _runner.R03OutageRecoveryError,
        match=(
            "CURRENT_TIME_PRECEDES_PENDING_DECISION"
        ),
    ):

        _runner.required_m5_history_bars(
            pending_decision_time_utc=(
                "2026-10-07T00:00:00Z"
            ),
            now_utc=(
                "2026-10-06T00:00:00Z"
            ),
        )


def test_excessive_age_fails_closed() -> None:

    with pytest.raises(
        _runner.R03OutageRecoveryError,
        match=(
            "PENDING_SAMPLE_TOO_OLD_FOR_RECOVERY_WINDOW"
        ),
    ):

        _runner.required_m5_history_bars(
            pending_decision_time_utc=(
                "2026-01-01T00:00:00Z"
            ),
            now_utc=(
                "2026-10-06T00:00:00Z"
            ),
        )


def test_all_authorization_flags_false() -> None:

    assert (
        _runner.PERFORMANCE_EVALUATION_AUTHORIZED
        is False
    )

    assert (
        _runner.PNL_EVALUATION_AUTHORIZED
        is False
    )

    assert (
        _runner.LIVE_AUTHORIZED
        is False
    )

    assert (
        _runner.EXECUTION_AUTHORIZED
        is False
    )