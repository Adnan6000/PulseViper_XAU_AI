"""
Deterministic offline tests for ResearchIntelligencePipeline v1.0.1.

Contracts:
- time + OHLC are required
- canonical production decisions remain unchanged
- all causal research layers are present
- hindsight cslabel_* columns are never attached
- stale research columns are removed before replay
- final wide dataframe composition emits no pandas PerformanceWarning
- research output is prefix invariant
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


def test_requires_time_and_ohlc() -> None:
    frame = (
        _frame(
            20
        )
        .drop(
            columns=[
                "time",
            ]
        )
    )

    with pytest.raises(
        ValueError,
        match="time",
    ):
        (
            ResearchIntelligencePipeline()
            .generate(
                frame
            )
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
        (
            ResearchIntelligencePipeline()
            .generate(
                duplicate
            )
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

    required_columns = {
        "ctx_version",
        "liq_lifecycle_version",
        "liqintel_version",
        "csi_version",
        "mdc_version",
        "lei_version",
        "research_pipeline_version",
        "research_pipeline_mode",
        "research_stage_count",
        "research_trade_ready_unchanged",
        "research_live_safe",
    }

    missing = (
        required_columns
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
            "1.0.1"
        )
        .all()
    )

    assert (
        result[
            "research_pipeline_mode"
        ]
        .eq(
            "SHADOW_CAUSAL_RESEARCH_ONLY"
        )
        .all()
    )

    assert (
        result[
            "research_stage_count"
        ]
        .eq(
            6
        )
        .all()
    )

    assert (
        result[
            "research_trade_ready_unchanged"
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

    protected_columns: list[str] = []

    for raw_column in canonical.columns:
        if not isinstance(
            raw_column,
            str,
        ):
            continue

        if (
            raw_column
            in {
                "trade_ready",
                "pipeline_version",
                "pipeline_mode",
            }
            or
            raw_column.startswith(
                (
                    "confidence_",
                    "setup_",
                    "bos_",
                )
            )
        ):
            protected_columns.append(
                raw_column
            )

    assert protected_columns

    for column in protected_columns:
        pd.testing.assert_series_equal(
            canonical[
                column
            ]
            .reset_index(
                drop=True
            ),

            result[
                column
            ]
            .reset_index(
                drop=True
            ),

            check_names=False,
            check_dtype=True,
        )


def test_hindsight_swing_labels_are_not_attached() -> None:
    result = (
        ResearchIntelligencePipeline()
        .generate(
            _frame(
                180
            )
        )
    )

    hindsight_columns = [
        column
        for column in result.columns
        if (
            isinstance(
                column,
                str,
            )
            and
            column.startswith(
                "cslabel_"
            )
        )
    ]

    assert hindsight_columns == []


def test_stale_research_columns_are_removed_before_fresh_replay() -> None:
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
        "cslabel_future_leak"
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
            "1.0.1"
        )
        .all()
    )

    assert (
        "cslabel_future_leak"
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
        ]
        .reset_index(
            drop=True
        ),

        result[
            "time"
        ]
        .reset_index(
            drop=True
        ),

        check_names=False,
        check_dtype=True,
    )


def test_final_composition_emits_no_performance_warning() -> None:
    """
    Wide research output must not emit pandas fragmentation warnings.

    PerformanceWarning is promoted to an exception inside this test so future
    repeated-column-insertion regressions fail deterministically.
    """

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
        "research_pipeline_version"
        in result.columns
    )


def test_repeated_generate_does_not_reuse_stale_research_metadata() -> None:
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

    assert len(
        first
    ) == len(
        second
    )

    assert (
        second[
            "research_pipeline_version"
        ]
        .eq(
            "1.0.1"
        )
        .all()
    )

    assert second.columns.is_unique

    hindsight_columns = [
        column
        for column in second.columns
        if (
            isinstance(
                column,
                str,
            )
            and
            column.startswith(
                "cslabel_"
            )
        )
    ]

    assert hindsight_columns == []


def test_prefix_invariance_prevents_future_leakage() -> None:
    frame = _frame(
        180
    )

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
            ]
            .reset_index(
                drop=True
            ),

            prefix[
                column
            ]
            .reset_index(
                drop=True
            ),

            check_names=False,
            check_dtype=False,
        )