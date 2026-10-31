"""
===============================================================================
Test Module : test_fvg_quality.py
Project     : PulseViper XAU AI
Purpose     : Complete tests for FVG Quality & Confluence Engine
===============================================================================
"""

from __future__ import annotations

import importlib

import pandas as pd
import pytest


MODULE_NAME = "02_AI.Core.fvg_quality_engine"


def load_engine():
    """Load the singleton FVG quality engine."""
    module = importlib.import_module(MODULE_NAME)

    assert hasattr(module, "FVGQualityEngine")
    assert hasattr(module, "fvg_quality_engine")

    return module, module.fvg_quality_engine


def build_test_data() -> pd.DataFrame:
    """
    Build deterministic FVG data matching the actual engine contract.
    """

    return pd.DataFrame(
        {
            # Required FVG identity/direction columns
            "fvg_id": [1, 2, 3],
            "bullish_fvg": [1, 0, 1],
            "bearish_fvg": [0, 1, 0],

            # Displacement
            "is_displacement": [1, 1, 0],
            "displacement_score": [90.0, 80.0, 20.0],

            # BOS
            "bullish_bos": [1, 0, 0],
            "bearish_bos": [0, 1, 0],
            "bos_strength": [2.0, 1.5, 0.0],

            # Liquidity
            "liquidity_sweep": [1, 1, 0],

            # Mitigation
            "fvg_mitigated": [0, 0, 1],

            # Rejection
            "fvg_rejection": [0, 0, 0],
            "fvg_rejection_strength": [0.0, 0.0, 0.0],

            # Market structure
            "HH": [1, 0, 0],
            "HL": [0, 0, 0],
            "LH": [0, 0, 0],
            "LL": [0, 1, 0],
        }
    )


# =============================================================================
# IMPORT TEST
# =============================================================================


def test_fvg_quality_engine_import():
    """Engine module and singleton must import successfully."""

    module, engine = load_engine()

    assert module is not None
    assert type(engine).__name__ == "FVGQualityEngine"


# =============================================================================
# CONFIGURATION TEST
# =============================================================================


def test_default_weights():
    """Default weights must match the engine design."""

    _, engine = load_engine()

    assert engine.displacement_weight == 25.0
    assert engine.bos_weight == 25.0
    assert engine.liquidity_weight == 20.0
    assert engine.mitigation_weight == 15.0
    assert engine.structure_weight == 15.0

    total_weight = (
        engine.displacement_weight
        + engine.bos_weight
        + engine.liquidity_weight
        + engine.mitigation_weight
        + engine.structure_weight
    )

    assert total_weight == 100.0


# =============================================================================
# REQUIRED COLUMN TEST
# =============================================================================


def test_missing_required_columns():
    """Missing required FVG columns must raise ValueError."""

    _, engine = load_engine()

    data = pd.DataFrame(
        {
            "fvg_id": [1],
        }
    )

    with pytest.raises(
        ValueError,
        match="Missing required FVG columns",
    ):
        engine.generate(data)


# =============================================================================
# BASIC GENERATION TEST
# =============================================================================


def test_fvg_quality_engine_generate():
    """Engine must generate all expected quality columns."""

    _, engine = load_engine()

    data = build_test_data()

    result = engine.generate(data)

    expected_columns = [
        "fvg_quality_score",
        "fvg_quality_grade",
        "fvg_displacement_score",
        "fvg_bos_score",
        "fvg_liquidity_score",
        "fvg_mitigation_score",
        "fvg_structure_score",
        "fvg_confluence_count",
        "fvg_institutional",
    ]

    for column in expected_columns:
        assert column in result.columns


# =============================================================================
# ROW 1 - STRONG BULLISH FVG
# =============================================================================


