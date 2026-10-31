"""
Offline tests for RiskModeBasketReconciliationEngine v1.0.
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace
from typing import Any

import pytest


pytestmark = pytest.mark.offline


planner_module: Any = importlib.import_module(
    "02_AI.Shadow.bootstrap_compounding_planner"
)

module: Any = importlib.import_module(
    "02_AI.Shadow.risk_mode_basket_reconciliation"
)


Policy: Any = (
    planner_module.BootstrapCompoundingPolicy
)

Engine: Any = (
    module.RiskModeBasketReconciliationEngine
)


def policy() -> Any:

    return Policy(
        compounding_enabled=True,
        allow_initial_multi_leg=False,
        max_simultaneous_legs=3,
        max_total_volume=0.03,
        bootstrap_balance_max=20.0,
        bootstrap_loss_budget_floor_usd=0.50,
        bootstrap_loss_budget_percent=16.67,
        bootstrap_loss_budget_ceiling_usd=2.00,
        bootstrap_margin_cap_percent=85.0,
        standard_basket_hard_loss_percent=2.00,
        standard_margin_cap_percent=35.0,
        max_total_spread_to_basket_loss_ratio=1.00,
        add_only_after_profit=True,
        minimum_profit_r_before_add=0.25,
        partial_booking_enabled=True,
        partial_booking_r=0.75,
        partial_booking_fraction=0.50,
        trail_enabled=True,
        trail_start_r=0.50,
        runner_r=1.25,
    )


def engine() -> Any:

    return Engine(
        policy()
    )


def admission(
    *,
    risk_mode: str = "STANDARD_COMPOUND",
    risk_base: float = 100.0,
    equity: float | None = None,
    basket_mode: str = "STANDARD_COMPOUND_BASKET",
    total_loss: float = 1.00,
    total_margin: float = 10.00,
    total_spread: float = 0.50,
    admission_valid: bool = True,
    admitted: bool = True,
    risk_valid: bool = True,
    account_valid: bool = True,
    basket_valid: bool = True,
    admission_live: bool = False,
    risk_live: bool = False,
    account_live: bool = False,
    basket_live: bool = False,
) -> Any:

    resolved_equity = (
        risk_base
        if equity is None
        else equity
    )

    basket_plan = SimpleNamespace(
        valid=basket_valid,
        basket_mode=basket_mode,
        total_projected_loss=total_loss,
        total_margin=total_margin,
        total_spread_cost=total_spread,
        live_authorized=basket_live,
    )

    account_plan = SimpleNamespace(
        valid=account_valid,
        live_authorized=account_live,
        basket_plan=basket_plan,
    )

    risk_plan = SimpleNamespace(
        valid=risk_valid,
        risk_mode=risk_mode,
        risk_base=risk_base,
        equity=resolved_equity,
        live_authorized=risk_live,
    )

    return SimpleNamespace(
        valid=admission_valid,
        admitted=admitted,
        reason=(
            "OK_EXECUTION_AWARE_COMPOUNDING_ADMISSION"
            if admission_valid and admitted
            else "EXECUTION_FRICTION_BLOCKED"
        ),
        live_authorized=admission_live,
        risk_plan=risk_plan,
        account_plan=account_plan,
    )


def test_reconciliation_is_shadow_only() -> None:

    result = engine().evaluate(
        admission_result=admission()
    )

    assert result.valid is True

    assert result.reconciled is True

    assert result.live_authorized is False

    assert result.mode == (
        "SHADOW_RISK_MODE_BASKET_RECONCILIATION_ONLY"
    )


def test_normal_standard_basket_uses_standard_caps() -> None:

    result = engine().evaluate(
        admission_result=admission(
            risk_mode="STANDARD_COMPOUND",
            risk_base=100.0,
            equity=100.0,
            basket_mode="STANDARD_COMPOUND_BASKET",
            total_loss=1.50,
            total_margin=20.0,
            total_spread=0.50,
        )
    )

    assert result.reconciled is True

    assert result.regime_override_required is False

    assert result.effective_loss_cap == pytest.approx(
        2.00
    )

    assert result.effective_loss_cap_percent == pytest.approx(
        2.00
    )

    assert result.effective_margin_cap_amount == pytest.approx(
        35.0
    )

    assert result.effective_margin_cap_percent == pytest.approx(
        35.0
    )


def test_standard_single_leg_hard_cap_does_not_replace_basket_cap() -> None:

    result = engine().evaluate(
        admission_result=admission(
            risk_mode="STANDARD_COMPOUND",
            risk_base=100.0,
            total_loss=1.50,
            total_margin=10.0,
            total_spread=0.25,
        )
    )

    assert result.total_projected_loss_percent == pytest.approx(
        1.50
    )

    assert result.effective_loss_cap_percent == pytest.approx(
        2.00
    )

    assert result.reconciled is True


def test_standard_risk_mode_can_override_balance_selected_bootstrap_label() -> None:

    result = engine().evaluate(
        admission_result=admission(
            risk_mode="STANDARD_COMPOUND",
            risk_base=20.0,
            equity=20.0,
            basket_mode="MICRO_BOOTSTRAP_BASKET",
            total_loss=0.30,
            total_margin=3.0,
            total_spread=0.10,
        )
    )

    assert result.valid is True

    assert result.reconciled is True

    assert result.regime_override_required is True

    assert result.planner_basket_mode == (
        "MICRO_BOOTSTRAP_BASKET"
    )

    assert result.effective_basket_mode == (
        "STANDARD_COMPOUND_BASKET"
    )

    assert result.effective_loss_cap == pytest.approx(
        0.40
    )

    assert result.reason == (
        "OK_RISK_MODE_BASKET_RECONCILIATION_OVERRIDE"
    )


def test_standard_override_blocks_bootstrap_accepted_loss_above_standard_cap() -> None:

    result = engine().evaluate(
        admission_result=admission(
            risk_mode="STANDARD_COMPOUND",
            risk_base=20.0,
            equity=20.0,
            basket_mode="MICRO_BOOTSTRAP_BASKET",
            total_loss=0.50,
            total_margin=3.0,
            total_spread=0.10,
        )
    )

    assert result.valid is True

    assert result.reconciled is False

    assert result.regime_override_required is True

    assert result.reason == (
        "BASKET_LOSS_EXCEEDS_RISK_MODE_CAP"
    )


def test_standard_override_blocks_margin_above_standard_basket_cap() -> None:

    result = engine().evaluate(
        admission_result=admission(
            risk_mode="STANDARD_COMPOUND",
            risk_base=20.0,
            equity=20.0,
            basket_mode="MICRO_BOOTSTRAP_BASKET",
            total_loss=0.30,
            total_margin=7.01,
            total_spread=0.10,
        )
    )

    assert result.reconciled is False

    assert result.effective_margin_cap_amount == pytest.approx(
        7.0
    )

    assert result.reason == (
        "BASKET_MARGIN_EXCEEDS_RISK_MODE_CAP"
    )


def test_standard_override_blocks_spread_above_effective_loss_cap_ratio() -> None:

    result = engine().evaluate(
        admission_result=admission(
            risk_mode="STANDARD_COMPOUND",
            risk_base=20.0,
            equity=20.0,
            basket_mode="MICRO_BOOTSTRAP_BASKET",
            total_loss=0.30,
            total_margin=3.0,
            total_spread=0.41,
        )
    )

    assert result.reconciled is False

    assert result.effective_loss_cap == pytest.approx(
        0.40
    )

    assert (
        result.spread_to_effective_loss_cap_ratio
        ==
        pytest.approx(
            1.025
        )
    )

    assert result.reason == (
        "BASKET_SPREAD_EXCEEDS_RISK_MODE_CAP"
    )


def test_micro_uses_bootstrap_floor_percent_ceiling_formula() -> None:

    result = engine().evaluate(
        admission_result=admission(
            risk_mode="MICRO_BOOTSTRAP",
            risk_base=10.0,
            equity=10.0,
            basket_mode="MICRO_BOOTSTRAP_BASKET",
            total_loss=1.00,
            total_margin=4.0,
            total_spread=0.50,
        )
    )

    assert result.reconciled is True

    assert result.regime_override_required is False

    assert result.effective_loss_cap == pytest.approx(
        1.667
    )

    assert result.effective_loss_cap_percent == pytest.approx(
        16.67
    )

    assert result.effective_margin_cap_amount == pytest.approx(
        8.50
    )


def test_micro_floor_is_preserved_at_small_balance() -> None:

    result = engine().evaluate(
        admission_result=admission(
            risk_mode="MICRO_BOOTSTRAP",
            risk_base=3.0,
            equity=3.0,
            basket_mode="MICRO_BOOTSTRAP_BASKET",
            total_loss=0.40,
            total_margin=2.0,
            total_spread=0.20,
        )
    )

    assert result.reconciled is True

    assert result.effective_loss_cap == pytest.approx(
        0.5001
    )


def test_micro_risk_mode_outside_bootstrap_range_fails_closed() -> None:

    result = engine().evaluate(
        admission_result=admission(
            risk_mode="MICRO_BOOTSTRAP",
            risk_base=21.0,
            equity=21.0,
            basket_mode="STANDARD_COMPOUND_BASKET",
            total_loss=0.30,
            total_margin=3.0,
            total_spread=0.10,
        )
    )

    assert result.valid is False

    assert result.reconciled is False

    assert result.reason == (
        "MICRO_RISK_MODE_OUTSIDE_BOOTSTRAP_RANGE"
    )


def test_micro_mode_can_reconcile_mismatched_planner_label_when_inside_range() -> None:

    result = engine().evaluate(
        admission_result=admission(
            risk_mode="MICRO_BOOTSTRAP",
            risk_base=10.0,
            equity=10.0,
            basket_mode="STANDARD_COMPOUND_BASKET",
            total_loss=1.00,
            total_margin=4.0,
            total_spread=0.50,
        )
    )

    assert result.valid is True

    assert result.reconciled is True

    assert result.regime_override_required is True

    assert result.effective_basket_mode == (
        "MICRO_BOOTSTRAP_BASKET"
    )


def test_rejected_execution_admission_is_not_reconciled() -> None:

    result = engine().evaluate(
        admission_result=admission(
            admission_valid=False,
            admitted=False,
        )
    )

    assert result.valid is False

    assert result.reconciled is False

    assert result.reason == (
        "EXECUTION_ADMISSION_REJECTED"
    )


def test_unknown_risk_mode_fails_closed() -> None:

    result = engine().evaluate(
        admission_result=admission(
            risk_mode="UNKNOWN_MODE",
        )
    )

    assert result.valid is False

    assert result.reconciled is False

    assert result.reason == (
        "UNKNOWN_RISK_MODE"
    )


def test_nested_live_authorization_is_refused() -> None:

    result = engine().evaluate(
        admission_result=admission(
            basket_live=True
        )
    )

    assert result.valid is False

    assert result.reconciled is False

    assert result.reason == (
        "NESTED_LIVE_AUTHORIZATION_NOT_ALLOWED"
    )


def test_invalid_basket_shape_fails_closed() -> None:

    malformed = admission()

    malformed.account_plan.basket_plan = SimpleNamespace(
        valid=True
    )

    result = engine().evaluate(
        admission_result=malformed
    )

    assert result.valid is False

    assert result.reconciled is False

    assert result.reason == (
        "INVALID_BASKET_PLAN_SHAPE"
    )