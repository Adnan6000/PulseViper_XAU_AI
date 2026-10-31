"""
MT5 read-only completed entry-fill adapter for forward/demo evidence capture.

Unlike the historical fill telemetry adapter, this module does not reconstruct
Bid/Ask from tick history. It reads completed order deals only, aggregates the
actual fill price/volume/commission, and emits CompletedExecutionFill.

The executable quote is supplied separately by
forward_execution_evidence_capture from evidence preserved before an external
execution owner submits the order.

SHADOW / RESEARCH / DEMO ONLY.

Broker boundary:
- history_deals_get(ticket=order_ticket)
- last_error() for diagnostics
- no copy_ticks_range
- no order_send
- no order/position modification
- no MT5 initialize/shutdown ownership
- no lifecycle/accounting mutation
- no live authorization
"""

from __future__ import annotations

import importlib
import math

from dataclasses import dataclass
from typing import Any, Sequence


_forward_module: Any = importlib.import_module(
    "02_AI.Shadow.forward_execution_evidence_capture"
)

CompletedExecutionFill: Any = (
    _forward_module.CompletedExecutionFill
)


@dataclass(frozen=True)
class MT5CompletedFillPolicy:
    volume_tolerance: float = 1e-8
    numeric_tolerance: float = 1e-10


@dataclass(frozen=True)
class MT5CompletedFillResult:
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
    weighted_fill_price: float

    raw_deal_count: int
    selected_deal_count: int

    deal_tickets: tuple[
        int,
        ...,
    ]

    first_deal_time_msc: int
    last_deal_time_msc: int

    raw_commission_sum: float
    raw_fee_sum: float
    normalized_commission_cost: float

    history_invoked: bool
    mt5_error: str

    completed_fill: Any


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


class SimpleMT5Constants:
    DEAL_TYPE_BUY = 0
    DEAL_TYPE_SELL = 1
    DEAL_ENTRY_IN = 0


