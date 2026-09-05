"""
Offline tests for MT5ReadOnlyFillTelemetryAdapter v1.0.
"""

from __future__ import annotations

import importlib
import math
from dataclasses import dataclass, replace
from datetime import timezone
from typing import Any

import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Shadow.mt5_read_only_fill_telemetry_adapter"
)

bridge_module: Any = importlib.import_module(
    "02_AI.Shadow.realized_fill_telemetry_bridge"
)


Adapter: Any = (
    module.MT5ReadOnlyFillTelemetryAdapter
)

Policy: Any = (
    module.MT5ReadOnlyFillPolicy
)

NormalizedTelemetry: Any = (
    bridge_module.NormalizedActualFillTelemetry
)


@dataclass(frozen=True)
class FakeDeal:
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


@dataclass(frozen=True)
class FakeTick:
    time_msc: int
    bid: float
    ask: float


class FakeMT5:
    DEAL_TYPE_BUY = 0
    DEAL_TYPE_SELL = 1

    DEAL_ENTRY_IN = 0
    DEAL_ENTRY_OUT = 1
    DEAL_ENTRY_INOUT = 2

    COPY_TICKS_INFO = 2
    COPY_TICKS_ALL = 3

    def __init__(
        self,
        *,
        deals: Any = (),
        ticks: Any = (),
        deal_exception: Exception | None = None,
        tick_exception: Exception | None = None,
        last_error_value: Any = (
            0,
            "OK",
        ),
        last_error_exception: Exception | None = None,
    ) -> None:

        self.deals = deals
        self.ticks = ticks

        self.deal_exception = (
            deal_exception
        )

        self.tick_exception = (
            tick_exception
        )

        self.last_error_value = (
            last_error_value
        )

        self.last_error_exception = (
            last_error_exception
        )

        self.calls: list[
            tuple[
                str,
                Any,
            ]
        ] = []

    def history_deals_get(
        self,
        *,
        ticket: int,
    ) -> Any:

        self.calls.append(
            (
                "history_deals_get",
                ticket,
            )
        )

        if self.deal_exception is not None:

            raise self.deal_exception

        return self.deals

    def copy_ticks_range(
        self,
        symbol: str,
        date_from: Any,
        date_to: Any,
        flags: int,
    ) -> Any:

        self.calls.append(
            (
                "copy_ticks_range",
                (
                    symbol,
                    date_from,
                    date_to,
                    flags,
                ),
            )
        )

        if self.tick_exception is not None:

            raise self.tick_exception

        return self.ticks

    def last_error(
        self,
    ) -> Any:

        self.calls.append(
            (
                "last_error",
                None,
            )
        )

        if self.last_error_exception is not None:

            raise self.last_error_exception

        return self.last_error_value


class FakeMT5AllTicksOnly:
    DEAL_TYPE_BUY = 0
    DEAL_TYPE_SELL = 1
    DEAL_ENTRY_IN = 0

    COPY_TICKS_ALL = 99

    def __init__(
        self,
        deals: Any,
        ticks: Any,
    ) -> None:

        self.deals = deals
        self.ticks = ticks
        self.calls: list[Any] = []

    def history_deals_get(
        self,
        *,
        ticket: int,
    ) -> Any:

        self.calls.append(
            (
                "history",
                ticket,
            )
        )

        return self.deals

    def copy_ticks_range(
        self,
        symbol: str,
        date_from: Any,
        date_to: Any,
        flags: int,
    ) -> Any:

        self.calls.append(
            (
                "ticks",
                symbol,
                flags,
            )
        )

        return self.ticks

    def last_error(
        self,
    ) -> Any:

        return (
            0,
            "OK",
        )


class FakeMT5NoTickFlags:
    DEAL_TYPE_BUY = 0
    DEAL_TYPE_SELL = 1
    DEAL_ENTRY_IN = 0

    def __init__(
        self,
        deals: Any,
    ) -> None:

        self.deals = deals

    def history_deals_get(
        self,
        *,
        ticket: int,
    ) -> Any:

        return self.deals

    def last_error(
        self,
    ) -> Any:

        return (
            0,
            "OK",
        )


ORDER = 900001
SYMBOL = "XAUUSDm"


def deal(
    *,
    ticket: int = 1001,
    order: int = ORDER,
    time_msc: int = 1_800_000_000_000,
    type: int = 0,
    entry: int = 0,
    volume: float = 0.01,
    price: float = 4316.720,
    commission: float = 0.0,
    fee: float = 0.0,
    symbol: str = SYMBOL,
) -> FakeDeal:

    return FakeDeal(
        ticket=ticket,
        order=order,
        time_msc=time_msc,
        type=type,
        entry=entry,
        volume=volume,
        price=price,
        commission=commission,
        fee=fee,
        symbol=symbol,
    )


