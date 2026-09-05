"""
Offline tests for BrokerExecutionStressMatrix v1.0.
"""

from __future__ import annotations

import importlib
from typing import Any

import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Shadow.broker_execution_stress_matrix"
)

Matrix: Any = module.BrokerExecutionStressMatrix
SingleScenario: Any = module.BrokerExecutionStressScenario
AddonScenario: Any = module.AddonStressScenario
ProtectionScenario: Any = module.ProtectionStressScenario
ProtectionCloseEvent: Any = module.ProtectionCloseEvent


def matrix() -> Any:
    return Matrix()


def by_id(rows: tuple[Any, ...], scenario_id: str) -> Any:
    matches = [
        row
        for row in rows
        if row.scenario_id == scenario_id
    ]
    assert len(matches) == 1
    return matches[0]


# =============================================================================
# Shadow / suite coverage
# =============================================================================


def test_matrix_is_shadow_only() -> None:
    engine = matrix()
    result = engine.evaluate_default_suite()

    assert engine.VERSION == "1.0"
    assert engine.MODE == "SHADOW_BROKER_EXECUTION_STRESS_MATRIX_ONLY"
    assert result.valid is True
    assert result.live_authorized is False
    assert result.shadow_boundary_intact is True


def test_default_suite_has_complete_expected_row_count() -> None:
    result = matrix().evaluate_default_suite()

    # 20 spread/stop grid
    # + 7 transition rows
    # + 5 account rows
    # + 8 fail-closed rows
    # + 12 add-on rows
    # + 8 protection rows
    assert result.total_rows == 60


def test_default_market_grid_covers_all_spread_stop_pairs() -> None:
    rows = matrix().spread_stop_grid()

    assert len(rows) == 20

    observed = {
        (
            row.spread_points,
            row.stop_distance_price,
        )
        for row in rows
    }

    expected = {
        (spread, stop)
        for spread in (200.0, 260.0, 350.0, 500.0)
        for stop in (0.30, 0.40, 0.50, 0.60, 1.00)
    }

    assert observed == expected


def test_market_grid_never_mutates_observable_structural_stop() -> None:
    rows = matrix().spread_stop_grid()

    assert all(
        (
            not row.structural_stop_observable
            or row.structural_stop_preserved
        )
        for row in rows
    )

    assert all(
        row.structural_stop_preserved
        for row in rows
        if row.risk_valid
    )


def test_all_default_rows_remain_live_unauthorized() -> None:
    result = matrix().evaluate_default_suite()

    single_rows = (
        result.market_grid
        + result.transition_matrix
        + result.account_matrix
        + result.fail_closed_matrix
    )

    assert all(
        row.live_authorized is False
        and row.shadow_boundary_intact
        for row in single_rows
    )

    assert all(
        row.live_authorized is False
        and row.shadow_boundary_intact
        for row in result.addon_matrix
    )

    assert all(
        row.live_authorized is False
        and row.shadow_boundary_intact
        for row in result.protection_matrix
    )


# =============================================================================
# Spread / stop stress grid
# =============================================================================


def test_spread_200_stop_030_is_risk_valid_but_friction_blocked() -> None:
    row = matrix().evaluate_single(
        SingleScenario(
            scenario_id="S200_D030",
            balance=63.35,
            equity=63.35,
            free_margin=63.35,
            spread_points=200.0,
            stop_distance_price=0.30,
        )
    )

    assert row.risk_valid is True
    assert row.risk_mode == "STANDARD_COMPOUND"
    assert row.friction_invoked is True
    assert row.execution_feasible is False
    assert "SPREAD_DOMINATES_STRUCTURAL_STOP" in row.friction_violations
    assert row.final_new_exposure_feasible is False


