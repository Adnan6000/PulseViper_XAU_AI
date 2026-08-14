"""
Offline integration tests for ExecutionAwareCompoundingAdmissionEngine v1.0.
"""

from __future__ import annotations

import importlib
from typing import Any

import pytest


pytestmark = pytest.mark.offline


risk_module: Any = importlib.import_module(
    "02_AI.Shadow.broker_aware_risk_engine"
)

friction_module: Any = importlib.import_module(
    "02_AI.Shadow.execution_friction_model"
)

basket_module: Any = importlib.import_module(
    "02_AI.Shadow.bootstrap_compounding_planner"
)

adapter_module: Any = importlib.import_module(
    "02_AI.Shadow.compounding_account_state_adapter"
)

bridge_module: Any = importlib.import_module(
    "02_AI.Shadow.execution_aware_compounding_admission"
)


RiskEngine: Any = (
    risk_module.BrokerAwareRiskEngine
)

RiskPolicy: Any = (
    risk_module.BrokerRiskPolicy
)

FrictionModel: Any = (
    friction_module.ExecutionFrictionModel
)

FrictionPolicy: Any = (
    friction_module.ExecutionFrictionPolicy
)

Planner: Any = (
    basket_module.BootstrapCompoundingPlanner
)

PlannerPolicy: Any = (
    basket_module.BootstrapCompoundingPolicy
)

Adapter: Any = (
    adapter_module.CompoundingAccountStateAdapter
)

Bridge: Any = (
    bridge_module.ExecutionAwareCompoundingAdmissionEngine
)


BID = 4318.705

ASK = 4318.965

POINT = 0.001

TICK_SIZE = 0.001

VOLUME_MIN = 0.01

VOLUME_MAX = 200.0

VOLUME_STEP = 0.01

SPREAD = 0.260


def risk_engine() -> Any:

    return RiskEngine(
        RiskPolicy(
            target_risk_percent=0.75,
            hard_max_risk_percent=1.00,
            max_margin_percent_of_free=25.0,
            max_spread_cost_to_hard_risk_ratio=1.0,
            micro_enabled=True,
            micro_min_balance=3.0,
            micro_max_balance=20.0,
            micro_hard_max_risk_percent=12.0,
            micro_max_margin_percent_of_free=80.0,
            micro_max_spread_cost_to_stop_risk_ratio=1.0,
            micro_max_stop_to_spread_risk_ratio=4.0,
        )
    )


def loss_estimator(
    stop_distance: float,
):

    def estimate(
        volume: float,
    ) -> float:

        return (
            stop_distance
            *
            (
                volume
                /
                0.01
            )
        )

    return estimate


def margin_estimator(
    volume: float,
) -> float:

    return (
        2.16
        *
        (
            volume
            /
            0.01
        )
    )


def spread_estimator(
    volume: float,
) -> float:

    return (
        SPREAD
        *
        (
            volume
            /
            0.01
        )
    )


def risk_plan(
    *,
    balance: float = 100.0,
    stop_distance: float = 0.50,
    direction: str = "LONG",
    equity: float | None = None,
    free_margin: float | None = None,
) -> Any:

    resolved_equity = (
        balance
        if equity is None
        else equity
    )

    resolved_free_margin = (
        resolved_equity
        if free_margin is None
        else free_margin
    )

    if direction == "LONG":

        stop_loss = (
            ASK
            -
            stop_distance
        )

    else:

        stop_loss = (
            BID
            +
            stop_distance
        )

    return risk_engine().plan(
        direction=direction,
        account_balance=balance,
        account_equity=resolved_equity,
        free_margin=resolved_free_margin,
        bid=BID,
        ask=ASK,
        stop_loss=stop_loss,
        point=POINT,
        tick_size=TICK_SIZE,
        volume_min=VOLUME_MIN,
        volume_max=VOLUME_MAX,
        volume_step=VOLUME_STEP,
        stops_level_points=0.0,
        loss_estimator=loss_estimator(
            stop_distance
        ),
        margin_estimator=margin_estimator,
        spread_cost_estimator=spread_estimator,
    )