def tick(
    *,
    time_msc: int = 1_799_999_999_990,
    bid: float = 4316.500,
    ask: float = 4316.700,
) -> FakeTick:

    return FakeTick(
        time_msc=time_msc,
        bid=bid,
        ask=ask,
    )


def normalize(
    *,
    deals: Any = None,
    ticks: Any = None,
    order_ticket: Any = ORDER,
    expected_symbol: Any = SYMBOL,
    expected_direction: Any = "LONG",
    expected_volume: Any = 0.01,
    policy: Any | None = None,
    api: Any | None = None,
) -> Any:

    resolved_deals = (
        (deal(),)
        if deals is None
        else deals
    )

    resolved_ticks = (
        (tick(),)
        if ticks is None
        else ticks
    )

    return Adapter(
        mt5_api=api,
        policy=policy,
    ).normalize_records(
        raw_deals=resolved_deals,
        raw_ticks=resolved_ticks,
        order_ticket=order_ticket,
        expected_symbol=expected_symbol,
        expected_direction=expected_direction,
        expected_volume=expected_volume,
        mt5_api=api,
    )


# =============================================================================
# Identity / safety
# =============================================================================


def test_adapter_is_shadow_read_only() -> None:

    result = normalize()

    assert result.valid is True
    assert result.normalized is True

    assert result.mode == (
        "SHADOW_MT5_READ_ONLY_FILL_TELEMETRY_ADAPTER_ONLY"
    )

    assert result.version == "1.0"
    assert result.live_authorized is False


def test_successful_result_emits_existing_normalized_telemetry_type() -> None:

    result = normalize()

    assert isinstance(
        result.telemetry,
        NormalizedTelemetry,
    )

    assert result.telemetry.live_authorized is False


def test_pure_normalization_does_not_claim_broker_reads() -> None:

    result = normalize()

    assert result.history_invoked is False
    assert result.tick_history_invoked is False


def test_execution_id_is_stable_order_identity() -> None:

    result = normalize()

    assert result.execution_id == (
        f"MT5_ORDER_{ORDER}"
    )

    assert result.telemetry.execution_id == (
        f"MT5_ORDER_{ORDER}"
    )


# =============================================================================
# Policy validation
# =============================================================================


@pytest.mark.parametrize(
    "policy",
    (
        Policy(
            quote_lookback_ms=0
        ),
        Policy(
            quote_lookback_ms=-1
        ),
        Policy(
            volume_tolerance=0.0
        ),
        Policy(
            volume_tolerance=-1.0
        ),
        Policy(
            numeric_tolerance=0.0
        ),
        Policy(
            numeric_tolerance=-1.0
        ),
    ),
)
def test_invalid_policy_fails_at_construction(
    policy: Any,
) -> None:

    with pytest.raises(
        ValueError
    ):

        Adapter(
            policy=policy
        )


# =============================================================================
# Basic LONG / SHORT normalization
# =============================================================================


def test_single_long_fill_normalizes_price_quote_volume() -> None:

    result = normalize()

    assert result.valid is True

    assert result.symbol == SYMBOL
    assert result.direction == "LONG"

    assert result.filled_volume == pytest.approx(
        0.01
    )

    assert result.weighted_fill_price == pytest.approx(
        4316.720
    )

    assert result.weighted_quote_bid == pytest.approx(
        4316.500
    )

    assert result.weighted_quote_ask == pytest.approx(
        4316.700
    )

    assert result.weighted_spread_price == pytest.approx(
        0.200
    )


def test_single_short_fill_normalizes() -> None:

    result = normalize(
        deals=(
            deal(
                type=1,
                price=4316.480,
            ),
        ),
        expected_direction="SHORT",
    )

    assert result.valid is True
    assert result.direction == "SHORT"

    assert result.telemetry.fill_price == pytest.approx(
        4316.480
    )

    assert result.telemetry.quote_bid == pytest.approx(
        4316.500
    )

    assert result.telemetry.quote_ask == pytest.approx(
        4316.700
    )


def test_expected_direction_buy_alias_normalizes_to_long() -> None:

    result = normalize(
        expected_direction="BUY"
    )

    assert result.valid is True
    assert result.expected_direction == "LONG"


def test_expected_direction_sell_alias_normalizes_to_short() -> None:

    result = normalize(
        deals=(
            deal(
                type=1
            ),
        ),
        expected_direction="SELL",
    )

    assert result.valid is True
    assert result.expected_direction == "SHORT"