def test_strong_bullish_fvg_quality():
    """
    Row 1:

    Displacement = 90
    BOS strength = 2.0
    Liquidity sweep = 1
    HH = 1
    No mitigation

    Expected:
        displacement = 22.50
        BOS          = 25.00
        liquidity    = 20.00
        mitigation   = 0.00
        structure    = 15.00
        total        = 82.50
        grade        = A
        institutional= 1
    """

    _, engine = load_engine()

    data = build_test_data()

    result = engine.generate(data)

    row = result.iloc[0]

    assert row["fvg_displacement_score"] == 90.0
    assert row["fvg_bos_score"] == 100.0
    assert row["fvg_liquidity_score"] == 100.0
    assert row["fvg_mitigation_score"] == 0.0
    assert row["fvg_structure_score"] == 100.0

    assert row["fvg_quality_score"] == 82.5
    assert row["fvg_quality_grade"] == "A"
    assert row["fvg_confluence_count"] == 4
    assert row["fvg_institutional"] == 1


# =============================================================================
# ROW 2 - STRONG BEARISH FVG
# =============================================================================


def test_strong_bearish_fvg_quality():
    """
    Row 2:

    Displacement = 80
    BOS strength = 1.5
    Liquidity sweep = 1
    LL = 1
    No mitigation

    Expected:
        displacement = 20.00
        BOS          = 100.00
        liquidity    = 100.00
        mitigation   = 0.00
        structure    = 100.00
        total        = 80.00
        grade        = A
        institutional= 1
    """

    _, engine = load_engine()

    data = build_test_data()

    result = engine.generate(data)

    row = result.iloc[1]

    assert row["fvg_displacement_score"] == 80.0
    assert row["fvg_bos_score"] == 100.0
    assert row["fvg_liquidity_score"] == 100.0
    assert row["fvg_mitigation_score"] == 0.0
    assert row["fvg_structure_score"] == 100.0

    assert row["fvg_quality_score"] == 80.0
    assert row["fvg_quality_grade"] == "A"
    assert row["fvg_confluence_count"] == 4
    assert row["fvg_institutional"] == 1


# =============================================================================
# ROW 3 - MITIGATED LOW-QUALITY FVG
# =============================================================================


def test_mitigated_low_quality_fvg():
    """
    Row 3:

    No displacement
    No BOS
    No liquidity
    Mitigated = 1

    Expected:
        mitigation = 100
        weighted score = 15
        grade = D
        institutional = 0
    """

    _, engine = load_engine()

    data = build_test_data()

    result = engine.generate(data)

    row = result.iloc[2]

    assert row["fvg_displacement_score"] == 0.0
    assert row["fvg_bos_score"] == 0.0
    assert row["fvg_liquidity_score"] == 0.0
    assert row["fvg_mitigation_score"] == 100.0
    assert row["fvg_structure_score"] == 0.0

    assert row["fvg_quality_score"] == 15.0
    assert row["fvg_quality_grade"] == "D"
    assert row["fvg_confluence_count"] == 1
    assert row["fvg_institutional"] == 0


# =============================================================================
# MITIGATION REJECTION TEST
# =============================================================================


def test_fvg_rejection_strength():
    """FVG rejection should contribute mitigation quality."""

    _, engine = load_engine()

    data = pd.DataFrame(
        {
            "fvg_id": [1],
            "bullish_fvg": [1],
            "bearish_fvg": [0],

            "is_displacement": [0],
            "displacement_score": [0.0],

            "bullish_bos": [0],
            "bearish_bos": [0],
            "bos_strength": [0.0],

            "liquidity_sweep": [0],

            "fvg_mitigated": [0],
            "fvg_rejection": [1],
            "fvg_rejection_strength": [75.0],

            "HH": [0],
            "HL": [0],
            "LH": [0],
            "LL": [0],
        }
    )

    result = engine.generate(data)

    row = result.iloc[0]

    assert row["fvg_mitigation_score"] == 75.0
    assert row["fvg_quality_score"] == 11.25
    assert row["fvg_quality_grade"] == "D"
    assert row["fvg_confluence_count"] == 1
    assert row["fvg_institutional"] == 0


# =============================================================================
# SCORE CLAMPING TEST
# =============================================================================


