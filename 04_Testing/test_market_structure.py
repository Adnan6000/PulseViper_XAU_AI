from pathlib import Path
import importlib
import os
import sys

import numpy as np
import pandas as pd
import pytest


# ==========================================================
# Project Root
# ==========================================================

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


# ==========================================================
# Imports
# ==========================================================

market_structure_module = importlib.import_module(
    "02_AI.Core.market_structure"
)

MarketStructure = market_structure_module.MarketStructure
market_structure = market_structure_module.market_structure


# ==========================================================
# Helpers
# ==========================================================

def _make_ohlc(
    rows: int = 20,
) -> pd.DataFrame:

    close = np.linspace(
        100.0,
        101.9,
        rows,
    )

    return pd.DataFrame(
        {
            "open": close - 0.10,
            "high": close + 0.40,
            "low": close - 0.40,
            "close": close,
        }
    )


def _with_atr(
    high: list[float],
    low: list[float],
    atr: list[float],
) -> pd.DataFrame:

    close = [
        (high_value + low_value) / 2.0
        for high_value, low_value
        in zip(high, low)
    ]

    return pd.DataFrame(
        {
            "open": close,
            "high": high,
            "low": low,
            "close": close,
            "atr": atr,
        }
    )


# ==========================================================
# Input Validation
# ==========================================================

@pytest.mark.parametrize(
    "missing_column",
    [
        "open",
        "high",
        "low",
        "close",
    ],
)
def test_missing_required_column_raises_value_error(
    missing_column: str,
) -> None:

    engine = MarketStructure()

    df = _make_ohlc().drop(
        columns=[missing_column]
    )

    with pytest.raises(
        ValueError,
        match="Missing required columns",
    ):
        engine.generate(df)


# ==========================================================
# Output Contract
# ==========================================================

def test_generate_exposes_market_structure_contract() -> None:

    engine = MarketStructure(
        pivot_window=2,
    )

    result = engine.generate(
        _make_ohlc(30)
    )

    expected_columns = {
        "atr",
        "pivot_high",
        "pivot_low",
        "pivot_strength",
        "major_high",
        "major_low",
        "minor_high",
        "minor_low",
        "major_swing",
        "swing_score",
        "swing_id",
        "swing_type",
        "swing_price",
        "HH",
        "HL",
        "LH",
        "LL",
        "structure",
        "last_major_high",
        "last_major_low",
        "structure_bias",
    }

    assert expected_columns.issubset(
        result.columns
    )


# ==========================================================
# Short Dataset
# ==========================================================

def test_short_dataset_returns_no_pivots() -> None:

    engine = MarketStructure(
        pivot_window=3,
    )

    result = engine.generate(
        _make_ohlc(6)
    )

    assert result["pivot_high"].sum() == 0
    assert result["pivot_low"].sum() == 0


# ==========================================================
# Pivot High
# ==========================================================

def test_detects_deterministic_pivot_high() -> None:

    engine = MarketStructure(
        pivot_window=1,
    )

    df = _with_atr(
        high=[
            10.0,
            12.0,
            10.0,
        ],
        low=[
            9.0,
            9.5,
            9.0,
        ],
        atr=[
            1.0,
            1.0,
            1.0,
        ],
    )

    result = engine.detect_pivots(df)

    assert result.loc[1, "pivot_high"] == 1
    assert result.loc[1, "pivot_low"] == 0

    assert (
        result.loc[1, "pivot_strength"]
        == pytest.approx(2.0)
    )


# ==========================================================
# Pivot Low
# ==========================================================

def test_detects_deterministic_pivot_low() -> None:

    engine = MarketStructure(
        pivot_window=1,
    )

    df = _with_atr(
        high=[
            10.0,
            9.5,
            10.0,
        ],
        low=[
            9.0,
            6.0,
            9.0,
        ],
        atr=[
            1.0,
            1.0,
            1.0,
        ],
    )

    result = engine.detect_pivots(df)

    assert result.loc[1, "pivot_high"] == 0
    assert result.loc[1, "pivot_low"] == 1

    assert (
        result.loc[1, "pivot_strength"]
        == pytest.approx(3.0)
    )


# ==========================================================
# Double Pivot Reproduction
# ==========================================================

def test_double_pivot_is_reproducible() -> None:

    engine = MarketStructure(
        pivot_window=1,
    )

    df = _with_atr(
        high=[
            9.0,
            12.0,
            10.0,
        ],
        low=[
            8.0,
            5.0,
            7.0,
        ],
        atr=[
            1.0,
            1.0,
            1.0,
        ],
    )

    result = engine.detect_pivots(df)

    assert result.loc[1, "pivot_high"] == 1
    assert result.loc[1, "pivot_low"] == 1

    # Important:
    # This test only proves that double pivots can exist.
    # Final HIGH/LOW representation policy is NOT changed yet.


