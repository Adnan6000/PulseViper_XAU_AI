"""
Deterministic offline tests for ResearchIntelligencePipeline v1.1.0.

Contracts
---------
- time + OHLC required
- canonical production outputs unchanged
- existing causal research chain preserved
- Institutional Zone context attached after LEI
- Institutional Zone context is observational only
- cslabel_* and izlabel_* hindsight prohibited
- stale research columns removed before replay
- wide composition emits no pandas PerformanceWarning
- output is prefix invariant
"""

from __future__ import annotations

import importlib
import warnings
from typing import Any

import numpy as np
import pandas as pd
import pytest


pytestmark = pytest.mark.offline


research_module: Any = importlib.import_module(
    "02_AI.Shadow.research_intelligence_pipeline"
)

ResearchIntelligencePipeline: Any = (
    research_module.ResearchIntelligencePipeline
)


def _frame(
    rows: int = 180,
) -> pd.DataFrame:

    sequence = np.arange(
        rows,
        dtype=float,
    )

    anchor = (
        2400.0
        +
        (
            sequence
            *
            0.002
        )
        +
        (
            np.sin(
                sequence
                /
                8.0
            )
            *
            0.75
        )
    )

    open_price = (
        anchor
        +
        (
            np.sin(
                sequence
                /
                5.0
            )
            *
            0.04
        )
    )

    close_price = (
        anchor
        +
        (
            np.cos(
                sequence
                /
                6.0
            )
            *
            0.04
        )
    )

    high = (
        np.maximum(
            open_price,
            close_price,
        )
        +
        0.24
        +
        (
            (
                sequence
                %
                5.0
            )
            *
            0.005
        )
    )

    low = (
        np.minimum(
            open_price,
            close_price,
        )
        -
        0.24
        -
        (
            (
                sequence
                %
                7.0
            )
            *
            0.004
        )
    )

    return pd.DataFrame(
        {
            "time": pd.date_range(
                "2026-08-10 00:00:00+00:00",
                periods=rows,
                freq="min",
            ),

            "open": open_price,

            "high": high,

            "low": low,

            "close": close_price,

            "tick_volume": (
                100
                +
                (
                    sequence
                    %
                    25
                )
            ).astype(
                np.int64
            ),
        }
    )


def _frame_with_clear_bullish_zone() -> pd.DataFrame:

    frame = _frame(
        180
    )

    frame.loc[
        60,
        [
            "open",
            "high",
            "low",
            "close",
        ],
    ] = [
        2400.0,
        2400.2,
        2399.2,
        2399.4,
    ]

    frame.loc[
        61,
        [
            "open",
            "high",
            "low",
            "close",
        ],
    ] = [
        2399.5,
        2401.2,
        2399.4,
        2401.0,
    ]

    return frame


def _manual_pre_zone_chain(
    pipeline: Any,
    frame: pd.DataFrame,
) -> pd.DataFrame:

    raw = (
        pipeline
        ._strip_prior_research_columns(
            frame
        )
    )

    canonical = pipeline._run_stage(
        pipeline.production_pipeline,
        raw,
        "canonical",
    )

    stages = (
        (
            "market_context_liquidity",
            pipeline.market_context_engine,
        ),
        (
            "liquidity_lifecycle",
            pipeline.liquidity_lifecycle_engine,
        ),
        (
            "liquidity_structure_intelligence",
            pipeline.liquidity_intelligence_engine,
        ),
        (
            "candle_swing_intelligence",
            pipeline.candle_swing_engine,
        ),
        (
            "market_decision_clarity",
            pipeline.decision_clarity_engine,
        ),
        (
            "level_entry_intelligence",
            pipeline.level_entry_engine,
        ),
    )

    current = canonical.copy()

    for name, engine in stages:

        current = pipeline._run_stage(
            engine,
            current,
            name,
        )

    return current.reset_index(
        drop=True
    )


def test_requires_time_and_ohlc() -> None:

    frame = _frame(
        20
    ).drop(
        columns=[
            "time",
        ]
    )

    with pytest.raises(
        ValueError,
        match="time",
    ):

        ResearchIntelligencePipeline().generate(
            frame
        )