def test_spread_200_stop_040_can_pass_full_new_exposure_stack() -> None:
    row = matrix().evaluate_single(
        SingleScenario(
            scenario_id="S200_D040",
            balance=63.35,
            equity=63.35,
            free_margin=63.35,
            spread_points=200.0,
            stop_distance_price=0.40,
        )
    )

    assert row.risk_valid is True
    assert row.execution_feasible is True
    assert row.admitted is True
    assert row.reconciled is True
    assert row.final_new_exposure_feasible is True


def test_spread_260_stop_040_is_blocked_by_structural_friction() -> None:
    row = matrix().evaluate_single(
        SingleScenario(
            scenario_id="S260_D040",
            balance=63.35,
            equity=63.35,
            free_margin=63.35,
            spread_points=260.0,
            stop_distance_price=0.40,
        )
    )

    assert row.risk_valid is True
    assert row.execution_feasible is False
    assert row.spread_to_stop_distance_ratio == pytest.approx(0.65)
    assert "SPREAD_DOMINATES_STRUCTURAL_STOP" in row.friction_violations


def test_spread_260_stop_050_is_blocked_by_all_in_budget() -> None:
    row = matrix().evaluate_single(
        SingleScenario(
            scenario_id="S260_D050",
            balance=63.35,
            equity=63.35,
            free_margin=63.35,
            spread_points=260.0,
            stop_distance_price=0.50,
        )
    )

    assert row.risk_valid is True
    assert row.risk_mode == "STANDARD_COMPOUND"
    assert row.spread_to_stop_distance_ratio == pytest.approx(0.52)
    assert row.execution_feasible is False
    assert "ALL_IN_LOSS_EXCEEDS_HARD_BUDGET" in row.friction_violations
    assert row.all_in_adverse_loss == pytest.approx(0.76)


def test_spread_350_stop_030_fails_broker_stop_geometry() -> None:
    row = matrix().evaluate_single(
        SingleScenario(
            scenario_id="S350_D030",
            balance=63.35,
            equity=63.35,
            free_margin=63.35,
            spread_points=350.0,
            stop_distance_price=0.30,
        )
    )

    assert row.risk_valid is False
    assert row.risk_reason == "STOP_NOT_BEYOND_CURRENT_BID"
    assert row.admission_invoked is False
    assert row.final_new_exposure_feasible is False


def test_spread_500_stop_050_fails_broker_stop_geometry() -> None:
    row = matrix().evaluate_single(
        SingleScenario(
            scenario_id="S500_D050",
            balance=63.35,
            equity=63.35,
            free_margin=63.35,
            spread_points=500.0,
            stop_distance_price=0.50,
        )
    )

    assert row.risk_valid is False
    assert row.risk_reason == "STOP_NOT_BEYOND_CURRENT_BID"


def test_spread_500_stop_060_reaches_friction_and_is_blocked() -> None:
    row = matrix().evaluate_single(
        SingleScenario(
            scenario_id="S500_D060",
            balance=63.35,
            equity=63.35,
            free_margin=63.35,
            spread_points=500.0,
            stop_distance_price=0.60,
        )
    )

    assert row.risk_valid is True
    assert row.friction_invoked is True
    assert row.execution_feasible is False
    assert row.spread_to_stop_distance_ratio == pytest.approx(
        0.5 / 0.6
    )


def test_one_dollar_stop_is_not_forced_to_fit_63_account() -> None:
    row = matrix().evaluate_single(
        SingleScenario(
            scenario_id="STOP_100",
            balance=63.35,
            equity=63.35,
            free_margin=63.35,
            spread_points=260.0,
            stop_distance_price=1.00,
        )
    )

    assert row.risk_valid is False
    assert row.risk_reason == "MICRO_BALANCE_ABOVE_BOOTSTRAP_MAX"
    assert row.structural_stop_observable is False
    assert row.stop_distance_price == pytest.approx(1.00)
    assert row.selected_volume == pytest.approx(0.0)


# =============================================================================
# MICRO / STANDARD transitions and <= $20 STANDARD cases
# =============================================================================


