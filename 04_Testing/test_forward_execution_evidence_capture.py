"""Offline tests for forward execution evidence capture."""

from __future__ import annotations

import importlib

from dataclasses import replace
from types import SimpleNamespace
from typing import Any

import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Shadow.forward_execution_evidence_capture"
)

Capture: Any = (
    module.ForwardExecutionEvidenceCapture
)

Policy: Any = (
    module.ForwardExecutionEvidencePolicy
)

CompletedFill: Any = (
    module.CompletedExecutionFill
)

State: Any = (
    module.ForwardExecutionEvidenceState
)


def captured(
    *,
    capture: Any | None = None,
    state: Any | None = None,
    request_id: str = "req-1",
    symbol: str = "XAUUSDm",
    direction: str = "LONG",
    volume: float = 0.01,
    bid: float = 4316.500,
    ask: float = 4316.760,
    quote_time_msc: int = 1_800_000_000_000,
    captured_at_msc: int = 1_800_000_000_010,
    submitted_at_msc: int = 1_800_000_000_030,
    request_price: float | None = 4316.760,
    deviation: int | None = 20,
    live_authorized: bool = False,
) -> Any:
    engine = (
        capture
        if capture is not None
        else Capture()
    )

    before = (
        state
        if state is not None
        else engine.initial_state()
    )

    return engine.capture_submission(
        state=before,
        request_id=request_id,
        symbol=symbol,
        direction=direction,
        requested_volume=volume,
        quote_bid=bid,
        quote_ask=ask,
        quote_time_msc=quote_time_msc,
        captured_at_msc=captured_at_msc,
        submitted_at_msc=submitted_at_msc,
        request_price=request_price,
        requested_deviation_points=deviation,
        live_authorized=live_authorized,
    )


def bound(
    *,
    capture: Any | None = None,
    request_id: str = "req-1",
    order_ticket: int = 9001,
    direction: str = "LONG",
) -> tuple[
    Any,
    Any,
]:
    engine = (
        capture
        if capture is not None
        else Capture()
    )

    first = captured(
        capture=engine,
        request_id=request_id,
        direction=direction,
    )

    assert first.valid

    second = engine.bind_order(
        state=first.state_after,
        request_id=request_id,
        order_ticket=order_ticket,
    )

    assert second.valid

    return (
        engine,
        second,
    )


def fill(
    *,
    order_ticket: int = 9001,
    execution_id: str = "MT5_ORDER_9001",
    symbol: str = "XAUUSDm",
    direction: str = "LONG",
    volume: float = 0.01,
    fill_price: float = 4316.800,
    commission: float = 0.0,
    live_authorized: bool = False,
) -> Any:
    return CompletedFill(
        order_ticket=order_ticket,
        execution_id=execution_id,
        symbol=symbol,
        direction=direction,
        filled_volume=volume,
        fill_price=fill_price,
        commission_cost=commission,
        live_authorized=live_authorized,
    )


def test_identity_and_initial_state() -> None:
    engine = Capture()

    state = engine.initial_state()

    assert engine.VERSION == "1.0"

    assert engine.MODE == (
        "SHADOW_FORWARD_EXECUTION_EVIDENCE_CAPTURE_ONLY"
    )

    assert state.records == ()


def test_policy_validation() -> None:
    with pytest.raises(
        ValueError
    ):
        Capture(
            policy=Policy(
                volume_tolerance=0.0
            )
        )

    with pytest.raises(
        ValueError
    ):
        Capture(
            policy=Policy(
                numeric_tolerance=float(
                    "nan"
                )
            )
        )

    with pytest.raises(
        ValueError
    ):
        Capture(
            policy=Policy(
                max_capture_to_submission_ms=-1
            )
        )


