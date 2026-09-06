"""
===============================================================================
Module      : portable_feature_contract.py
Project     : PulseViper XAU AI
Purpose     : Immutable Frozen 331-Feature Model Input Contract (Gate 13)
===============================================================================

Immutable production contract governing the exact 331-feature model input contract
used by the accepted historical research lineage (C04_FLAT_EXTRA_TREES_CONSTRAINED).
Derived directly from the authoritative frozen training manifest:
pv_portable_xauusd_cff75b0686383a3ab6f8352b.manifest.json

No live trading.
No execution authority.
No retraining.
"""

from __future__ import annotations

import hashlib
import json
from typing import Sequence


PORTABLE_FEATURE_CONTRACT_VERSION: str = "XAUUSD_MTF_PORTABLE_FEATURE_V1"
PARENT_FEATURE_CONTRACT_VERSION: str = "XAUUSD_MTF_TRAINING_V3"

EXPECTED_FEATURE_COUNT: int = 331
PARENT_FEATURE_COUNT: int = 333

EXPECTED_FEATURE_COLUMNS_SHA256: str = (
    "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
)

FROZEN_MODEL_SHA256: str = (
    "48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769"
)

FROZEN_MODEL_WINNER_ID: str = "C04_FLAT_EXTRA_TREES_CONSTRAINED"
FROZEN_MODEL_CLASSES: tuple[int, ...] = (-1, 0, 1)

BASE_TIMEFRAME: str = "M5"
CONTEXT_TIMEFRAMES: tuple[str, ...] = ("M15", "M30", "H1", "H4", "D1")
ALL_TIMEFRAMES: tuple[str, ...] = ("M5", "M15", "M30", "H1", "H4", "D1")

CANONICAL_SYMBOL: str = "XAUUSD"
# Supported production symbols proven by broker evidence
SUPPORTED_SYMBOLS: tuple[str, ...] = ("XAUUSD", "XAUUSDm")

DROPPED_FEATURES: tuple[str, ...] = (
    "m5_spread_points",
    "m5_tick_volume_log1p",
)

RETAINED_RELATIVE_VOLUME_FEATURE: str = "m5_tick_volume_ratio20"

TIMEFRAME_MINUTES: dict[str, int] = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}

D1_SESSION_BOUNDARY_UTC: str = "00:00:00"