def test_three_dollar_micro_can_be_risk_valid_but_execution_blocked() -> None:
    rows = matrix().default_transition_matrix()
    row = by_id(rows, "MICRO_3_STOP_030")

    assert row.risk_valid is True
    assert row.risk_mode == "MICRO_BOOTSTRAP"
    assert row.execution_feasible is False
    assert "ALL_IN_LOSS_EXCEEDS_HARD_BUDGET" in row.friction_violations
    assert row.final_new_exposure_feasible is False


def test_twenty_dollar_micro_stop_030_can_pass_full_stack() -> None:
    rows = matrix().default_transition_matrix()
    row = by_id(rows, "MICRO_20_STOP_030")

    assert row.risk_valid is True
    assert row.risk_mode == "MICRO_BOOTSTRAP"
    assert row.execution_feasible is True
    assert row.admitted is True
    assert row.reconciled is True
    assert row.effective_basket_mode == "MICRO_BOOTSTRAP_BASKET"
    assert row.final_new_exposure_feasible is True


def test_standard_mode_can_be_selected_at_ten_dollars() -> None:
    rows = matrix().default_transition_matrix()
    row = by_id(rows, "STANDARD_10_STOP_010_FRICTION_BLOCK")

    assert row.risk_valid is True
    assert row.risk_mode == "STANDARD_COMPOUND"
    assert row.selected_volume == pytest.approx(0.01)
    assert row.execution_feasible is False
    assert row.final_new_exposure_feasible is False


def test_standard_mode_at_twenty_dollars_reconciles_micro_planner_label() -> None:
    rows = matrix().default_transition_matrix()
    row = by_id(rows, "STANDARD_20_STOP_010_OVERRIDE_PASS")

    assert row.risk_valid is True
    assert row.risk_mode == "STANDARD_COMPOUND"
    assert row.planner_basket_mode == "MICRO_BOOTSTRAP_BASKET"
    assert row.reconciliation_invoked is True
    assert row.reconciled is True
    assert row.regime_override_required is True
    assert row.effective_basket_mode == "STANDARD_COMPOUND_BASKET"
    assert row.final_new_exposure_feasible is True


def test_balance_21_can_fall_into_mode_transition_gap_for_stop_030() -> None:
    rows = matrix().default_transition_matrix()
    row = by_id(rows, "TRANSITION_GAP_21_STOP_030")

    assert row.risk_valid is False
    assert row.risk_reason == "MICRO_BALANCE_ABOVE_BOOTSTRAP_MAX"
    assert row.admission_invoked is False


def test_standard_risk_threshold_can_still_fail_execution_cost_at_30() -> None:
    rows = matrix().default_transition_matrix()
    row = by_id(rows, "STANDARD_RISK_30_EXECUTION_BLOCK")

    assert row.risk_valid is True
    assert row.risk_mode == "STANDARD_COMPOUND"
    assert row.execution_feasible is False
    assert "ALL_IN_LOSS_EXCEEDS_HARD_BUDGET" in row.friction_violations


def test_standard_stop_030_passes_full_stack_at_35_with_low_spread() -> None:
    rows = matrix().default_transition_matrix()
    row = by_id(rows, "STANDARD_EXECUTION_35_PASS")

    assert row.risk_valid is True
    assert row.risk_mode == "STANDARD_COMPOUND"
    assert row.execution_feasible is True
    assert row.admitted is True
    assert row.reconciled is True
    assert row.final_new_exposure_feasible is True


# =============================================================================
# Account state stress
# =============================================================================


def test_balance_equity_divergence_uses_lower_risk_base() -> None:
    rows = matrix().default_account_matrix()
    row = by_id(rows, "EQUITY_DIVERGENCE")

    assert row.risk_valid is True
    assert row.risk_plan.risk_base == pytest.approx(80.0)
    assert row.final_new_exposure_feasible is True


def test_low_free_margin_blocks_standard_before_admission() -> None:
    rows = matrix().default_account_matrix()
    row = by_id(rows, "LOW_MARGIN_STANDARD_BLOCK")

    assert row.risk_valid is False
    assert row.risk_reason == "MICRO_BALANCE_ABOVE_BOOTSTRAP_MAX"
    assert row.admission_invoked is False


