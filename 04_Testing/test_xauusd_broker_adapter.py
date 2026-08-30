from __future__ import annotations

import importlib
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from typing import Any


ROOT_DIR = Path(
    __file__
).resolve().parents[
    1
]

if str(
    ROOT_DIR
) not in sys.path:

    sys.path.insert(
        0,
        str(
            ROOT_DIR
        ),
    )


adapter_module: Any = (
    importlib
    .import_module(
        "02_AI.Adapters.xauusd_broker_adapter"
    )
)


BrokerCostAdapter = (
    adapter_module
    .BrokerCostAdapter
)

CanonicalGoldResolver = (
    adapter_module
    .CanonicalGoldResolver
)

gold_usd_semantics = (
    adapter_module
    .gold_usd_semantics
)


def _symbol(
    name: str,
    *,
    description: str = (
        "Gold vs US Dollar"
    ),
    path: str = (
        "Commodities\\Metals"
    ),
    currency_base: str = (
        "XAU"
    ),
    currency_profit: str = (
        "USD"
    ),
    visible: bool = True,
    trade_mode: int = 4,
    point: float = 0.01,
    tick_size: float = 0.01,
) -> SimpleNamespace:

    return SimpleNamespace(
        name=name,
        description=(
            description
        ),
        path=(
            path
        ),
        currency_base=(
            currency_base
        ),
        currency_profit=(
            currency_profit
        ),
        currency_margin=(
            currency_base
        ),
        visible=(
            visible
        ),
        trade_mode=(
            trade_mode
        ),
        digits=2,
        point=(
            point
        ),
        trade_tick_size=(
            tick_size
        ),
        trade_tick_value=1.0,
        trade_tick_value_profit=1.0,
        trade_tick_value_loss=1.0,
        trade_contract_size=100.0,
        trade_stops_level=0,
        trade_freeze_level=0,
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01,
        volume_limit=0.0,
        spread=20,
        spread_float=True,
        trade_calc_mode=0,
        filling_mode=2,
        order_mode=127,
        swap_mode=1,
        swap_long=-1.0,
        swap_short=1.0,
        margin_initial=100.0,
        margin_maintenance=0.0,
    )


def _tick(
    *,
    bid: float,
    ask: float,
    time_value: int,
) -> SimpleNamespace:

    return SimpleNamespace(
        bid=(
            bid
        ),
        ask=(
            ask
        ),
        last=0.0,
        time=(
            time_value
        ),
        time_msc=(
            time_value
            *
            1000
        ),
    )


def _rates(
    count: int = 40,
) -> list[
    dict[str, float]
]:

    rows: list[
        dict[str, float]
    ] = []

    close = 2000.0

    for index in range(
        count
    ):

        base = (
            close
            +
            index
            *
            0.1
        )

        rows.append(
            {
                "high": (
                    base
                    +
                    1.0
                ),
                "low": (
                    base
                    -
                    1.0
                ),
                "close": (
                    base
                    +
                    0.2
                ),
            }
        )

    return rows


class FakeMT5:

    TIMEFRAME_M5 = 5

    def __init__(
        self,
        *,
        symbols: list[
            SimpleNamespace
        ],
        ticks: dict[
            str,
            SimpleNamespace
            |
            None,
        ],
        server: str = (
            "Broker-Demo"
        ),
    ) -> None:

        self._symbols = list(
            symbols
        )

        self._ticks = dict(
            ticks
        )

        self._server = (
            server
        )

    def symbols_get(
        self,
    ) -> tuple[
        SimpleNamespace,
        ...,
    ]:

        return tuple(
            self._symbols
        )

    def symbol_info(
        self,
        name: str,
    ) -> (
        SimpleNamespace
        |
        None
    ):

        for symbol in (
            self._symbols
        ):

            if (
                symbol.name
                ==
                name
            ):

                return symbol

        return None

    def symbol_info_tick(
        self,
        name: str,
    ) -> (
        SimpleNamespace
        |
        None
    ):

        return (
            self._ticks
            .get(
                name
            )
        )

    def account_info(
        self,
    ) -> SimpleNamespace:

        return SimpleNamespace(
            server=(
                self._server
            )
        )

    def copy_rates_from_pos(
        self,
        symbol_name: str,
        timeframe: int,
        start_pos: int,
        count: int,
    ) -> list[
        dict[str, float]
    ]:

        del (
            symbol_name,
            timeframe,
            start_pos,
            count,
        )

        return _rates()


