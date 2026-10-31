"""
Offline tests for RealizedFillTelemetryBridge v1.0.
"""

from __future__ import annotations

import importlib
from types import SimpleNamespace
from typing import Any

import pytest


pytestmark = pytest.mark.offline


bridge_module: Any = importlib.import_module(
    "02_AI.Shadow.realized_fill_telemetry_bridge"
)

cost_module: Any = importlib.import_module(
    "02_AI.Shadow.realized_execution_cost_accounting"
)

friction_module: Any = importlib.import_module(
    "02_AI.Shadow.execution_friction_model"
)


Bridge: Any = (
    bridge_module.RealizedFillTelemetryBridge
)

Telemetry: Any = (
    bridge_module.NormalizedActualFillTelemetry
)

CostAccounting: Any = (
    cost_module.RealizedExecutionCostAccounting
)

FrictionModel: Any = (
    friction_module.ExecutionFrictionModel
)


# =============================================================================
# Fixtures
# =============================================================================


def friction_assessment(
    *,
    direction: str = "LONG",
    spread_price: float = 0.20,
    spread_cost: float = 0.20,
    projected_stop_loss: float = 0.50,
    stop_distance: float = 0.50,
    entry_price: float | None = None,
) -> Any:

    normalized = direction.upper()

    entry = (
        entry_price
        if entry_price is not None
        else (
            4316.700
            if normalized == "LONG"
            else
            4316.500
        )
    )

    stop = (
        entry
        -
        stop_distance
        if normalized == "LONG"
        else
        entry
        +
        stop_distance
    )

    return FrictionModel().evaluate(
        direction=normalized,
        volume=0.01,
        balance=63.35,
        equity=63.35,
        hard_loss_budget=1.00,
        entry_price=entry,
        stop_loss=stop,
        point=0.001,
        spread_price=spread_price,
        spread_cost=spread_cost,
        projected_stop_loss=projected_stop_loss,
        estimated_slippage_price=0.02,
        estimated_slippage_cost=0.02,
        estimated_commission_cost=0.03,
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
    direction: str = "LONG",
    spread_before: float = 0.0,
    spread_after: float = 0.20,
    risk_overrides: dict[str, Any] | None = None,
    friction_overrides: dict[str, Any] | None = None,
    candidate_overrides: dict[str, Any] | None = None,
) -> Any:

    normalized = direction.upper()

    entry = (
        4316.700
        if normalized == "LONG"
        else
        4316.500
    )

    friction = friction_assessment(
        direction=normalized,
        entry_price=entry,
    )

    if friction_overrides:

        friction = SimpleNamespace(
            **{
                **friction.__dict__,
                **friction_overrides,
            }
        )

    risk_values = {
        "valid": True,
        "live_authorized": False,
        "direction": normalized,
        "selected_volume": 0.01,
        "entry_price": entry,
        "stop_distance_price": 0.50,
        "stop_distance_points": 500.0,
        "estimated_stop_loss_amount": 0.50,
        "spread_price": 0.20,
        "spread_points": 200.0,
        "spread_cost": 0.20,
    }

    if risk_overrides:

        risk_values.update(
            risk_overrides
        )

    risk_plan = SimpleNamespace(
        **risk_values
    )

    candidate_values = {
        "direction": normalized,
        "volume": 0.01,
        "projected_stop_loss": 0.50,
        "spread_cost": 0.20,
        "structural_stop_distance": 0.50,
    }

    if candidate_overrides:

        candidate_values.update(
            candidate_overrides
        )

    candidate = SimpleNamespace(
        **candidate_values
    )

    admission = SimpleNamespace(
        valid=True,
        admitted=True,
        live_authorized=False,
        risk_plan=risk_plan,
        friction_assessment=friction,
        candidate=candidate,
    )

    protected = SimpleNamespace(
        live_authorized=False,
        admission_result=admission,
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
        protected_admission_result=protected,
    )


