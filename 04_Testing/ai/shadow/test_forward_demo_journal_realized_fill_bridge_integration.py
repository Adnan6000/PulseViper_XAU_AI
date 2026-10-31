"""
Cross-module offline integration tests:

ForwardDemoExecutionEvidenceJournal
    -> NormalizedActualFillTelemetry
    -> RealizedFillTelemetryBridge
    -> RealizedExecutionCostLifecycleObserver

No broker writes.
No live authorization.
No lifecycle P&L rebooking.
"""

from __future__ import annotations

import importlib

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest


pytestmark = pytest.mark.offline


journal_module: Any = importlib.import_module(
    "02_AI.Shadow.forward_demo_execution_evidence_journal"
)

bridge_module: Any = importlib.import_module(
    "02_AI.Shadow.realized_fill_telemetry_bridge"
)

friction_module: Any = importlib.import_module(
    "02_AI.Shadow.execution_friction_model"
)


Journal: Any = (
    journal_module.ForwardDemoExecutionEvidenceJournal
)

Bridge: Any = (
    bridge_module.RealizedFillTelemetryBridge
)

Telemetry: Any = (
    bridge_module.NormalizedActualFillTelemetry
)

FrictionModel: Any = (
    friction_module.ExecutionFrictionModel
)


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

    def __init__(
        self,
        value: int = BASE + 100,
    ) -> None:

        self.value = value

    def __call__(
        self,
    ) -> int:

        return self.value


class FakeMT5:

    DEAL_TYPE_BUY = 0
    DEAL_TYPE_SELL = 1

    DEAL_ENTRY_IN = 0
    DEAL_ENTRY_OUT = 1

    def __init__(
        self,
        *,
        deals: tuple[Any, ...],
    ) -> None:

        self.tick = Tick()
        self.deals = deals

        self.calls: list[
            tuple[
                str,
                Any,
            ]
        ] = []

    def symbol_info_tick(
        self,
        symbol: str,
    ) -> Any:

        self.calls.append(
            (
                "symbol_info_tick",
                symbol,
            )
        )

        return self.tick

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

        return (
            0,
            "OK",
        )

    # Explicit safety traps.

    def order_send(
        self,
        *_args: Any,
        **_kwargs: Any,
    ) -> Any:

        raise AssertionError(
            "integration observer must never call order_send"
        )

    def initialize(
        self,
        *_args: Any,
        **_kwargs: Any,
    ) -> Any:

        raise AssertionError(
            "integration observer must not own MT5 initialize"
        )

    def shutdown(
        self,
        *_args: Any,
        **_kwargs: Any,
    ) -> Any:

        raise AssertionError(
            "integration observer must not own MT5 shutdown"
        )

    def copy_ticks_range(
        self,
        *_args: Any,
        **_kwargs: Any,
    ) -> Any:

        raise AssertionError(
            "historical quote reconstruction is forbidden"
        )


def deal(
    *,
    direction: str = "LONG",
    order: int = 9001,
    ticket: int = 1001,
    time_msc: int = BASE + 150,
    volume: float = 0.01,
    price: float | None = None,
    commission: float = -0.04,
) -> Deal:

    normalized = direction.upper()

    if normalized == "LONG":

        deal_type = 0

        resolved_price = (
            4316.800
            if price is None
            else price
        )

    else:

        deal_type = 1

        resolved_price = (
            4316.450
            if price is None
            else price
        )

    return Deal(
        ticket=ticket,
        order=order,
        time_msc=time_msc,
        type=deal_type,
        entry=0,
        volume=volume,
        price=resolved_price,
        commission=commission,
        fee=0.0,
        symbol="XAUUSDm",
    )


def lifecycle_state(
    cumulative_spread_cost: float,
) -> Any:

    return SimpleNamespace(
        pnl_state=SimpleNamespace(
            cumulative_spread_cost=(
                cumulative_spread_cost
            )
        )
    )


