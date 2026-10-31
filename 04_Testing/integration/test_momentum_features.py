from __future__ import annotations

import importlib

fetcher = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
).fetcher

momentum = importlib.import_module(
    "02_AI.Features.momentum_features"
).momentum


def test_momentum():

    df = fetcher.fetch(bars=500)

    df = momentum.generate(df)

    assert "rsi14" in df.columns
    assert "macd" in df.columns
    assert "macd_signal" in df.columns
    assert "macd_hist" in df.columns
    assert "roc10" in df.columns