def default_telemetry(
    *,
    execution_id: str = "FILL_1",
    filled_volume: float = 0.01,
    fill_price: float | None = 4316.720,
    quote_bid: float | None = 4316.500,
    quote_ask: float | None = 4316.700,
    commission_cost: float | None = 0.04,
) -> Any:

    return Telemetry(
        execution_id=execution_id,
        filled_volume=filled_volume,
        fill_price=fill_price,
        quote_bid=quote_bid,
        quote_ask=quote_ask,
        commission_cost=commission_cost,
    )


def observe(
    *,
    bridge: Any | None = None,
    state: Any | None = None,
    transition: Any | None = None,
    telemetry: Any | None = None,
) -> Any:

    engine = (
        bridge
        if bridge is not None
        else Bridge()
    )

    cost_state = (
        state
        if state is not None
        else engine.initial_cost_state()
    )

    return engine.observe_fill(
        cost_state=cost_state,
        lifecycle_transition=(
            transition
            if transition is not None
            else successful_transition()
        ),
        telemetry=(
            telemetry
            if telemetry is not None
            else default_telemetry()
        ),
    )


# =============================================================================
# Core / safety boundary
# =============================================================================


def test_bridge_is_shadow_only() -> None:

    result = observe()

    assert result.valid is True

    assert result.observed is True

    assert result.live_authorized is False

    assert result.lifecycle_pnl_delta == pytest.approx(
        0.0
    )

    assert result.mode == (
        "SHADOW_REALIZED_FILL_TELEMETRY_BRIDGE_ONLY"
    )


def test_initial_cost_state_delegates_to_existing_accounting() -> None:

    state = Bridge().initial_cost_state()

    assert state.observation_count == 0

    assert state.complete_observation_count == 0

    assert state.live_authorized is False


def test_successful_complete_long_fill_records_all_components() -> None:

    result = observe()

    assert result.reason == (
        "OK_NORMALIZED_ACTUAL_FILL_OBSERVED"
    )

    assert result.observer_invoked is True

    assert result.observer_reason == (
        "OK_REALIZED_EXECUTION_COST_LIFECYCLE_OBSERVATION"
    )

    assert result.realized_spread_cost == pytest.approx(
        0.20
    )

    assert result.realized_slippage_cost == pytest.approx(
        0.02
    )

    assert result.realized_commission_cost == pytest.approx(
        0.04
    )

    assert (
        result.monetary_cost_per_price_unit
        ==
        pytest.approx(
            1.0
        )
    )

    assert (
        result.cost_state_after
        .complete_observation_count
        ==
        1
    )

    record = (
        result.observer_result
        .cost_transition
        .record
    )

    assert (
        record.complete_realized_total_cost
        ==
        pytest.approx(
            0.26
        )
    )

    assert record.lifecycle_pnl_delta == pytest.approx(
        0.0
    )


def test_point_and_realized_points_are_auditable() -> None:

    result = observe()

    assert result.point_available is True

    assert result.point == pytest.approx(
        0.001
    )

    assert result.realized_spread_points == pytest.approx(
        200.0
    )

    assert result.realized_slippage_points == pytest.approx(
        20.0
    )


def test_monetary_scale_is_cross_checked_across_upstream_layers() -> None:

    result = observe()

    checks = dict(
        result.monetary_scale_cross_checks
    )

    assert set(
        checks
    ) == {
        "RISK_STOP",
        "RISK_SPREAD",
        "FRICTION_STOP",
        "FRICTION_SPREAD",
        "CANDIDATE_STOP",
    }

    assert all(
        value
        ==
        pytest.approx(
            1.0
        )
        for value
        in checks.values()
    )


# =============================================================================
# LONG / SHORT signed slippage
# =============================================================================


def test_long_adverse_slippage_is_positive() -> None:

    result = observe(
        telemetry=default_telemetry(
            fill_price=4316.730
        )
    )

    assert result.realized_slippage_price == pytest.approx(
        0.03
    )

    assert result.realized_slippage_cost == pytest.approx(
        0.03
    )


def test_long_favorable_slippage_remains_negative() -> None:

    result = observe(
        telemetry=default_telemetry(
            fill_price=4316.680
        )
    )

    assert result.valid is True

    assert result.realized_slippage_price == pytest.approx(
        -0.02
    )

    assert result.realized_slippage_cost == pytest.approx(
        -0.02
    )

    assert (
        result.observer_result
        .cost_transition
        .record
        .realized_slippage_cost
        ==
        pytest.approx(
            -0.02
        )
    )


