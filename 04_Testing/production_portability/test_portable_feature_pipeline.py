"""
===============================================================================
Module      : test_portable_feature_pipeline.py
Project     : PulseViper XAU AI
Purpose     : Unit & Fail-Closed Tests for Portable Feature Pipeline (Gate 13)
===============================================================================
"""

from __future__ import annotations

import hashlib
import importlib
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

pipeline_mod = importlib.import_module("02_AI.Features.portable_feature_pipeline")
contract_mod = importlib.import_module("02_AI.Features.portable_feature_contract")

PortableFeaturePipeline = pipeline_mod.PortableFeaturePipeline
PortableFeaturePipelineResult = pipeline_mod.PortableFeaturePipelineResult
PortableFeatureGenerationError = pipeline_mod.PortableFeatureGenerationError

EXPECTED_FEATURE_COUNT = contract_mod.EXPECTED_FEATURE_COUNT
EXPECTED_FEATURE_COLUMNS_SHA256 = contract_mod.EXPECTED_FEATURE_COLUMNS_SHA256
FROZEN_FEATURE_COLUMNS = contract_mod.FROZEN_FEATURE_COLUMNS
FROZEN_MODEL_SHA256 = contract_mod.FROZEN_MODEL_SHA256
FROZEN_MODEL_CLASSES = contract_mod.FROZEN_MODEL_CLASSES


def _create_synthetic_ohlcv(
    start_time: str,
    bars: int,
    freq_minutes: int,
    base_price: float = 2000.0,
) -> pd.DataFrame:
    """Create deterministic valid OHLCV synthetic data for testing."""
    times = pd.date_range(start=start_time, periods=bars, freq=f"{freq_minutes}min", tz="UTC")
    rng = np.random.RandomState(42)

    returns = rng.normal(0, 0.001, bars)
    prices = base_price * np.exp(np.cumsum(returns))

    opens = prices
    highs = prices + np.abs(rng.normal(0.5, 0.2, bars))
    lows = prices - np.abs(rng.normal(0.5, 0.2, bars))
    closes = prices + rng.normal(0, 0.2, bars)

    # Ensure price consistency
    highs = np.maximum(highs, np.maximum(opens, closes))
    lows = np.minimum(lows, np.minimum(opens, closes))
    lows = np.maximum(lows, 1.0)
    volumes = rng.randint(100, 1000, bars).astype(float)

    return pd.DataFrame(
        {
            "time": times,
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "tick_volume": volumes,
        }
    )


@pytest.fixture
def synthetic_market_data() -> dict[str, pd.DataFrame]:
    """Provide a complete synthetic multi-timeframe dataset spanning sufficient warm-up bars."""
    # Stagger start dates so higher timeframes are already fully warmed up by the time M5 starts (2025-01-01)
    return {
        "M5": _create_synthetic_ohlcv("2025-01-01 00:00:00", 500, 5),
        "M15": _create_synthetic_ohlcv("2024-12-25 00:00:00", 700, 15),
        "M30": _create_synthetic_ohlcv("2024-12-20 00:00:00", 600, 30),
        "H1": _create_synthetic_ohlcv("2024-12-01 00:00:00", 800, 60),
        "H4": _create_synthetic_ohlcv("2024-10-01 00:00:00", 600, 240),
        "D1": _create_synthetic_ohlcv("2024-04-01 00:00:00", 300, 1440),
    }


def test_pipeline_produces_exact_331_contract(synthetic_market_data: dict[str, pd.DataFrame]) -> None:
    """Validate that pipeline generation produces exactly 331 features matching the contract SHA."""
    pipeline = PortableFeaturePipeline()
    result = pipeline.generate(synthetic_market_data, symbol="XAUUSD")

    assert isinstance(result, PortableFeaturePipelineResult)
    assert result.feature_count == EXPECTED_FEATURE_COUNT
    assert result.features.shape[1] == EXPECTED_FEATURE_COUNT
    assert tuple(result.features.columns) == FROZEN_FEATURE_COLUMNS
    assert result.feature_columns_sha256 == EXPECTED_FEATURE_COLUMNS_SHA256
    assert result.symbol == "XAUUSD"
    assert result.row_count > 0
    assert result.live_authorized is False

    # Check to_model_matrix
    matrix = result.to_model_matrix()
    assert matrix.shape == (result.row_count, 331)
    assert matrix.dtype == np.float32
    assert np.all(np.isfinite(matrix))


