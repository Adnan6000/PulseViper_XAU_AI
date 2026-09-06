from __future__ import annotations

import importlib

fetcher = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
).fetcher

feature_generator = importlib.import_module(
    "02_AI.Features.feature_generator"
).feature_generator


def test_feature_generator():

    df = fetcher.fetch(bars=1000)

    df = feature_generator.generate(df)

    assert "ema20" in df.columns
    assert "ema50" in df.columns
    assert "ema200" in df.columns
    assert "trend_strength" in df.columns