def test_short_adverse_slippage_is_positive() -> None:

    transition = successful_transition(
        direction="SHORT"
    )

    telemetry = default_telemetry(
        fill_price=4316.480,
        quote_bid=4316.500,
        quote_ask=4316.700,
    )

    result = observe(
        transition=transition,
        telemetry=telemetry,
    )

    assert result.direction == "SHORT"

    assert result.realized_slippage_price == pytest.approx(
        0.02
    )

    assert result.realized_slippage_cost == pytest.approx(
        0.02
    )


def test_short_favorable_slippage_remains_negative() -> None:

    transition = successful_transition(
        direction="SHORT"
    )

    telemetry = default_telemetry(
        fill_price=4316.520,
        quote_bid=4316.500,
        quote_ask=4316.700,
    )

    result = observe(
        transition=transition,
        telemetry=telemetry,
    )

    assert result.valid is True

    assert result.realized_slippage_price == pytest.approx(
        -0.02
    )

    assert result.realized_slippage_cost == pytest.approx(
        -0.02
    )


# =============================================================================
# Realized spread / partial telemetry
# =============================================================================


def test_realized_spread_uses_fill_time_quote_not_estimated_spread() -> None:

    result = observe(
        telemetry=default_telemetry(
            quote_bid=4316.450,
            quote_ask=4316.700,
            fill_price=4316.710,
        )
    )

    assert result.realized_spread_price == pytest.approx(
        0.25
    )

    assert result.realized_spread_cost == pytest.approx(
        0.25
    )

    assert (
        result.observer_result.expected_raw_spread_cost
        ==
        pytest.approx(
            0.20
        )
    )

    assert (
        result.observer_result.lifecycle_spread_delta
        ==
        pytest.approx(
            0.20
        )
    )


def test_zero_realized_spread_is_valid_observation() -> None:

    result = observe(
        telemetry=default_telemetry(
            quote_bid=4316.700,
            quote_ask=4316.700,
            fill_price=None,
            commission_cost=None,
        )
    )

    assert result.valid is True

    assert result.realized_spread_available is True

    assert result.realized_spread_cost == pytest.approx(
        0.0
    )

    assert result.realized_slippage_available is False


def test_quote_without_fill_records_spread_only() -> None:

    result = observe(
        telemetry=default_telemetry(
            fill_price=None,
            commission_cost=None,
        )
    )

    assert result.valid is True

    assert result.realized_spread_available is True

    assert result.realized_slippage_available is False

    assert result.realized_commission_available is False

    record = (
        result.observer_result
        .cost_transition
        .record
    )

    assert record.realized_spread_available is True

    assert record.realized_slippage_available is False


def test_commission_only_observation_is_allowed() -> None:

    result = observe(
        telemetry=default_telemetry(
            fill_price=4316.720,
            quote_bid=None,
            quote_ask=None,
            commission_cost=0.04,
        )
    )

    assert result.valid is True

    assert result.realized_spread_available is False

    assert result.realized_slippage_available is False

    assert result.realized_commission_available is True

    assert result.realized_commission_cost == pytest.approx(
        0.04
    )


def test_zero_commission_is_still_an_available_observation() -> None:

    result = observe(
        telemetry=default_telemetry(
            quote_bid=None,
            quote_ask=None,
            fill_price=None,
            commission_cost=0.0,
        )
    )

    assert result.valid is True

    assert result.realized_commission_available is True

    assert result.realized_commission_cost == pytest.approx(
        0.0
    )


def test_fill_without_quote_or_commission_has_no_comparable_cost_observation() -> None:

    state = Bridge().initial_cost_state()

    result = observe(
        state=state,
        telemetry=default_telemetry(
            quote_bid=None,
            quote_ask=None,
            commission_cost=None,
        ),
    )

    assert result.valid is False

    assert result.reason == (
        "NO_REALIZED_COST_OBSERVATION"
    )

    assert result.observer_invoked is False

    assert result.cost_state_after == state


# =============================================================================
# Telemetry validation
# =============================================================================


