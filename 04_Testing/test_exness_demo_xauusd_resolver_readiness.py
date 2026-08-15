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


def gold_symbol(
    name: str = "XAUUSDm",
) -> Any:

    return SimpleNamespace(
        name=name,
        description="Gold vs US Dollar",
        currency_base="XAU",
        currency_profit="USD",
    )


class FakeAPI:

    def __init__(
        self,
        symbols: tuple[
            Any,
            ...,
        ],
    ) -> None:

        self.symbols = symbols

        self.calls: list[
            str
        ] = []

    def symbols_get(
        self,
    ):

        self.calls.append(
            "symbols_get"
        )

        return self.symbols

    def last_error(
        self,
    ):

        self.calls.append(
            "last_error"
        )

        return (
            1,
            "Success",
        )


class FlakyFetcher:

    def __init__(
        self,
    ) -> None:

        self.calls = 0

    def resolve_symbol(
        self,
        *,
        requested_symbol: str,
        timeframe: int,
    ) -> str:

        self.calls += 1

        assert (
            requested_symbol
            ==
            "XAUUSDm"
        )

        assert (
            timeframe
            ==
            1
        )

        if (
            self.calls
            ==
            1
        ):

            raise RuntimeError(
                "catalog not ready"
            )

        return "XAUUSDm"


class FailingFetcher:

    def __init__(
        self,
    ) -> None:

        self.calls = 0

    def resolve_symbol(
        self,
        *,
        requested_symbol: str,
        timeframe: int,
    ) -> str:

        self.calls += 1

        raise RuntimeError(
            "probe failed"
        )


def test_readiness_catalog_precedes_bounded_retry():

    api = FakeAPI(
        (
            gold_symbol(
                "XAUUSDm"
            ),
            gold_symbol(
                "XAUUSD247m"
            ),
        )
    )

    fetcher = (
        FlakyFetcher()
    )

    (
        resolved,
        evidence,
    ) = module.resolve_with_readiness(
        api=api,
        fetcher=fetcher,
        requested_symbol="XAUUSDm",
        timeframe=1,
        max_attempts=3,
    )

    assert (
        resolved
        ==
        "XAUUSDm"
    )

    assert (
        evidence.attempt_count
        ==
        2
    )

    assert (
        evidence.symbol_catalog_count
        ==
        2
    )

    assert (
        evidence.gold_candidates
        ==
        (
            "XAUUSD247m",
            "XAUUSDm",
        )
    )

    assert (
        evidence.resolver_error
        ==
        ""
    )

    assert (
        fetcher.calls
        ==
        2
    )

    assert (
        api.calls.count(
            "symbols_get"
        )
        ==
        2
    )


def test_failed_resolver_does_not_silently_use_discovered_candidate():

    api = FakeAPI(
        (
            gold_symbol(
                "XAUUSDm"
            ),
        )
    )

    fetcher = (
        FailingFetcher()
    )

    (
        resolved,
        evidence,
    ) = module.resolve_with_readiness(
        api=api,
        fetcher=fetcher,
        requested_symbol="XAUUSDm",
        timeframe=1,
        max_attempts=3,
    )

    assert resolved == ""

    assert (
        evidence.attempt_count
        ==
        3
    )

    assert (
        evidence.gold_candidates
        ==
        (
            "XAUUSDm",
        )
    )

    assert (
        evidence.resolver_error
        ==
        "RuntimeError: probe failed"
    )

    assert (
        fetcher.calls
        ==
        3
    )


def test_invalid_attempt_count_fails_closed():

    with pytest.raises(
        ValueError,
        match="positive integer",
    ):

        module.resolve_with_readiness(
            api=FakeAPI(
                ()
            ),
            fetcher=(
                FailingFetcher()
            ),
            requested_symbol="XAUUSDm",
            timeframe=1,
            max_attempts=0,
        )


def test_gold_candidate_diagnostics_include_cross_gold_contracts():

    symbols = (
        SimpleNamespace(
            name="BTCXAUm",
            description=(
                "Bitcoin vs Gold"
            ),
            currency_base="BTC",
            currency_profit="XAU",
        ),
        SimpleNamespace(
            name="XAUAUDm",
            description=(
                "Gold vs Australian Dollar"
            ),
            currency_base="XAU",
            currency_profit="AUD",
        ),
        gold_symbol(
            "XAUUSDm"
        ),
    )

    result = (
        module
        ._gold_candidates_from_symbols(
            symbols
        )
    )

    assert result == (
        "BTCXAUm",
        "XAUAUDm",
        "XAUUSDm",
    )


def test_operation_source_has_no_trade_execution_authority():

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
        forbidden
    )