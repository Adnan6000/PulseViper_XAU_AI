from __future__ import annotations

import importlib
from typing import Any

import pandas as pd
import pytest


module = importlib.import_module(
    "02_AI.Core.setup_state_engine"
)

SetupStateEngine = (
    module.SetupStateEngine
)


# =============================================================================
# Helpers
# =============================================================================

def _base_frame(
    rows: int,
) -> pd.DataFrame:

    df = pd.DataFrame(
        {
            "time": pd.date_range(
                "2026-08-07 10:00:00",
                periods=rows,
                freq="min",
            ),

            "open": [
                4300.0
            ] * rows,

            "high": [
                4301.0
            ] * rows,

            "low": [
                4299.0
            ] * rows,

            "close": [
                4300.0
            ] * rows,

            "bullish_sweep": [
                0
            ] * rows,

            "bearish_sweep": [
                0
            ] * rows,

            "sell_side_sweep": [
                0
            ] * rows,

            "buy_side_sweep": [
                0
            ] * rows,

            "institutional_move": [
                0
            ] * rows,

            "is_displacement": [
                0
            ] * rows,

            "displacement_score": [
                0.0
            ] * rows,

            "impulse_strength": [
                0.0
            ] * rows,

            "bullish_bos": [
                0
            ] * rows,

            "bearish_bos": [
                0
            ] * rows,

            "bos_id": [
                0
            ] * rows,

            "bos_scope": [
                "NONE"
            ] * rows,

            "broken_swing_scale": [
                "NONE"
            ] * rows,

            "bos_strength_atr": [
                0.0
            ] * rows,

            "break_distance_atr": [
                0.0
            ] * rows,

            "bos_context": [
                "NONE"
            ] * rows,

            "fvg_id": [
                0
            ] * rows,

            "bullish_fvg": [
                0
            ] * rows,

            "bearish_fvg": [
                0
            ] * rows,

            "structure_bias": [
                "NEUTRAL"
            ] * rows,
        }
    )

    df[
        "fvg_interaction_events"
    ] = pd.Series(
        [
            []
            for _ in range(
                rows
            )
        ],
        index=df.index,
        dtype="object",
    )

    return df


def _set_interaction_events(
    df: pd.DataFrame,
    row_index: int,
    events: list[
        dict[str, Any]
    ],
) -> None:

    event_buffer: list[Any] = (
        df[
            "fvg_interaction_events"
        ]
        .tolist()
    )

    event_buffer[
        row_index
    ] = events

    df[
        "fvg_interaction_events"
    ] = pd.Series(
        event_buffer,
        index=df.index,
        dtype="object",
    )


# =============================================================================
# Bullish Temporal Setup + v1.1 Telemetry
# =============================================================================

