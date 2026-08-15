from __future__ import annotations

import ast
import importlib

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "04_Testing."
    "exness_demo_xauusd_context_"
    "attestation_operation"
)


class FakeMT5:
    ACCOUNT_TRADE_MODE_DEMO = 0
    ACCOUNT_TRADE_MODE_REAL = 2

    TIMEFRAME_M1 = 1

    def __init__(
        self,
        *,
        initialize_ok: bool = True,
        connected: bool = True,
        trade_mode: int = 0,
        company: str = "Exness",
        server: str = "Exness-MT5Trial",
        rates_count: int = 32,
        symbol_info: Any | None = None,
    ) -> None:

        self.initialize_ok = (
            initialize_ok
        )

        self.connected = (
            connected
        )

        self.trade_mode = (
            trade_mode
        )

        self.company = company
        self.server = server

        self.rates_count = (
            rates_count
        )

        self._symbol_info = (
            symbol_info
            if symbol_info is not None
            else
            self.gold_info()
        )

        self.calls: list[
            tuple[
                str,
                Any,
            ]
        ] = []

    @staticmethod
    def gold_info(
        *,
        name: str = "XAUUSDm",
        point: float = 0.001,
    ) -> Any:

        return SimpleNamespace(
            name=name,
            currency_base="XAU",
            currency_profit="USD",
            description=(
                "Gold vs US Dollar"
            ),
            digits=3,
            point=point,
            trade_contract_size=100.0,
            volume_min=0.01,
            volume_max=200.0,
            volume_step=0.01,
            trade_mode=4,
            visible=True,
            select=True,
        )

    def initialize(
        self,
    ) -> bool:

        self.calls.append(
            (
                "initialize",
                None,
            )
        )

        return self.initialize_ok

    def shutdown(
        self,
    ) -> None:

        self.calls.append(
            (
                "shutdown",
                None,
            )
        )

    def terminal_info(
        self,
    ) -> Any:

        self.calls.append(
            (
                "terminal_info",
                None,
            )
        )

        return SimpleNamespace(
            connected=(
                self.connected
            )
        )

    def account_info(
        self,
    ) -> Any:

        self.calls.append(
            (
                "account_info",
                None,
            )
        )

        return SimpleNamespace(
            login=12345678,
            server=self.server,
            company=self.company,
            trade_mode=self.trade_mode,
            currency="USD",
        )

    def copy_rates_from_pos(
        self,
        symbol: str,
        timeframe: int,
        start: int,
        bars: int,
    ) -> list[int]:

        self.calls.append(
            (
                "copy_rates_from_pos",
                symbol,
            )
        )

        return list(
            range(
                min(
                    bars,
                    self.rates_count,
                )
            )
        )

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

        return self._symbol_info

    def last_error(
        self,
    ) -> Any:

        return (
            0,
            "OK",
        )

    def order_send(
        self,
        *_args: Any,
        **_kwargs: Any,
    ) -> Any:

        raise AssertionError(
            "order_send must never be called"
        )

    def order_check(
        self,
        *_args: Any,
        **_kwargs: Any,
    ) -> Any:

        raise AssertionError(
            "order_check must never be called"
        )

    def positions_get(
        self,
        *_args: Any,
        **_kwargs: Any,
    ) -> Any:

        raise AssertionError(
            "positions_get must never be called"
        )


def resolver(
    requested: str,
    timeframe: int,
) -> str:

    assert requested in {
        "XAUUSDm",
        "AUTO",
    }

    assert timeframe == 1

    return "XAUUSDm"


def run(
    api: Any,
    *,
    requested: str = "XAUUSDm",
) -> Any:

    return module.run_attestation(
        requested_symbol=requested,
        probe_bars=32,
        broker_id="EXNESS",
        account_scope_id="PRIMARY_DEMO",
        data_schema_version=(
            "MARKET_V1"
        ),
        feature_contract_version=(
            "FEATURES_V1"
        ),
        mt5_api=api,
        resolver=resolver,
    )


def test_successful_demo_attestation():

    api = FakeMT5()

    result = run(
        api
    )

    assert result.valid is True

    assert (
        result.reason
        ==
        "OK_EXNESS_DEMO_XAUUSD_CONTEXT_ATTESTED"
    )

    assert result.live_authorized is False

    assert result.initialized is True
    assert result.terminal_connected is True
    assert result.demo_account_verified is True
    assert result.broker_verified is True

    assert result.resolved_symbol == "XAUUSDm"
    assert result.history_bar_count == 32

    assert (
        result.context.canonical_symbol
        ==
        "XAUUSD"
    )

    assert (
        result.context.asset_class
        ==
        "METAL"
    )

    assert (
        result.context.execution_environment
        ==
        "DEMO"
    )

    assert result.context.live_authorized is False

    assert (
        result.contract_spec_id.startswith(
            "EXNESS_XAUUSD_SPEC_"
        )
    )

    assert api.calls[-1] == (
        "shutdown",
        None,
    )


