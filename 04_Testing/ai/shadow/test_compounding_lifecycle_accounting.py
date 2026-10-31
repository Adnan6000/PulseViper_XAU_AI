"""
Offline integration tests for CompoundingLifecycleAccounting v1.0.
"""

from __future__ import annotations

import importlib
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

integration_module: Any = importlib.import_module(
    "02_AI.Shadow.compounding_lifecycle_accounting"
)


Planner: Any = (
    basket_module.BootstrapCompoundingPlanner
)

Policy: Any = (
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

Coordinator: Any = (
    integration_module.CompoundingLifecycleAccounting
)


def coordinator() -> Any:

    planner = Planner(
        Policy(
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

    ledger = Ledger()

    return Coordinator(
        machine=machine,
        ledger=ledger,
    )


def leg(
    leg_id: str,
    *,
    loss: float = 0.50,
    margin: float = 2.19,
    spread: float = 0.26,
) -> Any:

    return Leg(
        leg_id=leg_id,
        direction="LONG",
        volume=0.01,
        projected_stop_loss=loss,
        margin_required=margin,
        spread_cost=spread,
        structural_stop_distance=loss,
    )


def start_one_leg() -> tuple[
    Any,
    Any,
]:

    engine = coordinator()

    state = engine.initial_state(
        balance=10.0
    )

    transition = engine.start(
        state=state,
        candidates=[
            leg(
                "L1"
            )
        ],
        volume_min=0.01,
        volume_step=0.01,
    )

    assert transition.valid is True

    return (
        engine,
        transition.state_after,
    )


def test_integration_is_shadow_only() -> None:

    engine, state = start_one_leg()

    assert state.pnl_state.live_authorized is False

    result = engine.step(
        state=state,
        current_market_floating_profit=0.0,
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.live_authorized is False

    assert result.mode == (
        "SHADOW_COMPOUNDING_LIFECYCLE_ACCOUNTING_ONLY"
    )


def test_start_immediately_accounts_for_spread() -> None:

    engine, state = start_one_leg()

    assert state.trade_state.active_volume == pytest.approx(
        0.01
    )

    assert state.pnl_state.active_volume == pytest.approx(
        0.01
    )

    assert state.pnl_state.floating_profit == pytest.approx(
        -0.26
    )

    assert state.pnl_state.equity == pytest.approx(
        9.74
    )

    assert state.pnl_state.margin_used == pytest.approx(
        2.19
    )

    assert state.pnl_state.free_margin == pytest.approx(
        7.55
    )


def test_profit_proof_can_add_second_leg() -> None:

    engine, state = start_one_leg()

    result = engine.step(
        state=state,

        # Broker-reported floating profit of existing L1.
        current_market_floating_profit=0.175,

        volume_min=0.01,
        volume_step=0.01,

        add_candidates=[
            leg(
                "L2"
            )
        ],
    )

    assert result.valid is True

    assert result.action == (
        "ADD_COMPOUNDING_LEGS"
    )

    assert result.state_after.trade_state.active_volume == pytest.approx(
        0.02
    )

    assert result.state_after.pnl_state.active_volume == pytest.approx(
        0.02
    )


def test_second_leg_immediately_applies_new_spread_drag() -> None:

    engine, state = start_one_leg()

    result = engine.step(
        state=state,
        current_market_floating_profit=0.175,
        volume_min=0.01,
        volume_step=0.01,
        add_candidates=[
            leg(
                "L2"
            )
        ],
    )

    pnl = (
        result.state_after.pnl_state
    )

    # Existing net broker P/L:
    # +0.175
    #
    # New L2 spread:
    # -0.260
    #
    # Immediate lifecycle floating:
    # -0.085
    assert pnl.floating_profit == pytest.approx(
        -0.085
    )

    assert pnl.lifecycle_profit == pytest.approx(
        -0.085
    )

    assert pnl.cumulative_spread_cost == pytest.approx(
        0.52
    )

    assert pnl.margin_used == pytest.approx(
        4.38
    )


def test_partial_booking_moves_profit_into_realized_bucket() -> None:

    engine, state = start_one_leg()

    added = engine.step(
        state=state,
        current_market_floating_profit=0.175,
        volume_min=0.01,
        volume_step=0.01,
        add_candidates=[
            leg(
                "L2"
            )
        ],
    )

    state = (
        added.state_after
    )

    partial = engine.step(
        state=state,

        # Current broker floating across both active legs.
        # Peak lifecycle risk = $1.00.
        current_market_floating_profit=0.85,

        volume_min=0.01,
        volume_step=0.01,
    )

    assert partial.valid is True

    assert partial.state_after.trade_state.active_volume == pytest.approx(
        0.01
    )

    pnl = (
        partial.state_after.pnl_state
    )

    assert pnl.active_volume == pytest.approx(
        0.01
    )

    assert pnl.realized_profit == pytest.approx(
        0.425
    )

    assert pnl.floating_profit == pytest.approx(
        0.425
    )

    assert pnl.lifecycle_profit == pytest.approx(
        0.85
    )

    assert pnl.lifecycle_r == pytest.approx(
        0.85
    )


def test_runner_uses_realized_plus_remaining_floating_profit() -> None:

    engine, state = start_one_leg()

    state = engine.step(
        state=state,
        current_market_floating_profit=0.175,
        volume_min=0.01,
        volume_step=0.01,
        add_candidates=[
            leg(
                "L2"
            )
        ],
    ).state_after

    state = engine.step(
        state=state,
        current_market_floating_profit=0.85,
        volume_min=0.01,
        volume_step=0.01,
    ).state_after

    assert state.pnl_state.realized_profit == pytest.approx(
        0.425
    )

    # Remaining floating only needs +1.075 because +0.425 has already
    # been realized.
    runner = engine.step(
        state=state,
        current_market_floating_profit=1.075,
        volume_min=0.01,
        volume_step=0.01,
    )

    assert runner.valid is True

    assert runner.state_after.pnl_state.lifecycle_profit == pytest.approx(
        1.50
    )

    assert runner.state_after.pnl_state.lifecycle_r == pytest.approx(
        1.50
    )

    assert runner.state_after.trade_state.runner_mode is True

    assert runner.state_after.trade_state.status == (
        "RUNNER"
    )


def test_runner_can_add_l3_and_new_spread_is_accounted() -> None:

    engine, state = start_one_leg()

    state = engine.step(
        state=state,
        current_market_floating_profit=0.175,
        volume_min=0.01,
        volume_step=0.01,
        add_candidates=[
            leg(
                "L2"
            )
        ],
    ).state_after

    state = engine.step(
        state=state,
        current_market_floating_profit=0.85,
        volume_min=0.01,
        volume_step=0.01,
    ).state_after

    state = engine.step(
        state=state,
        current_market_floating_profit=1.075,
        volume_min=0.01,
        volume_step=0.01,
    ).state_after

    assert state.pnl_state.lifecycle_profit == pytest.approx(
        1.50
    )

    add_l3 = engine.step(
        state=state,
        current_market_floating_profit=1.075,
        volume_min=0.01,
        volume_step=0.01,
        add_candidates=[
            leg(
                "L3"
            )
        ],
    )

    assert add_l3.valid is True

    assert add_l3.action == (
        "ADD_COMPOUNDING_LEGS"
    )

    pnl = (
        add_l3.state_after.pnl_state
    )

    assert pnl.active_volume == pytest.approx(
        0.02
    )

    # Realized = 0.425
    # Existing remaining floating = 1.075
    # New spread = -0.26
    #
    # Lifecycle:
    # 0.425 + 1.075 - 0.26 = 1.24
    assert pnl.lifecycle_profit == pytest.approx(
        1.24
    )

    assert pnl.cumulative_spread_cost == pytest.approx(
        0.78
    )


def test_structure_exit_moves_remaining_floating_into_realized() -> None:

    engine, state = start_one_leg()

    exit_result = engine.step(
        state=state,
        current_market_floating_profit=-0.30,
        volume_min=0.01,
        volume_step=0.01,
        structure_invalidated=True,
    )

    assert exit_result.valid is True

    assert exit_result.state_after.trade_state.status == (
        "CLOSED"
    )

    pnl = (
        exit_result.state_after.pnl_state
    )

    assert pnl.active_volume == pytest.approx(
        0.0
    )

    assert pnl.margin_used == pytest.approx(
        0.0
    )

    assert pnl.floating_profit == pytest.approx(
        0.0
    )

    assert pnl.realized_profit == pytest.approx(
        -0.30
    )


def test_trade_and_pnl_exposure_stay_reconciled() -> None:

    engine, state = start_one_leg()

    result = engine.step(
        state=state,
        current_market_floating_profit=0.175,
        volume_min=0.01,
        volume_step=0.01,
        add_candidates=[
            leg(
                "L2"
            )
        ],
    )

    trade = (
        result.state_after.trade_state
    )

    pnl = (
        result.state_after.pnl_state
    )

    assert trade.active_volume == pytest.approx(
        pnl.active_volume
    )

    assert trade.basket_margin == pytest.approx(
        pnl.margin_used
    )