def test_low_free_margin_blocks_micro_on_micro_margin_cap() -> None:
    rows = matrix().default_account_matrix()
    row = by_id(rows, "LOW_MARGIN_MICRO_BLOCK")

    assert row.risk_valid is False
    assert row.risk_mode == "MICRO_BOOTSTRAP"
    assert row.risk_reason == "MICRO_MIN_VOLUME_EXCEEDS_MARGIN_CAP"


def test_current_63_style_260_spread_050_stop_is_execution_blocked() -> None:
    rows = matrix().default_account_matrix()
    row = by_id(rows, "CURRENT_BROKER_STYLE_63_SPREAD260_STOP050")

    assert row.risk_valid is True
    assert row.risk_mode == "STANDARD_COMPOUND"
    assert row.raw_spread_cost == pytest.approx(0.26)
    assert row.execution_feasible is False
    assert row.admission_reason == "EXECUTION_FRICTION_BLOCKED"
    assert row.reconciliation_invoked is False


def test_standard_volume_growth_can_hit_basket_total_volume_cap() -> None:
    rows = matrix().default_account_matrix()
    row = by_id(rows, "STANDARD_VOLUME_GROWTH_BASKET_CAP")

    assert row.risk_valid is True
    assert row.risk_mode == "STANDARD_COMPOUND"
    assert row.selected_volume == pytest.approx(0.25)
    assert row.execution_feasible is True
    assert row.admitted is False
    assert row.account_reason == "NO_NEW_LEG_FITS_BASKET_LIMITS"
    assert row.final_new_exposure_feasible is False


# =============================================================================
# Fail-closed estimator / input behavior
# =============================================================================


@pytest.mark.parametrize(
    ("scenario_id", "reason"),
    (
        ("FAIL_INVALID_DIRECTION", "INVALID_DIRECTION"),
        ("FAIL_LOSS_ESTIMATOR", "LOSS_ESTIMATOR_FAILED"),
        ("FAIL_MARGIN_ESTIMATOR", "MARGIN_ESTIMATOR_FAILED"),
        ("FAIL_SPREAD_ESTIMATOR", "SPREAD_ESTIMATOR_FAILED"),
        ("FAIL_ZERO_EQUITY", "INVALID_ACCOUNT_STATE"),
        ("FAIL_ZERO_FREE_MARGIN", "INVALID_ACCOUNT_STATE"),
        ("FAIL_NEGATIVE_REQUESTED_RISK", "INVALID_REQUESTED_RISK"),
        ("FAIL_NEGATIVE_SPREAD", "INVALID_MARKET_STATE"),
    ),
)
def test_fail_closed_matrix_rejects_before_downstream(
    scenario_id: str,
    reason: str,
) -> None:
    rows = matrix().default_fail_closed_matrix()
    row = by_id(rows, scenario_id)

    assert row.risk_valid is False
    assert row.risk_reason == reason
    assert row.admission_invoked is False
    assert row.reconciliation_invoked is False
    assert row.final_new_exposure_feasible is False
    assert row.live_authorized is False


# =============================================================================
# Add-on stress
# =============================================================================


def test_addon_at_exact_profit_threshold_can_pass() -> None:
    rows = matrix().default_addon_matrix()
    row = by_id(rows, "ADD_PASS_AT_025R")

    assert row.risk_valid is True
    assert row.admitted is True
    assert row.reconciled is True
    assert row.final_addon_feasible is True
    assert row.planner_total_legs == 2
    assert row.planner_total_volume == pytest.approx(0.02)


def test_addon_below_profit_threshold_is_blocked() -> None:
    rows = matrix().default_addon_matrix()
    row = by_id(rows, "ADD_BLOCK_BELOW_025R")

    assert row.risk_valid is True
    assert row.admitted is False
    assert row.account_reason == "ADD_REQUIRES_EXISTING_PROFIT"
    assert row.reconciliation_invoked is False