class TestXAUUSDBrokerAdapter(
    unittest.TestCase
):

    def test_suffix_symbol_is_resolved_and_lookalikes_rejected(
        self,
    ) -> None:

        symbols = [
            _symbol(
                "XAUUSDm",
                visible=True,
            ),
            _symbol(
                "XAUEUR",
                description=(
                    "Gold vs Euro"
                ),
                currency_profit=(
                    "EUR"
                ),
                visible=False,
            ),
            _symbol(
                "GOLD.NYSE-24",
                description=(
                    "GOLD.COM INC 24/5 CFD"
                ),
                path=(
                    "Stocks\\NYSE"
                ),
                currency_base=(
                    "USD"
                ),
                currency_profit=(
                    "USD"
                ),
                visible=False,
            ),
        ]

        fake = FakeMT5(
            symbols=(
                symbols
            ),
            ticks={
                "XAUUSDm": (
                    _tick(
                        bid=2000.0,
                        ask=2000.2,
                        time_value=995,
                    )
                ),
                "XAUEUR": None,
                "GOLD.NYSE-24": None,
            },
        )

        resolver = (
            CanonicalGoldResolver(
                fake,
                now_provider=lambda: (
                    1000.0
                ),
            )
        )

        result = (
            resolver
            .resolve()
        )

        self.assertEqual(
            result.canonical_symbol,
            "XAUUSD",
        )

        self.assertEqual(
            result.broker_symbol,
            "XAUUSDm",
        )

        self.assertEqual(
            result.candidate_count,
            1,
        )

        self.assertEqual(
            result.rejected_gold_like_count,
            2,
        )

    def test_gold_name_is_supported_without_hardcoded_suffixes(
        self,
    ) -> None:

        symbol = (
            _symbol(
                "GOLDmicro",
                description=(
                    "Spot Gold"
                ),
                path=(
                    "Metals\\Spot"
                ),
                currency_base="",
                currency_profit="USD",
            )
        )

        semantics = (
            gold_usd_semantics(
                symbol
            )
        )

        self.assertTrue(
            semantics[
                "accepted"
            ]
        )

        self.assertTrue(
            semantics[
                "name_gold_family"
            ]
        )

        fake = FakeMT5(
            symbols=[
                symbol
            ],
            ticks={
                "GOLDmicro": (
                    _tick(
                        bid=2500.0,
                        ask=2500.1,
                        time_value=995,
                    )
                )
            },
        )

        result = (
            CanonicalGoldResolver(
                fake,
                now_provider=lambda: (
                    1000.0
                ),
            )
            .resolve()
        )

        self.assertEqual(
            result.broker_symbol,
            "GOLDmicro",
        )

    def test_stale_tick_keeps_symbol_resolution_but_blocks_cost_use(
        self,
    ) -> None:

        symbol = (
            _symbol(
                "XAUUSD.c"
            )
        )

        fake = FakeMT5(
            symbols=[
                symbol
            ],
            ticks={
                "XAUUSD.c": (
                    _tick(
                        bid=2000.0,
                        ask=2000.4,
                        time_value=500,
                    )
                )
            },
            server=(
                "ExampleBroker-MT5"
            ),
        )

        snapshot = (
            BrokerCostAdapter(
                fake,
                max_tick_age_seconds=180,
                now_provider=lambda: (
                    1000.0
                ),
            )
            .snapshot()
        )

        self.assertEqual(
            snapshot[
                "resolution"
            ][
                "broker_symbol"
            ],
            "XAUUSD.c",
        )

        self.assertFalse(
            snapshot[
                "tick"
            ][
                "fresh"
            ]
        )

        self.assertFalse(
            snapshot[
                "spread"
            ][
                "usable_for_runtime_costs"
            ]
        )

        self.assertIsNone(
            snapshot[
                "spread"
            ][
                "spread_atr14"
            ]
        )

    def test_fresh_tick_produces_normalized_costs_and_fingerprint(
        self,
    ) -> None:

        symbol = (
            _symbol(
                "XAUUSD"
            )
        )

        fake = FakeMT5(
            symbols=[
                symbol
            ],
            ticks={
                "XAUUSD": (
                    _tick(
                        bid=2000.0,
                        ask=2000.2,
                        time_value=995,
                    )
                )
            },
            server=(
                "ICMarketsSC-MT5-3"
            ),
        )

        snapshot = (
            BrokerCostAdapter(
                fake,
                now_provider=lambda: (
                    1000.0
                ),
            )
            .snapshot()
        )

        spread = (
            snapshot[
                "spread"
            ]
        )

        self.assertTrue(
            spread[
                "usable_for_runtime_costs"
            ]
        )

        self.assertAlmostEqual(
            spread[
                "spread_price"
            ],
            0.2,
            places=8,
        )

        self.assertAlmostEqual(
            spread[
                "spread_ticks"
            ],
            20.0,
            places=8,
        )

        self.assertIsNotNone(
            spread[
                "spread_bps"
            ]
        )

        self.assertIsNotNone(
            spread[
                "spread_atr14"
            ]
        )

        fingerprint = (
            snapshot[
                "contract_fingerprint"
            ][
                "sha256"
            ]
        )

        self.assertEqual(
            len(
                fingerprint
            ),
            64,
        )

        self.assertEqual(
            snapshot[
                "broker_identity"
            ][
                "server"
            ],
            "ICMarketsSC-MT5-3",
        )

        self.assertFalse(
            snapshot[
                "broker_identity"
            ][
                "account_login_emitted"
            ]
        )

        self.assertFalse(
            snapshot[
                "broker_identity"
            ][
                "account_holder_name_emitted"
            ]
        )


if __name__ == "__main__":

    unittest.main(
        verbosity=2
    )