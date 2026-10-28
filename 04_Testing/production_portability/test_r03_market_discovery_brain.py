
from __future__ import annotations

import importlib

import numpy as np
import pandas as pd
import pytest


d = importlib.import_module(
    "04_Testing.production_portability."
    "r03_market_discovery_brain"
)


def candles(
    *,
    count: int = 40,
    volume: bool = True,
) -> pd.DataFrame:
    times = pd.date_range(
        "2026-10-28T10:00:00Z",
        periods=count,
        freq="5min",
    )

    close = np.linspace(
        100.0, 101.0, count
    )

    data = pd.DataFrame({
        "time": times,
        "open": close - 0.05,
        "high": close + 0.15,
        "low": close - 0.15,
        "close": close,
    })

    if volume:
        data["tick_volume"] = 100

    return data


def test_genuine_structure_report() -> None:
    result = d.analyze_m5(candles())

    assert result["completed_bars_analyzed"] == 40
    assert result["volume"]["available"] is True
    assert result["hidden_orders_detected"] is False
    assert result["predictive_edge_established"] is False
    assert result["execution_authorized"] is False


def test_repeated_upper_rejections() -> None:
    data = candles()

    for index in (31, 34, 37):
        data.loc[index, "high"] = 103.0
        data.loc[index, "open"] = 101.1
        data.loc[index, "close"] = 101.0
        data.loc[index, "low"] = 100.8

    result = d.analyze_m5(data)

    assert result["resistance_rejections"] >= 2

    assert any(
        item["id"] == "UPPER_ZONE_REJECTION"
        for item in result["candidate_hypotheses"]
    )


def test_future_bar_cannot_change_past_report() -> None:
    data = candles()
    previous = d.analyze_m5(data)

    future = data.iloc[[-1]].copy()
    future["time"] = (
        data["time"].iloc[-1]
        + pd.Timedelta(minutes=5)
    )
    future["open"] = 101.0
    future["high"] = 120.0
    future["low"] = 99.0
    future["close"] = 119.0

    extended = pd.concat(
        [data, future],
        ignore_index=True,
    )

    # An explicit past-only slice must remain identical.
    restored = d.analyze_m5(
        extended.iloc[:-1].copy()
    )

    assert restored == previous


def test_duplicate_bars_blocked() -> None:
    data = candles()
    data.loc[1, "time"] = data.loc[0, "time"]

    with pytest.raises(
        d.DiscoveryError,
        match="DUPLICATE_M5_TIME",
    ):
        d.analyze_m5(data)


def test_invalid_ohlc_blocks() -> None:
    data = candles()
    data.loc[4, "high"] = 0.0

    with pytest.raises(
        d.DiscoveryError,
        match="NONPOSITIVE_M5_PRICE|INVALID_M5_HIGH",
    ):
        d.analyze_m5(data)


def test_insufficient_history_blocks() -> None:
    with pytest.raises(
        d.DiscoveryError,
        match="INSUFFICIENT_COMPLETED_M5_BARS",
    ):
        d.analyze_m5(candles(count=10))


def test_missing_volume_does_not_invent_cash_flow() -> None:
    result = d.analyze_m5(
        candles(volume=False)
    )

    assert result["volume"]["available"] is False
    assert result["volume"]["cash_flow_measured"] is False
    assert result["volume"]["resting_orders_observed"] is False


def test_no_model_or_ledger_writes() -> None:
    result = d.analyze_m5(candles())

    assert result["v2_observation_written"] is False
    assert result["outcome_written"] is False
    assert result["live_authorized"] is False
    assert result["execution_authorized"] is False


def test_unfinished_candle_not_accepted_as_proof() -> None:
    # A caller can only guarantee completion by
    # using the authorized completed-bar snapshot.
    # The standalone analyzer itself cannot prove
    # whether a bar is still forming.
    assert (
        d.analyze_m5(candles())[
            "predictive_edge_established"
        ] is False
    )