def test_capture_long_submission_preserves_exact_quote() -> None:
    result = captured()

    assert result.valid is True
    assert result.applied is True

    assert result.reason == (
        "OK_FORWARD_EXECUTION_SUBMISSION_CAPTURED"
    )

    assert result.live_authorized is False

    assert (
        result.quote_side_price
        ==
        pytest.approx(
            4316.760
        )
    )

    assert result.submission_latency_ms == 20

    assert len(
        result.state_after.records
    ) == 1

    record = result.record

    assert record.status == "CAPTURED"

    assert record.quote_bid == pytest.approx(
        4316.500
    )

    assert record.quote_ask == pytest.approx(
        4316.760
    )

    assert record.request_price == pytest.approx(
        4316.760
    )

    assert record.requested_deviation_points == 20

    assert record.live_authorized is False


@pytest.mark.parametrize(
    (
        "direction",
        "expected",
        "side",
    ),
    [
        (
            "LONG",
            "LONG",
            4316.760,
        ),
        (
            "buy",
            "LONG",
            4316.760,
        ),
        (
            "bullish",
            "LONG",
            4316.760,
        ),
        (
            "SHORT",
            "SHORT",
            4316.500,
        ),
        (
            "sell",
            "SHORT",
            4316.500,
        ),
        (
            "bearish",
            "SHORT",
            4316.500,
        ),
    ],
)
def test_direction_aliases(
    direction: str,
    expected: str,
    side: float,
) -> None:
    result = captured(
        direction=direction
    )

    assert result.valid

    assert (
        result.record.direction
        ==
        expected
    )

    assert (
        result.quote_side_price
        ==
        pytest.approx(
            side
        )
    )


def test_tiny_quote_inversion_is_normalized() -> None:
    engine = Capture(
        policy=Policy(
            numeric_tolerance=1e-6
        )
    )

    result = captured(
        capture=engine,
        bid=4316.5000005,
        ask=4316.5000000,
    )

    assert result.valid

    assert (
        result.record.quote_ask
        ==
        pytest.approx(
            result.record.quote_bid
        )
    )


@pytest.mark.parametrize(
    (
        "kwargs",
        "reason",
    ),
    [
        (
            {
                "request_id": "",
            },
            "INVALID_REQUEST_ID",
        ),
        (
            {
                "symbol": "",
            },
            "INVALID_SYMBOL",
        ),
        (
            {
                "direction": "SIDEWAYS",
            },
            "INVALID_DIRECTION",
        ),
        (
            {
                "volume": 0.0,
            },
            "INVALID_REQUESTED_VOLUME",
        ),
        (
            {
                "volume": float(
                    "nan"
                ),
            },
            "INVALID_REQUESTED_VOLUME",
        ),
        (
            {
                "bid": 0.0,
            },
            "INVALID_SUBMISSION_QUOTE",
        ),
        (
            {
                "ask": float(
                    "inf"
                ),
            },
            "INVALID_SUBMISSION_QUOTE",
        ),
        (
            {
                "bid": 4316.8,
                "ask": 4316.7,
            },
            "SUBMISSION_QUOTE_INVERTED",
        ),
        (
            {
                "quote_time_msc": 0,
            },
            "INVALID_SUBMISSION_TIMESTAMPS",
        ),
        (
            {
                "captured_at_msc": 0,
            },
            "INVALID_SUBMISSION_TIMESTAMPS",
        ),
        (
            {
                "submitted_at_msc": 0,
            },
            "INVALID_SUBMISSION_TIMESTAMPS",
        ),
        (
            {
                "captured_at_msc": (
                    1_800_000_000_100
                ),
                "submitted_at_msc": (
                    1_800_000_000_099
                ),
            },
            "SUBMISSION_TIME_PRECEDES_CAPTURE",
        ),
        (
            {
                "request_price": 0.0,
            },
            "INVALID_REQUEST_PRICE",
        ),
        (
            {
                "deviation": -1,
            },
            "INVALID_REQUESTED_DEVIATION",
        ),
        (
            {
                "live_authorized": True,
            },
            "LIVE_AUTHORIZATION_NOT_ALLOWED",
        ),
    ],
)
def test_capture_fail_closed(
    kwargs: dict[
        str,
        Any,
    ],
    reason: str,
) -> None:
    engine = Capture()

    before = engine.initial_state()

    result = captured(
        capture=engine,
        state=before,
        **kwargs,
    )

    assert result.valid is False
    assert result.applied is False

    assert result.reason == reason

    assert (
        result.state_after
        is
        before
    )


