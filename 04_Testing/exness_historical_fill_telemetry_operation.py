"""
===============================================================================
Module      : exness_historical_fill_telemetry_operation.py
Project     : PulseViper XAU AI
Version     : 1.0.1
Purpose     : Read-Only Exness / MT5 Complete Historical Entry-Fill Audit
===============================================================================

Status
------
RESEARCH / SHADOW / DEMO / READ ONLY.

Purpose
-------
Scan available MetaTrader 5 deal history for a requested XAU symbol, group
completed BUY/SELL entry deals by order ticket, reconstruct causal Bid/Ask
quotes from historical ticks, and normalize each completed entry order through
MT5ReadOnlyFillTelemetryAdapter.

The operation can inspect the complete broker/terminal-available history by
requesting a broad UTC interval, for example:

    2000-01-01T00:00:00Z -> now

"Complete history" means history actually available from the connected MT5
terminal/broker. Missing historical ticks are explicitly rejected and never
fabricated.

Safety boundary
---------------
This operation is READ ONLY with respect to the broker account.

It does NOT:
- send orders
- modify orders
- cancel orders
- open or close positions
- modify positions
- modify SL/TP
- size a live trade
- modify trade_ready
- modify production RiskEngine
- mutate lifecycle state
- mutate realized-cost accounting state
- authorize live execution

Only entry-side historical execution telemetry is normalized here. Exit/close
execution telemetry belongs to a separate future boundary.

Every row and report has:

    live_authorized = False

Broker-history rows also have:

    lifecycle_attested = False

Direct-script support
---------------------
The project root is explicitly inserted into sys.path so both invocation styles
work from the repository root:

    python -m 04_Testing.exness_historical_fill_telemetry_operation

and:

    python 04_Testing/exness_historical_fill_telemetry_operation.py
"""

from __future__ import annotations

import argparse
import csv
import importlib
import math
import statistics
import sys

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence


# =============================================================================
# Project import bootstrap
# =============================================================================

PROJECT_ROOT = (
    Path(
        __file__
    )
    .resolve()
    .parents[
        1
    ]
)

if str(
    PROJECT_ROOT
) not in sys.path:

    sys.path.insert(
        0,
        str(
            PROJECT_ROOT
        ),
    )


# =============================================================================
# Existing normalized MT5 fill adapter
# =============================================================================

_adapter_mod: Any = importlib.import_module(
    "02_AI.Shadow.mt5_read_only_fill_telemetry_adapter"
)

MT5ReadOnlyFillTelemetryAdapter: Any = (
    _adapter_mod.MT5ReadOnlyFillTelemetryAdapter
)


# =============================================================================
# Result models
# =============================================================================


@dataclass(
    frozen=True
)
class Distribution:
    count: int = 0
    minimum: float = 0.0
    median: float = 0.0
    mean: float = 0.0
    p90: float = 0.0
    p95: float = 0.0
    maximum: float = 0.0


@dataclass(
    frozen=True
)
class HistoricalFillRow:
    normalized: bool
    reason: str

    order_ticket: int
    execution_id: str

    symbol: str
    direction: str

    volume: float
    deal_count: int
    deal_tickets: tuple[
        int,
        ...,
    ]

    first_time_msc: int
    last_time_msc: int

    fill_price: float

    quote_bid: float
    quote_ask: float

    spread_price: float
    spread_points: float

    slippage_price: float
    slippage_points: float

    commission_cost: float

    max_quote_age_ms: int

    lifecycle_attested: bool = False
    live_authorized: bool = False

    telemetry: Any = None
    adapter_result: Any = None


@dataclass(
    frozen=True
)
class HistoricalFillReport:
    valid: bool
    reason: str

    mode: str
    version: str

    live_authorized: bool

    symbol: str

    date_from_utc: datetime
    date_to_utc: datetime

    point: float

    raw_deal_count: int
    candidate_entry_deal_count: int
    candidate_order_count: int

    normalized_order_count: int
    rejected_order_count: int

    long_order_count: int
    short_order_count: int

    adverse_slippage_count: int
    favorable_slippage_count: int
    zero_slippage_count: int

    total_volume: float
    total_commission_cost: float

    spread_points: Distribution

    signed_slippage_points: Distribution
    adverse_slippage_points: Distribution
    favorable_improvement_points: Distribution

    commission_cost: Distribution
    quote_age_ms: Distribution

    rejection_counts: tuple[
        tuple[
            str,
            int,
        ],
        ...,
    ]

    rows: tuple[
        HistoricalFillRow,
        ...,
    ]

    history_invoked: bool
    symbol_info_invoked: bool
    tick_history_invocations: int

    mt5_error: str = ""


# =============================================================================
# Operation
# =============================================================================


