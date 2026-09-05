"""
Offline tests for BootstrapCompoundingPlanner v1.0.
"""

from __future__ import annotations

import importlib
from typing import Any

import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Shadow.bootstrap_compounding_planner"
)

Planner: Any = (
    module.BootstrapCompoundingPlanner
)

Policy: Any = (
    module.BootstrapCompoundingPolicy
)

Leg: Any = (
    module.BasketLegCandidate
)


def leg(
    leg_id: str,
    *,
    loss: float = 0.30,
    margin: float = 2.16,
    spread: float = 0.26,
    volume: float = 0.01,
    direction: str = "LONG",
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


def planner(
    *,
    enabled: bool = True,
    initial_multi: bool = True,
    add_after_profit: bool = True,
) -> Any:

    return Planner(
        Policy(
            compounding_enabled=enabled,
            allow_initial_multi_leg=initial_multi,
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
            add_only_after_profit=add_after_profit,
            minimum_profit_r_before_add=0.25,
            partial_booking_enabled=True,
            partial_booking_r=0.75,
            partial_booking_fraction=0.50,
            trail_enabled=True,
            trail_start_r=0.50,
            runner_r=1.25,
        )
    )


def test_shadow_only() -> None:

    result = planner().plan(
        account_balance=3.0,
        account_equity=3.0,
        free_margin=3.0,
        candidates=[
            leg(
                "L1",
                loss=0.30,
            ),
        ],
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.live_authorized is False

    assert result.mode == (
        "SHADOW_BOOTSTRAP_COMPOUNDING_RESEARCH_ONLY"
    )


def test_three_dollar_bootstrap_cap_has_half_dollar_floor() -> None:

    mode, cap, pct = (
        planner().basket_loss_cap(
            3.0
        )
    )

    assert mode == (
        "MICRO_BOOTSTRAP_BASKET"
    )

    assert cap == pytest.approx(
        0.5001,
        abs=1e-4,
    )

    assert pct > 16.0


def test_bootstrap_cap_grows_with_balance() -> None:

    _, cap3, _ = (
        planner().basket_loss_cap(
            3.0
        )
    )

    _, cap10, _ = (
        planner().basket_loss_cap(
            10.0
        )
    )

    assert cap10 > cap3

    assert cap10 == pytest.approx(
        1.667,
        abs=1e-3,
    )


def test_standard_basket_uses_percentage_cap() -> None:

    mode, cap, pct = (
        planner().basket_loss_cap(
            100.0
        )
    )

    assert mode == (
        "STANDARD_COMPOUND_BASKET"
    )

    assert cap == pytest.approx(
        2.0
    )

    assert pct == pytest.approx(
        2.0
    )


def test_compounding_off_allows_only_one_initial_leg() -> None:

    result = planner(
        enabled=False,
        initial_multi=True,
    ).plan(
        account_balance=10.0,
        account_equity=10.0,
        free_margin=10.0,
        candidates=[
            leg(
                "L1",
                loss=0.30,
            ),
            leg(
                "L2",
                loss=0.30,
            ),
        ],
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.valid is True

    assert result.accepted_new_legs == 1

    assert result.total_volume == pytest.approx(
        0.01
    )


def test_initial_multi_leg_switch_off_starts_with_one() -> None:

    result = planner(
        enabled=True,
        initial_multi=False,
    ).plan(
        account_balance=10.0,
        account_equity=10.0,
        free_margin=10.0,
        candidates=[
            leg(
                "L1",
                loss=0.30,
            ),
            leg(
                "L2",
                loss=0.30,
            ),
        ],
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.accepted_new_legs == 1


def test_initial_multi_leg_option_can_accept_multiple() -> None:

    result = planner(
        enabled=True,
        initial_multi=True,
    ).plan(
        account_balance=10.0,
        account_equity=10.0,
        free_margin=10.0,
        candidates=[
            leg(
                "L1",
                loss=0.30,
            ),
            leg(
                "L2",
                loss=0.30,
            ),
        ],
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.valid is True

    assert result.accepted_new_legs == 2

    assert result.total_volume == pytest.approx(
        0.02
    )


def test_three_dollar_account_cannot_stack_two_030_loss_legs() -> None:

    result = planner(
        enabled=True,
        initial_multi=True,
    ).plan(
        account_balance=3.0,
        account_equity=3.0,
        free_margin=3.0,
        candidates=[
            leg(
                "L1",
                loss=0.30,
                margin=1.0,
                spread=0.10,
            ),
            leg(
                "L2",
                loss=0.30,
                margin=1.0,
                spread=0.10,
            ),
        ],
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.valid is True

    assert result.accepted_new_legs == 1

    assert result.total_projected_loss <= (
        result.basket_loss_cap
        +
        1e-9
    )


def test_max_leg_count_is_enforced() -> None:

    result = planner(
        enabled=True,
        initial_multi=True,
    ).plan(
        account_balance=20.0,
        account_equity=20.0,
        free_margin=20.0,
        candidates=[
            leg(
                "L1",
                loss=0.20,
                margin=1.0,
                spread=0.05,
            ),
            leg(
                "L2",
                loss=0.20,
                margin=1.0,
                spread=0.05,
            ),
            leg(
                "L3",
                loss=0.20,
                margin=1.0,
                spread=0.05,
            ),
            leg(
                "L4",
                loss=0.20,
                margin=1.0,
                spread=0.05,
            ),
        ],
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.total_legs <= 3

    assert result.total_volume <= (
        0.03
        +
        1e-9
    )


def test_max_total_volume_is_enforced() -> None:

    custom = Planner(
        Policy(
            compounding_enabled=True,
            allow_initial_multi_leg=True,
            max_simultaneous_legs=5,
            max_total_volume=0.02,
            add_only_after_profit=False,
        )
    )

    result = custom.plan(
        account_balance=20.0,
        account_equity=20.0,
        free_margin=20.0,
        candidates=[
            leg(
                "L1",
                loss=0.10,
                margin=1.0,
                spread=0.02,
            ),
            leg(
                "L2",
                loss=0.10,
                margin=1.0,
                spread=0.02,
            ),
            leg(
                "L3",
                loss=0.10,
                margin=1.0,
                spread=0.02,
            ),
        ],
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.total_volume == pytest.approx(
        0.02
    )

    assert result.accepted_new_legs == 2


def test_add_on_requires_existing_profit() -> None:

    result = planner(
        enabled=True,
        initial_multi=True,
        add_after_profit=True,
    ).plan(
        account_balance=10.0,
        account_equity=10.0,
        free_margin=8.0,
        candidates=[
            leg(
                "L2",
                loss=0.30,
                margin=2.0,
                spread=0.10,
            ),
        ],
        volume_min=0.01,
        volume_step=0.01,
        existing_legs=1,
        existing_direction="LONG",
        existing_volume=0.01,
        existing_projected_loss=0.30,
        existing_margin=2.0,
        existing_spread_cost=0.10,
        existing_floating_profit=0.05,
        first_leg_initial_risk=0.30,
    )

    assert result.valid is False

    assert result.reason == (
        "ADD_REQUIRES_EXISTING_PROFIT"
    )


def test_profitable_existing_leg_can_unlock_add_on() -> None:

    result = planner(
        enabled=True,
        initial_multi=True,
        add_after_profit=True,
    ).plan(
        account_balance=10.0,
        account_equity=10.0,
        free_margin=10.0,
        candidates=[
            leg(
                "L2",
                loss=0.30,
                margin=1.0,
                spread=0.05,
            ),
        ],
        volume_min=0.01,
        volume_step=0.01,
        existing_legs=1,
        existing_direction="LONG",
        existing_volume=0.01,
        existing_projected_loss=0.30,
        existing_margin=1.0,
        existing_spread_cost=0.05,
        existing_floating_profit=0.10,
        first_leg_initial_risk=0.30,
    )

    assert result.valid is True

    assert result.existing_profit_r > 0.25

    assert result.accepted_new_legs == 1


def test_opposite_direction_candidate_is_not_added() -> None:

    result = planner(
        enabled=True,
        initial_multi=True,
        add_after_profit=False,
    ).plan(
        account_balance=10.0,
        account_equity=10.0,
        free_margin=10.0,
        candidates=[
            leg(
                "S1",
                direction="SHORT",
                loss=0.20,
                margin=1.0,
                spread=0.05,
            ),
        ],
        volume_min=0.01,
        volume_step=0.01,
        existing_legs=1,
        existing_direction="LONG",
        existing_volume=0.01,
        existing_projected_loss=0.20,
        existing_margin=1.0,
        existing_spread_cost=0.05,
    )

    assert result.valid is False

    assert result.accepted_new_legs == 0


def test_margin_cap_limits_basket() -> None:

    custom = Planner(
        Policy(
            compounding_enabled=True,
            allow_initial_multi_leg=True,
            max_simultaneous_legs=3,
            max_total_volume=0.03,
            bootstrap_margin_cap_percent=50.0,
            add_only_after_profit=False,
        )
    )

    result = custom.plan(
        account_balance=10.0,
        account_equity=10.0,
        free_margin=5.0,
        candidates=[
            leg(
                "L1",
                loss=0.20,
                margin=2.0,
                spread=0.05,
            ),
            leg(
                "L2",
                loss=0.20,
                margin=2.0,
                spread=0.05,
            ),
        ],
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.accepted_new_legs == 1

    assert result.total_margin <= (
        result.margin_cap_amount
        +
        1e-9
    )


def test_spread_cap_can_limit_basket() -> None:

    custom = Planner(
        Policy(
            compounding_enabled=True,
            allow_initial_multi_leg=True,
            max_simultaneous_legs=3,
            max_total_volume=0.03,
            max_total_spread_to_basket_loss_ratio=0.50,
            add_only_after_profit=False,
        )
    )

    result = custom.plan(
        account_balance=10.0,
        account_equity=10.0,
        free_margin=10.0,
        candidates=[
            leg(
                "L1",
                loss=0.50,
                margin=1.0,
                spread=0.60,
            ),
        ],
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.valid is True

    assert (
        result.spread_to_basket_loss_cap_ratio
        <
        0.50
    )


def test_single_001_cannot_partial_book() -> None:

    result = planner().management_plan(
        current_volume=0.01,
        volume_min=0.01,
        volume_step=0.01,
        current_unrealized_profit=0.30,
        initial_basket_risk=0.30,
    )

    assert result.valid is True

    assert result.partial_booking is False

    assert result.close_volume == pytest.approx(
        0.0
    )


def test_002_can_book_one_001_leg() -> None:

    result = planner().management_plan(
        current_volume=0.02,
        volume_min=0.01,
        volume_step=0.01,
        current_unrealized_profit=0.30,
        initial_basket_risk=0.30,
    )

    assert result.valid is True

    assert result.current_r == pytest.approx(
        1.0
    )

    assert result.partial_booking is True

    assert result.close_volume == pytest.approx(
        0.01
    )

    assert result.remaining_volume == pytest.approx(
        0.01
    )


def test_trailing_activates_after_profit_threshold() -> None:

    result = planner().management_plan(
        current_volume=0.01,
        volume_min=0.01,
        volume_step=0.01,
        current_unrealized_profit=0.18,
        initial_basket_risk=0.30,
    )

    assert result.current_r == pytest.approx(
        0.60
    )

    assert result.trail_active is True


def test_runner_mode_activates_at_high_r() -> None:

    result = planner().management_plan(
        current_volume=0.02,
        volume_min=0.01,
        volume_step=0.01,
        current_unrealized_profit=0.45,
        initial_basket_risk=0.30,
    )

    assert result.current_r == pytest.approx(
        1.50
    )

    assert result.runner_mode is True

    assert result.partial_booking is True

    assert result.instruction == (
        "BOOK_PARTIAL_AND_TRAIL_RUNNER_ON_STRUCTURE"
    )


def test_management_never_authorizes_live_execution() -> None:

    result = planner().management_plan(
        current_volume=0.02,
        volume_min=0.01,
        volume_step=0.01,
        current_unrealized_profit=0.30,
        initial_basket_risk=0.30,
    )

    assert result.live_authorized is False