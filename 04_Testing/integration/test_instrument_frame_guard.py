from __future__ import annotations

from importlib import import_module

import pandas as pd
import pytest


context_module = import_module(
    "02_AI.Common.instrument_context"
)

guard_module = import_module(
    "02_AI.Dataset.instrument_frame_guard"
)

Definition = (
    context_module.InstrumentDefinition
)

Context = (
    context_module.InstrumentContext
)

IsolationError = (
    context_module.InstrumentIsolationError
)

Guard = (
    guard_module.InstrumentFrameGuard
)


def context(
    symbol: str = "XAUUSD",
    asset: str = "METAL",
    broker_symbol: str = "XAUUSDm",
):

    return Context(
        definition=Definition(
            symbol,
            asset,
            (
                broker_symbol,
            ),
            "1",
        ),
        broker_id="EXNESS",
        broker_symbol=broker_symbol,
        account_scope_id="PRIMARY_DEMO",
        execution_environment="DEMO",
        contract_spec_id=(
            f"EXNESS_{symbol}_V1"
        ),
        data_schema_version="MARKET_V1",
        feature_contract_version="FEATURES_V1",
    )


def frame():

    return pd.DataFrame(
        {
            "time": [
                1,
                2,
            ],
            "close": [
                100.0,
                101.0,
            ],
        }
    )


def test_stamp_adds_complete_identity_without_modifying_input():

    source = frame()

    original = source.copy(
        deep=True
    )

    guard = Guard(
        context()
    )

    stamped = guard.stamp(
        source
    )

    pd.testing.assert_frame_equal(
        source,
        original,
    )

    for column in guard.IDENTITY_COLUMNS:

        assert (
            column
            in
            stamped.columns
        )

    guard.validate(
        stamped
    )


def test_stamp_empty_frame_still_creates_identity_schema():

    guard = Guard(
        context()
    )

    result = guard.stamp(
        pd.DataFrame(
            columns=[
                "time",
                "close",
            ]
        )
    )

    assert result.empty

    guard.validate(
        result
    )


def test_validate_requires_identity_columns():

    with pytest.raises(
        IsolationError,
        match="COLUMNS_MISSING",
    ):

        Guard(
            context()
        ).validate(
            frame()
        )


def test_partial_identity_columns_fail_closed():

    source = frame()

    source[
        "pv_canonical_symbol"
    ] = "XAUUSD"

    with pytest.raises(
        IsolationError,
        match="PARTIAL",
    ):

        Guard(
            context()
        ).stamp(
            source
        )


def test_single_foreign_row_is_detected():

    guard = Guard(
        context()
    )

    stamped = guard.stamp(
        frame()
    )

    stamped.loc[
        1,
        "pv_canonical_symbol",
    ] = "BTCUSD"

    with pytest.raises(
        IsolationError,
        match="pv_canonical_symbol",
    ):

        guard.validate(
            stamped
        )


def test_broker_symbol_is_exact_not_silently_normalized():

    guard = Guard(
        context()
    )

    stamped = guard.stamp(
        frame()
    )

    stamped.loc[
        0,
        "pv_broker_symbol",
    ] = "XAUUSDM"

    with pytest.raises(
        IsolationError,
        match="pv_broker_symbol",
    ):

        guard.validate(
            stamped
        )


def test_xau_guard_rejects_btc_frame():

    xau_guard = Guard(
        context()
    )

    btc_guard = Guard(
        context(
            "BTCUSD",
            "CRYPTO",
            "BTCUSDm",
        )
    )

    btc_frame = btc_guard.stamp(
        frame()
    )

    with pytest.raises(
        IsolationError,
        match="IDENTITY_MISMATCH",
    ):

        xau_guard.validate(
            btc_frame
        )


def test_concat_accepts_only_same_exact_context():

    guard = Guard(
        context()
    )

    first = guard.stamp(
        pd.DataFrame(
            {
                "close": [
                    100.0,
                ]
            }
        )
    )

    second = guard.stamp(
        pd.DataFrame(
            {
                "close": [
                    101.0,
                ]
            }
        )
    )

    combined = guard.concat(
        [
            first,
            second,
        ]
    )

    assert (
        combined[
            "close"
        ].tolist()
        ==
        [
            100.0,
            101.0,
        ]
    )

    guard.validate(
        combined
    )


def test_concat_rejects_cross_symbol_contamination():

    xau_guard = Guard(
        context()
    )

    btc_guard = Guard(
        context(
            "BTCUSD",
            "CRYPTO",
            "BTCUSDm",
        )
    )

    xau = xau_guard.stamp(
        pd.DataFrame(
            {
                "close": [
                    4300.0,
                ]
            }
        )
    )

    btc = btc_guard.stamp(
        pd.DataFrame(
            {
                "close": [
                    60000.0,
                ]
            }
        )
    )

    with pytest.raises(
        IsolationError,
        match="IDENTITY_MISMATCH",
    ):

        xau_guard.concat(
            [
                xau,
                btc,
            ]
        )


def test_concat_empty_returns_stamped_empty_frame():

    guard = Guard(
        context()
    )

    combined = guard.concat(
        []
    )

    assert combined.empty

    guard.validate(
        combined
    )


def test_require_nonempty_is_fail_closed():

    guard = Guard(
        context()
    )

    empty = guard.stamp(
        pd.DataFrame()
    )

    with pytest.raises(
        IsolationError,
        match="FRAME_EMPTY",
    ):

        guard.validate(
            empty,
            require_nonempty=True,
        )