def test_rejects_duplicate_input_columns() -> None:

    frame = _frame(
        20
    )

    duplicate = pd.concat(
        [
            frame,
            frame[
                [
                    "close",
                ]
            ],
        ],
        axis=1,
    )

    with pytest.raises(
        ValueError,
        match="duplicate column",
    ):

        ResearchIntelligencePipeline().generate(
            duplicate
        )


def test_adds_full_causal_research_chain() -> None:

    result = (
        ResearchIntelligencePipeline()
        .generate(
            _frame(
                180
            )
        )
    )

    required = {
        "ctx_version",
        "liq_lifecycle_version",
        "liqintel_version",
        "csi_version",
        "mdc_version",
        "lei_version",

        "izctx_live_safe",
        "izctx_version",
        "izctx_mode",

        "research_pipeline_version",
        "research_pipeline_mode",
        "research_stage_count",
        "research_zone_context_attached",
        "research_trade_ready_unchanged",
        "research_live_safe",
    }

    missing = (
        required
        -
        set(
            result.columns
        )
    )

    assert not missing, (
        f"Missing research columns: {sorted(missing)}"
    )

    assert (
        result[
            "research_pipeline_version"
        ]
        .eq(
            "1.1.0"
        )
        .all()
    )

    assert (
        result[
            "research_stage_count"
        ]
        .eq(
            9
        )
        .all()
    )

    assert (
        result[
            "research_zone_context_attached"
        ]
        .eq(
            1
        )
        .all()
    )

    assert (
        result[
            "research_live_safe"
        ]
        .eq(
            1
        )
        .all()
    )


def test_canonical_protected_outputs_are_unchanged() -> None:

    frame = _frame(
        180
    )

    pipeline = (
        ResearchIntelligencePipeline()
    )

    canonical = (
        pipeline
        .production_pipeline
        .generate(
            frame.copy()
        )
        .reset_index(
            drop=True
        )
    )

    result = (
        pipeline
        .generate(
            frame.copy()
        )
        .reset_index(
            drop=True
        )
    )

    protected: list[str] = []

    for column in canonical.columns:

        if not isinstance(
            column,
            str,
        ):
            continue

        if (
            column
            in {
                "trade_ready",
                "pipeline_version",
                "pipeline_mode",
            }
            or
            column.startswith(
                (
                    "confidence_",
                    "setup_",
                    "bos_",
                )
            )
        ):
            protected.append(
                column
            )

    assert protected

    for column in protected:

        pd.testing.assert_series_equal(
            canonical[
                column
            ].reset_index(
                drop=True
            ),

            result[
                column
            ].reset_index(
                drop=True
            ),

            check_names=False,
            check_dtype=True,
        )


def test_zone_context_does_not_modify_mdc_or_lei() -> None:

    frame = _frame_with_clear_bullish_zone()

    pipeline = (
        ResearchIntelligencePipeline()
    )

    before = _manual_pre_zone_chain(
        pipeline,
        frame,
    )

    after = pipeline.generate(
        frame
    )

    protected_research = [
        column
        for column in before.columns
        if (
            isinstance(
                column,
                str,
            )
            and
            column.startswith(
                (
                    "mdc_",
                    "lei_",
                )
            )
        )
    ]

    assert protected_research

    for column in protected_research:

        pd.testing.assert_series_equal(
            before[
                column
            ].reset_index(
                drop=True
            ),

            after[
                column
            ].reset_index(
                drop=True
            ),

            check_names=False,
            check_dtype=True,
        )


def test_clear_zone_reaches_context_adapter() -> None:

    result = (
        ResearchIntelligencePipeline()
        .generate(
            _frame_with_clear_bullish_zone()
        )
    )

    observed = (
        result[
            "izctx_bullish_event_id"
        ]
        .astype(
            str
        )
        .ne(
            "NONE"
        )
    )

    assert bool(
        observed.any()
    )

    assert bool(
        result[
            "izctx_live_safe"
        ]
        .eq(
            1
        )
        .all()
    )


def test_no_hindsight_labels_are_attached() -> None:

    result = (
        ResearchIntelligencePipeline()
        .generate(
            _frame(
                180
            )
        )
    )

    hindsight = [
        column
        for column in result.columns
        if (
            isinstance(
                column,
                str,
            )
            and
            column.startswith(
                (
                    "cslabel_",
                    "izlabel_",
                )
            )
        )
    ]

    assert hindsight == []


