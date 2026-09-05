"""
Offline tests for ResearchOpportunityQualityProfiler v1.0.
"""

from __future__ import annotations

import importlib
from typing import Any

import pandas as pd
import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Shadow.research_opportunity_quality"
)

Profiler: Any = (
    module.ResearchOpportunityQualityProfiler
)


def _episodes() -> pd.DataFrame:

    rows: list[
        dict[
            str,
            object,
        ]
    ] = []

    for index in range(
        40
    ):

        long_side = (
            index < 20
        )

        strong_band = (
            index % 2 == 0
        )

        direction = (
            "LONG"
            if long_side
            else
            "SHORT"
        )

        confidence = (
            75.0
            if strong_band
            else
            42.0
        )

        family = (
            "BREAK_ACCEPTANCE"
            if index % 3
            else
            "FAILED_BREAKOUT"
        )

        reference_source = (
            "INTERNAL_HIGH"
            if long_side
            else
            "INTERNAL_LOW"
        )

        confirmation = (
            "BREAKOUT_ACCEPTANCE"
            if family == "BREAK_ACCEPTANCE"
            else
            (
                "BULLISH_DISPLACEMENT"
                if long_side
                else
                "BEARISH_DISPLACEMENT"
            )
        )

        distance = (
            0.08
            if strong_band
            else
            0.30
        )

        if (
            long_side
            and
            strong_band
        ):
            net20 = 2.0
            positive = 1
            mfe = 4.0
            mae = 1.0

        elif long_side:
            net20 = -0.5
            positive = 0
            mfe = 2.0
            mae = 2.5

        elif strong_band:
            net20 = -1.0
            positive = 0
            mfe = 2.0
            mae = 3.0

        else:
            net20 = -2.0
            positive = 0
            mfe = 1.5
            mae = 4.0

        rows.append(
            {
                "direction": direction,

                "lei_entry_family": family,

                "lei_reference_source": (
                    reference_source
                ),

                "lei_confirmation_type": (
                    confirmation
                ),

                "first_distance_atr": (
                    distance
                ),

                "first_confidence_score": (
                    confidence
                ),

                "first_regime_state": (
                    "BULLISH_NORMAL_VOL"
                    if long_side
                    else
                    "BEARISH_NORMAL_VOL"
                ),

                "first_status": (
                    "MATURED_20"
                ),

                "first_net_5": (
                    net20 / 4.0
                ),

                "first_net_10": (
                    net20 / 2.0
                ),

                "first_net_20": (
                    net20
                ),

                "first_mfe_20": (
                    mfe
                ),

                "first_mae_20": (
                    mae
                ),

                "first_positive_20": (
                    positive
                ),
            }
        )

    return pd.DataFrame(
        rows
    )


def test_prepare_keeps_only_matured() -> None:

    frame = _episodes()

    extra = frame.iloc[
        [
            0
        ]
    ].copy()

    extra[
        "first_status"
    ] = "PARTIAL_5"

    combined = pd.concat(
        [
            frame,
            extra,
        ],
        ignore_index=True,
    )

    prepared = Profiler.prepare(
        combined
    )

    assert len(
        prepared
    ) == 40


def test_confidence_band_mapping() -> None:

    assert (
        Profiler._confidence_band(
            42
        )
        ==
        "<50"
    )

    assert (
        Profiler._confidence_band(
            55
        )
        ==
        "50-69"
    )

    assert (
        Profiler._confidence_band(
            75
        )
        ==
        "70-84"
    )

    assert (
        Profiler._confidence_band(
            90
        )
        ==
        "85+"
    )


def test_distance_band_mapping() -> None:

    assert (
        Profiler._distance_band(
            0.05
        )
        ==
        "<=0.10 ATR"
    )

    assert (
        Profiler._distance_band(
            0.20
        )
        ==
        "0.10-0.25 ATR"
    )

    assert (
        Profiler._distance_band(
            0.40
        )
        ==
        "0.25-0.50 ATR"
    )

    assert (
        Profiler._distance_band(
            0.80
        )
        ==
        ">0.50 ATR"
    )


def test_reference_class_mapping() -> None:

    assert (
        Profiler._reference_class(
            "MICRO_LOW"
        )
        ==
        "MICRO"
    )

    assert (
        Profiler._reference_class(
            "INTERNAL_HIGH"
        )
        ==
        "INTERNAL"
    )

    assert (
        Profiler._reference_class(
            "MAJOR_LOW"
        )
        ==
        "MAJOR"
    )

    assert (
        Profiler._reference_class(
            "PDH"
        )
        ==
        "HTF_CONTEXT"
    )


def test_single_direction_profile_counts_all_rows() -> None:

    result = Profiler.profile(
        _episodes(),
        dimensions=(
            "direction",
        ),
    )

    assert int(
        result[
            "n"
        ].sum()
    ) == 40


def test_long_70_84_profile_is_positive() -> None:

    result = Profiler.profile(
        _episodes(),
        dimensions=(
            "direction",
            "confidence_band",
        ),
        minimum_n=1,
    )

    target = result.loc[
        result[
            "profile_key"
        ].str.contains(
            "direction=LONG",
            regex=False,
        )
        &
        result[
            "profile_key"
        ].str.contains(
            "confidence_band=70-84",
            regex=False,
        )
    ]

    assert len(
        target
    ) == 1

    assert float(
        target.iloc[
            0
        ][
            "net20_med"
        ]
    ) > 0.0


def test_short_profiles_are_negative() -> None:

    result = Profiler.profile(
        _episodes(),
        dimensions=(
            "direction",
        ),
    )

    short = result.loc[
        result[
            "profile_key"
        ].str.contains(
            "direction=SHORT",
            regex=False,
        )
    ].iloc[
        0
    ]

    assert float(
        short[
            "net20_med"
        ]
    ) < 0.0


def test_minimum_n_removes_tiny_groups() -> None:

    result = Profiler.profile(
        _episodes(),
        dimensions=(
            "direction",
            "lei_entry_family",
        ),
        minimum_n=50,
    )

    assert result.empty


def test_direction_interactions_work() -> None:

    result = Profiler.direction_interactions(
        _episodes(),
        minimum_n=5,
    )

    assert not result.empty

    assert bool(
        result[
            "profile_dimensions"
        ]
        .str
        .startswith(
            "direction × "
        )
        .all()
    )


def test_three_way_profiles_work() -> None:

    result = Profiler.three_way_profiles(
        _episodes(),
        minimum_n=3,
    )

    assert not result.empty

    assert bool(
        result[
            "profile_dimensions"
        ]
        .str
        .startswith(
            "direction × confidence_band × "
        )
        .all()
    )


def test_evidence_shortlist_is_research_only_positive_subset() -> None:

    profiles = Profiler.profile(
        _episodes(),
        dimensions=(
            "direction",
            "confidence_band",
        ),
        minimum_n=1,
    )

    shortlist = Profiler.evidence_shortlist(
        profiles,
        minimum_n=5,
    )

    assert not shortlist.empty

    assert bool(
        pd.to_numeric(
            shortlist[
                "net20_med"
            ],
            errors="coerce",
        )
        .gt(
            0.0
        )
        .all()
    )

    assert bool(
        pd.to_numeric(
            shortlist[
                "positive20_pct"
            ],
            errors="coerce",
        )
        .gt(
            50.0
        )
        .all()
    )