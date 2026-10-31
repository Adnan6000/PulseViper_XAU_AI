from __future__ import annotations

import importlib

import pandas as pd
import pytest


MODULE = "02_AI.Core.institutional_zones"


def _load_module():
    return importlib.import_module(MODULE)


def _bullish_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open": [
                100.0,
                98.0,
                101.0,
                104.0,
                106.0,
            ],
            "high": [
                101.0,
                100.0,
                104.0,
                107.0,
                108.0,
            ],
            "low": [
                99.0,
                96.0,
                100.0,
                103.0,
                105.0,
            ],
            "close": [
                100.0,
                97.0,
                103.0,
                106.0,
                107.0,
            ],
        }
    )


def _bearish_data() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "open": [
                100.0,
                102.0,
                99.0,
                96.0,
                94.0,
            ],
            "high": [
                101.0,
                104.0,
                100.0,
                97.0,
                95.0,
            ],
            "low": [
                99.0,
                101.0,
                98.0,
                94.0,
                93.0,
            ],
            "close": [
                100.0,
                103.0,
                99.0,
                95.0,
                94.0,
            ],
        }
    )


def test_institutional_zones_import():
    module = _load_module()

    assert hasattr(
        module,
        "InstitutionalZone",
    )

    assert hasattr(
        module,
        "InstitutionalZonesEngine",
    )

    assert hasattr(
        module,
        "institutional_zones",
    )


def test_default_engine():
    module = _load_module()

    engine = module.institutional_zones

    assert isinstance(
        engine,
        module.InstitutionalZonesEngine,
    )


def test_missing_required_columns():
    module = _load_module()

    engine = module.InstitutionalZonesEngine()

    data = pd.DataFrame(
        {
            "open": [100.0],
            "high": [105.0],
            "close": [103.0],
        }
    )

    with pytest.raises(
        ValueError
    ):
        engine.generate(
            data
        )


def test_invalid_input_type():
    module = _load_module()

    engine = module.InstitutionalZonesEngine()

    with pytest.raises(
        TypeError
    ):
        engine.generate(
            [1, 2, 3]
        )


def test_empty_dataframe_returns_causal_schema():
    module = _load_module()

    engine = module.InstitutionalZonesEngine()

    data = pd.DataFrame(
        columns=[
            "open",
            "high",
            "low",
            "close",
        ]
    )

    result = engine.generate(
        data
    )

    assert isinstance(
        result,
        pd.DataFrame,
    )

    assert result.empty

    assert list(
        result.columns
    ) == list(
        engine.CAUSAL_OUTPUT_COLUMNS
    )


def test_bullish_institutional_zone():
    module = _load_module()

    engine = module.InstitutionalZonesEngine(
        {
            "min_displacement_score": 20.0,
        }
    )

    result = engine.generate(
        _bullish_data()
    )

    assert not result.empty

    assert (
        "BULLISH"
        in
        result[
            "iz_direction"
        ].tolist()
    )

    assert (
        "DEMAND"
        in
        result[
            "iz_zone_type"
        ].tolist()
    )

    assert bool(
        result[
            "iz_live_safe"
        ]
        .eq(
            1
        )
        .all()
    )

    assert bool(
        result[
            "iz_mode"
        ]
        .eq(
            engine.CAUSAL_MODE
        )
        .all()
    )

    assert bool(
        (
            result[
                "iz_confirmation_position"
            ]
            >
            result[
                "iz_origin_position"
            ]
        ).all()
    )


def test_bearish_institutional_zone():
    module = _load_module()

    engine = module.InstitutionalZonesEngine(
        {
            "min_displacement_score": 20.0,
        }
    )

    result = engine.generate(
        _bearish_data()
    )

    assert not result.empty

    assert (
        "BEARISH"
        in
        result[
            "iz_direction"
        ].tolist()
    )

    assert (
        "SUPPLY"
        in
        result[
            "iz_zone_type"
        ].tolist()
    )

    assert bool(
        result[
            "iz_live_safe"
        ]
        .eq(
            1
        )
        .all()
    )

    assert bool(
        (
            result[
                "iz_confirmation_position"
            ]
            >
            result[
                "iz_origin_position"
            ]
        ).all()
    )


def test_causal_zone_values_are_valid():
    module = _load_module()

    engine = module.InstitutionalZonesEngine(
        {
            "min_displacement_score": 20.0,
        }
    )

    result = engine.generate(
        _bullish_data()
    )

    if result.empty:
        pytest.fail(
            "Expected at least one causal institutional-zone event."
        )

    assert bool(
        (
            result[
                "iz_zone_high"
            ]
            >
            result[
                "iz_zone_low"
            ]
        ).all()
    )

    assert bool(
        (
            result[
                "iz_zone_size"
            ]
            >
            0.0
        ).all()
    )

    assert bool(
        (
            result[
                "iz_zone_midpoint"
            ]
            >
            result[
                "iz_zone_low"
            ]
        ).all()
    )

    assert bool(
        (
            result[
                "iz_zone_midpoint"
            ]
            <
            result[
                "iz_zone_high"
            ]
        ).all()
    )

    assert bool(
        result[
            "iz_strength"
        ]
        .between(
            0.0,
            100.0,
        )
        .all()
    )

    assert bool(
        result[
            "iz_displacement_score"
        ]
        .between(
            0.0,
            100.0,
        )
        .all()
    )


