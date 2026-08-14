"""
===============================================================================
Module      : execution_aware_lifecycle_gate.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Shadow Execution-Admission -> Lifecycle Accounting Gate
===============================================================================

RESEARCH / SHADOW / DEMO ONLY.

Purpose
-------
Safely forward an already-evaluated execution-aware compounding admission into
CompoundingLifecycleAccounting.

The boundary is intentionally narrow:

    ExecutionAwareCompoundingAdmission
        -> validate shadow/friction linkage
        -> CompoundingLifecycleAccounting

Safety invariants
-----------------
1. Rejected execution admission never reaches lifecycle accounting.
2. Rejected execution admission returns the exact lifecycle state unchanged.
3. The gate never debits spread, slippage, or commission itself.
4. Lifecycle accounting remains the only component that applies the candidate's
   raw spread_cost to P&L.
5. Candidate spread_cost must equal the friction assessment's raw spread_cost.
   total_friction_cost must NOT be substituted for candidate spread.
6. Slippage and commission remain research estimates at this boundary; they are
   not realized into P&L here.
7. live_authorized is always False.

This module does NOT:
- connect to MT5
- send orders
- open/close real positions
- modify SL/TP
- modify production trade_ready
- modify production RiskEngine
"""

from __future__ import annotations

import importlib
import math
from dataclasses import dataclass
from typing import Any


lifecycle_module: Any = importlib.import_module(
    "02_AI.Shadow.compounding_lifecycle_accounting"
)


CompoundingLifecycleAccounting: Any = (
    lifecycle_module.CompoundingLifecycleAccounting
)


@dataclass(
    frozen=True,
)
class ExecutionAwareLifecycleGateTransition:
    valid: bool

    reason: str

    action: str

    mode: str

    version: str

    live_authorized: bool

    lifecycle_invoked: bool

    state_before: Any

    state_after: Any

    admission_result: Any

    lifecycle_transition: Any


