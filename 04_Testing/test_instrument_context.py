from __future__ import annotations

from importlib import import_module
from pathlib import Path

import pytest


module = import_module(
    "02_AI.Common.instrument_context"
)

Definition = (
    module.InstrumentDefinition
)

Context = (
    module.InstrumentContext
)

IsolationError = (
    module.InstrumentIsolationError
)


def definition(
    symbol: str = "XAUUSD",
    asset: str = "METAL",
    aliases: tuple[
        str,
        ...,
    ] = (
        "XAUUSDm",
    ),
):
    return Definition(
        symbol,
        asset,
        aliases,
        "1",
    )


def context(
    **overrides,
):
    values = {
        "definition": definition(),
        "broker_id": "EXNESS",
        "broker_symbol": "XAUUSDm",
        "account_scope_id": "PRIMARY_DEMO",
        "execution_environment": "DEMO",
        "contract_spec_id": (
            "EXNESS_XAUUSD_STANDARD_V1"
        ),
        "data_schema_version": "MARKET_V1",
        "feature_contract_version": (
            "FEATURES_V1"
        ),
    }

    values.update(
        overrides
    )

    return Context(
        **values
    )


def test_definition_normalizes_canonical_identity():

    item = Definition(
        "xauusd",
        "metal",
        (
            "XAUUSDm",
            "GOLDm",
        ),
        "v1",
    )

    assert (
        item.canonical_symbol
        ==
        "XAUUSD"
    )

    assert (
        item.asset_class
        ==
        "METAL"
    )

    assert (
        item.definition_version
        ==
        "V1"
    )

    assert (
        item.broker_symbols
        ==
        (
            "GOLDm",
            "XAUUSDm",
        )
    )


def test_definition_requires_explicit_broker_aliases():

    with pytest.raises(
        IsolationError,
        match="ALIASES_REQUIRED",
    ):

        Definition(
            "XAUUSD",
            "METAL",
            (),
        )


def test_definition_rejects_duplicate_case_ambiguous_alias():

    with pytest.raises(
        IsolationError,
        match="AMBIGUOUS",
    ):

        Definition(
            "XAUUSD",
            "METAL",
            (
                "XAUUSDm",
                "xauusdm",
            ),
        )


def test_definition_fingerprint_is_order_independent():

    first = Definition(
        "XAUUSD",
        "METAL",
        (
            "XAUUSDm",
            "GOLDm",
        ),
    )

    second = Definition(
        "XAUUSD",
        "METAL",
        (
            "GOLDm",
            "XAUUSDm",
        ),
    )

    assert (
        first.fingerprint
        ==
        second.fingerprint
    )


def test_context_preserves_exact_broker_symbol():

    item = context()

    assert (
        item.canonical_symbol
        ==
        "XAUUSD"
    )

    assert (
        item.broker_symbol
        ==
        "XAUUSDm"
    )

    assert (
        item.live_authorized
        is False
    )


def test_wrong_broker_symbol_for_definition_fails_closed():

    with pytest.raises(
        IsolationError,
        match="NOT_ALLOWED",
    ):

        context(
            broker_symbol="BTCUSDm"
        )


def test_xau_and_btc_are_different_instrument_scopes():

    xau = context()

    btc = context(
        definition=definition(
            "BTCUSD",
            "CRYPTO",
            (
                "BTCUSDm",
            ),
        ),
        broker_symbol="BTCUSDm",
        contract_spec_id=(
            "EXNESS_BTCUSD_V1"
        ),
    )

    with pytest.raises(
        IsolationError,
        match="CROSS_INSTRUMENT",
    ):

        xau.assert_same_instrument(
            btc
        )


def test_same_instrument_different_account_passes_instrument_scope_only():

    first = context()

    second = context(
        account_scope_id=(
            "SECOND_DEMO"
        )
    )

    first.assert_same_instrument(
        second
    )

    first.assert_same_learning_scope(
        second
    )

    with pytest.raises(
        IsolationError,
        match="CROSS_EXECUTION",
    ):

        first.assert_same_execution_scope(
            second
        )


