from __future__ import annotations

import importlib

import pandas as pd


module = importlib.import_module(
    "02_AI.Core.confidence_engine"
)

ConfidenceEngine = (
    module.ConfidenceEngine
)


def _frame(
    rows: int = 1,
) -> pd.DataFrame:

    return pd.DataFrame(
        {
            "close": [
                4300.0
            ] * rows,

            "setup_id": [
                1
            ] * rows,

            "setup_direction": [
                "BULLISH"
            ] * rows,

            "setup_state": [
                "DEVELOPING"
            ] * rows,

            "setup_ready": [
                0
            ] * rows,

            "setup_ready_event": [
                0
            ] * rows,

            "setup_evidence_count": [
                1
            ] * rows,

            "setup_has_sweep": [
                1
            ] * rows,

            "setup_has_displacement": [
                0
            ] * rows,

            "setup_has_bos": [
                0
            ] * rows,

            "setup_has_fvg": [
                0
            ] * rows,

            "setup_has_rejection": [
                0
            ] * rows,

            "setup_structure_alignment": [
                0
            ] * rows,

            "setup_bos_scope": [
                "NONE"
            ] * rows,

            "setup_age_bars": [
                0
            ] * rows,

            "setup_conflict": [
                0
            ] * rows,
        }
    )


# =============================================================================
# Temporal Evidence
# =============================================================================

def test_confidence_uses_accumulated_setup_state():

    df = _frame()

    # Current candle contains no raw BOS/FVG/sweep signals.
    # Everything comes from accumulated setup state.
    df[
        "setup_has_displacement"
    ] = 1

    df[
        "setup_has_bos"
    ] = 1

    df[
        "setup_bos_scope"
    ] = "INTERNAL"

    df[
        "setup_has_fvg"
    ] = 1

    df[
        "setup_has_rejection"
    ] = 1

    df[
        "setup_structure_alignment"
    ] = 1

    df[
        "setup_ready"
    ] = 1

    df[
        "setup_ready_event"
    ] = 1

    df[
        "setup_state"
    ] = "READY"

    result = (
        ConfidenceEngine()
        .generate(
            df
        )
    )

    assert (
        result.loc[
            0,
            "confidence_mode",
        ]
        == "TEMPORAL_SETUP"
    )

    assert (
        result.loc[
            0,
            "confidence_direction",
        ]
        == "BULLISH"
    )

    assert (
        result.loc[
            0,
            "confidence_confluence",
        ]
        == 6
    )

    assert (
        result.loc[
            0,
            "confidence_score",
        ]
        >= 85.0
    )

    assert (
        result.loc[
            0,
            "trade_ready",
        ]
        == 1
    )


# =============================================================================
# One-Shot Trigger
# =============================================================================

def test_ready_setup_triggers_trade_only_once():

    df = _frame(
        rows=2
    )

    for column in (
        "setup_has_displacement",
        "setup_has_bos",
        "setup_has_fvg",
        "setup_has_rejection",
    ):

        df[
            column
        ] = 1

    df[
        "setup_bos_scope"
    ] = "INTERNAL"

    df[
        "setup_structure_alignment"
    ] = 1

    df[
        "setup_ready"
    ] = [
        1,
        1,
    ]

    df[
        "setup_ready_event"
    ] = [
        1,
        0,
    ]

    df[
        "setup_state"
    ] = [
        "READY",
        "READY",
    ]

    result = (
        ConfidenceEngine()
        .generate(
            df
        )
    )

    assert (
        result.loc[
            0,
            "trade_ready",
        ]
        == 1
    )

    # Same setup remains ready but does not fire again.
    assert (
        result.loc[
            1,
            "trade_ready",
        ]
        == 0
    )


# =============================================================================
# Structure Is Soft Context
# =============================================================================

def test_structure_conflict_penalizes_but_does_not_hard_block():

    df = _frame()

    df[
        "setup_has_displacement"
    ] = 1

    df[
        "setup_has_bos"
    ] = 1

    df[
        "setup_bos_scope"
    ] = "MICRO"

    df[
        "setup_has_fvg"
    ] = 1

    df[
        "setup_has_rejection"
    ] = 1

    # M1 bullish setup against broader bearish structure.
    df[
        "setup_structure_alignment"
    ] = -1

    df[
        "setup_ready"
    ] = 1

    df[
        "setup_ready_event"
    ] = 1

    df[
        "setup_state"
    ] = "READY"

    result = (
        ConfidenceEngine()
        .generate(
            df
        )
    )

    assert (
        result.loc[
            0,
            "confidence_structure",
        ]
        == 0.0
    )

    assert (
        result.loc[
            0,
            "confidence_score",
        ]
        >= 65.0
    )

    # Conflict is context penalty, not automatic scalp rejection.
    assert (
        result.loc[
            0,
            "trade_ready",
        ]
        == 1
    )