def test_bullish_setup_combines_events_across_candles():

    df = _base_frame(
        5
    )

    # Sweep
    df.loc[
        0,
        "bullish_sweep",
    ] = 1

    # Displacement
    df.loc[
        1,
        "institutional_move",
    ] = 1

    df.loc[
        1,
        "is_displacement",
    ] = 1

    df.loc[
        1,
        "displacement_score",
    ] = 82.0

    df.loc[
        1,
        "impulse_strength",
    ] = 1.40

    # BOS
    df.loc[
        2,
        "bullish_bos",
    ] = 1

    df.loc[
        2,
        "bos_id",
    ] = 501

    df.loc[
        2,
        "bos_scope",
    ] = "INTERNAL"

    df.loc[
        2,
        "bos_strength_atr",
    ] = 0.44

    df.loc[
        2,
        "break_distance_atr",
    ] = 0.44

    df.loc[
        2,
        "bos_context",
    ] = "REVERSAL"

    # FVG
    df.loc[
        3,
        "fvg_id",
    ] = 10

    df.loc[
        3,
        "bullish_fvg",
    ] = 1

    # Rejection of exact attached FVG
    _set_interaction_events(
        df,
        4,
        [
            {
                "fvg_id": 10,
                "direction": "BULLISH",
                "event_type": "REJECTION",
                "fill_percent": 62.5,
                "index": 4,
            }
        ],
    )

    result = (
        SetupStateEngine()
        .generate(
            df
        )
    )

    assert (
        result.loc[
            4,
            "setup_direction",
        ]
        == "BULLISH"
    )

    assert (
        result.loc[
            4,
            "setup_state",
        ]
        == "READY"
    )

    assert (
        result.loc[
            4,
            "setup_evidence_count",
        ]
        == 5
    )

    assert (
        result.loc[
            4,
            "setup_ready",
        ]
        == 1
    )

    assert (
        result.loc[
            4,
            "setup_ready_event",
        ]
        == 1
    )

    assert (
        result.loc[
            4,
            "setup_fvg_id",
        ]
        == 10
    )

    assert (
        result.loc[
            4,
            "setup_rejection_fvg_id",
        ]
        == 10
    )

    # -------------------------------------------------------------------------
    # v1.1 telemetry
    # -------------------------------------------------------------------------

    assert (
        result.loc[
            4,
            "setup_displacement_score",
        ]
        == pytest.approx(
            82.0
        )
    )

    assert (
        result.loc[
            4,
            "setup_impulse_strength",
        ]
        == pytest.approx(
            1.40
        )
    )

    assert (
        result.loc[
            4,
            "setup_bos_id",
        ]
        == 501
    )

    assert (
        result.loc[
            4,
            "setup_bos_strength_atr",
        ]
        == pytest.approx(
            0.44
        )
    )

    assert (
        result.loc[
            4,
            "setup_break_distance_atr",
        ]
        == pytest.approx(
            0.44
        )
    )

    assert (
        result.loc[
            4,
            "setup_bos_event_scope",
        ]
        == "INTERNAL"
    )

    assert (
        result.loc[
            4,
            "setup_bos_context",
        ]
        == "REVERSAL"
    )

    assert (
        result.loc[
            4,
            "setup_rejection_fill_percent",
        ]
        == pytest.approx(
            62.5
        )
    )

    assert (
        result.loc[
            4,
            "setup_fvg_count",
        ]
        == 1
    )

    assert (
        result.loc[
            4,
            "setup_displacement_index",
        ]
        == 1
    )

    assert (
        result.loc[
            4,
            "setup_bos_index",
        ]
        == 2
    )

    assert (
        result.loc[
            4,
            "setup_fvg_index",
        ]
        == 3
    )

    assert (
        result.loc[
            4,
            "setup_rejection_index",
        ]
        == 4
    )

    assert (
        result.loc[
            4,
            "setup_ready_index",
        ]
        == 4
    )

    assert (
        result.loc[
            4,
            "setup_sweep_to_displacement_bars",
        ]
        == 1
    )

    assert (
        result.loc[
            4,
            "setup_sweep_to_bos_bars",
        ]
        == 2
    )

    assert (
        result.loc[
            4,
            "setup_sweep_to_fvg_bars",
        ]
        == 3
    )

    assert (
        result.loc[
            4,
            "setup_sweep_to_rejection_bars",
        ]
        == 4
    )

    assert (
        result.loc[
            4,
            "setup_sweep_to_ready_bars",
        ]
        == 4
    )

    assert (
        result.loc[
            4,
            "setup_event_span_bars",
        ]
        == 4
    )


# =============================================================================
# FVG Identity Protection
# =============================================================================

def test_unrelated_fvg_rejection_cannot_complete_setup():

    df = _base_frame(
        5
    )

    df.loc[
        0,
        "bullish_sweep",
    ] = 1

    df.loc[
        1,
        "institutional_move",
    ] = 1

    df.loc[
        2,
        "bullish_bos",
    ] = 1

    df.loc[
        2,
        "bos_scope",
    ] = "MICRO"

    df.loc[
        3,
        "fvg_id",
    ] = 20

    df.loc[
        3,
        "bullish_fvg",
    ] = 1

    _set_interaction_events(
        df,
        4,
        [
            {
                "fvg_id": 999,
                "direction": "BULLISH",
                "event_type": "REJECTION",
                "fill_percent": 90.0,
                "index": 4,
            }
        ],
    )

    result = (
        SetupStateEngine()
        .generate(
            df
        )
    )

    assert (
        result.loc[
            4,
            "bullish_setup_has_rejection",
        ]
        == 0
    )

    assert (
        result.loc[
            4,
            "bullish_setup_ready",
        ]
        == 0
    )

    assert (
        result.loc[
            4,
            "bullish_setup_rejection_fill_percent",
        ]
        == 0.0
    )


# =============================================================================
# Direction Isolation
# =============================================================================

def test_bearish_evidence_cannot_contaminate_bullish_setup():

    df = _base_frame(
        4
    )

    df.loc[
        0,
        "bullish_sweep",
    ] = 1

    df.loc[
        1,
        "institutional_move",
    ] = -1

    df.loc[
        2,
        "bearish_bos",
    ] = 1

    df.loc[
        3,
        "fvg_id",
    ] = 30

    df.loc[
        3,
        "bearish_fvg",
    ] = 1

    result = (
        SetupStateEngine()
        .generate(
            df
        )
    )

    assert (
        result.loc[
            3,
            "bullish_setup_evidence_count",
        ]
        == 1
    )

    assert (
        result.loc[
            3,
            "bullish_setup_has_displacement",
        ]
        == 0
    )

    assert (
        result.loc[
            3,
            "bullish_setup_has_bos",
        ]
        == 0
    )

    assert (
        result.loc[
            3,
            "bullish_setup_has_fvg",
        ]
        == 0
    )