def test_expected_symbol_match_is_case_insensitive() -> None:

    result = normalize(
        expected_symbol="xauusdm"
    )

    assert result.valid is True
    assert result.symbol == "XAUUSDm"


# =============================================================================
# Partial-fill aggregation
# =============================================================================


def test_two_partial_deals_aggregate_only_when_expected_volume_complete() -> None:

    first = deal(
        ticket=1001,
        time_msc=1_800_000_000_000,
        volume=0.004,
        price=4316.710,
    )

    second = deal(
        ticket=1002,
        time_msc=1_800_000_000_200,
        volume=0.006,
        price=4316.730,
    )

    ticks = (
        tick(
            time_msc=1_799_999_999_990,
            bid=4316.490,
            ask=4316.690,
        ),
        tick(
            time_msc=1_800_000_000_190,
            bid=4316.500,
            ask=4316.700,
        ),
    )

    result = normalize(
        deals=(
            first,
            second,
        ),
        ticks=ticks,
    )

    assert result.valid is True

    assert result.selected_deal_count == 2

    assert result.deal_tickets == (
        1001,
        1002,
    )

    assert result.filled_volume == pytest.approx(
        0.01
    )

    assert result.weighted_fill_price == pytest.approx(
        (
            4316.710 * 0.004
            +
            4316.730 * 0.006
        )
        /
        0.01
    )

    assert result.weighted_quote_bid == pytest.approx(
        (
            4316.490 * 0.004
            +
            4316.500 * 0.006
        )
        /
        0.01
    )

    assert result.weighted_quote_ask == pytest.approx(
        (
            4316.690 * 0.004
            +
            4316.700 * 0.006
        )
        /
        0.01
    )


def test_partial_fill_below_expected_volume_fails_closed() -> None:

    result = normalize(
        deals=(
            deal(
                volume=0.005
            ),
        ),
    )

    assert result.valid is False

    assert result.reason == (
        "PARTIAL_OR_OVERFILL_VOLUME_MISMATCH"
    )

    assert result.filled_volume == pytest.approx(
        0.005
    )

    assert result.telemetry is None


def test_overfill_above_expected_volume_fails_closed() -> None:

    result = normalize(
        deals=(
            deal(
                volume=0.02
            ),
        ),
    )

    assert result.valid is False

    assert result.reason == (
        "PARTIAL_OR_OVERFILL_VOLUME_MISMATCH"
    )


def test_small_volume_float_noise_within_tolerance_is_allowed() -> None:

    result = normalize(
        deals=(
            deal(
                volume=0.010000000001
            ),
        ),
    )

    assert result.valid is True


def test_volume_difference_outside_tolerance_is_rejected() -> None:

    result = normalize(
        deals=(
            deal(
                volume=0.010001
            ),
        ),
    )

    assert result.valid is False

    assert result.reason == (
        "PARTIAL_OR_OVERFILL_VOLUME_MISMATCH"
    )


# =============================================================================
# Commission / fee normalization
# =============================================================================


def test_negative_mt5_commission_becomes_positive_normalized_cost() -> None:

    result = normalize(
        deals=(
            deal(
                commission=-0.04
            ),
        ),
    )

    assert result.valid is True

    assert result.raw_commission_sum == pytest.approx(
        -0.04
    )

    assert result.normalized_commission_cost == pytest.approx(
        0.04
    )

    assert result.telemetry.commission_cost == pytest.approx(
        0.04
    )


def test_negative_commission_and_fee_are_combined() -> None:

    result = normalize(
        deals=(
            deal(
                commission=-0.03,
                fee=-0.02,
            ),
        ),
    )

    assert result.valid is True

    assert result.raw_commission_sum == pytest.approx(
        -0.03
    )

    assert result.raw_fee_sum == pytest.approx(
        -0.02
    )

    assert result.normalized_commission_cost == pytest.approx(
        0.05
    )


def test_multi_deal_commissions_are_aggregated() -> None:

    result = normalize(
        deals=(
            deal(
                ticket=1001,
                volume=0.004,
                commission=-0.01,
            ),
            deal(
                ticket=1002,
                time_msc=1_800_000_000_100,
                volume=0.006,
                commission=-0.02,
                fee=-0.01,
            ),
        ),
        ticks=(
            tick(
                time_msc=1_799_999_999_990
            ),
            tick(
                time_msc=1_800_000_000_090
            ),
        ),
    )

    assert result.valid is True

    assert result.normalized_commission_cost == pytest.approx(
        0.04
    )