def test_addon_max_leg_count_is_enforced() -> None:
    rows = matrix().default_addon_matrix()
    row = by_id(rows, "ADD_BLOCK_MAX_LEGS")

    assert row.admitted is False
    assert row.account_reason == "NO_NEW_LEG_FITS_BASKET_LIMITS"
    assert row.final_addon_feasible is False


def test_addon_max_total_volume_is_enforced() -> None:
    rows = matrix().default_addon_matrix()
    row = by_id(rows, "ADD_BLOCK_MAX_VOLUME")

    assert row.admitted is False
    assert row.account_reason == "NO_NEW_LEG_FITS_BASKET_LIMITS"


def test_addon_standard_basket_loss_cap_is_enforced() -> None:
    rows = matrix().default_addon_matrix()
    row = by_id(rows, "ADD_BLOCK_STANDARD_BASKET_LOSS")

    assert row.admitted is False
    assert row.account_reason == "NO_NEW_LEG_FITS_BASKET_LIMITS"


def test_addon_standard_basket_margin_cap_is_enforced() -> None:
    rows = matrix().default_addon_matrix()
    row = by_id(rows, "ADD_BLOCK_STANDARD_BASKET_MARGIN")

    assert row.admitted is False
    assert row.account_reason == "NO_NEW_LEG_FITS_BASKET_LIMITS"


def test_addon_standard_basket_spread_cap_is_enforced() -> None:
    rows = matrix().default_addon_matrix()
    row = by_id(rows, "ADD_BLOCK_STANDARD_BASKET_SPREAD")

    assert row.admitted is False
    assert row.account_reason == "NO_NEW_LEG_FITS_BASKET_LIMITS"


def test_addon_direction_mismatch_is_enforced() -> None:
    rows = matrix().default_addon_matrix()
    row = by_id(rows, "ADD_BLOCK_DIRECTION_MISMATCH")

    assert row.admitted is False
    assert row.account_reason == "NO_NEW_LEG_FITS_BASKET_LIMITS"


def test_small_standard_addon_can_reconcile_bootstrap_planner_label() -> None:
    rows = matrix().default_addon_matrix()
    row = by_id(rows, "ADD_SMALL_STANDARD_OVERRIDE_PASS")

    assert row.risk_mode == "STANDARD_COMPOUND"
    assert row.admitted is True
    assert row.planner_basket_mode == "MICRO_BOOTSTRAP_BASKET"
    assert row.reconciled is True
    assert row.regime_override_required is True
    assert row.effective_basket_mode == "STANDARD_COMPOUND_BASKET"
    assert row.effective_loss_cap == pytest.approx(0.40)
    assert row.final_addon_feasible is True


def test_reconciliation_blocks_small_standard_basket_using_standard_cap() -> None:
    rows = matrix().default_addon_matrix()
    row = by_id(rows, "ADD_SMALL_STANDARD_RECONCILIATION_BLOCK")

    assert row.risk_mode == "STANDARD_COMPOUND"
    assert row.admitted is True
    assert row.planner_basket_mode == "MICRO_BOOTSTRAP_BASKET"
    assert row.reconciliation_invoked is True
    assert row.reconciled is False
    assert row.reconciliation_reason == "BASKET_LOSS_EXCEEDS_RISK_MODE_CAP"
    assert row.effective_loss_cap == pytest.approx(0.40)
    assert row.final_addon_feasible is False


def test_reconciliation_blocks_small_standard_basket_margin_using_standard_cap() -> None:
    rows = matrix().default_addon_matrix()
    row = by_id(rows, "ADD_SMALL_STANDARD_RECONCILIATION_MARGIN_BLOCK")

    assert row.risk_mode == "STANDARD_COMPOUND"
    assert row.admitted is True
    assert row.planner_basket_mode == "MICRO_BOOTSTRAP_BASKET"
    assert row.reconciled is False
    assert row.reconciliation_reason == "BASKET_MARGIN_EXCEEDS_RISK_MODE_CAP"
    assert row.effective_margin_cap_amount == pytest.approx(7.0)
    assert row.final_addon_feasible is False