# =============================================================================
# BOS Hierarchy
# =============================================================================

def test_bos_scope_changes_confidence_quality():

    rows = []

    for scope in (
        "MICRO",
        "INTERNAL",
        "MAJOR",
    ):

        rows.append(
            {
                "close": 4300.0,
                "setup_id": 1,
                "setup_direction": "BULLISH",
                "setup_state": "DEVELOPING",
                "setup_ready": 0,
                "setup_ready_event": 0,
                "setup_evidence_count": 3,
                "setup_has_sweep": 1,
                "setup_has_displacement": 1,
                "setup_has_bos": 1,
                "setup_has_fvg": 0,
                "setup_has_rejection": 0,
                "setup_structure_alignment": 0,
                "setup_bos_scope": scope,
                "setup_age_bars": 3,
                "setup_conflict": 0,
            }
        )

    df = pd.DataFrame(
        rows
    )

    result = (
        ConfidenceEngine()
        .generate(
            df
        )
    )

    micro = result.loc[
        0,
        "confidence_score",
    ]

    internal = result.loc[
        1,
        "confidence_score",
    ]

    major = result.loc[
        2,
        "confidence_score",
    ]

    assert (
        micro
        < internal
        < major
    )


# =============================================================================
# Conflict
# =============================================================================

def test_exact_setup_conflict_never_creates_trade():

    df = _frame()

    df[
        "setup_id"
    ] = 0

    df[
        "setup_direction"
    ] = "CONFLICT"

    df[
        "setup_state"
    ] = "CONFLICT"

    df[
        "setup_conflict"
    ] = 1

    result = (
        ConfidenceEngine()
        .generate(
            df
        )
    )

    assert (
        result.loc[
            0,
            "confidence_direction",
        ]
        == "NEUTRAL"
    )

    assert (
        result.loc[
            0,
            "confidence_score",
        ]
        == 0.0
    )

    assert (
        result.loc[
            0,
            "trade_ready",
        ]
        == 0
    )


# =============================================================================
# Developing Setup Cannot Trigger
# =============================================================================

def test_high_developing_score_does_not_trade_before_ready_event():

    df = _frame()

    df[
        "setup_has_displacement"
    ] = 1

    df[
        "setup_has_bos"
    ] = 1

    df[
        "setup_bos_scope"
    ] = "MAJOR"

    df[
        "setup_has_fvg"
    ] = 1

    df[
        "setup_structure_alignment"
    ] = 1

    result = (
        ConfidenceEngine()
        .generate(
            df
        )
    )

    assert (
        result.loc[
            0,
            "confidence_score",
        ]
        > 65.0
    )

    # No rejection, no ready transition.
    assert (
        result.loc[
            0,
            "trade_ready",
        ]
        == 0
    )


# =============================================================================
# Legacy Compatibility
# =============================================================================

def test_legacy_row_contract_remains_available():

    df = pd.DataFrame(
        {
            "close": [
                4300.0
            ],

            "fvg_quality_score": [
                90.0
            ],

            "fvg_displacement_score": [
                100.0
            ],

            "fvg_bos_score": [
                100.0
            ],

            "fvg_liquidity_score": [
                100.0
            ],

            "fvg_structure_score": [
                100.0
            ],

            "fvg_mitigation_score": [
                100.0
            ],

            "bullish_fvg": [
                1
            ],

            "bullish_bos": [
                1
            ],

            "bullish_sweep": [
                1
            ],
        }
    )

    result = (
        ConfidenceEngine()
        .generate(
            df
        )
    )

    assert (
        result.loc[
            0,
            "confidence_mode",
        ]
        == "LEGACY_ROW"
    )

    assert (
        result.loc[
            0,
            "confidence_direction",
        ]
        == "BULLISH"
    )

    assert (
        result.loc[
            0,
            "trade_ready",
        ]
        == 1
    )