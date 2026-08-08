"""
===============================================================================
Test        : test_fvg_mitigation.py
Project     : PulseViper XAU AI
Purpose     : Validate causal FVG lifecycle and event identity
===============================================================================
"""

from __future__ import annotations

import importlib

import pandas as pd
import pytest


module = importlib.import_module(
    "02_AI.Core.fvg_mitigation_engine"
)

FVGMitigationEngine = (
    module.FVGMitigationEngine
)


# =============================================================================
# Bullish Full Mitigation
# =============================================================================

def test_bullish_fvg_mitigation_identity():

    engine = FVGMitigationEngine()

    df = pd.DataFrame(
        {
            "open": [
                103.0,
                103.0,
            ],
            "high": [
                104.0,
                103.0,
            ],
            "low": [
                102.0,
                99.0,
            ],
            "close": [
                103.0,
                101.0,
            ],

            "fvg_id": [
                1,
                0,
            ],
            "bullish_fvg": [
                1,
                0,
            ],
            "bearish_fvg": [
                0,
                0,
            ],

            "fvg_high": [
                102.0,
                0.0,
            ],
            "fvg_low": [
                100.0,
                0.0,
            ],
        }
    )

    result = engine.generate(
        df
    )

    assert (
        result.loc[
            1,
            "fvg_mitigated",
        ]
        == 1
    )

    assert (
        result.loc[
            1,
            "fvg_mitigation_id",
        ]
        == 1
    )

    assert (
        result.loc[
            1,
            "fvg_mitigation_direction",
        ]
        == "BULLISH"
    )

    assert (
        result.loc[
            1,
            "fvg_mitigation_index",
        ]
        == 1
    )

    assert (
        result.loc[
            1,
            "fvg_mitigation_price",
        ]
        == pytest.approx(
            99.0
        )
    )


# =============================================================================
# Bearish Full Mitigation
# =============================================================================

def test_bearish_fvg_mitigation_identity():

    engine = FVGMitigationEngine()

    df = pd.DataFrame(
        {
            "open": [
                97.0,
                97.0,
            ],
            "high": [
                98.0,
                101.0,
            ],
            "low": [
                96.0,
                97.0,
            ],
            "close": [
                97.0,
                99.0,
            ],

            "fvg_id": [
                2,
                0,
            ],
            "bullish_fvg": [
                0,
                0,
            ],
            "bearish_fvg": [
                1,
                0,
            ],

            "fvg_high": [
                100.0,
                0.0,
            ],
            "fvg_low": [
                98.0,
                0.0,
            ],
        }
    )

    result = engine.generate(
        df
    )

    assert (
        result.loc[
            1,
            "fvg_mitigated",
        ]
        == 1
    )

    assert (
        result.loc[
            1,
            "fvg_mitigation_id",
        ]
        == 2
    )

    assert (
        result.loc[
            1,
            "fvg_mitigation_direction",
        ]
        == "BEARISH"
    )

    assert (
        result.loc[
            1,
            "fvg_mitigation_price",
        ]
        == pytest.approx(
            101.0
        )
    )


# =============================================================================
# Bullish Rejection
# =============================================================================

def test_bullish_rejection_preserves_fvg_identity():

    engine = FVGMitigationEngine(
        rejection_threshold=0.25
    )

    df = pd.DataFrame(
        {
            "open": [
                103.0,
                102.5,
            ],
            "high": [
                104.0,
                103.5,
            ],
            "low": [
                102.0,
                101.0,
            ],
            "close": [
                103.0,
                103.0,
            ],

            "fvg_id": [
                7,
                0,
            ],
            "bullish_fvg": [
                1,
                0,
            ],
            "bearish_fvg": [
                0,
                0,
            ],

            "fvg_high": [
                102.0,
                0.0,
            ],
            "fvg_low": [
                100.0,
                0.0,
            ],
        }
    )

    result = engine.generate(
        df
    )

    assert (
        result.loc[
            1,
            "fvg_rejection",
        ]
        == 1
    )

    assert (
        result.loc[
            1,
            "fvg_rejection_id",
        ]
        == 7
    )

    assert (
        result.loc[
            1,
            "fvg_rejection_direction",
        ]
        == "BULLISH"
    )

    assert (
        result.loc[
            1,
            "fvg_interaction_id",
        ]
        == 7
    )

    assert (
        result.loc[
            1,
            "fvg_interaction_direction",
        ]
        == "BULLISH"
    )

    assert (
        result.loc[
            1,
            "fvg_interaction_type",
        ]
        == "REJECTION"
    )

    assert (
        result.loc[
            1,
            "fvg_interaction_fill_percent",
        ]
        == pytest.approx(
            50.0
        )
    )


