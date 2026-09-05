from __future__ import annotations

import ast
import importlib
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pandas as pd
import pytest


pytestmark = pytest.mark.offline


binding_module: Any = importlib.import_module(
    "02_AI.Dataset.broker_instrument_context_binding"
)

guard_module: Any = importlib.import_module(
    "02_AI.Dataset.instrument_frame_guard"
)

Binder: Any = (
    binding_module.XAUUSDBrokerInstrumentContextBinder
)

Guard: Any = (
    guard_module.InstrumentFrameGuard
)

IsolationError: Any = (
    binding_module.InstrumentIsolationError
)


def fetcher_state(
    *,
    requested: str = "XAUUSDm",
    resolved: str = "XAUUSDm",
    bars: Any = 500,
) -> Any:

    return SimpleNamespace(
        last_requested_symbol=requested,
        last_resolved_symbol=resolved,
        last_bar_count=bars,
    )


def symbol_info(
    *,
    name: str = "XAUUSDm",
    base: str = "XAU",
    profit: str = "USD",
    description: str = "Gold vs US Dollar",
) -> Any:

    return SimpleNamespace(
        name=name,
        currency_base=base,
        currency_profit=profit,
        description=description,
    )


def bind(
    *,
    state: Any | None = None,
    info: Any | None = None,
    environment: str = "DEMO",
    binder: Any | None = None,
) -> Any:

    engine = (
        binder
        if binder is not None
        else Binder()
    )

    return engine.bind_fetcher_resolution(
        fetcher_state=(
            state
            if state is not None
            else fetcher_state()
        ),
        symbol_info=(
            info
            if info is not None
            else symbol_info()
        ),
        broker_id="EXNESS",
        account_scope_id="PRIMARY_DEMO",
        execution_environment=environment,
        contract_spec_id=(
            "EXNESS_XAUUSD_STANDARD_V1"
        ),
        data_schema_version="MARKET_V1",
        feature_contract_version=(
            "FEATURES_V1"
        ),
    )


def test_fetcher_resolution_binds_exact_xauusd_context():

    result = bind()

    assert result.valid is True
    assert result.bound is True

    assert (
        result.reason
        ==
        "OK_XAUUSD_INSTRUMENT_CONTEXT_BOUND"
    )

    assert result.live_authorized is False
    assert result.canonical_symbol == "XAUUSD"
    assert result.asset_class == "METAL"

    assert (
        result.context.canonical_symbol
        ==
        "XAUUSD"
    )

    assert (
        result.context.broker_symbol
        ==
        "XAUUSDm"
    )

    assert result.context.live_authorized is False


def test_auto_request_can_bind_resolved_xauusd():

    result = bind(
        state=fetcher_state(
            requested="AUTO"
        )
    )

    assert result.valid is True
    assert result.requested_symbol == "AUTO"
    assert result.resolved_symbol == "XAUUSDm"


def test_gold_alias_requires_xau_usd_metadata():

    result = bind(
        state=fetcher_state(
            requested="GOLDm",
            resolved="GOLDm",
        ),
        info=symbol_info(
            name="GOLDm"
        ),
    )

    assert result.valid is True

    assert (
        result.context.broker_symbol
        ==
        "GOLDm"
    )

    assert (
        result.context.canonical_symbol
        ==
        "XAUUSD"
    )


def test_btc_request_cannot_fall_into_gold_context():

    result = bind(
        state=fetcher_state(
            requested="BTCUSDm",
            resolved="XAUUSDm",
        )
    )

    assert result.valid is False

    assert (
        result.reason
        ==
        "REQUESTED_SYMBOL_NOT_XAUUSD_FAMILY"
    )

    assert result.context is None


def test_btc_resolved_symbol_cannot_bind_as_xauusd():

    result = bind(
        state=fetcher_state(
            requested="AUTO",
            resolved="BTCUSDm",
        ),
        info=symbol_info(
            name="BTCUSDm",
            base="BTC",
            description=(
                "Bitcoin vs US Dollar"
            ),
        ),
    )

    assert result.valid is False

    assert (
        result.reason
        ==
        "RESOLVED_SYMBOL_NOT_IN_XAUUSD_ALLOWLIST"
    )


