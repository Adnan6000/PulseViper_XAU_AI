"""
Offline tests for CompoundingTradeStateMachine v1.0.
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

state_module: Any = importlib.import_module(
    "02_AI.Shadow.compounding_trade_state_machine"
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
    state_module.CompoundingTradeStateMachine
)


# =============================================================================
# Fixtures
# =============================================================================


def planner() -> Any:

    return Planner(
        Policy(
            compounding_enabled=True,
            allow_initial_multi_leg=True,
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


def machine() -> Any:

    resolved_planner = (
        planner()
    )

    resolved_adapter = Adapter(
        planner=resolved_planner
    )

    return Machine(
        planner=resolved_planner,
        adapter=resolved_adapter,
    )


def leg(
    leg_id: str,
    *,
    direction: str = "LONG",
    loss: float = 0.30,
    margin: float = 2.17,
    spread: float = 0.26,
    volume: float = 0.01,
) -> Any:

    return Leg(
        leg_id=leg_id,
        direction=direction,
        volume=volume,
        projected_stop_loss=loss,
        margin_required=margin,
        spread_cost=spread,
        structural_stop_distance=loss,
    )


def start_one_leg(
    *,
    balance: float = 10.0,
) -> tuple[
    Any,
    Any,
]:

    engine = machine()

    transition = engine.start(
        state=engine.empty_state(),
        account_balance=balance,
        account_equity=balance,
        account_free_margin=balance,
        account_margin_used=0.0,
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


# =============================================================================
# Safety
# =============================================================================


def test_state_machine_is_shadow_only() -> None:

    engine, state = start_one_leg()

    transition = engine.step(
        state=state,
        account_balance=10.0,
        account_equity=10.0,
        account_free_margin=7.83,
        account_margin_used=2.17,
        current_floating_profit=0.0,
        volume_min=0.01,
        volume_step=0.01,
    )

    assert transition.live_authorized is False

    assert transition.mode == (
        "SHADOW_STATEFUL_COMPOUNDING_LIFECYCLE_ONLY"
    )


# =============================================================================
# Start
# =============================================================================


def test_start_single_leg() -> None:

    engine = machine()

    transition = engine.start(
        state=engine.empty_state(),
        account_balance=10.0,
        account_equity=10.0,
        account_free_margin=10.0,
        account_margin_used=0.0,
        candidates=[
            leg(
                "L1"
            )
        ],
        volume_min=0.01,
        volume_step=0.01,
    )

    assert transition.valid is True

    assert transition.action == (
        "START_BASKET"
    )

    assert transition.state_after.status == (
        "LEG_1_ACTIVE"
    )

    assert transition.state_after.active_volume == pytest.approx(
        0.01
    )

    assert transition.state_after.projected_stop_loss == pytest.approx(
        0.30
    )


def test_start_can_accept_initial_multi_leg_when_policy_allows() -> None:

    engine = machine()

    transition = engine.start(
        state=engine.empty_state(),
        account_balance=10.0,
        account_equity=10.0,
        account_free_margin=10.0,
        account_margin_used=0.0,
        candidates=[
            leg(
                "L1"
            ),
            leg(
                "L2"
            ),
        ],
        volume_min=0.01,
        volume_step=0.01,
    )

    assert transition.valid is True

    assert transition.state_after.status == (
        "PYRAMID_ACTIVE"
    )

    assert len(
        transition.state_after.active_legs
    ) == 2

    assert transition.state_after.active_volume == pytest.approx(
        0.02
    )


def test_duplicate_initial_leg_id_is_rejected() -> None:

    engine = machine()

    transition = engine.start(
        state=engine.empty_state(),
        account_balance=10.0,
        account_equity=10.0,
        account_free_margin=10.0,
        account_margin_used=0.0,
        candidates=[
            leg(
                "L1"
            ),
            leg(
                "L1"
            ),
        ],
        volume_min=0.01,
        volume_step=0.01,
    )

    assert transition.valid is False

    assert transition.reason == (
        "DUPLICATE_LEG_ID"
    )


# =============================================================================
# Profit-gated pyramid
# =============================================================================


def test_low_profit_does_not_unlock_second_leg() -> None:

    engine, state = start_one_leg()

    transition = engine.step(
        state=state,
        account_balance=10.0,
        account_equity=10.03,
        account_free_margin=7.86,
        account_margin_used=2.17,

        # $0.03 / $0.30 = 0.10R
        current_floating_profit=0.03,

        volume_min=0.01,
        volume_step=0.01,

        add_candidates=[
            leg(
                "L2"
            )
        ],
    )

    assert transition.valid is False

    assert transition.reason == (
        "ADD_REQUIRES_EXISTING_PROFIT"
    )

    assert transition.state_after.active_volume == pytest.approx(
        0.01
    )


def test_profit_proof_unlocks_second_leg() -> None:

    engine, state = start_one_leg()

    transition = engine.step(
        state=state,
        account_balance=10.0,

        # Existing basket is profitable.
        account_equity=10.10,

        # Equity 10.10 - existing margin 2.17.
        account_free_margin=7.93,

        account_margin_used=2.17,

        # $0.10 / $0.30 = 0.333R.
        current_floating_profit=0.10,

        volume_min=0.01,
        volume_step=0.01,

        add_candidates=[
            leg(
                "L2"
            )
        ],
    )

    assert transition.valid is True

    assert transition.action == (
        "ADD_COMPOUNDING_LEGS"
    )

    assert transition.admitted_leg_ids == (
        "L2",
    )

    assert transition.state_after.active_volume == pytest.approx(
        0.02
    )

    assert transition.state_after.projected_stop_loss == pytest.approx(
        0.60
    )

    assert transition.state_after.status == (
        "PYRAMID_ACTIVE"
    )


# =============================================================================
# Partial booking
# =============================================================================


def test_partial_booking_has_priority_over_new_add_on() -> None:

    engine = machine()

    start = engine.start(
        state=engine.empty_state(),
        account_balance=10.0,
        account_equity=10.0,
        account_free_margin=10.0,
        account_margin_used=0.0,
        candidates=[
            leg(
                "L1"
            ),
            leg(
                "L2"
            ),
        ],
        volume_min=0.01,
        volume_step=0.01,
    )

    state = start.state_after

    assert state.active_volume == pytest.approx(
        0.02
    )

    transition = engine.step(
        state=state,
        account_balance=10.0,
        account_equity=10.50,
        account_free_margin=6.16,
        account_margin_used=4.34,

        # Initial basket risk = $0.60.
        # $0.50 / $0.60 = 0.833R.
        current_floating_profit=0.50,

        volume_min=0.01,
        volume_step=0.01,

        # This candidate must NOT be added on the same step because
        # partial-book management has priority.
        add_candidates=[
            leg(
                "L3"
            )
        ],
    )

    assert transition.valid is True

    assert transition.action == (
        "BOOK_PARTIAL_AND_ACTIVATE_STRUCTURE_TRAIL"
    )

    assert transition.admitted_leg_ids == ()

    assert transition.simulated_close_volume == pytest.approx(
        0.01
    )

    assert transition.state_after.active_volume == pytest.approx(
        0.01
    )

    assert transition.state_after.partial_booking_count == 1

    assert transition.state_after.trail_active is True


def test_paid_spread_is_not_erased_after_partial_booking() -> None:

    engine = machine()

    start = engine.start(
        state=engine.empty_state(),
        account_balance=10.0,
        account_equity=10.0,
        account_free_margin=10.0,
        account_margin_used=0.0,
        candidates=[
            leg(
                "L1"
            ),
            leg(
                "L2"
            ),
        ],
        volume_min=0.01,
        volume_step=0.01,
    )

    state = start.state_after

    assert state.cumulative_spread_cost == pytest.approx(
        0.52
    )

    transition = engine.step(
        state=state,
        account_balance=10.0,
        account_equity=10.50,
        account_free_margin=6.16,
        account_margin_used=4.34,
        current_floating_profit=0.50,
        volume_min=0.01,
        volume_step=0.01,
    )

    assert transition.state_after.cumulative_spread_cost == pytest.approx(
        0.52
    )


# =============================================================================
# Trail / runner
# =============================================================================


def test_single_leg_can_enter_structure_trail_state() -> None:

    engine, state = start_one_leg()

    transition = engine.step(
        state=state,
        account_balance=10.0,
        account_equity=10.18,
        account_free_margin=8.01,
        account_margin_used=2.17,

        # $0.18 / $0.30 = 0.60R
        current_floating_profit=0.18,

        volume_min=0.01,
        volume_step=0.01,
    )

    assert transition.valid is True

    assert transition.state_after.trail_active is True

    assert transition.state_after.status == (
        "PROTECTED"
    )

    assert transition.action == (
        "ACTIVATE_STRUCTURE_TRAIL"
    )


def test_single_leg_can_enter_runner_state() -> None:

    engine, state = start_one_leg()

    transition = engine.step(
        state=state,
        account_balance=10.0,
        account_equity=10.45,
        account_free_margin=8.28,
        account_margin_used=2.17,

        # $0.45 / $0.30 = 1.50R
        current_floating_profit=0.45,

        volume_min=0.01,
        volume_step=0.01,
    )

    assert transition.valid is True

    assert transition.state_after.runner_mode is True

    assert transition.state_after.status == (
        "RUNNER"
    )


# =============================================================================
# Optional later leg
# =============================================================================


def test_runner_can_add_another_leg_if_account_and_basket_allow() -> None:

    engine, state = start_one_leg()

    # First move state into runner without adding.
    runner_transition = engine.step(
        state=state,
        account_balance=10.0,
        account_equity=10.45,
        account_free_margin=8.28,
        account_margin_used=2.17,
        current_floating_profit=0.45,
        volume_min=0.01,
        volume_step=0.01,
    )

    runner_state = (
        runner_transition.state_after
    )

    assert runner_state.runner_mode is True

    add_transition = engine.step(
        state=runner_state,
        account_balance=10.0,
        account_equity=10.45,
        account_free_margin=8.28,
        account_margin_used=2.17,
        current_floating_profit=0.45,
        volume_min=0.01,
        volume_step=0.01,
        add_candidates=[
            leg(
                "L2"
            )
        ],
    )

    assert add_transition.valid is True

    assert add_transition.action == (
        "ADD_COMPOUNDING_LEGS"
    )

    assert add_transition.state_after.active_volume == pytest.approx(
        0.02
    )

    assert add_transition.state_after.runner_mode is True


# =============================================================================
# Direction protection
# =============================================================================


def test_opposite_direction_add_is_rejected() -> None:

    engine, state = start_one_leg()

    transition = engine.step(
        state=state,
        account_balance=10.0,
        account_equity=10.10,
        account_free_margin=7.93,
        account_margin_used=2.17,
        current_floating_profit=0.10,
        volume_min=0.01,
        volume_step=0.01,
        add_candidates=[
            leg(
                "S1",
                direction="SHORT",
            )
        ],
    )

    assert transition.valid is False

    assert transition.reason == (
        "ADD_DIRECTION_MISMATCH"
    )


# =============================================================================
# Structural invalidation
# =============================================================================


def test_structure_invalidation_closes_shadow_basket() -> None:

    engine = machine()

    start = engine.start(
        state=engine.empty_state(),
        account_balance=10.0,
        account_equity=10.0,
        account_free_margin=10.0,
        account_margin_used=0.0,
        candidates=[
            leg(
                "L1"
            ),
            leg(
                "L2"
            ),
        ],
        volume_min=0.01,
        volume_step=0.01,
    )

    transition = engine.step(
        state=start.state_after,
        account_balance=10.0,
        account_equity=9.80,
        account_free_margin=5.46,
        account_margin_used=4.34,
        current_floating_profit=-0.20,
        volume_min=0.01,
        volume_step=0.01,
        structure_invalidated=True,
    )

    assert transition.valid is True

    assert transition.action == (
        "EXIT_BASKET_ON_STRUCTURE_INVALIDATION"
    )

    assert transition.state_after.status == (
        "CLOSED"
    )

    assert transition.state_after.active_volume == pytest.approx(
        0.0
    )

    assert set(
        transition.fully_closed_leg_ids
    ) == {
        "L1",
        "L2",
    }


def test_closed_session_cannot_continue_trading_lifecycle() -> None:

    engine, state = start_one_leg()

    closed = engine.step(
        state=state,
        account_balance=10.0,
        account_equity=9.90,
        account_free_margin=7.73,
        account_margin_used=2.17,
        current_floating_profit=-0.10,
        volume_min=0.01,
        volume_step=0.01,
        structure_invalidated=True,
    )

    transition = engine.step(
        state=closed.state_after,
        account_balance=10.0,
        account_equity=10.0,
        account_free_margin=10.0,
        account_margin_used=0.0,
        current_floating_profit=0.0,
        volume_min=0.01,
        volume_step=0.01,
    )

    assert transition.valid is False

    assert transition.reason == (
        "NO_ACTIVE_BASKET"
    )