class ExnessHistoricalFillTelemetryOperation:
    VERSION = "1.0.1"

    MODE = (
        "READ_ONLY_EXNESS_COMPLETE_FILL_HISTORY_AUDIT"
    )

    EPS = 1e-10

    def __init__(
        self,
        *,
        mt5_api: Any | None = None,
        adapter: Any | None = None,
    ) -> None:

        self._mt5_api = (
            mt5_api
        )

        self.adapter = (
            adapter
            if adapter is not None
            else MT5ReadOnlyFillTelemetryAdapter(
                mt5_api=mt5_api
            )
        )

    # =========================================================================
    # Generic helpers
    # =========================================================================

    def _api(
        self,
    ) -> Any:

        if self._mt5_api is not None:

            return self._mt5_api

        return importlib.import_module(
            "MetaTrader5"
        )

    @staticmethod
    def _get(
        obj: Any,
        name: str,
        default: Any = None,
    ) -> Any:

        if obj is None:

            return default

        if isinstance(
            obj,
            dict,
        ):

            return obj.get(
                name,
                default,
            )

        if hasattr(
            obj,
            name,
        ):

            return getattr(
                obj,
                name,
            )

        dtype = getattr(
            obj,
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

                value = obj[
                    name
                ]

                if hasattr(
                    value,
                    "item",
                ):

                    return value.item()

                return value

            except Exception:

                return default

        try:

            return obj[
                name
            ]

        except Exception:

            return default

    @staticmethod
    def _num(
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
    def _int(
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
    def _utc(
        value: datetime,
    ) -> datetime | None:

        if (
            not isinstance(
                value,
                datetime,
            )
            or
            value.tzinfo is None
        ):

            return None

        return value.astimezone(
            timezone.utc
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

    # =========================================================================
    # Distribution helpers
    # =========================================================================

    @staticmethod
    def _pct(
        values: Sequence[
            float
        ],
        quantile: float,
    ) -> float:

        if not values:

            return 0.0

        ordered = sorted(
            values
        )

        if len(
            ordered
        ) == 1:

            return float(
                ordered[
                    0
                ]
            )

        position = (
            (
                len(
                    ordered
                )
                -
                1
            )
            *
            quantile
        )

        lower = math.floor(
            position
        )

        upper = math.ceil(
            position
        )

        if lower == upper:

            return float(
                ordered[
                    lower
                ]
            )

        weight = (
            position
            -
            lower
        )

        return float(
            (
                ordered[
                    lower
                ]
                *
                (
                    1.0
                    -
                    weight
                )
            )
            +
            (
                ordered[
                    upper
                ]
                *
                weight
            )
        )

    @classmethod
    def _dist(
        cls,
        values: Iterable[
            float
        ],
    ) -> Distribution:

        resolved: list[
            float
        ] = []

        for value in values:

            try:

                number = float(
                    value
                )

            except (
                TypeError,
                ValueError,
            ):

                continue

            if math.isfinite(
                number
            ):

                resolved.append(
                    number
                )

        if not resolved:

            return Distribution()

        return Distribution(
            count=len(
                resolved
            ),
            minimum=min(
                resolved
            ),
            median=float(
                statistics.median(
                    resolved
                )
            ),
            mean=float(
                statistics.fmean(
                    resolved
                )
            ),
            p90=cls._pct(
                resolved,
                0.90,
            ),
            p95=cls._pct(
                resolved,
                0.95,
            ),
            maximum=max(
                resolved
            ),
        )

    # =========================================================================
    # Range validation
    # =========================================================================

    def _validate_range(
        self,
        symbol: str,
        date_from: datetime,
        date_to: datetime,
    ) -> tuple[
        str,
        datetime | None,
        datetime | None,
    ]:

        resolved_symbol = str(
            symbol
        ).strip()

        start = self._utc(
            date_from
        )

        end = self._utc(
            date_to
        )

        if not resolved_symbol:

            return (
                "INVALID_HISTORY_SYMBOL",
                start,
                end,
            )

        if (
            start is None
            or
            end is None
            or
            start >= end
        ):

            return (
                "INVALID_UTC_HISTORY_RANGE",
                start,
                end,
            )

        return (
            "",
            start,
            end,
        )

    # =========================================================================
    # Entry-deal grouping
    # =========================================================================

    def _groups(
        self,
        *,
        api: Any,
        deals: Sequence[
            Any
        ],
        symbol: str,
        magic: int | None,
        comment_contains: str,
    ) -> tuple[
        dict[
            int,
            tuple[
                Any,
                ...,
            ],
        ],
        int,
    ]:

        buy_type = int(
            getattr(
                api,
                "DEAL_TYPE_BUY",
                0,
            )
        )

        sell_type = int(
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

        expected_symbol = (
            symbol
            .strip()
            .upper()
        )

        comment_filter = (
            comment_contains
            .strip()
            .lower()
        )

        groups: dict[
            int,
            list[
                Any
            ],
        ] = defaultdict(
            list
        )

        candidate_entry_count = 0

        for item in deals:

            deal_type = self._int(
                self._get(
                    item,
                    "type",
                    None,
                )
            )

            entry = self._int(
                self._get(
                    item,
                    "entry",
                    None,
                )
            )

            volume = self._num(
                self._get(
                    item,
                    "volume",
                    0.0,
                )
            )

            deal_symbol = str(
                self._get(
                    item,
                    "symbol",
                    "",
                )
            ).strip()

            if deal_type not in {
                buy_type,
                sell_type,
            }:

                continue

            if entry != entry_in:

                continue

            if (
                not math.isfinite(
                    volume
                )
                or
                volume <= 0.0
            ):

                continue

            if (
                deal_symbol.upper()
                !=
                expected_symbol
            ):

                continue

            if magic is not None:

                deal_magic = self._int(
                    self._get(
                        item,
                        "magic",
                        None,
                    )
                )

                if deal_magic != magic:

                    continue

            if comment_filter:

                comment = str(
                    self._get(
                        item,
                        "comment",
                        "",
                    )
                ).lower()

                if (
                    comment_filter
                    not in
                    comment
                ):

                    continue

            order_ticket = self._int(
                self._get(
                    item,
                    "order",
                    None,
                )
            )

            if (
                order_ticket is None
                or
                order_ticket <= 0
            ):

                continue

            candidate_entry_count += 1

            groups[
                order_ticket
            ].append(
                item
            )

        return (
            {
                order_ticket: tuple(
                    rows
                )
                for (
                    order_ticket,
                    rows,
                )
                in groups.items()
            },
            candidate_entry_count,
        )

    # =========================================================================
    # Adapter -> report-row conversion
    # =========================================================================

    def _row(
        self,
        result: Any,
        point: float,
    ) -> HistoricalFillRow:

        normalized = bool(
            getattr(
                result,
                "normalized",
                False,
            )
        )

        direction = str(
            getattr(
                result,
                "direction",
                "",
            )
        )

        fill_price = self._num(
            getattr(
                result,
                "weighted_fill_price",
                0.0,
            )
        )

        quote_bid = self._num(
            getattr(
                result,
                "weighted_quote_bid",
                0.0,
            )
        )

        quote_ask = self._num(
            getattr(
                result,
                "weighted_quote_ask",
                0.0,
            )
        )

        spread_price = self._num(
            getattr(
                result,
                "weighted_spread_price",
                0.0,
            )
        )

        fill_price = (
            fill_price
            if math.isfinite(
                fill_price
            )
            else 0.0
        )

        quote_bid = (
            quote_bid
            if math.isfinite(
                quote_bid
            )
            else 0.0
        )

        quote_ask = (
            quote_ask
            if math.isfinite(
                quote_ask
            )
            else 0.0
        )

        spread_price = (
            spread_price
            if math.isfinite(
                spread_price
            )
            else 0.0
        )

        slippage_price = 0.0

        if normalized:

            if direction == "LONG":

                slippage_price = (
                    fill_price
                    -
                    quote_ask
                )

            elif direction == "SHORT":

                slippage_price = (
                    quote_bid
                    -
                    fill_price
                )

        spread_points = (
            spread_price
            /
            point
            if normalized
            else 0.0
        )

        slippage_points = (
            slippage_price
            /
            point
            if normalized
            else 0.0
        )

        return HistoricalFillRow(
            normalized=normalized,
            reason=str(
                getattr(
                    result,
                    "reason",
                    "",
                )
            ),
            order_ticket=int(
                getattr(
                    result,
                    "order_ticket",
                    0,
                )
            ),
            execution_id=str(
                getattr(
                    result,
                    "execution_id",
                    "",
                )
            ),
            symbol=str(
                getattr(
                    result,
                    "symbol",
                    "",
                )
            ),
            direction=direction,
            volume=float(
                getattr(
                    result,
                    "filled_volume",
                    0.0,
                )
            ),
            deal_count=int(
                getattr(
                    result,
                    "selected_deal_count",
                    0,
                )
            ),
            deal_tickets=tuple(
                getattr(
                    result,
                    "deal_tickets",
                    (),
                )
            ),
            first_time_msc=int(
                getattr(
                    result,
                    "first_deal_time_msc",
                    0,
                )
            ),
            last_time_msc=int(
                getattr(
                    result,
                    "last_deal_time_msc",
                    0,
                )
            ),
            fill_price=fill_price,
            quote_bid=quote_bid,
            quote_ask=quote_ask,
            spread_price=spread_price,
            spread_points=spread_points,
            slippage_price=slippage_price,
            slippage_points=slippage_points,
            commission_cost=float(
                getattr(
                    result,
                    "normalized_commission_cost",
                    0.0,
                )
            ),
            max_quote_age_ms=int(
                getattr(
                    result,
                    "max_quote_age_ms",
                    0,
                )
            ),
            lifecycle_attested=False,
            live_authorized=False,
            telemetry=getattr(
                result,
                "telemetry",
                None,
            ),
            adapter_result=result,
        )

    # =========================================================================
    # Synthetic rejection row
    # =========================================================================

    def _tick_rejection_row(
        self,
        *,
        reason: str,
        order_ticket: int,
        order_deals: Sequence[
            Any
        ],
        symbol: str,
    ) -> HistoricalFillRow:

        deal_tickets: list[
            int
        ] = []

        deal_times: list[
            int
        ] = []

        volume = 0.0

        for item in order_deals:

            ticket = self._int(
                self._get(
                    item,
                    "ticket",
                    0,
                )
            )

            if ticket is not None:

                deal_tickets.append(
                    ticket
                )

            time_msc = self._int(
                self._get(
                    item,
                    "time_msc",
                    0,
                )
            )

            if time_msc is not None:

                deal_times.append(
                    time_msc
                )

            deal_volume = self._num(
                self._get(
                    item,
                    "volume",
                    0.0,
                )
            )

            if math.isfinite(
                deal_volume
            ):

                volume += (
                    deal_volume
                )

        return HistoricalFillRow(
            normalized=False,
            reason=reason,
            order_ticket=order_ticket,
            execution_id=(
                f"MT5_ORDER_{order_ticket}"
            ),
            symbol=symbol,
            direction="",
            volume=volume,
            deal_count=len(
                order_deals
            ),
            deal_tickets=tuple(
                deal_tickets
            ),
            first_time_msc=(
                min(
                    deal_times
                )
                if deal_times
                else 0
            ),
            last_time_msc=(
                max(
                    deal_times
                )
                if deal_times
                else 0
            ),
            fill_price=0.0,
            quote_bid=0.0,
            quote_ask=0.0,
            spread_price=0.0,
            spread_points=0.0,
            slippage_price=0.0,
            slippage_points=0.0,
            commission_cost=0.0,
            max_quote_age_ms=0,
            lifecycle_attested=False,
            live_authorized=False,
            telemetry=None,
            adapter_result=None,
        )

    # =========================================================================
    # Report aggregation
    # =========================================================================

    def _report(
        self,
        *,
        valid: bool,
        reason: str,
        symbol: str,
        start: datetime,
        end: datetime,
        point: float,
        rows: Sequence[
            HistoricalFillRow
        ] = (),
        raw_deal_count: int = 0,
        candidate_entry_deal_count: int = 0,
        candidate_order_count: int = 0,
        history_invoked: bool = False,
        symbol_info_invoked: bool = False,
        tick_history_invocations: int = 0,
        mt5_error: str = "",
    ) -> HistoricalFillReport:

        normalized_rows = [
            row
            for row
            in rows
            if row.normalized
        ]

        rejected_rows = [
            row
            for row
            in rows
            if not row.normalized
        ]

        adverse_slippage = [
            row.slippage_points
            for row
            in normalized_rows
            if (
                row.slippage_points
                >
                self.EPS
            )
        ]

        favorable_slippage = [
            row.slippage_points
            for row
            in normalized_rows
            if (
                row.slippage_points
                <
                -self.EPS
            )
        ]

        zero_slippage_count = sum(
            (
                abs(
                    row.slippage_points
                )
                <=
                self.EPS
            )
            for row
            in normalized_rows
        )

        rejection_counts = tuple(
            sorted(
                Counter(
                    row.reason
                    for row
                    in rejected_rows
                ).items()
            )
        )

        return HistoricalFillReport(
            valid=valid,
            reason=reason,
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            symbol=symbol,
            date_from_utc=start,
            date_to_utc=end,
            point=point,
            raw_deal_count=raw_deal_count,
            candidate_entry_deal_count=(
                candidate_entry_deal_count
            ),
            candidate_order_count=(
                candidate_order_count
            ),
            normalized_order_count=len(
                normalized_rows
            ),
            rejected_order_count=len(
                rejected_rows
            ),
            long_order_count=sum(
                (
                    row.direction
                    ==
                    "LONG"
                )
                for row
                in normalized_rows
            ),
            short_order_count=sum(
                (
                    row.direction
                    ==
                    "SHORT"
                )
                for row
                in normalized_rows
            ),
            adverse_slippage_count=len(
                adverse_slippage
            ),
            favorable_slippage_count=len(
                favorable_slippage
            ),
            zero_slippage_count=(
                zero_slippage_count
            ),
            total_volume=sum(
                row.volume
                for row
                in normalized_rows
            ),
            total_commission_cost=sum(
                row.commission_cost
                for row
                in normalized_rows
            ),
            spread_points=self._dist(
                row.spread_points
                for row
                in normalized_rows
            ),
            signed_slippage_points=self._dist(
                row.slippage_points
                for row
                in normalized_rows
            ),
            adverse_slippage_points=self._dist(
                adverse_slippage
            ),
            favorable_improvement_points=self._dist(
                abs(
                    value
                )
                for value
                in favorable_slippage
            ),
            commission_cost=self._dist(
                row.commission_cost
                for row
                in normalized_rows
            ),
            quote_age_ms=self._dist(
                float(
                    row.max_quote_age_ms
                )
                for row
                in normalized_rows
            ),
            rejection_counts=(
                rejection_counts
            ),
            rows=tuple(
                rows
            ),
            history_invoked=(
                history_invoked
            ),
            symbol_info_invoked=(
                symbol_info_invoked
            ),
            tick_history_invocations=(
                tick_history_invocations
            ),
            mt5_error=mt5_error,
        )

    # =========================================================================
    # Report-reason helper
    # =========================================================================

    @staticmethod
    def _audit_reason(
        *,
        candidate_order_count: int,
        rows: Sequence[
            HistoricalFillRow
        ],
    ) -> str:

        if candidate_order_count == 0:

            return (
                "OK_NO_MATCHING_ENTRY_ORDERS"
            )

        normalized_count = sum(
            row.normalized
            for row
            in rows
        )

        if (
            normalized_count
            ==
            candidate_order_count
        ):

            return (
                "OK_COMPLETE_HISTORY_AUDIT"
            )

        if normalized_count > 0:

            return (
                "OK_HISTORY_AUDIT_WITH_REJECTIONS"
            )

        return (
            "HISTORY_AUDIT_NO_ORDERS_NORMALIZED"
        )

    # =========================================================================
    # Pure offline record audit
    # =========================================================================

    def audit_records(
        self,
        *,
        raw_deals: Sequence[
            Any
        ],
        ticks_by_order: dict[
            int,
            Sequence[
                Any
            ],
        ],
        symbol: str,
        point: float,
        date_from: datetime,
        date_to: datetime,
        magic: int | None = None,
        comment_contains: str = "",
        mt5_api: Any | None = None,
    ) -> HistoricalFillReport:

        (
            range_error,
            start,
            end,
        ) = self._validate_range(
            symbol,
            date_from,
            date_to,
        )

        fallback = datetime(
            1970,
            1,
            1,
            tzinfo=timezone.utc,
        )

        resolved_point = self._num(
            point
        )

        if range_error:

            return self._report(
                valid=False,
                reason=range_error,
                symbol=str(
                    symbol
                ).strip(),
                start=(
                    start
                    if start is not None
                    else fallback
                ),
                end=(
                    end
                    if end is not None
                    else fallback
                ),
                point=(
                    resolved_point
                    if math.isfinite(
                        resolved_point
                    )
                    else 0.0
                ),
            )

        if (
            not math.isfinite(
                resolved_point
            )
            or
            resolved_point <= 0.0
        ):

            return self._report(
                valid=False,
                reason="INVALID_SYMBOL_POINT",
                symbol=str(
                    symbol
                ).strip(),
                start=start,
                end=end,
                point=0.0,
                raw_deal_count=len(
                    raw_deals
                ),
            )

        api = (
            mt5_api
            if mt5_api is not None
            else (
                self._mt5_api
                if self._mt5_api is not None
                else object()
            )
        )

        (
            groups,
            candidate_entry_count,
        ) = self._groups(
            api=api,
            deals=raw_deals,
            symbol=str(
                symbol
            ).strip(),
            magic=magic,
            comment_contains=(
                comment_contains
            ),
        )

        buy_type = int(
            getattr(
                api,
                "DEAL_TYPE_BUY",
                0,
            )
        )

        rows: list[
            HistoricalFillRow
        ] = []

        for order_ticket in sorted(
            groups
        ):

            order_deals = groups[
                order_ticket
            ]

            expected_volume = sum(
                self._num(
                    self._get(
                        item,
                        "volume",
                        0.0,
                    )
                )
                for item
                in order_deals
            )

            first_type = int(
                self._get(
                    order_deals[
                        0
                    ],
                    "type",
                    0,
                )
            )

            expected_direction = (
                "LONG"
                if first_type
                ==
                buy_type
                else "SHORT"
            )

            adapter_result = (
                self.adapter
                .normalize_records(
                    raw_deals=order_deals,
                    raw_ticks=tuple(
                        ticks_by_order.get(
                            order_ticket,
                            (),
                        )
                    ),
                    order_ticket=order_ticket,
                    expected_symbol=str(
                        symbol
                    ).strip(),
                    expected_direction=(
                        expected_direction
                    ),
                    expected_volume=(
                        expected_volume
                    ),
                    mt5_api=api,
                )
            )

            rows.append(
                self._row(
                    adapter_result,
                    resolved_point,
                )
            )

        report_reason = (
            self._audit_reason(
                candidate_order_count=len(
                    groups
                ),
                rows=rows,
            )
        )

        return self._report(
            valid=True,
            reason=report_reason,
            symbol=str(
                symbol
            ).strip(),
            start=start,
            end=end,
            point=resolved_point,
            rows=rows,
            raw_deal_count=len(
                raw_deals
            ),
            candidate_entry_deal_count=(
                candidate_entry_count
            ),
            candidate_order_count=len(
                groups
            ),
            history_invoked=False,
            symbol_info_invoked=False,
            tick_history_invocations=0,
        )

    # =========================================================================
    # Connected MT5 read-only audit
    # =========================================================================

    def read_history(
        self,
        *,
        symbol: str,
        date_from: datetime,
        date_to: datetime,
        magic: int | None = None,
        comment_contains: str = "",
    ) -> HistoricalFillReport:

        (
            range_error,
            start,
            end,
        ) = self._validate_range(
            symbol,
            date_from,
            date_to,
        )

        fallback = datetime(
            1970,
            1,
            1,
            tzinfo=timezone.utc,
        )

        resolved_symbol = str(
            symbol
        ).strip()

        if range_error:

            return self._report(
                valid=False,
                reason=range_error,
                symbol=resolved_symbol,
                start=(
                    start
                    if start is not None
                    else fallback
                ),
                end=(
                    end
                    if end is not None
                    else fallback
                ),
                point=0.0,
            )

        try:

            api = self._api()

        except Exception as exc:

            return self._report(
                valid=False,
                reason="MT5_API_IMPORT_FAILED",
                symbol=resolved_symbol,
                start=start,
                end=end,
                point=0.0,
                mt5_error=str(
                    exc
                ),
            )

        # ---------------------------------------------------------------------
        # Symbol metadata
        # ---------------------------------------------------------------------

        try:

            symbol_info = api.symbol_info(
                resolved_symbol
            )

        except Exception as exc:

            return self._report(
                valid=False,
                reason=(
                    "MT5_SYMBOL_INFO_READ_EXCEPTION"
                ),
                symbol=resolved_symbol,
                start=start,
                end=end,
                point=0.0,
                symbol_info_invoked=True,
                mt5_error=str(
                    exc
                ),
            )

        if symbol_info is None:

            return self._report(
                valid=False,
                reason=(
                    "MT5_SYMBOL_INFO_READ_FAILED"
                ),
                symbol=resolved_symbol,
                start=start,
                end=end,
                point=0.0,
                symbol_info_invoked=True,
                mt5_error=self._last_error(
                    api
                ),
            )

        point = self._num(
            self._get(
                symbol_info,
                "point",
                None,
            )
        )

        if (
            not math.isfinite(
                point
            )
            or
            point <= 0.0
        ):

            return self._report(
                valid=False,
                reason="INVALID_SYMBOL_POINT",
                symbol=resolved_symbol,
                start=start,
                end=end,
                point=0.0,
                symbol_info_invoked=True,
            )

        # ---------------------------------------------------------------------
        # Complete requested deal interval
        # ---------------------------------------------------------------------

        try:

            history = api.history_deals_get(
                start,
                end,
                group=(
                    f"*{resolved_symbol}*"
                ),
            )

        except Exception as exc:

            return self._report(
                valid=False,
                reason=(
                    "MT5_HISTORY_READ_EXCEPTION"
                ),
                symbol=resolved_symbol,
                start=start,
                end=end,
                point=point,
                history_invoked=True,
                symbol_info_invoked=True,
                mt5_error=str(
                    exc
                ),
            )

        if history is None:

            return self._report(
                valid=False,
                reason=(
                    "MT5_HISTORY_READ_FAILED"
                ),
                symbol=resolved_symbol,
                start=start,
                end=end,
                point=point,
                history_invoked=True,
                symbol_info_invoked=True,
                mt5_error=self._last_error(
                    api
                ),
            )

        try:

            deals = tuple(
                history
            )

        except Exception:

            return self._report(
                valid=False,
                reason=(
                    "INVALID_MT5_HISTORY_RESULT"
                ),
                symbol=resolved_symbol,
                start=start,
                end=end,
                point=point,
                history_invoked=True,
                symbol_info_invoked=True,
            )

        (
            groups,
            candidate_entry_count,
        ) = self._groups(
            api=api,
            deals=deals,
            symbol=resolved_symbol,
            magic=magic,
            comment_contains=(
                comment_contains
            ),
        )

        # No entry orders means no tick reads are necessary.
        if not groups:

            return self._report(
                valid=True,
                reason=(
                    "OK_NO_MATCHING_ENTRY_ORDERS"
                ),
                symbol=resolved_symbol,
                start=start,
                end=end,
                point=point,
                rows=(),
                raw_deal_count=len(
                    deals
                ),
                candidate_entry_deal_count=(
                    candidate_entry_count
                ),
                candidate_order_count=0,
                history_invoked=True,
                symbol_info_invoked=True,
                tick_history_invocations=0,
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

            return self._report(
                valid=False,
                reason=(
                    "MT5_TICK_FLAG_UNAVAILABLE"
                ),
                symbol=resolved_symbol,
                start=start,
                end=end,
                point=point,
                raw_deal_count=len(
                    deals
                ),
                candidate_entry_deal_count=(
                    candidate_entry_count
                ),
                candidate_order_count=len(
                    groups
                ),
                history_invoked=True,
                symbol_info_invoked=True,
                tick_history_invocations=0,
            )

        buy_type = int(
            getattr(
                api,
                "DEAL_TYPE_BUY",
                0,
            )
        )

        quote_lookback_ms = int(
            self.adapter
            .policy
            .quote_lookback_ms
        )

        rows: list[
            HistoricalFillRow
        ] = []

        tick_history_invocations = 0

        # ---------------------------------------------------------------------
        # Per-order historical quote reconstruction
        # ---------------------------------------------------------------------

        for order_ticket in sorted(
            groups
        ):

            order_deals = groups[
                order_ticket
            ]

            deal_times = [
                int(
                    self._get(
                        item,
                        "time_msc",
                        0,
                    )
                )
                for item
                in order_deals
            ]

            first_time_msc = min(
                deal_times
            )

            last_time_msc = max(
                deal_times
            )

            tick_from = datetime.fromtimestamp(
                (
                    first_time_msc
                    -
                    quote_lookback_ms
                )
                /
                1000.0,
                tz=timezone.utc,
            )

            # +1 ms allows a tick exactly at last fill time to be returned
            # without ever permitting the adapter to use a post-fill quote.
            tick_to = (
                datetime.fromtimestamp(
                    last_time_msc
                    /
                    1000.0,
                    tz=timezone.utc,
                )
                +
                timedelta(
                    milliseconds=1
                )
            )

            tick_history_invocations += 1

            try:

                raw_ticks = api.copy_ticks_range(
                    resolved_symbol,
                    tick_from,
                    tick_to,
                    tick_flag,
                )

            except Exception:

                rows.append(
                    self._tick_rejection_row(
                        reason=(
                            "MT5_TICK_HISTORY_READ_EXCEPTION"
                        ),
                        order_ticket=order_ticket,
                        order_deals=order_deals,
                        symbol=resolved_symbol,
                    )
                )

                continue

            if raw_ticks is None:

                rows.append(
                    self._tick_rejection_row(
                        reason=(
                            "MT5_TICK_HISTORY_READ_FAILED"
                        ),
                        order_ticket=order_ticket,
                        order_deals=order_deals,
                        symbol=resolved_symbol,
                    )
                )

                continue

            try:

                ticks = tuple(
                    raw_ticks
                )

            except Exception:

                rows.append(
                    self._tick_rejection_row(
                        reason=(
                            "INVALID_MT5_TICK_HISTORY_RESULT"
                        ),
                        order_ticket=order_ticket,
                        order_deals=order_deals,
                        symbol=resolved_symbol,
                    )
                )

                continue

            expected_volume = sum(
                self._num(
                    self._get(
                        item,
                        "volume",
                        0.0,
                    )
                )
                for item
                in order_deals
            )

            first_type = int(
                self._get(
                    order_deals[
                        0
                    ],
                    "type",
                    0,
                )
            )

            expected_direction = (
                "LONG"
                if first_type
                ==
                buy_type
                else "SHORT"
            )

            adapter_result = (
                self.adapter
                .normalize_records(
                    raw_deals=order_deals,
                    raw_ticks=ticks,
                    order_ticket=order_ticket,
                    expected_symbol=(
                        resolved_symbol
                    ),
                    expected_direction=(
                        expected_direction
                    ),
                    expected_volume=(
                        expected_volume
                    ),
                    mt5_api=api,
                )
            )

            rows.append(
                self._row(
                    adapter_result,
                    point,
                )
            )

        report_reason = (
            self._audit_reason(
                candidate_order_count=len(
                    groups
                ),
                rows=rows,
            )
        )

        return self._report(
            valid=True,
            reason=report_reason,
            symbol=resolved_symbol,
            start=start,
            end=end,
            point=point,
            rows=rows,
            raw_deal_count=len(
                deals
            ),
            candidate_entry_deal_count=(
                candidate_entry_count
            ),
            candidate_order_count=len(
                groups
            ),
            history_invoked=True,
            symbol_info_invoked=True,
            tick_history_invocations=(
                tick_history_invocations
            ),
        )

    # =========================================================================
    # Runtime CSV export
    # =========================================================================

    @staticmethod
    def write_csv(
        report: HistoricalFillReport,
        path: str | Path,
    ) -> Path:

        output = Path(
            path
        )

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        fields = (
            "normalized",
            "reason",
            "order_ticket",
            "execution_id",
            "symbol",
            "direction",
            "volume",
            "deal_count",
            "first_time_msc",
            "last_time_msc",
            "fill_price",
            "quote_bid",
            "quote_ask",
            "spread_price",
            "spread_points",
            "slippage_price",
            "slippage_points",
            "commission_cost",
            "max_quote_age_ms",
            "lifecycle_attested",
        )

        with output.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as handle:

            writer = csv.DictWriter(
                handle,
                fieldnames=fields,
            )

            writer.writeheader()

            for row in report.rows:

                writer.writerow(
                    {
                        field: getattr(
                            row,
                            field,
                        )
                        for field
                        in fields
                    }
                )

        return output

    # =========================================================================
    # Console reporting
    # =========================================================================

    @staticmethod
    def _fmt(
        name: str,
        distribution: Distribution,
    ) -> str:

        return (
            f"{name:<28} "
            f"n={distribution.count:<4} "
            f"min={distribution.minimum:.2f} "
            f"med={distribution.median:.2f} "
            f"mean={distribution.mean:.2f} "
            f"p90={distribution.p90:.2f} "
            f"p95={distribution.p95:.2f} "
            f"max={distribution.maximum:.2f}"
        )

    @classmethod
    def print_report(
        cls,
        report: HistoricalFillReport,
        *,
        show_rows: int = 20,
    ) -> None:

        print(
            "="
            *
            112
        )

        print(
            "EXNESS / MT5 COMPLETE HISTORICAL "
            "ENTRY-FILL AUDIT — READ ONLY"
        )

        print(
            "="
            *
            112
        )

        print(
            f"valid / reason                : "
            f"{report.valid} / {report.reason}"
        )

        print(
            f"symbol / point                : "
            f"{report.symbol} / {report.point}"
        )

        print(
            f"UTC range                     : "
            f"{report.date_from_utc.isoformat()} -> "
            f"{report.date_to_utc.isoformat()}"
        )

        print(
            f"raw deals / entry deals       : "
            f"{report.raw_deal_count} / "
            f"{report.candidate_entry_deal_count}"
        )

        print(
            f"candidate orders              : "
            f"{report.candidate_order_count}"
        )

        print(
            f"orders normalized / rejected  : "
            f"{report.normalized_order_count} / "
            f"{report.rejected_order_count}"
        )

        print(
            f"LONG / SHORT                  : "
            f"{report.long_order_count} / "
            f"{report.short_order_count}"
        )

        print(
            f"adverse / favorable / zero    : "
            f"{report.adverse_slippage_count} / "
            f"{report.favorable_slippage_count} / "
            f"{report.zero_slippage_count}"
        )

        print(
            f"total volume                  : "
            f"{report.total_volume:.4f}"
        )

        print(
            f"total commission cost         : "
            f"{report.total_commission_cost:.4f}"
        )

        print(
            f"tick-history calls            : "
            f"{report.tick_history_invocations}"
        )

        print()

        print(
            "DISTRIBUTIONS"
        )

        print(
            cls._fmt(
                "spread points",
                report.spread_points,
            )
        )

        print(
            cls._fmt(
                "signed slippage points",
                report.signed_slippage_points,
            )
        )

        print(
            cls._fmt(
                "adverse slippage points",
                report.adverse_slippage_points,
            )
        )

        print(
            cls._fmt(
                "favorable improvement pts",
                report.favorable_improvement_points,
            )
        )

        print(
            cls._fmt(
                "commission cost",
                report.commission_cost,
            )
        )

        print(
            cls._fmt(
                "quote age ms",
                report.quote_age_ms,
            )
        )

        if report.rejection_counts:

            print()

            print(
                "REJECTIONS"
            )

            for (
                rejection_reason,
                count,
            ) in report.rejection_counts:

                print(
                    f"{rejection_reason:<52} "
                    f"{count}"
                )

        normalized_rows = sorted(
            (
                row
                for row
                in report.rows
                if row.normalized
            ),
            key=lambda row: (
                row.last_time_msc
            ),
            reverse=True,
        )

        if (
            show_rows > 0
            and
            normalized_rows
        ):

            print()

            print(
                "MOST RECENT NORMALIZED ORDERS"
            )

            print(
                f"{'ORDER':>12} "
                f"{'DIR':>5} "
                f"{'VOL':>7} "
                f"{'DEALS':>5} "
                f"{'SPR pts':>9} "
                f"{'SLIP pts':>9} "
                f"{'COMM':>8} "
                f"{'QAGE':>7}"
            )

            for row in normalized_rows[
                :
                show_rows
            ]:

                print(
                    f"{row.order_ticket:>12} "
                    f"{row.direction:>5} "
                    f"{row.volume:>7.3f} "
                    f"{row.deal_count:>5} "
                    f"{row.spread_points:>9.1f} "
                    f"{row.slippage_points:>9.1f} "
                    f"{row.commission_cost:>8.4f} "
                    f"{row.max_quote_age_ms:>7}"
                )

        if report.mt5_error:

            print()

            print(
                f"MT5 error                     : "
                f"{report.mt5_error}"
            )

        print()

        print(
            "Broker-history rows are "
            "lifecycle_attested=False."
        )

        print(
            "No broker write, order placement, "
            "position modification, or lifecycle mutation is performed."
        )


# =============================================================================
# CLI
# =============================================================================


def _parse_utc(
    value: str,
) -> datetime:

    text = str(
        value
    ).strip()

    if text.lower() == "now":

        return datetime.now(
            timezone.utc
        )

    if text.endswith(
        "Z"
    ):

        text = (
            text[
                :-1
            ]
            +
            "+00:00"
        )

    parsed = datetime.fromisoformat(
        text
    )

    if parsed.tzinfo is None:

        parsed = parsed.replace(
            tzinfo=timezone.utc
        )

    return parsed.astimezone(
        timezone.utc
    )


def build_parser(
) -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "READ-ONLY Exness/MT5 complete "
            "historical XAU entry-fill audit"
        )
    )

    parser.add_argument(
        "--symbol",
        default="XAUUSDm",
    )

    parser.add_argument(
        "--from-date",
        default=(
            "2000-01-01T00:00:00Z"
        ),
    )

    parser.add_argument(
        "--to-date",
        default="now",
    )

    parser.add_argument(
        "--magic",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--comment-contains",
        default="",
    )

    parser.add_argument(
        "--show-rows",
        type=int,
        default=20,
    )

    parser.add_argument(
        "--csv",
        default="",
        help=(
            "Optional generated runtime CSV. "
            "Do not stage or commit it."
        ),
    )

    return parser


def main(
    argv: Sequence[
        str
    ]
    | None = None,
) -> int:

    args = (
        build_parser()
        .parse_args(
            argv
        )
    )

    try:

        start = _parse_utc(
            args.from_date
        )

        end = _parse_utc(
            args.to_date
        )

    except Exception as exc:

        print(
            f"Invalid UTC date: {exc}"
        )

        return 2

    # Import only when actually running a connected operation.
    # --help therefore remains safe even without MetaTrader5 installed.
    try:

        mt5 = importlib.import_module(
            "MetaTrader5"
        )

    except Exception as exc:

        print(
            "MetaTrader5 import failed: "
            f"{exc}"
        )

        return 3

    try:

        initialized = bool(
            mt5.initialize()
        )

    except Exception as exc:

        print(
            "MT5 initialize exception: "
            f"{exc}"
        )

        return 4

    if not initialized:

        print(
            "MT5 initialize failed: "
            f"{ExnessHistoricalFillTelemetryOperation._last_error(mt5)}"
        )

        return 4

    try:

        operation = (
            ExnessHistoricalFillTelemetryOperation(
                mt5_api=mt5
            )
        )

        report = operation.read_history(
            symbol=args.symbol,
            date_from=start,
            date_to=end,
            magic=args.magic,
            comment_contains=(
                args.comment_contains
            ),
        )

        operation.print_report(
            report,
            show_rows=max(
                0,
                args.show_rows,
            ),
        )

        if args.csv:

            output = operation.write_csv(
                report,
                args.csv,
            )

            print()

            print(
                f"Runtime CSV written: {output}"
            )

            print(
                "Do NOT stage or commit "
                "this generated CSV."
            )

        return (
            0
            if report.valid
            else 5
        )

    finally:

        try:

            mt5.shutdown()

        except Exception:

            pass


if __name__ == "__main__":

    raise SystemExit(
        main()
    )