from __future__ import annotations

import importlib

import numpy as np
import pandas as pd
import pytest


v = importlib.import_module(
    "04_Testing.production_portability."
    "r03_market_discovery_validation"
)


def history(n: int = 130) -> pd.DataFrame:
    times = pd.date_range(
        "2026-10-20T00:00:00Z",
        periods=n,
        freq="5min",
    )
    close = 4000.0 + np.linspace(0, 8, n)

    return pd.DataFrame({
        "time": times,
        "open": close - 0.1,
        "high": close + 0.5,
        "low": close - 0.5,
        "close": close,
        "tick_volume": np.full(n, 100),
    })


def test_full_walk_forward() -> None:
    report = v.validate_history(history())
    assert report["evaluated_decisions"] == 59
    assert report["future_horizon_bars"] == 12
    assert report["execution_authorized"] is False
    assert report["v2_prospective_outcomes_written"] is False


def test_future_changes_cannot_change_past_detection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = []
    original = v.brain.analyze_m5

    def inspect(frame):
        seen.append(frame["time"].max())
        return original(frame)

    monkeypatch.setattr(v.brain, "analyze_m5", inspect)
    v.validate_history(history(73))

    assert len(seen) == 2
    assert seen[0] == history(73)["time"].iloc[59]
    assert seen[1] == history(73)["time"].iloc[60]


def test_gap_horizon_skipped() -> None:
    data = history(80)
    data.loc[70:, "time"] += pd.Timedelta(minutes=5)

    report = v.validate_history(data)
    assert report["skipped_due_to_m5_gaps"] > 0


def test_duplicate_time_blocked() -> None:
    data = history()
    data.loc[1, "time"] = data.loc[0, "time"]

    with pytest.raises(
        v.ValidationError,
        match="DUPLICATE_TIME",
    ):
        v.validate_history(data)


def test_insufficient_history_blocked() -> None:
    with pytest.raises(
        v.ValidationError,
        match="INSUFFICIENT_M5_HISTORY",
    ):
        v.validate_history(history(71))


def test_no_false_significance() -> None:
    report = v.validate_history(history())

    for result in report["hypotheses"].values():
        assert result["independently_validated"] is False
        assert result["predictive_edge_established"] is False


def test_invalid_ohlc_blocked() -> None:
    data = history()
    data.loc[3, "high"] = 0.0

    with pytest.raises(
        v.ValidationError,
        match="NONPOSITIVE_PRICE",
    ):
        v.validate_history(data)
