"""
===============================================================================
Module      : enums.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Common Enumerations
===============================================================================
"""

from __future__ import annotations

from enum import Enum


# ==========================================================
# Liquidity
# ==========================================================

class LiquidityType(str, Enum):

    BUY_SIDE = "BUY_SIDE"

    SELL_SIDE = "SELL_SIDE"


# ==========================================================
# Market Structure
# ==========================================================

class TrendType(str, Enum):

    BULLISH = "BULLISH"

    BEARISH = "BEARISH"

    RANGING = "RANGING"


# ==========================================================
# BOS
# ==========================================================

class BOSType(str, Enum):

    BULLISH = "BULLISH"

    BEARISH = "BEARISH"


# ==========================================================
# CHOCH
# ==========================================================

class CHOCHType(str, Enum):

    BULLISH = "BULLISH"

    BEARISH = "BEARISH"


# ==========================================================
# Future Placeholders
# ==========================================================

class OrderBlockType(str, Enum):

    BULLISH = "BULLISH"

    BEARISH = "BEARISH"


class FVGType(str, Enum):

    BULLISH = "BULLISH"

    BEARISH = "BEARISH"


class SessionType(str, Enum):

    ASIA = "ASIA"

    LONDON = "LONDON"

    NEW_YORK = "NEW_YORK"

    OVERLAP = "OVERLAP"