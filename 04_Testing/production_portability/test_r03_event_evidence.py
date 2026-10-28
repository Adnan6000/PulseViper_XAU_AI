
from __future__ import annotations

import importlib

import numpy as np
import pandas as pd
import pytest

module = importlib.import_module(
    "02_AI.MarketIntelligence.r03_event_evidence"
)


def history(n: int = 220) -> pd.DataFrame:
    closes = (
        4000
        + np.arange(n) * 0.03
        + np.sin(np.arange(n) / 8)
    )

    return pd.DataFrame({
        "time": pd.date_range(
            "2026-10-20T00:00:00Z",
            periods=n,
            freq="5min",
        ),
        "open": closes - 0.1,
        "high": closes + 0.5,
        "low": closes - 0.5,
        "close": closes,
        "tick_volume": np.full(n, 100),
    })


def fake_discovery(frame: pd.DataFrame) -> dict:
    # The fake detector makes repeated consecutive
    # lower-zone signals. Their event horizons
    # must collapse to fewer independent events.
    timestamp = pd.Timestamp(
        frame["time"].iloc[-1]
    )
    start = pd.Timestamp(
        "2026-10-20T00:00:00Z"
    )
    assert isinstance(timestamp, pd.Timestamp)
    assert isinstance(start, pd.Timestamp)

    index = int(
        (timestamp.value - start.value)
        // 300_000_000_000
    )

    active = (
        65 <= index <= 72
        or 100 <= index <= 104
        or 145 <= index <= 147
    )

    return {
        "atr14_price_units": 1.0,
        "candidate_hypotheses": (
            [{"id": "LOWER_ZONE_DEFENSE"}]
            if active else []
        ),
        "failed_break_above": False,
        "failed_break_below": False,
    }


def test_repeated_signals_become_events(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        module.brain,
        "analyze_m5",
        fake_discovery,
    )

    report = module.evaluate_events(history())
    result = report["hypotheses"]["LOWER_ZONE_DEFENSE"]

    assert result["raw_candidate_decisions"] == 16
    assert (
        result["non_overlapping_events"]["count"]
        == 3
    )
    assert result["predictive_edge_established"] is False


def test_paired_math_and_nonoverlap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        module.brain,
        "analyze_m5",
        fake_discovery,
    )

    report = module.evaluate_events(history())
    result = report["hypotheses"]["LOWER_ZONE_DEFENSE"]

    pairs = result["example_pairs"]
    assert len(pairs) == result["matched_pair_count"]

    event_indices = [
        p["event_index"] for p in pairs
    ]
    control_indices = [
        p["control_index"] for p in pairs
    ]

    for a in control_indices:
        assert all(
            abs(a - b) >= 12
            for b in event_indices
        )

    for j, a in enumerate(control_indices):
        assert all(
            abs(a - b) >= 12
            for b in control_indices[j + 1:]
        )

    assert result[
        "paired_event_statistics"
    ]["count"] == result["matched_pair_count"]

    assert result[
        "paired_control_statistics"
    ]["count"] == result["matched_pair_count"]

    if pairs:
        expected = float(np.mean([
            p["difference_atr"]
            for p in pairs
        ]))
        measured = result[
            "paired_difference_statistics"
        ]["mean_atr_return"]
        assert measured == pytest.approx(
            expected, abs=1e-6
        )


def test_no_signal_no_edge() -> None:
    report = module.evaluate_events(history())

    for item in report["hypotheses"].values():
        assert item["independently_validated"] is False
        assert item["predictive_edge_established"] is False

    assert report["ledger_written"] is False
    assert report["orders_sent"] is False


def test_bad_history_blocked() -> None:
    data = history()
    data.loc[0, "high"] = -1.0

    with pytest.raises(
        module.validator.ValidationError,
        match="NONPOSITIVE_PRICE",
    ):
        module.evaluate_events(data)