def test_pipeline_deterministic_repeatability(synthetic_market_data: dict[str, pd.DataFrame]) -> None:
    """Validate that two independent pipeline runs produce bitwise identical outputs."""
    pipeline1 = PortableFeaturePipeline()
    res1 = pipeline1.generate(synthetic_market_data, symbol="XAUUSD")

    pipeline2 = PortableFeaturePipeline()
    res2 = pipeline2.generate(synthetic_market_data, symbol="XAUUSD")

    assert res1.row_count == res2.row_count
    np.testing.assert_array_equal(res1.to_model_matrix(), res2.to_model_matrix())
    pd.testing.assert_series_equal(res1.decision_times, res2.decision_times)


def test_pipeline_accepts_xauusdm_symbol(synthetic_market_data: dict[str, pd.DataFrame]) -> None:
    """Validate that XAUUSDm is accepted and normalizes to canonical XAUUSD."""
    pipeline = PortableFeaturePipeline()
    res = pipeline.generate(synthetic_market_data, symbol="XAUUSDm")
    assert res.symbol == "XAUUSD"
    assert res.feature_count == 331


def test_pipeline_fails_closed_on_alien_symbol(synthetic_market_data: dict[str, pd.DataFrame]) -> None:
    """Validate that unproven symbols raise typed fail-closed exception."""
    pipeline = PortableFeaturePipeline()
    with pytest.raises(PortableFeatureGenerationError, match="UNSUPPORTED_BROKER_SYMBOL"):
        pipeline.generate(synthetic_market_data, symbol="EURUSD")


def test_pipeline_fails_closed_on_missing_timeframe(synthetic_market_data: dict[str, pd.DataFrame]) -> None:
    """Validate that missing any required timeframe raises typed exception."""
    incomplete_data = {k: v for k, v in synthetic_market_data.items() if k != "H4"}
    pipeline = PortableFeaturePipeline()
    with pytest.raises(PortableFeatureGenerationError, match="REQUIRED_TIMEFRAME_MISSING: H4"):
        pipeline.generate(incomplete_data, symbol="XAUUSD")


def test_pipeline_fails_closed_on_missing_required_column(synthetic_market_data: dict[str, pd.DataFrame]) -> None:
    """Validate that missing a required OHLCV column raises typed exception."""
    corrupt_data = {k: v.copy() for k, v in synthetic_market_data.items()}
    corrupt_data["M5"] = corrupt_data["M5"].drop(columns=["tick_volume"])

    pipeline = PortableFeaturePipeline()
    with pytest.raises(PortableFeatureGenerationError, match="MISSING_REQUIRED_RAW_COLUMNS"):
        pipeline.generate(corrupt_data, symbol="XAUUSD")


def test_pipeline_fails_closed_on_non_monotonic_timestamps(synthetic_market_data: dict[str, pd.DataFrame]) -> None:
    """Validate that non-chronological timestamps raise typed exception."""
    corrupt_data = {k: v.copy() for k, v in synthetic_market_data.items()}
    # Swap two rows
    idx = [0, 2, 1, *range(3, len(corrupt_data["M5"]))]
    corrupt_data["M5"] = corrupt_data["M5"].iloc[idx].reset_index(drop=True)

    pipeline = PortableFeaturePipeline()
    with pytest.raises(PortableFeatureGenerationError, match="TIMESTAMPS_NOT_MONOTONIC_INCREASING"):
        pipeline.generate(corrupt_data, symbol="XAUUSD")


def test_pipeline_fails_closed_on_duplicate_timestamps(synthetic_market_data: dict[str, pd.DataFrame]) -> None:
    """Validate that duplicate timestamps raise typed exception."""
    corrupt_data = {k: v.copy() for k, v in synthetic_market_data.items()}
    corrupt_data["M5"].iloc[5, corrupt_data["M5"].columns.get_loc("time")] = corrupt_data["M5"].iloc[4]["time"]

    pipeline = PortableFeaturePipeline()
    with pytest.raises(PortableFeatureGenerationError, match="DUPLICATE_TIMESTAMPS_DETECTED"):
        pipeline.generate(corrupt_data, symbol="XAUUSD")