# =============================================================================
# Fresh Sweep Resets Setup + Telemetry
# =============================================================================

def test_new_same_direction_sweep_replaces_old_setup():

    df = _base_frame(
        3
    )

    df.loc[
        0,
        "bullish_sweep",
    ] = 1

    df.loc[
        1,
        "institutional_move",
    ] = 1

    df.loc[
        1,
        "displacement_score",
    ] = 91.0

    df.loc[
        2,
        "bullish_sweep",
    ] = 1

    result = (
        SetupStateEngine()
        .generate(
            df
        )
    )

    first_id = int(
        result.loc[
            0,
            "bullish_setup_id",
        ]
    )

    second_id = int(
        result.loc[
            2,
            "bullish_setup_id",
        ]
    )

    assert (
        second_id
        > first_id
    )

    assert (
        result.loc[
            2,
            "bullish_setup_age_bars",
        ]
        == 0
    )

    assert (
        result.loc[
            2,
            "bullish_setup_evidence_count",
        ]
        == 1
    )

    assert (
        result.loc[
            2,
            "bullish_setup_displacement_score",
        ]
        == 0.0
    )


# =============================================================================
# Expiry
# =============================================================================

def test_stale_setup_expires():

    df = _base_frame(
        4
    )

    df.loc[
        0,
        "bullish_sweep",
    ] = 1

    result = (
        SetupStateEngine(
            max_setup_bars=2
        )
        .generate(
            df
        )
    )

    assert (
        result.loc[
            2,
            "bullish_setup_id",
        ]
        > 0
    )

    assert (
        result.loc[
            2,
            "bullish_setup_age_bars",
        ]
        == 2
    )

    assert (
        result.loc[
            3,
            "bullish_setup_id",
        ]
        == 0
    )

    assert (
        result.loc[
            3,
            "bullish_setup_expired_event",
        ]
        == 1
    )


# =============================================================================
# Bearish Temporal Setup
# =============================================================================

def test_bearish_temporal_setup_can_become_ready():

    df = _base_frame(
        5
    )

    df.loc[
        0,
        "bearish_sweep",
    ] = 1

    df.loc[
        1,
        "institutional_move",
    ] = -1

    df.loc[
        1,
        "displacement_score",
    ] = 78.0

    df.loc[
        2,
        "bearish_bos",
    ] = 1

    df.loc[
        2,
        "bos_scope",
    ] = "INTERNAL"

    df.loc[
        3,
        "fvg_id",
    ] = 50

    df.loc[
        3,
        "bearish_fvg",
    ] = 1

    _set_interaction_events(
        df,
        4,
        [
            {
                "fvg_id": 50,
                "direction": "BEARISH",
                "event_type": "REJECTION",
                "fill_percent": 55.0,
                "index": 4,
            }
        ],
    )

    result = (
        SetupStateEngine()
        .generate(
            df
        )
    )

    assert (
        result.loc[
            4,
            "setup_direction",
        ]
        == "BEARISH"
    )

    assert (
        result.loc[
            4,
            "setup_ready",
        ]
        == 1
    )

    assert (
        result.loc[
            4,
            "setup_evidence_count",
        ]
        == 5
    )

    assert (
        result.loc[
            4,
            "setup_rejection_fill_percent",
        ]
        == pytest.approx(
            55.0
        )
    )


# =============================================================================
# Structure Remains Soft Context
# =============================================================================

def test_structure_bias_is_soft_context_only():

    df = _base_frame(
        2
    )

    df.loc[
        0,
        "bullish_sweep",
    ] = 1

    df.loc[
        1,
        "structure_bias",
    ] = "BEARISH"

    result = (
        SetupStateEngine()
        .generate(
            df
        )
    )

    assert (
        result.loc[
            1,
            "bullish_setup_structure_alignment",
        ]
        == -1
    )

    assert (
        result.loc[
            1,
            "bullish_setup_id",
        ]
        > 0
    )

    assert (
        result.loc[
            1,
            "bullish_setup_state",
        ]
        != "NONE"
    )


# =============================================================================
# Strongest Displacement Telemetry
# =============================================================================

