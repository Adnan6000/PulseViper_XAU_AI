"""
Offline tests for RealizedExecutionCostAccounting v1.0.
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace
from typing import Any

import pytest


pytestmark = pytest.mark.offline


accounting_module: Any = importlib.import_module(
    "02_AI.Shadow.realized_execution_cost_accounting"
)

friction_module: Any = importlib.import_module(
    "02_AI.Shadow.execution_friction_model"
)


Accounting: Any = (
    accounting_module.RealizedExecutionCostAccounting
)

FrictionModel: Any = (
    friction_module.ExecutionFrictionModel
)


def friction_assessment(
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
        "hard_loss_budget": 1.00,
        "entry_price": 4316.729,
        "stop_loss": 4316.229,
        "point": 0.001,
        "spread_price": 0.26,
        "spread_cost": 0.26,
        "projected_stop_loss": 0.50,
        "estimated_slippage_price": 0.03,
        "estimated_slippage_cost": 0.03,
        "estimated_commission_cost": 0.04,
    }

    values.update(
        overrides
    )

    return FrictionModel().evaluate(
        **values
    )


def test_initial_state_is_shadow_only() -> None:

    accounting = Accounting()

    state = accounting.initial_state()

    assert state.live_authorized is False

    assert state.observation_count == 0

    assert state.complete_observation_count == 0

    assert state.execution_ids == ()

    assert (
        state.cumulative_estimated_total_friction
        ==
        pytest.approx(
            0.0
        )
    )


def test_complete_realization_records_component_variances() -> None:

    accounting = Accounting()

    result = accounting.record_execution(
        state=accounting.initial_state(),
        execution_id="L1_FILL_1",
        friction_assessment=friction_assessment(),
        realized_spread_cost=0.28,
        realized_slippage_cost=0.02,
        realized_commission_cost=0.05,
    )

    assert result.valid is True

    assert result.reason == (
        "OK_REALIZED_EXECUTION_COST_RECORDED"
    )

    assert result.live_authorized is False

    assert result.lifecycle_pnl_delta == pytest.approx(
        0.0
    )

    assert result.record is not None

    record = result.record

    assert record.live_authorized is False

    assert record.lifecycle_pnl_delta == pytest.approx(
        0.0
    )

    assert record.estimated_spread_cost == pytest.approx(
        0.26
    )

    assert record.estimated_slippage_cost == pytest.approx(
        0.03
    )

    assert record.estimated_commission_cost == pytest.approx(
        0.04
    )

    assert record.estimated_total_friction == pytest.approx(
        0.33
    )

    assert record.realized_cost_complete is True

    assert record.complete_realized_total_cost == pytest.approx(
        0.35
    )

    assert (
        record.complete_execution_cost_variance
        ==
        pytest.approx(
            0.02
        )
    )

    assert record.spread_variance == pytest.approx(
        0.02
    )

    assert record.slippage_variance == pytest.approx(
        -0.01
    )

    assert record.commission_variance == pytest.approx(
        0.01
    )


def test_complete_realization_updates_cumulative_state() -> None:

    accounting = Accounting()

    result = accounting.record_execution(
        state=accounting.initial_state(),
        execution_id="L1_FILL_1",
        friction_assessment=friction_assessment(),
        realized_spread_cost=0.28,
        realized_slippage_cost=0.02,
        realized_commission_cost=0.05,
    )

    state = result.state_after

    assert state.execution_ids == (
        "L1_FILL_1",
    )

    assert state.observation_count == 1

    assert state.complete_observation_count == 1

    assert state.realized_spread_observation_count == 1

    assert state.realized_slippage_observation_count == 1

    assert state.realized_commission_observation_count == 1

    assert (
        state.cumulative_estimated_spread_cost
        ==
        pytest.approx(
            0.26
        )
    )

    assert (
        state.cumulative_realized_spread_cost
        ==
        pytest.approx(
            0.28
        )
    )

    assert (
        state.cumulative_estimated_total_friction
        ==
        pytest.approx(
            0.33
        )
    )

    assert (
        state.cumulative_complete_realized_cost
        ==
        pytest.approx(
            0.35
        )
    )

    assert (
        state.cumulative_complete_variance
        ==
        pytest.approx(
            0.02
        )
    )


def test_partial_realization_does_not_treat_missing_components_as_zero() -> None:

    accounting = Accounting()

    result = accounting.record_execution(
        state=accounting.initial_state(),
        execution_id="L1_FILL_1",
        friction_assessment=friction_assessment(),
        realized_slippage_cost=0.05,
    )

    assert result.valid is True

    assert result.record is not None

    record = result.record

    assert record.realized_spread_available is False

    assert record.realized_spread_cost is None

    assert record.realized_slippage_available is True

    assert record.realized_slippage_cost == pytest.approx(
        0.05
    )

    assert record.realized_commission_available is False

    assert record.realized_commission_cost is None

    assert record.realized_cost_complete is False

    assert record.complete_realized_total_cost is None

    assert record.complete_execution_cost_variance is None

    assert record.comparable_estimated_cost == pytest.approx(
        0.03
    )

    assert record.comparable_realized_cost == pytest.approx(
        0.05
    )

    assert record.comparable_variance == pytest.approx(
        0.02
    )

    state = result.state_after

    assert state.observation_count == 1

    assert state.complete_observation_count == 0

    assert state.realized_spread_observation_count == 0

    assert state.realized_slippage_observation_count == 1

    assert state.realized_commission_observation_count == 0

    assert (
        state.cumulative_complete_realized_cost
        ==
        pytest.approx(
            0.0
        )
    )


def test_favorable_realized_slippage_can_be_negative() -> None:

    accounting = Accounting()

    result = accounting.record_execution(
        state=accounting.initial_state(),
        execution_id="L1_FILL_1",
        friction_assessment=friction_assessment(),
        realized_slippage_cost=-0.01,
    )

    assert result.valid is True

    assert result.record is not None

    assert (
        result.record.realized_slippage_cost
        ==
        pytest.approx(
            -0.01
        )
    )

    assert (
        result.record.slippage_variance
        ==
        pytest.approx(
            -0.04
        )
    )

    assert (
        result.record.comparable_variance
        ==
        pytest.approx(
            -0.04
        )
    )


def test_multiple_executions_accumulate_without_touching_lifecycle() -> None:

    accounting = Accounting()

    first = accounting.record_execution(
        state=accounting.initial_state(),
        execution_id="L1_FILL_1",
        friction_assessment=friction_assessment(),
        realized_spread_cost=0.28,
        realized_slippage_cost=0.02,
        realized_commission_cost=0.05,
    )

    assert first.valid is True

    second = accounting.record_execution(
        state=first.state_after,
        execution_id="L2_FILL_1",
        friction_assessment=friction_assessment(),
        realized_spread_cost=0.24,
        realized_slippage_cost=-0.01,
        realized_commission_cost=0.04,
    )

    assert second.valid is True

    assert second.lifecycle_pnl_delta == pytest.approx(
        0.0
    )

    assert second.record is not None

    assert second.record.lifecycle_pnl_delta == pytest.approx(
        0.0
    )

    state = second.state_after

    assert state.observation_count == 2

    assert state.complete_observation_count == 2

    assert state.execution_ids == (
        "L1_FILL_1",
        "L2_FILL_1",
    )

    assert (
        state.cumulative_estimated_total_friction
        ==
        pytest.approx(
            0.66
        )
    )

    assert (
        state.cumulative_complete_realized_cost
        ==
        pytest.approx(
            0.62
        )
    )

    assert (
        state.cumulative_complete_variance
        ==
        pytest.approx(
            -0.04
        )
    )


def test_duplicate_execution_id_is_rejected_without_state_change() -> None:

    accounting = Accounting()

    first = accounting.record_execution(
        state=accounting.initial_state(),
        execution_id="L1_FILL_1",
        friction_assessment=friction_assessment(),
        realized_spread_cost=0.26,
    )

    assert first.valid is True

    second = accounting.record_execution(
        state=first.state_after,
        execution_id="L1_FILL_1",
        friction_assessment=friction_assessment(),
        realized_spread_cost=0.27,
    )

    assert second.valid is False

    assert second.reason == (
        "DUPLICATE_EXECUTION_ID"
    )

    assert second.state_after == first.state_after

    assert second.lifecycle_pnl_delta == pytest.approx(
        0.0
    )


def test_empty_execution_id_is_rejected() -> None:

    accounting = Accounting()

    state = accounting.initial_state()

    result = accounting.record_execution(
        state=state,
        execution_id="   ",
        friction_assessment=friction_assessment(),
        realized_spread_cost=0.26,
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_EXECUTION_ID"
    )

    assert result.state_after == state


def test_no_realized_observation_is_rejected() -> None:

    accounting = Accounting()

    state = accounting.initial_state()

    result = accounting.record_execution(
        state=state,
        execution_id="L1_FILL_1",
        friction_assessment=friction_assessment(),
    )

    assert result.valid is False

    assert result.reason == (
        "NO_REALIZED_COST_OBSERVATION"
    )

    assert result.state_after == state


def test_negative_realized_spread_is_rejected() -> None:

    accounting = Accounting()

    state = accounting.initial_state()

    result = accounting.record_execution(
        state=state,
        execution_id="L1_FILL_1",
        friction_assessment=friction_assessment(),
        realized_spread_cost=-0.01,
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_REALIZED_SPREAD_COST"
    )

    assert result.state_after == state


def test_negative_realized_commission_is_rejected() -> None:

    accounting = Accounting()

    state = accounting.initial_state()

    result = accounting.record_execution(
        state=state,
        execution_id="L1_FILL_1",
        friction_assessment=friction_assessment(),
        realized_commission_cost=-0.01,
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_REALIZED_COMMISSION_COST"
    )

    assert result.state_after == state


def test_non_finite_realized_slippage_is_rejected() -> None:

    accounting = Accounting()

    state = accounting.initial_state()

    result = accounting.record_execution(
        state=state,
        execution_id="L1_FILL_1",
        friction_assessment=friction_assessment(),
        realized_slippage_cost=float(
            "nan"
        ),
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_REALIZED_SLIPPAGE_COST"
    )

    assert result.state_after == state


def test_malformed_friction_assessment_is_rejected() -> None:

    accounting = Accounting()

    state = accounting.initial_state()

    result = accounting.record_execution(
        state=state,
        execution_id="L1_FILL_1",
        friction_assessment=SimpleNamespace(
            valid=True
        ),
        realized_spread_cost=0.26,
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_FRICTION_ASSESSMENT_SHAPE"
    )

    assert result.state_after == state


def test_live_authorized_friction_assessment_is_rejected() -> None:

    accounting = Accounting()

    assessment = friction_assessment()

    live_assessment = SimpleNamespace(
        valid=assessment.valid,
        execution_feasible=(
            assessment.execution_feasible
        ),
        live_authorized=True,
        spread_cost=assessment.spread_cost,
        estimated_slippage_cost=(
            assessment.estimated_slippage_cost
        ),
        estimated_commission_cost=(
            assessment.estimated_commission_cost
        ),
        total_friction_cost=(
            assessment.total_friction_cost
        ),
    )

    state = accounting.initial_state()

    result = accounting.record_execution(
        state=state,
        execution_id="L1_FILL_1",
        friction_assessment=live_assessment,
        realized_spread_cost=0.26,
    )

    assert result.valid is False

    assert result.reason == (
        "LIVE_AUTHORIZATION_NOT_ALLOWED"
    )

    assert result.live_authorized is False

    assert result.state_after == state


def test_invalid_friction_assessment_is_rejected() -> None:

    accounting = Accounting()

    assessment = friction_assessment(
        direction="SIDEWAYS"
    )

    assert assessment.valid is False

    state = accounting.initial_state()

    result = accounting.record_execution(
        state=state,
        execution_id="L1_FILL_1",
        friction_assessment=assessment,
        realized_spread_cost=0.26,
    )

    assert result.valid is False

    assert result.reason == (
        "FRICTION_ASSESSMENT_REJECTED"
    )

    assert result.state_after == state


def test_blocked_friction_assessment_is_rejected() -> None:

    accounting = Accounting()

    assessment = friction_assessment(
        stop_loss=4316.329,
        projected_stop_loss=0.40,
    )

    assert assessment.valid is True

    assert assessment.execution_feasible is False

    state = accounting.initial_state()

    result = accounting.record_execution(
        state=state,
        execution_id="L1_FILL_1",
        friction_assessment=assessment,
        realized_spread_cost=0.26,
    )

    assert result.valid is False

    assert result.reason == (
        "EXECUTION_FRICTION_BLOCKED"
    )

    assert result.state_after == state


def test_estimated_component_mismatch_fails_closed() -> None:

    accounting = Accounting()

    assessment = friction_assessment()

    malformed = SimpleNamespace(
        valid=True,
        execution_feasible=True,
        live_authorized=False,
        spread_cost=assessment.spread_cost,
        estimated_slippage_cost=(
            assessment.estimated_slippage_cost
        ),
        estimated_commission_cost=(
            assessment.estimated_commission_cost
        ),
        total_friction_cost=999.0,
    )

    state = accounting.initial_state()

    result = accounting.record_execution(
        state=state,
        execution_id="L1_FILL_1",
        friction_assessment=malformed,
        realized_spread_cost=0.26,
    )

    assert result.valid is False

    assert result.reason == (
        "ESTIMATED_FRICTION_COMPONENT_MISMATCH"
    )

    assert result.state_after == state


def test_raw_spread_is_observed_not_rebooked_into_lifecycle() -> None:

    accounting = Accounting()

    result = accounting.record_execution(
        state=accounting.initial_state(),
        execution_id="L1_FILL_1",
        friction_assessment=friction_assessment(),
        realized_spread_cost=0.31,
        realized_slippage_cost=0.02,
        realized_commission_cost=0.04,
    )

    assert result.valid is True

    assert result.record is not None

    assert result.record.estimated_spread_cost == pytest.approx(
        0.26
    )

    assert result.record.realized_spread_cost == pytest.approx(
        0.31
    )

    assert result.record.spread_variance == pytest.approx(
        0.05
    )

    # Critical boundary:
    # existing CompoundingPnLLedger remains the sole current
    # RAW-spread P&L booker.
    assert result.lifecycle_pnl_delta == pytest.approx(
        0.0
    )

    assert result.record.lifecycle_pnl_delta == pytest.approx(
        0.0
    )