"""
===============================================================================
Module      : mt5_read_only_fill_telemetry_adapter.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : MT5 / Exness Read-Only Fill -> Normalized Actual Fill Telemetry
===============================================================================

Status
------
SHADOW / RESEARCH / DEMO ONLY.

Purpose
-------
Read already-completed MetaTrader 5 order deals plus historical Bid/Ask ticks,
aggregate broker partial fills, reconstruct causal fill-time quotes, normalize
commission/fee cost, and emit NormalizedActualFillTelemetry for the existing
RealizedFillTelemetryBridge.

Read-only broker boundary
-------------------------
This adapter only uses:

- history_deals_get(...)
- copy_ticks_range(...)
- last_error() for diagnostics

It does NOT:

- initialize or shut down MT5 implicitly,
- send trade requests,
- place/modify/cancel orders,
- open/close/modify positions,
- alter SL/TP,
- size a trade,
- modify trade_ready,
- modify production RiskEngine,
- mutate lifecycle/accounting state,
- call the realized-cost bridge,
- authorize live execution.

The caller owns terminal connection lifecycle.

Order-centric semantics
-----------------------
MetaTrader 5 history_deals_get(ticket=...) filters by DEAL_ORDER, therefore
the adapter is intentionally keyed by order ticket.

An order may contain multiple partial-fill deals. They are aggregated only
when:

- every selected deal is a BUY/SELL trading deal,
- every selected deal is an entry deal,
- symbol and direction are consistent,
- deal tickets are unique,
- total filled volume exactly matches expected_volume within tolerance.

Incomplete fills and overfills fail closed.

Causal quote reconstruction
---------------------------
For every deal the adapter chooses the latest valid historical Bid/Ask tick
whose time_msc is <= deal.time_msc.

Post-fill ticks are never used as a fallback.

For multi-deal fills, fill price, Bid, and Ask are volume weighted. This keeps
aggregate price-distance economics consistent with the downstream realized-fill
telemetry bridge.

Commission / fee normalization
------------------------------
MT5 commission and fee values are expected to be zero or negative when they
represent costs.

They are normalized as:

    commission_cost = -(sum(commission) + sum(fee))

Positive commission/fee values may represent rebates or broker-specific
semantics which the current normalized telemetry contract cannot represent
without losing sign. They therefore fail closed.

Safety
------
Every result has:

    live_authorized = False
"""

from __future__ import annotations

import importlib
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Sequence


telemetry_module: Any = importlib.import_module(
    "02_AI.Shadow.realized_fill_telemetry_bridge"
)

NormalizedActualFillTelemetry: Any = (
    telemetry_module.NormalizedActualFillTelemetry
)


@dataclass(frozen=True)
class MT5ReadOnlyFillPolicy:
    quote_lookback_ms: int = 2000
    volume_tolerance: float = 1e-8
    numeric_tolerance: float = 1e-10


@dataclass(frozen=True)
class MT5ReadOnlyFillTelemetryResult:
    valid: bool
    normalized: bool
    reason: str
    action: str
    mode: str
    version: str
    live_authorized: bool

    order_ticket: int
    execution_id: str

    expected_symbol: str
    symbol: str

    expected_direction: str
    direction: str

    expected_volume: float
    filled_volume: float

    history_invoked: bool
    tick_history_invoked: bool

    raw_deal_count: int
    selected_deal_count: int
    deal_tickets: tuple[int, ...]

    first_deal_time_msc: int
    last_deal_time_msc: int

    weighted_fill_price: float
    weighted_quote_bid: float
    weighted_quote_ask: float
    weighted_spread_price: float

    quote_age_ms_by_deal: tuple[
        tuple[
            int,
            int,
        ],
        ...,
    ]

    max_quote_age_ms: int

    raw_commission_sum: float
    raw_fee_sum: float
    normalized_commission_cost: float

    mt5_error: str

    telemetry: Any


@dataclass(frozen=True)
class _Deal:
    ticket: int
    order: int
    time_msc: int
    type: int
    entry: int
    volume: float
    price: float
    commission: float
    fee: float
    symbol: str
    direction: str


@dataclass(frozen=True)
class _Tick:
    time_msc: int
    bid: float
    ask: float


class SimpleMT5Constants:
    """
    Minimal constants for pure offline record normalization.

    The live read path uses constants exposed by the injected/lazy-loaded
    MetaTrader5 API.
    """

    DEAL_TYPE_BUY = 0
    DEAL_TYPE_SELL = 1
    DEAL_ENTRY_IN = 0