def test_spoofed_xau_name_with_wrong_base_fails_closed():

    result = bind(
        info=symbol_info(
            base="BTC"
        )
    )

    assert result.valid is False

    assert (
        result.reason
        ==
        "RESOLVED_SYMBOL_BASE_NOT_XAU"
    )


def test_wrong_profit_currency_fails_closed():

    result = bind(
        info=symbol_info(
            profit="EUR"
        )
    )

    assert result.valid is False

    assert (
        result.reason
        ==
        "RESOLVED_SYMBOL_PROFIT_NOT_USD"
    )


def test_symbol_info_name_must_exactly_match_resolved_symbol():

    result = bind(
        info=symbol_info(
            name="XAUUSD"
        )
    )

    assert result.valid is False

    assert (
        result.reason
        ==
        "RESOLVED_SYMBOL_INFO_NAME_MISMATCH"
    )


@pytest.mark.parametrize(
    "bars",
    [
        0,
        -1,
        1.5,
        float("nan"),
    ],
)
def test_positive_validated_history_is_required(
    bars,
):

    result = bind(
        state=fetcher_state(
            bars=bars
        )
    )

    assert result.valid is False

    assert (
        result.reason
        ==
        "INVALID_HISTORY_BAR_COUNT"
    )


def test_invalid_fetcher_state_shape_fails_closed():

    result = bind(
        state=SimpleNamespace(
            last_resolved_symbol="XAUUSDm"
        )
    )

    assert result.valid is False

    assert (
        result.reason
        ==
        "INVALID_FETCHER_RESOLUTION_STATE"
    )


def test_invalid_symbol_info_shape_fails_closed():

    result = bind(
        info=SimpleNamespace(
            name="XAUUSDm"
        )
    )

    assert result.valid is False

    assert (
        result.reason
        ==
        "INVALID_SYMBOL_INFO_SHAPE"
    )


def test_unknown_gold_alias_requires_explicit_allowlist_change():

    result = bind(
        state=fetcher_state(
            requested="XAUUSDc",
            resolved="XAUUSDc",
        ),
        info=symbol_info(
            name="XAUUSDc"
        ),
    )

    assert result.valid is False

    assert (
        result.reason
        ==
        "RESOLVED_SYMBOL_NOT_IN_XAUUSD_ALLOWLIST"
    )


def test_explicitly_allowlisted_gold_alias_can_bind():

    engine = Binder(
        allowed_broker_symbols=(
            "XAUUSDm",
            "XAUUSDc",
        )
    )

    result = bind(
        binder=engine,
        state=fetcher_state(
            requested="XAUUSDc",
            resolved="XAUUSDc",
        ),
        info=symbol_info(
            name="XAUUSDc"
        ),
    )

    assert result.valid is True

    assert (
        result.context.broker_symbol
        ==
        "XAUUSDc"
    )


def test_real_environment_identity_does_not_authorize_live_trading():

    result = bind(
        environment="REAL"
    )

    assert result.valid is True
    assert result.live_authorized is False
    assert result.context.live_authorized is False

    assert (
        result.context.execution_environment
        ==
        "REAL"
    )


def test_binding_fingerprints_are_deterministic():

    first = bind()
    second = bind()

    assert first.valid is True
    assert second.valid is True

    assert (
        first.evidence_fingerprint
        ==
        second.evidence_fingerprint
    )

    assert (
        first.definition_fingerprint
        ==
        second.definition_fingerprint
    )

    assert (
        first.context_identity_fingerprint
        ==
        second.context_identity_fingerprint
    )


