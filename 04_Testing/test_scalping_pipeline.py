from __future__ import annotations

import importlib
from typing import Any

import pandas as pd
import pytest


module = importlib.import_module(
    "02_AI.Core.scalping_pipeline"
)

ScalpingPipeline = (
    module.ScalpingPipeline
)


# =============================================================================
# Fake Engines
#
# This test validates orchestration only.
# It deliberately does not fetch MT5 data or retest every engine.
# =============================================================================

class FakeEngine:

    def __init__(
        self,
        name: str,
        calls: list[str],
    ) -> None:

        self.name = name

        self.calls = calls

    def generate(
        self,
        data: pd.DataFrame,
        **kwargs: Any,
    ) -> pd.DataFrame:

        df = data.copy()

        self.calls.append(
            self.name
        )

        df[
            f"stage_{self.name}"
        ] = 1

        return df


class FakeSweepEngine(
    FakeEngine
):

    def generate(
        self,
        data: pd.DataFrame,
        reset_memory: bool = True,
    ) -> pd.DataFrame:

        assert (
            reset_memory
            is True
        )

        return super().generate(
            data
        )


class FakeBOSEngine(
    FakeEngine
):

    def generate(
        self,
        data: pd.DataFrame,
        reset_memory: bool = True,
    ) -> pd.DataFrame:

        assert (
            reset_memory
            is True
        )

        return super().generate(
            data
        )


# =============================================================================
# Helper
# =============================================================================

def _frame() -> pd.DataFrame:

    return pd.DataFrame(
        {
            "open": [
                4300.0,
                4301.0,
            ],

            "high": [
                4302.0,
                4303.0,
            ],

            "low": [
                4299.0,
                4300.0,
            ],

            "close": [
                4301.0,
                4302.0,
            ],
        }
    )


# =============================================================================
# Exact Pipeline Order
# =============================================================================

def test_scalping_pipeline_executes_exact_temporal_order():

    calls: list[str] = []

    pipeline = ScalpingPipeline(
        liquidity_engine=(
            FakeEngine(
                "liquidity",
                calls,
            )
        ),

        sweep_engine=(
            FakeSweepEngine(
                "sweep",
                calls,
            )
        ),

        displacement_engine=(
            FakeEngine(
                "displacement",
                calls,
            )
        ),

        market_structure_engine=(
            FakeEngine(
                "structure",
                calls,
            )
        ),

        bos_engine=(
            FakeBOSEngine(
                "bos",
                calls,
            )
        ),

        fvg_engine=(
            FakeEngine(
                "fvg",
                calls,
            )
        ),

        mitigation_engine=(
            FakeEngine(
                "mitigation",
                calls,
            )
        ),

        quality_engine=(
            FakeEngine(
                "quality",
                calls,
            )
        ),

        setup_state_engine=(
            FakeEngine(
                "setup_state",
                calls,
            )
        ),

        confidence_engine=(
            FakeEngine(
                "confidence",
                calls,
            )
        ),
    )

    result = pipeline.generate(
        _frame()
    )

    assert calls == [
        "liquidity",
        "sweep",
        "displacement",
        "structure",
        "bos",
        "fvg",
        "mitigation",
        "quality",
        "setup_state",
        "confidence",
    ]

    assert (
        result[
            "pipeline_mode"
        ]
        .eq(
            "SCALPING_TEMPORAL"
        )
        .all()
    )

    assert (
        result[
            "pipeline_version"
        ]
        .eq(
            "1.0"
        )
        .all()
    )


# =============================================================================
# Input Must Not Be Mutated
# =============================================================================

def test_pipeline_does_not_mutate_original_dataframe():

    calls: list[str] = []

    pipeline = ScalpingPipeline(
        liquidity_engine=(
            FakeEngine(
                "liquidity",
                calls,
            )
        ),

        sweep_engine=(
            FakeSweepEngine(
                "sweep",
                calls,
            )
        ),

        displacement_engine=(
            FakeEngine(
                "displacement",
                calls,
            )
        ),

        market_structure_engine=(
            FakeEngine(
                "structure",
                calls,
            )
        ),

        bos_engine=(
            FakeBOSEngine(
                "bos",
                calls,
            )
        ),

        fvg_engine=(
            FakeEngine(
                "fvg",
                calls,
            )
        ),

        mitigation_engine=(
            FakeEngine(
                "mitigation",
                calls,
            )
        ),

        quality_engine=(
            FakeEngine(
                "quality",
                calls,
            )
        ),

        setup_state_engine=(
            FakeEngine(
                "setup_state",
                calls,
            )
        ),

        confidence_engine=(
            FakeEngine(
                "confidence",
                calls,
            )
        ),
    )

    source = _frame()

    pipeline.generate(
        source
    )

    assert (
        "pipeline_mode"
        not in source.columns
    )

    assert (
        "stage_liquidity"
        not in source.columns
    )


# =============================================================================
# Required OHLC
# =============================================================================

def test_pipeline_rejects_missing_ohlc():

    pipeline = ScalpingPipeline(
        liquidity_engine=object(),
        sweep_engine=object(),
        displacement_engine=object(),
        market_structure_engine=object(),
        bos_engine=object(),
        fvg_engine=object(),
        mitigation_engine=object(),
        quality_engine=object(),
        setup_state_engine=object(),
        confidence_engine=object(),
    )

    df = pd.DataFrame(
        {
            "close": [
                4300.0
            ]
        }
    )

    with pytest.raises(
        ValueError,
        match=(
            "Missing required pipeline columns"
        ),
    ):

        pipeline.generate(
            df
        )