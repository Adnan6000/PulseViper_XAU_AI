"""
Offline tests for RealizedExecutionCostLifecycleObserver v1.0.
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace
from typing import Any

import pytest


pytestmark = pytest.mark.offline


observer_module: Any = importlib.import_module(
    "02_AI.Shadow.realized_execution_cost_lifecycle_observer"
)

cost_module: Any = importlib.import_module(
    "02_AI.Shadow.realized_execution_cost_accounting"
)

friction_module: Any = importlib.import_module(
    "02_AI.Shadow.execution_friction_model"
)


Observer: Any = (
    observer_module.RealizedExecutionCostLifecycleObserver
)

CostAccounting: Any = (
    cost_module.RealizedExecutionCostAccounting
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


def lifecycle_state(
    cumulative_spread_cost: float,
) -> Any:

    return SimpleNamespace(
        pnl_state=SimpleNamespace(
            cumulative_spread_cost=(
                cumulative_spread_cost
            )
        )
    )


def successful_transition(
    *,
    spread_before: float = 0.0,
    spread_after: float = 0.26,
    candidate_spread: float = 0.26,
    friction: Any | None = None,
) -> Any:

    resolved_friction = (
        friction
        if friction is not None
        else friction_assessment()
    )

    admission_result = SimpleNamespace(
        valid=True,
        admitted=True,
        live_authorized=False,
        friction_assessment=resolved_friction,
        candidate=SimpleNamespace(
            spread_cost=candidate_spread
        ),
    )

    protected_result = SimpleNamespace(
        live_authorized=False,
        admission_result=admission_result,
    )

    return SimpleNamespace(
        valid=True,
        exposure_applied=True,
        live_authorized=False,
        lifecycle_invoked=True,
        lifecycle_state_before=lifecycle_state(
            spread_before
        ),
        lifecycle_state_after=lifecycle_state(
            spread_after
        ),
        protected_admission_result=(
            protected_result
        ),
    )


def test_observer_is_shadow_only() -> None:

    observer = Observer()

    result = observer.observe(
        cost_state=CostAccounting().initial_state(),
        execution_id="L1_FILL_1",
        lifecycle_transition=successful_transition(),
        realized_spread_cost=0.28,
    )

    assert result.valid is True

    assert result.observed is True

    assert result.live_authorized is False

    assert result.mode == (
        "SHADOW_REALIZED_EXECUTION_COST_LIFECYCLE_OBSERVER_ONLY"
    )

    assert result.lifecycle_pnl_delta == pytest.approx(
        0.0
    )


def test_successful_exposure_records_complete_realized_cost() -> None:

    observer = Observer()

    cost_state = CostAccounting().initial_state()

    lifecycle_transition = successful_transition()

    result = observer.observe(
        cost_state=cost_state,
        execution_id="L1_FILL_1",
        lifecycle_transition=lifecycle_transition,
        realized_spread_cost=0.28,
        realized_slippage_cost=0.02,
        realized_commission_cost=0.05,
    )

    assert result.valid is True

    assert result.observed is True

    assert result.reason == (
        "OK_REALIZED_EXECUTION_COST_LIFECYCLE_OBSERVATION"
    )

    assert result.cost_reason == (
        "OK_REALIZED_EXECUTION_COST_RECORDED"
    )

    assert (
        result.expected_raw_spread_cost
        ==
        pytest.approx(
            0.26
        )
    )

    assert (
        result.lifecycle_spread_delta
        ==
        pytest.approx(
            0.26
        )
    )

    assert result.lifecycle_pnl_delta == pytest.approx(
        0.0
    )

    assert result.cost_transition is not None

    assert result.cost_transition.record is not None

    assert (
        result.cost_transition
        .record
        .complete_realized_total_cost
        ==
        pytest.approx(
            0.35
        )
    )

    assert (
        result.cost_state_after
        .observation_count
        ==
        1
    )

    assert (
        result.cost_state_after
        .complete_observation_count
        ==
        1
    )


def test_raw_spread_is_verified_but_not_rebooked() -> None:

    observer = Observer()

    lifecycle_transition = successful_transition(
        spread_before=0.52,
        spread_after=0.78,
    )

    result = observer.observe(
        cost_state=CostAccounting().initial_state(),
        execution_id="L3_FILL_1",
        lifecycle_transition=lifecycle_transition,
        realized_spread_cost=0.31,
        realized_slippage_cost=0.02,
        realized_commission_cost=0.04,
    )

    assert result.valid is True

    assert result.lifecycle_spread_delta == pytest.approx(
        0.26
    )

    assert result.expected_raw_spread_cost == pytest.approx(
        0.26
    )

    assert result.lifecycle_pnl_delta == pytest.approx(
        0.0
    )

    assert result.cost_transition is not None

    assert (
        result.cost_transition.lifecycle_pnl_delta
        ==
        pytest.approx(
            0.0
        )
    )

    assert result.cost_transition.record is not None

    assert (
        result.cost_transition
        .record
        .realized_spread_cost
        ==
        pytest.approx(
            0.31
        )
    )


def test_partial_realized_observation_is_allowed() -> None:

    observer = Observer()

    result = observer.observe(
        cost_state=CostAccounting().initial_state(),
        execution_id="L1_FILL_1",
        lifecycle_transition=successful_transition(),
        realized_slippage_cost=0.05,
    )

    assert result.valid is True

    assert result.observed is True

    assert result.cost_transition.record is not None

    record = (
        result.cost_transition.record
    )

    assert record.realized_spread_available is False

    assert record.realized_slippage_available is True

    assert record.realized_commission_available is False

    assert record.realized_cost_complete is False

    assert record.comparable_variance == pytest.approx(
        0.02
    )


def test_favorable_slippage_remains_signed() -> None:

    observer = Observer()

    result = observer.observe(
        cost_state=CostAccounting().initial_state(),
        execution_id="L1_FILL_1",
        lifecycle_transition=successful_transition(),
        realized_slippage_cost=-0.01,
    )

    assert result.valid is True

    assert result.cost_transition.record is not None

    assert (
        result.cost_transition
        .record
        .realized_slippage_cost
        ==
        pytest.approx(
            -0.01
        )
    )


def test_rejected_lifecycle_does_not_reach_cost_accounting() -> None:

    observer = Observer()

    transition = successful_transition()

    transition = SimpleNamespace(
        **{
            **transition.__dict__,
            "valid": False,
            "exposure_applied": False,
        }
    )

    state = CostAccounting().initial_state()

    result = observer.observe(
        cost_state=state,
        execution_id="L1_FILL_1",
        lifecycle_transition=transition,
        realized_spread_cost=0.26,
    )

    assert result.valid is False

    assert result.observed is False

    assert result.reason == (
        "LIFECYCLE_EXPOSURE_NOT_APPLIED"
    )

    assert result.cost_transition is None

    assert result.cost_state_after == state


def test_exposure_flag_is_required() -> None:

    observer = Observer()

    transition = successful_transition()

    transition = SimpleNamespace(
        **{
            **transition.__dict__,
            "exposure_applied": False,
        }
    )

    state = CostAccounting().initial_state()

    result = observer.observe(
        cost_state=state,
        execution_id="L1_FILL_1",
        lifecycle_transition=transition,
        realized_spread_cost=0.26,
    )

    assert result.valid is False

    assert result.reason == (
        "LIFECYCLE_EXPOSURE_NOT_APPLIED"
    )

    assert result.cost_state_after == state


def test_lifecycle_must_have_been_invoked() -> None:

    observer = Observer()

    transition = successful_transition()

    transition = SimpleNamespace(
        **{
            **transition.__dict__,
            "lifecycle_invoked": False,
        }
    )

    state = CostAccounting().initial_state()

    result = observer.observe(
        cost_state=state,
        execution_id="L1_FILL_1",
        lifecycle_transition=transition,
        realized_spread_cost=0.26,
    )

    assert result.valid is False

    assert result.reason == (
        "LIFECYCLE_NOT_INVOKED"
    )

    assert result.cost_state_after == state


def test_live_lifecycle_transition_is_rejected() -> None:

    observer = Observer()

    transition = successful_transition()

    transition = SimpleNamespace(
        **{
            **transition.__dict__,
            "live_authorized": True,
        }
    )

    state = CostAccounting().initial_state()

    result = observer.observe(
        cost_state=state,
        execution_id="L1_FILL_1",
        lifecycle_transition=transition,
        realized_spread_cost=0.26,
    )

    assert result.valid is False

    assert result.reason == (
        "LIFECYCLE_LIVE_AUTHORIZATION_NOT_ALLOWED"
    )

    assert result.live_authorized is False

    assert result.cost_state_after == state


def test_live_nested_admission_is_rejected() -> None:

    observer = Observer()

    transition = successful_transition()

    admission = (
        transition
        .protected_admission_result
        .admission_result
    )

    live_admission = SimpleNamespace(
        **{
            **admission.__dict__,
            "live_authorized": True,
        }
    )

    protected = SimpleNamespace(
        live_authorized=False,
        admission_result=live_admission,
    )

    transition = SimpleNamespace(
        **{
            **transition.__dict__,
            "protected_admission_result": protected,
        }
    )

    state = CostAccounting().initial_state()

    result = observer.observe(
        cost_state=state,
        execution_id="L1_FILL_1",
        lifecycle_transition=transition,
        realized_spread_cost=0.26,
    )

    assert result.valid is False

    assert result.reason == (
        "ADMISSION_LIVE_AUTHORIZATION_NOT_ALLOWED"
    )

    assert result.cost_state_after == state


def test_candidate_and_friction_raw_spread_must_match() -> None:

    observer = Observer()

    transition = successful_transition(
        candidate_spread=0.27,
        spread_after=0.27,
    )

    state = CostAccounting().initial_state()

    result = observer.observe(
        cost_state=state,
        execution_id="L1_FILL_1",
        lifecycle_transition=transition,
        realized_spread_cost=0.27,
    )

    assert result.valid is False

    assert result.reason == (
        "CANDIDATE_FRICTION_SPREAD_MISMATCH"
    )

    assert result.cost_transition is None

    assert result.cost_state_after == state


def test_lifecycle_raw_spread_delta_must_match_candidate() -> None:

    observer = Observer()

    transition = successful_transition(
        spread_before=0.0,
        spread_after=0.52,
        candidate_spread=0.26,
    )

    state = CostAccounting().initial_state()

    result = observer.observe(
        cost_state=state,
        execution_id="L1_FILL_1",
        lifecycle_transition=transition,
        realized_spread_cost=0.26,
    )

    assert result.valid is False

    assert result.reason == (
        "LIFECYCLE_RAW_SPREAD_BOOKING_MISMATCH"
    )

    assert result.expected_raw_spread_cost == pytest.approx(
        0.26
    )

    assert result.lifecycle_spread_delta == pytest.approx(
        0.52
    )

    assert result.cost_transition is None

    assert result.cost_state_after == state


def test_lifecycle_spread_cannot_move_backward() -> None:

    observer = Observer()

    transition = successful_transition(
        spread_before=0.52,
        spread_after=0.26,
    )

    state = CostAccounting().initial_state()

    result = observer.observe(
        cost_state=state,
        execution_id="L1_FILL_1",
        lifecycle_transition=transition,
        realized_spread_cost=0.26,
    )

    assert result.valid is False

    assert result.reason == (
        "LIFECYCLE_SPREAD_MOVED_BACKWARD"
    )

    assert result.cost_state_after == state


def test_duplicate_execution_id_is_fail_closed() -> None:

    observer = Observer()

    initial_state = (
        CostAccounting().initial_state()
    )

    transition = successful_transition()

    first = observer.observe(
        cost_state=initial_state,
        execution_id="L1_FILL_1",
        lifecycle_transition=transition,
        realized_spread_cost=0.26,
    )

    assert first.valid is True

    second = observer.observe(
        cost_state=first.cost_state_after,
        execution_id="L1_FILL_1",
        lifecycle_transition=transition,
        realized_spread_cost=0.27,
    )

    assert second.valid is False

    assert second.reason == (
        "REALIZED_COST_ACCOUNTING_REJECTED"
    )

    assert second.cost_reason == (
        "DUPLICATE_EXECUTION_ID"
    )

    assert (
        second.cost_state_after
        ==
        first.cost_state_after
    )


def test_missing_realized_cost_telemetry_is_fail_closed() -> None:

    observer = Observer()

    state = CostAccounting().initial_state()

    result = observer.observe(
        cost_state=state,
        execution_id="L1_FILL_1",
        lifecycle_transition=successful_transition(),
    )

    assert result.valid is False

    assert result.reason == (
        "REALIZED_COST_ACCOUNTING_REJECTED"
    )

    assert result.cost_reason == (
        "NO_REALIZED_COST_OBSERVATION"
    )

    assert result.cost_state_after == state


def test_empty_execution_id_is_rejected_before_accounting() -> None:

    observer = Observer()

    state = CostAccounting().initial_state()

    result = observer.observe(
        cost_state=state,
        execution_id="   ",
        lifecycle_transition=successful_transition(),
        realized_spread_cost=0.26,
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_EXECUTION_ID"
    )

    assert result.cost_transition is None

    assert result.cost_state_after == state


def test_malformed_lifecycle_transition_is_rejected() -> None:

    observer = Observer()

    state = CostAccounting().initial_state()

    result = observer.observe(
        cost_state=state,
        execution_id="L1_FILL_1",
        lifecycle_transition=SimpleNamespace(
            valid=True
        ),
        realized_spread_cost=0.26,
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_LIFECYCLE_TRANSITION_SHAPE"
    )

    assert result.cost_state_after == state


def test_malformed_lifecycle_pnl_state_is_rejected() -> None:

    observer = Observer()

    transition = successful_transition()

    malformed_after = SimpleNamespace(
        pnl_state=SimpleNamespace()
    )

    transition = SimpleNamespace(
        **{
            **transition.__dict__,
            "lifecycle_state_after": malformed_after,
        }
    )

    state = CostAccounting().initial_state()

    result = observer.observe(
        cost_state=state,
        execution_id="L1_FILL_1",
        lifecycle_transition=transition,
        realized_spread_cost=0.26,
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_LIFECYCLE_PNL_STATE_SHAPE"
    )

    assert result.cost_state_after == state