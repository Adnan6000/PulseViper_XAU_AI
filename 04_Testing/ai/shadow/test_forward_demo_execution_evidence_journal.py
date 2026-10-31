"""Offline tests for the durable forward/demo execution evidence journal."""

from __future__ import annotations

import importlib
import json

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest


pytestmark = pytest.mark.offline

module: Any = importlib.import_module(
    "02_AI.Shadow.forward_demo_execution_evidence_journal"
)
forward_module: Any = importlib.import_module(
    "02_AI.Shadow.forward_execution_evidence_capture"
)

Journal: Any = module.ForwardDemoExecutionEvidenceJournal
Policy: Any = module.ForwardDemoEvidenceJournalPolicy
IntegrityError: Any = module.ForwardDemoEvidenceJournalIntegrityError
PersistenceError: Any = module.ForwardDemoEvidenceJournalPersistenceError
Capture: Any = forward_module.ForwardExecutionEvidenceCapture
CapturePolicy: Any = forward_module.ForwardExecutionEvidencePolicy

BASE = 1_800_000_000_000


@dataclass(frozen=True)
class Tick:
    bid: float = 4316.500
    ask: float = 4316.760
    time_msc: int = BASE


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


class FixedClock:
    def __init__(self, value: int = BASE + 100) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value


class FakeMT5:
    DEAL_TYPE_BUY = 0
    DEAL_TYPE_SELL = 1
    DEAL_ENTRY_IN = 0
    DEAL_ENTRY_OUT = 1

    def __init__(
        self,
        *,
        tick: Any = None,
        deals: Any = None,
        tick_exception: Exception | None = None,
        history_exception: Exception | None = None,
        last_error: Any = (0, "OK"),
    ) -> None:
        self.tick = Tick() if tick is None else tick
        self.deals = (
            (deal(),)
            if deals is None
            else deals
        )
        self.tick_exception = tick_exception
        self.history_exception = history_exception
        self.last_error_value = last_error
        self.calls: list[tuple[str, Any]] = []

    def symbol_info_tick(self, symbol: str) -> Any:
        self.calls.append(("symbol_info_tick", symbol))
        if self.tick_exception is not None:
            raise self.tick_exception
        return self.tick

    def history_deals_get(self, *, ticket: int) -> Any:
        self.calls.append(("history_deals_get", ticket))
        if self.history_exception is not None:
            raise self.history_exception
        return self.deals

    def last_error(self) -> Any:
        self.calls.append(("last_error", None))
        return self.last_error_value

    def order_send(self, *_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("order_send must never be called")

    def initialize(self, *_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("initialize ownership is out of scope")

    def shutdown(self, *_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("shutdown ownership is out of scope")

    def copy_ticks_range(self, *_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("historical quote reconstruction is forbidden")

    def copy_ticks_from(self, *_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("historical quote reconstruction is forbidden")


def deal(
    *,
    ticket: int = 1001,
    order: int = 9001,
    time_msc: int = BASE + 150,
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


def journal(
    tmp_path: Path,
    *,
    api: Any | None = None,
    clock: FixedClock | None = None,
    policy: Any | None = None,
    capture: Any | None = None,
) -> Any:
    return Journal(
        journal_path=tmp_path / "forward_demo.journal.jsonl",
        mt5_api=api if api is not None else FakeMT5(),
        clock_msc=clock if clock is not None else FixedClock(),
        policy=policy,
        evidence_capture=capture,
    )


def prepared(
    engine: Any,
    *,
    request_id: str = "req-1",
    direction: str = "LONG",
    volume: float = 0.01,
    request_price: float | None = 4316.760,
    deviation: int | None = 20,
    live_authorized: bool = False,
) -> Any:
    return engine.capture_pre_submit(
        request_id=request_id,
        symbol="XAUUSDm",
        direction=direction,
        requested_volume=volume,
        request_price=request_price,
        requested_deviation_points=deviation,
        live_authorized=live_authorized,
    )


def bound(
    engine: Any,
    prep: Any,
    *,
    request_id: str = "req-1",
    submitted_at_msc: int | None = None,
    order_ticket: int = 9001,
    live_authorized: bool = False,
) -> Any:
    submitted = (
        prep.handoff.captured_at_msc + 30
        if submitted_at_msc is None
        else submitted_at_msc
    )
    return engine.bind_external_order(
        request_id=request_id,
        handoff_event_hash=prep.handoff.journal_event_hash,
        submitted_at_msc=submitted,
        order_ticket=order_ticket,
        live_authorized=live_authorized,
    )


def read_events(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]


def test_identity_and_empty_state_do_not_create_runtime_files(
    tmp_path: Path,
) -> None:
    engine = journal(tmp_path)

    assert engine.VERSION == "1.0"
    assert engine.MODE == (
        "SHADOW_FORWARD_DEMO_EXECUTION_EVIDENCE_JOURNAL_ONLY"
    )
    assert engine.snapshot().total_request_count == 0
    assert engine.evidence_state.records == ()
    assert not engine.path.exists()
    assert not engine.anchor_path.exists()
    assert not engine.lock_path.exists()


def test_policy_validation_is_fail_closed(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError):
        journal(
            tmp_path,
            policy=Policy(max_quote_age_ms=-1),
        )

    with pytest.raises(ValueError):
        journal(
            tmp_path,
            policy=Policy(
                max_submission_future_skew_ms=-1
            ),
        )

    with pytest.raises(ValueError):
        journal(
            tmp_path,
            policy=Policy(numeric_tolerance=0.0),
        )


def test_capture_pre_submit_persists_exact_long_quote_and_handoff(
    tmp_path: Path,
) -> None:
    api = FakeMT5()
    engine = journal(
        tmp_path,
        api=api,
    )

    result = prepared(engine)

    assert result.valid and result.applied
    assert result.reason == (
        "OK_FORWARD_DEMO_PRE_SUBMIT_EVIDENCE_DURABLE"
    )
    assert result.action == (
        "HANDOFF_TO_EXTERNAL_DEMO_EXECUTION_OWNER"
    )
    assert result.stage == "PREPARED"
    assert result.live_authorized is False

    assert result.handoff.quote_bid == pytest.approx(
        4316.500
    )
    assert result.handoff.quote_ask == pytest.approx(
        4316.760
    )
    assert result.handoff.executable_quote_side == pytest.approx(
        4316.760
    )
    assert result.handoff.quote_age_ms == 100
    assert result.handoff.request_price == pytest.approx(
        4316.760
    )
    assert result.handoff.requested_deviation_points == 20
    assert result.handoff.max_capture_to_submission_ms == 1000
    assert result.handoff.live_authorized is False

    assert engine.path.exists()
    assert engine.anchor_path.exists()
    assert not engine.lock_path.exists()

    assert api.calls == [
        ("symbol_info_tick", "XAUUSDm")
    ]

    events = read_events(engine.path)

    assert len(events) == 1
    assert events[0]["event_type"] == "PREPARED"
    assert events[0]["payload"]["quote_bid"] == pytest.approx(
        4316.500
    )
    assert events[0]["payload"]["quote_ask"] == pytest.approx(
        4316.760
    )
    assert events[0]["payload"]["live_authorized"] is False


def test_short_handoff_uses_bid_as_executable_side(
    tmp_path: Path,
) -> None:
    engine = journal(tmp_path)

    result = prepared(
        engine,
        direction="SELL",
    )

    assert result.valid
    assert result.handoff.direction == "SHORT"
    assert result.handoff.executable_quote_side == pytest.approx(
        4316.500
    )


def test_capture_rejects_live_authorization_without_broker_call(
    tmp_path: Path,
) -> None:
    api = FakeMT5()
    engine = journal(
        tmp_path,
        api=api,
    )

    result = prepared(
        engine,
        live_authorized=True,
    )

    assert not result.valid
    assert result.reason == "LIVE_AUTHORIZATION_NOT_ALLOWED"
    assert api.calls == []
    assert not engine.path.exists()


def test_capture_rejects_stale_future_inverted_and_invalid_quote(
    tmp_path: Path,
) -> None:
    stale = journal(
        tmp_path / "stale",
        api=FakeMT5(
            tick=Tick(
                time_msc=BASE - 1000
            )
        ),
    )

    assert prepared(stale).reason == (
        "CURRENT_EXECUTABLE_QUOTE_STALE"
    )

    future = journal(
        tmp_path / "future",
        api=FakeMT5(
            tick=Tick(
                time_msc=BASE + 1000
            )
        ),
    )

    assert prepared(future).reason == (
        "CURRENT_EXECUTABLE_QUOTE_TIME_IN_FUTURE"
    )

    inverted = journal(
        tmp_path / "inverted",
        api=FakeMT5(
            tick=Tick(
                bid=4317.0,
                ask=4316.0,
            )
        ),
    )

    assert prepared(inverted).reason == (
        "CURRENT_EXECUTABLE_QUOTE_INVERTED"
    )

    invalid = journal(
        tmp_path / "invalid",
        api=FakeMT5(
            tick=Tick(
                bid=0.0
            )
        ),
    )

    assert prepared(invalid).reason == (
        "INVALID_CURRENT_EXECUTABLE_QUOTE"
    )


def test_capture_read_failures_are_diagnostic_and_non_mutating(
    tmp_path: Path,
) -> None:
    none_api = FakeMT5(
        tick=False,
        last_error=(1, "no tick"),
    )
    none_api.tick = None

    engine = journal(
        tmp_path / "none",
        api=none_api,
    )

    result = prepared(engine)

    assert not result.valid
    assert result.reason == "MT5_CURRENT_QUOTE_READ_FAILED"
    assert "no tick" in result.mt5_error
    assert not engine.path.exists()

    exc_engine = journal(
        tmp_path / "exc",
        api=FakeMT5(
            tick_exception=RuntimeError("boom")
        ),
    )

    exc = prepared(exc_engine)

    assert not exc.valid
    assert exc.reason == "MT5_CURRENT_QUOTE_READ_EXCEPTION"
    assert "boom" in exc.mt5_error


def test_duplicate_request_is_rejected_without_second_quote_read(
    tmp_path: Path,
) -> None:
    api = FakeMT5()
    engine = journal(
        tmp_path,
        api=api,
    )

    first = prepared(engine)
    before = engine.path.read_bytes()

    second = prepared(engine)

    assert first.valid
    assert not second.valid
    assert second.reason == "DUPLICATE_REQUEST_ID"
    assert engine.path.read_bytes() == before
    assert api.calls == [
        ("symbol_info_tick", "XAUUSDm")
    ]


def test_bind_external_order_creates_underlying_forward_state(
    tmp_path: Path,
) -> None:
    engine = journal(tmp_path)
    prep = prepared(engine)

    result = bound(
        engine,
        prep,
    )

    assert result.valid and result.applied
    assert result.reason == (
        "OK_EXTERNAL_DEMO_ORDER_BOUND_TO_DURABLE_EVIDENCE"
    )
    assert result.action == "WAIT_FOR_COMPLETED_FILL_READ_ONLY"
    assert result.order_ticket == 9001

    record = engine.evidence_state.records[0]

    assert record.request_id == "req-1"
    assert record.status == "BOUND"
    assert record.order_ticket == 9001
    assert record.quote_bid == pytest.approx(
        4316.500
    )
    assert record.quote_ask == pytest.approx(
        4316.760
    )
    assert record.submitted_at_msc == BASE + 130
    assert record.submission_latency_ms == 30

    events = read_events(engine.path)

    assert [
        event["event_type"]
        for event in events
    ] == [
        "PREPARED",
        "ORDER_BOUND",
    ]


def test_bind_requires_exact_prepared_hash(
    tmp_path: Path,
) -> None:
    engine = journal(tmp_path)
    prep = prepared(engine)

    before = engine.path.read_bytes()

    result = engine.bind_external_order(
        request_id="req-1",
        handoff_event_hash="f" * 64,
        submitted_at_msc=BASE + 130,
        order_ticket=9001,
    )

    assert not result.valid
    assert result.reason == "PREPARED_HANDOFF_HASH_MISMATCH"
    assert engine.path.read_bytes() == before
    assert engine.evidence_state.records == ()
    assert prep.handoff.journal_event_hash != "f" * 64


def test_bind_rejects_late_submission_using_existing_capture_policy(
    tmp_path: Path,
) -> None:
    clock = FixedClock(
        BASE + 1500
    )
    api = FakeMT5(
        tick=Tick(
            time_msc=BASE + 1400
        )
    )

    engine = journal(
        tmp_path,
        api=api,
        clock=clock,
    )

    prep = prepared(engine)

    clock.value = BASE + 2600

    result = bound(
        engine,
        prep,
        submitted_at_msc=BASE + 2501,
    )

    assert not result.valid
    assert result.reason.endswith(
        "CAPTURE_TO_SUBMISSION_DELAY_EXCEEDED"
    )
    assert engine.evidence_state.records == ()
    assert len(
        read_events(engine.path)
    ) == 1


def test_bind_rejects_future_submission_timestamp(
    tmp_path: Path,
) -> None:
    engine = journal(tmp_path)
    prep = prepared(engine)

    result = bound(
        engine,
        prep,
        submitted_at_msc=BASE + 1000,
    )

    assert not result.valid
    assert result.reason == (
        "EXTERNAL_SUBMISSION_TIMESTAMP_IN_FUTURE"
    )
    assert engine.evidence_state.records == ()


def test_duplicate_order_and_duplicate_bind_fail_closed(
    tmp_path: Path,
) -> None:
    engine = journal(tmp_path)

    first = prepared(
        engine,
        request_id="req-1",
    )

    assert bound(
        engine,
        first,
        request_id="req-1",
        order_ticket=9001,
    ).valid

    second = prepared(
        engine,
        request_id="req-2",
    )

    duplicate_order = bound(
        engine,
        second,
        request_id="req-2",
        order_ticket=9001,
    )

    assert not duplicate_order.valid
    assert duplicate_order.reason == (
        "DUPLICATE_EXTERNAL_ORDER_TICKET"
    )

    duplicate_request = bound(
        engine,
        first,
        request_id="req-1",
        order_ticket=9002,
    )

    assert not duplicate_request.valid
    assert duplicate_request.reason == (
        "REQUEST_ALREADY_BOUND_OR_FINALIZED"
    )


def test_completed_fill_long_produces_authoritative_forward_telemetry(
    tmp_path: Path,
) -> None:
    api = FakeMT5()
    clock = FixedClock(
        BASE + 200
    )

    engine = journal(
        tmp_path,
        api=api,
        clock=clock,
    )

    prep = prepared(engine)

    assert bound(
        engine,
        prep,
    ).valid

    result = engine.reconcile_completed_order(
        request_id="req-1"
    )

    assert result.valid and result.applied
    assert result.reason == (
        "OK_FORWARD_DEMO_AUTHORITATIVE_FILL_EVIDENCE_FINALIZED"
    )
    assert result.action == (
        "FORWARD_NORMALIZED_TELEMETRY_READY_FOR_EXISTING_BRIDGE"
    )
    assert result.execution_id == "MT5_ORDER_9001"

    assert result.telemetry.fill_price == pytest.approx(
        4316.800
    )
    assert result.telemetry.quote_bid == pytest.approx(
        4316.500
    )
    assert result.telemetry.quote_ask == pytest.approx(
        4316.760
    )
    assert result.telemetry.commission_cost == pytest.approx(
        0.0
    )
    assert result.telemetry.live_authorized is False

    assert result.forward_transition.signed_slippage_price == (
        pytest.approx(0.040)
    )

    assert engine.evidence_state.records[0].status == "FINALIZED"
    assert engine.telemetry_for("req-1") == result.telemetry

    assert (
        "history_deals_get",
        9001,
    ) in api.calls

    assert all(
        call[0]
        not in {
            "copy_ticks_range",
            "copy_ticks_from",
        }
        for call in api.calls
    )


def test_completed_fill_short_signed_slippage_uses_original_bid(
    tmp_path: Path,
) -> None:
    api = FakeMT5(
        deals=(
            deal(
                type=1,
                price=4316.450,
            ),
        )
    )

    engine = journal(
        tmp_path,
        api=api,
        clock=FixedClock(BASE + 200),
    )

    prep = prepared(
        engine,
        direction="SHORT",
    )

    assert bound(
        engine,
        prep,
    ).valid

    result = engine.reconcile_completed_order(
        request_id="req-1"
    )

    assert result.valid
    assert result.forward_transition.signed_slippage_price == (
        pytest.approx(0.050)
    )
    assert result.telemetry.quote_bid == pytest.approx(
        4316.500
    )


def test_partial_fills_and_commission_are_audit_persisted(
    tmp_path: Path,
) -> None:
    api = FakeMT5(
        deals=(
            deal(
                ticket=1001,
                volume=0.004,
                price=4316.790,
                commission=-0.05,
            ),
            deal(
                ticket=1002,
                volume=0.006,
                price=4316.810,
                commission=-0.07,
            ),
        )
    )

    engine = journal(
        tmp_path,
        api=api,
        clock=FixedClock(BASE + 200),
    )

    prep = prepared(engine)

    assert bound(
        engine,
        prep,
    ).valid

    result = engine.reconcile_completed_order(
        request_id="req-1"
    )

    assert result.valid
    assert result.telemetry.filled_volume == pytest.approx(
        0.01
    )
    assert result.telemetry.fill_price == pytest.approx(
        4316.802
    )
    assert result.telemetry.commission_cost == pytest.approx(
        0.12
    )

    final = read_events(
        engine.path
    )[-1]

    assert final["event_type"] == "FINALIZED"

    assert final["payload"]["fill_audit"][
        "deal_tickets"
    ] == [
        1001,
        1002,
    ]

    assert final["payload"]["fill_audit"][
        "selected_deal_count"
    ] == 2

    assert final["payload"]["fill_audit"][
        "history_invoked"
    ] is True

    assert final["payload"]["telemetry"][
        "commission_cost"
    ] == pytest.approx(
        0.12
    )


def test_execution_id_override_is_persisted_and_recovered(
    tmp_path: Path,
) -> None:
    api = FakeMT5()
    clock = FixedClock(
        BASE + 200
    )

    engine = journal(
        tmp_path,
        api=api,
        clock=clock,
    )

    prep = prepared(engine)

    assert bound(
        engine,
        prep,
    ).valid

    result = engine.reconcile_completed_order(
        request_id="req-1",
        execution_id="demo-session-42-order-9001",
    )

    assert result.valid
    assert result.execution_id == (
        "demo-session-42-order-9001"
    )

    recovered = journal(
        tmp_path,
        api=api,
        clock=clock,
    )

    assert recovered.telemetry_for(
        "req-1"
    ).execution_id == (
        "demo-session-42-order-9001"
    )

    assert recovered.evidence_state.records[
        0
    ].finalized_execution_id == (
        "demo-session-42-order-9001"
    )


def test_reconcile_requires_bound_request_before_history_read(
    tmp_path: Path,
) -> None:
    api = FakeMT5()

    engine = journal(
        tmp_path,
        api=api,
    )

    prepared(engine)

    calls_before = list(
        api.calls
    )

    result = engine.reconcile_completed_order(
        request_id="req-1"
    )

    assert not result.valid
    assert result.reason == "BOUND_EVIDENCE_NOT_FOUND"
    assert api.calls == calls_before


def test_completed_fill_adapter_failure_does_not_finalize_or_append(
    tmp_path: Path,
) -> None:
    api = FakeMT5(
        deals=()
    )

    engine = journal(
        tmp_path,
        api=api,
        clock=FixedClock(BASE + 200),
    )

    prep = prepared(engine)

    assert bound(
        engine,
        prep,
    ).valid

    before = engine.path.read_bytes()

    result = engine.reconcile_completed_order(
        request_id="req-1"
    )

    assert not result.valid
    assert result.reason.startswith(
        "COMPLETED_FILL_READ_REJECTED:"
    )
    assert engine.path.read_bytes() == before
    assert engine.evidence_state.records[0].status == "BOUND"


def test_completed_fill_cannot_precede_submission(
    tmp_path: Path,
) -> None:
    api = FakeMT5(
        deals=(
            deal(
                time_msc=BASE - 500
            ),
        )
    )

    engine = journal(
        tmp_path,
        api=api,
        clock=FixedClock(BASE + 200),
    )

    prep = prepared(engine)

    assert bound(
        engine,
        prep,
    ).valid

    result = engine.reconcile_completed_order(
        request_id="req-1"
    )

    assert not result.valid
    assert result.reason == (
        "COMPLETED_FILL_PRECEDES_SUBMISSION"
    )
    assert engine.evidence_state.records[0].status == "BOUND"


def test_completed_fill_far_future_timestamp_is_rejected(
    tmp_path: Path,
) -> None:
    api = FakeMT5(
        deals=(
            deal(
                time_msc=BASE + 1000
            ),
        )
    )

    engine = journal(
        tmp_path,
        api=api,
        clock=FixedClock(BASE + 200),
    )

    prep = prepared(engine)

    assert bound(
        engine,
        prep,
    ).valid

    result = engine.reconcile_completed_order(
        request_id="req-1"
    )

    assert not result.valid
    assert result.reason == (
        "COMPLETED_FILL_TIMESTAMP_IN_FUTURE"
    )


def test_reconcile_live_authorization_is_rejected_before_history_read(
    tmp_path: Path,
) -> None:
    api = FakeMT5()

    engine = journal(
        tmp_path,
        api=api,
    )

    prep = prepared(engine)

    assert bound(
        engine,
        prep,
    ).valid

    calls_before = list(
        api.calls
    )

    result = engine.reconcile_completed_order(
        request_id="req-1",
        live_authorized=True,
    )

    assert not result.valid
    assert result.reason == "LIVE_AUTHORIZATION_NOT_ALLOWED"
    assert api.calls == calls_before


def test_finalization_is_exactly_once(
    tmp_path: Path,
) -> None:
    api = FakeMT5()

    engine = journal(
        tmp_path,
        api=api,
        clock=FixedClock(BASE + 200),
    )

    prep = prepared(engine)

    assert bound(
        engine,
        prep,
    ).valid

    assert engine.reconcile_completed_order(
        request_id="req-1"
    ).valid

    history_calls = [
        call
        for call in api.calls
        if call[0] == "history_deals_get"
    ]

    duplicate = engine.reconcile_completed_order(
        request_id="req-1"
    )

    assert not duplicate.valid
    assert duplicate.reason == (
        "ORDER_EVIDENCE_ALREADY_FINALIZED"
    )

    assert [
        call
        for call in api.calls
        if call[0] == "history_deals_get"
    ] == history_calls


def test_restart_recovers_prepared_only_without_requerying_tick(
    tmp_path: Path,
) -> None:
    api = FakeMT5()

    engine = journal(
        tmp_path,
        api=api,
    )

    prep = prepared(engine)

    assert prep.valid

    calls_before = list(
        api.calls
    )

    recovered = journal(
        tmp_path,
        api=api,
    )

    assert recovered.snapshot().prepared_only_count == 1
    assert recovered.evidence_state.records == ()
    assert api.calls == calls_before

    rebound = bound(
        recovered,
        prep,
    )

    assert rebound.valid


def test_restart_recovers_bound_state_without_history_read(
    tmp_path: Path,
) -> None:
    api = FakeMT5()

    engine = journal(
        tmp_path,
        api=api,
    )

    prep = prepared(engine)

    assert bound(
        engine,
        prep,
    ).valid

    calls_before = list(
        api.calls
    )

    recovered = journal(
        tmp_path,
        api=api,
    )

    assert recovered.snapshot().bound_count == 1
    assert recovered.evidence_state.records[0].status == "BOUND"
    assert api.calls == calls_before


def test_restart_recovers_finalized_telemetry_without_broker_requery(
    tmp_path: Path,
) -> None:
    api = FakeMT5()
    clock = FixedClock(
        BASE + 200
    )

    engine = journal(
        tmp_path,
        api=api,
        clock=clock,
    )

    prep = prepared(engine)

    assert bound(
        engine,
        prep,
    ).valid

    first = engine.reconcile_completed_order(
        request_id="req-1"
    )

    assert first.valid

    calls_before = list(
        api.calls
    )

    recovered = journal(
        tmp_path,
        api=api,
        clock=clock,
    )

    assert recovered.snapshot().finalized_count == 1

    assert recovered.telemetry_for(
        "req-1"
    ).fill_price == pytest.approx(
        4316.800
    )

    assert api.calls == calls_before


def test_capture_policy_drift_fails_closed_on_recovery(
    tmp_path: Path,
) -> None:
    api = FakeMT5()

    engine = journal(
        tmp_path,
        api=api,
    )

    assert prepared(engine).valid

    changed_capture = Capture(
        policy=CapturePolicy(
            max_capture_to_submission_ms=999
        )
    )

    with pytest.raises(
        IntegrityError,
        match="policy drift",
    ):
        journal(
            tmp_path,
            api=api,
            capture=changed_capture,
        )


def test_hash_tampering_is_detected_on_restart(
    tmp_path: Path,
) -> None:
    engine = journal(tmp_path)

    assert prepared(engine).valid

    events = read_events(
        engine.path
    )

    events[0]["payload"]["quote_ask"] = 9999.0

    engine.path.write_text(
        json.dumps(
            events[0],
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        IntegrityError,
        match="event hash mismatch",
    ):
        journal(tmp_path)


def test_anchor_tampering_is_detected_on_restart(
    tmp_path: Path,
) -> None:
    engine = journal(tmp_path)

    assert prepared(engine).valid

    anchor = json.loads(
        engine.anchor_path.read_text(
            encoding="utf-8"
        )
    )

    anchor["event_hash"] = "f" * 64

    engine.anchor_path.write_text(
        json.dumps(anchor),
        encoding="utf-8",
    )

    with pytest.raises(
        IntegrityError,
        match="does not match",
    ):
        journal(tmp_path)


def test_journal_without_anchor_and_anchor_without_journal_fail_closed(
    tmp_path: Path,
) -> None:
    first = journal(
        tmp_path / "first"
    )

    assert prepared(first).valid

    first.anchor_path.unlink()

    with pytest.raises(
        IntegrityError,
        match="presence mismatch",
    ):
        journal(
            tmp_path / "first"
        )

    second = journal(
        tmp_path / "second"
    )

    assert prepared(second).valid

    second.path.unlink()

    with pytest.raises(
        IntegrityError,
        match="presence mismatch",
    ):
        journal(
            tmp_path / "second"
        )


def test_extra_unanchored_tail_is_treated_as_half_commit(
    tmp_path: Path,
) -> None:
    engine = journal(tmp_path)

    assert prepared(engine).valid

    original = engine.path.read_text(
        encoding="utf-8"
    )

    engine.path.write_text(
        original + original,
        encoding="utf-8",
    )

    with pytest.raises(
        IntegrityError
    ):
        journal(tmp_path)


def test_existing_writer_lock_fails_closed_at_construction(
    tmp_path: Path,
) -> None:
    path = (
        tmp_path
        / "forward_demo.journal.jsonl"
    )

    lock = path.with_suffix(
        path.suffix + ".lock"
    )

    lock.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    lock.write_text(
        "stale lock",
        encoding="utf-8",
    )

    with pytest.raises(
        PersistenceError,
        match="writer lock",
    ):
        Journal(
            journal_path=path,
            mt5_api=FakeMT5(),
            clock_msc=FixedClock(),
        )


def test_clock_rollback_blocks_new_append_without_mutating_existing_journal(
    tmp_path: Path,
) -> None:
    clock = FixedClock(
        BASE + 100
    )

    api = FakeMT5()

    engine = journal(
        tmp_path,
        api=api,
        clock=clock,
    )

    assert prepared(
        engine,
        request_id="req-1",
    ).valid

    before = engine.path.read_bytes()

    clock.value = BASE + 50

    with pytest.raises(
        PersistenceError,
        match="clock moved backward",
    ):
        prepared(
            engine,
            request_id="req-2",
        )

    assert engine.path.read_bytes() == before
    assert engine.snapshot().total_request_count == 1


def test_snapshot_counts_all_three_stages(
    tmp_path: Path,
) -> None:
    api = FakeMT5()

    clock = FixedClock(
        BASE + 200
    )

    engine = journal(
        tmp_path,
        api=api,
        clock=clock,
    )

    first = prepared(
        engine,
        request_id="prepared",
    )

    assert first.valid

    second = prepared(
        engine,
        request_id="bound",
    )

    assert bound(
        engine,
        second,
        request_id="bound",
        order_ticket=9002,
    ).valid

    api.deals = (
        deal(
            order=9003
        ),
    )

    third = prepared(
        engine,
        request_id="finalized",
    )

    assert bound(
        engine,
        third,
        request_id="finalized",
        order_ticket=9003,
    ).valid

    assert engine.reconcile_completed_order(
        request_id="finalized"
    ).valid

    snap = engine.snapshot()

    assert snap.total_request_count == 3
    assert snap.prepared_only_count == 1
    assert snap.bound_count == 1
    assert snap.finalized_count == 1
    assert snap.live_authorized is False


def test_only_expected_mt5_read_methods_are_exercised_end_to_end(
    tmp_path: Path,
) -> None:
    api = FakeMT5()

    engine = journal(
        tmp_path,
        api=api,
        clock=FixedClock(BASE + 200),
    )

    prep = prepared(engine)

    assert bound(
        engine,
        prep,
    ).valid

    assert engine.reconcile_completed_order(
        request_id="req-1"
    ).valid

    assert [
        name
        for name, _ in api.calls
    ] == [
        "symbol_info_tick",
        "history_deals_get",
    ]


def test_no_bridge_or_lifecycle_mutation_is_owned_by_journal_result(
    tmp_path: Path,
) -> None:
    api = FakeMT5()

    engine = journal(
        tmp_path,
        api=api,
        clock=FixedClock(BASE + 200),
    )

    prep = prepared(engine)

    assert bound(
        engine,
        prep,
    ).valid

    result = engine.reconcile_completed_order(
        request_id="req-1"
    )

    assert result.valid
    assert result.telemetry is not None
    assert not hasattr(
        result,
        "lifecycle_pnl_delta",
    )
    assert result.action == (
        "FORWARD_NORMALIZED_TELEMETRY_READY_FOR_EXISTING_BRIDGE"
    )