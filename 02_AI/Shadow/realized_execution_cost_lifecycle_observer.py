"""
===============================================================================
Module      : realized_execution_cost_lifecycle_observer.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Shadow Lifecycle -> Realized Execution Cost Observation Bridge
===============================================================================

Status
------
SHADOW / RESEARCH / DEMO ONLY.

Purpose
-------
Observe realized execution-cost telemetry only after a successful protected,
risk-reconciled lifecycle exposure transition.

Flow
----
Successful RiskReconciledAccountProtectedLifecycleTransition
    -> validate execution/admission linkage
    -> verify RAW spread was already booked exactly once by lifecycle
    -> RealizedExecutionCostAccounting

Critical accounting boundary
----------------------------
The existing lifecycle remains authoritative for RAW spread P&L booking.

This observer:

- does NOT debit spread
- does NOT debit slippage
- does NOT debit commission
- does NOT mutate lifecycle state
- does NOT call lifecycle
- does NOT call admission
- does NOT replace candidate.spread_cost
- does NOT substitute total friction for raw spread
- does NOT authorize live execution

A successful observation requires:

    lifecycle cumulative spread delta
    ==
    admission candidate.spread_cost
    ==
    friction assessment.spread_cost

within numerical tolerance.

The realized-cost ledger remains observational:

    lifecycle_pnl_delta = 0.0
"""

from __future__ import annotations

import importlib
import math
from dataclasses import dataclass
from typing import Any


cost_module: Any = importlib.import_module(
    "02_AI.Shadow.realized_execution_cost_accounting"
)

RealizedExecutionCostAccounting: Any = (
    cost_module.RealizedExecutionCostAccounting
)


@dataclass(
    frozen=True,
)
class RealizedExecutionCostLifecycleObservation:
    valid: bool

    observed: bool

    reason: str

    cost_reason: str

    action: str

    mode: str

    version: str

    live_authorized: bool

    execution_id: str

    expected_raw_spread_cost: float

    lifecycle_spread_delta: float

    lifecycle_pnl_delta: float

    lifecycle_transition: Any

    cost_state_before: Any

    cost_state_after: Any

    cost_transition: Any