def test_capture_delay_limit() -> None:
    engine = Capture(
        policy=Policy(
            max_capture_to_submission_ms=10
        )
    )

    result = captured(
        capture=engine,
        captured_at_msc=1_800_000_000_000,
        submitted_at_msc=1_800_000_000_011,
    )

    assert result.reason == (
        "CAPTURE_TO_SUBMISSION_DELAY_EXCEEDED"
    )


def test_duplicate_request_id_rejected_without_mutation() -> None:
    engine = Capture()

    first = captured(
        capture=engine
    )

    result = captured(
        capture=engine,
        state=first.state_after,
    )

    assert result.reason == (
        "DUPLICATE_REQUEST_ID"
    )

    assert (
        result.state_after
        is
        first.state_after
    )


def test_bind_order_success() -> None:
    engine, result = bound()

    assert result.reason == (
        "OK_FORWARD_EXECUTION_ORDER_BOUND"
    )

    assert result.order_ticket == 9001

    assert result.record.status == "BOUND"

    assert result.record.order_ticket == 9001

    assert (
        result.state_after
        .records[
            0
        ]
        .order_ticket
        ==
        9001
    )


@pytest.mark.parametrize(
    (
        "request_id",
        "order_ticket",
        "reason",
    ),
    [
        (
            "",
            9001,
            "INVALID_REQUEST_ID",
        ),
        (
            "req-1",
            0,
            "INVALID_ORDER_TICKET",
        ),
        (
            "missing",
            9001,
            "REQUEST_EVIDENCE_NOT_FOUND",
        ),
    ],
)
def test_bind_fail_closed(
    request_id: str,
    order_ticket: int,
    reason: str,
) -> None:
    engine = Capture()

    first = captured(
        capture=engine
    )

    before = first.state_after

    result = engine.bind_order(
        state=before,
        request_id=request_id,
        order_ticket=order_ticket,
    )

    assert result.valid is False

    assert result.reason == reason

    assert (
        result.state_after
        is
        before
    )


def test_bind_live_authorization_rejected() -> None:
    engine = Capture()

    first = captured(
        capture=engine
    )

    result = engine.bind_order(
        state=first.state_after,
        request_id="req-1",
        order_ticket=9001,
        live_authorized=True,
    )

    assert result.reason == (
        "LIVE_AUTHORIZATION_NOT_ALLOWED"
    )


def test_request_cannot_bind_twice() -> None:
    engine, first_bind = bound()

    result = engine.bind_order(
        state=first_bind.state_after,
        request_id="req-1",
        order_ticket=9002,
    )

    assert result.reason == (
        "REQUEST_ALREADY_BOUND_OR_FINALIZED"
    )


def test_order_ticket_cannot_bind_to_two_requests() -> None:
    engine = Capture()

    first = captured(
        capture=engine,
        request_id="req-1",
    )

    second = captured(
        capture=engine,
        state=first.state_after,
        request_id="req-2",
    )

    first_bind = engine.bind_order(
        state=second.state_after,
        request_id="req-1",
        order_ticket=9001,
    )

    result = engine.bind_order(
        state=first_bind.state_after,
        request_id="req-2",
        order_ticket=9001,
    )

    assert result.reason == (
        "DUPLICATE_ORDER_TICKET_BINDING"
    )


def test_reconcile_long_uses_pre_submit_ask() -> None:
    engine, bind = bound()

    result = engine.reconcile_completed_fill(
        state=bind.state_after,
        completed_fill=fill(
            fill_price=4316.800
        ),
    )

    assert result.valid

    assert result.reason == (
        "OK_FORWARD_EXECUTION_EVIDENCE_RECONCILED"
    )

    assert (
        result.signed_slippage_price
        ==
        pytest.approx(
            0.040
        )
    )

    assert result.telemetry.quote_bid == pytest.approx(
        4316.500
    )

    assert result.telemetry.quote_ask == pytest.approx(
        4316.760
    )

    assert result.telemetry.fill_price == pytest.approx(
        4316.800
    )

    assert result.telemetry.live_authorized is False

    assert result.record.status == "FINALIZED"