def planner() -> Any:

    return Planner(
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


def bridge(
    *,
    adapter: Any | None = None,
) -> Any:

    resolved_adapter = (
        adapter
        if adapter is not None
        else Adapter(
            planner=planner()
        )
    )

    return Bridge(
        friction_model=FrictionModel(
            FrictionPolicy()
        ),
        adapter=resolved_adapter,
    )


def test_bridge_is_shadow_only() -> None:

    result = bridge().admit(
        risk_plan=risk_plan(),
        leg_id="L1",
        account_margin_used=0.0,
    )

    assert result.valid is True

    assert result.admitted is True

    assert result.live_authorized is False

    assert result.mode == (
        "SHADOW_EXECUTION_AWARE_COMPOUNDING_ADMISSION_ONLY"
    )


def test_valid_risk_plan_maps_into_exact_basket_candidate() -> None:

    upstream = risk_plan()

    result = bridge().admit(
        risk_plan=upstream,
        leg_id="L1",
        account_margin_used=0.0,
        estimated_slippage_price=0.02,
        estimated_slippage_cost=0.02,
    )

    assert result.valid is True

    assert result.candidate.leg_id == (
        "L1"
    )

    assert result.candidate.direction == (
        upstream.direction
    )

    assert result.candidate.volume == pytest.approx(
        upstream.selected_volume
    )

    assert result.candidate.projected_stop_loss == pytest.approx(
        upstream.estimated_stop_loss_amount
    )

    assert result.candidate.margin_required == pytest.approx(
        upstream.margin_required
    )

    assert result.candidate.structural_stop_distance == pytest.approx(
        upstream.stop_distance_price
    )


def test_candidate_preserves_raw_spread_semantics() -> None:

    upstream = risk_plan()

    result = bridge().admit(
        risk_plan=upstream,
        leg_id="L1",
        account_margin_used=0.0,
        estimated_slippage_price=0.02,
        estimated_slippage_cost=0.02,
        estimated_commission_cost=0.03,
    )

    assert result.valid is True

    assert result.friction_assessment.total_friction_cost == pytest.approx(
        0.31
    )

    assert result.candidate.spread_cost == pytest.approx(
        upstream.spread_cost
    )

    assert result.candidate.spread_cost == pytest.approx(
        0.26
    )


def test_current_63_account_is_blocked_by_all_in_one_percent_budget() -> None:

    upstream = risk_plan(
        balance=63.35,
        stop_distance=0.50,
    )

    assert upstream.valid is True

    result = bridge().admit(
        risk_plan=upstream,
        leg_id="L1",
        account_margin_used=0.0,
    )

    assert result.valid is False

    assert result.admitted is False

    assert result.reason == (
        "EXECUTION_FRICTION_BLOCKED"
    )

    assert (
        "ALL_IN_LOSS_EXCEEDS_HARD_BUDGET"
        in
        result.friction_assessment.violations
    )

    assert result.account_plan is None


def test_friction_block_happens_before_account_adapter() -> None:

    class ExplodingAdapter:

        def plan_addition(
            self,
            **_: Any,
        ) -> Any:

            raise AssertionError(
                "account adapter must not run after friction block"
            )

    result = bridge(
        adapter=ExplodingAdapter()
    ).admit(
        risk_plan=risk_plan(
            balance=63.35,
            stop_distance=0.50,
        ),
        leg_id="L1",
        account_margin_used=0.0,
    )

    assert result.reason == (
        "EXECUTION_FRICTION_BLOCKED"
    )


def test_high_slippage_can_block_otherwise_feasible_plan() -> None:

    result = bridge().admit(
        risk_plan=risk_plan(),
        leg_id="L1",
        account_margin_used=0.0,
        estimated_slippage_price=0.11,
        estimated_slippage_cost=0.05,
    )

    assert result.valid is False

    assert result.reason == (
        "EXECUTION_FRICTION_BLOCKED"
    )

    assert (
        "SLIPPAGE_DOMINATES_STRUCTURAL_STOP"
        in
        result.friction_assessment.violations
    )


def test_invalid_friction_input_stops_before_account_admission() -> None:

    result = bridge().admit(
        risk_plan=risk_plan(),
        leg_id="L1",
        account_margin_used=0.0,
        estimated_slippage_cost=-0.01,
    )

    assert result.valid is False

    assert result.reason == (
        "FRICTION_ASSESSMENT_INVALID"
    )

    assert result.friction_reason == (
        "NEGATIVE_ESTIMATED_SLIPPAGE_COST"
    )

    assert result.account_plan is None


def test_rejected_broker_plan_stops_before_friction() -> None:

    upstream = risk_plan(
        balance=2.0,
        stop_distance=0.50,
    )

    assert upstream.valid is False

    result = bridge().admit(
        risk_plan=upstream,
        leg_id="L1",
        account_margin_used=0.0,
    )

    assert result.valid is False

    assert result.reason == (
        "BROKER_RISK_PLAN_REJECTED"
    )

    assert result.friction_assessment is None

    assert result.account_plan is None


def test_profitable_existing_basket_can_admit_addon() -> None:

    upstream = risk_plan(
        balance=100.0,
        equity=100.30,
        free_margin=98.14,
        stop_distance=0.50,
    )

    result = bridge().admit(
        risk_plan=upstream,
        leg_id="L2",
        account_margin_used=2.16,
        existing_legs=1,
        existing_direction="LONG",
        existing_volume=0.01,
        existing_projected_loss=0.50,
        existing_basket_margin=2.16,
        existing_spread_cost=0.26,
        existing_floating_profit=0.30,
        first_leg_initial_risk=0.50,
    )

    assert result.valid is True

    assert result.admitted is True

    assert result.account_plan.accepted_new_legs == 1

    assert result.account_reason == (
        "OK_ACCOUNT_STATE_ADMISSION"
    )


def test_existing_basket_profit_gate_still_applies() -> None:

    upstream = risk_plan(
        balance=100.0,
        equity=100.05,
        free_margin=97.89,
        stop_distance=0.50,
    )

    result = bridge().admit(
        risk_plan=upstream,
        leg_id="L2",
        account_margin_used=2.16,
        existing_legs=1,
        existing_direction="LONG",
        existing_volume=0.01,
        existing_projected_loss=0.50,
        existing_basket_margin=2.16,
        existing_spread_cost=0.26,
        existing_floating_profit=0.05,
        first_leg_initial_risk=0.50,
    )

    assert result.valid is False

    assert result.admitted is False

    assert result.reason == (
        "ACCOUNT_COMPOUNDING_ADMISSION_REJECTED"
    )

    assert result.account_reason == (
        "ADD_REQUIRES_EXISTING_PROFIT"
    )


def test_impossible_existing_margin_state_is_preserved() -> None:

    result = bridge().admit(
        risk_plan=risk_plan(),
        leg_id="L2",
        account_margin_used=2.00,
        existing_legs=1,
        existing_direction="LONG",
        existing_volume=0.01,
        existing_projected_loss=0.50,
        existing_basket_margin=2.16,
        existing_spread_cost=0.26,
        existing_floating_profit=0.30,
        first_leg_initial_risk=0.50,
    )

    assert result.valid is False

    assert result.reason == (
        "ACCOUNT_COMPOUNDING_ADMISSION_REJECTED"
    )

    assert result.account_reason == (
        "BASKET_MARGIN_EXCEEDS_ACCOUNT_MARGIN"
    )


def test_short_direction_flows_through_all_layers() -> None:

    result = bridge().admit(
        risk_plan=risk_plan(
            balance=100.0,
            stop_distance=0.50,
            direction="SHORT",
        ),
        leg_id="S1",
        account_margin_used=0.0,
    )

    assert result.valid is True

    assert result.admitted is True

    assert result.direction == (
        "SHORT"
    )

    assert result.candidate.direction == (
        "SHORT"
    )


def test_empty_leg_id_is_rejected() -> None:

    result = bridge().admit(
        risk_plan=risk_plan(),
        leg_id="   ",
        account_margin_used=0.0,
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_LEG_ID"
    )