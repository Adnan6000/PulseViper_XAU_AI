from __future__ import annotations

import ast
import importlib

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pandas as pd
import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Dataset.mt5_read_only_instrument_attestation_adapter"
)

guard_module: Any = importlib.import_module(
    "02_AI.Dataset.instrument_frame_guard"
)


Adapter: Any = (
    module.MT5ReadOnlyInstrumentAttestationAdapter
)

XAUAttestor: Any = (
    module.MT5ReadOnlyXAUUSDContextAttestor
)

Guard: Any = (
    guard_module.InstrumentFrameGuard
)


class FakeMT5:

    def __init__(
        self,
        *,
        info: Any = None,
        error: Any = (
            0,
            "OK",
        ),
        raise_symbol_info: bool = False,
    ) -> None:

        self.info = (
            info
            if info is not None
            else
            gold_info()
        )

        self.error = error

        self.raise_symbol_info = (
            raise_symbol_info
        )

        self.calls: list[
            tuple[
                str,
                Any,
            ]
        ] = []

    def symbol_info(
        self,
        symbol: str,
    ) -> Any:

        self.calls.append(
            (
                "symbol_info",
                symbol,
            )
        )

        if self.raise_symbol_info:

            raise RuntimeError(
                "simulated symbol_info failure"
            )

        return self.info

    def last_error(
        self,
    ) -> Any:

        self.calls.append(
            (
                "last_error",
                None,
            )
        )

        return self.error

    def order_send(
        self,
        *_args: Any,
        **_kwargs: Any,
    ) -> Any:

        raise AssertionError(
            "order_send must never be called"
        )

    def initialize(
        self,
        *_args: Any,
        **_kwargs: Any,
    ) -> Any:

        raise AssertionError(
            "initialize must never be called"
        )

    def shutdown(
        self,
        *_args: Any,
        **_kwargs: Any,
    ) -> Any:

        raise AssertionError(
            "shutdown must never be called"
        )

    def symbol_select(
        self,
        *_args: Any,
        **_kwargs: Any,
    ) -> Any:

        raise AssertionError(
            "symbol_select must never be called"
        )

    def copy_rates_from_pos(
        self,
        *_args: Any,
        **_kwargs: Any,
    ) -> Any:

        raise AssertionError(
            "history must never be called"
        )

    def copy_ticks_range(
        self,
        *_args: Any,
        **_kwargs: Any,
    ) -> Any:

        raise AssertionError(
            "ticks must never be called"
        )


def gold_info(
    *,
    name: str = "XAUUSDm",
    base: str = "XAU",
    profit: str = "USD",
    point: float = 0.001,
    digits: int = 3,
    contract_size: float = 100.0,
    volume_min: float = 0.01,
    volume_max: float = 200.0,
    volume_step: float = 0.01,
) -> Any:

    return SimpleNamespace(
        name=name,
        currency_base=base,
        currency_profit=profit,
        description="Gold vs US Dollar",
        digits=digits,
        point=point,
        trade_contract_size=(
            contract_size
        ),
        volume_min=volume_min,
        volume_max=volume_max,
        volume_step=volume_step,
        trade_mode=4,
        visible=True,
        select=True,
    )


def btc_info() -> Any:

    return SimpleNamespace(
        name="BTCUSDm",
        currency_base="BTC",
        currency_profit="USD",
        description="Bitcoin vs US Dollar",
        digits=2,
        point=0.01,
        trade_contract_size=1.0,
        volume_min=0.01,
        volume_max=20.0,
        volume_step=0.01,
        trade_mode=4,
        visible=True,
        select=True,
    )


def fetcher_state(
    *,
    requested: str = "XAUUSDm",
    resolved: str = "XAUUSDm",
    bars: int = 500,
) -> Any:

    return SimpleNamespace(
        last_requested_symbol=(
            requested
        ),
        last_resolved_symbol=(
            resolved
        ),
        last_bar_count=bars,
    )


def attest_xau(
    api: Any,
    *,
    state: Any | None = None,
    environment: str = "DEMO",
) -> Any:

    return XAUAttestor(
        mt5_api=api
    ).attest_fetcher_resolution(
        fetcher_state=(
            state
            if state is not None
            else
            fetcher_state()
        ),
        broker_id="EXNESS",
        account_scope_id=(
            "PRIMARY_DEMO"
        ),
        execution_environment=(
            environment
        ),
        contract_spec_id=(
            "EXNESS_XAUUSD_STANDARD_V1"
        ),
        data_schema_version=(
            "MARKET_V1"
        ),
        feature_contract_version=(
            "FEATURES_V1"
        ),
    )