def test_causal_strength_is_clamped():
    module = _load_module()

    engine = module.InstitutionalZonesEngine(
        {
            "min_displacement_score": 0.0,
        }
    )

    result = engine.generate(
        _bullish_data()
    )

    if result.empty:
        pytest.fail(
            "Expected causal institutional-zone events."
        )

    assert (
        result[
            "iz_strength"
        ].min()
        >=
        0.0
    )

    assert (
        result[
            "iz_strength"
        ].max()
        <=
        100.0
    )


def test_generate_does_not_modify_input():
    module = _load_module()

    engine = module.InstitutionalZonesEngine(
        {
            "min_displacement_score": 20.0,
        }
    )

    data = _bullish_data()

    original = data.copy(
        deep=True
    )

    engine.generate(
        data
    )

    pd.testing.assert_frame_equal(
        data,
        original,
    )


def test_generate_alias_matches_generate_causal():
    module = _load_module()

    engine = module.InstitutionalZonesEngine(
        {
            "min_displacement_score": 20.0,
        }
    )

    data = _bullish_data()

    generated = engine.generate(
        data
    )

    causal = engine.generate_causal(
        data
    )

    pd.testing.assert_frame_equal(
        generated.reset_index(
            drop=True
        ),
        causal.reset_index(
            drop=True
        ),
    )


def test_detect_preserves_explicit_retrospective_legacy_schema():
    module = _load_module()

    engine = module.InstitutionalZonesEngine(
        {
            "min_displacement_score": 20.0,
        }
    )

    result = engine.detect(
        _bullish_data()
    )

    assert list(
        result.columns
    ) == list(
        engine.OUTPUT_COLUMNS
    )

    assert not any(
        str(
            column
        ).startswith(
            "iz_"
        )
        for column
        in result.columns
    )

    if not result.empty:

        assert bool(
            result[
                "strength"
            ]
            .between(
                0.0,
                100.0,
            )
            .all()
        )

        assert bool(
            (
                result[
                    "high"
                ]
                >
                result[
                    "low"
                ]
            ).all()
        )


def test_generate_research_is_explicit_hindsight_namespace():
    module = _load_module()

    engine = module.InstitutionalZonesEngine(
        {
            "min_displacement_score": 20.0,
        }
    )

    result = engine.generate_research(
        _bullish_data()
    )

    assert all(
        str(
            column
        ).startswith(
            "izlabel_"
        )
        for column
        in result.columns
    )

    assert (
        "izlabel_live_safe"
        in
        result.columns
    )

    assert (
        "izlabel_mode"
        in
        result.columns
    )

    if not result.empty:

        assert bool(
            result[
                "izlabel_live_safe"
            ]
            .eq(
                0
            )
            .all()
        )

        assert bool(
            result[
                "izlabel_mode"
            ]
            .eq(
                engine.RESEARCH_MODE
            )
            .all()
        )


def test_zone_dataclass_to_dict():
    module = _load_module()

    zone = module.InstitutionalZone(
        zone_id=1,
        direction="BULLISH",
        zone_type="DEMAND",
        index=1,
        high=100.0,
        low=98.0,
        midpoint=99.0,
        size=2.0,
        candle_open=99.0,
        candle_close=98.0,
        candle_high=100.0,
        candle_low=97.0,
        body_ratio=0.5,
        displacement_score=80.0,
        strength=75.0,
        active=True,
    )

    result = zone.to_dict()

    assert isinstance(
        result,
        dict,
    )

    assert (
        result[
            "direction"
        ]
        ==
        "BULLISH"
    )

    assert (
        result[
            "zone_type"
        ]
        ==
        "DEMAND"
    )

    assert (
        result[
            "strength"
        ]
        ==
        75.0
    )


def test_invalid_config():
    module = _load_module()

    with pytest.raises(
        ValueError
    ):
        module.InstitutionalZonesEngine(
            {
                "min_body_ratio": -1,
            }
        )

    with pytest.raises(
        ValueError
    ):
        module.InstitutionalZonesEngine(
            {
                "lookahead": 0,
            }
        )


def test_no_false_zone_from_small_body():
    module = _load_module()

    engine = module.InstitutionalZonesEngine(
        {
            "min_body_ratio": 0.90,
            "min_displacement_score": 20.0,
        }
    )

    data = pd.DataFrame(
        {
            "open": [
                100,
                100.0,
                101,
                102,
            ],
            "high": [
                105,
                105,
                105,
                106,
            ],
            "low": [
                95,
                95,
                99,
                101,
            ],
            "close": [
                100.1,
                100.1,
                104,
                105,
            ],
        }
    )

    result = engine.generate(
        data
    )

    assert result.empty