def successful_lifecycle_transition(
    *,
    direction: str,
) -> Any:

    normalized = direction.upper()

    entry = (
        4316.760
        if normalized == "LONG"
        else
        4316.500
    )

    stop = (
        entry - 0.50
        if normalized == "LONG"
        else
        entry + 0.50
    )

    friction = FrictionModel().evaluate(
        direction=normalized,
        volume=0.01,
        balance=63.35,
        equity=63.35,
        hard_loss_budget=1.00,
        entry_price=entry,
        stop_loss=stop,
        point=0.001,
        spread_price=0.26,
        spread_cost=0.26,
        projected_stop_loss=0.50,
        estimated_slippage_price=0.02,
        estimated_slippage_cost=0.02,
        estimated_commission_cost=0.04,
    )

    assert friction.valid is True

    risk_plan = SimpleNamespace(
        valid=True,
        live_authorized=False,
        direction=normalized,
        selected_volume=0.01,
        entry_price=entry,
        stop_distance_price=0.50,
        stop_distance_points=500.0,
        estimated_stop_loss_amount=0.50,
        spread_price=0.26,
        spread_points=260.0,
        spread_cost=0.26,
    )

    candidate = SimpleNamespace(
        direction=normalized,
        volume=0.01,
        projected_stop_loss=0.50,
        spread_cost=0.26,
        structural_stop_distance=0.50,
    )

    admission = SimpleNamespace(
        valid=True,
        admitted=True,
        live_authorized=False,
        risk_plan=risk_plan,
        friction_assessment=friction,
        candidate=candidate,
    )

    protected = SimpleNamespace(
        live_authorized=False,
        admission_result=admission,
    )

    return SimpleNamespace(
        valid=True,
        exposure_applied=True,
        live_authorized=False,
        lifecycle_invoked=True,
        lifecycle_state_before=lifecycle_state(
            0.0
        ),
        lifecycle_state_after=lifecycle_state(
            0.26
        ),
        protected_admission_result=protected,
    )


def finalized_journal(
    tmp_path: Path,
    *,
    direction: str,
) -> tuple[
    Any,
    Any,
    Any,
    Any,
]:

    api = FakeMT5(
        deals=(
            deal(
                direction=direction
            ),
        )
    )

    clock = FixedClock()

    engine = Journal(
        journal_path=(
            tmp_path
            /
            "forward_demo_bridge.journal.jsonl"
        ),
        mt5_api=api,
        clock_msc=clock,
    )

    prepared = engine.capture_pre_submit(
        request_id="req-1",
        symbol="XAUUSDm",
        direction=direction,
        requested_volume=0.01,
        request_price=(
            4316.760
            if direction.upper() == "LONG"
            else
            4316.500
        ),
        requested_deviation_points=20,
    )

    assert prepared.valid is True
    assert prepared.applied is True

    bound = engine.bind_external_order(
        request_id="req-1",
        handoff_event_hash=(
            prepared
            .handoff
            .journal_event_hash
        ),
        submitted_at_msc=(
            prepared
            .handoff
            .captured_at_msc
            +
            30
        ),
        order_ticket=9001,
    )

    assert bound.valid is True
    assert bound.applied is True

    finalized = engine.reconcile_completed_order(
        request_id="req-1"
    )

    assert finalized.valid is True
    assert finalized.applied is True

    return (
        api,
        clock,
        engine,
        finalized,
    )


@pytest.mark.parametrize(
    (
        "direction",
        "expected_slippage",
        "expected_total",
    ),
    (
        (
            "LONG",
            0.04,
            0.34,
        ),
        (
            "SHORT",
            0.05,
            0.35,
        ),
    ),
)
def test_forward_journal_telemetry_is_accepted_by_existing_bridge(
    tmp_path: Path,
    direction: str,
    expected_slippage: float,
    expected_total: float,
) -> None:

    (
        _api,
        _clock,
        _journal,
        finalized,
    ) = finalized_journal(
        tmp_path,
        direction=direction,
    )

    # Exact public bridge telemetry contract.
    assert isinstance(
        finalized.telemetry,
        Telemetry,
    )

    assert (
        finalized.telemetry.live_authorized
        is False
    )

    bridge = Bridge()

    initial_cost_state = (
        bridge.initial_cost_state()
    )

    observed = bridge.observe_fill(
        cost_state=initial_cost_state,
        lifecycle_transition=(
            successful_lifecycle_transition(
                direction=direction
            )
        ),
        telemetry=finalized.telemetry,
    )

    assert observed.valid is True
    assert observed.observed is True

    assert observed.reason == (
        "OK_NORMALIZED_ACTUAL_FILL_OBSERVED"
    )

    assert observed.live_authorized is False

    # The current executable quote was:
    #
    # Bid = 4316.500
    # Ask = 4316.760
    #
    # therefore realized spread = 0.260.

    assert (
        observed.realized_spread_price
        ==
        pytest.approx(
            0.26
        )
    )

    assert (
        observed.realized_spread_cost
        ==
        pytest.approx(
            0.26
        )
    )

    assert (
        observed.realized_slippage_price
        ==
        pytest.approx(
            expected_slippage
        )
    )

    assert (
        observed.realized_slippage_cost
        ==
        pytest.approx(
            expected_slippage
        )
    )

    assert (
        observed.realized_commission_cost
        ==
        pytest.approx(
            0.04
        )
    )

    # Critical accounting boundary:
    # observation does NOT rebook lifecycle P&L.

    assert observed.lifecycle_pnl_delta == pytest.approx(
        0.0
    )

    assert (
        observed.observer_result
        .cost_transition
        .lifecycle_pnl_delta
        ==
        pytest.approx(
            0.0
        )
    )

    record = (
        observed
        .observer_result
        .cost_transition
        .record
    )

    assert (
        record.complete_realized_total_cost
        ==
        pytest.approx(
            expected_total
        )
    )

    assert (
        observed.cost_state_after
        .observation_count
        ==
        1
    )

    assert (
        observed.cost_state_after
        .complete_observation_count
        ==
        1
    )


