
from __future__ import annotations

import importlib

import numpy as np
import pandas as pd
import pytest

mtf = importlib.import_module(
    "02_AI.MarketIntelligence.r03_mtf_reasoning"
)


def sample_market() -> dict[str, pd.DataFrame]:
    decision = pd.Timestamp("2026-10-28T12:00:00Z")
    market = {}

    for tf in mtf.TIMEFRAMES:
        minutes = mtf.MINUTES[tf]
        period = pd.Timedelta(minutes=minutes)

        # Each final candle closes at decision time.
        # Earlier candles also close before decision.
        opens = [
            decision - period * (20 - i)
            for i in range(20)
        ]

        closes = np.linspace(4000.0, 4007.6, 20)

        market[tf] = pd.DataFrame({
            "time": opens,
            "open": closes - 0.1,
            "high": closes + 0.5,
            "low": closes - 0.5,
            "close": closes,
        })

    return market


def test_all_six_timeframes() -> None:
    result = mtf.analyze_mtf(
        sample_market(),
        "2026-10-28T12:00:00Z",
    )

    assert len(result["timeframes"]) == 5
    assert result["trade_authorized"] is False
    assert result["ledger_written"] is False


def test_forming_h4_cannot_change_report() -> None:
    market = sample_market()
    decision = "2026-10-28T12:00:00Z"

    before = mtf.analyze_mtf(market, decision)

    extra = market["H4"].iloc[[-1]].copy()
    extra["time"] = pd.Timestamp(
        "2026-10-28T12:00:00Z"
    )
    extra["open"] = 4000
    extra["high"] = 9000
    extra["low"] = 1000
    extra["close"] = 8000

    market["H4"] = pd.concat(
        [market["H4"], extra],
        ignore_index=True,
    )

    after = mtf.analyze_mtf(market, decision)

    assert before == after


def test_missing_timeframe_blocks() -> None:
    market = sample_market()
    del market["H4"]

    with pytest.raises(
        mtf.MTFError,
        match="REQUIRED_TIMEFRAME_MISSING",
    ):
        mtf.analyze_mtf(
            market, "2026-10-28T12:00:00Z"
        )


def test_unavailable_htf_history_blocks() -> None:
    market = sample_market()
    market["H1"] = market["H1"].tail(3)

    with pytest.raises(
        mtf.MTFError,
        match="INSUFFICIENT_CLOSED_BARS_H1",
    ):
        mtf.analyze_mtf(
            market, "2026-10-28T12:00:00Z"
        )


def test_duplicate_h1_time_blocks() -> None:
    market = sample_market()
    market["H1"].loc[1, "time"] = (
        market["H1"].loc[0, "time"]
    )

    with pytest.raises(
        mtf.MTFError,
        match="DUPLICATE_TIME_H1",
    ):
        mtf.analyze_mtf(
            market, "2026-10-28T12:00:00Z"
        )