def test_strongest_displacement_quality_is_preserved():

    df = _base_frame(
        3
    )

    df.loc[
        0,
        "bullish_sweep",
    ] = 1

    df.loc[
        1,
        "institutional_move",
    ] = 1

    df.loc[
        1,
        "displacement_score",
    ] = 60.0

    df.loc[
        1,
        "impulse_strength",
    ] = 1.10

    df.loc[
        2,
        "institutional_move",
    ] = 1

    df.loc[
        2,
        "displacement_score",
    ] = 88.0

    df.loc[
        2,
        "impulse_strength",
    ] = 1.60

    result = (
        SetupStateEngine()
        .generate(
            df
        )
    )

    assert (
        result.loc[
            2,
            "bullish_setup_displacement_score",
        ]
        == pytest.approx(
            88.0
        )
    )

    assert (
        result.loc[
            2,
            "bullish_setup_impulse_strength",
        ]
        == pytest.approx(
            1.60
        )
    )

    # Timing stays tied to FIRST directional displacement.
    assert (
        result.loc[
            2,
            "bullish_setup_displacement_index",
        ]
        == 1
    )


# =============================================================================
# Structural Scope vs Quantitative BOS Quality
# =============================================================================

def test_bos_scope_and_best_bos_event_quality_are_separate():

    df = _base_frame(
        3
    )

    df.loc[
        0,
        "bullish_sweep",
    ] = 1

    # Strong MICRO break
    df.loc[
        1,
        "bullish_bos",
    ] = 1

    df.loc[
        1,
        "bos_id",
    ] = 101

    df.loc[
        1,
        "bos_scope",
    ] = "MICRO"

    df.loc[
        1,
        "bos_strength_atr",
    ] = 0.80

    df.loc[
        1,
        "break_distance_atr",
    ] = 0.80

    df.loc[
        1,
        "bos_context",
    ] = "REVERSAL"

    # Weaker MAJOR break later
    df.loc[
        2,
        "bullish_bos",
    ] = 1

    df.loc[
        2,
        "bos_id",
    ] = 102

    df.loc[
        2,
        "bos_scope",
    ] = "MAJOR"

    df.loc[
        2,
        "bos_strength_atr",
    ] = 0.20

    df.loc[
        2,
        "break_distance_atr",
    ] = 0.20

    df.loc[
        2,
        "bos_context",
    ] = "CONTINUATION"

    result = (
        SetupStateEngine()
        .generate(
            df
        )
    )

    # Existing compatibility behavior:
    # highest structural scope seen.
    assert (
        result.loc[
            2,
            "bullish_setup_bos_scope",
        ]
        == "MAJOR"
    )

    # New quantitative telemetry:
    # strongest break event stays MICRO.
    assert (
        result.loc[
            2,
            "bullish_setup_bos_event_scope",
        ]
        == "MICRO"
    )

    assert (
        result.loc[
            2,
            "bullish_setup_bos_id",
        ]
        == 101
    )

    assert (
        result.loc[
            2,
            "bullish_setup_bos_strength_atr",
        ]
        == pytest.approx(
            0.80
        )
    )

    assert (
        result.loc[
            2,
            "bullish_setup_break_distance_atr",
        ]
        == pytest.approx(
            0.80
        )
    )


# =============================================================================
# Strongest Rejection Fill
# =============================================================================

def test_strongest_attached_rejection_fill_is_preserved():

    df = _base_frame(
        4
    )

    df.loc[
        0,
        "bullish_sweep",
    ] = 1

    df.loc[
        1,
        "fvg_id",
    ] = 70

    df.loc[
        1,
        "bullish_fvg",
    ] = 1

    _set_interaction_events(
        df,
        2,
        [
            {
                "fvg_id": 70,
                "direction": "BULLISH",
                "event_type": "REJECTION",
                "fill_percent": 40.0,
                "index": 2,
            }
        ],
    )

    _set_interaction_events(
        df,
        3,
        [
            {
                "fvg_id": 70,
                "direction": "BULLISH",
                "event_type": "REJECTION",
                "fill_percent": 72.0,
                "index": 3,
            }
        ],
    )

    result = (
        SetupStateEngine()
        .generate(
            df
        )
    )

    assert (
        result.loc[
            3,
            "bullish_setup_rejection_fill_percent",
        ]
        == pytest.approx(
            72.0
        )
    )

    assert (
        result.loc[
            3,
            "bullish_setup_rejection_strength_fvg_id",
        ]
        == 70
    )

    # First causal rejection index remains first event.
    assert (
        result.loc[
            3,
            "bullish_setup_rejection_index",
        ]
        == 2
    )