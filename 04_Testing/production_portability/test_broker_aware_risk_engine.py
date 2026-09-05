"""
Offline tests for BrokerAwareRiskEngine v1.1.
"""

from __future__ import annotations

import importlib
from typing import Any

import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Shadow.broker_aware_risk_engine"
)

BrokerAwareRiskEngine: Any = (
    module.BrokerAwareRiskEngine
)

BrokerRiskPolicy: Any = (
    module.BrokerRiskPolicy
)


# =============================================================================
# Exness XAUUSDm calibration
# =============================================================================


BID = 4318.705

ASK = 4318.965

POINT = 0.001

TICK_SIZE = 0.001

VOLUME_MIN = 0.01

VOLUME_MAX = 200.0

VOLUME_STEP = 0.01

SPREAD = 0.260


def engine() -> Any:

    return BrokerAwareRiskEngine(
        BrokerRiskPolicy(
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

        # Exness calibration:
        #
        # 0.01 lot + $1.00 XAU move ~= $1.00
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

    # Exness calibration:
    #
    # 0.01 lot ~= $2.16 margin at observed price/account state.
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


def plan(
    *,
    balance: float,
    stop_distance: float,
    direction: str = "LONG",
    equity: float | None = None,
    free_margin: float | None = None,
    requested_risk_percent: float | None = None,
) -> Any:

    planner = engine()

    effective_equity = (
        balance
        if equity is None
        else equity
    )

    effective_free_margin = (
        effective_equity
        if free_margin is None
        else free_margin
    )

    if direction == "LONG":

        stop = (
            ASK
            -
            stop_distance
        )

    else:

        stop = (
            BID
            +
            stop_distance
        )

    return planner.plan(
        direction=direction,
        account_balance=balance,
        account_equity=effective_equity,
        free_margin=effective_free_margin,
        bid=BID,
        ask=ASK,
        stop_loss=stop,
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
        requested_risk_percent=requested_risk_percent,
    )


# =============================================================================
# Policy
# =============================================================================


def test_version_and_shadow_mode() -> None:

    planner = engine()

    assert planner.VERSION == "1.1"

    assert planner.MODE == (
        "SHADOW_BROKER_AWARE_RISK_RESEARCH_ONLY"
    )


def test_policy_rejects_standard_target_above_hard_cap() -> None:

    with pytest.raises(
        ValueError,
        match="cannot exceed",
    ):

        BrokerRiskPolicy(
            target_risk_percent=1.5,
            hard_max_risk_percent=1.0,
        )


def test_micro_balance_range_validation() -> None:

    with pytest.raises(
        ValueError,
        match="micro_max_balance",
    ):

        BrokerRiskPolicy(
            micro_min_balance=10.0,
            micro_max_balance=5.0,
        )


# =============================================================================
# Standard mode
# =============================================================================


def test_current_63_account_uses_standard_mode() -> None:

    result = plan(
        balance=63.35,
        stop_distance=0.50,
    )

    assert result.valid is True

    assert result.risk_mode == (
        "STANDARD_COMPOUND"
    )

    assert result.selected_volume == pytest.approx(
        0.01
    )

    assert result.live_authorized is False


def test_current_63_account_500_stop_is_0789_percent_risk() -> None:

    result = plan(
        balance=63.35,
        stop_distance=0.50,
    )

    assert result.actual_risk_percent == pytest.approx(
        (
            0.50
            /
            63.35
        )
        *
        100.0
    )


def test_current_63_account_075_stop_remains_blocked() -> None:

    result = plan(
        balance=63.35,
        stop_distance=0.75,
    )

    assert result.valid is False

    # Standard 1% cannot accept minimum lot.
    #
    # Micro fallback is deliberately unavailable at this account size.
    assert result.reason == (
        "MICRO_BALANCE_ABOVE_BOOTSTRAP_MAX"
    )


def test_large_account_increases_lot_instead_of_stop() -> None:

    result = plan(
        balance=1000.0,
        stop_distance=0.30,
    )

    assert result.valid is True

    assert result.risk_mode == (
        "STANDARD_COMPOUND"
    )

    # 0.75% of $1000 = $7.50
    #
    # 0.30 stop at 0.01 lot = $0.30 risk
    #
    # $7.50 / $0.30 = 25 minimum-lot units
    # = 0.25 lot.
    assert result.selected_volume == pytest.approx(
        0.25
    )

    assert result.stop_distance_price == pytest.approx(
        0.30
    )

    assert result.estimated_stop_loss_amount == pytest.approx(
        7.50
    )


def test_standard_risk_base_uses_lower_of_balance_and_equity() -> None:

    result = plan(
        balance=100.0,
        equity=80.0,
        free_margin=80.0,
        stop_distance=0.50,
    )

    assert result.valid is True

    assert result.risk_base == pytest.approx(
        80.0
    )


def test_requested_risk_above_standard_hard_cap_is_capped() -> None:

    result = plan(
        balance=1000.0,
        stop_distance=0.30,
        requested_risk_percent=2.0,
    )

    assert result.valid is True

    assert result.target_risk_percent == pytest.approx(
        1.0
    )

    assert result.hard_max_risk_percent == pytest.approx(
        1.0
    )


# =============================================================================
# $3 bootstrap
# =============================================================================


def test_three_dollar_account_can_use_micro_bootstrap() -> None:

    result = plan(
        balance=3.0,
        stop_distance=0.30,
    )

    assert result.valid is True

    assert result.risk_mode == (
        "MICRO_BOOTSTRAP"
    )

    assert result.reason == (
        "OK_MICRO_BOOTSTRAP_MIN_VOLUME"
    )

    assert result.selected_volume == pytest.approx(
        0.01
    )


def test_three_dollar_micro_stop_risk_is_ten_percent() -> None:

    result = plan(
        balance=3.0,
        stop_distance=0.30,
    )

    assert result.valid is True

    assert result.estimated_stop_loss_amount == pytest.approx(
        0.30
    )

    assert result.actual_risk_percent == pytest.approx(
        10.0
    )


def test_three_dollar_micro_margin_is_about_72_percent() -> None:

    result = plan(
        balance=3.0,
        stop_distance=0.30,
    )

    assert result.valid is True

    assert result.margin_required == pytest.approx(
        2.16
    )

    assert result.margin_percent_of_free == pytest.approx(
        72.0
    )


def test_three_dollar_040_stop_exceeds_micro_hard_risk() -> None:

    result = plan(
        balance=3.0,
        stop_distance=0.40,
    )

    assert result.valid is False

    assert result.risk_mode == (
        "MICRO_BOOTSTRAP"
    )

    assert result.reason == (
        "MICRO_MIN_VOLUME_EXCEEDS_HARD_RISK"
    )

    assert result.actual_risk_percent == pytest.approx(
        (
            0.40
            /
            3.0
        )
        *
        100.0
    )


def test_below_three_dollars_is_not_bootstrap_eligible() -> None:

    result = plan(
        balance=2.99,
        stop_distance=0.30,
    )

    assert result.valid is False

    assert result.reason == (
        "MICRO_BALANCE_BELOW_MINIMUM"
    )


# =============================================================================
# Micro growth behavior
# =============================================================================


def test_five_dollar_account_can_carry_half_dollar_stop() -> None:

    result = plan(
        balance=5.0,
        stop_distance=0.50,
    )

    assert result.valid is True

    assert result.risk_mode == (
        "MICRO_BOOTSTRAP"
    )

    assert result.selected_volume == pytest.approx(
        0.01
    )

    assert result.actual_risk_percent == pytest.approx(
        10.0
    )


def test_ten_dollar_account_can_carry_one_dollar_stop_under_micro_risk() -> None:

    result = plan(
        balance=10.0,
        stop_distance=1.00,
    )

    assert result.valid is True

    assert result.risk_mode == (
        "MICRO_BOOTSTRAP"
    )

    assert result.actual_risk_percent == pytest.approx(
        10.0
    )


def test_micro_never_increases_above_broker_minimum_lot() -> None:

    result = plan(
        balance=10.0,
        stop_distance=0.50,
    )

    # Although the account could mathematically use more than 0.01 under the
    # 12% bootstrap cap, MICRO mode intentionally stays at minimum lot.
    assert result.valid is True

    assert result.risk_mode == (
        "MICRO_BOOTSTRAP"
    )

    assert result.selected_volume == pytest.approx(
        0.01
    )


def test_micro_mode_stops_after_bootstrap_balance_range() -> None:

    result = plan(
        balance=21.0,
        stop_distance=0.50,
    )

    # $0.50 loss > standard 1% budget of $0.21.
    # Micro mode is not allowed above configured $20 bootstrap range.
    assert result.valid is False

    assert result.reason == (
        "MICRO_BALANCE_ABOVE_BOOTSTRAP_MAX"
    )


# =============================================================================
# Friction
# =============================================================================


def test_micro_records_current_spread_efficiency() -> None:

    result = plan(
        balance=3.0,
        stop_distance=0.30,
    )

    assert result.valid is True

    assert result.spread_cost == pytest.approx(
        0.26
    )

    assert result.spread_cost_to_stop_risk_ratio == pytest.approx(
        0.26
        /
        0.30
    )

    assert result.stop_risk_to_spread_cost_ratio == pytest.approx(
        0.30
        /
        0.26
    )


def test_micro_rejects_stop_that_is_too_wide_for_fast_bootstrap_friction() -> None:

    result = plan(
        balance=20.0,
        stop_distance=1.50,
    )

    # Risk:
    #
    # $1.50 / $20 = 7.5%
    #
    # which is below 12% micro hard cap.
    #
    # But:
    #
    # $1.50 / $0.26 spread = 5.77
    #
    # which exceeds micro fast-bootstrap friction ratio 4.0.
    assert result.valid is False

    assert result.reason == (
        "MICRO_STOP_TOO_WIDE_FOR_FRICTION"
    )


def test_micro_rejects_when_spread_cost_exceeds_stop_risk() -> None:

    planner = engine()

    stop_distance = 0.30

    def bad_spread(
        volume: float,
    ) -> float:

        return (
            0.40
            *
            (
                volume
                /
                0.01
            )
        )

    result = planner.plan(
        direction="LONG",
        account_balance=3.0,
        account_equity=3.0,
        free_margin=3.0,
        bid=BID,
        ask=ASK,
        stop_loss=ASK - stop_distance,
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
        spread_cost_estimator=bad_spread,
    )

    assert result.valid is False

    assert result.reason == (
        "MICRO_SPREAD_DOMINATES_STOP_RISK"
    )


# =============================================================================
# Stop geometry
# =============================================================================


def test_long_stop_inside_current_spread_is_rejected() -> None:

    result = plan(
        balance=63.35,
        stop_distance=0.25,
    )

    assert result.valid is False

    assert result.reason == (
        "STOP_NOT_BEYOND_CURRENT_BID"
    )


def test_short_stop_inside_current_spread_is_rejected() -> None:

    result = plan(
        balance=63.35,
        stop_distance=0.25,
        direction="SHORT",
    )

    assert result.valid is False

    assert result.reason == (
        "STOP_NOT_BEYOND_CURRENT_ASK"
    )


def test_long_and_short_standard_plans_are_symmetric() -> None:

    long_result = plan(
        balance=63.35,
        stop_distance=0.50,
        direction="LONG",
    )

    short_result = plan(
        balance=63.35,
        stop_distance=0.50,
        direction="SHORT",
    )

    assert long_result.valid is True
    assert short_result.valid is True

    assert (
        long_result.estimated_stop_loss_amount
        ==
        pytest.approx(
            short_result.estimated_stop_loss_amount
        )
    )

    assert (
        long_result.selected_volume
        ==
        pytest.approx(
            short_result.selected_volume
        )
    )


# =============================================================================
# Fail closed
# =============================================================================


def test_invalid_direction_fails_closed() -> None:

    planner = engine()

    result = planner.plan(
        direction="SIDEWAYS",
        account_balance=10.0,
        account_equity=10.0,
        free_margin=10.0,
        bid=BID,
        ask=ASK,
        stop_loss=ASK - 0.50,
        point=POINT,
        tick_size=TICK_SIZE,
        volume_min=VOLUME_MIN,
        volume_max=VOLUME_MAX,
        volume_step=VOLUME_STEP,
        stops_level_points=0.0,
        loss_estimator=loss_estimator(
            0.50
        ),
        margin_estimator=margin_estimator,
        spread_cost_estimator=spread_estimator,
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_DIRECTION"
    )


def test_loss_estimator_failure_fails_closed() -> None:

    planner = engine()

    result = planner.plan(
        direction="LONG",
        account_balance=10.0,
        account_equity=10.0,
        free_margin=10.0,
        bid=BID,
        ask=ASK,
        stop_loss=ASK - 0.50,
        point=POINT,
        tick_size=TICK_SIZE,
        volume_min=VOLUME_MIN,
        volume_max=VOLUME_MAX,
        volume_step=VOLUME_STEP,
        stops_level_points=0.0,
        loss_estimator=lambda volume: None,
        margin_estimator=margin_estimator,
        spread_cost_estimator=spread_estimator,
    )

    assert result.valid is False

    assert result.reason == (
        "LOSS_ESTIMATOR_FAILED"
    )


def test_margin_estimator_failure_fails_closed() -> None:

    planner = engine()

    result = planner.plan(
        direction="LONG",
        account_balance=10.0,
        account_equity=10.0,
        free_margin=10.0,
        bid=BID,
        ask=ASK,
        stop_loss=ASK - 0.50,
        point=POINT,
        tick_size=TICK_SIZE,
        volume_min=VOLUME_MIN,
        volume_max=VOLUME_MAX,
        volume_step=VOLUME_STEP,
        stops_level_points=0.0,
        loss_estimator=loss_estimator(
            0.50
        ),
        margin_estimator=lambda volume: None,
        spread_cost_estimator=spread_estimator,
    )

    assert result.valid is False

    assert result.reason == (
        "MARGIN_ESTIMATOR_FAILED"
    )