def test_reconciliation_blocks_small_standard_basket_spread_using_standard_cap() -> None:
    rows = matrix().default_addon_matrix()
    row = by_id(rows, "ADD_SMALL_STANDARD_RECONCILIATION_SPREAD_BLOCK")

    assert row.risk_mode == "STANDARD_COMPOUND"
    assert row.admitted is True
    assert row.planner_basket_mode == "MICRO_BOOTSTRAP_BASKET"
    assert row.reconciled is False
    assert row.reconciliation_reason == "BASKET_SPREAD_EXCEEDS_RISK_MODE_CAP"
    assert row.effective_loss_cap == pytest.approx(0.40)
    assert row.final_addon_feasible is False


# =============================================================================
# Account protection stress
# =============================================================================


def test_drawdown_just_below_ten_percent_remains_allowed() -> None:
    rows = matrix().default_protection_matrix()
    row = by_id(rows, "DD_BELOW_LOCK")

    assert row.assessment_valid is True
    assert row.current_drawdown_percent == pytest.approx(9.99)
    assert row.hard_locked is False
    assert row.exposure_allowed is True


def test_drawdown_at_ten_percent_hard_locks() -> None:
    rows = matrix().default_protection_matrix()
    row = by_id(rows, "DD_AT_LOCK")

    assert row.current_drawdown_percent == pytest.approx(10.0)
    assert row.hard_locked is True
    assert row.hard_lock_reason == "PEAK_DRAWDOWN_LIMIT_REACHED"
    assert row.exposure_allowed is False
    assert row.assessment_reason == "HARD_DRAWDOWN_LOCK"


def test_drawdown_is_measured_from_new_peak_not_starting_equity() -> None:
    rows = matrix().default_protection_matrix()
    row = by_id(rows, "PEAK_BASED_DD_LOCK")

    assert row.peak_equity == pytest.approx(120.0)
    assert row.current_equity == pytest.approx(108.0)
    assert row.current_drawdown_percent == pytest.approx(10.0)
    assert row.hard_locked is True


def test_hard_drawdown_lock_is_sticky_after_equity_recovery() -> None:
    rows = matrix().default_protection_matrix()
    row = by_id(rows, "HARD_LOCK_STICKY_RECOVERY")

    assert row.hard_locked is True
    assert row.recovery_invoked is True
    assert row.recovery_valid is True
    assert row.recovery_hard_locked is True
    assert row.recovery_exposure_allowed is False
    assert row.recovery_reason == "HARD_DRAWDOWN_LOCK"


def test_single_loss_cooldown_blocks_through_n_plus_4() -> None:
    rows = matrix().default_protection_matrix()
    row = by_id(rows, "LOSS_COOLDOWN_BLOCKED")

    assert row.consecutive_losses == 1
    assert row.cooldown_until_bar == 15
    assert row.cooldown_remaining_bars == 1
    assert row.exposure_allowed is False
    assert row.assessment_reason == "LOSS_COOLDOWN_ACTIVE"


def test_single_loss_cooldown_releases_at_n_plus_5() -> None:
    rows = matrix().default_protection_matrix()
    row = by_id(rows, "LOSS_COOLDOWN_RELEASE")

    assert row.cooldown_until_bar == 15
    assert row.cooldown_remaining_bars == 0
    assert row.exposure_allowed is True
    assert row.assessment_reason == "OK_ACCOUNT_PROTECTION"


def test_three_loss_streak_uses_extended_cooldown() -> None:
    rows = matrix().default_protection_matrix()
    row = by_id(rows, "LOSS_STREAK_COOLDOWN_BLOCKED")

    assert row.consecutive_losses == 3
    assert row.cooldown_until_bar == 60
    assert row.cooldown_remaining_bars == 1
    assert row.exposure_allowed is False