class RealizedExecutionCostLifecycleObserver:
    VERSION = "1.0"

    MODE = (
        "SHADOW_REALIZED_EXECUTION_COST_LIFECYCLE_OBSERVER_ONLY"
    )

    _EPSILON = 1e-8

    _REQUIRED_LIFECYCLE_FIELDS = (
        "valid",
        "exposure_applied",
        "live_authorized",
        "lifecycle_invoked",
        "lifecycle_state_before",
        "lifecycle_state_after",
        "protected_admission_result",
    )

    _REQUIRED_PROTECTED_FIELDS = (
        "live_authorized",
        "admission_result",
    )

    _REQUIRED_ADMISSION_FIELDS = (
        "valid",
        "admitted",
        "live_authorized",
        "friction_assessment",
        "candidate",
    )

    _REQUIRED_FRICTION_FIELDS = (
        "live_authorized",
        "spread_cost",
    )

    _REQUIRED_CANDIDATE_FIELDS = (
        "spread_cost",
    )

    _REQUIRED_LIFECYCLE_STATE_FIELDS = (
        "pnl_state",
    )

    _REQUIRED_PNL_FIELDS = (
        "cumulative_spread_cost",
    )

    def __init__(
        self,
        *,
        accounting: Any | None = None,
    ) -> None:

        self.accounting = (
            accounting
            if accounting is not None
            else RealizedExecutionCostAccounting()
        )

    # =========================================================================
    # Helpers
    # =========================================================================

    @staticmethod
    def _has_fields(
        value: Any,
        fields: tuple[
            str,
            ...,
        ],
    ) -> bool:

        if value is None:

            return False

        return all(
            hasattr(
                value,
                field,
            )
            for field
            in fields
        )

    @staticmethod
    def _number(
        value: float | int | None,
    ) -> float:

        try:

            resolved = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return math.nan

        if not math.isfinite(
            resolved
        ):

            return math.nan

        return resolved

    def _result(
        self,
        *,
        valid: bool,
        observed: bool,
        reason: str,
        cost_reason: str,
        execution_id: str,
        lifecycle_transition: Any,
        cost_state_before: Any,
        cost_state_after: Any,
        cost_transition: Any = None,
        expected_raw_spread_cost: float = 0.0,
        lifecycle_spread_delta: float = 0.0,
    ) -> RealizedExecutionCostLifecycleObservation:

        return RealizedExecutionCostLifecycleObservation(
            valid=valid,
            observed=observed,
            reason=reason,
            cost_reason=cost_reason,
            action=(
                "OBSERVE_REALIZED_EXECUTION_COST"
                if observed
                else
                "NO_ACTION"
            ),
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            execution_id=execution_id,
            expected_raw_spread_cost=round(
                expected_raw_spread_cost,
                8,
            ),
            lifecycle_spread_delta=round(
                lifecycle_spread_delta,
                8,
            ),
            lifecycle_pnl_delta=0.0,
            lifecycle_transition=lifecycle_transition,
            cost_state_before=cost_state_before,
            cost_state_after=cost_state_after,
            cost_transition=cost_transition,
        )

    def _invalid(
        self,
        *,
        reason: str,
        execution_id: str,
        lifecycle_transition: Any,
        cost_state: Any,
        cost_transition: Any = None,
        cost_reason: str = "",
        expected_raw_spread_cost: float = 0.0,
        lifecycle_spread_delta: float = 0.0,
    ) -> RealizedExecutionCostLifecycleObservation:

        return self._result(
            valid=False,
            observed=False,
            reason=reason,
            cost_reason=cost_reason,
            execution_id=execution_id,
            lifecycle_transition=lifecycle_transition,
            cost_state_before=cost_state,
            cost_state_after=cost_state,
            cost_transition=cost_transition,
            expected_raw_spread_cost=(
                expected_raw_spread_cost
            ),
            lifecycle_spread_delta=(
                lifecycle_spread_delta
            ),
        )

    # =========================================================================
    # Lifecycle spread reconciliation
    # =========================================================================

    def _lifecycle_spread_delta(
        self,
        *,
        lifecycle_transition: Any,
    ) -> tuple[
        bool,
        str,
        float,
    ]:

        state_before = (
            lifecycle_transition.lifecycle_state_before
        )

        state_after = (
            lifecycle_transition.lifecycle_state_after
        )

        if (
            not self._has_fields(
                state_before,
                self._REQUIRED_LIFECYCLE_STATE_FIELDS,
            )
            or
            not self._has_fields(
                state_after,
                self._REQUIRED_LIFECYCLE_STATE_FIELDS,
            )
        ):

            return (
                False,
                "INVALID_LIFECYCLE_STATE_SHAPE",
                0.0,
            )

        pnl_before = (
            state_before.pnl_state
        )

        pnl_after = (
            state_after.pnl_state
        )

        if (
            not self._has_fields(
                pnl_before,
                self._REQUIRED_PNL_FIELDS,
            )
            or
            not self._has_fields(
                pnl_after,
                self._REQUIRED_PNL_FIELDS,
            )
        ):

            return (
                False,
                "INVALID_LIFECYCLE_PNL_STATE_SHAPE",
                0.0,
            )

        spread_before = self._number(
            pnl_before.cumulative_spread_cost
        )

        spread_after = self._number(
            pnl_after.cumulative_spread_cost
        )

        if (
            not math.isfinite(
                spread_before
            )
            or
            not math.isfinite(
                spread_after
            )
            or
            spread_before < 0.0
            or
            spread_after < 0.0
        ):

            return (
                False,
                "INVALID_LIFECYCLE_SPREAD_STATE",
                0.0,
            )

        spread_delta = (
            spread_after
            -
            spread_before
        )

        if spread_delta < -self._EPSILON:

            return (
                False,
                "LIFECYCLE_SPREAD_MOVED_BACKWARD",
                spread_delta,
            )

        return (
            True,
            "",
            max(
                0.0,
                spread_delta,
            ),
        )

    # =========================================================================
    # Main observer
    # =========================================================================

    def observe(
        self,
        *,
        cost_state: Any,
        execution_id: str,
        lifecycle_transition: Any,
        realized_spread_cost: float | None = None,
        realized_slippage_cost: float | None = None,
        realized_commission_cost: float | None = None,
    ) -> RealizedExecutionCostLifecycleObservation:

        resolved_execution_id = str(
            execution_id
        ).strip()

        if not resolved_execution_id:

            return self._invalid(
                reason="INVALID_EXECUTION_ID",
                execution_id="",
                lifecycle_transition=lifecycle_transition,
                cost_state=cost_state,
            )

        if not self._has_fields(
            lifecycle_transition,
            self._REQUIRED_LIFECYCLE_FIELDS,
        ):

            return self._invalid(
                reason="INVALID_LIFECYCLE_TRANSITION_SHAPE",
                execution_id=resolved_execution_id,
                lifecycle_transition=lifecycle_transition,
                cost_state=cost_state,
            )

        if bool(
            lifecycle_transition.live_authorized
        ):

            return self._invalid(
                reason="LIFECYCLE_LIVE_AUTHORIZATION_NOT_ALLOWED",
                execution_id=resolved_execution_id,
                lifecycle_transition=lifecycle_transition,
                cost_state=cost_state,
            )

        if (
            not bool(
                lifecycle_transition.valid
            )
            or
            not bool(
                lifecycle_transition.exposure_applied
            )
        ):

            return self._invalid(
                reason="LIFECYCLE_EXPOSURE_NOT_APPLIED",
                execution_id=resolved_execution_id,
                lifecycle_transition=lifecycle_transition,
                cost_state=cost_state,
            )

        if not bool(
            lifecycle_transition.lifecycle_invoked
        ):

            return self._invalid(
                reason="LIFECYCLE_NOT_INVOKED",
                execution_id=resolved_execution_id,
                lifecycle_transition=lifecycle_transition,
                cost_state=cost_state,
            )

        protected_result = (
            lifecycle_transition.protected_admission_result
        )

        if not self._has_fields(
            protected_result,
            self._REQUIRED_PROTECTED_FIELDS,
        ):

            return self._invalid(
                reason="INVALID_PROTECTED_ADMISSION_SHAPE",
                execution_id=resolved_execution_id,
                lifecycle_transition=lifecycle_transition,
                cost_state=cost_state,
            )

        if bool(
            protected_result.live_authorized
        ):

            return self._invalid(
                reason="PROTECTED_LIVE_AUTHORIZATION_NOT_ALLOWED",
                execution_id=resolved_execution_id,
                lifecycle_transition=lifecycle_transition,
                cost_state=cost_state,
            )

        admission_result = (
            protected_result.admission_result
        )

        if not self._has_fields(
            admission_result,
            self._REQUIRED_ADMISSION_FIELDS,
        ):

            return self._invalid(
                reason="INVALID_EXECUTION_ADMISSION_SHAPE",
                execution_id=resolved_execution_id,
                lifecycle_transition=lifecycle_transition,
                cost_state=cost_state,
            )

        if bool(
            admission_result.live_authorized
        ):

            return self._invalid(
                reason="ADMISSION_LIVE_AUTHORIZATION_NOT_ALLOWED",
                execution_id=resolved_execution_id,
                lifecycle_transition=lifecycle_transition,
                cost_state=cost_state,
            )

        if (
            not bool(
                admission_result.valid
            )
            or
            not bool(
                admission_result.admitted
            )
        ):

            return self._invalid(
                reason="EXECUTION_ADMISSION_REJECTED",
                execution_id=resolved_execution_id,
                lifecycle_transition=lifecycle_transition,
                cost_state=cost_state,
            )

        friction_assessment = (
            admission_result.friction_assessment
        )

        candidate = (
            admission_result.candidate
        )

        if not self._has_fields(
            friction_assessment,
            self._REQUIRED_FRICTION_FIELDS,
        ):

            return self._invalid(
                reason="INVALID_FRICTION_ASSESSMENT_SHAPE",
                execution_id=resolved_execution_id,
                lifecycle_transition=lifecycle_transition,
                cost_state=cost_state,
            )

        if bool(
            friction_assessment.live_authorized
        ):

            return self._invalid(
                reason="FRICTION_LIVE_AUTHORIZATION_NOT_ALLOWED",
                execution_id=resolved_execution_id,
                lifecycle_transition=lifecycle_transition,
                cost_state=cost_state,
            )

        if not self._has_fields(
            candidate,
            self._REQUIRED_CANDIDATE_FIELDS,
        ):

            return self._invalid(
                reason="INVALID_CANDIDATE_SHAPE",
                execution_id=resolved_execution_id,
                lifecycle_transition=lifecycle_transition,
                cost_state=cost_state,
            )

        candidate_spread = self._number(
            candidate.spread_cost
        )

        friction_spread = self._number(
            friction_assessment.spread_cost
        )

        if (
            not math.isfinite(
                candidate_spread
            )
            or
            not math.isfinite(
                friction_spread
            )
            or
            candidate_spread < 0.0
            or
            friction_spread < 0.0
        ):

            return self._invalid(
                reason="INVALID_RAW_SPREAD_LINKAGE",
                execution_id=resolved_execution_id,
                lifecycle_transition=lifecycle_transition,
                cost_state=cost_state,
            )

        if (
            abs(
                candidate_spread
                -
                friction_spread
            )
            >
            self._EPSILON
        ):

            return self._invalid(
                reason="CANDIDATE_FRICTION_SPREAD_MISMATCH",
                execution_id=resolved_execution_id,
                lifecycle_transition=lifecycle_transition,
                cost_state=cost_state,
                expected_raw_spread_cost=candidate_spread,
            )

        (
            spread_state_valid,
            spread_state_reason,
            lifecycle_spread_delta,
        ) = self._lifecycle_spread_delta(
            lifecycle_transition=lifecycle_transition,
        )

        if not spread_state_valid:

            return self._invalid(
                reason=spread_state_reason,
                execution_id=resolved_execution_id,
                lifecycle_transition=lifecycle_transition,
                cost_state=cost_state,
                expected_raw_spread_cost=candidate_spread,
                lifecycle_spread_delta=(
                    lifecycle_spread_delta
                ),
            )

        if (
            abs(
                lifecycle_spread_delta
                -
                candidate_spread
            )
            >
            self._EPSILON
        ):

            return self._invalid(
                reason="LIFECYCLE_RAW_SPREAD_BOOKING_MISMATCH",
                execution_id=resolved_execution_id,
                lifecycle_transition=lifecycle_transition,
                cost_state=cost_state,
                expected_raw_spread_cost=candidate_spread,
                lifecycle_spread_delta=(
                    lifecycle_spread_delta
                ),
            )

        cost_transition = (
            self.accounting.record_execution(
                state=cost_state,
                execution_id=resolved_execution_id,
                friction_assessment=friction_assessment,
                realized_spread_cost=(
                    realized_spread_cost
                ),
                realized_slippage_cost=(
                    realized_slippage_cost
                ),
                realized_commission_cost=(
                    realized_commission_cost
                ),
            )
        )

        if not bool(
            cost_transition.valid
        ):

            return self._invalid(
                reason="REALIZED_COST_ACCOUNTING_REJECTED",
                cost_reason=str(
                    cost_transition.reason
                ),
                execution_id=resolved_execution_id,
                lifecycle_transition=lifecycle_transition,
                cost_state=cost_state,
                cost_transition=cost_transition,
                expected_raw_spread_cost=candidate_spread,
                lifecycle_spread_delta=(
                    lifecycle_spread_delta
                ),
            )

        if (
            bool(
                cost_transition.live_authorized
            )
            or
            abs(
                float(
                    cost_transition.lifecycle_pnl_delta
                )
            )
            >
            self._EPSILON
        ):

            return self._invalid(
                reason="REALIZED_COST_ACCOUNTING_BOUNDARY_VIOLATION",
                cost_reason=str(
                    cost_transition.reason
                ),
                execution_id=resolved_execution_id,
                lifecycle_transition=lifecycle_transition,
                cost_state=cost_state,
                cost_transition=cost_transition,
                expected_raw_spread_cost=candidate_spread,
                lifecycle_spread_delta=(
                    lifecycle_spread_delta
                ),
            )

        return self._result(
            valid=True,
            observed=True,
            reason=(
                "OK_REALIZED_EXECUTION_COST_LIFECYCLE_OBSERVATION"
            ),
            cost_reason=str(
                cost_transition.reason
            ),
            execution_id=resolved_execution_id,
            lifecycle_transition=lifecycle_transition,
            cost_state_before=cost_state,
            cost_state_after=(
                cost_transition.state_after
            ),
            cost_transition=cost_transition,
            expected_raw_spread_cost=candidate_spread,
            lifecycle_spread_delta=(
                lifecycle_spread_delta
            ),
        )


realized_execution_cost_lifecycle_observer = (
    RealizedExecutionCostLifecycleObserver()
)