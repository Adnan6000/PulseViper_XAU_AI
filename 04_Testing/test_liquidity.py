from pathlib import Path
import sys
import importlib

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


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