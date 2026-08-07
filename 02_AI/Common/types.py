"""
===============================================================================
Module      : types.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Central Registry for Shared Project Types
===============================================================================
"""

from __future__ import annotations

import importlib

# ==========================================================
# Objects
# ==========================================================

Liquidity = importlib.import_module(
    "02_AI.Objects.liquidity"
).Liquidity

# Future Objects
#
# BOS = importlib.import_module(
#     "02_AI.Objects.bos"
# ).BOS
#
# OrderBlock = importlib.import_module(
#     "02_AI.Objects.order_block"
# ).OrderBlock
#
# FVG = importlib.import_module(
#     "02_AI.Objects.fvg"
# ).FVG
#
# TradeSignal = importlib.import_module(
#     "02_AI.Objects.trade_signal"
# ).TradeSignal