# ==========================================================
# Weak Pivot
# ==========================================================

def test_weak_pivot_does_not_become_structural_swing() -> None:

    engine = MarketStructure(
        pivot_window=1,
        min_strength=1.20,
        major_strength=2.50,
    )

    df = _with_atr(
        high=[
            10.0,
            10.5,
            10.0,
        ],
        low=[
            9.0,
            9.2,
            9.1,
        ],
        atr=[
            1.0,
            1.0,
            1.0,
        ],
    )

    pivots = engine.detect_pivots(df)

    result = engine.classify_swings(
        pivots
    )

    assert result.loc[1, "pivot_high"] == 1

    assert (
        result.loc[1, "pivot_strength"]
        < engine.min_strength
    )

    assert result.loc[1, "swing_id"] == 0

    assert (
        result.loc[1, "swing_type"]
        == "NONE"
    )

    assert result.loc[1, "swing_score"] == 0.0

    assert result.loc[1, "major_high"] == 0
    assert result.loc[1, "minor_high"] == 0


# ==========================================================
# Minor / Major Boundaries
# ==========================================================

def test_minor_and_major_strength_boundaries() -> None:

    engine = MarketStructure(
        min_strength=1.20,
        major_strength=2.50,
    )

    df = pd.DataFrame(
        {
            "high": [
                100.0,
                101.0,
                102.0,
                103.0,
            ],
            "low": [
                90.0,
                91.0,
                92.0,
                93.0,
            ],
            "pivot_high": [
                1,
                1,
                0,
                0,
            ],
            "pivot_low": [
                0,
                0,
                1,
                1,
            ],
            "pivot_strength": [
                1.20,
                2.499,
                2.50,
                1.20,
            ],
        }
    )

    result = engine.classify_swings(df)

    # 1.20 = minor
    assert result.loc[0, "minor_high"] == 1
    assert result.loc[0, "major_high"] == 0

    # Below 2.50 = still minor
    assert result.loc[1, "minor_high"] == 1
    assert result.loc[1, "major_high"] == 0

    # 2.50 = major
    assert result.loc[2, "major_low"] == 1
    assert result.loc[2, "minor_low"] == 0

    # 1.20 = minor
    assert result.loc[3, "minor_low"] == 1
    assert result.loc[3, "major_low"] == 0


# ==========================================================
# Swing IDs
# ==========================================================

def test_swing_ids_are_reserved_for_valid_swings() -> None:

    engine = MarketStructure(
        min_strength=1.20,
        major_strength=2.50,
    )

    df = pd.DataFrame(
        {
            "high": [
                100.0,
                101.0,
                102.0,
            ],
            "low": [
                90.0,
                91.0,
                92.0,
            ],
            "pivot_high": [
                1,
                0,
                1,
            ],
            "pivot_low": [
                0,
                1,
                0,
            ],
            "pivot_strength": [
                0.40,
                1.20,
                2.50,
            ],
        }
    )

    result = engine.classify_swings(df)

    assert result["swing_id"].tolist() == [
        0,
        1,
        2,
    ]

    assert result["swing_type"].tolist() == [
        "NONE",
        "LOW",
        "HIGH",
    ]


# ==========================================================
# HH / HL / LH / LL
# ==========================================================

def test_structure_classification_hh_hl_lh_ll() -> None:

    engine = MarketStructure()

    df = pd.DataFrame(
        {
            "high": [
                100.0,
                101.0,
                110.0,
                108.0,
                105.0,
                103.0,
            ],
            "low": [
                95.0,
                90.0,
                100.0,
                95.0,
                97.0,
                85.0,
            ],
            "major_high": [
                1,
                0,
                1,
                0,
                1,
                0,
            ],
            "major_low": [
                0,
                1,
                0,
                1,
                0,
                1,
            ],
        }
    )

    result = engine.detect_structure(df)

    assert result.loc[2, "HH"] == 1
    assert result.loc[2, "structure"] == "HH"

    assert result.loc[3, "HL"] == 1
    assert result.loc[3, "structure"] == "HL"

    assert result.loc[4, "LH"] == 1
    assert result.loc[4, "structure"] == "LH"

    assert result.loc[5, "LL"] == 1
    assert result.loc[5, "structure"] == "LL"


# ==========================================================
# Last Major State
# ==========================================================