def test_demo_and_real_execution_scopes_are_separate():

    demo = context()

    real = context(
        execution_environment="REAL",
        account_scope_id="PRIMARY_REAL",
    )

    demo.assert_same_learning_scope(
        real
    )

    with pytest.raises(
        IsolationError,
        match="CROSS_EXECUTION",
    ):

        demo.assert_same_execution_scope(
            real
        )

    assert (
        real.live_authorized
        is False
    )


def test_feature_contract_change_separates_learning_scope():

    first = context()

    second = context(
        feature_contract_version=(
            "FEATURES_V2"
        )
    )

    with pytest.raises(
        IsolationError,
        match="CROSS_LEARNING",
    ):

        first.assert_same_learning_scope(
            second
        )


def test_contract_spec_change_separates_learning_scope():

    first = context()

    second = context(
        contract_spec_id=(
            "EXNESS_XAUUSD_RAW_V2"
        )
    )

    with pytest.raises(
        IsolationError,
        match="CROSS_LEARNING",
    ):

        first.assert_same_learning_scope(
            second
        )


def test_namespace_is_deterministic():

    item = context()

    first = item.namespace(
        "01_Data",
        "journals",
        scope="EXECUTION",
    )

    second = item.namespace(
        Path(
            "01_Data"
        ),
        "journals",
        scope="execution",
    )

    assert (
        first
        ==
        second
    )

    assert (
        first.parts[
            -5
        ]
        ==
        "Instruments"
    )

    assert (
        "XAUUSD"
        in first.parts
    )


def test_xau_and_btc_namespaces_cannot_collide():

    xau = context()

    btc = context(
        definition=definition(
            "BTCUSD",
            "CRYPTO",
            (
                "BTCUSDm",
            ),
        ),
        broker_symbol="BTCUSDm",
        contract_spec_id=(
            "EXNESS_BTCUSD_V1"
        ),
    )

    assert (
        xau.namespace(
            "01_Data",
            "raw",
            scope="INSTRUMENT",
        )
        !=
        btc.namespace(
            "01_Data",
            "raw",
            scope="INSTRUMENT",
        )
    )


def test_demo_and_real_execution_namespaces_cannot_collide():

    demo = context()

    real = context(
        execution_environment="REAL",
        account_scope_id=(
            "PRIMARY_REAL"
        ),
    )

    assert (
        demo.namespace(
            "01_Data",
            "runtime",
        )
        !=
        real.namespace(
            "01_Data",
            "runtime",
        )
    )


def test_invalid_namespace_purpose_cannot_escape_root():

    with pytest.raises(
        IsolationError,
        match="NAMESPACE_PURPOSE",
    ):

        context().namespace(
            "01_Data",
            "../BTCUSD",
        )


def test_metadata_stamp_and_validate():

    item = context()

    stamped = item.stamp_metadata(
        {
            "rows": 100,
        },
        scope="LEARNING",
    )

    assert (
        stamped[
            "rows"
        ]
        ==
        100
    )

    item.validate_metadata(
        stamped,
        scope="LEARNING",
    )


def test_metadata_without_identity_fails_validation():

    with pytest.raises(
        IsolationError,
        match="MISSING_IDENTITY",
    ):

        context().validate_metadata(
            {
                "rows": 100,
            },
            scope="LEARNING",
        )


def test_foreign_metadata_fails_closed():

    xau = context()

    btc = context(
        definition=definition(
            "BTCUSD",
            "CRYPTO",
            (
                "BTCUSDm",
            ),
        ),
        broker_symbol="BTCUSDm",
        contract_spec_id=(
            "EXNESS_BTCUSD_V1"
        ),
    )

    metadata = xau.stamp_metadata(
        {},
        scope="LEARNING",
    )

    with pytest.raises(
        IsolationError,
        match="IDENTITY_MISMATCH",
    ):

        btc.validate_metadata(
            metadata,
            scope="LEARNING",
        )