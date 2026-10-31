"""
Offline tests for ExecutionFrictionModel v1.0.
"""

from __future__ import annotations

import importlib
from typing import Any

import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Shadow.execution_friction_model"
)


Policy: Any = (
    module.ExecutionFrictionPolicy
)

Model: Any = (
    module.ExecutionFrictionModel
)


def model(
    **policy_overrides: float,
) -> Any:

    return Model(
        Policy(
            **policy_overrides
        )
    )


def assess(
    engine: Any,
    **overrides: float | str,
) -> Any:

    values: dict[
        str,
        float | str,
    ] = {
        "direction": "LONG",
        "volume": 0.01,
        "balance": 63.35,
        "equity": 63.35,
        "hard_loss_budget": 0.90,
        "entry_price": 4316.729,
        "stop_loss": 4316.229,
        "point": 0.001,
        "spread_price": 0.26,
        "spread_cost": 0.26,
        "projected_stop_loss": 0.50,
        "estimated_slippage_price": 0.03,
        "estimated_slippage_cost": 0.03,
        "estimated_commission_cost": 0.00,
    }

    values.update(
        overrides
    )

    return engine.evaluate(
        **values
    )


def test_model_is_shadow_only() -> None:

    result = assess(
        model()
    )

    assert result.valid is True

    assert result.live_authorized is False

    assert result.mode == (
        "SHADOW_EXECUTION_FRICTION_RESEARCH_ONLY"
    )


def test_exness_style_spread_ratio_is_measured_against_structural_stop() -> None:

    result = assess(
        model()
    )

    assert result.stop_distance_price == pytest.approx(
        0.50
    )

    assert result.stop_distance_points == pytest.approx(
        500.0
    )

    assert result.spread_points == pytest.approx(
        260.0
    )

    assert result.spread_to_stop_distance_ratio == pytest.approx(
        0.52
    )


def test_feasible_case_includes_spread_slippage_and_commission() -> None:

    result = assess(
        model(),
        estimated_commission_cost=0.04,
        hard_loss_budget=0.90,
    )

    assert result.execution_feasible is True

    assert result.reason == (
        "PASS"
    )

    assert result.total_friction_cost == pytest.approx(
        0.33
    )

    assert result.all_in_adverse_loss == pytest.approx(
        0.83
    )

    assert result.total_friction_to_stop_risk_ratio == pytest.approx(
        0.66
    )


def test_tight_stop_can_fail_even_when_absolute_spread_is_unchanged() -> None:

    result = assess(
        model(),
        stop_loss=4316.329,
        projected_stop_loss=0.40,
        hard_loss_budget=1.00,
    )

    assert result.valid is True

    assert result.execution_feasible is False

    assert result.spread_to_stop_distance_ratio == pytest.approx(
        0.65
    )

    assert (
        "SPREAD_DOMINATES_STRUCTURAL_STOP"
        in
        result.violations
    )


def test_slippage_can_independently_make_execution_infeasible() -> None:

    result = assess(
        model(),
        estimated_slippage_price=0.11,
        estimated_slippage_cost=0.05,
        hard_loss_budget=1.00,
    )

    assert result.execution_feasible is False

    assert result.slippage_to_stop_distance_ratio == pytest.approx(
        0.22
    )

    assert (
        "SLIPPAGE_DOMINATES_STRUCTURAL_STOP"
        in
        result.violations
    )


def test_total_friction_can_dominate_stop_risk() -> None:

    result = assess(
        model(),
        estimated_slippage_price=0.05,
        estimated_slippage_cost=0.10,
        estimated_commission_cost=0.05,
        hard_loss_budget=1.20,
    )

    assert result.total_friction_cost == pytest.approx(
        0.41
    )

    assert result.total_friction_to_stop_risk_ratio == pytest.approx(
        0.82
    )

    assert result.execution_feasible is False

    assert (
        "TOTAL_FRICTION_DOMINATES_STOP_RISK"
        in
        result.violations
    )


def test_all_in_loss_must_fit_hard_loss_budget() -> None:

    engine = model(
        max_spread_to_stop_distance_ratio=1.0,
        max_slippage_to_stop_distance_ratio=1.0,
        max_total_friction_to_stop_risk_ratio=1.0,
        max_all_in_loss_to_budget_ratio=1.0,
    )

    result = assess(
        engine,
        estimated_slippage_price=0.00,
        estimated_slippage_cost=0.00,
        hard_loss_budget=0.70,
    )

    assert result.all_in_adverse_loss == pytest.approx(
        0.76
    )

    assert result.all_in_loss_to_budget_ratio == pytest.approx(
        0.76
        /
        0.70
    )

    assert result.execution_feasible is False

    assert (
        "ALL_IN_LOSS_EXCEEDS_HARD_BUDGET"
        in
        result.violations
    )


def test_risk_base_uses_lower_of_balance_and_equity() -> None:

    result = assess(
        model(),
        balance=100.0,
        equity=80.0,
        hard_loss_budget=1.00,
    )

    assert result.risk_base == pytest.approx(
        80.0
    )

    assert result.projected_stop_loss_percent_of_risk_base == pytest.approx(
        0.625
    )


def test_short_alias_is_normalized_without_changing_stop_geometry() -> None:

    result = assess(
        model(),
        direction="SELL",
        entry_price=4316.469,
        stop_loss=4316.969,
    )

    assert result.direction == (
        "SHORT"
    )

    assert result.stop_distance_price == pytest.approx(
        0.50
    )


def test_invalid_direction_is_rejected() -> None:

    result = assess(
        model(),
        direction="SIDEWAYS",
    )

    assert result.valid is False

    assert result.execution_feasible is False

    assert result.reason == (
        "INVALID_DIRECTION"
    )

    assert result.live_authorized is False


def test_negative_friction_cost_is_rejected() -> None:

    result = assess(
        model(),
        estimated_slippage_cost=-0.01,
    )

    assert result.valid is False

    assert result.reason == (
        "NEGATIVE_ESTIMATED_SLIPPAGE_COST"
    )


def test_zero_structural_stop_distance_is_rejected() -> None:

    result = assess(
        model(),
        stop_loss=4316.729,
    )

    assert result.valid is False

    assert result.reason == (
        "ZERO_STRUCTURAL_STOP_DISTANCE"
    )