# =============================================================================
# Bearish Rejection
# =============================================================================

def test_bearish_rejection_preserves_fvg_identity():

    engine = FVGMitigationEngine(
        rejection_threshold=0.25
    )

    df = pd.DataFrame(
        {
            "open": [
                97.0,
                97.5,
            ],
            "high": [
                98.0,
                99.0,
            ],
            "low": [
                96.0,
                96.5,
            ],
            "close": [
                97.0,
                97.0,
            ],

            "fvg_id": [
                9,
                0,
            ],
            "bullish_fvg": [
                0,
                0,
            ],
            "bearish_fvg": [
                1,
                0,
            ],

            "fvg_high": [
                100.0,
                0.0,
            ],
            "fvg_low": [
                98.0,
                0.0,
            ],
        }
    )

    result = engine.generate(
        df
    )

    assert (
        result.loc[
            1,
            "fvg_rejection",
        ]
        == 1
    )

    assert (
        result.loc[
            1,
            "fvg_rejection_id",
        ]
        == 9
    )

    assert (
        result.loc[
            1,
            "fvg_rejection_direction",
        ]
        == "BEARISH"
    )


# =============================================================================
# No Same-Candle Lifecycle Event
# =============================================================================

def test_fvg_cannot_mitigate_on_creation_candle():

    engine = FVGMitigationEngine()

    df = pd.DataFrame(
        {
            "open": [
                101.0,
            ],
            "high": [
                104.0,
            ],
            "low": [
                99.0,
            ],
            "close": [
                103.0,
            ],

            "fvg_id": [
                11,
            ],
            "bullish_fvg": [
                1,
            ],
            "bearish_fvg": [
                0,
            ],

            "fvg_high": [
                102.0,
            ],
            "fvg_low": [
                100.0,
            ],
        }
    )

    result = engine.generate(
        df
    )

    assert (
        result.loc[
            0,
            "fvg_mitigated",
        ]
        == 0
    )

    assert (
        result.loc[
            0,
            "fvg_rejection",
        ]
        == 0
    )

    assert (
        result.loc[
            0,
            "fvg_interaction_count",
        ]
        == 0
    )


# =============================================================================
# Complete Event List
# =============================================================================

def test_rejection_event_is_available_in_event_list():

    engine = FVGMitigationEngine()

    df = pd.DataFrame(
        {
            "open": [
                103.0,
                102.5,
            ],
            "high": [
                104.0,
                103.5,
            ],
            "low": [
                102.0,
                101.0,
            ],
            "close": [
                103.0,
                103.0,
            ],

            "fvg_id": [
                15,
                0,
            ],
            "bullish_fvg": [
                1,
                0,
            ],
            "bearish_fvg": [
                0,
                0,
            ],

            "fvg_high": [
                102.0,
                0.0,
            ],
            "fvg_low": [
                100.0,
                0.0,
            ],
        }
    )

    result = engine.generate(
        df
    )

    events = result.loc[
        1,
        "fvg_interaction_events",
    ]

    assert isinstance(
        events,
        list,
    )

    assert len(
        events
    ) == 1

    assert (
        events[0][
            "fvg_id"
        ]
        == 15
    )

    assert (
        events[0][
            "direction"
        ]
        == "BULLISH"
    )

    assert (
        events[0][
            "event_type"
        ]
        == "REJECTION"
    )