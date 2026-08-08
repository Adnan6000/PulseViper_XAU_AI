from __future__ import annotations

import importlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(ROOT_DIR) not in sys.path:

    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


# =============================================================================
# Modules
# =============================================================================

def _modules():

    liquidity_module = importlib.import_module(
        "02_AI.Core.liquidity_engine"
    )

    sweep_module = importlib.import_module(
        "02_AI.Core.liquidity_sweep_engine"
    )

    memory_module = importlib.import_module(
        "02_AI.Memory.liquidity_memory"
    )

    types_module = importlib.import_module(
        "02_AI.Common.types"
    )

    enums_module = importlib.import_module(
        "02_AI.Common.enums"
    )

    return (
        liquidity_module,
        sweep_module,
        memory_module,
        types_module,
        enums_module,
    )


# =============================================================================
# Helper DataFrame
# =============================================================================

def _frame(
    high,
    low,
    close,
    buy_liquidity=None,
    sell_liquidity=None,
    eqh_price=None,
    eql_price=None,
):

    size = len(
        high
    )

    if buy_liquidity is None:

        buy_liquidity = [
            0
        ] * size

    if sell_liquidity is None:

        sell_liquidity = [
            0
        ] * size

    if eqh_price is None:

        eqh_price = [
            np.nan
        ] * size

    if eql_price is None:

        eql_price = [
            np.nan
        ] * size

    return pd.DataFrame(
        {
            "high": high,
            "low": low,
            "close": close,

            "buy_side_liquidity": (
                buy_liquidity
            ),

            "sell_side_liquidity": (
                sell_liquidity
            ),

            "eqh_price": (
                eqh_price
            ),

            "eql_price": (
                eql_price
            ),
        }
    )


# =============================================================================
# MT5 Integration Contract
# =============================================================================

def test_liquidity_sweep():

    (
        liquidity_module,
        sweep_module,
        _,
        _,
        _,
    ) = _modules()

    fetcher = importlib.import_module(
        "02_AI.Dataset.data_fetcher"
    ).fetcher

    liquidity_engine = (
        liquidity_module
        .liquidity_engine
    )

    df = fetcher.fetch(
        bars=1000
    )

    assert df is not None
    assert len(df) > 0

    df = (
        liquidity_engine
        .generate(
            df
        )
    )

    engine = (
        sweep_module
        .LiquiditySweepEngine(
            sweep_buffer=0.05,
            memory=(
                liquidity_engine
                .memory
            ),
        )
    )

    result = engine.generate(
        df
    )

    required = [
        "buy_side_sweep",
        "sell_side_sweep",

        "bullish_sweep",
        "bearish_sweep",

        "liquidity_sweep",
        "liquidity_swept",

        "sweep_price",
        "sweep_liquidity_id",

        "causal_liquidity_id",
    ]

    for column in required:

        assert (
            column
            in result.columns
        )

    assert len(result) > 0


# =============================================================================
# Buy-Side Sweep = Bearish Raid
# =============================================================================

def test_buy_side_sweep_is_bearish():

    (
        _,
        sweep_module,
        memory_module,
        _,
        _,
    ) = _modules()

    memory = (
        memory_module
        .LiquidityMemory()
    )

    df = _frame(
        high=[
            100.20,
            100.20,
        ],
        low=[
            99.50,
            99.20,
        ],
        close=[
            99.80,
            99.80,
        ],
        buy_liquidity=[
            1,
            0,
        ],
        eqh_price=[
            100.0,
            np.nan,
        ],
    )

    engine = (
        sweep_module
        .LiquiditySweepEngine(
            sweep_buffer=0.05,
            memory=memory,
        )
    )

    result = engine.generate(
        df
    )

    # Creation candle cannot sweep itself.
    assert (
        result.loc[
            0,
            "buy_side_sweep",
        ]
        == 0
    )

    # Next candle raids above 100
    # and closes back below.
    assert (
        result.loc[
            1,
            "buy_side_sweep",
        ]
        == 1
    )

    assert (
        result.loc[
            1,
            "bearish_sweep",
        ]
        == 1
    )

    assert (
        result.loc[
            1,
            "bullish_sweep",
        ]
        == 0
    )

    assert (
        result.loc[
            1,
            "liquidity_sweep",
        ]
        == 1
    )

    assert (
        result.loc[
            1,
            "liquidity_swept",
        ]
        == 1
    )


# =============================================================================
# Sell-Side Sweep = Bullish Raid
# =============================================================================