class MT5ReadOnlyFillTelemetryAdapter:
    VERSION = "1.0"

    MODE = (
        "SHADOW_MT5_READ_ONLY_FILL_TELEMETRY_ADAPTER_ONLY"
    )

    def __init__(
        self,
        *,
        mt5_api: Any | None = None,
        policy: MT5ReadOnlyFillPolicy | None = None,
    ) -> None:

        self._mt5_api = mt5_api

        self.policy = (
            policy
            if policy is not None
            else MT5ReadOnlyFillPolicy()
        )

        self._validate_policy()

    # =========================================================================
    # Policy / API
    # =========================================================================

    def _validate_policy(
        self,
    ) -> None:

        if (
            not isinstance(
                self.policy.quote_lookback_ms,
                int,
            )
            or
            self.policy.quote_lookback_ms <= 0
        ):

            raise ValueError(
                "quote_lookback_ms must be a positive integer"
            )

        if (
            not math.isfinite(
                float(
                    self.policy.volume_tolerance
                )
            )
            or
            self.policy.volume_tolerance <= 0.0
        ):

            raise ValueError(
                "volume_tolerance must be positive"
            )

        if (
            not math.isfinite(
                float(
                    self.policy.numeric_tolerance
                )
            )
            or
            self.policy.numeric_tolerance <= 0.0
        ):

            raise ValueError(
                "numeric_tolerance must be positive"
            )

    def _api(
        self,
    ) -> Any:

        if self._mt5_api is not None:

            return self._mt5_api

        return importlib.import_module(
            "MetaTrader5"
        )

    # =========================================================================
    # Generic helpers
    # =========================================================================

    @staticmethod
    def _field(
        value: Any,
        name: str,
        default: Any = None,
    ) -> Any:

        if value is None:

            return default

        if isinstance(
            value,
            dict,
        ):

            return value.get(
                name,
                default,
            )

        if hasattr(
            value,
            name,
        ):

            return getattr(
                value,
                name,
            )

        dtype = getattr(
            value,
            "dtype",
            None,
        )

        names = getattr(
            dtype,
            "names",
            None,
        )

        if (
            names is not None
            and
            name in names
        ):

            try:

                result = value[
                    name
                ]

                if hasattr(
                    result,
                    "item",
                ):

                    return result.item()

                return result

            except Exception:

                return default

        try:

            return value[
                name
            ]

        except Exception:

            return default

    @staticmethod
    def _number(
        value: Any,
    ) -> float:

        try:

            resolved = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return math.nan

        if not math.isfinite(
            resolved
        ):

            return math.nan

        return resolved

    @staticmethod
    def _integer(
        value: Any,
    ) -> int | None:

        try:

            return int(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return None

    @staticmethod
    def _direction(
        value: str,
    ) -> str:

        resolved = str(
            value
        ).strip().upper()

        if resolved in {
            "LONG",
            "BUY",
            "BULLISH",
        }:

            return "LONG"

        if resolved in {
            "SHORT",
            "SELL",
            "BEARISH",
        }:

            return "SHORT"

        return "INVALID"

    @staticmethod
    def _symbol(
        value: Any,
    ) -> str:

        return str(
            value
        ).strip()

    def _volume_close(
        self,
        left: float,
        right: float,
    ) -> bool:

        return math.isclose(
            left,
            right,
            rel_tol=0.0,
            abs_tol=self.policy.volume_tolerance,
        )

    def _numeric_close(
        self,
        left: float,
        right: float,
    ) -> bool:

        return math.isclose(
            left,
            right,
            rel_tol=0.0,
            abs_tol=self.policy.numeric_tolerance,
        )

    @staticmethod
    def _last_error(
        api: Any,
    ) -> str:

        try:

            return str(
                api.last_error()
            )

        except Exception:

            return "unavailable"

    @staticmethod
    def _constant(
        api: Any,
        name: str,
        fallback: int,
    ) -> int:

        value = getattr(
            api,
            name,
            fallback,
        )

        try:

            return int(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return fallback

    # =========================================================================
    # Result helpers
    # =========================================================================

    def _result(
        self,
        *,
        valid: bool,
        normalized: bool,
        reason: str,
        order_ticket: int,
        expected_symbol: str,
        expected_direction: str,
        expected_volume: float,
        history_invoked: bool,
        tick_history_invoked: bool,
        raw_deal_count: int = 0,
        selected_deal_count: int = 0,
        deal_tickets: tuple[int, ...] = (),
        first_deal_time_msc: int = 0,
        last_deal_time_msc: int = 0,
        symbol: str = "",
        direction: str = "",
        filled_volume: float = 0.0,
        weighted_fill_price: float = 0.0,
        weighted_quote_bid: float = 0.0,
        weighted_quote_ask: float = 0.0,
        quote_age_ms_by_deal: tuple[
            tuple[
                int,
                int,
            ],
            ...,
        ] = (),
        raw_commission_sum: float = 0.0,
        raw_fee_sum: float = 0.0,
        normalized_commission_cost: float = 0.0,
        mt5_error: str = "",
        telemetry: Any = None,
    ) -> MT5ReadOnlyFillTelemetryResult:

        weighted_spread = (
            weighted_quote_ask
            -
            weighted_quote_bid
        )

        if (
            weighted_spread < 0.0
            and
            abs(
                weighted_spread
            )
            <=
            self.policy.numeric_tolerance
        ):

            weighted_spread = 0.0

        ages = tuple(
            (
                int(
                    ticket
                ),
                int(
                    age
                ),
            )
            for (
                ticket,
                age,
            )
            in quote_age_ms_by_deal
        )

        max_age = max(
            (
                age
                for (
                    _,
                    age,
                )
                in ages
            ),
            default=0,
        )

        return MT5ReadOnlyFillTelemetryResult(
            valid=valid,
            normalized=normalized,
            reason=reason,
            action=(
                "NORMALIZE_MT5_COMPLETED_ORDER_FILL"
                if normalized
                else
                "NO_ACTION"
            ),
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            order_ticket=int(
                order_ticket
            ),
            execution_id=(
                f"MT5_ORDER_{int(order_ticket)}"
                if int(
                    order_ticket
                ) > 0
                else
                ""
            ),
            expected_symbol=expected_symbol,
            symbol=symbol,
            expected_direction=expected_direction,
            direction=direction,
            expected_volume=round(
                expected_volume,
                8,
            ),
            filled_volume=round(
                filled_volume,
                8,
            ),
            history_invoked=history_invoked,
            tick_history_invoked=tick_history_invoked,
            raw_deal_count=int(
                raw_deal_count
            ),
            selected_deal_count=int(
                selected_deal_count
            ),
            deal_tickets=deal_tickets,
            first_deal_time_msc=int(
                first_deal_time_msc
            ),
            last_deal_time_msc=int(
                last_deal_time_msc
            ),
            weighted_fill_price=round(
                weighted_fill_price,
                8,
            ),
            weighted_quote_bid=round(
                weighted_quote_bid,
                8,
            ),
            weighted_quote_ask=round(
                weighted_quote_ask,
                8,
            ),
            weighted_spread_price=round(
                weighted_spread,
                8,
            ),
            quote_age_ms_by_deal=ages,
            max_quote_age_ms=int(
                max_age
            ),
            raw_commission_sum=round(
                raw_commission_sum,
                8,
            ),
            raw_fee_sum=round(
                raw_fee_sum,
                8,
            ),
            normalized_commission_cost=round(
                normalized_commission_cost,
                8,
            ),
            mt5_error=str(
                mt5_error
            ),
            telemetry=telemetry,
        )

    def _invalid(
        self,
        *,
        reason: str,
        order_ticket: int,
        expected_symbol: str,
        expected_direction: str,
        expected_volume: float,
        history_invoked: bool,
        tick_history_invoked: bool,
        **kwargs: Any,
    ) -> MT5ReadOnlyFillTelemetryResult:

        return self._result(
            valid=False,
            normalized=False,
            reason=reason,
            order_ticket=order_ticket,
            expected_symbol=expected_symbol,
            expected_direction=expected_direction,
            expected_volume=expected_volume,
            history_invoked=history_invoked,
            tick_history_invoked=tick_history_invoked,
            **kwargs,
        )

    # =========================================================================
    # Deal normalization
    # =========================================================================

    def _normalize_deals(
        self,
        *,
        api: Any,
        raw_deals: Sequence[Any],
        order_ticket: int,
        expected_symbol: str,
        expected_direction: str,
        expected_volume: float,
    ) -> tuple[
        bool,
        str,
        tuple[
            _Deal,
            ...,
        ],
        dict[
            str,
            Any,
        ],
    ]:

        buy_type = self._constant(
            api,
            "DEAL_TYPE_BUY",
            0,
        )

        sell_type = self._constant(
            api,
            "DEAL_TYPE_SELL",
            1,
        )

        entry_in = self._constant(
            api,
            "DEAL_ENTRY_IN",
            0,
        )

        selected: list[
            _Deal
        ] = []

        seen_tickets: set[
            int
        ] = set()

        diagnostics: dict[
            str,
            Any,
        ] = {
            "raw_deal_count": len(
                raw_deals
            ),
        }

        for raw in raw_deals:

            raw_volume = self._number(
                self._field(
                    raw,
                    "volume",
                    0.0,
                )
            )

            raw_type = self._integer(
                self._field(
                    raw,
                    "type",
                    None,
                )
            )

            if (
                not math.isfinite(
                    raw_volume
                )
                or
                raw_volume < 0.0
            ):

                return (
                    False,
                    "INVALID_DEAL_VOLUME",
                    (),
                    diagnostics,
                )

            # Balance/credit/history metadata rows carry no trade volume.
            if (
                raw_volume
                <=
                self.policy.volume_tolerance
            ):

                continue

            if raw_type not in {
                buy_type,
                sell_type,
            }:

                return (
                    False,
                    "NON_BUY_SELL_DEAL_FOR_ORDER",
                    (),
                    diagnostics,
                )

            ticket = self._integer(
                self._field(
                    raw,
                    "ticket",
                    None,
                )
            )

            deal_order = self._integer(
                self._field(
                    raw,
                    "order",
                    None,
                )
            )

            time_msc = self._integer(
                self._field(
                    raw,
                    "time_msc",
                    None,
                )
            )

            entry = self._integer(
                self._field(
                    raw,
                    "entry",
                    None,
                )
            )

            price = self._number(
                self._field(
                    raw,
                    "price",
                    None,
                )
            )

            commission = self._number(
                self._field(
                    raw,
                    "commission",
                    0.0,
                )
            )

            fee = self._number(
                self._field(
                    raw,
                    "fee",
                    0.0,
                )
            )

            symbol = self._symbol(
                self._field(
                    raw,
                    "symbol",
                    "",
                )
            )

            if (
                ticket is None
                or
                ticket <= 0
            ):

                return (
                    False,
                    "INVALID_DEAL_TICKET",
                    (),
                    diagnostics,
                )

            if ticket in seen_tickets:

                return (
                    False,
                    "DUPLICATE_DEAL_TICKET",
                    (),
                    diagnostics,
                )

            seen_tickets.add(
                ticket
            )

            if (
                deal_order is None
                or
                deal_order
                !=
                order_ticket
            ):

                return (
                    False,
                    "DEAL_ORDER_LINKAGE_MISMATCH",
                    (),
                    diagnostics,
                )

            if (
                time_msc is None
                or
                time_msc <= 0
            ):

                return (
                    False,
                    "INVALID_DEAL_TIME_MSC",
                    (),
                    diagnostics,
                )

            if entry != entry_in:

                return (
                    False,
                    "NON_ENTRY_DEAL_NOT_SUPPORTED",
                    (),
                    diagnostics,
                )

            if (
                not math.isfinite(
                    price
                )
                or
                price <= 0.0
            ):

                return (
                    False,
                    "INVALID_DEAL_PRICE",
                    (),
                    diagnostics,
                )

            if (
                not math.isfinite(
                    commission
                )
                or
                not math.isfinite(
                    fee
                )
            ):

                return (
                    False,
                    "INVALID_DEAL_COMMISSION_OR_FEE",
                    (),
                    diagnostics,
                )

            if (
                commission
                >
                self.policy.numeric_tolerance
                or
                fee
                >
                self.policy.numeric_tolerance
            ):

                return (
                    False,
                    "POSITIVE_COMMISSION_OR_FEE_NOT_SUPPORTED",
                    (),
                    diagnostics,
                )

            if not symbol:

                return (
                    False,
                    "INVALID_DEAL_SYMBOL",
                    (),
                    diagnostics,
                )

            direction = (
                "LONG"
                if raw_type == buy_type
                else
                "SHORT"
            )

            selected.append(
                _Deal(
                    ticket=ticket,
                    order=deal_order,
                    time_msc=time_msc,
                    type=raw_type,
                    entry=entry,
                    volume=raw_volume,
                    price=price,
                    commission=commission,
                    fee=fee,
                    symbol=symbol,
                    direction=direction,
                )
            )

        if not selected:

            return (
                False,
                "NO_ENTRY_FILL_DEALS",
                (),
                diagnostics,
            )

        selected.sort(
            key=lambda deal: (
                deal.time_msc,
                deal.ticket,
            )
        )

        symbols = {
            deal.symbol.upper()
            for deal
            in selected
        }

        if len(
            symbols
        ) != 1:

            return (
                False,
                "MIXED_FILL_SYMBOLS",
                (),
                diagnostics,
            )

        directions = {
            deal.direction
            for deal
            in selected
        }

        if len(
            directions
        ) != 1:

            return (
                False,
                "MIXED_FILL_DIRECTIONS",
                (),
                diagnostics,
            )

        actual_symbol = (
            selected[
                0
            ].symbol
        )

        actual_direction = (
            selected[
                0
            ].direction
        )

        if (
            actual_symbol.upper()
            !=
            expected_symbol.upper()
        ):

            return (
                False,
                "EXPECTED_SYMBOL_MISMATCH",
                (),
                diagnostics,
            )

        if (
            actual_direction
            !=
            expected_direction
        ):

            return (
                False,
                "EXPECTED_DIRECTION_MISMATCH",
                (),
                diagnostics,
            )

        total_volume = sum(
            deal.volume
            for deal
            in selected
        )

        diagnostics.update(
            {
                "selected_deal_count": len(
                    selected
                ),
                "deal_tickets": tuple(
                    deal.ticket
                    for deal
                    in selected
                ),
                "first_deal_time_msc": (
                    selected[
                        0
                    ].time_msc
                ),
                "last_deal_time_msc": (
                    selected[
                        -1
                    ].time_msc
                ),
                "symbol": actual_symbol,
                "direction": actual_direction,
                "filled_volume": total_volume,
                "raw_commission_sum": sum(
                    deal.commission
                    for deal
                    in selected
                ),
                "raw_fee_sum": sum(
                    deal.fee
                    for deal
                    in selected
                ),
            }
        )

        if not self._volume_close(
            total_volume,
            expected_volume,
        ):

            return (
                False,
                "PARTIAL_OR_OVERFILL_VOLUME_MISMATCH",
                tuple(
                    selected
                ),
                diagnostics,
            )

        return (
            True,
            "",
            tuple(
                selected
            ),
            diagnostics,
        )

    # =========================================================================
    # Tick normalization
    # =========================================================================

    def _normalize_ticks(
        self,
        raw_ticks: Iterable[Any],
    ) -> tuple[
        _Tick,
        ...,
    ]:

        normalized: list[
            _Tick
        ] = []

        for raw in raw_ticks:

            time_msc = self._integer(
                self._field(
                    raw,
                    "time_msc",
                    None,
                )
            )

            bid = self._number(
                self._field(
                    raw,
                    "bid",
                    None,
                )
            )

            ask = self._number(
                self._field(
                    raw,
                    "ask",
                    None,
                )
            )

            if (
                time_msc is None
                or
                time_msc <= 0
                or
                not math.isfinite(
                    bid
                )
                or
                not math.isfinite(
                    ask
                )
                or
                bid <= 0.0
                or
                ask <= 0.0
                or
                ask
                <
                (
                    bid
                    -
                    self.policy.numeric_tolerance
                )
            ):

                continue

            if (
                ask < bid
                and
                self._numeric_close(
                    ask,
                    bid,
                )
            ):

                ask = bid

            normalized.append(
                _Tick(
                    time_msc=time_msc,
                    bid=bid,
                    ask=ask,
                )
            )

        normalized.sort(
            key=lambda tick: (
                tick.time_msc,
                tick.bid,
                tick.ask,
            )
        )

        return tuple(
            normalized
        )

    def _causal_quotes(
        self,
        *,
        deals: tuple[
            _Deal,
            ...,
        ],
        ticks: tuple[
            _Tick,
            ...,
        ],
    ) -> tuple[
        bool,
        str,
        tuple[
            tuple[
                _Deal,
                _Tick,
                int,
            ],
            ...,
        ],
    ]:

        if not ticks:

            return (
                False,
                "NO_VALID_QUOTE_TICKS",
                (),
            )

        matched: list[
            tuple[
                _Deal,
                _Tick,
                int,
            ]
        ] = []

        for deal in deals:

            eligible = [
                tick
                for tick
                in ticks
                if tick.time_msc
                <=
                deal.time_msc
            ]

            if not eligible:

                return (
                    False,
                    "NO_CAUSAL_QUOTE_FOR_FILL",
                    (),
                )

            tick = max(
                eligible,
                key=lambda value: (
                    value.time_msc,
                ),
            )

            age_ms = (
                deal.time_msc
                -
                tick.time_msc
            )

            if (
                age_ms < 0
                or
                age_ms
                >
                self.policy.quote_lookback_ms
            ):

                return (
                    False,
                    "CAUSAL_QUOTE_OUTSIDE_LOOKBACK",
                    (),
                )

            matched.append(
                (
                    deal,
                    tick,
                    age_ms,
                )
            )

        return (
            True,
            "",
            tuple(
                matched
            ),
        )

    # =========================================================================
    # Input validation
    # =========================================================================

    def _inputs(
        self,
        *,
        order_ticket: Any,
        expected_symbol: Any,
        expected_direction: Any,
        expected_volume: Any,
    ) -> tuple[
        bool,
        str,
        int,
        str,
        str,
        float,
    ]:

        try:

            order = int(
                order_ticket
            )

        except (
            TypeError,
            ValueError,
        ):

            order = 0

        symbol = self._symbol(
            expected_symbol
        )

        direction = self._direction(
            expected_direction
        )

        volume = self._number(
            expected_volume
        )

        if order <= 0:

            return (
                False,
                "INVALID_ORDER_TICKET",
                order,
                symbol,
                direction,
                (
                    volume
                    if math.isfinite(
                        volume
                    )
                    else
                    0.0
                ),
            )

        if not symbol:

            return (
                False,
                "INVALID_EXPECTED_SYMBOL",
                order,
                symbol,
                direction,
                (
                    volume
                    if math.isfinite(
                        volume
                    )
                    else
                    0.0
                ),
            )

        if direction == "INVALID":

            return (
                False,
                "INVALID_EXPECTED_DIRECTION",
                order,
                symbol,
                direction,
                (
                    volume
                    if math.isfinite(
                        volume
                    )
                    else
                    0.0
                ),
            )

        if (
            not math.isfinite(
                volume
            )
            or
            volume <= 0.0
        ):

            return (
                False,
                "INVALID_EXPECTED_VOLUME",
                order,
                symbol,
                direction,
                0.0,
            )

        return (
            True,
            "",
            order,
            symbol,
            direction,
            volume,
        )

    # =========================================================================
    # Pure normalization from already-read records
    # =========================================================================

    def normalize_records(
        self,
        *,
        raw_deals: Sequence[Any],
        raw_ticks: Sequence[Any],
        order_ticket: int,
        expected_symbol: str,
        expected_direction: str,
        expected_volume: float,
        mt5_api: Any | None = None,
    ) -> MT5ReadOnlyFillTelemetryResult:

        (
            inputs_valid,
            inputs_reason,
            order,
            symbol,
            direction,
            volume,
        ) = self._inputs(
            order_ticket=order_ticket,
            expected_symbol=expected_symbol,
            expected_direction=expected_direction,
            expected_volume=expected_volume,
        )

        if not inputs_valid:

            return self._invalid(
                reason=inputs_reason,
                order_ticket=order,
                expected_symbol=symbol,
                expected_direction=direction,
                expected_volume=volume,
                history_invoked=False,
                tick_history_invoked=False,
            )

        api = (
            mt5_api
            if mt5_api is not None
            else (
                self._mt5_api
                if self._mt5_api is not None
                else
                SimpleMT5Constants()
            )
        )

        (
            deals_valid,
            deals_reason,
            deals,
            diagnostics,
        ) = self._normalize_deals(
            api=api,
            raw_deals=raw_deals,
            order_ticket=order,
            expected_symbol=symbol,
            expected_direction=direction,
            expected_volume=volume,
        )

        if not deals_valid:

            return self._invalid(
                reason=deals_reason,
                order_ticket=order,
                expected_symbol=symbol,
                expected_direction=direction,
                expected_volume=volume,
                history_invoked=False,
                tick_history_invoked=False,
                **diagnostics,
            )

        ticks = self._normalize_ticks(
            raw_ticks
        )

        (
            quote_valid,
            quote_reason,
            matched,
        ) = self._causal_quotes(
            deals=deals,
            ticks=ticks,
        )

        if not quote_valid:

            return self._invalid(
                reason=quote_reason,
                order_ticket=order,
                expected_symbol=symbol,
                expected_direction=direction,
                expected_volume=volume,
                history_invoked=False,
                tick_history_invoked=False,
                **diagnostics,
            )

        total_volume = sum(
            deal.volume
            for (
                deal,
                _,
                _,
            )
            in matched
        )

        weighted_fill = (
            sum(
                deal.price
                *
                deal.volume
                for (
                    deal,
                    _,
                    _,
                )
                in matched
            )
            /
            total_volume
        )

        weighted_bid = (
            sum(
                tick.bid
                *
                deal.volume
                for (
                    deal,
                    tick,
                    _,
                )
                in matched
            )
            /
            total_volume
        )

        weighted_ask = (
            sum(
                tick.ask
                *
                deal.volume
                for (
                    deal,
                    tick,
                    _,
                )
                in matched
            )
            /
            total_volume
        )

        if (
            weighted_ask
            <
            (
                weighted_bid
                -
                self.policy.numeric_tolerance
            )
        ):

            return self._invalid(
                reason="AGGREGATED_QUOTE_INVERTED",
                order_ticket=order,
                expected_symbol=symbol,
                expected_direction=direction,
                expected_volume=volume,
                history_invoked=False,
                tick_history_invoked=False,
                **diagnostics,
            )

        raw_commission = sum(
            deal.commission
            for deal
            in deals
        )

        raw_fee = sum(
            deal.fee
            for deal
            in deals
        )

        normalized_commission = -(
            raw_commission
            +
            raw_fee
        )

        if (
            normalized_commission < 0.0
            and
            abs(
                normalized_commission
            )
            <=
            self.policy.numeric_tolerance
        ):

            normalized_commission = 0.0

        if normalized_commission < 0.0:

            return self._invalid(
                reason="INVALID_NORMALIZED_COMMISSION_COST",
                order_ticket=order,
                expected_symbol=symbol,
                expected_direction=direction,
                expected_volume=volume,
                history_invoked=False,
                tick_history_invoked=False,
                **diagnostics,
            )

        telemetry = NormalizedActualFillTelemetry(
            execution_id=(
                f"MT5_ORDER_{order}"
            ),
            filled_volume=total_volume,
            fill_price=weighted_fill,
            quote_bid=weighted_bid,
            quote_ask=weighted_ask,
            commission_cost=normalized_commission,
            live_authorized=False,
        )

        quote_ages = tuple(
            (
                deal.ticket,
                age_ms,
            )
            for (
                deal,
                _,
                age_ms,
            )
            in matched
        )

        return self._result(
            valid=True,
            normalized=True,
            reason=(
                "OK_MT5_COMPLETED_ORDER_FILL_NORMALIZED"
            ),
            order_ticket=order,
            expected_symbol=symbol,
            expected_direction=direction,
            expected_volume=volume,
            history_invoked=False,
            tick_history_invoked=False,
            raw_deal_count=diagnostics[
                "raw_deal_count"
            ],
            selected_deal_count=diagnostics[
                "selected_deal_count"
            ],
            deal_tickets=diagnostics[
                "deal_tickets"
            ],
            first_deal_time_msc=diagnostics[
                "first_deal_time_msc"
            ],
            last_deal_time_msc=diagnostics[
                "last_deal_time_msc"
            ],
            symbol=diagnostics[
                "symbol"
            ],
            direction=diagnostics[
                "direction"
            ],
            filled_volume=total_volume,
            weighted_fill_price=weighted_fill,
            weighted_quote_bid=weighted_bid,
            weighted_quote_ask=weighted_ask,
            quote_age_ms_by_deal=quote_ages,
            raw_commission_sum=raw_commission,
            raw_fee_sum=raw_fee,
            normalized_commission_cost=(
                normalized_commission
            ),
            telemetry=telemetry,
        )

    # =========================================================================
    # MT5 read path
    # =========================================================================

    def read_order_fill(
        self,
        *,
        order_ticket: int,
        expected_symbol: str,
        expected_direction: str,
        expected_volume: float,
    ) -> MT5ReadOnlyFillTelemetryResult:

        (
            inputs_valid,
            inputs_reason,
            order,
            symbol,
            direction,
            volume,
        ) = self._inputs(
            order_ticket=order_ticket,
            expected_symbol=expected_symbol,
            expected_direction=expected_direction,
            expected_volume=expected_volume,
        )

        if not inputs_valid:

            return self._invalid(
                reason=inputs_reason,
                order_ticket=order,
                expected_symbol=symbol,
                expected_direction=direction,
                expected_volume=volume,
                history_invoked=False,
                tick_history_invoked=False,
            )

        try:

            api = self._api()

        except Exception as exc:

            return self._invalid(
                reason="MT5_API_IMPORT_FAILED",
                order_ticket=order,
                expected_symbol=symbol,
                expected_direction=direction,
                expected_volume=volume,
                history_invoked=False,
                tick_history_invoked=False,
                mt5_error=str(
                    exc
                ),
            )

        try:

            raw_deals = api.history_deals_get(
                ticket=order
            )

        except Exception as exc:

            return self._invalid(
                reason=(
                    "MT5_DEAL_HISTORY_READ_EXCEPTION"
                ),
                order_ticket=order,
                expected_symbol=symbol,
                expected_direction=direction,
                expected_volume=volume,
                history_invoked=True,
                tick_history_invoked=False,
                mt5_error=str(
                    exc
                ),
            )

        if raw_deals is None:

            return self._invalid(
                reason=(
                    "MT5_DEAL_HISTORY_READ_FAILED"
                ),
                order_ticket=order,
                expected_symbol=symbol,
                expected_direction=direction,
                expected_volume=volume,
                history_invoked=True,
                tick_history_invoked=False,
                mt5_error=self._last_error(
                    api
                ),
            )

        try:

            raw_deal_sequence = tuple(
                raw_deals
            )

        except Exception:

            return self._invalid(
                reason=(
                    "INVALID_MT5_DEAL_HISTORY_RESULT"
                ),
                order_ticket=order,
                expected_symbol=symbol,
                expected_direction=direction,
                expected_volume=volume,
                history_invoked=True,
                tick_history_invoked=False,
            )

        (
            deals_valid,
            deals_reason,
            deals,
            diagnostics,
        ) = self._normalize_deals(
            api=api,
            raw_deals=raw_deal_sequence,
            order_ticket=order,
            expected_symbol=symbol,
            expected_direction=direction,
            expected_volume=volume,
        )

        if not deals_valid:

            return self._invalid(
                reason=deals_reason,
                order_ticket=order,
                expected_symbol=symbol,
                expected_direction=direction,
                expected_volume=volume,
                history_invoked=True,
                tick_history_invoked=False,
                **diagnostics,
            )

        first_ms = deals[
            0
        ].time_msc

        last_ms = deals[
            -1
        ].time_msc

        date_from = datetime.fromtimestamp(
            (
                first_ms
                -
                self.policy.quote_lookback_ms
            )
            /
            1000.0,
            tz=timezone.utc,
        )

        date_to = (
            datetime.fromtimestamp(
                last_ms
                /
                1000.0,
                tz=timezone.utc,
            )
            +
            timedelta(
                milliseconds=1
            )
        )

        tick_flag = getattr(
            api,
            "COPY_TICKS_INFO",
            getattr(
                api,
                "COPY_TICKS_ALL",
                None,
            ),
        )

        if tick_flag is None:

            return self._invalid(
                reason="MT5_TICK_FLAG_UNAVAILABLE",
                order_ticket=order,
                expected_symbol=symbol,
                expected_direction=direction,
                expected_volume=volume,
                history_invoked=True,
                tick_history_invoked=False,
                **diagnostics,
            )

        actual_symbol = deals[
            0
        ].symbol

        try:

            raw_ticks = api.copy_ticks_range(
                actual_symbol,
                date_from,
                date_to,
                tick_flag,
            )

        except Exception as exc:

            return self._invalid(
                reason=(
                    "MT5_TICK_HISTORY_READ_EXCEPTION"
                ),
                order_ticket=order,
                expected_symbol=symbol,
                expected_direction=direction,
                expected_volume=volume,
                history_invoked=True,
                tick_history_invoked=True,
                mt5_error=str(
                    exc
                ),
                **diagnostics,
            )

        if raw_ticks is None:

            return self._invalid(
                reason=(
                    "MT5_TICK_HISTORY_READ_FAILED"
                ),
                order_ticket=order,
                expected_symbol=symbol,
                expected_direction=direction,
                expected_volume=volume,
                history_invoked=True,
                tick_history_invoked=True,
                mt5_error=self._last_error(
                    api
                ),
                **diagnostics,
            )

        try:

            raw_tick_sequence = tuple(
                raw_ticks
            )

        except Exception:

            return self._invalid(
                reason=(
                    "INVALID_MT5_TICK_HISTORY_RESULT"
                ),
                order_ticket=order,
                expected_symbol=symbol,
                expected_direction=direction,
                expected_volume=volume,
                history_invoked=True,
                tick_history_invoked=True,
                **diagnostics,
            )

        normalized = self.normalize_records(
            raw_deals=raw_deal_sequence,
            raw_ticks=raw_tick_sequence,
            order_ticket=order,
            expected_symbol=symbol,
            expected_direction=direction,
            expected_volume=volume,
            mt5_api=api,
        )

        return self._result(
            valid=normalized.valid,
            normalized=normalized.normalized,
            reason=normalized.reason,
            order_ticket=normalized.order_ticket,
            expected_symbol=normalized.expected_symbol,
            expected_direction=(
                normalized.expected_direction
            ),
            expected_volume=normalized.expected_volume,
            history_invoked=True,
            tick_history_invoked=True,
            raw_deal_count=normalized.raw_deal_count,
            selected_deal_count=(
                normalized.selected_deal_count
            ),
            deal_tickets=normalized.deal_tickets,
            first_deal_time_msc=(
                normalized.first_deal_time_msc
            ),
            last_deal_time_msc=(
                normalized.last_deal_time_msc
            ),
            symbol=normalized.symbol,
            direction=normalized.direction,
            filled_volume=normalized.filled_volume,
            weighted_fill_price=(
                normalized.weighted_fill_price
            ),
            weighted_quote_bid=(
                normalized.weighted_quote_bid
            ),
            weighted_quote_ask=(
                normalized.weighted_quote_ask
            ),
            quote_age_ms_by_deal=(
                normalized.quote_age_ms_by_deal
            ),
            raw_commission_sum=(
                normalized.raw_commission_sum
            ),
            raw_fee_sum=normalized.raw_fee_sum,
            normalized_commission_cost=(
                normalized.normalized_commission_cost
            ),
            mt5_error=normalized.mt5_error,
            telemetry=normalized.telemetry,
        )


mt5_read_only_fill_telemetry_adapter = (
    MT5ReadOnlyFillTelemetryAdapter()
)