FROZEN_FEATURE_COLUMNS: tuple[str, ...] = (
    "m5_ema20",
    "m5_ema50",
    "m5_ema200",
    "m5_dist_ema20",
    "m5_dist_ema50",
    "m5_dist_ema200",
    "m5_ema20_slope",
    "m5_ema50_slope",
    "m5_ema200_slope",
    "m5_trend_strength",
    "m5_trend_direction",
    "m5_rsi14",
    "m5_rsi_slope",
    "m5_macd",
    "m5_macd_signal",
    "m5_macd_hist",
    "m5_roc10",
    "m5_momentum10",
    "m5_true_range",
    "m5_atr14",
    "m5_atr_percent",
    "m5_candle_range",
    "m5_avg_range20",
    "m5_volatility_ratio",
    "m5_rolling_std20",
    "m5_body",
    "m5_range",
    "m5_upper_wick",
    "m5_lower_wick",
    "m5_body_ratio",
    "m5_upper_wick_ratio",
    "m5_lower_wick_ratio",
    "m5_bullish",
    "m5_bearish",
    "m5_doji",
    "m5_marubozu",
    "m5_pinbar",
    "m5_bullish_engulfing",
    "m5_bearish_engulfing",
    "m5_inside_bar",
    "m5_outside_bar",
    "m5_expansion",
    "m5_compression",
    "m5_tick_volume_ratio20",
    "m15_ema20",
    "m15_ema50",
    "m15_ema200",
    "m15_dist_ema20",
    "m15_dist_ema50",
    "m15_dist_ema200",
    "m15_ema20_slope",
    "m15_ema50_slope",
    "m15_ema200_slope",
    "m15_trend_strength",
    "m15_trend_direction",
    "m15_rsi14",
    "m15_rsi_slope",
    "m15_macd",
    "m15_macd_signal",
    "m15_macd_hist",
    "m15_roc10",
    "m15_momentum10",
    "m15_true_range",
    "m15_atr14",
    "m15_atr_percent",
    "m15_candle_range",
    "m15_avg_range20",
    "m15_volatility_ratio",
    "m15_rolling_std20",
    "m15_body",
    "m15_range",
    "m15_upper_wick",
    "m15_lower_wick",
    "m15_body_ratio",
    "m15_upper_wick_ratio",
    "m15_lower_wick_ratio",
    "m15_bullish",
    "m15_bearish",
    "m15_doji",
    "m15_marubozu",
    "m15_pinbar",
    "m15_bullish_engulfing",
    "m15_bearish_engulfing",
    "m15_inside_bar",
    "m15_outside_bar",
    "m15_expansion",
    "m15_compression",
    "m15_age_minutes",
    "m30_ema20",
    "m30_ema50",
    "m30_ema200",
    "m30_dist_ema20",
    "m30_dist_ema50",
    "m30_dist_ema200",
    "m30_ema20_slope",
    "m30_ema50_slope",
    "m30_ema200_slope",
    "m30_trend_strength",
    "m30_trend_direction",
    "m30_rsi14",
    "m30_rsi_slope",
    "m30_macd",
    "m30_macd_signal",
    "m30_macd_hist",
    "m30_roc10",
    "m30_momentum10",
    "m30_true_range",
    "m30_atr14",
    "m30_atr_percent",
    "m30_candle_range",
    "m30_avg_range20",
    "m30_volatility_ratio",
    "m30_rolling_std20",
    "m30_body",
    "m30_range",
    "m30_upper_wick",
    "m30_lower_wick",
    "m30_body_ratio",
    "m30_upper_wick_ratio",
    "m30_lower_wick_ratio",
    "m30_bullish",
    "m30_bearish",
    "m30_doji",
    "m30_marubozu",
    "m30_pinbar",
    "m30_bullish_engulfing",
    "m30_bearish_engulfing",
    "m30_inside_bar",
    "m30_outside_bar",
    "m30_expansion",
    "m30_compression",
    "m30_age_minutes",
    "h1_ema20",
    "h1_ema50",
    "h1_ema200",
    "h1_dist_ema20",
    "h1_dist_ema50",
    "h1_dist_ema200",
    "h1_ema20_slope",
    "h1_ema50_slope",
    "h1_ema200_slope",
    "h1_trend_strength",
    "h1_trend_direction",
    "h1_rsi14",
    "h1_rsi_slope",
    "h1_macd",
    "h1_macd_signal",
    "h1_macd_hist",
    "h1_roc10",
    "h1_momentum10",
    "h1_true_range",
    "h1_atr14",
    "h1_atr_percent",
    "h1_candle_range",
    "h1_avg_range20",
    "h1_volatility_ratio",
    "h1_rolling_std20",
    "h1_body",
    "h1_range",
    "h1_upper_wick",
    "h1_lower_wick",
    "h1_body_ratio",
    "h1_upper_wick_ratio",
    "h1_lower_wick_ratio",
    "h1_bullish",
    "h1_bearish",
    "h1_doji",
    "h1_marubozu",
    "h1_pinbar",
    "h1_bullish_engulfing",
    "h1_bearish_engulfing",
    "h1_inside_bar",
    "h1_outside_bar",
    "h1_expansion",
    "h1_compression",
    "h1_age_minutes",
    "h4_ema20",
    "h4_ema50",
    "h4_ema200",
    "h4_dist_ema20",
    "h4_dist_ema50",
    "h4_dist_ema200",
    "h4_ema20_slope",
    "h4_ema50_slope",
    "h4_ema200_slope",
    "h4_trend_strength",
    "h4_trend_direction",
    "h4_rsi14",
    "h4_rsi_slope",
    "h4_macd",
    "h4_macd_signal",
    "h4_macd_hist",
    "h4_roc10",
    "h4_momentum10",
    "h4_true_range",
    "h4_atr14",
    "h4_atr_percent",
    "h4_candle_range",
    "h4_avg_range20",
    "h4_volatility_ratio",
    "h4_rolling_std20",
    "h4_body",
    "h4_range",
    "h4_upper_wick",
    "h4_lower_wick",
    "h4_body_ratio",
    "h4_upper_wick_ratio",
    "h4_lower_wick_ratio",
    "h4_bullish",
    "h4_bearish",
    "h4_doji",
    "h4_marubozu",
    "h4_pinbar",
    "h4_bullish_engulfing",
    "h4_bearish_engulfing",
    "h4_inside_bar",
    "h4_outside_bar",
    "h4_expansion",
    "h4_compression",
    "h4_age_minutes",
    "d1_ema20",
    "d1_ema50",
    "d1_ema200",
    "d1_dist_ema20",
    "d1_dist_ema50",
    "d1_dist_ema200",
    "d1_ema20_slope",
    "d1_ema50_slope",
    "d1_ema200_slope",
    "d1_trend_strength",
    "d1_trend_direction",
    "d1_rsi14",
    "d1_rsi_slope",
    "d1_macd",
    "d1_macd_signal",
    "d1_macd_hist",
    "d1_roc10",
    "d1_momentum10",
    "d1_true_range",
    "d1_atr14",
    "d1_atr_percent",
    "d1_candle_range",
    "d1_avg_range20",
    "d1_volatility_ratio",
    "d1_rolling_std20",
    "d1_body",
    "d1_range",
    "d1_upper_wick",
    "d1_lower_wick",
    "d1_body_ratio",
    "d1_upper_wick_ratio",
    "d1_lower_wick_ratio",
    "d1_bullish",
    "d1_bearish",
    "d1_doji",
    "d1_marubozu",
    "d1_pinbar",
    "d1_bullish_engulfing",
    "d1_bearish_engulfing",
    "d1_inside_bar",
    "d1_outside_bar",
    "d1_expansion",
    "d1_compression",
    "d1_age_minutes",
    "utc_hour_sin",
    "utc_hour_cos",
    "utc_day_sin",
    "utc_day_cos",
    "m5_domain_regime_ready",
    "m5_domain_regime_atr_percentile",
    "m5_domain_regime_range_atr",
    "m5_domain_regime_efficiency",
    "m5_domain_regime_directional_move_atr",
    "m5_domain_regime_trend_strength",
    "m5_domain_regime_trend_code",
    "m5_domain_regime_volatility_code",
    "m5_domain_hh",
    "m5_domain_hl",
    "m5_domain_lh",
    "m5_domain_ll",
    "m5_domain_micro_high",
    "m5_domain_micro_low",
    "m5_domain_internal_high",
    "m5_domain_internal_low",
    "m5_domain_major_high",
    "m5_domain_major_low",
    "m5_domain_swing_score",
    "m5_domain_swing_excursion_atr",
    "m5_domain_swing_reversal_atr",
    "m5_domain_swing_direction_code",
    "m5_domain_swing_scale_code",
    "m5_domain_structure_bias_code",
    "m5_domain_last_swing_high_known",
    "m5_domain_last_swing_low_known",
    "m5_domain_last_major_high_known",
    "m5_domain_last_major_low_known",
    "m5_domain_dist_last_swing_high_atr",
    "m5_domain_dist_last_swing_low_atr",
    "m5_domain_dist_last_major_high_atr",
    "m5_domain_dist_last_major_low_atr",
    "m5_domain_structure_range_position",
    "m5_domain_bars_since_swing",
    "m5_domain_bullish_bos",
    "m5_domain_bearish_bos",
    "m5_domain_micro_bos",
    "m5_domain_internal_bos",
    "m5_domain_major_bos",
    "m5_domain_bos_strength_atr",
    "m5_domain_bos_continuation",
    "m5_domain_bos_reversal",
    "m5_domain_bars_since_bullish_bos",
    "m5_domain_bars_since_bearish_bos",
    "m5_domain_last_bos_direction",
    "m5_domain_bullish_fvg",
    "m5_domain_bearish_fvg",
    "m5_domain_fvg_atr_ratio",
    "m5_domain_bars_since_bullish_fvg",
    "m5_domain_bars_since_bearish_fvg",
    "m5_domain_last_fvg_direction",
    "m5_domain_last_fvg_atr_ratio",
    "m5_domain_iz_event",
    "m5_domain_iz_direction",
    "m5_domain_iz_strength",
    "m5_domain_iz_displacement_score",
    "m5_domain_iz_body_ratio",
    "m5_domain_iz_zone_size_atr",
    "m5_domain_iz_confirmation_delay_bars",
    "m5_domain_bars_since_bullish_iz",
    "m5_domain_bars_since_bearish_iz",
    "m5_domain_last_iz_direction",
    "m5_domain_last_iz_strength",
)


def compute_feature_columns_sha256(feature_columns: Sequence[str]) -> str:
    """Compute the canonical SHA256 checksum of an ordered sequence of feature names."""
    payload = json.dumps(
        [str(c) for c in feature_columns],
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def verify_feature_columns(feature_columns: Sequence[str]) -> bool:
    """Verify that feature columns exactly match the frozen 331 contract in name, count, and order."""
    if len(feature_columns) != EXPECTED_FEATURE_COUNT:
        return False
    if tuple(feature_columns) != FROZEN_FEATURE_COLUMNS:
        return False
    return compute_feature_columns_sha256(feature_columns) == EXPECTED_FEATURE_COLUMNS_SHA256


def normalize_supported_symbol(symbol: str) -> str:
    """
    Validate that symbol is in the proven supported set (XAUUSD, XAUUSDm).
    Returns canonical XAUUSD or raises ValueError (fail-closed).
    """
    raw = str(symbol).strip()
    if raw in SUPPORTED_SYMBOLS:
        return CANONICAL_SYMBOL
    raise ValueError(f"UNSUPPORTED_BROKER_SYMBOL: '{symbol}' not in {SUPPORTED_SYMBOLS}")