def test_real_account_fails_closed_before_market_attestation():

    api = FakeMT5(
        trade_mode=(
            FakeMT5
            .ACCOUNT_TRADE_MODE_REAL
        )
    )

    result = run(
        api
    )

    assert result.valid is False

    assert (
        result.reason
        ==
        "ACTIVE_MT5_ACCOUNT_IS_NOT_DEMO"
    )

    assert not any(
        name
        ==
        "copy_rates_from_pos"
        for name, _
        in api.calls
    )

    assert not any(
        name
        ==
        "symbol_info"
        for name, _
        in api.calls
    )

    assert api.calls[-1] == (
        "shutdown",
        None,
    )


def test_wrong_broker_identity_fails_closed():

    api = FakeMT5(
        company="Other Broker",
        server="OtherBroker-Demo",
    )

    result = run(
        api
    )

    assert result.valid is False

    assert (
        result.reason
        ==
        "BROKER_IDENTITY_MISMATCH"
    )


def test_disconnected_terminal_fails_closed():

    api = FakeMT5(
        connected=False
    )

    result = run(
        api
    )

    assert result.valid is False

    assert (
        result.reason
        ==
        "MT5_TERMINAL_NOT_CONNECTED"
    )


def test_initialize_failure_does_not_shutdown_unowned_session():

    api = FakeMT5(
        initialize_ok=False
    )

    result = run(
        api
    )

    assert result.valid is False

    assert (
        result.reason
        ==
        "MT5_INITIALIZE_FAILED"
    )

    assert api.calls == [
        (
            "initialize",
            None,
        )
    ]


def test_empty_history_fails_closed():

    api = FakeMT5(
        rates_count=0
    )

    result = run(
        api
    )

    assert result.valid is False

    assert (
        result.reason
        ==
        "MT5_HISTORY_PROBE_EMPTY"
    )


def test_auto_symbol_request_is_supported():

    result = run(
        FakeMT5(),
        requested="AUTO",
    )

    assert result.valid is True

    assert result.requested_symbol == "AUTO"
    assert result.resolved_symbol == "XAUUSDm"


def test_spoofed_gold_name_with_btc_metadata_is_rejected():

    bad = SimpleNamespace(
        name="XAUUSDm",
        currency_base="BTC",
        currency_profit="USD",
        description="Wrong contract",
        digits=3,
        point=0.001,
        trade_contract_size=100.0,
        volume_min=0.01,
        volume_max=200.0,
        volume_step=0.01,
        trade_mode=4,
        visible=True,
        select=True,
    )

    result = run(
        FakeMT5(
            symbol_info=bad
        )
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


def test_contract_spec_identity_is_deterministic():

    first = run(
        FakeMT5()
    )

    second = run(
        FakeMT5()
    )

    assert first.valid is True
    assert second.valid is True

    assert (
        first.contract_spec_id
        ==
        second.contract_spec_id
    )

    assert (
        first.context_identity_fingerprint
        ==
        second.context_identity_fingerprint
    )


def test_contract_semantic_change_changes_contract_spec_identity():

    first = run(
        FakeMT5(
            symbol_info=(
                FakeMT5.gold_info(
                    point=0.001
                )
            )
        )
    )

    second = run(
        FakeMT5(
            symbol_info=(
                FakeMT5.gold_info(
                    point=0.01
                )
            )
        )
    )

    assert first.valid is True
    assert second.valid is True

    assert (
        first.contract_spec_id
        !=
        second.contract_spec_id
    )

    assert (
        first.context_identity_fingerprint
        !=
        second.context_identity_fingerprint
    )


def test_account_identity_fingerprint_is_not_raw_login():

    result = run(
        FakeMT5()
    )

    assert result.valid is True

    assert (
        result.account_identity_fingerprint
    )

    assert (
        "12345678"
        not in
        result.account_identity_fingerprint
    )


def test_invalid_probe_count_fails_before_mt5():

    api = FakeMT5()

    result = module.run_attestation(
        requested_symbol="XAUUSDm",
        probe_bars=0,
        mt5_api=api,
        resolver=resolver,
    )

    assert result.valid is False

    assert (
        result.reason
        ==
        "INVALID_PROBE_BAR_COUNT"
    )

    assert api.calls == []


def test_source_contains_no_trade_execution_calls():

    source = Path(
        module.__file__
    ).read_text(
        encoding="utf-8"
    )

    tree = ast.parse(
        source
    )

    forbidden = {
        "order_send",
        "order_check",
        "positions_get",
        "positions_total",
        "orders_get",
        "order_calc_margin",
        "order_calc_profit",
    }

    called: set[str] = set()

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
        forbidden
    )