def test_zero_commission_and_fee_are_explicit_zero_cost() -> None:

    result = normalize()

    assert result.valid is True

    assert result.normalized_commission_cost == pytest.approx(
        0.0
    )

    assert result.telemetry.commission_cost == pytest.approx(
        0.0
    )


def test_positive_commission_fails_closed_instead_of_losing_rebate_sign() -> None:

    result = normalize(
        deals=(
            deal(
                commission=0.01
            ),
        ),
    )

    assert result.valid is False

    assert result.reason == (
        "POSITIVE_COMMISSION_OR_FEE_NOT_SUPPORTED"
    )


def test_positive_fee_fails_closed() -> None:

    result = normalize(
        deals=(
            deal(
                fee=0.01
            ),
        ),
    )

    assert result.valid is False

    assert result.reason == (
        "POSITIVE_COMMISSION_OR_FEE_NOT_SUPPORTED"
    )


@pytest.mark.parametrize(
    "field",
    (
        "commission",
        "fee",
    ),
)
def test_non_finite_commission_or_fee_fails_closed(
    field: str,
) -> None:

    values = {
        field: math.nan
    }

    result = normalize(
        deals=(
            replace(
                deal(),
                **values,
            ),
        ),
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_DEAL_COMMISSION_OR_FEE"
    )


# =============================================================================
# Deal linkage and fail-closed behavior
# =============================================================================


def test_zero_volume_non_trade_history_row_is_ignored() -> None:

    metadata = deal(
        ticket=999,
        type=2,
        volume=0.0,
        price=0.0,
        symbol="",
    )

    result = normalize(
        deals=(
            metadata,
            deal(),
        ),
    )

    assert result.valid is True
    assert result.raw_deal_count == 2
    assert result.selected_deal_count == 1


def test_positive_volume_non_buy_sell_deal_fails_closed() -> None:

    result = normalize(
        deals=(
            deal(
                type=2
            ),
        ),
    )

    assert result.valid is False

    assert result.reason == (
        "NON_BUY_SELL_DEAL_FOR_ORDER"
    )


def test_exit_deal_is_not_accepted_as_new_exposure_fill() -> None:

    result = normalize(
        deals=(
            deal(
                entry=1
            ),
        ),
    )

    assert result.valid is False

    assert result.reason == (
        "NON_ENTRY_DEAL_NOT_SUPPORTED"
    )


def test_inout_deal_is_not_accepted_as_new_exposure_fill() -> None:

    result = normalize(
        deals=(
            deal(
                entry=2
            ),
        ),
    )

    assert result.valid is False

    assert result.reason == (
        "NON_ENTRY_DEAL_NOT_SUPPORTED"
    )


def test_mixed_fill_directions_fail_closed() -> None:

    result = normalize(
        deals=(
            deal(
                ticket=1001,
                volume=0.005,
                type=0,
            ),
            deal(
                ticket=1002,
                time_msc=1_800_000_000_100,
                volume=0.005,
                type=1,
            ),
        ),
    )

    assert result.valid is False

    assert result.reason == (
        "MIXED_FILL_DIRECTIONS"
    )


def test_mixed_fill_symbols_fail_closed() -> None:

    result = normalize(
        deals=(
            deal(
                ticket=1001,
                volume=0.005,
                symbol="XAUUSDm",
            ),
            deal(
                ticket=1002,
                time_msc=1_800_000_000_100,
                volume=0.005,
                symbol="XAUUSD",
            ),
        ),
    )

    assert result.valid is False

    assert result.reason == (
        "MIXED_FILL_SYMBOLS"
    )


def test_expected_symbol_mismatch_fails_closed() -> None:

    result = normalize(
        expected_symbol="XAUUSD"
    )

    assert result.valid is False

    assert result.reason == (
        "EXPECTED_SYMBOL_MISMATCH"
    )


def test_expected_direction_mismatch_fails_closed() -> None:

    result = normalize(
        expected_direction="SHORT"
    )

    assert result.valid is False

    assert result.reason == (
        "EXPECTED_DIRECTION_MISMATCH"
    )


def test_deal_order_linkage_mismatch_fails_closed() -> None:

    result = normalize(
        deals=(
            deal(
                order=ORDER + 1
            ),
        ),
    )

    assert result.valid is False

    assert result.reason == (
        "DEAL_ORDER_LINKAGE_MISMATCH"
    )


def test_duplicate_deal_ticket_fails_closed() -> None:

    result = normalize(
        deals=(
            deal(
                ticket=1001,
                volume=0.005,
            ),
            deal(
                ticket=1001,
                time_msc=1_800_000_000_100,
                volume=0.005,
            ),
        ),
    )

    assert result.valid is False

    assert result.reason == (
        "DUPLICATE_DEAL_TICKET"
    )


