"""Offline tests for MT5 read-only completed fill adapter."""

from __future__ import annotations

import importlib
import math

from dataclasses import dataclass
from typing import Any

import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Shadow.mt5_read_only_completed_fill_adapter"
)

Adapter: Any = (
    module.MT5ReadOnlyCompletedFillAdapter
)

Policy: Any = (
    module.MT5CompletedFillPolicy
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


class FakeMT5:
    DEAL_TYPE_BUY = 0
    DEAL_TYPE_SELL = 1

    DEAL_ENTRY_IN = 0
    DEAL_ENTRY_OUT = 1

    def __init__(
        self,
        *,
        deals: Any = (),
        exception: Exception | None = None,
        last_error: Any = (
            0,
            "OK",
        ),
    ) -> None:
        self.deals = deals
        self.exception = exception

        self.last_error_value = (
            last_error
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

        if self.exception is not None:
            raise self.exception

        return self.deals

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


def deal(
    *,
    ticket: int = 1001,
    order: int = 9001,
    time_msc: int = 1_800_000_000_000,
    type: int = 0,
    entry: int = 0,
    volume: float = 0.01,
    price: float = 4316.800,
    commission: float = 0.0,
    fee: float = 0.0,
    symbol: str = "XAUUSDm",
) -> Deal:
    return Deal(
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


def normalize(
    *,
    raw_deals: Any = None,
    order: int = 9001,
    symbol: str = "XAUUSDm",
    direction: str = "LONG",
    volume: float = 0.01,
    api: Any | None = None,
) -> Any:
    rows = (
        (
            deal(),
        )
        if raw_deals is None
        else raw_deals
    )

    return Adapter(
        mt5_api=api
    ).normalize_records(
        raw_deals=rows,
        order_ticket=order,
        expected_symbol=symbol,
        expected_direction=direction,
        expected_volume=volume,
        mt5_api=api,
    )


def test_identity_and_live_boundary() -> None:
    result = normalize()

    assert result.valid
    assert result.normalized

    assert result.mode == (
        "SHADOW_MT5_READ_ONLY_COMPLETED_FILL_ADAPTER_ONLY"
    )

    assert result.version == "1.0"

    assert result.live_authorized is False

    assert (
        result.completed_fill.live_authorized
        is False
    )


def test_long_fill_normalizes_without_ticks() -> None:
    result = normalize()

    assert result.reason == (
        "OK_MT5_COMPLETED_FILL_NORMALIZED_WITHOUT_TICKS"
    )

    assert result.execution_id == (
        "MT5_ORDER_9001"
    )

    assert result.direction == "LONG"

    assert (
        result.filled_volume
        ==
        pytest.approx(
            0.01
        )
    )

    assert (
        result.weighted_fill_price
        ==
        pytest.approx(
            4316.800
        )
    )

    assert (
        result.completed_fill.fill_price
        ==
        pytest.approx(
            4316.800
        )
    )


def test_short_fill_normalizes() -> None:
    result = normalize(
        raw_deals=(
            deal(
                type=1
            ),
        ),
        direction="SHORT",
    )

    assert result.valid

    assert result.direction == "SHORT"


def test_direction_aliases() -> None:
    assert normalize(
        direction="buy"
    ).valid

    assert normalize(
        raw_deals=(
            deal(
                type=1
            ),
        ),
        direction="sell",
    ).valid


def test_symbol_match_is_case_insensitive() -> None:
    assert normalize(
        symbol="xauusdm"
    ).valid


def test_partial_fills_are_volume_weighted() -> None:
    result = normalize(
        raw_deals=(
            deal(
                ticket=1001,
                volume=0.004,
                price=4316.700,
            ),
            deal(
                ticket=1002,
                time_msc=1_800_000_000_100,
                volume=0.006,
                price=4316.900,
            ),
        ),
    )

    expected = (
        (
            4316.700
            *
            0.004
        )
        +
        (
            4316.900
            *
            0.006
        )
    ) / 0.01

    assert result.valid

    assert result.selected_deal_count == 2

    assert (
        result.weighted_fill_price
        ==
        pytest.approx(
            expected
        )
    )

    assert result.deal_tickets == (
        1001,
        1002,
    )


@pytest.mark.parametrize(
    "actual_volume",
    [
        0.009,
        0.011,
    ],
)
def test_partial_or_overfill_rejected(
    actual_volume: float,
) -> None:
    result = normalize(
        raw_deals=(
            deal(
                volume=actual_volume
            ),
        ),
    )

    assert result.reason == (
        "PARTIAL_OR_OVERFILL_VOLUME_MISMATCH"
    )


def test_volume_tolerance_is_honored() -> None:
    adapter = Adapter(
        policy=Policy(
            volume_tolerance=1e-6
        )
    )

    result = adapter.normalize_records(
        raw_deals=(
            deal(
                volume=0.0100005
            ),
        ),
        order_ticket=9001,
        expected_symbol="XAUUSDm",
        expected_direction="LONG",
        expected_volume=0.01,
    )

    assert result.valid


def test_commission_and_fee_normalize_to_positive_cost() -> None:
    result = normalize(
        raw_deals=(
            deal(
                commission=-0.03,
                fee=-0.02,
            ),
        )
    )

    assert (
        result.raw_commission_sum
        ==
        pytest.approx(
            -0.03
        )
    )

    assert (
        result.raw_fee_sum
        ==
        pytest.approx(
            -0.02
        )
    )

    assert (
        result.normalized_commission_cost
        ==
        pytest.approx(
            0.05
        )
    )

    assert (
        result
        .completed_fill
        .commission_cost
        ==
        pytest.approx(
            0.05
        )
    )


@pytest.mark.parametrize(
    (
        "commission",
        "fee",
    ),
    [
        (
            0.01,
            0.0,
        ),
        (
            0.0,
            0.01,
        ),
    ],
)
def test_positive_commission_or_fee_fails_closed(
    commission: float,
    fee: float,
) -> None:
    result = normalize(
        raw_deals=(
            deal(
                commission=commission,
                fee=fee,
            ),
        )
    )

    assert result.reason == (
        "POSITIVE_COMMISSION_OR_FEE_NOT_SUPPORTED"
    )


@pytest.mark.parametrize(
    (
        "commission",
        "fee",
    ),
    [
        (
            math.nan,
            0.0,
        ),
        (
            0.0,
            math.inf,
        ),
    ],
)
def test_nonfinite_commission_or_fee_fails_closed(
    commission: float,
    fee: float,
) -> None:
    result = normalize(
        raw_deals=(
            deal(
                commission=commission,
                fee=fee,
            ),
        )
    )

    assert result.reason == (
        "INVALID_DEAL_COMMISSION_OR_FEE"
    )


def test_zero_volume_metadata_row_is_ignored() -> None:
    metadata = deal(
        ticket=5000,
        order=0,
        time_msc=0,
        type=999,
        entry=999,
        volume=0.0,
        price=0.0,
        symbol="",
    )

    result = normalize(
        raw_deals=(
            metadata,
            deal(),
        )
    )

    assert result.valid

    assert result.raw_deal_count == 2

    assert result.selected_deal_count == 1


@pytest.mark.parametrize(
    (
        "raw",
        "reason",
    ),
    [
        (
            (
                deal(
                    type=999
                ),
            ),
            "NON_BUY_SELL_DEAL_FOR_ORDER",
        ),
        (
            (
                deal(
                    ticket=0
                ),
            ),
            "INVALID_DEAL_TICKET",
        ),
        (
            (
                deal(
                    order=9999
                ),
            ),
            "DEAL_ORDER_LINKAGE_MISMATCH",
        ),
        (
            (
                deal(
                    time_msc=0
                ),
            ),
            "INVALID_DEAL_TIME_MSC",
        ),
        (
            (
                deal(
                    entry=1
                ),
            ),
            "NON_ENTRY_DEAL_NOT_SUPPORTED",
        ),
        (
            (
                deal(
                    volume=-0.01
                ),
            ),
            "INVALID_DEAL_VOLUME",
        ),
        (
            (
                deal(
                    price=0.0
                ),
            ),
            "INVALID_DEAL_PRICE",
        ),
        (
            (
                deal(
                    symbol=""
                ),
            ),
            "INVALID_DEAL_SYMBOL",
        ),
    ],
)
def test_invalid_deal_fields_fail_closed(
    raw: tuple[
        Any,
        ...,
    ],
    reason: str,
) -> None:
    result = normalize(
        raw_deals=raw
    )

    assert result.valid is False

    assert result.reason == reason


def test_duplicate_deal_ticket_rejected() -> None:
    result = normalize(
        raw_deals=(
            deal(
                ticket=1001,
                volume=0.005,
            ),
            deal(
                ticket=1001,
                time_msc=1_800_000_000_100,
                volume=0.005,
            ),
        )
    )

    assert result.reason == (
        "DUPLICATE_DEAL_TICKET"
    )


def test_mixed_symbols_rejected() -> None:
    result = normalize(
        raw_deals=(
            deal(
                ticket=1001,
                volume=0.005,
            ),
            deal(
                ticket=1002,
                volume=0.005,
                symbol="EURUSD",
            ),
        )
    )

    assert result.reason == (
        "MIXED_FILL_SYMBOLS"
    )


def test_mixed_directions_rejected() -> None:
    result = normalize(
        raw_deals=(
            deal(
                ticket=1001,
                volume=0.005,
                type=0,
            ),
            deal(
                ticket=1002,
                volume=0.005,
                type=1,
            ),
        )
    )

    assert result.reason == (
        "MIXED_FILL_DIRECTIONS"
    )


def test_expected_symbol_mismatch() -> None:
    result = normalize(
        symbol="EURUSD"
    )

    assert result.reason == (
        "EXPECTED_SYMBOL_MISMATCH"
    )


def test_expected_direction_mismatch() -> None:
    result = normalize(
        direction="SHORT"
    )

    assert result.reason == (
        "EXPECTED_DIRECTION_MISMATCH"
    )


def test_no_entry_fill_deals() -> None:
    result = normalize(
        raw_deals=()
    )

    assert result.reason == (
        "NO_ENTRY_FILL_DEALS"
    )


@pytest.mark.parametrize(
    (
        "kwargs",
        "reason",
    ),
    [
        (
            {
                "order": 0,
            },
            "INVALID_ORDER_TICKET",
        ),
        (
            {
                "symbol": "",
            },
            "INVALID_EXPECTED_SYMBOL",
        ),
        (
            {
                "direction": "SIDEWAYS",
            },
            "INVALID_EXPECTED_DIRECTION",
        ),
        (
            {
                "volume": 0.0,
            },
            "INVALID_EXPECTED_VOLUME",
        ),
        (
            {
                "volume": math.nan,
            },
            "INVALID_EXPECTED_VOLUME",
        ),
    ],
)
def test_public_input_validation(
    kwargs: dict[
        str,
        Any,
    ],
    reason: str,
) -> None:
    result = normalize(
        **kwargs
    )

    assert result.reason == reason

    assert result.history_invoked is False


def test_policy_validation() -> None:
    with pytest.raises(
        ValueError
    ):
        Adapter(
            policy=Policy(
                volume_tolerance=0.0
            )
        )

    with pytest.raises(
        ValueError
    ):
        Adapter(
            policy=Policy(
                numeric_tolerance=math.inf
            )
        )


def test_read_order_fill_only_reads_deal_history() -> None:
    api = FakeMT5(
        deals=(
            deal(),
        )
    )

    result = Adapter(
        mt5_api=api
    ).read_order_fill(
        order_ticket=9001,
        expected_symbol="XAUUSDm",
        expected_direction="LONG",
        expected_volume=0.01,
    )

    assert result.valid

    assert result.history_invoked is True

    assert api.calls == [
        (
            "history_deals_get",
            9001,
        )
    ]


def test_read_order_fill_uses_exact_order_ticket() -> None:
    api = FakeMT5(
        deals=(
            deal(
                order=12345
            ),
        )
    )

    result = Adapter(
        mt5_api=api
    ).read_order_fill(
        order_ticket=12345,
        expected_symbol="XAUUSDm",
        expected_direction="LONG",
        expected_volume=0.01,
    )

    assert result.valid

    assert api.calls[
        0
    ] == (
        "history_deals_get",
        12345,
    )


def test_history_exception_fails_closed() -> None:
    api = FakeMT5(
        exception=RuntimeError(
            "boom"
        )
    )

    result = Adapter(
        mt5_api=api
    ).read_order_fill(
        order_ticket=9001,
        expected_symbol="XAUUSDm",
        expected_direction="LONG",
        expected_volume=0.01,
    )

    assert result.reason == (
        "MT5_DEAL_HISTORY_READ_EXCEPTION"
    )

    assert result.history_invoked is True

    assert "boom" in result.mt5_error


def test_history_none_fails_closed_with_last_error() -> None:
    api = FakeMT5(
        deals=None,
        last_error=(
            -1,
            "unavailable",
        ),
    )

    result = Adapter(
        mt5_api=api
    ).read_order_fill(
        order_ticket=9001,
        expected_symbol="XAUUSDm",
        expected_direction="LONG",
        expected_volume=0.01,
    )

    assert result.reason == (
        "MT5_DEAL_HISTORY_READ_FAILED"
    )

    assert (
        "unavailable"
        in
        result.mt5_error
    )

    assert api.calls == [
        (
            "history_deals_get",
            9001,
        ),
        (
            "last_error",
            None,
        ),
    ]


def test_history_result_must_be_iterable() -> None:
    api = FakeMT5(
        deals=123
    )

    result = Adapter(
        mt5_api=api
    ).read_order_fill(
        order_ticket=9001,
        expected_symbol="XAUUSDm",
        expected_direction="LONG",
        expected_volume=0.01,
    )

    assert result.reason == (
        "INVALID_MT5_DEAL_HISTORY_RESULT"
    )


def test_result_completed_fill_has_no_quote_fields() -> None:
    result = normalize()

    completed = result.completed_fill

    assert not hasattr(
        completed,
        "quote_bid",
    )

    assert not hasattr(
        completed,
        "quote_ask",
    )


def test_forward_capture_end_to_end_uses_submission_quote_not_tick_history() -> None:
    forward = importlib.import_module(
        "02_AI.Shadow.forward_execution_evidence_capture"
    )

    capture = (
        forward.ForwardExecutionEvidenceCapture()
    )

    first = capture.capture_submission(
        state=capture.initial_state(),
        request_id="req-forward",
        symbol="XAUUSDm",
        direction="LONG",
        requested_volume=0.01,
        quote_bid=4316.500,
        quote_ask=4316.760,
        quote_time_msc=1_800_000_000_000,
        captured_at_msc=1_800_000_000_010,
        submitted_at_msc=1_800_000_000_020,
    )

    second = capture.bind_order(
        state=first.state_after,
        request_id="req-forward",
        order_ticket=9001,
    )

    completed = normalize(
        raw_deals=(
            deal(
                price=4316.800
            ),
        )
    )

    assert completed.valid

    final = capture.reconcile_completed_fill(
        state=second.state_after,
        completed_fill=(
            completed.completed_fill
        ),
    )

    assert final.valid

    assert final.telemetry.quote_bid == pytest.approx(
        4316.500
    )

    assert final.telemetry.quote_ask == pytest.approx(
        4316.760
    )

    assert final.telemetry.fill_price == pytest.approx(
        4316.800
    )

    assert (
        final.signed_slippage_price
        ==
        pytest.approx(
            0.040
        )
    )


def test_module_has_no_tick_or_trade_write_authority() -> None:
    with open(
        module.__file__,
        "r",
        encoding="utf-8",
    ) as handle:
        text = handle.read()

    assert "copy_ticks_range(" not in text
    assert "order_send(" not in text
    assert "TRADE_ACTION_" not in text

    assert "trade_ready =" not in text

    assert "live_authorized=True" not in text