class MT5ReadOnlyCompletedFillAdapter:
    VERSION = "1.0"

    MODE = (
        "SHADOW_MT5_READ_ONLY_COMPLETED_FILL_ADAPTER_ONLY"
    )

    def __init__(
        self,
        *,
        mt5_api: Any | None = None,
        policy: MT5CompletedFillPolicy | None = None,
    ) -> None:
        self._mt5_api = mt5_api

        self.policy = (
            policy
            if policy is not None
            else MT5CompletedFillPolicy()
        )

        self._validate_policy()

    # =========================================================================
    # Policy / API
    # =========================================================================

    def _validate_policy(
        self,
    ) -> None:
        for (
            name,
            value,
        ) in (
            (
                "volume_tolerance",
                self.policy.volume_tolerance,
            ),
            (
                "numeric_tolerance",
                self.policy.numeric_tolerance,
            ),
        ):
            try:
                resolved = float(
                    value
                )

            except (
                TypeError,
                ValueError,
            ) as exc:
                raise ValueError(
                    f"{name} must be numeric"
                ) from exc

            if (
                not math.isfinite(
                    resolved
                )
                or
                resolved <= 0.0
            ):
                raise ValueError(
                    f"{name} must be positive"
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
        if isinstance(
            value,
            bool,
        ):
            return None

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
        value: Any,
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
    def _last_error(
        api: Any,
    ) -> str:
        try:
            return str(
                api.last_error()
            )

        except Exception:
            return "unavailable"

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
        raw_deal_count: int = 0,
        selected_deal_count: int = 0,
        deal_tickets: tuple[
            int,
            ...,
        ] = (),
        first_deal_time_msc: int = 0,
        last_deal_time_msc: int = 0,
        symbol: str = "",
        direction: str = "",
        filled_volume: float = 0.0,
        weighted_fill_price: float = 0.0,
        raw_commission_sum: float = 0.0,
        raw_fee_sum: float = 0.0,
        normalized_commission_cost: float = 0.0,
        mt5_error: str = "",
        completed_fill: Any = None,
    ) -> MT5CompletedFillResult:
        execution_id = (
            f"MT5_ORDER_{order_ticket}"
            if order_ticket > 0
            else ""
        )

        return MT5CompletedFillResult(
            valid=valid,
            normalized=normalized,
            reason=reason,
            action=(
                "NORMALIZE_MT5_COMPLETED_FILL"
                if normalized
                else "NO_ACTION"
            ),
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            order_ticket=order_ticket,
            execution_id=execution_id,
            expected_symbol=expected_symbol,
            symbol=symbol,
            expected_direction=expected_direction,
            direction=direction,
            expected_volume=expected_volume,
            filled_volume=filled_volume,
            weighted_fill_price=weighted_fill_price,
            raw_deal_count=raw_deal_count,
            selected_deal_count=selected_deal_count,
            deal_tickets=deal_tickets,
            first_deal_time_msc=first_deal_time_msc,
            last_deal_time_msc=last_deal_time_msc,
            raw_commission_sum=raw_commission_sum,
            raw_fee_sum=raw_fee_sum,
            normalized_commission_cost=(
                normalized_commission_cost
            ),
            history_invoked=history_invoked,
            mt5_error=mt5_error,
            completed_fill=completed_fill,
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
        **diagnostics: Any,
    ) -> MT5CompletedFillResult:
        return self._result(
            valid=False,
            normalized=False,
            reason=reason,
            order_ticket=order_ticket,
            expected_symbol=expected_symbol,
            expected_direction=expected_direction,
            expected_volume=expected_volume,
            history_invoked=history_invoked,
            **diagnostics,
        )

    # =========================================================================
    # Public-input validation
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
        order = self._integer(
            order_ticket
        )

        if (
            order is None
            or
            order <= 0
        ):
            return (
                False,
                "INVALID_ORDER_TICKET",
                0,
                "",
                "",
                0.0,
            )

        symbol = str(
            expected_symbol
        ).strip()

        if not symbol:
            return (
                False,
                "INVALID_EXPECTED_SYMBOL",
                order,
                "",
                "",
                0.0,
            )

        direction = self._direction(
            expected_direction
        )

        if (
            direction
            ==
            "INVALID"
        ):
            return (
                False,
                "INVALID_EXPECTED_DIRECTION",
                order,
                symbol,
                "",
                0.0,
            )

        volume = self._number(
            expected_volume
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
    # Deal normalization
    # =========================================================================

    def _normalize_deals(
        self,
        *,
        api: Any,
        raw_deals: Sequence[
            Any
        ],
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
        buy = int(
            getattr(
                api,
                "DEAL_TYPE_BUY",
                0,
            )
        )

        sell = int(
            getattr(
                api,
                "DEAL_TYPE_SELL",
                1,
            )
        )

        entry_in = int(
            getattr(
                api,
                "DEAL_ENTRY_IN",
                0,
            )
        )

        raw_count = len(
            raw_deals
        )

        selected: list[
            _Deal
        ] = []

        seen_tickets: set[
            int
        ] = set()

        def diagnostics(
        ) -> dict[
            str,
            Any,
        ]:
            if not selected:
                return {
                    "raw_deal_count": raw_count,
                    "selected_deal_count": 0,
                }

            ordered = sorted(
                selected,
                key=lambda item: (
                    item.time_msc,
                    item.ticket,
                ),
            )

            return {
                "raw_deal_count": raw_count,
                "selected_deal_count": len(
                    ordered
                ),
                "deal_tickets": tuple(
                    item.ticket
                    for item
                    in ordered
                ),
                "first_deal_time_msc": (
                    ordered[
                        0
                    ].time_msc
                ),
                "last_deal_time_msc": (
                    ordered[
                        -1
                    ].time_msc
                ),
                "symbol": ordered[
                    0
                ].symbol,
                "direction": ordered[
                    0
                ].direction,
                "filled_volume": sum(
                    item.volume
                    for item
                    in ordered
                ),
                "raw_commission_sum": sum(
                    item.commission
                    for item
                    in ordered
                ),
                "raw_fee_sum": sum(
                    item.fee
                    for item
                    in ordered
                ),
            }

        for raw in raw_deals:
            volume = self._number(
                self._field(
                    raw,
                    "volume",
                    0.0,
                )
            )

            if not math.isfinite(
                volume
            ):
                return (
                    False,
                    "INVALID_DEAL_VOLUME",
                    (),
                    diagnostics(),
                )

            # MT5 history may contain non-trade metadata rows.
            if (
                abs(
                    volume
                )
                <=
                self.policy.volume_tolerance
            ):
                continue

            if volume < 0.0:
                return (
                    False,
                    "INVALID_DEAL_VOLUME",
                    (),
                    diagnostics(),
                )

            deal_type = self._integer(
                self._field(
                    raw,
                    "type",
                    None,
                )
            )

            if deal_type not in {
                buy,
                sell,
            }:
                return (
                    False,
                    "NON_BUY_SELL_DEAL_FOR_ORDER",
                    (),
                    diagnostics(),
                )

            ticket = self._integer(
                self._field(
                    raw,
                    "ticket",
                    None,
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
                    diagnostics(),
                )

            if (
                ticket
                in
                seen_tickets
            ):
                return (
                    False,
                    "DUPLICATE_DEAL_TICKET",
                    (),
                    diagnostics(),
                )

            linked_order = self._integer(
                self._field(
                    raw,
                    "order",
                    None,
                )
            )

            if (
                linked_order
                !=
                order_ticket
            ):
                return (
                    False,
                    "DEAL_ORDER_LINKAGE_MISMATCH",
                    (),
                    diagnostics(),
                )

            time_msc = self._integer(
                self._field(
                    raw,
                    "time_msc",
                    None,
                )
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
                    diagnostics(),
                )

            entry = self._integer(
                self._field(
                    raw,
                    "entry",
                    None,
                )
            )

            if (
                entry
                !=
                entry_in
            ):
                return (
                    False,
                    "NON_ENTRY_DEAL_NOT_SUPPORTED",
                    (),
                    diagnostics(),
                )

            price = self._number(
                self._field(
                    raw,
                    "price",
                    None,
                )
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
                    diagnostics(),
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
                    diagnostics(),
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
                    diagnostics(),
                )

            symbol = str(
                self._field(
                    raw,
                    "symbol",
                    "",
                )
            ).strip()

            if not symbol:
                return (
                    False,
                    "INVALID_DEAL_SYMBOL",
                    (),
                    diagnostics(),
                )

            direction = (
                "LONG"
                if deal_type == buy
                else "SHORT"
            )

            selected.append(
                _Deal(
                    ticket=ticket,
                    order=linked_order,
                    time_msc=time_msc,
                    type=deal_type,
                    entry=entry,
                    volume=volume,
                    price=price,
                    commission=commission,
                    fee=fee,
                    symbol=symbol,
                    direction=direction,
                )
            )

            seen_tickets.add(
                ticket
            )

        if not selected:
            return (
                False,
                "NO_ENTRY_FILL_DEALS",
                (),
                diagnostics(),
            )

        symbols = {
            item.symbol.upper()
            for item
            in selected
        }

        if len(
            symbols
        ) != 1:
            return (
                False,
                "MIXED_FILL_SYMBOLS",
                (),
                diagnostics(),
            )

        directions = {
            item.direction
            for item
            in selected
        }

        if len(
            directions
        ) != 1:
            return (
                False,
                "MIXED_FILL_DIRECTIONS",
                (),
                diagnostics(),
            )

        actual_symbol = selected[
            0
        ].symbol

        if (
            actual_symbol.upper()
            !=
            expected_symbol.upper()
        ):
            return (
                False,
                "EXPECTED_SYMBOL_MISMATCH",
                (),
                diagnostics(),
            )

        actual_direction = selected[
            0
        ].direction

        if (
            actual_direction
            !=
            expected_direction
        ):
            return (
                False,
                "EXPECTED_DIRECTION_MISMATCH",
                (),
                diagnostics(),
            )

        total_volume = sum(
            item.volume
            for item
            in selected
        )

        if not self._volume_close(
            total_volume,
            expected_volume,
        ):
            return (
                False,
                "PARTIAL_OR_OVERFILL_VOLUME_MISMATCH",
                (),
                diagnostics(),
            )

        ordered = tuple(
            sorted(
                selected,
                key=lambda item: (
                    item.time_msc,
                    item.ticket,
                ),
            )
        )

        return (
            True,
            "",
            ordered,
            diagnostics(),
        )

    # =========================================================================
    # Pure normalization
    # =========================================================================

    def normalize_records(
        self,
        *,
        raw_deals: Sequence[
            Any
        ],
        order_ticket: int,
        expected_symbol: str,
        expected_direction: str,
        expected_volume: float,
        mt5_api: Any | None = None,
    ) -> MT5CompletedFillResult:
        (
            valid_inputs,
            input_reason,
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

        if not valid_inputs:
            return self._invalid(
                reason=input_reason,
                order_ticket=order,
                expected_symbol=symbol,
                expected_direction=direction,
                expected_volume=volume,
                history_invoked=False,
            )

        try:
            raw_sequence = tuple(
                raw_deals
            )

        except Exception:
            return self._invalid(
                reason="INVALID_MT5_DEAL_HISTORY_RESULT",
                order_ticket=order,
                expected_symbol=symbol,
                expected_direction=direction,
                expected_volume=volume,
                history_invoked=False,
            )

        api = (
            mt5_api
            if mt5_api is not None
            else (
                self._mt5_api
                if self._mt5_api is not None
                else SimpleMT5Constants()
            )
        )

        (
            deals_valid,
            deal_reason,
            deals,
            diagnostics,
        ) = self._normalize_deals(
            api=api,
            raw_deals=raw_sequence,
            order_ticket=order,
            expected_symbol=symbol,
            expected_direction=direction,
            expected_volume=volume,
        )

        if not deals_valid:
            return self._invalid(
                reason=deal_reason,
                order_ticket=order,
                expected_symbol=symbol,
                expected_direction=direction,
                expected_volume=volume,
                history_invoked=False,
                **diagnostics,
            )

        total_volume = sum(
            item.volume
            for item
            in deals
        )

        weighted_fill = (
            sum(
                (
                    item.price
                    *
                    item.volume
                )
                for item
                in deals
            )
            /
            total_volume
        )

        raw_commission = sum(
            item.commission
            for item
            in deals
        )

        raw_fee = sum(
            item.fee
            for item
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
                reason=(
                    "INVALID_NORMALIZED_COMMISSION_COST"
                ),
                order_ticket=order,
                expected_symbol=symbol,
                expected_direction=direction,
                expected_volume=volume,
                history_invoked=False,
                **diagnostics,
            )

        completed_fill = CompletedExecutionFill(
            order_ticket=order,
            execution_id=(
                f"MT5_ORDER_{order}"
            ),
            symbol=deals[
                0
            ].symbol,
            direction=deals[
                0
            ].direction,
            filled_volume=total_volume,
            fill_price=weighted_fill,
            commission_cost=(
                normalized_commission
            ),
            live_authorized=False,
        )

        return self._result(
            valid=True,
            normalized=True,
            reason=(
                "OK_MT5_COMPLETED_FILL_NORMALIZED_WITHOUT_TICKS"
            ),
            order_ticket=order,
            expected_symbol=symbol,
            expected_direction=direction,
            expected_volume=volume,
            history_invoked=False,
            raw_deal_count=diagnostics[
                "raw_deal_count"
            ],
            selected_deal_count=len(
                deals
            ),
            deal_tickets=tuple(
                item.ticket
                for item
                in deals
            ),
            first_deal_time_msc=deals[
                0
            ].time_msc,
            last_deal_time_msc=deals[
                -1
            ].time_msc,
            symbol=deals[
                0
            ].symbol,
            direction=deals[
                0
            ].direction,
            filled_volume=total_volume,
            weighted_fill_price=weighted_fill,
            raw_commission_sum=raw_commission,
            raw_fee_sum=raw_fee,
            normalized_commission_cost=(
                normalized_commission
            ),
            completed_fill=completed_fill,
        )

    # =========================================================================
    # MT5 read-only path
    # =========================================================================

    def read_order_fill(
        self,
        *,
        order_ticket: int,
        expected_symbol: str,
        expected_direction: str,
        expected_volume: float,
    ) -> MT5CompletedFillResult:
        (
            valid_inputs,
            input_reason,
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

        if not valid_inputs:
            return self._invalid(
                reason=input_reason,
                order_ticket=order,
                expected_symbol=symbol,
                expected_direction=direction,
                expected_volume=volume,
                history_invoked=False,
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
                mt5_error=self._last_error(
                    api
                ),
            )

        try:
            raw_sequence = tuple(
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
            )

        normalized = self.normalize_records(
            raw_deals=raw_sequence,
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
            expected_volume=(
                normalized.expected_volume
            ),
            history_invoked=True,
            raw_deal_count=(
                normalized.raw_deal_count
            ),
            selected_deal_count=(
                normalized.selected_deal_count
            ),
            deal_tickets=(
                normalized.deal_tickets
            ),
            first_deal_time_msc=(
                normalized.first_deal_time_msc
            ),
            last_deal_time_msc=(
                normalized.last_deal_time_msc
            ),
            symbol=normalized.symbol,
            direction=normalized.direction,
            filled_volume=(
                normalized.filled_volume
            ),
            weighted_fill_price=(
                normalized.weighted_fill_price
            ),
            raw_commission_sum=(
                normalized.raw_commission_sum
            ),
            raw_fee_sum=(
                normalized.raw_fee_sum
            ),
            normalized_commission_cost=(
                normalized.normalized_commission_cost
            ),
            mt5_error=normalized.mt5_error,
            completed_fill=(
                normalized.completed_fill
            ),
        )


mt5_read_only_completed_fill_adapter = (
    MT5ReadOnlyCompletedFillAdapter()
)