def test_last_major_high_and_low_persist_until_replaced() -> None:

    engine = MarketStructure()

    df = pd.DataFrame(
        {
            "high": [
                100.0,
                101.0,
                110.0,
                108.0,
                105.0,
                103.0,
            ],
            "low": [
                95.0,
                90.0,
                100.0,
                95.0,
                97.0,
                85.0,
            ],
            "major_high": [
                1,
                0,
                1,
                0,
                1,
                0,
            ],
            "major_low": [
                0,
                1,
                0,
                1,
                0,
                1,
            ],
        }
    )

    result = engine.detect_structure(df)

    assert (
        result.loc[0, "last_major_high"]
        == pytest.approx(100.0)
    )

    assert (
        result.loc[1, "last_major_high"]
        == pytest.approx(100.0)
    )

    assert (
        result.loc[2, "last_major_high"]
        == pytest.approx(110.0)
    )

    assert (
        result.loc[3, "last_major_high"]
        == pytest.approx(110.0)
    )

    assert (
        result.loc[4, "last_major_high"]
        == pytest.approx(105.0)
    )

    assert np.isnan(
        result.loc[0, "last_major_low"]
    )

    assert (
        result.loc[1, "last_major_low"]
        == pytest.approx(90.0)
    )

    assert (
        result.loc[2, "last_major_low"]
        == pytest.approx(90.0)
    )

    assert (
        result.loc[3, "last_major_low"]
        == pytest.approx(95.0)
    )

    assert (
        result.loc[4, "last_major_low"]
        == pytest.approx(95.0)
    )

    assert (
        result.loc[5, "last_major_low"]
        == pytest.approx(85.0)
    )


# ==========================================================
# Persistent Structure Bias
# ==========================================================

def test_structure_bias_persists_between_structure_events() -> None:

    engine = MarketStructure()

    df = pd.DataFrame(
        {
            "structure": [
                "NONE",
                "HH",
                "NONE",
                "HL",
                "NONE",
                "LH",
                "NONE",
                "LL",
                "NONE",
            ]
        }
    )

    result = engine.add_structure_state(
        df
    )

    assert result["structure_bias"].tolist() == [
        "NEUTRAL",
        "BULLISH",
        "BULLISH",
        "BULLISH",
        "BULLISH",
        "BEARISH",
        "BEARISH",
        "BEARISH",
        "BEARISH",
    ]


# ==========================================================
# Invalid ATR
# ==========================================================

@pytest.mark.parametrize(
    "bad_atr",
    [
        0.0,
        -1.0,
        np.nan,
    ],
)
def test_invalid_atr_does_not_create_artificial_strength(
    bad_atr: float,
) -> None:

    engine = MarketStructure(
        pivot_window=1,
        min_strength=1.20,
        major_strength=2.50,
    )

    df = _with_atr(
        high=[
            10.0,
            12.0,
            10.0,
        ],
        low=[
            9.0,
            9.5,
            9.0,
        ],
        atr=[
            1.0,
            bad_atr,
            1.0,
        ],
    )

    pivots = engine.detect_pivots(df)

    result = engine.classify_swings(
        pivots
    )

    # Geometry can still identify the pivot.
    assert result.loc[1, "pivot_high"] == 1

    # Invalid ATR must not manufacture huge strength.
    assert result.loc[1, "pivot_strength"] == 0.0

    # Therefore it must not become a structural swing.
    assert result.loc[1, "swing_id"] == 0
    assert result.loc[1, "major_high"] == 0
    assert result.loc[1, "minor_high"] == 0


# ==========================================================
# Pivot Confirmation / Look-Ahead Contract
# ==========================================================

def test_pivot_requires_right_side_confirmation_window() -> None:

    engine = MarketStructure(
        pivot_window=2,
    )

    full = _with_atr(
        high=[
            10.0,
            11.0,
            15.0,
            12.0,
            11.0,
        ],
        low=[
            9.0,
            9.5,
            10.0,
            9.8,
            9.7,
        ],
        atr=[
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
        ],
    )

    before_confirmation = engine.detect_pivots(
        full.iloc[:4].copy()
    )

    after_confirmation = engine.detect_pivots(
        full.copy()
    )

    # Pivot cannot be confirmed until the required
    # right-side candles exist.
    assert (
        before_confirmation.loc[
            2,
            "pivot_high",
        ]
        == 0
    )

    assert (
        after_confirmation.loc[
            2,
            "pivot_high",
        ]
        == 1
    )


# ==========================================================
# Real XAUUSD / MT5 Integration Smoke Test
# ==========================================================

@pytest.mark.skipif(
    os.getenv(
        "RUN_MT5_INTEGRATION",
        "0",
    )
    != "1",
    reason=(
        "Set RUN_MT5_INTEGRATION=1 "
        "to run live MT5/XAUUSDm test."
    ),
)
def test_market_structure_real_xauusd_smoke() -> None:

    fetcher = importlib.import_module(
        "02_AI.Dataset.data_fetcher"
    ).fetcher

    df = fetcher.fetch(
        bars=5000
    )

    assert df is not None
    assert not df.empty

    result = market_structure.generate(
        df
    )

    assert result["pivot_high"].sum() > 0
    assert result["pivot_low"].sum() > 0

    assert "structure_bias" in result.columns
    assert "last_major_high" in result.columns
    assert "last_major_low" in result.columns