def test_generic_adapter_attests_exact_gold_metadata():

    api = FakeMT5()

    result = Adapter(
        mt5_api=api
    ).read_symbol(
        expected_symbol="XAUUSDm"
    )

    assert result.valid is True
    assert result.attested is True

    assert (
        result.reason
        ==
        "OK_MT5_SYMBOL_METADATA_ATTESTED"
    )

    assert (
        result.attestation.name
        ==
        "XAUUSDm"
    )

    assert (
        result.attestation.currency_base
        ==
        "XAU"
    )

    assert (
        result.attestation.currency_profit
        ==
        "USD"
    )

    assert (
        result.attestation.point
        ==
        pytest.approx(
            0.001
        )
    )

    assert (
        result.attestation.trade_contract_size
        ==
        pytest.approx(
            100.0
        )
    )

    assert result.live_authorized is False

    assert api.calls == [
        (
            "symbol_info",
            "XAUUSDm",
        )
    ]


def test_low_level_adapter_is_generic_and_can_read_btc_metadata():

    api = FakeMT5(
        info=btc_info()
    )

    result = Adapter(
        mt5_api=api
    ).read_symbol(
        expected_symbol="BTCUSDm"
    )

    assert result.valid is True

    assert (
        result.attestation.currency_base
        ==
        "BTC"
    )

    assert (
        result.attestation.name
        ==
        "BTCUSDm"
    )


def test_xau_attestor_rejects_btc_context():

    api = FakeMT5(
        info=btc_info()
    )

    result = attest_xau(
        api,
        state=fetcher_state(
            requested="BTCUSDm",
            resolved="BTCUSDm",
        ),
    )

    assert result.valid is False
    assert result.bound is False

    assert (
        result.reason
        ==
        "XAUUSD_CONTEXT_BINDING_REJECTED"
    )

    assert (
        result.binding_reason
        ==
        "REQUESTED_SYMBOL_NOT_XAUUSD_FAMILY"
    )


def test_missing_symbol_info_fails_closed():

    api = FakeMT5(
        info=None,
        error=(
            4301,
            "unknown symbol",
        ),
    )

    api.info = None

    result = Adapter(
        mt5_api=api
    ).read_symbol(
        expected_symbol="XAUUSDm"
    )

    assert result.valid is False

    assert (
        result.reason
        ==
        "MT5_SYMBOL_INFO_NOT_FOUND"
    )

    assert (
        "4301"
        in result.mt5_error
    )

    assert api.calls == [
        (
            "symbol_info",
            "XAUUSDm",
        ),
        (
            "last_error",
            None,
        ),
    ]


def test_symbol_info_exception_fails_closed():

    api = FakeMT5(
        raise_symbol_info=True
    )

    result = Adapter(
        mt5_api=api
    ).read_symbol(
        expected_symbol="XAUUSDm"
    )

    assert result.valid is False

    assert (
        result.reason
        ==
        "MT5_SYMBOL_INFO_EXCEPTION"
    )


def test_exact_broker_symbol_name_is_required():

    api = FakeMT5(
        info=gold_info(
            name="XAUUSD"
        )
    )

    result = Adapter(
        mt5_api=api
    ).read_symbol(
        expected_symbol="XAUUSDm"
    )

    assert result.valid is False

    assert (
        result.reason
        ==
        "MT5_SYMBOL_INFO_EXACT_NAME_MISMATCH"
    )


@pytest.mark.parametrize(
    (
        "info",
        "reason",
    ),
    [
        (
            gold_info(
                point=0.0
            ),
            "INVALID_MT5_SYMBOL_POINT",
        ),
        (
            gold_info(
                contract_size=0.0
            ),
            "INVALID_MT5_SYMBOL_CONTRACT_SIZE",
        ),
        (
            gold_info(
                volume_min=0.0
            ),
            "INVALID_MT5_SYMBOL_VOLUME_MIN",
        ),
        (
            gold_info(
                volume_max=0.001
            ),
            "INVALID_MT5_SYMBOL_VOLUME_MAX",
        ),
        (
            gold_info(
                volume_step=0.0
            ),
            "INVALID_MT5_SYMBOL_VOLUME_STEP",
        ),
    ],
)
def test_invalid_contract_metadata_fails_closed(
    info,
    reason,
):

    result = Adapter(
        mt5_api=FakeMT5(
            info=info
        )
    ).read_symbol(
        expected_symbol="XAUUSDm"
    )

    assert result.valid is False
    assert result.reason == reason


