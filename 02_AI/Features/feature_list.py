"""
===============================================================================
Module      : feature_list.py
Project     : PulseViper XAU AI
Version     : 3.1
Purpose     : Central Feature Registry
===============================================================================
"""

FEATURE_COLUMNS = [

    # ===========================
    # Trend Features
    # ===========================

    "ema20",
    "ema50",
    "ema200",

    "dist_ema20",
    "dist_ema50",
    "dist_ema200",

    "ema20_slope",
    "ema50_slope",
    "ema200_slope",

    "trend_strength",
    "trend_direction",

    # ===========================
    # Momentum Features
    # ===========================

    "rsi14",
    "rsi_slope",

    "macd",
    "macd_signal",
    "macd_hist",

    "roc10",

    "momentum10",

    # ===========================
    # Volatility Features
    # ===========================

    "true_range",

    "atr14",

    "atr_percent",

    "candle_range",

    "avg_range20",

    "volatility_ratio",

    "rolling_std20",

    # ===========================
    # Candle Features
    # ===========================

    "body",
    "range",

    "upper_wick",
    "lower_wick",

    "body_ratio",
    "upper_wick_ratio",
    "lower_wick_ratio",

    "bullish",
    "bearish",

    "doji",
    "marubozu",
    "pinbar",

    "bullish_engulfing",
    "bearish_engulfing",

    "inside_bar",
    "outside_bar",

    "expansion",
    "compression",

]