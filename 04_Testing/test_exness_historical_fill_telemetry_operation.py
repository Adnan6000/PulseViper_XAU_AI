"""Offline tests for complete historical Exness/MT5 fill telemetry audit."""
from __future__ import annotations

import importlib
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "04_Testing.exness_historical_fill_telemetry_operation"
)

Operation: Any = (
    module.ExnessHistoricalFillTelemetryOperation
)


@dataclass(frozen=True)
class Deal:
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
    magic: int = 0
    comment: str = ""


@dataclass(frozen=True)
class Tick:
    time_msc: int
    bid: float
    ask: float


@dataclass(frozen=True)
class SymbolInfo:
    point: float


class FakeMT5:
    DEAL_TYPE_BUY = 0
    DEAL_TYPE_SELL = 1

    DEAL_ENTRY_IN = 0
    DEAL_ENTRY_OUT = 1

    COPY_TICKS_INFO = 2
    COPY_TICKS_ALL = 3

    def __init__(
        self,
        *,
        deals: Any = (),
        ticks: dict[int, Any] | None = None,
        info: Any = "DEFAULT",
        history_exception: Exception | None = None,
        tick_exception_orders: set[int] | None = None,
        none_tick_orders: set[int] | None = None,
        last_error: Any = (
            0,
            "OK",
        ),
    ) -> None:
        self.deals = deals

        self.ticks = (
            ticks
            or {}
        )

        self.info = (
            SymbolInfo(
                0.001
            )
            if info
            ==
            "DEFAULT"
            else info
        )

        self.history_exception = (
            history_exception
        )

        self.tick_exception_orders = (
            tick_exception_orders
            or set()
        )

        self.none_tick_orders = (
            none_tick_orders
            or set()
        )

        self.last_error_value = (
            last_error
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

        return self.info

    def history_deals_get(
        self,
        start: datetime,
        end: datetime,
        *,
        group: str,
    ) -> Any:
        self.calls.append(
            (
                "history_deals_get",
                (
                    start,
                    end,
                    group,
                ),
            )
        )

        if self.history_exception:
            raise self.history_exception

        return self.deals

    def copy_ticks_range(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        flags: int,
    ) -> Any:
        end_msc = int(
            end.timestamp()
            *
            1000
        )

        candidates = [
            item
            for item
            in (
                self.deals
                or ()
            )
            if (
                item.symbol
                ==
                symbol
                and
                item.entry
                ==
                0
                and
                item.volume
                >
                0
                and
                item.time_msc
                <=
                end_msc
            )
        ]

        order_ticket = (
            max(
                candidates,
                key=lambda item: (
                    item.time_msc
                ),
            ).order
            if candidates
            else 0
        )

        self.calls.append(
            (
                "copy_ticks_range",
                (
                    symbol,
                    start,
                    end,
                    flags,
                    order_ticket,
                ),
            )
        )

        if (
            order_ticket
            in
            self.tick_exception_orders
        ):
            raise RuntimeError(
                "tick failure"
            )

        if (
            order_ticket
            in
            self.none_tick_orders
        ):
            return None

        return self.ticks.get(
            order_ticket,
            (),
        )

    def last_error(
        self,
    ) -> Any:
        self.calls.append(
            (
                "last_error",
                None,
            )
        )

        return self.last_error_value


START = datetime(
    2025,
    1,
    1,
    tzinfo=timezone.utc,
)

END = datetime(
    2027,
    1,
    1,
    tzinfo=timezone.utc,
)

SYMBOL = "XAUUSDm"


def deal(
    *,
    ticket: int = 1001,
    order: int = 9001,
    time_msc: int = 1_800_000_000_000,
    type: int = 0,
    entry: int = 0,
    volume: float = 0.01,
    price: float = 4316.720,
    commission: float = 0.0,
    fee: float = 0.0,
    symbol: str = SYMBOL,
    magic: int = 0,
    comment: str = "",
) -> Deal:
    return Deal(
        ticket,
        order,
        time_msc,
        type,
        entry,
        volume,
        price,
        commission,
        fee,
        symbol,
        magic,
        comment,
    )


def tick(
    *,
    time_msc: int = 1_799_999_999_990,
    bid: float = 4316.500,
    ask: float = 4316.700,
) -> Tick:
    return Tick(
        time_msc,
        bid,
        ask,
    )


def audit(
    *,
    deals: Any = None,
    ticks: dict[int, Any] | None = None,
    magic: int | None = None,
    comment: str = "",
    point: float = 0.001,
) -> Any:
    resolved_deals = (
        (
            deal(),
        )
        if deals is None
        else deals
    )

    resolved_ticks = (
        {
            9001: (
                tick(),
            )
        }
        if ticks is None
        else ticks
    )

    api = FakeMT5(
        deals=resolved_deals
    )

    return Operation(
        mt5_api=api
    ).audit_records(
        raw_deals=resolved_deals,
        ticks_by_order=resolved_ticks,
        symbol=SYMBOL,
        point=point,
        date_from=START,
        date_to=END,
        magic=magic,
        comment_contains=comment,
        mt5_api=api,
    )


def test_mode_and_live_boundary() -> None:
    report = audit()

    assert report.valid is True

    assert report.mode == (
        "READ_ONLY_EXNESS_COMPLETE_FILL_HISTORY_AUDIT"
    )

    assert report.live_authorized is False

    assert (
        report.rows[
            0
        ].lifecycle_attested
        is False
    )

    assert (
        report.rows[
            0
        ].live_authorized
        is False
    )


def test_long_spread_and_adverse_slippage_points() -> None:
    row = audit().rows[
        0
    ]

    assert row.spread_points == pytest.approx(
        200.0
    )

    assert row.slippage_points == pytest.approx(
        20.0
    )


def test_long_favorable_slippage_stays_negative() -> None:
    report = audit(
        deals=(
            deal(
                price=4316.680
            ),
        )
    )

    assert (
        report.rows[
            0
        ].slippage_points
        ==
        pytest.approx(
            -20.0
        )
    )

    assert (
        report.favorable_slippage_count
        ==
        1
    )

    assert (
        report
        .favorable_improvement_points
        .mean
        ==
        pytest.approx(
            20.0
        )
    )


def test_short_adverse_slippage_is_positive() -> None:
    row = audit(
        deals=(
            deal(
                type=1,
                price=4316.480,
            ),
        )
    ).rows[
        0
    ]

    assert row.direction == "SHORT"

    assert row.slippage_points == pytest.approx(
        20.0
    )


def test_zero_slippage_bucket() -> None:
    report = audit(
        deals=(
            deal(
                price=4316.700
            ),
        )
    )

    assert report.zero_slippage_count == 1


def test_commission_and_fee_aggregate_as_cost() -> None:
    report = audit(
        deals=(
            deal(
                commission=-0.03,
                fee=-0.02,
            ),
        )
    )

    assert report.total_commission_cost == pytest.approx(
        0.05
    )


def test_two_orders_normalize_independently() -> None:
    deals = (
        deal(
            order=9001,
            ticket=1001,
        ),
        deal(
            order=9002,
            ticket=1002,
            time_msc=1_800_000_100_000,
            type=1,
            price=4317.480,
        ),
    )

    ticks = {
        9001: (
            tick(),
        ),
        9002: (
            tick(
                time_msc=1_800_000_099_990,
                bid=4317.500,
                ask=4317.700,
            ),
        ),
    }

    report = audit(
        deals=deals,
        ticks=ticks,
    )

    assert report.candidate_order_count == 2

    assert report.normalized_order_count == 2

    assert report.long_order_count == 1

    assert report.short_order_count == 1


def test_partial_deals_same_order_aggregate() -> None:
    deals = (
        deal(
            ticket=1001,
            volume=0.004,
            price=4316.710,
        ),
        deal(
            ticket=1002,
            time_msc=1_800_000_000_200,
            volume=0.006,
            price=4316.730,
        ),
    )

    ticks = {
        9001: (
            tick(),
            tick(
                time_msc=1_800_000_000_190,
                bid=4316.510,
                ask=4316.710,
            ),
        )
    }

    row = audit(
        deals=deals,
        ticks=ticks,
    ).rows[
        0
    ]

    assert row.deal_count == 2

    assert row.volume == pytest.approx(
        0.01
    )


def test_non_matching_symbol_and_exit_deals_are_ignored() -> None:
    report = audit(
        deals=(
            deal(
                symbol="EURUSD"
            ),
            deal(
                order=9002,
                ticket=1002,
                entry=1,
            ),
        ),
        ticks={},
    )

    assert report.reason == (
        "OK_NO_MATCHING_ENTRY_ORDERS"
    )

    assert report.candidate_order_count == 0


def test_magic_filter() -> None:
    deals = (
        deal(
            order=9001,
            ticket=1001,
            magic=777,
        ),
        deal(
            order=9002,
            ticket=1002,
            time_msc=1_800_000_100_000,
            magic=888,
        ),
    )

    report = audit(
        deals=deals,
        ticks={
            9001: (
                tick(),
            )
        },
        magic=777,
    )

    assert report.candidate_order_count == 1

    assert (
        report.rows[
            0
        ].order_ticket
        ==
        9001
    )


def test_comment_filter_case_insensitive() -> None:
    deals = (
        deal(
            comment="PulseViper Entry"
        ),
        deal(
            order=9002,
            ticket=1002,
            time_msc=1_800_000_100_000,
            comment="manual",
        ),
    )

    report = audit(
        deals=deals,
        ticks={
            9001: (
                tick(),
            )
        },
        comment="pulseviper",
    )

    assert report.candidate_order_count == 1


def test_missing_ticks_are_reported_without_fabrication() -> None:
    deals = (
        deal(
            order=9001,
            ticket=1001,
        ),
        deal(
            order=9002,
            ticket=1002,
            time_msc=1_800_000_100_000,
        ),
    )

    report = audit(
        deals=deals,
        ticks={
            9001: (
                tick(),
            ),
            9002: (),
        },
    )

    assert report.valid is True

    assert report.reason == (
        "OK_HISTORY_AUDIT_WITH_REJECTIONS"
    )

    assert report.normalized_order_count == 1

    assert report.rejected_order_count == 1

    assert (
        dict(
            report.rejection_counts
        )[
            "NO_VALID_QUOTE_TICKS"
        ]
        ==
        1
    )


def test_all_rejected_report_is_explicit() -> None:
    report = audit(
        ticks={
            9001: ()
        }
    )

    assert report.valid is True

    assert report.reason == (
        "HISTORY_AUDIT_NO_ORDERS_NORMALIZED"
    )


def test_rejected_rows_do_not_enter_distributions() -> None:
    deals = (
        deal(
            order=9001,
            ticket=1001,
        ),
        deal(
            order=9002,
            ticket=1002,
            time_msc=1_800_000_100_000,
        ),
    )

    report = audit(
        deals=deals,
        ticks={
            9001: (
                tick(),
            ),
            9002: (),
        },
    )

    assert report.spread_points.count == 1

    assert (
        report
        .signed_slippage_points
        .count
        ==
        1
    )


def test_distribution_math() -> None:
    distribution = Operation(
        mt5_api=FakeMT5()
    )._dist(
        [
            1,
            2,
            3,
            4,
            5,
        ]
    )

    assert distribution.median == pytest.approx(
        3.0
    )

    assert distribution.mean == pytest.approx(
        3.0
    )

    assert distribution.p90 == pytest.approx(
        4.6
    )

    assert distribution.p95 == pytest.approx(
        4.8
    )


@pytest.mark.parametrize(
    "point",
    (
        0.0,
        -0.001,
        math.nan,
        math.inf,
    ),
)
def test_invalid_point_fails_closed(
    point: float,
) -> None:
    report = audit(
        point=point
    )

    assert report.valid is False

    assert report.reason == (
        "INVALID_SYMBOL_POINT"
    )


def test_naive_or_reversed_range_fails_closed() -> None:
    operation = Operation(
        mt5_api=FakeMT5()
    )

    report = operation.audit_records(
        raw_deals=(),
        ticks_by_order={},
        symbol=SYMBOL,
        point=0.001,
        date_from=datetime(
            2025,
            1,
            1,
        ),
        date_to=END,
    )

    assert report.reason == (
        "INVALID_UTC_HISTORY_RANGE"
    )

    report = operation.audit_records(
        raw_deals=(),
        ticks_by_order={},
        symbol=SYMBOL,
        point=0.001,
        date_from=END,
        date_to=START,
    )

    assert report.reason == (
        "INVALID_UTC_HISTORY_RANGE"
    )


def test_connected_read_uses_only_symbol_history_and_tick_reads() -> None:
    api = FakeMT5(
        deals=(
            deal(),
        ),
        ticks={
            9001: (
                tick(),
            )
        },
    )

    report = Operation(
        mt5_api=api
    ).read_history(
        symbol=SYMBOL,
        date_from=START,
        date_to=END,
    )

    assert report.valid is True

    assert [
        name
        for (
            name,
            _,
        )
        in api.calls
    ] == [
        "symbol_info",
        "history_deals_get",
        "copy_ticks_range",
    ]

    assert report.history_invoked is True

    assert report.symbol_info_invoked is True

    assert report.tick_history_invocations == 1


def test_connected_history_uses_symbol_group_and_utc_tick_windows() -> None:
    api = FakeMT5(
        deals=(
            deal(),
        ),
        ticks={
            9001: (
                tick(),
            )
        },
    )

    Operation(
        mt5_api=api
    ).read_history(
        symbol=SYMBOL,
        date_from=START,
        date_to=END,
    )

    history_call = [
        item
        for item
        in api.calls
        if item[
            0
        ]
        ==
        "history_deals_get"
    ][
        0
    ][
        1
    ]

    tick_call = [
        item
        for item
        in api.calls
        if item[
            0
        ]
        ==
        "copy_ticks_range"
    ][
        0
    ][
        1
    ]

    assert history_call[
        2
    ] == (
        f"*{SYMBOL}*"
    )

    assert tick_call[
        1
    ].tzinfo == timezone.utc

    assert tick_call[
        2
    ].tzinfo == timezone.utc


def test_symbol_info_failure_and_history_failure_are_fail_closed() -> None:
    api = FakeMT5(
        info=None
    )

    report = Operation(
        mt5_api=api
    ).read_history(
        symbol=SYMBOL,
        date_from=START,
        date_to=END,
    )

    assert report.reason == (
        "MT5_SYMBOL_INFO_READ_FAILED"
    )

    api = FakeMT5(
        deals=None,
        last_error=(
            -1,
            "history unavailable",
        ),
    )

    report = Operation(
        mt5_api=api
    ).read_history(
        symbol=SYMBOL,
        date_from=START,
        date_to=END,
    )

    assert report.reason == (
        "MT5_HISTORY_READ_FAILED"
    )

    assert (
        "history unavailable"
        in report.mt5_error
    )


def test_history_exception_is_fail_closed() -> None:
    api = FakeMT5(
        history_exception=RuntimeError(
            "boom"
        )
    )

    report = Operation(
        mt5_api=api
    ).read_history(
        symbol=SYMBOL,
        date_from=START,
        date_to=END,
    )

    assert report.reason == (
        "MT5_HISTORY_READ_EXCEPTION"
    )


def test_tick_read_failure_is_order_rejection_not_fake_data() -> None:
    api = FakeMT5(
        deals=(
            deal(),
        ),
        tick_exception_orders={
            9001
        },
    )

    report = Operation(
        mt5_api=api
    ).read_history(
        symbol=SYMBOL,
        date_from=START,
        date_to=END,
    )

    assert report.valid is True

    assert report.normalized_order_count == 0

    assert (
        dict(
            report.rejection_counts
        )[
            "MT5_TICK_HISTORY_READ_EXCEPTION"
        ]
        ==
        1
    )


def test_none_tick_read_is_order_rejection() -> None:
    api = FakeMT5(
        deals=(
            deal(),
        ),
        none_tick_orders={
            9001
        },
    )

    report = Operation(
        mt5_api=api
    ).read_history(
        symbol=SYMBOL,
        date_from=START,
        date_to=END,
    )

    assert (
        dict(
            report.rejection_counts
        )[
            "MT5_TICK_HISTORY_READ_FAILED"
        ]
        ==
        1
    )


def test_csv_export_is_runtime_only_data(
    tmp_path: Path,
) -> None:
    report = audit()

    path = Operation.write_csv(
        report,
        tmp_path
        /
        "history.csv",
    )

    text = path.read_text(
        encoding="utf-8"
    )

    assert "order_ticket" in text

    assert "9001" in text

    assert "lifecycle_attested" in text


def test_cli_defaults_cover_complete_available_history() -> None:
    args = (
        module
        .build_parser()
        .parse_args(
            []
        )
    )

    assert args.symbol == "XAUUSDm"

    assert args.from_date == (
        "2000-01-01T00:00:00Z"
    )

    assert args.to_date == "now"

    assert args.csv == ""