def test_finalized_journal_telemetry_survives_restart_and_bridge_observation(
    tmp_path: Path,
) -> None:

    (
        api,
        clock,
        engine,
        finalized,
    ) = finalized_journal(
        tmp_path,
        direction="LONG",
    )

    broker_calls_before_restart = tuple(
        api.calls
    )

    recovered = Journal(
        journal_path=engine.path,
        mt5_api=api,
        clock_msc=clock,
    )

    # Replay must use persisted evidence only.
    assert tuple(
        api.calls
    ) == broker_calls_before_restart

    recovered_telemetry = (
        recovered.telemetry_for(
            "req-1"
        )
    )

    assert recovered_telemetry is not None

    assert isinstance(
        recovered_telemetry,
        Telemetry,
    )

    assert (
        recovered_telemetry
        ==
        finalized.telemetry
    )

    bridge = Bridge()

    observed = bridge.observe_fill(
        cost_state=bridge.initial_cost_state(),
        lifecycle_transition=(
            successful_lifecycle_transition(
                direction="LONG"
            )
        ),
        telemetry=recovered_telemetry,
    )

    assert observed.valid is True
    assert observed.observed is True

    assert observed.lifecycle_pnl_delta == pytest.approx(
        0.0
    )

    # Bridge observation itself must not touch MT5.
    assert tuple(
        api.calls
    ) == broker_calls_before_restart


def test_bridge_duplicate_execution_id_remains_fail_closed(
    tmp_path: Path,
) -> None:

    (
        _api,
        _clock,
        _journal,
        finalized,
    ) = finalized_journal(
        tmp_path,
        direction="LONG",
    )

    bridge = Bridge()

    transition = (
        successful_lifecycle_transition(
            direction="LONG"
        )
    )

    first = bridge.observe_fill(
        cost_state=bridge.initial_cost_state(),
        lifecycle_transition=transition,
        telemetry=finalized.telemetry,
    )

    assert first.valid is True
    assert first.observed is True

    second = bridge.observe_fill(
        cost_state=first.cost_state_after,
        lifecycle_transition=transition,
        telemetry=finalized.telemetry,
    )

    assert second.valid is False
    assert second.observed is False

    assert second.reason == (
        "REALIZED_COST_OBSERVER_REJECTED"
    )

    assert second.cost_reason == (
        "DUPLICATE_EXECUTION_ID"
    )

    assert (
        second.cost_state_after
        ==
        first.cost_state_after
    )

    assert second.lifecycle_pnl_delta == pytest.approx(
        0.0
    )


def test_cross_module_path_never_authorizes_live_execution(
    tmp_path: Path,
) -> None:

    (
        api,
        _clock,
        _journal,
        finalized,
    ) = finalized_journal(
        tmp_path,
        direction="LONG",
    )

    bridge = Bridge()

    observed = bridge.observe_fill(
        cost_state=bridge.initial_cost_state(),
        lifecycle_transition=(
            successful_lifecycle_transition(
                direction="LONG"
            )
        ),
        telemetry=finalized.telemetry,
    )

    assert finalized.live_authorized is False

    assert (
        finalized.telemetry.live_authorized
        is False
    )

    assert observed.live_authorized is False

    assert (
        observed.observer_result.live_authorized
        is False
    )

    assert [
        name
        for name, _value
        in api.calls
    ] == [
        "symbol_info_tick",
        "history_deals_get",
    ]