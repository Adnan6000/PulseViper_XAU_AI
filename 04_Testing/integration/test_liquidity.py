from __future__ import annotations

import importlib


fetcher = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
).fetcher

liquidity_module = importlib.import_module(
    "02_AI.Core.liquidity_engine"
)

liquidity_engine = (
    liquidity_module.liquidity_engine
)


def test_liquidity():

    df = fetcher.fetch(
        bars=1000
    )

    result = liquidity_engine.generate(
        df
    )

    required_columns = [
        "equal_high",
        "equal_low",
        "eqh_price",
        "eql_price",
        "buy_side_liquidity",
        "sell_side_liquidity",
        "liquidity_id",
    ]

    for column in required_columns:

        assert column in result.columns

    assert len(result) > 0

    active = (
        liquidity_engine
        .get_active_liquidity()
    )

    assert isinstance(
        active,
        list
    )