def test_sell_side_sweep_is_bullish():

    (
        _,
        sweep_module,
        memory_module,
        _,
        _,
    ) = _modules()

    memory = (
        memory_module
        .LiquidityMemory()
    )

    df = _frame(
        high=[
            100.50,
            100.80,
        ],
        low=[
            99.80,
            99.80,
        ],
        close=[
            100.20,
            100.20,
        ],
        sell_liquidity=[
            1,
            0,
        ],
        eql_price=[
            100.0,
            np.nan,
        ],
    )

    engine = (
        sweep_module
        .LiquiditySweepEngine(
            sweep_buffer=0.05,
            memory=memory,
        )
    )

    result = engine.generate(
        df
    )

    assert (
        result.loc[
            0,
            "sell_side_sweep",
        ]
        == 0
    )

    assert (
        result.loc[
            1,
            "sell_side_sweep",
        ]
        == 1
    )

    assert (
        result.loc[
            1,
            "bullish_sweep",
        ]
        == 1
    )

    assert (
        result.loc[
            1,
            "bearish_sweep",
        ]
        == 0
    )


# =============================================================================
# Future Liquidity Must Not Leak Backward
# =============================================================================

def test_future_liquidity_cannot_affect_past():

    (
        _,
        sweep_module,
        memory_module,
        types_module,
        enums_module,
    ) = _modules()

    memory = (
        memory_module
        .LiquidityMemory()
    )

    # Poison the memory intentionally with a
    # future level before replay starts.
    future_liquidity = (
        types_module
        .Liquidity(
            liquidity_id=(
                memory.generate_id()
            ),
            liquidity_type=(
                enums_module
                .LiquidityType
                .BUY_SIDE
            ),
            price=100.0,
            touches=1,
            first_index=10,
            last_index=10,
        )
    )

    memory.register(
        future_liquidity
    )

    df = _frame(
        high=[
            101.0,
            101.0,
            100.2,
            100.2,
        ],
        low=[
            99.0,
            99.0,
            99.5,
            99.0,
        ],
        close=[
            99.0,
            99.0,
            99.8,
            99.8,
        ],
        buy_liquidity=[
            0,
            0,
            1,
            0,
        ],
        eqh_price=[
            np.nan,
            np.nan,
            100.0,
            np.nan,
        ],
    )

    engine = (
        sweep_module
        .LiquiditySweepEngine(
            sweep_buffer=0.05,
            memory=memory,
        )
    )

    result = engine.generate(
        df,
        reset_memory=True,
    )

    # Poisoned future memory is discarded.
    assert (
        result.loc[
            0,
            "buy_side_sweep",
        ]
        == 0
    )

    assert (
        result.loc[
            1,
            "buy_side_sweep",
        ]
        == 0
    )

    # Level is confirmed here,
    # but cannot sweep itself.
    assert (
        result.loc[
            2,
            "buy_side_sweep",
        ]
        == 0
    )

    # First legitimate post-confirmation sweep.
    assert (
        result.loc[
            3,
            "buy_side_sweep",
        ]
        == 1
    )


# =============================================================================
# Swept Pool Can Form Again Later
# =============================================================================

def test_swept_level_can_reform_and_sweep_again():

    (
        _,
        sweep_module,
        memory_module,
        _,
        _,
    ) = _modules()

    memory = (
        memory_module
        .LiquidityMemory()
    )

    df = _frame(
        high=[
            100.00,
            100.20,
            100.00,
            100.20,
        ],
        low=[
            99.50,
            99.20,
            99.50,
            99.20,
        ],
        close=[
            99.90,
            99.80,
            99.90,
            99.80,
        ],
        buy_liquidity=[
            1,
            0,
            1,
            0,
        ],
        eqh_price=[
            100.0,
            np.nan,
            100.0,
            np.nan,
        ],
    )

    engine = (
        sweep_module
        .LiquiditySweepEngine(
            sweep_buffer=0.05,
            memory=memory,
        )
    )

    result = engine.generate(
        df
    )

    assert int(
        result[
            "buy_side_sweep"
        ].sum()
    ) == 2

    assert (
        result.loc[
            1,
            "buy_side_sweep",
        ]
        == 1
    )

    assert (
        result.loc[
            3,
            "buy_side_sweep",
        ]
        == 1
    )

    assert (
        memory.swept_count()
        == 2
    )


# =============================================================================
# Missing Candidate Contract
# =============================================================================

def test_missing_liquidity_candidate_columns_raise():

    (
        _,
        sweep_module,
        _,
        _,
        _,
    ) = _modules()

    df = pd.DataFrame(
        {
            "high": [100.0],
            "low": [99.0],
            "close": [99.5],
        }
    )

    engine = (
        sweep_module
        .LiquiditySweepEngine()
    )

    try:

        engine.generate(
            df
        )

    except ValueError as exc:

        message = str(
            exc
        )

        assert (
            "buy_side_liquidity"
            in message
        )

    else:

        raise AssertionError(
            "Expected ValueError"
        )