def test_xau_attestation_binds_verified_context():

    api = FakeMT5()

    result = attest_xau(
        api
    )

    assert result.valid is True
    assert result.bound is True

    assert (
        result.reason
        ==
        "OK_READ_ONLY_XAUUSD_CONTEXT_ATTESTED"
    )

    assert result.canonical_symbol == "XAUUSD"
    assert result.asset_class == "METAL"

    assert (
        result.context.broker_symbol
        ==
        "XAUUSDm"
    )

    assert (
        result.context.execution_environment
        ==
        "DEMO"
    )

    assert result.context.live_authorized is False
    assert result.live_authorized is False


def test_xau_attestation_rejects_wrong_metadata_base():

    api = FakeMT5(
        info=gold_info(
            base="BTC"
        )
    )

    result = attest_xau(
        api
    )

    assert result.valid is False

    assert (
        result.reason
        ==
        "XAUUSD_CONTEXT_BINDING_REJECTED"
    )

    assert (
        result.binding_reason
        ==
        "RESOLVED_SYMBOL_BASE_NOT_XAU"
    )


def test_xau_attestation_rejects_wrong_profit_currency():

    api = FakeMT5(
        info=gold_info(
            profit="EUR"
        )
    )

    result = attest_xau(
        api
    )

    assert result.valid is False

    assert (
        result.binding_reason
        ==
        "RESOLVED_SYMBOL_PROFIT_NOT_USD"
    )


def test_missing_resolved_symbol_does_not_call_mt5():

    api = FakeMT5()

    result = attest_xau(
        api,
        state=fetcher_state(
            resolved=""
        ),
    )

    assert result.valid is False

    assert (
        result.reason
        ==
        "RESOLVED_SYMBOL_MISSING"
    )

    assert api.calls == []


def test_invalid_fetcher_shape_does_not_call_mt5():

    api = FakeMT5()

    result = attest_xau(
        api,
        state=SimpleNamespace(
            last_resolved_symbol=(
                "XAUUSDm"
            )
        ),
    )

    assert result.valid is False

    assert (
        result.reason
        ==
        "INVALID_FETCHER_RESOLUTION_STATE"
    )

    assert api.calls == []


def test_real_identity_still_does_not_authorize_live_execution():

    api = FakeMT5()

    result = attest_xau(
        api,
        environment="REAL",
    )

    assert result.valid is True

    assert (
        result.context.execution_environment
        ==
        "REAL"
    )

    assert result.live_authorized is False
    assert result.context.live_authorized is False


def test_attestation_fingerprint_is_deterministic():

    first = Adapter(
        mt5_api=FakeMT5()
    ).read_symbol(
        expected_symbol="XAUUSDm"
    )

    second = Adapter(
        mt5_api=FakeMT5()
    ).read_symbol(
        expected_symbol="XAUUSDm"
    )

    assert first.valid is True
    assert second.valid is True

    assert (
        first.attestation_fingerprint
        ==
        second.attestation_fingerprint
    )


def test_verified_context_can_stamp_xau_training_frame():

    result = attest_xau(
        FakeMT5()
    )

    assert result.valid is True

    guard = Guard(
        result.context
    )

    frame = guard.stamp(
        pd.DataFrame(
            {
                "time": [
                    1,
                    2,
                ],
                "close": [
                    4310.0,
                    4311.0,
                ],
            }
        )
    )

    guard.validate(
        frame
    )

    assert bool(
        frame[
            "pv_canonical_symbol"
        ]
        .eq(
            "XAUUSD"
        )
        .all()
    )

    assert bool(
        frame[
            "pv_broker_symbol"
        ]
        .eq(
            "XAUUSDm"
        )
        .all()
    )


def test_adapter_source_contains_no_execution_or_connection_ownership():

    source = Path(
        module.__file__
    ).read_text(
        encoding="utf-8"
    )

    tree = ast.parse(
        source
    )

    forbidden_calls = {
        "order_send",
        "initialize",
        "shutdown",
        "symbol_select",
        "copy_rates_from_pos",
        "copy_rates_range",
        "copy_ticks_range",
        "copy_ticks_from",
        "positions_get",
        "order_check",
    }

    called: set[
        str
    ] = set()

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


def test_successful_attestation_uses_symbol_info_only():

    api = FakeMT5()

    result = attest_xau(
        api
    )

    assert result.valid is True

    assert api.calls == [
        (
            "symbol_info",
            "XAUUSDm",
        )
    ]