def test_partial_quote_fails_closed() -> None:

    result = observe(
        telemetry=default_telemetry(
            quote_ask=None
        )
    )

    assert result.valid is False

    assert result.reason == (
        "PARTIAL_EXECUTION_QUOTE"
    )

    assert result.observer_invoked is False


def test_inverted_quote_fails_closed() -> None:

    result = observe(
        telemetry=default_telemetry(
            quote_bid=4316.800,
            quote_ask=4316.700,
        )
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_EXECUTION_QUOTE"
    )


def test_non_positive_fill_price_fails_closed() -> None:

    result = observe(
        telemetry=default_telemetry(
            fill_price=0.0
        )
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_FILL_PRICE"
    )


def test_negative_normalized_commission_fails_closed() -> None:

    result = observe(
        telemetry=default_telemetry(
            commission_cost=-0.01
        )
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_NORMALIZED_COMMISSION_COST"
    )


def test_live_authorized_telemetry_is_rejected() -> None:

    telemetry = SimpleNamespace(
        execution_id="LIVE_FILL",
        filled_volume=0.01,
        fill_price=4316.720,
        quote_bid=4316.500,
        quote_ask=4316.700,
        commission_cost=0.04,
        live_authorized=True,
    )

    result = observe(
        telemetry=telemetry
    )

    assert result.valid is False

    assert result.reason == (
        "FILL_TELEMETRY_LIVE_AUTHORIZATION_NOT_ALLOWED"
    )

    assert result.live_authorized is False


def test_invalid_telemetry_shape_fails_closed() -> None:

    result = observe(
        telemetry=SimpleNamespace(
            execution_id="BAD",
            filled_volume=0.01,
        )
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_FILL_TELEMETRY_SHAPE"
    )


# =============================================================================
# Exact execution linkage
# =============================================================================


def test_partial_fill_volume_is_not_silently_treated_as_full_fill() -> None:

    result = observe(
        telemetry=default_telemetry(
            filled_volume=0.005
        )
    )

    assert result.valid is False

    assert result.reason == (
        "FILLED_VOLUME_MISMATCH"
    )

    assert result.expected_volume == pytest.approx(
        0.01
    )

    assert result.filled_volume == pytest.approx(
        0.005
    )

    assert result.observer_invoked is False


def test_upstream_candidate_volume_mismatch_fails_before_observation() -> None:

    transition = successful_transition(
        candidate_overrides={
            "volume": 0.02
        }
    )

    result = observe(
        transition=transition
    )

    assert result.valid is False

    assert result.reason == (
        "UPSTREAM_EXECUTION_VOLUME_MISMATCH"
    )


def test_direction_linkage_mismatch_fails_closed() -> None:

    transition = successful_transition(
        candidate_overrides={
            "direction": "SHORT"
        }
    )

    result = observe(
        transition=transition
    )

    assert result.valid is False

    assert result.reason == (
        "EXECUTION_DIRECTION_LINKAGE_MISMATCH"
    )


def test_risk_plan_spread_linkage_mismatch_fails_closed() -> None:

    transition = successful_transition(
        risk_overrides={
            "spread_cost": 0.21
        }
    )

    result = observe(
        transition=transition
    )

    assert result.valid is False

    assert result.reason == (
        "RISK_PLAN_SPREAD_LINKAGE_MISMATCH"
    )


def test_risk_friction_entry_mismatch_fails_closed() -> None:

    transition = successful_transition(
        risk_overrides={
            "entry_price": 4316.710
        }
    )

    result = observe(
        transition=transition
    )

    assert result.valid is False

    assert result.reason == (
        "RISK_FRICTION_ENTRY_MISMATCH"
    )


def test_upstream_stop_geometry_mismatch_fails_closed() -> None:

    transition = successful_transition(
        candidate_overrides={
            "structural_stop_distance": 0.60
        }
    )

    result = observe(
        transition=transition
    )

    assert result.valid is False

    assert result.reason == (
        "UPSTREAM_STOP_GEOMETRY_MISMATCH"
    )