def test_stale_research_and_hindsight_are_removed() -> None:

    frame = _frame(
        120
    )

    frame[
        "research_pipeline_version"
    ] = "STALE"

    frame[
        "mdc_state"
    ] = "STALE"

    frame[
        "lei_status"
    ] = "STALE"

    frame[
        "izctx_bullish_state"
    ] = "STALE"

    frame[
        "cslabel_future_leak"
    ] = 1

    frame[
        "izlabel_future_leak"
    ] = 1

    result = (
        ResearchIntelligencePipeline()
        .generate(
            frame
        )
    )

    assert (
        result[
            "research_pipeline_version"
        ]
        .eq(
            "1.1.0"
        )
        .all()
    )

    assert (
        "cslabel_future_leak"
        not in result.columns
    )

    assert (
        "izlabel_future_leak"
        not in result.columns
    )

    assert not (
        result[
            "mdc_state"
        ]
        .astype(
            str
        )
        .eq(
            "STALE"
        )
        .any()
    )

    assert not (
        result[
            "lei_status"
        ]
        .astype(
            str
        )
        .eq(
            "STALE"
        )
        .any()
    )

    assert not (
        result[
            "izctx_bullish_state"
        ]
        .astype(
            str
        )
        .eq(
            "STALE"
        )
        .any()
    )


def test_pipeline_preserves_input_time_representation() -> None:

    frame = _frame(
        100
    )

    result = (
        ResearchIntelligencePipeline()
        .generate(
            frame
        )
    )

    pd.testing.assert_series_equal(
        frame[
            "time"
        ].reset_index(
            drop=True
        ),

        result[
            "time"
        ].reset_index(
            drop=True
        ),

        check_names=False,
        check_dtype=True,
    )


def test_final_composition_emits_no_performance_warning() -> None:

    with warnings.catch_warnings():

        warnings.simplefilter(
            "error",
            pd.errors.PerformanceWarning,
        )

        result = (
            ResearchIntelligencePipeline()
            .generate(
                _frame(
                    180
                )
            )
        )

    assert not result.empty

    assert (
        "izctx_version"
        in result.columns
    )


def test_repeated_generate_is_deterministic() -> None:

    pipeline = (
        ResearchIntelligencePipeline()
    )

    first = pipeline.generate(
        _frame(
            140
        )
    )

    second = pipeline.generate(
        first
    )

    assert first.columns.is_unique
    assert second.columns.is_unique

    common = [
        column
        for column in first.columns
        if column in second.columns
    ]

    for column in common:

        pd.testing.assert_series_equal(
            first[
                column
            ].reset_index(
                drop=True
            ),

            second[
                column
            ].reset_index(
                drop=True
            ),

            check_names=False,
            check_dtype=False,
        )


def test_prefix_invariance_prevents_future_leakage() -> None:

    frame = _frame_with_clear_bullish_zone()

    prefix_size = 120

    full = (
        ResearchIntelligencePipeline()
        .generate(
            frame.copy()
        )
    )

    prefix = (
        ResearchIntelligencePipeline()
        .generate(
            frame.iloc[
                :prefix_size
            ].copy()
        )
    )

    research_columns = [
        column
        for column in prefix.columns
        if (
            isinstance(
                column,
                str,
            )
            and
            column.startswith(
                ResearchIntelligencePipeline.RESEARCH_PREFIXES
            )
        )
    ]

    assert research_columns

    for column in research_columns:

        pd.testing.assert_series_equal(
            full.loc[
                :prefix_size - 1,
                column,
            ].reset_index(
                drop=True
            ),

            prefix[
                column
            ].reset_index(
                drop=True
            ),

            check_names=False,
            check_dtype=False,
        )


def test_trade_ready_unchanged_metadata_is_true() -> None:

    result = (
        ResearchIntelligencePipeline()
        .generate(
            _frame(
                180
            )
        )
    )

    assert bool(
        result[
            "research_trade_ready_unchanged"
        ]
        .eq(
            1
        )
        .all()
    )

    assert bool(
        result[
            "research_zone_context_attached"
        ]
        .eq(
            1
        )
        .all()
    )