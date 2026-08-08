from __future__ import annotations

import importlib
from typing import Any

import pandas as pd


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

    return pd.DataFrame(
        {
            "open": [
                100.0
            ] * rows,

            "close": [
                100.0
            ] * rows,

            "bullish_sweep": [
                0
            ] * rows,

            "bearish_sweep": [
                0
            ] * rows,

            "is_displacement": [
                0
            ] * rows,

            "institutional_move": [
                0
            ] * rows,

            "bullish_bos": [
                0
            ] * rows,

            "bearish_bos": [
                0
            ] * rows,

            "bos_scope": [
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

            "fvg_interaction_events": pd.Series(
                [
                    []
                    for _ in range(
                        rows
                    )
                ],
                dtype="object",
            ),

            "structure_bias": [
                "NEUTRAL"
            ] * rows,
        }
    )


def _set_interaction_events(
    df: pd.DataFrame,
    row_index: int,
    events: list[
        dict[str, Any]
    ],
) -> None:
    """
    Safely replace one row's object-based FVG event list.

    We deliberately avoid:

        df.at[index, column] = list[dict]

    because Pandas/Pylance types scalar .at assignment as ScalarOrNA.
    """

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
# Bullish Temporal Sequence
# =============================================================================

def test_bullish_setup_combines_events_across_candles():

    df = _base_frame(
        5
    )

    # Candle 0:
    # sell-side raid => bullish setup starts.
    df.loc[
        0,
        "bullish_sweep",
    ] = 1

    # Candle 1:
    # bullish displacement.
    df.loc[
        1,
        "is_displacement",
    ] = 1

    df.loc[
        1,
        "institutional_move",
    ] = 1

    # Candle 2:
    # micro bullish BOS.
    df.loc[
        2,
        "bullish_bos",
    ] = 1

    df.loc[
        2,
        "bos_scope",
    ] = "MICRO"

    # Candle 3:
    # bullish FVG #10 forms.
    df.loc[
        3,
        "fvg_id",
    ] = 10

    df.loc[
        3,
        "bullish_fvg",
    ] = 1

    # Candle 4:
    # same FVG rejects.
    _set_interaction_events(
        df=df,
        row_index=4,
        events=[
            {
                "fvg_id": 10,
                "direction": (
                    "BULLISH"
                ),
                "event_type": (
                    "REJECTION"
                ),
                "fill_percent": (
                    50.0
                ),
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
            0,
            "bullish_setup_started_event",
        ]
        == 1
    )

    assert (
        result.loc[
            0,
            "bullish_setup_evidence_count",
        ]
        == 1
    )

    assert (
        result.loc[
            1,
            "bullish_setup_has_displacement",
        ]
        == 1
    )

    assert (
        result.loc[
            2,
            "bullish_setup_has_bos",
        ]
        == 1
    )

    assert (
        result.loc[
            3,
            "bullish_setup_has_fvg",
        ]
        == 1
    )

    assert (
        result.loc[
            4,
            "bullish_setup_has_rejection",
        ]
        == 1
    )

    assert (
        result.loc[
            4,
            "bullish_setup_evidence_count",
        ]
        == 5
    )

    assert (
        result.loc[
            4,
            "bullish_setup_ready",
        ]
        == 1
    )

    assert (
        result.loc[
            4,
            "bullish_setup_ready_event",
        ]
        == 1
    )

    assert (
        result.loc[
            4,
            "bullish_setup_state",
        ]
        == "READY"
    )

    assert (
        result.loc[
            4,
            "bullish_setup_fvg_id",
        ]
        == 10
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
    ] = "INTERNAL"

    df.loc[
        3,
        "fvg_id",
    ] = 20

    df.loc[
        3,
        "bullish_fvg",
    ] = 1

    # Wrong FVG ID.
    _set_interaction_events(
        df=df,
        row_index=4,
        events=[
            {
                "fvg_id": 999,
                "direction": (
                    "BULLISH"
                ),
                "event_type": (
                    "REJECTION"
                ),
                "fill_percent": (
                    60.0
                ),
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
    ] = 31

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
# New Sweep = New Setup
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
            1,
            "bullish_setup_id",
        ]
    )

    assert (
        first_id
        > 0
    )

    assert (
        second_id
        > first_id
    )

    assert (
        result.loc[
            1,
            "bullish_setup_age_bars",
        ]
        == 0
    )


# =============================================================================
# Expiration
# =============================================================================

def test_stale_setup_expires():

    df = _base_frame(
        5
    )

    df.loc[
        0,
        "bullish_sweep",
    ] = 1

    engine = SetupStateEngine(
        max_setup_bars=2
    )

    result = engine.generate(
        df
    )

    assert (
        result.loc[
            2,
            "bullish_setup_id",
        ]
        > 0
    )

    # Age becomes 3 here,
    # beyond max_setup_bars=2.
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
# Bearish Temporal Sequence
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
        df=df,
        row_index=4,
        events=[
            {
                "fvg_id": 50,
                "direction": (
                    "BEARISH"
                ),
                "event_type": (
                    "REJECTION"
                ),
                "fill_percent": (
                    40.0
                ),
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
            "bearish_setup_ready",
        ]
        == 1
    )

    assert (
        result.loc[
            4,
            "bearish_setup_evidence_count",
        ]
        == 5
    )

    assert (
        result.loc[
            4,
            "bearish_setup_state",
        ]
        == "READY"
    )


# =============================================================================
# Structure Alignment Is Context, Not Hard Gate
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

    # Setup still exists.
    # Context conflict does not automatically
    # destroy an M1 scalping setup.
    assert (
        result.loc[
            1,
            "bullish_setup_id",
        ]
        > 0
    )