"""
Offline tests for CompoundingAccountStateAdapter v1.0.
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


def adapter() -> Any:

    return Adapter(
        planner=planner()
    )


def leg(
    leg_id: str,
    *,
    loss: float = 0.30,
    margin: float = 2.17,
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


def test_shadow_only() -> None:

    result = adapter().plan_addition(
        account_balance=3.0,
        account_equity=3.0,
        account_free_margin=3.0,
        account_margin_used=0.0,
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
        "SHADOW_ACCOUNT_AWARE_COMPOUNDING_ONLY"
    )


def test_three_dollar_account_can_admit_one_minimum_leg() -> None:

    result = adapter().plan_addition(
        account_balance=3.0,
        account_equity=3.0,
        account_free_margin=3.0,
        account_margin_used=0.0,
        candidates=[
            leg(
                "L1",
                loss=0.30,
            ),
        ],
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.valid is True

    assert result.accepted_new_legs == 1

    assert result.added_margin == pytest.approx(
        2.17
    )

    assert result.estimated_free_margin_after == pytest.approx(
        0.83
    )


def test_three_dollar_account_cannot_admit_two_legs() -> None:

    result = adapter().plan_addition(
        account_balance=3.0,
        account_equity=3.0,
        account_free_margin=3.0,
        account_margin_used=0.0,
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

    assert result.reason == (
        "OK_ACCOUNT_STATE_PARTIAL_ADMISSION"
    )


def test_five_dollar_account_still_only_admits_one_under_85pct_cap() -> None:

    result = adapter().plan_addition(
        account_balance=5.0,
        account_equity=5.0,
        account_free_margin=5.0,
        account_margin_used=0.0,
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


def test_small_equity_growth_can_make_second_leg_margin_feasible() -> None:

    result = adapter().plan_addition(
        account_balance=5.20,
        account_equity=5.20,
        account_free_margin=5.20,
        account_margin_used=0.0,
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

    assert result.added_margin == pytest.approx(
        4.34
    )


def test_profitable_existing_leg_can_add_second_leg_when_free_margin_exists() -> None:

    result = adapter().plan_addition(
        account_balance=5.0,

        # Existing profitable trade increased equity.
        account_equity=5.30,

        # 5.30 equity - 2.17 used margin.
        account_free_margin=3.13,

        account_margin_used=2.17,

        candidates=[
            leg(
                "L2",
                loss=0.30,
            ),
        ],

        volume_min=0.01,
        volume_step=0.01,

        existing_legs=1,
        existing_direction="LONG",
        existing_volume=0.01,
        existing_projected_loss=0.30,
        existing_basket_margin=2.17,
        existing_spread_cost=0.26,

        # +1R relative to initial $0.30 risk.
        existing_floating_profit=0.30,
        first_leg_initial_risk=0.30,
    )

    assert result.valid is True

    assert result.accepted_new_legs == 1

    assert result.added_margin == pytest.approx(
        2.17
    )

    assert result.estimated_free_margin_after == pytest.approx(
        0.96
    )


def test_addition_blocks_when_current_free_margin_is_insufficient() -> None:

    result = adapter().plan_addition(
        account_balance=10.0,
        account_equity=10.0,

        # Other account exposure has consumed most free margin.
        account_free_margin=1.00,

        account_margin_used=9.00,

        candidates=[
            leg(
                "L1",
                loss=0.30,
            ),
        ],
        volume_min=0.01,
        volume_step=0.01,
    )

    assert result.valid is False

    assert result.reason == (
        "INSUFFICIENT_CURRENT_FREE_MARGIN"
    )


def test_basket_margin_cannot_exceed_total_account_margin_used() -> None:

    result = adapter().plan_addition(
        account_balance=10.0,
        account_equity=10.0,
        account_free_margin=8.0,
        account_margin_used=2.0,
        candidates=[
            leg(
                "L2",
            ),
        ],
        volume_min=0.01,
        volume_step=0.01,
        existing_legs=1,
        existing_direction="LONG",
        existing_volume=0.01,
        existing_projected_loss=0.30,

        # Impossible: basket says 2.17 margin but account says only 2.00 used.
        existing_basket_margin=2.17,

        existing_spread_cost=0.26,
        existing_floating_profit=0.30,
        first_leg_initial_risk=0.30,
    )

    assert result.valid is False

    assert result.reason == (
        "BASKET_MARGIN_EXCEEDS_ACCOUNT_MARGIN"
    )


def test_profit_gate_still_applies_through_adapter() -> None:

    result = adapter().plan_addition(
        account_balance=10.0,
        account_equity=10.0,
        account_free_margin=7.83,
        account_margin_used=2.17,
        candidates=[
            leg(
                "L2",
            ),
        ],
        volume_min=0.01,
        volume_step=0.01,
        existing_legs=1,
        existing_direction="LONG",
        existing_volume=0.01,
        existing_projected_loss=0.30,
        existing_basket_margin=2.17,
        existing_spread_cost=0.26,

        # Only +0.10R, below +0.25R add threshold.
        existing_floating_profit=0.03,
        first_leg_initial_risk=0.30,
    )

    assert result.valid is False

    assert result.reason == (
        "ADD_REQUIRES_EXISTING_PROFIT"
    )