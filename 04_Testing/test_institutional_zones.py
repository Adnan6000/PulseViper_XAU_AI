from __future__ import annotations

import importlib

import pandas as pd
import pytest


MODULE = "02_AI.Core.institutional_zones"


def _load_module():
    return importlib.import_module(MODULE)


def test_institutional_zones_import():
    module = _load_module()

    assert hasattr(module, "InstitutionalZone")
    assert hasattr(module, "InstitutionalZonesEngine")
    assert hasattr(module, "institutional_zones")


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

    with pytest.raises(ValueError):
        engine.generate(data)


def test_invalid_input_type():
    module = _load_module()

    engine = module.InstitutionalZonesEngine()

    with pytest.raises(TypeError):
        engine.generate([1, 2, 3])


def test_empty_dataframe():
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

    result = engine.generate(data)

    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_bullish_institutional_zone():
    module = _load_module()

    engine = module.InstitutionalZonesEngine(
        {
            "min_displacement_score": 20.0,
        }
    )

    data = pd.DataFrame(
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

    result = engine.generate(data)

    assert not result.empty
    assert "BULLISH" in result["direction"].tolist()
    assert "DEMAND" in result["zone_type"].tolist()


def test_bearish_institutional_zone():
    module = _load_module()

    engine = module.InstitutionalZonesEngine(
        {
            "min_displacement_score": 20.0,
        }
    )

    data = pd.DataFrame(
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

    result = engine.generate(data)

    assert not result.empty
    assert "BEARISH" in result["direction"].tolist()
    assert "SUPPLY" in result["zone_type"].tolist()


def test_zone_values_are_valid():
    module = _load_module()

    engine = module.InstitutionalZonesEngine(
        {
            "min_displacement_score": 20.0,
        }
    )

    data = pd.DataFrame(
        {
            "open": [100, 98, 101, 104, 106],
            "high": [101, 100, 104, 107, 108],
            "low": [99, 96, 100, 103, 105],
            "close": [100, 97, 103, 106, 107],
        }
    )

    result = engine.generate(data)

    if result.empty:
        pytest.fail("Expected at least one institutional zone.")

    assert (result["high"] > result["low"]).all()
    assert (result["size"] > 0).all()
    assert (result["midpoint"] > result["low"]).all()
    assert (result["midpoint"] < result["high"]).all()

    assert (
        result["strength"].between(0, 100).all()
    )

    assert (
        result["displacement_score"]
        .between(0, 100)
        .all()
    )


def test_strength_is_clamped():
    module = _load_module()

    engine = module.InstitutionalZonesEngine(
        {
            "min_displacement_score": 0.0,
        }
    )

    data = pd.DataFrame(
        {
            "open": [100, 98, 101, 104, 106],
            "high": [101, 100, 104, 107, 108],
            "low": [99, 96, 100, 103, 105],
            "close": [100, 97, 103, 106, 107],
        }
    )

    result = engine.generate(data)

    if result.empty:
        pytest.fail("Expected zones.")

    assert result["strength"].min() >= 0
    assert result["strength"].max() <= 100


def test_generate_does_not_modify_input():
    module = _load_module()

    engine = module.InstitutionalZonesEngine(
        {
            "min_displacement_score": 20.0,
        }
    )

    data = pd.DataFrame(
        {
            "open": [100, 98, 101, 104, 106],
            "high": [101, 100, 104, 107, 108],
            "low": [99, 96, 100, 103, 105],
            "close": [100, 97, 103, 106, 107],
        }
    )

    original = data.copy(deep=True)

    engine.generate(data)

    pd.testing.assert_frame_equal(
        data,
        original,
    )


def test_generate_alias_matches_detect():
    module = _load_module()

    engine = module.InstitutionalZonesEngine(
        {
            "min_displacement_score": 20.0,
        }
    )

    data = pd.DataFrame(
        {
            "open": [100, 98, 101, 104, 106],
            "high": [101, 100, 104, 107, 108],
            "low": [99, 96, 100, 103, 105],
            "close": [100, 97, 103, 106, 107],
        }
    )

    detected = engine.detect(data)
    generated = engine.generate(data)

    pd.testing.assert_frame_equal(
        detected.reset_index(drop=True),
        generated.reset_index(drop=True),
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

    assert isinstance(result, dict)
    assert result["direction"] == "BULLISH"
    assert result["zone_type"] == "DEMAND"
    assert result["strength"] == 75.0


def test_invalid_config():
    module = _load_module()

    with pytest.raises(ValueError):
        module.InstitutionalZonesEngine(
            {
                "min_body_ratio": -1,
            }
        )

    with pytest.raises(ValueError):
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
            "open": [100, 100.0, 101, 102],
            "high": [105, 105, 105, 106],
            "low": [95, 95, 99, 101],
            "close": [100.1, 100.1, 104, 105],
        }
    )

    result = engine.generate(data)

    assert result.empty