def test_upstream_stop_risk_mismatch_fails_closed() -> None:

    transition = successful_transition(
        candidate_overrides={
            "projected_stop_loss": 0.60
        }
    )

    result = observe(
        transition=transition
    )

    assert result.valid is False

    assert result.reason == (
        "UPSTREAM_STOP_RISK_MISMATCH"
    )


def test_risk_friction_spread_price_mismatch_fails_closed() -> None:

    transition = successful_transition(
        friction_overrides={
            "spread_price": 0.21
        }
    )

    result = observe(
        transition=transition
    )

    assert result.valid is False

    assert result.reason == (
        "RISK_FRICTION_SPREAD_PRICE_MISMATCH"
    )


# =============================================================================
# Scale integrity
# =============================================================================


def test_monetary_scale_mismatch_fails_closed() -> None:

    transition = successful_transition(
        spread_after=0.30,
        risk_overrides={
            "spread_cost": 0.30,
        },
        friction_overrides={
            "spread_cost": 0.30,
        },
        candidate_overrides={
            "spread_cost": 0.30,
        },
    )

    result = observe(
        transition=transition
    )

    assert result.valid is False

    assert result.reason == (
        "MONETARY_COST_SCALE_MISMATCH"
    )

    assert result.observer_invoked is False


def test_point_resolution_mismatch_fails_closed() -> None:

    transition = successful_transition(
        risk_overrides={
            "stop_distance_points": 250.0,
        }
    )

    result = observe(
        transition=transition
    )

    assert result.valid is False

    assert result.reason == (
        "RISK_POINT_RESOLUTION_MISMATCH"
    )


# =============================================================================
# Existing observer remains accounting authority
# =============================================================================


def test_lifecycle_raw_spread_booking_mismatch_is_rejected_by_observer() -> None:

    transition = successful_transition(
        spread_after=0.19
    )

    state = Bridge().initial_cost_state()

    result = observe(
        state=state,
        transition=transition,
    )

    assert result.valid is False

    assert result.reason == (
        "REALIZED_COST_OBSERVER_REJECTED"
    )

    assert result.observer_invoked is True

    assert result.observer_reason == (
        "LIFECYCLE_RAW_SPREAD_BOOKING_MISMATCH"
    )

    assert result.cost_state_after == state