def test_three_loss_streak_extended_cooldown_releases_on_boundary() -> None:
    rows = matrix().default_protection_matrix()
    row = by_id(rows, "LOSS_STREAK_COOLDOWN_RELEASE")

    assert row.consecutive_losses == 3
    assert row.cooldown_until_bar == 60
    assert row.cooldown_remaining_bars == 0
    assert row.exposure_allowed is True


# =============================================================================
# Custom direct stress cases
# =============================================================================


def test_short_direction_uses_symmetric_structural_stop_geometry() -> None:
    row = matrix().evaluate_single(
        SingleScenario(
            scenario_id="SHORT_PASS",
            balance=63.35,
            equity=63.35,
            free_margin=63.35,
            spread_points=200.0,
            stop_distance_price=0.40,
            direction="SHORT",
        )
    )

    assert row.risk_valid is True
    assert row.structural_stop_preserved is True
    assert row.risk_plan.direction == "SHORT"
    assert row.final_new_exposure_feasible is True


def test_slippage_spike_can_block_otherwise_passable_case() -> None:
    row = matrix().evaluate_single(
        SingleScenario(
            scenario_id="SLIPPAGE_SPIKE",
            balance=63.35,
            equity=63.35,
            free_margin=63.35,
            spread_points=200.0,
            stop_distance_price=0.40,
            estimated_slippage_price=0.09,
            estimated_slippage_cost=0.05,
        )
    )

    assert row.risk_valid is True
    assert row.execution_feasible is False
    assert "SLIPPAGE_DOMINATES_STRUCTURAL_STOP" in row.friction_violations
    assert row.final_new_exposure_feasible is False


def test_commission_spike_can_break_all_in_budget_without_rebooking_spread() -> None:
    row = matrix().evaluate_single(
        SingleScenario(
            scenario_id="COMMISSION_SPIKE",
            balance=63.35,
            equity=63.35,
            free_margin=63.35,
            spread_points=200.0,
            stop_distance_price=0.40,
            estimated_commission_cost=0.10,
        )
    )

    assert row.risk_valid is True
    assert row.raw_spread_cost == pytest.approx(0.20)
    assert row.total_friction_cost == pytest.approx(0.30)
    assert row.execution_feasible is False
    assert "ALL_IN_LOSS_EXCEEDS_HARD_BUDGET" in row.friction_violations


def test_addon_stress_never_changes_upstream_structural_stop() -> None:
    row = matrix().evaluate_addon(
        AddonScenario(
            scenario_id="ADD_STOP_PRESERVE",
        )
    )

    assert row.risk_valid is True
    assert row.risk_plan.stop_distance_price == pytest.approx(0.50)
    assert row.risk_plan.stop_loss == pytest.approx(
        row.risk_plan.entry_price - 0.50
    )


def test_invalid_protection_initial_state_fails_closed() -> None:
    row = matrix().evaluate_protection(
        ProtectionScenario(
            scenario_id="INVALID_PROTECTION",
            starting_equity=0.0,
            assessment_equity=0.0,
            assessment_bar=1,
        )
    )

    assert row.valid is False
    assert row.reason == "INVALID_PROTECTION_INITIAL_STATE"
    assert row.live_authorized is False


def test_non_monotonic_protection_event_fails_closed() -> None:
    row = matrix().evaluate_protection(
        ProtectionScenario(
            scenario_id="NON_MONOTONIC_PROTECTION",
            starting_equity=100.0,
            close_events=(
                ProtectionCloseEvent(-1.0, 99.0, 10),
                ProtectionCloseEvent(-1.0, 98.0, 9),
            ),
            assessment_equity=98.0,
            assessment_bar=11,
        )
    )

    assert row.valid is False
    assert row.reason == "PROTECTION_CLOSE_EVENT_REJECTED"
    assert row.live_authorized is False