def test_invalid_deal_ticket_fails_closed() -> None:

    result = normalize(
        deals=(
            deal(
                ticket=0
            ),
        ),
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_DEAL_TICKET"
    )


def test_invalid_deal_time_fails_closed() -> None:

    result = normalize(
        deals=(
            deal(
                time_msc=0
            ),
        ),
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_DEAL_TIME_MSC"
    )


@pytest.mark.parametrize(
    "bad_volume",
    (
        -0.01,
        math.nan,
        math.inf,
    ),
)
def test_invalid_deal_volume_fails_closed(
    bad_volume: float,
) -> None:

    result = normalize(
        deals=(
            deal(
                volume=bad_volume
            ),
        ),
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_DEAL_VOLUME"
    )


@pytest.mark.parametrize(
    "bad_price",
    (
        0.0,
        -1.0,
        math.nan,
        math.inf,
    ),
)
def test_invalid_deal_price_fails_closed(
    bad_price: float,
) -> None:

    result = normalize(
        deals=(
            deal(
                price=bad_price
            ),
        ),
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_DEAL_PRICE"
    )


def test_empty_deal_symbol_fails_closed() -> None:

    result = normalize(
        deals=(
            deal(
                symbol=""
            ),
        ),
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_DEAL_SYMBOL"
    )


def test_no_entry_fill_deals_fails_closed() -> None:

    result = normalize(
        deals=(),
    )

    assert result.valid is False

    assert result.reason == (
        "NO_ENTRY_FILL_DEALS"
    )


# =============================================================================
# Public input validation
# =============================================================================


@pytest.mark.parametrize(
    "order_ticket",
    (
        0,
        -1,
        "bad",
        None,
    ),
)
def test_invalid_order_ticket_is_rejected_before_any_broker_read(
    order_ticket: Any,
) -> None:

    api = FakeMT5()

    result = Adapter(
        mt5_api=api
    ).read_order_fill(
        order_ticket=order_ticket,
        expected_symbol=SYMBOL,
        expected_direction="LONG",
        expected_volume=0.01,
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_ORDER_TICKET"
    )

    assert api.calls == []


def test_empty_expected_symbol_is_rejected_before_broker_read() -> None:

    api = FakeMT5()

    result = Adapter(
        mt5_api=api
    ).read_order_fill(
        order_ticket=ORDER,
        expected_symbol="",
        expected_direction="LONG",
        expected_volume=0.01,
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_EXPECTED_SYMBOL"
    )

    assert api.calls == []


def test_invalid_expected_direction_is_rejected_before_broker_read() -> None:

    api = FakeMT5()

    result = Adapter(
        mt5_api=api
    ).read_order_fill(
        order_ticket=ORDER,
        expected_symbol=SYMBOL,
        expected_direction="SIDEWAYS",
        expected_volume=0.01,
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_EXPECTED_DIRECTION"
    )

    assert api.calls == []


@pytest.mark.parametrize(
    "expected_volume",
    (
        0.0,
        -0.01,
        math.nan,
        math.inf,
    ),
)
def test_invalid_expected_volume_is_rejected_before_broker_read(
    expected_volume: float,
) -> None:

    api = FakeMT5()

    result = Adapter(
        mt5_api=api
    ).read_order_fill(
        order_ticket=ORDER,
        expected_symbol=SYMBOL,
        expected_direction="LONG",
        expected_volume=expected_volume,
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_EXPECTED_VOLUME"
    )

    assert api.calls == []


# =============================================================================
# Causal quote reconstruction
# =============================================================================


def test_latest_tick_at_or_before_deal_is_selected() -> None:

    result = normalize(
        ticks=(
            tick(
                time_msc=1_799_999_999_800,
                bid=4316.400,
                ask=4316.600,
            ),
            tick(
                time_msc=1_799_999_999_990,
                bid=4316.500,
                ask=4316.700,
            ),
        ),
    )

    assert result.valid is True

    assert result.weighted_quote_bid == pytest.approx(
        4316.500
    )

    assert result.weighted_quote_ask == pytest.approx(
        4316.700
    )


def test_tick_at_exact_deal_timestamp_is_causal() -> None:

    result = normalize(
        ticks=(
            tick(
                time_msc=1_800_000_000_000,
                bid=4316.510,
                ask=4316.710,
            ),
        ),
    )

    assert result.valid is True

    assert result.max_quote_age_ms == 0

    assert result.weighted_quote_bid == pytest.approx(
        4316.510
    )