def test_reconcile_short_uses_pre_submit_bid_and_keeps_favorable_sign() -> None:
    engine, bind = bound(
        direction="SHORT"
    )

    result = engine.reconcile_completed_fill(
        state=bind.state_after,
        completed_fill=fill(
            direction="SHORT",
            fill_price=4316.550,
        ),
    )

    # SHORT:
    # quote_bid - fill
    # 4316.500 - 4316.550 = -0.050
    assert (
        result.signed_slippage_price
        ==
        pytest.approx(
            -0.050
        )
    )


def test_reconcile_preserves_commission() -> None:
    engine, bind = bound()

    result = engine.reconcile_completed_fill(
        state=bind.state_after,
        completed_fill=fill(
            commission=0.07
        ),
    )

    assert (
        result.telemetry.commission_cost
        ==
        pytest.approx(
            0.07
        )
    )


def test_output_is_existing_normalized_fill_contract() -> None:
    engine, bind = bound()

    result = engine.reconcile_completed_fill(
        state=bind.state_after,
        completed_fill=fill(),
    )

    telemetry_cls = importlib.import_module(
        "02_AI.Shadow.realized_fill_telemetry_bridge"
    ).NormalizedActualFillTelemetry

    assert isinstance(
        result.telemetry,
        telemetry_cls,
    )

    assert result.telemetry.execution_id == (
        "MT5_ORDER_9001"
    )

    assert (
        result.telemetry.filled_volume
        ==
        pytest.approx(
            0.01
        )
    )


@pytest.mark.parametrize(
    (
        "completed",
        "reason",
    ),
    [
        (
            SimpleNamespace(),
            "INVALID_COMPLETED_FILL_SHAPE",
        ),
        (
            fill(
                live_authorized=True
            ),
            (
                "COMPLETED_FILL_LIVE_AUTHORIZATION_NOT_ALLOWED"
            ),
        ),
        (
            replace(
                fill(),
                order_ticket=0,
            ),
            "INVALID_COMPLETED_FILL_ORDER_TICKET",
        ),
        (
            replace(
                fill(),
                execution_id="",
            ),
            "INVALID_COMPLETED_FILL_EXECUTION_ID",
        ),
        (
            replace(
                fill(),
                symbol="EURUSD",
            ),
            "COMPLETED_FILL_SYMBOL_MISMATCH",
        ),
        (
            replace(
                fill(),
                direction="SHORT",
            ),
            "COMPLETED_FILL_DIRECTION_MISMATCH",
        ),
        (
            replace(
                fill(),
                filled_volume=0.02,
            ),
            "COMPLETED_FILL_VOLUME_MISMATCH",
        ),
        (
            replace(
                fill(),
                fill_price=0.0,
            ),
            "INVALID_COMPLETED_FILL_PRICE",
        ),
        (
            replace(
                fill(),
                commission_cost=-0.01,
            ),
            "INVALID_COMPLETED_FILL_COMMISSION",
        ),
    ],
)
def test_reconcile_fail_closed(
    completed: Any,
    reason: str,
) -> None:
    engine, bind = bound()

    before = bind.state_after

    result = engine.reconcile_completed_fill(
        state=before,
        completed_fill=completed,
    )

    assert result.valid is False
    assert result.applied is False

    assert result.reason == reason

    assert (
        result.state_after
        is
        before
    )

    assert result.telemetry is None


def test_unknown_order_rejected() -> None:
    engine, bind = bound()

    result = engine.reconcile_completed_fill(
        state=bind.state_after,
        completed_fill=fill(
            order_ticket=9999
        ),
    )

    assert result.reason == (
        "ORDER_EVIDENCE_NOT_FOUND"
    )


def test_finalize_is_exactly_once() -> None:
    engine, bind = bound()

    first = engine.reconcile_completed_fill(
        state=bind.state_after,
        completed_fill=fill(),
    )

    second = engine.reconcile_completed_fill(
        state=first.state_after,
        completed_fill=fill(),
    )

    assert first.valid

    assert second.reason == (
        "ORDER_EVIDENCE_ALREADY_FINALIZED"
    )

    assert (
        second.state_after
        is
        first.state_after
    )