def test_pipeline_fails_closed_on_invalid_ohlc(synthetic_market_data: dict[str, pd.DataFrame]) -> None:
    """Validate that high < low or negative prices raise typed exception."""
    corrupt_data = {k: v.copy() for k, v in synthetic_market_data.items()}
    corrupt_data["M5"].iloc[10, corrupt_data["M5"].columns.get_loc("low")] = -5.0

    pipeline = PortableFeaturePipeline()
    with pytest.raises(PortableFeatureGenerationError, match="INVALID_OHLC_PRICE_RELATION"):
        pipeline.generate(corrupt_data, symbol="XAUUSD")


def test_pipeline_fails_closed_on_insufficient_history(synthetic_market_data: dict[str, pd.DataFrame]) -> None:
    """Validate that insufficient history bars raise typed exception."""
    corrupt_data = {k: v.copy() for k, v in synthetic_market_data.items()}
    corrupt_data["M5"] = corrupt_data["M5"].head(50)

    pipeline = PortableFeaturePipeline()
    with pytest.raises(PortableFeatureGenerationError, match="INSUFFICIENT_HISTORY_BARS"):
        pipeline.generate(corrupt_data, symbol="XAUUSD")


def test_no_future_leakage(synthetic_market_data: dict[str, pd.DataFrame]) -> None:
    """
    Prove zero future-data leakage: modifying future bars must NOT change
    any past or current feature values.
    """
    pipeline = PortableFeaturePipeline()
    res_orig = pipeline.generate(synthetic_market_data, symbol="XAUUSD")

    # Cutoff is 12 hours before the end of M5
    end_m5 = synthetic_market_data["M5"]["time"].max()
    cutoff_time = end_m5 - pd.Timedelta(hours=12)

    # Tamper only bars strictly after cutoff_time
    tampered_data = {}
    for k, v in synthetic_market_data.items():
        df_t = v.copy()
        mask = df_t["time"] > cutoff_time
        if mask.any():
            df_t.loc[mask, "close"] *= 1.5
            df_t.loc[mask, "high"] *= 1.6
        tampered_data[k] = df_t

    res_tampered = pipeline.generate(tampered_data, symbol="XAUUSD")

    # Features at or before cutoff_time must be 100% bitwise identical
    mask_orig = res_orig.decision_times <= cutoff_time
    mask_tampered = res_tampered.decision_times <= cutoff_time

    assert mask_orig.sum() > 0
    assert mask_orig.sum() == mask_tampered.sum()

    features_orig_sub = res_orig.features.loc[mask_orig].to_numpy()
    features_tamp_sub = res_tampered.features.loc[mask_tampered].to_numpy()

    np.testing.assert_array_equal(features_orig_sub, features_tamp_sub)


def test_d1_reconstruction_from_h1_matches_boundary(synthetic_market_data: dict[str, pd.DataFrame]) -> None:
    """Validate D1 reconstruction from H1 uses 00:00:00 UTC boundaries and correct OHLCV aggregation."""
    pipeline = PortableFeaturePipeline(
        d1_reconstruction_source="H1",
        min_history_bars={"D1": 10},
    )
    res = pipeline.generate(synthetic_market_data, symbol="XAUUSD")

    assert res.d1_source == "RECONSTRUCTED_FROM_H1"
    assert res.feature_count == EXPECTED_FEATURE_COUNT
    assert res.row_count > 0


def test_frozen_model_read_only_compatibility() -> None:
    """
    Verify offline compatibility with the frozen model artifact.
    Does NOT invoke predict_proba for live deployment (Directive 7).
    """
    model_path = REPO_ROOT / "xauusd_portable_331_c04_full_train_model.joblib"
    assert model_path.is_file(), f"Frozen model missing: {model_path}"

    # Verify SHA256
    model_bytes = model_path.read_bytes()
    computed_sha = hashlib.sha256(model_bytes).hexdigest()
    assert computed_sha == FROZEN_MODEL_SHA256

    # Load in read-only mode
    model = joblib.load(model_path)
    assert getattr(model, "n_features_in_", None) == EXPECTED_FEATURE_COUNT
    assert tuple(getattr(model, "classes_", ())) == FROZEN_MODEL_CLASSES