def test_post_fill_tick_is_never_used_as_fallback() -> None:

    result = normalize(
        ticks=(
            tick(
                time_msc=1_800_000_000_001,
                bid=4316.500,
                ask=4316.700,
            ),
        ),
    )

    assert result.valid is False

    assert result.reason == (
        "NO_CAUSAL_QUOTE_FOR_FILL"
    )


def test_stale_pre_fill_tick_outside_lookback_is_rejected() -> None:

    result = normalize(
        ticks=(
            tick(
                time_msc=1_799_999_997_000
            ),
        ),
    )

    assert result.valid is False

    assert result.reason == (
        "CAUSAL_QUOTE_OUTSIDE_LOOKBACK"
    )


def test_quote_age_is_auditable_per_deal() -> None:

    result = normalize(
        ticks=(
            tick(
                time_msc=1_799_999_999_900
            ),
        ),
    )

    assert result.valid is True

    assert result.quote_age_ms_by_deal == (
        (
            1001,
            100,
        ),
    )

    assert result.max_quote_age_ms == 100


def test_each_partial_fill_gets_its_own_causal_quote() -> None:

    deals = (
        deal(
            ticket=1001,
            time_msc=1_800_000_000_000,
            volume=0.005,
            price=4316.710,
        ),
        deal(
            ticket=1002,
            time_msc=1_800_000_000_500,
            volume=0.005,
            price=4316.730,
        ),
    )

    ticks = (
        tick(
            time_msc=1_799_999_999_990,
            bid=4316.490,
            ask=4316.690,
        ),
        tick(
            time_msc=1_800_000_000_490,
            bid=4316.510,
            ask=4316.710,
        ),
    )

    result = normalize(
        deals=deals,
        ticks=ticks,
    )

    assert result.valid is True

    assert result.weighted_quote_bid == pytest.approx(
        4316.500
    )

    assert result.weighted_quote_ask == pytest.approx(
        4316.700
    )

    assert result.quote_age_ms_by_deal == (
        (
            1001,
            10,
        ),
        (
            1002,
            10,
        ),
    )


def test_invalid_tick_rows_are_ignored_when_valid_tick_exists() -> None:

    result = normalize(
        ticks=(
            FakeTick(
                time_msc=0,
                bid=0.0,
                ask=0.0,
            ),
            FakeTick(
                time_msc=1_799_999_999_980,
                bid=4316.800,
                ask=4316.700,
            ),
            tick(),
        ),
    )

    assert result.valid is True

    assert result.weighted_quote_bid == pytest.approx(
        4316.500
    )


def test_all_invalid_ticks_fail_closed() -> None:

    result = normalize(
        ticks=(
            FakeTick(
                time_msc=0,
                bid=0.0,
                ask=0.0,
            ),
            FakeTick(
                time_msc=1_799_999_999_990,
                bid=4316.800,
                ask=4316.700,
            ),
        ),
    )

    assert result.valid is False

    assert result.reason == (
        "NO_VALID_QUOTE_TICKS"
    )


def test_tiny_quote_rounding_inversion_within_tolerance_is_flattened() -> None:

    bid = 4316.70000000005
    ask = 4316.70000000000

    result = normalize(
        ticks=(
            tick(
                bid=bid,
                ask=ask,
            ),
        ),
    )

    assert result.valid is True

    assert result.weighted_spread_price == pytest.approx(
        0.0
    )


# =============================================================================
# Live MT5 read-path behavior using fake API
# =============================================================================


def test_read_order_fill_uses_only_history_and_tick_read_paths() -> None:

    api = FakeMT5(
        deals=(
            deal(),
        ),
        ticks=(
            tick(),
        ),
    )

    result = Adapter(
        mt5_api=api
    ).read_order_fill(
        order_ticket=ORDER,
        expected_symbol=SYMBOL,
        expected_direction="LONG",
        expected_volume=0.01,
    )

    assert result.valid is True

    assert result.history_invoked is True
    assert result.tick_history_invoked is True

    assert [
        call[
            0
        ]
        for call
        in api.calls
    ] == [
        "history_deals_get",
        "copy_ticks_range",
    ]


def test_read_path_passes_order_ticket_to_history_deals_get() -> None:

    api = FakeMT5(
        deals=(
            deal(),
        ),
        ticks=(
            tick(),
        ),
    )

    Adapter(
        mt5_api=api
    ).read_order_fill(
        order_ticket=ORDER,
        expected_symbol=SYMBOL,
        expected_direction="LONG",
        expected_volume=0.01,
    )

    assert api.calls[
        0
    ] == (
        "history_deals_get",
        ORDER,
    )