def test_allowed_gold_aliases_share_instrument_not_learning_scope():

    first = bind()

    second = bind(
        state=fetcher_state(
            requested="XAUUSD.a",
            resolved="XAUUSD.a",
        ),
        info=symbol_info(
            name="XAUUSD.a"
        ),
    )

    assert first.valid is True
    assert second.valid is True

    first.context.assert_same_instrument(
        second.context
    )

    with pytest.raises(
        IsolationError,
        match="CROSS_LEARNING",
    ):

        first.context.assert_same_learning_scope(
            second.context
        )


def test_history_export_metadata_can_bind_same_contract():

    result = Binder().bind_history_export(
        export_metadata={
            "requested_symbol": "XAUUSDm",
            "resolved_symbol": "XAUUSDm",
            "timeframe": "M1",
            "bars": 500,
            "path": Path(
                "01_Data/Raw/"
                "XAUUSDm_M1_20260815.csv"
            ),
        },
        symbol_info=symbol_info(),
        broker_id="EXNESS",
        account_scope_id="PRIMARY_DEMO",
        execution_environment="DEMO",
        contract_spec_id=(
            "EXNESS_XAUUSD_STANDARD_V1"
        ),
        data_schema_version="MARKET_V1",
        feature_contract_version=(
            "FEATURES_V1"
        ),
    )

    assert result.valid is True

    assert (
        result.evidence.source
        ==
        "HISTORY_DOWNLOADER_EXPORT"
    )

    assert (
        result.context.broker_symbol
        ==
        "XAUUSDm"
    )


def test_invalid_history_export_metadata_fails_closed():

    result = Binder().bind_history_export(
        export_metadata={
            "resolved_symbol": "XAUUSDm",
        },
        symbol_info=symbol_info(),
        broker_id="EXNESS",
        account_scope_id="PRIMARY_DEMO",
        execution_environment="DEMO",
        contract_spec_id=(
            "EXNESS_XAUUSD_STANDARD_V1"
        ),
        data_schema_version="MARKET_V1",
        feature_contract_version=(
            "FEATURES_V1"
        ),
    )

    assert result.valid is False

    assert (
        result.reason
        ==
        "INVALID_HISTORY_EXPORT_METADATA"
    )


def test_bound_context_can_stamp_training_frame_identity():

    result = bind()

    guard = Guard(
        result.context
    )

    stamped = guard.stamp(
        pd.DataFrame(
            {
                "time": [
                    1,
                    2,
                ],
                "close": [
                    4300.0,
                    4301.0,
                ],
            }
        )
    )

    guard.validate(
        stamped
    )

    assert (
        stamped[
            "pv_canonical_symbol"
        ]
        .eq(
            "XAUUSD"
        )
        .all()
    )

    assert (
        stamped[
            "pv_broker_symbol"
        ]
        .eq(
            "XAUUSDm"
        )
        .all()
    )


def test_binder_has_no_mt5_or_execution_authority():

    source = Path(
        binding_module.__file__
    ).read_text(
        encoding="utf-8"
    )

    tree = ast.parse(
        source
    )

    imported = set()

    for node in ast.walk(
        tree
    ):

        if isinstance(
            node,
            ast.Import,
        ):

            imported.update(
                alias.name
                for alias
                in node.names
            )

        elif (
            isinstance(
                node,
                ast.ImportFrom,
            )
            and
            node.module
        ):

            imported.add(
                node.module
            )

    assert (
        "MetaTrader5"
        not in imported
    )

    assert (
        "mt5"
        not in imported
    )

    forbidden_calls = {
        "order_send",
        "initialize",
        "shutdown",
        "symbol_select",
        "copy_rates_from_pos",
        "copy_ticks_range",
    }

    called = set()

    for node in ast.walk(
        tree
    ):

        if not isinstance(
            node,
            ast.Call,
        ):

            continue

        if isinstance(
            node.func,
            ast.Attribute,
        ):

            called.add(
                node.func.attr
            )

        elif isinstance(
            node.func,
            ast.Name,
        ):

            called.add(
                node.func.id
            )

    assert called.isdisjoint(
        forbidden_calls
    )