class ExecutionAwareLifecycleGate:
    VERSION = "1.0"

    MODE = "SHADOW_EXECUTION_AWARE_LIFECYCLE_GATE_ONLY"

    _EPSILON = 1e-8

    _REQUIRED_ADMISSION_FIELDS = (
        "valid",
        "admitted",
        "reason",
        "live_authorized",
        "candidate",
        "friction_assessment",
    )

    _REQUIRED_FRICTION_FIELDS = (
        "valid",
        "execution_feasible",
        "live_authorized",
        "direction",
        "volume",
        "spread_cost",
        "total_friction_cost",
    )

    _REQUIRED_CANDIDATE_FIELDS = (
        "leg_id",
        "direction",
        "volume",
        "projected_stop_loss",
        "margin_required",
        "spread_cost",
        "structural_stop_distance",
    )

    def __init__(
        self,
        *,
        lifecycle: Any | None = None,
    ) -> None:

        self.lifecycle = (
            lifecycle
            if lifecycle is not None
            else CompoundingLifecycleAccounting()
        )

    # =========================================================================
    # Helpers
    # =========================================================================

    @staticmethod
    def _number(
        value: float | int | None,
    ) -> float:

        try:

            result = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return math.nan

        if not math.isfinite(
            result
        ):

            return math.nan

        return result

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

    def _transition(
        self,
        *,
        valid: bool,
        reason: str,
        action: str,
        lifecycle_invoked: bool,
        state_before: Any,
        state_after: Any,
        admission_result: Any,
        lifecycle_transition: Any = None,
    ) -> ExecutionAwareLifecycleGateTransition:

        return ExecutionAwareLifecycleGateTransition(
            valid=valid,
            reason=reason,
            action=action,
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            lifecycle_invoked=lifecycle_invoked,
            state_before=state_before,
            state_after=state_after,
            admission_result=admission_result,
            lifecycle_transition=lifecycle_transition,
        )

    def _blocked(
        self,
        *,
        reason: str,
        state: Any,
        admission_result: Any,
    ) -> ExecutionAwareLifecycleGateTransition:

        return self._transition(
            valid=False,
            reason=reason,
            action="NO_ACTION",
            lifecycle_invoked=False,
            state_before=state,
            state_after=state,
            admission_result=admission_result,
        )

    def _validate_admission(
        self,
        admission_result: Any,
    ) -> str | None:

        # ---------------------------------------------------------------------
        # Admission shape
        # ---------------------------------------------------------------------

        if not self._has_fields(
            admission_result,
            self._REQUIRED_ADMISSION_FIELDS,
        ):

            return "INVALID_EXECUTION_ADMISSION_SHAPE"

        if bool(
            admission_result.live_authorized
        ):

            return "LIVE_AUTHORIZATION_NOT_ALLOWED"

        if (
            not bool(
                admission_result.valid
            )
            or
            not bool(
                admission_result.admitted
            )
        ):

            return "EXECUTION_ADMISSION_REJECTED"

        candidate = (
            admission_result.candidate
        )

        friction = (
            admission_result.friction_assessment
        )

        # ---------------------------------------------------------------------
        # Candidate / friction shape
        # ---------------------------------------------------------------------

        if not self._has_fields(
            candidate,
            self._REQUIRED_CANDIDATE_FIELDS,
        ):

            return "INVALID_ADMITTED_CANDIDATE_SHAPE"

        if not self._has_fields(
            friction,
            self._REQUIRED_FRICTION_FIELDS,
        ):

            return "INVALID_FRICTION_ASSESSMENT_SHAPE"

        if bool(
            friction.live_authorized
        ):

            return "FRICTION_LIVE_AUTHORIZATION_NOT_ALLOWED"

        if not bool(
            friction.valid
        ):

            return "FRICTION_ASSESSMENT_INVALID"

        if not bool(
            friction.execution_feasible
        ):

            return "EXECUTION_FRICTION_NOT_FEASIBLE"

        # ---------------------------------------------------------------------
        # Numeric linkage
        # ---------------------------------------------------------------------

        candidate_volume = self._number(
            candidate.volume
        )

        friction_volume = self._number(
            friction.volume
        )

        candidate_spread = self._number(
            candidate.spread_cost
        )

        friction_spread = self._number(
            friction.spread_cost
        )

        total_friction = self._number(
            friction.total_friction_cost
        )

        if (
            not math.isfinite(
                candidate_volume
            )
            or
            not math.isfinite(
                friction_volume
            )
            or
            candidate_volume <= 0.0
            or
            friction_volume <= 0.0
        ):

            return "INVALID_ADMISSION_VOLUME_LINKAGE"

        if (
            abs(
                candidate_volume
                -
                friction_volume
            )
            >
            self._EPSILON
        ):

            return "ADMISSION_VOLUME_MISMATCH"

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

            return "INVALID_ADMISSION_SPREAD_LINKAGE"

        # Critical anti-double-count invariant:
        #
        # BasketLegCandidate.spread_cost must remain RAW spread only.
        if (
            abs(
                candidate_spread
                -
                friction_spread
            )
            >
            self._EPSILON
        ):

            return "CANDIDATE_SPREAD_NOT_RAW_FRICTION_SPREAD"

        if (
            not math.isfinite(
                total_friction
            )
            or
            total_friction < 0.0
        ):

            return "INVALID_TOTAL_FRICTION_COST"

        if (
            total_friction
            +
            self._EPSILON
            <
            friction_spread
        ):

            return "TOTAL_FRICTION_BELOW_RAW_SPREAD"

        # ---------------------------------------------------------------------
        # Direction linkage
        # ---------------------------------------------------------------------

        candidate_direction = str(
            candidate.direction
        ).strip().upper()

        friction_direction = str(
            friction.direction
        ).strip().upper()

        if (
            not candidate_direction
            or
            not friction_direction
        ):

            return "INVALID_ADMISSION_DIRECTION_LINKAGE"

        if (
            candidate_direction
            !=
            friction_direction
        ):

            return "ADMISSION_DIRECTION_MISMATCH"

        return None

    # =========================================================================
    # Start basket from an admitted execution candidate
    # =========================================================================

    def apply_start_admission(
        self,
        *,
        state: Any,
        admission_result: Any,
        volume_min: float,
        volume_step: float,
    ) -> ExecutionAwareLifecycleGateTransition:

        validation_reason = (
            self._validate_admission(
                admission_result
            )
        )

        if validation_reason is not None:

            return self._blocked(
                reason=validation_reason,
                state=state,
                admission_result=admission_result,
            )

        lifecycle_transition = (
            self.lifecycle.start(
                state=state,
                candidates=[
                    admission_result.candidate
                ],
                volume_min=volume_min,
                volume_step=volume_step,
            )
        )

        return self._transition(
            valid=bool(
                lifecycle_transition.valid
            ),
            reason=str(
                lifecycle_transition.reason
            ),
            action=str(
                lifecycle_transition.action
            ),
            lifecycle_invoked=True,
            state_before=state,
            state_after=(
                lifecycle_transition.state_after
            ),
            admission_result=admission_result,
            lifecycle_transition=lifecycle_transition,
        )

    # =========================================================================
    # Add exposure from an admitted execution candidate
    # =========================================================================

    def apply_addon_admission(
        self,
        *,
        state: Any,
        admission_result: Any,
        current_market_floating_profit: float,
        volume_min: float,
        volume_step: float,
        structure_invalidated: bool = False,
    ) -> ExecutionAwareLifecycleGateTransition:

        validation_reason = (
            self._validate_admission(
                admission_result
            )
        )

        if validation_reason is not None:

            return self._blocked(
                reason=validation_reason,
                state=state,
                admission_result=admission_result,
            )

        lifecycle_transition = (
            self.lifecycle.step(
                state=state,
                current_market_floating_profit=(
                    current_market_floating_profit
                ),
                volume_min=volume_min,
                volume_step=volume_step,
                add_candidates=[
                    admission_result.candidate
                ],
                structure_invalidated=(
                    structure_invalidated
                ),
            )
        )

        return self._transition(
            valid=bool(
                lifecycle_transition.valid
            ),
            reason=str(
                lifecycle_transition.reason
            ),
            action=str(
                lifecycle_transition.action
            ),
            lifecycle_invoked=True,
            state_before=state,
            state_after=(
                lifecycle_transition.state_after
            ),
            admission_result=admission_result,
            lifecycle_transition=lifecycle_transition,
        )


execution_aware_lifecycle_gate = (
    ExecutionAwareLifecycleGate()
)