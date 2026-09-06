from __future__ import annotations

import importlib

fetcher_module = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
)

trend_module = importlib.import_module(
    "02_AI.Features.trend_features"
)

fetcher = fetcher_module.fetcher

trend = trend_module.trend


def test_trend():

    df = fetcher.fetch(bars=500)

    df = trend.generate(df)

    assert "ema20" in df.columns
    assert "ema50" in df.columns
    assert "ema200" in df.columns
    assert "trend_strength" in df.columns