def test_duplicate_execution_id_is_rejected_by_existing_cost_accounting() -> None:

    bridge = Bridge()

    state0 = (
        bridge.initial_cost_state()
    )

    telemetry = default_telemetry(
        execution_id="DUP_FILL"
    )

    first = observe(
        bridge=bridge,
        state=state0,
        telemetry=telemetry,
    )

    assert first.valid is True

    second = observe(
        bridge=bridge,
        state=first.cost_state_after,
        telemetry=telemetry,
    )

    assert second.valid is False

    assert second.reason == (
        "REALIZED_COST_OBSERVER_REJECTED"
    )

    assert second.observer_reason == (
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


def test_rejected_lifecycle_never_reaches_observer() -> None:

    transition = successful_transition()

    transition = SimpleNamespace(
        **{
            **transition.__dict__,
            "valid": False,
            "exposure_applied": False,
        }
    )

    result = observe(
        transition=transition
    )

    assert result.valid is False

    assert result.reason == (
        "LIFECYCLE_EXPOSURE_NOT_APPLIED"
    )

    assert result.observer_invoked is False


def test_live_authorized_lifecycle_never_reaches_observer() -> None:

    transition = successful_transition()

    transition = SimpleNamespace(
        **{
            **transition.__dict__,
            "live_authorized": True,
        }
    )

    result = observe(
        transition=transition
    )

    assert result.valid is False

    assert result.reason == (
        "LIFECYCLE_LIVE_AUTHORIZATION_NOT_ALLOWED"
    )

    assert result.observer_invoked is False


# =============================================================================
# Observational behavior under bad realized execution
# =============================================================================


def test_large_adverse_realized_slippage_is_recorded_not_rejected() -> None:

    result = observe(
        telemetry=default_telemetry(
            fill_price=4317.700
        )
    )

    assert result.valid is True

    assert result.realized_slippage_cost == pytest.approx(
        1.0
    )

    record = (
        result.observer_result
        .cost_transition
        .record
    )

    assert record.realized_slippage_cost == pytest.approx(
        1.0
    )

    assert result.lifecycle_pnl_delta == pytest.approx(
        0.0
    )


def test_large_realized_commission_is_recorded_observationally() -> None:

    result = observe(
        telemetry=default_telemetry(
            commission_cost=1.50
        )
    )

    assert result.valid is True

    assert result.realized_commission_cost == pytest.approx(
        1.50
    )

    assert result.lifecycle_pnl_delta == pytest.approx(
        0.0
    )


# =============================================================================
# Observer boundary defense
# =============================================================================


class BoundaryViolatingObserver:
    def __init__(
        self,
        *,
        live_authorized: bool = False,
        lifecycle_pnl_delta: float = 0.10,
    ) -> None:

        self.live_authorized = (
            live_authorized
        )

        self.lifecycle_pnl_delta = (
            lifecycle_pnl_delta
        )

    def observe(
        self,
        **kwargs: Any,
    ) -> Any:

        return SimpleNamespace(
            valid=True,
            observed=True,
            reason="FAKE_OK",
            cost_reason="FAKE_COST_OK",
            live_authorized=self.live_authorized,
            lifecycle_pnl_delta=(
                self.lifecycle_pnl_delta
            ),
            cost_state_after=SimpleNamespace(
                mutated=True
            ),
        )


class RaisingObserver:
    def observe(
        self,
        **kwargs: Any,
    ) -> Any:

        raise RuntimeError(
            "observer failure"
        )


class MalformedObserver:
    def observe(
        self,
        **kwargs: Any,
    ) -> Any:

        return SimpleNamespace(
            valid=True,
            observed=True,
        )


def test_observer_exception_is_fail_closed_and_state_is_unchanged() -> None:

    state = (
        CostAccounting()
        .initial_state()
    )

    bridge = Bridge(
        observer=RaisingObserver()
    )

    result = observe(
        bridge=bridge,
        state=state,
    )

    assert result.valid is False

    assert result.reason == (
        "REALIZED_COST_OBSERVER_EXCEPTION"
    )

    assert result.observer_invoked is True

    assert result.cost_state_after == state


def test_malformed_observer_result_is_fail_closed() -> None:

    state = (
        CostAccounting()
        .initial_state()
    )

    bridge = Bridge(
        observer=MalformedObserver()
    )

    result = observe(
        bridge=bridge,
        state=state,
    )

    assert result.valid is False

    assert result.reason == (
        "INVALID_REALIZED_COST_OBSERVER_RESULT"
    )

    assert result.observer_invoked is True

    assert result.cost_state_after == state


def test_nonzero_observer_lifecycle_delta_is_fail_closed() -> None:

    state = (
        CostAccounting()
        .initial_state()
    )

    bridge = Bridge(
        observer=BoundaryViolatingObserver(
            lifecycle_pnl_delta=0.10,
        )
    )

    result = observe(
        bridge=bridge,
        state=state,
    )

    assert result.valid is False

    assert result.reason == (
        "REALIZED_COST_OBSERVER_BOUNDARY_VIOLATION"
    )

    assert result.cost_state_after == state

    assert result.lifecycle_pnl_delta == pytest.approx(
        0.0
    )


def test_live_authorized_observer_result_is_fail_closed() -> None:

    state = (
        CostAccounting()
        .initial_state()
    )

    bridge = Bridge(
        observer=BoundaryViolatingObserver(
            live_authorized=True,
            lifecycle_pnl_delta=0.0,
        )
    )

    result = observe(
        bridge=bridge,
        state=state,
    )

    assert result.valid is False

    assert result.reason == (
        "REALIZED_COST_OBSERVER_BOUNDARY_VIOLATION"
    )

    assert result.cost_state_after == state

    assert result.live_authorized is False


def test_prevalidation_rejection_never_mutates_cost_state() -> None:

    state = (
        CostAccounting()
        .initial_state()
    )

    result = observe(
        state=state,
        telemetry=default_telemetry(
            filled_volume=0.005
        ),
    )

    assert result.valid is False

    assert result.cost_state_before == state

    assert result.cost_state_after == state