def test_read_path_uses_actual_deal_symbol_for_tick_query() -> None:

    api = FakeMT5(
        deals=(
            deal(
                symbol="XAUUSDm"
            ),
        ),
        ticks=(
            tick(),
        ),
    )

    result = Adapter(
        mt5_api=api
    ).read_order_fill(
        order_ticket=ORDER,
        expected_symbol="xauusdm",
        expected_direction="LONG",
        expected_volume=0.01,
    )

    assert result.valid is True

    tick_call = api.calls[
        1
    ][
        1
    ]

    assert tick_call[
        0
    ] == "XAUUSDm"


def test_read_path_uses_utc_datetimes() -> None:

    api = FakeMT5(
        deals=(
            deal(),
        ),
        ticks=(
            tick(),
        ),
    )

    Adapter(
        mt5_api=api
    ).read_order_fill(
        order_ticket=ORDER,
        expected_symbol=SYMBOL,
        expected_direction="LONG",
        expected_volume=0.01,
    )

    tick_call = api.calls[
        1
    ][
        1
    ]

    date_from = tick_call[
        1
    ]

    date_to = tick_call[
        2
    ]

    assert date_from.tzinfo == timezone.utc
    assert date_to.tzinfo == timezone.utc


def test_read_path_prefers_copy_ticks_info() -> None:

    api = FakeMT5(
        deals=(
            deal(),
        ),
        ticks=(
            tick(),
        ),
    )

    Adapter(
        mt5_api=api
    ).read_order_fill(
        order_ticket=ORDER,
        expected_symbol=SYMBOL,
        expected_direction="LONG",
        expected_volume=0.01,
    )

    flags = api.calls[
        1
    ][
        1
    ][
        3
    ]

    assert flags == api.COPY_TICKS_INFO


def test_read_path_falls_back_to_copy_ticks_all_when_info_flag_absent() -> None:

    api = FakeMT5AllTicksOnly(
        deals=(
            deal(),
        ),
        ticks=(
            tick(),
        ),
    )

    result = Adapter(
        mt5_api=api
    ).read_order_fill(
        order_ticket=ORDER,
        expected_symbol=SYMBOL,
        expected_direction="LONG",
        expected_volume=0.01,
    )

    assert result.valid is True

    assert api.calls[
        1
    ][
        2
    ] == api.COPY_TICKS_ALL


def test_missing_tick_flags_fail_closed_before_tick_read() -> None:

    api = FakeMT5NoTickFlags(
        deals=(
            deal(),
        )
    )

    result = Adapter(
        mt5_api=api
    ).read_order_fill(
        order_ticket=ORDER,
        expected_symbol=SYMBOL,
        expected_direction="LONG",
        expected_volume=0.01,
    )

    assert result.valid is False

    assert result.reason == (
        "MT5_TICK_FLAG_UNAVAILABLE"
    )

    assert result.history_invoked is True
    assert result.tick_history_invoked is False


# =============================================================================
# MT5 read failures
# =============================================================================


def test_none_deal_history_is_fail_closed_with_last_error() -> None:

    api = FakeMT5(
        deals=None,
        last_error_value=(
            -1,
            "history unavailable",
        ),
    )

    result = Adapter(
        mt5_api=api
    ).read_order_fill(
        order_ticket=ORDER,
        expected_symbol=SYMBOL,
        expected_direction="LONG",
        expected_volume=0.01,
    )

    assert result.valid is False

    assert result.reason == (
        "MT5_DEAL_HISTORY_READ_FAILED"
    )

    assert "history unavailable" in result.mt5_error


def test_deal_history_exception_is_fail_closed() -> None:

    api = FakeMT5(
        deal_exception=RuntimeError(
            "history failure"
        )
    )

    result = Adapter(
        mt5_api=api
    ).read_order_fill(
        order_ticket=ORDER,
        expected_symbol=SYMBOL,
        expected_direction="LONG",
        expected_volume=0.01,
    )

    assert result.valid is False

    assert result.reason == (
        "MT5_DEAL_HISTORY_READ_EXCEPTION"
    )

    assert result.history_invoked is True
    assert result.tick_history_invoked is False


def test_none_tick_history_is_fail_closed_with_last_error() -> None:

    api = FakeMT5(
        deals=(
            deal(),
        ),
        ticks=None,
        last_error_value=(
            -2,
            "tick history unavailable",
        ),
    )

    result = Adapter(
        mt5_api=api
    ).read_order_fill(
        order_ticket=ORDER,
        expected_symbol=SYMBOL,
        expected_direction="LONG",
        expected_volume=0.01,
    )

    assert result.valid is False

    assert result.reason == (
        "MT5_TICK_HISTORY_READ_FAILED"
    )

    assert result.history_invoked is True
    assert result.tick_history_invoked is True

    assert "tick history unavailable" in result.mt5_error


