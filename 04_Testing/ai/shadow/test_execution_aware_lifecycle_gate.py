"""
Offline integration tests for ExecutionAwareLifecycleGate v1.0.
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace
from typing import Any

import pytest


pytestmark = pytest.mark.offline


basket_module: Any = importlib.import_module(
    "02_AI.Shadow.bootstrap_compounding_planner"
)

adapter_module: Any = importlib.import_module(
    "02_AI.Shadow.compounding_account_state_adapter"
)

trade_module: Any = importlib.import_module(
    "02_AI.Shadow.compounding_trade_state_machine"
)

pnl_module: Any = importlib.import_module(
    "02_AI.Shadow.compounding_pnl_ledger"
)

lifecycle_module: Any = importlib.import_module(
    "02_AI.Shadow.compounding_lifecycle_accounting"
)

admission_module: Any = importlib.import_module(
    "02_AI.Shadow.execution_aware_compounding_admission"
)

gate_module: Any = importlib.import_module(
    "02_AI.Shadow.execution_aware_lifecycle_gate"
)


Planner: Any = (
    basket_module.BootstrapCompoundingPlanner
)

PlannerPolicy: Any = (
    basket_module.BootstrapCompoundingPolicy
)

Leg: Any = (
    basket_module.BasketLegCandidate
)

Adapter: Any = (
    adapter_module.CompoundingAccountStateAdapter
)

Machine: Any = (
    trade_module.CompoundingTradeStateMachine
)

Ledger: Any = (
    pnl_module.CompoundingPnLLedger
)

Lifecycle: Any = (
    lifecycle_module.CompoundingLifecycleAccounting
)

Admission: Any = (
    admission_module.ExecutionAwareCompoundingAdmission
)

Gate: Any = (
    gate_module.ExecutionAwareLifecycleGate
)


def lifecycle() -> Any:

    planner = Planner(
        PlannerPolicy(
            compounding_enabled=True,
            allow_initial_multi_leg=False,
            max_simultaneous_legs=3,
            max_total_volume=0.03,
            bootstrap_balance_max=20.0,
            bootstrap_loss_budget_floor_usd=0.50,
            bootstrap_loss_budget_percent=16.67,
            bootstrap_loss_budget_ceiling_usd=2.00,
            bootstrap_margin_cap_percent=85.0,
            standard_basket_hard_loss_percent=2.0,
            standard_margin_cap_percent=35.0,
            max_total_spread_to_basket_loss_ratio=1.0,
            add_only_after_profit=True,
            minimum_profit_r_before_add=0.25,
            partial_booking_enabled=True,
            partial_booking_r=0.75,
            partial_booking_fraction=0.50,
            trail_enabled=True,
            trail_start_r=0.50,
            runner_r=1.25,
        )
    )

    adapter = Adapter(
        planner=planner
    )

    machine = Machine(
        planner=planner,
        adapter=adapter,
    )

    return Lifecycle(
        machine=machine,
        ledger=Ledger(),
    )


def gate() -> Any:

    return Gate(
        lifecycle=lifecycle()
    )


def leg(
    leg_id: str,
    *,
    direction: str = "LONG",
    loss: float = 0.50,
    margin: float = 2.19,
    spread: float = 0.26,
) -> Any:

    return Leg(
        leg_id=leg_id,
        direction=direction,
        volume=0.01,
        projected_stop_loss=loss,
        margin_required=margin,
        spread_cost=spread,
        structural_stop_distance=loss,
    )


def friction(
    *,
    direction: str = "LONG",
    volume: float = 0.01,
    spread_cost: float = 0.26,
    total_friction_cost: float = 0.33,
    valid: bool = True,
    execution_feasible: bool = True,
    live_authorized: bool = False,
) -> Any:

    return SimpleNamespace(
        valid=valid,
        execution_feasible=execution_feasible,
        live_authorized=live_authorized,
        direction=direction,
        volume=volume,
        spread_cost=spread_cost,
        total_friction_cost=total_friction_cost,
    )


def admission(
    candidate: Any | None,
    *,
    valid: bool = True,
    admitted: bool = True,
    live_authorized: bool = False,
    friction_assessment: Any | None = None,
) -> Any:

    resolved_friction = (
        friction()
        if friction_assessment is None
        else friction_assessment
    )

    return Admission(
        valid=valid,
        admitted=admitted,
        reason=(
            "OK_EXECUTION_AWARE_COMPOUNDING_ADMISSION"
            if valid and admitted
            else "EXECUTION_FRICTION_BLOCKED"
        ),
        mode=(
            "SHADOW_EXECUTION_AWARE_COMPOUNDING_ADMISSION_ONLY"
        ),
        version="1.0.1",
        live_authorized=live_authorized,
        leg_id=(
            ""
            if candidate is None
            else candidate.leg_id
        ),
        direction=(
            ""
            if candidate is None
            else candidate.direction
        ),
        risk_mode="STANDARD_COMPOUND",
        risk_reason="OK_STANDARD_RISK_PLAN",
        friction_reason="OK_EXECUTION_FEASIBLE",
        account_reason="OK_ACCOUNT_STATE_ADMISSION",
        risk_plan=None,
        friction_assessment=resolved_friction,
        candidate=candidate,
        account_plan=None,
    )


def test_gate_is_shadow_only() -> None:

    engine = gate()

    state = engine.lifecycle.initial_state(
        balance=10.0
    )

    result = engine.apply_start_admission(
        state=state,
        admission_result=admission(
            leg(
                "L1"
            )
        ),
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.valid is True

    assert result.live_authorized is False

    assert result.mode == (
        "SHADOW_EXECUTION_AWARE_LIFECYCLE_GATE_ONLY"
    )

    assert result.lifecycle_invoked is True


def test_rejected_start_admission_never_invokes_lifecycle() -> None:

    class ExplodingLifecycle:

        def start(
            self,
            **_: Any,
        ) -> Any:

            raise AssertionError(
                "rejected admission must not reach lifecycle"
            )

    engine = Gate(
        lifecycle=ExplodingLifecycle()
    )

    sentinel_state = object()

    result = engine.apply_start_admission(
        state=sentinel_state,
        admission_result=admission(
            None,
            valid=False,
            admitted=False,
        ),
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.valid is False

    assert result.reason == (
        "EXECUTION_ADMISSION_REJECTED"
    )

    assert result.lifecycle_invoked is False

    assert result.state_before is sentinel_state

    assert result.state_after is sentinel_state


def test_admitted_start_debits_only_raw_spread_once() -> None:

    engine = gate()

    state = engine.lifecycle.initial_state(
        balance=10.0
    )

    accepted = admission(
        leg(
            "L1",
            spread=0.26,
        ),
        friction_assessment=friction(
            spread_cost=0.26,
            total_friction_cost=0.33,
        ),
    )

    result = engine.apply_start_admission(
        state=state,
        admission_result=accepted,
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.valid is True

    pnl = (
        result.state_after.pnl_state
    )

    assert pnl.floating_profit == pytest.approx(
        -0.26
    )

    assert pnl.cumulative_spread_cost == pytest.approx(
        0.26
    )

    assert (
        accepted
        .friction_assessment
        .total_friction_cost
        ==
        pytest.approx(
            0.33
        )
    )


def test_total_friction_cannot_be_substituted_as_candidate_spread() -> None:

    engine = gate()

    state = engine.lifecycle.initial_state(
        balance=10.0
    )

    bad = admission(
        leg(
            "L1",
            spread=0.33,
        ),
        friction_assessment=friction(
            spread_cost=0.26,
            total_friction_cost=0.33,
        ),
    )

    result = engine.apply_start_admission(
        state=state,
        admission_result=bad,
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.valid is False

    assert result.reason == (
        "CANDIDATE_SPREAD_NOT_RAW_FRICTION_SPREAD"
    )

    assert result.lifecycle_invoked is False

    assert result.state_after == (
        state
    )


def test_admitted_addon_debits_only_new_raw_spread_once() -> None:

    engine = gate()

    state = engine.lifecycle.initial_state(
        balance=10.0
    )

    started = engine.apply_start_admission(
        state=state,
        admission_result=admission(
            leg(
                "L1"
            )
        ),
        volume_min=0.01,
        volume_step=0.01,
    )

    assert started.valid is True

    addon = admission(
        leg(
            "L2"
        ),
        friction_assessment=friction(
            spread_cost=0.26,
            total_friction_cost=0.33,
        ),
    )

    result = engine.apply_addon_admission(
        state=started.state_after,
        admission_result=addon,
        current_market_floating_profit=0.175,
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.valid is True

    assert result.action == (
        "ADD_COMPOUNDING_LEGS"
    )

    pnl = (
        result.state_after.pnl_state
    )

    assert pnl.active_volume == pytest.approx(
        0.02
    )

    assert pnl.floating_profit == pytest.approx(
        -0.085
    )

    assert pnl.cumulative_spread_cost == pytest.approx(
        0.52
    )


def test_rejected_addon_does_not_mark_or_mutate_lifecycle_state() -> None:

    engine = gate()

    state = engine.lifecycle.initial_state(
        balance=10.0
    )

    started = engine.apply_start_admission(
        state=state,
        admission_result=admission(
            leg(
                "L1"
            )
        ),
        volume_min=0.01,
        volume_step=0.01,
    )

    before = (
        started.state_after
    )

    rejected = admission(
        None,
        valid=False,
        admitted=False,
    )

    result = engine.apply_addon_admission(
        state=before,
        admission_result=rejected,
        current_market_floating_profit=0.175,
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.valid is False

    assert result.reason == (
        "EXECUTION_ADMISSION_REJECTED"
    )

    assert result.lifecycle_invoked is False

    assert result.state_after == (
        before
    )

    assert result.state_after.pnl_state.floating_profit == pytest.approx(
        -0.26
    )

    assert result.state_after.pnl_state.cumulative_spread_cost == pytest.approx(
        0.26
    )


def test_infeasible_friction_fails_closed_before_lifecycle() -> None:

    engine = gate()

    state = engine.lifecycle.initial_state(
        balance=10.0
    )

    result = engine.apply_start_admission(
        state=state,
        admission_result=admission(
            leg(
                "L1"
            ),
            friction_assessment=friction(
                execution_feasible=False
            ),
        ),
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.valid is False

    assert result.reason == (
        "EXECUTION_FRICTION_NOT_FEASIBLE"
    )

    assert result.lifecycle_invoked is False

    assert result.state_after == (
        state
    )


def test_direction_mismatch_fails_closed() -> None:

    engine = gate()

    state = engine.lifecycle.initial_state(
        balance=10.0
    )

    result = engine.apply_start_admission(
        state=state,
        admission_result=admission(
            leg(
                "L1",
                direction="LONG",
            ),
            friction_assessment=friction(
                direction="SHORT",
            ),
        ),
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.valid is False

    assert result.reason == (
        "ADMISSION_DIRECTION_MISMATCH"
    )

    assert result.lifecycle_invoked is False


def test_volume_mismatch_fails_closed() -> None:

    engine = gate()

    state = engine.lifecycle.initial_state(
        balance=10.0
    )

    result = engine.apply_start_admission(
        state=state,
        admission_result=admission(
            leg(
                "L1"
            ),
            friction_assessment=friction(
                volume=0.02,
            ),
        ),
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.valid is False

    assert result.reason == (
        "ADMISSION_VOLUME_MISMATCH"
    )

    assert result.lifecycle_invoked is False


def test_live_authorized_admission_is_refused() -> None:

    engine = gate()

    state = engine.lifecycle.initial_state(
        balance=10.0
    )

    result = engine.apply_start_admission(
        state=state,
        admission_result=admission(
            leg(
                "L1"
            ),
            live_authorized=True,
        ),
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.valid is False

    assert result.reason == (
        "LIVE_AUTHORIZATION_NOT_ALLOWED"
    )

    assert result.lifecycle_invoked is False

    assert result.live_authorized is False