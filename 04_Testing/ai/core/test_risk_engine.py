from __future__ import annotations

import importlib


def get_engine():
    module = importlib.import_module(
        "02_AI.Core.risk_engine"
    )
    return module.risk_engine


def test_risk_engine_import():
    engine = get_engine()

    assert engine is not None
    assert type(engine).__name__ == "RiskEngine"


def test_risk_amount():
    engine = get_engine()

    risk = engine.calculate_risk_amount(
        account_balance=1000.0,
        risk_percent=1.0,
    )

    assert risk == 10.0


def test_position_size():
    engine = get_engine()

    size = engine.calculate_position_size(
        account_balance=1000.0,
        entry_price=2000.0,
        stop_loss=1990.0,
        risk_percent=1.0,
        value_per_price_unit=1.0,
    )

    assert size == 1.0


def test_buy_stop_loss():
    engine = get_engine()

    assert engine.validate_stop_loss(
        "BUY",
        2000.0,
        1990.0,
    )

    assert not engine.validate_stop_loss(
        "BUY",
        2000.0,
        2010.0,
    )


def test_sell_stop_loss():
    engine = get_engine()

    assert engine.validate_stop_loss(
        "SELL",
        2000.0,
        2010.0,
    )

    assert not engine.validate_stop_loss(
        "SELL",
        2000.0,
        1990.0,
    )


def test_buy_take_profit():
    engine = get_engine()

    assert engine.validate_take_profit(
        "BUY",
        2000.0,
        2020.0,
    )

    assert not engine.validate_take_profit(
        "BUY",
        2000.0,
        1980.0,
    )


def test_sell_take_profit():
    engine = get_engine()

    assert engine.validate_take_profit(
        "SELL",
        2000.0,
        1980.0,
    )

    assert not engine.validate_take_profit(
        "SELL",
        2000.0,
        2020.0,
    )


def test_buy_risk_reward():
    engine = get_engine()

    ratio = engine.calculate_risk_reward(
        direction="BUY",
        entry_price=2000.0,
        stop_loss=1990.0,
        take_profit=2020.0,
    )

    assert ratio == 2.0


def test_sell_risk_reward():
    engine = get_engine()

    ratio = engine.calculate_risk_reward(
        direction="SELL",
        entry_price=2000.0,
        stop_loss=2010.0,
        take_profit=1980.0,
    )

    assert ratio == 2.0


def test_confidence_risk_adjustment():
    engine = get_engine()

    low = engine.calculate_risk_percent(
        confidence_score=40.0,
    )

    medium = engine.calculate_risk_percent(
        confidence_score=70.0,
    )

    high = engine.calculate_risk_percent(
        confidence_score=90.0,
    )

    assert low == 0.0
    assert medium == 0.75
    assert high == 1.0


def test_invalid_direction():
    engine = get_engine()

    result = engine.assess_trade(
        account_balance=1000.0,
        direction="INVALID",
        entry_price=2000.0,
        stop_loss=1990.0,
        take_profit=2020.0,
        confidence_score=90.0,
    )

    assert result.valid is False
    assert result.reason == "Invalid trade direction"


def test_invalid_stop_loss():
    engine = get_engine()

    result = engine.assess_trade(
        account_balance=1000.0,
        direction="BUY",
        entry_price=2000.0,
        stop_loss=2010.0,
        take_profit=2020.0,
        confidence_score=90.0,
    )

    assert result.valid is False
    assert result.reason == "Invalid stop loss"


def test_low_confidence_blocks_trade():
    engine = get_engine()

    result = engine.assess_trade(
        account_balance=1000.0,
        direction="BUY",
        entry_price=2000.0,
        stop_loss=1990.0,
        take_profit=2020.0,
        confidence_score=40.0,
    )

    assert result.valid is False
    assert result.position_size == 0.0


def test_complete_buy_assessment():
    engine = get_engine()

    result = engine.assess_trade(
        account_balance=1000.0,
        direction="BUY",
        entry_price=2000.0,
        stop_loss=1990.0,
        take_profit=2020.0,
        confidence_score=90.0,
    )

    assert result.valid is True
    assert result.risk_amount == 10.0
    assert result.risk_percent == 1.0
    assert result.stop_distance == 10.0
    assert result.reward_distance == 20.0
    assert result.risk_reward_ratio == 2.0
    assert result.position_size == 1.0


def test_complete_sell_assessment():
    engine = get_engine()

    result = engine.assess_trade(
        account_balance=1000.0,
        direction="SELL",
        entry_price=2000.0,
        stop_loss=2010.0,
        take_profit=1980.0,
        confidence_score=90.0,
    )

    assert result.valid is True
    assert result.risk_amount == 10.0
    assert result.risk_percent == 1.0
    assert result.stop_distance == 10.0
    assert result.reward_distance == 20.0
    assert result.risk_reward_ratio == 2.0
    assert result.position_size == 1.0