def test_score_clamping():
    """
    Scores must remain within their valid 0-100 range.
    """

    _, engine = load_engine()

    data = pd.DataFrame(
        {
            "fvg_id": [1],
            "bullish_fvg": [1],
            "bearish_fvg": [0],

            "is_displacement": [1],
            "displacement_score": [999.0],

            "bullish_bos": [1],
            "bearish_bos": [0],
            "bos_strength": [999.0],

            "liquidity_sweep": [1],

            "fvg_mitigated": [1],

            "HH": [1],
            "HL": [0],
            "LH": [0],
            "LL": [0],
        }
    )

    result = engine.generate(data)

    row = result.iloc[0]

    assert row["fvg_displacement_score"] == 100.0
    assert row["fvg_bos_score"] == 100.0
    assert row["fvg_liquidity_score"] == 100.0
    assert row["fvg_mitigation_score"] == 100.0
    assert row["fvg_structure_score"] == 100.0

    assert row["fvg_quality_score"] == 100.0
    assert row["fvg_quality_grade"] == "A"
    assert row["fvg_confluence_count"] == 5
    assert row["fvg_institutional"] == 1


# =============================================================================
# ZERO / INVALID FVG ID TEST
# =============================================================================


def test_invalid_fvg_id_is_skipped():
    """FVG IDs <= 0 should not receive quality scores."""

    _, engine = load_engine()

    data = pd.DataFrame(
        {
            "fvg_id": [0, -1],
            "bullish_fvg": [1, 0],
            "bearish_fvg": [0, 1],

            "is_displacement": [1, 1],
            "displacement_score": [100.0, 100.0],

            "bullish_bos": [1, 1],
            "bearish_bos": [0, 0],
            "bos_strength": [2.0, 2.0],

            "liquidity_sweep": [1, 1],

            "fvg_mitigated": [1, 1],

            "HH": [1, 1],
            "HL": [0, 0],
            "LH": [0, 0],
            "LL": [0, 0],
        }
    )

    result = engine.generate(data)

    assert result.loc[0, "fvg_quality_score"] == 0.0
    assert result.loc[1, "fvg_quality_score"] == 0.0

    assert result.loc[0, "fvg_quality_grade"] == "NONE"
    assert result.loc[1, "fvg_quality_grade"] == "NONE"

    assert result.loc[0, "fvg_confluence_count"] == 0
    assert result.loc[1, "fvg_confluence_count"] == 0


# =============================================================================
# INPUT IMMUTABILITY TEST
# =============================================================================


def test_generate_does_not_modify_input():
    """generate() must operate on a copy of the input DataFrame."""

    _, engine = load_engine()

    data = build_test_data()

    original_columns = list(data.columns)
    original_values = data.copy(deep=True)

    result = engine.generate(data)

    assert list(data.columns) == original_columns
    pd.testing.assert_frame_equal(data, original_values)

    assert result is not data


# =============================================================================
# TO-FLOAT HELPER TEST
# =============================================================================


def test_to_float_helper():
    """Internal numeric conversion helper must handle normal/invalid values."""

    _, engine = load_engine()

    assert engine._to_float(10) == 10.0
    assert engine._to_float(10.5) == 10.5
    assert engine._to_float("20.5") == 20.5

    assert engine._to_float(None) == 0.0
    assert engine._to_float("invalid") == 0.0

    assert engine._to_float(
        "invalid",
        default=7.5,
    ) == 7.5


# =============================================================================
# FULL PIPELINE CONSISTENCY TEST
# =============================================================================


def test_full_pipeline_consistency():
    """
    Every generated FVG quality result must obey the engine invariants.
    """

    _, engine = load_engine()

    data = build_test_data()

    result = engine.generate(data)

    for _, row in result.iterrows():

        score = float(row["fvg_quality_score"])

        assert 0.0 <= score <= 100.0

        assert row["fvg_quality_grade"] in {
            "NONE",
            "D",
            "C",
            "B",
            "A",
        }

        assert 0 <= int(row["fvg_confluence_count"]) <= 5

        assert int(row["fvg_institutional"]) in {
            0,
            1,
        }

        assert 0.0 <= float(
            row["fvg_displacement_score"]
        ) <= 100.0

        assert 0.0 <= float(
            row["fvg_bos_score"]
        ) <= 100.0

        assert 0.0 <= float(
            row["fvg_liquidity_score"]
        ) <= 100.0

        assert 0.0 <= float(
            row["fvg_mitigation_score"]
        ) <= 100.0

        assert 0.0 <= float(
            row["fvg_structure_score"]
        ) <= 100.0