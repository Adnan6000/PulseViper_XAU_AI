"""
Regression tests for compounding lifecycle R-risk watermark.

The lifecycle must never reduce its R denominator merely because a position
was partially booked.
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


def machine() -> Any:

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

    return Machine(
        planner=planner,
        adapter=adapter,
    )


def leg(
    leg_id: str,
) -> Any:

    return Leg(
        leg_id=leg_id,
        direction="LONG",
        volume=0.01,
        projected_stop_loss=0.50,
        margin_required=2.19,
        spread_cost=0.26,
        structural_stop_distance=0.50,
    )


def test_pyramid_updates_lifecycle_risk_watermark() -> None:

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
            )
        ],
        volume_min=0.01,
        volume_step=0.01,
    )

    assert start.valid is True

    assert start.state_after.initial_basket_risk == pytest.approx(
        0.50
    )

    add = engine.step(
        state=start.state_after,
        account_balance=10.0,
        account_equity=10.175,
        account_free_margin=7.985,
        account_margin_used=2.19,
        current_floating_profit=0.175,
        volume_min=0.01,
        volume_step=0.01,
        add_candidates=[
            leg(
                "L2"
            )
        ],
    )

    assert add.valid is True

    assert add.state_after.projected_stop_loss == pytest.approx(
        1.00
    )

    assert add.state_after.initial_basket_risk == pytest.approx(
        1.00
    )


def test_partial_booking_does_not_reduce_risk_watermark() -> None:

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
            )
        ],
        volume_min=0.01,
        volume_step=0.01,
    )

    add = engine.step(
        state=start.state_after,
        account_balance=10.0,
        account_equity=10.175,
        account_free_margin=7.985,
        account_margin_used=2.19,
        current_floating_profit=0.175,
        volume_min=0.01,
        volume_step=0.01,
        add_candidates=[
            leg(
                "L2"
            )
        ],
    )

    partial = engine.step(
        state=add.state_after,
        account_balance=10.0,
        account_equity=10.85,
        account_free_margin=6.47,
        account_margin_used=4.38,

        # 0.85R against $1.00 risk watermark.
        current_floating_profit=0.85,

        volume_min=0.01,
        volume_step=0.01,
    )

    assert partial.valid is True

    assert partial.simulated_close_volume == pytest.approx(
        0.01
    )

    assert partial.state_after.projected_stop_loss == pytest.approx(
        0.50
    )

    # Critical:
    # active risk reduced, lifecycle reference did NOT.
    assert partial.state_after.initial_basket_risk == pytest.approx(
        1.00
    )


def test_old_regressive_runner_threshold_no_longer_works() -> None:

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
            )
        ],
        volume_min=0.01,
        volume_step=0.01,
    )

    add = engine.step(
        state=start.state_after,
        account_balance=10.0,
        account_equity=10.175,
        account_free_margin=7.985,
        account_margin_used=2.19,
        current_floating_profit=0.175,
        volume_min=0.01,
        volume_step=0.01,
        add_candidates=[
            leg(
                "L2"
            )
        ],
    )

    partial = engine.step(
        state=add.state_after,
        account_balance=10.0,
        account_equity=10.85,
        account_free_margin=6.47,
        account_margin_used=4.38,
        current_floating_profit=0.85,
        volume_min=0.01,
        volume_step=0.01,
    )

    # Old bug:
    # after partial the denominator shrank to $0.50, therefore $0.75 looked
    # like 1.50R.
    #
    # Correct:
    # denominator remains $1.00, so $0.75 = 0.75R.
    regression = engine.step(
        state=partial.state_after,
        account_balance=10.0,
        account_equity=10.75,
        account_free_margin=8.56,
        account_margin_used=2.19,
        current_floating_profit=0.75,
        volume_min=0.01,
        volume_step=0.01,
    )

    assert regression.valid is True

    assert regression.state_after.current_r == pytest.approx(
        0.75
    )

    assert regression.state_after.runner_mode is False


def test_runner_requires_true_150r_against_peak_basket_risk() -> None:

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
            )
        ],
        volume_min=0.01,
        volume_step=0.01,
    )

    add = engine.step(
        state=start.state_after,
        account_balance=10.0,
        account_equity=10.175,
        account_free_margin=7.985,
        account_margin_used=2.19,
        current_floating_profit=0.175,
        volume_min=0.01,
        volume_step=0.01,
        add_candidates=[
            leg(
                "L2"
            )
        ],
    )

    partial = engine.step(
        state=add.state_after,
        account_balance=10.0,
        account_equity=10.85,
        account_free_margin=6.47,
        account_margin_used=4.38,
        current_floating_profit=0.85,
        volume_min=0.01,
        volume_step=0.01,
    )

    runner = engine.step(
        state=partial.state_after,
        account_balance=10.0,
        account_equity=11.50,
        account_free_margin=9.31,
        account_margin_used=2.19,

        # True 1.50R against $1.00 lifecycle watermark.
        current_floating_profit=1.50,

        volume_min=0.01,
        volume_step=0.01,
    )

    assert runner.valid is True

    assert runner.state_after.current_r == pytest.approx(
        1.50
    )

    assert runner.state_after.runner_mode is True

    assert runner.state_after.status == (
        "RUNNER"
    )


def test_watermark_never_decreases_after_scale_out() -> None:

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
            )
        ],
        volume_min=0.01,
        volume_step=0.01,
    )

    add = engine.step(
        state=start.state_after,
        account_balance=10.0,
        account_equity=10.175,
        account_free_margin=7.985,
        account_margin_used=2.19,
        current_floating_profit=0.175,
        volume_min=0.01,
        volume_step=0.01,
        add_candidates=[
            leg(
                "L2"
            )
        ],
    )

    partial = engine.step(
        state=add.state_after,
        account_balance=10.0,
        account_equity=10.85,
        account_free_margin=6.47,
        account_margin_used=4.38,
        current_floating_profit=0.85,
        volume_min=0.01,
        volume_step=0.01,
    )

    assert (
        partial.state_after.initial_basket_risk
        >=
        add.state_after.initial_basket_risk
    )

    assert (
        partial.state_after.initial_basket_risk
        >=
        partial.state_after.projected_stop_loss
    )