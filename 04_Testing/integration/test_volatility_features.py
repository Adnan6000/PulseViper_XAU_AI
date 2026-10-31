from __future__ import annotations

import importlib

fetcher = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
).fetcher

volatility = importlib.import_module(
    "02_AI.Features.volatility_features"
).volatility


def test_volatility():

    df = fetcher.fetch(bars=1000)

    df = volatility.generate(df)

    assert "atr14" in df.columns
    assert "true_range" in df.columns
    assert "rolling_std20" in df.columns
    assert "volatility_ratio" in df.columns