def test_tick_history_exception_is_fail_closed() -> None:

    api = FakeMT5(
        deals=(
            deal(),
        ),
        tick_exception=RuntimeError(
            "tick failure"
        ),
    )

    result = Adapter(
        mt5_api=api
    ).read_order_fill(
        order_ticket=ORDER,
        expected_symbol=SYMBOL,
        expected_direction="LONG",
        expected_volume=0.01,
    )

    assert result.valid is False

    assert result.reason == (
        "MT5_TICK_HISTORY_READ_EXCEPTION"
    )


def test_last_error_exception_does_not_escape_adapter() -> None:

    api = FakeMT5(
        deals=None,
        last_error_exception=RuntimeError(
            "last error broken"
        ),
    )

    result = Adapter(
        mt5_api=api
    ).read_order_fill(
        order_ticket=ORDER,
        expected_symbol=SYMBOL,
        expected_direction="LONG",
        expected_volume=0.01,
    )

    assert result.valid is False

    assert result.mt5_error == (
        "unavailable"
    )


# =============================================================================
# Completed-volume gate occurs before tick history
# =============================================================================


def test_partial_order_does_not_query_ticks() -> None:

    api = FakeMT5(
        deals=(
            deal(
                volume=0.005
            ),
        ),
        ticks=(
            tick(),
        ),
    )

    result = Adapter(
        mt5_api=api
    ).read_order_fill(
        order_ticket=ORDER,
        expected_symbol=SYMBOL,
        expected_direction="LONG",
        expected_volume=0.01,
    )

    assert result.valid is False

    assert result.reason == (
        "PARTIAL_OR_OVERFILL_VOLUME_MISMATCH"
    )

    assert [
        call[
            0
        ]
        for call
        in api.calls
    ] == [
        "history_deals_get",
    ]


def test_exit_order_does_not_query_ticks() -> None:

    api = FakeMT5(
        deals=(
            deal(
                entry=1
            ),
        ),
    )

    result = Adapter(
        mt5_api=api
    ).read_order_fill(
        order_ticket=ORDER,
        expected_symbol=SYMBOL,
        expected_direction="LONG",
        expected_volume=0.01,
    )

    assert result.valid is False

    assert result.reason == (
        "NON_ENTRY_DEAL_NOT_SUPPORTED"
    )

    assert [
        call[
            0
        ]
        for call
        in api.calls
    ] == [
        "history_deals_get",
    ]


# =============================================================================
# Downstream bridge contract
# =============================================================================


def test_output_contract_contains_exact_completed_volume() -> None:

    result = normalize()

    assert result.telemetry.filled_volume == pytest.approx(
        result.expected_volume
    )


def test_output_contract_contains_volume_weighted_fill_and_quote() -> None:

    deals = (
        deal(
            ticket=1001,
            volume=0.003,
            price=4316.710,
        ),
        deal(
            ticket=1002,
            time_msc=1_800_000_000_200,
            volume=0.007,
            price=4316.730,
        ),
    )

    ticks = (
        tick(
            time_msc=1_799_999_999_990,
            bid=4316.490,
            ask=4316.690,
        ),
        tick(
            time_msc=1_800_000_000_190,
            bid=4316.510,
            ask=4316.710,
        ),
    )

    result = normalize(
        deals=deals,
        ticks=ticks,
    )

    assert result.valid is True

    assert result.telemetry.fill_price == pytest.approx(
        result.weighted_fill_price
    )

    assert result.telemetry.quote_bid == pytest.approx(
        result.weighted_quote_bid
    )

    assert result.telemetry.quote_ask == pytest.approx(
        result.weighted_quote_ask
    )


def test_adapter_never_emits_live_authorized_telemetry() -> None:

    result = normalize()

    assert result.live_authorized is False
    assert result.telemetry.live_authorized is False


def test_failed_normalization_never_emits_telemetry() -> None:

    result = normalize(
        deals=(
            deal(
                volume=0.005
            ),
        ),
    )

    assert result.valid is False
    assert result.normalized is False
    assert result.telemetry is None


def test_adapter_does_not_call_realized_fill_bridge() -> None:
    """
    Adapter output is data only. Accounting/observation remains downstream.
    """

    result = normalize()

    assert result.valid is True

    assert isinstance(
        result.telemetry,
        NormalizedTelemetry,
    )

    assert not hasattr(
        result,
        "observer_result",
    )