def test_duplicate_execution_id_across_orders_rejected() -> None:
    engine = Capture()

    first = captured(
        capture=engine,
        request_id="req-1",
    )

    second = captured(
        capture=engine,
        state=first.state_after,
        request_id="req-2",
        direction="SHORT",
    )

    bind1 = engine.bind_order(
        state=second.state_after,
        request_id="req-1",
        order_ticket=9001,
    )

    bind2 = engine.bind_order(
        state=bind1.state_after,
        request_id="req-2",
        order_ticket=9002,
    )

    final1 = engine.reconcile_completed_fill(
        state=bind2.state_after,
        completed_fill=fill(
            order_ticket=9001,
            execution_id="same-exec",
        ),
    )

    result = engine.reconcile_completed_fill(
        state=final1.state_after,
        completed_fill=fill(
            order_ticket=9002,
            execution_id="same-exec",
            direction="SHORT",
        ),
    )

    assert result.reason == (
        "DUPLICATE_COMPLETED_EXECUTION_ID"
    )


def test_invalid_state_fails_closed() -> None:
    engine = Capture()

    result = captured(
        capture=engine,
        state=object(),
    )

    assert result.reason == (
        "INVALID_EVIDENCE_STATE_SHAPE"
    )


def test_unbound_record_cannot_reconcile() -> None:
    engine = Capture()

    first = captured(
        capture=engine
    )

    record = replace(
        first.record,
        order_ticket=9001,
        status="CAPTURED",
    )

    state = State(
        records=(
            record,
        )
    )

    result = engine.reconcile_completed_fill(
        state=state,
        completed_fill=fill(),
    )

    assert result.reason == (
        "ORDER_EVIDENCE_NOT_BOUND"
    )


def test_reconciled_telemetry_passes_existing_realized_fill_bridge() -> None:
    bridge_tests = importlib.import_module(
        "04_Testing.test_realized_fill_telemetry_bridge"
    )

    engine = Capture()

    first = engine.capture_submission(
        state=engine.initial_state(),
        request_id="req-bridge",
        symbol="XAUUSDm",
        direction="LONG",
        requested_volume=0.01,
        quote_bid=4316.500,
        quote_ask=4316.700,
        quote_time_msc=1_800_000_000_000,
        captured_at_msc=1_800_000_000_010,
        submitted_at_msc=1_800_000_000_020,
    )

    second = engine.bind_order(
        state=first.state_after,
        request_id="req-bridge",
        order_ticket=9001,
    )

    final = engine.reconcile_completed_fill(
        state=second.state_after,
        completed_fill=fill(
            fill_price=4316.720,
            commission=0.04,
        ),
    )

    assert final.valid

    bridge = bridge_tests.Bridge()

    observation = bridge.observe_fill(
        cost_state=bridge.initial_cost_state(),
        lifecycle_transition=(
            bridge_tests.successful_transition()
        ),
        telemetry=final.telemetry,
    )

    assert observation.valid is True
    assert observation.observed is True

    assert observation.reason == (
        "OK_NORMALIZED_ACTUAL_FILL_OBSERVED"
    )

    assert (
        observation.realized_spread_cost
        ==
        pytest.approx(
            0.20
        )
    )

    assert (
        observation.realized_slippage_cost
        ==
        pytest.approx(
            0.02
        )
    )

    assert (
        observation.realized_commission_cost
        ==
        pytest.approx(
            0.04
        )
    )

    assert (
        observation.lifecycle_pnl_delta
        ==
        pytest.approx(
            0.0
        )
    )


def test_module_has_no_broker_or_bridge_side_effect_authority() -> None:
    source = module.__file__

    with open(
        source,
        "r",
        encoding="utf-8",
    ) as handle:
        text = handle.read()

    assert "order_send(" not in text
    assert "copy_ticks_range(" not in text
    assert "history_deals_get(" not in text

    assert ".observe_fill(" not in text

    assert "trade_ready =" not in text

    assert "live_authorized=True" not in text