"""
===============================================================================
Module      : realized_execution_cost_accounting.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Shadow Realized Execution Cost Accounting
===============================================================================

Status
------
SHADOW / RESEARCH / DEMO ONLY.

Purpose
-------
Record estimated versus realized execution costs without modifying the existing
compounding P&L lifecycle.

The existing lifecycle remains authoritative for its current RAW spread debit.

This module observes:

    estimated spread
    realized spread, when available

    estimated slippage
    realized slippage, when available

    estimated commission
    realized commission, when available

and derives execution-cost variance.

Important accounting boundary
-----------------------------
This module MUST NOT:

- debit spread into lifecycle P&L
- debit slippage into lifecycle P&L
- debit commission into lifecycle P&L
- replace candidate.spread_cost
- substitute total friction for raw spread
- mutate CompoundingPnLLedger
- mutate CompoundingLifecycleAccounting
- authorize live execution

Realized slippage cost may be negative because favorable execution / price
improvement is possible.

Missing realized values remain explicitly unavailable. They are never silently
treated as zero.

Safety
------
Every state/result:

    live_authorized = False

Every successful transition:

    lifecycle_pnl_delta = 0.0

Therefore this layer is observational only.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass(
    frozen=True,
)
class RealizedExecutionCostState:
    execution_ids: tuple[
        str,
        ...,
    ]

    observation_count: int

    complete_observation_count: int

    realized_spread_observation_count: int

    realized_slippage_observation_count: int

    realized_commission_observation_count: int

    cumulative_estimated_spread_cost: float

    cumulative_realized_spread_cost: float

    cumulative_estimated_slippage_cost: float

    cumulative_realized_slippage_cost: float

    cumulative_estimated_commission_cost: float

    cumulative_realized_commission_cost: float

    cumulative_estimated_total_friction: float

    cumulative_comparable_estimated_cost: float

    cumulative_comparable_realized_cost: float

    cumulative_comparable_variance: float

    cumulative_complete_estimated_cost: float

    cumulative_complete_realized_cost: float

    cumulative_complete_variance: float

    live_authorized: bool


@dataclass(
    frozen=True,
)
class RealizedExecutionCostRecord:
    execution_id: str

    estimated_spread_cost: float

    estimated_slippage_cost: float

    estimated_commission_cost: float

    estimated_total_friction: float

    realized_spread_available: bool

    realized_spread_cost: float | None

    realized_slippage_available: bool

    realized_slippage_cost: float | None

    realized_commission_available: bool

    realized_commission_cost: float | None

    realized_cost_complete: bool

    comparable_estimated_cost: float

    comparable_realized_cost: float

    comparable_variance: float

    spread_variance: float | None

    slippage_variance: float | None

    commission_variance: float | None

    complete_realized_total_cost: float | None

    complete_execution_cost_variance: float | None

    lifecycle_pnl_delta: float

    live_authorized: bool


@dataclass(
    frozen=True,
)
class RealizedExecutionCostTransition:
    valid: bool

    reason: str

    action: str

    mode: str

    version: str

    live_authorized: bool

    state_before: RealizedExecutionCostState

    state_after: RealizedExecutionCostState

    record: RealizedExecutionCostRecord | None

    lifecycle_pnl_delta: float


class RealizedExecutionCostAccounting:
    VERSION = "1.0"

    MODE = (
        "SHADOW_REALIZED_EXECUTION_COST_ACCOUNTING_ONLY"
    )

    _EPSILON = 1e-8

    _REQUIRED_FRICTION_FIELDS = (
        "valid",
        "execution_feasible",
        "live_authorized",
        "spread_cost",
        "estimated_slippage_cost",
        "estimated_commission_cost",
        "total_friction_cost",
    )

    # =========================================================================
    # State
    # =========================================================================

    def initial_state(
        self,
    ) -> RealizedExecutionCostState:

        return self._state(
            execution_ids=(),
            observation_count=0,
            complete_observation_count=0,
            realized_spread_observation_count=0,
            realized_slippage_observation_count=0,
            realized_commission_observation_count=0,
            cumulative_estimated_spread_cost=0.0,
            cumulative_realized_spread_cost=0.0,
            cumulative_estimated_slippage_cost=0.0,
            cumulative_realized_slippage_cost=0.0,
            cumulative_estimated_commission_cost=0.0,
            cumulative_realized_commission_cost=0.0,
            cumulative_estimated_total_friction=0.0,
            cumulative_comparable_estimated_cost=0.0,
            cumulative_comparable_realized_cost=0.0,
            cumulative_complete_estimated_cost=0.0,
            cumulative_complete_realized_cost=0.0,
        )

    def _state(
        self,
        *,
        execution_ids: tuple[
            str,
            ...,
        ],
        observation_count: int,
        complete_observation_count: int,
        realized_spread_observation_count: int,
        realized_slippage_observation_count: int,
        realized_commission_observation_count: int,
        cumulative_estimated_spread_cost: float,
        cumulative_realized_spread_cost: float,
        cumulative_estimated_slippage_cost: float,
        cumulative_realized_slippage_cost: float,
        cumulative_estimated_commission_cost: float,
        cumulative_realized_commission_cost: float,
        cumulative_estimated_total_friction: float,
        cumulative_comparable_estimated_cost: float,
        cumulative_comparable_realized_cost: float,
        cumulative_complete_estimated_cost: float,
        cumulative_complete_realized_cost: float,
    ) -> RealizedExecutionCostState:

        return RealizedExecutionCostState(
            execution_ids=execution_ids,
            observation_count=observation_count,
            complete_observation_count=(
                complete_observation_count
            ),
            realized_spread_observation_count=(
                realized_spread_observation_count
            ),
            realized_slippage_observation_count=(
                realized_slippage_observation_count
            ),
            realized_commission_observation_count=(
                realized_commission_observation_count
            ),
            cumulative_estimated_spread_cost=round(
                cumulative_estimated_spread_cost,
                8,
            ),
            cumulative_realized_spread_cost=round(
                cumulative_realized_spread_cost,
                8,
            ),
            cumulative_estimated_slippage_cost=round(
                cumulative_estimated_slippage_cost,
                8,
            ),
            cumulative_realized_slippage_cost=round(
                cumulative_realized_slippage_cost,
                8,
            ),
            cumulative_estimated_commission_cost=round(
                cumulative_estimated_commission_cost,
                8,
            ),
            cumulative_realized_commission_cost=round(
                cumulative_realized_commission_cost,
                8,
            ),
            cumulative_estimated_total_friction=round(
                cumulative_estimated_total_friction,
                8,
            ),
            cumulative_comparable_estimated_cost=round(
                cumulative_comparable_estimated_cost,
                8,
            ),
            cumulative_comparable_realized_cost=round(
                cumulative_comparable_realized_cost,
                8,
            ),
            cumulative_comparable_variance=round(
                (
                    cumulative_comparable_realized_cost
                    -
                    cumulative_comparable_estimated_cost
                ),
                8,
            ),
            cumulative_complete_estimated_cost=round(
                cumulative_complete_estimated_cost,
                8,
            ),
            cumulative_complete_realized_cost=round(
                cumulative_complete_realized_cost,
                8,
            ),
            cumulative_complete_variance=round(
                (
                    cumulative_complete_realized_cost
                    -
                    cumulative_complete_estimated_cost
                ),
                8,
            ),
            live_authorized=False,
        )

    # =========================================================================
    # Numeric / shape helpers
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

    # =========================================================================
    # Transition helpers
    # =========================================================================

    def _invalid(
        self,
        *,
        state: RealizedExecutionCostState,
        reason: str,
    ) -> RealizedExecutionCostTransition:

        return RealizedExecutionCostTransition(
            valid=False,
            reason=reason,
            action="NO_ACTION",
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            state_before=state,
            state_after=state,
            record=None,
            lifecycle_pnl_delta=0.0,
        )

    def _transition(
        self,
        *,
        state_before: RealizedExecutionCostState,
        state_after: RealizedExecutionCostState,
        record: RealizedExecutionCostRecord,
    ) -> RealizedExecutionCostTransition:

        return RealizedExecutionCostTransition(
            valid=True,
            reason="OK_REALIZED_EXECUTION_COST_RECORDED",
            action="RECORD_EXECUTION_COST",
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            state_before=state_before,
            state_after=state_after,
            record=record,
            lifecycle_pnl_delta=0.0,
        )

    # =========================================================================
    # Main accounting operation
    # =========================================================================

    def record_execution(
        self,
        *,
        state: RealizedExecutionCostState,
        execution_id: str,
        friction_assessment: Any,
        realized_spread_cost: float | None = None,
        realized_slippage_cost: float | None = None,
        realized_commission_cost: float | None = None,
    ) -> RealizedExecutionCostTransition:

        resolved_execution_id = str(
            execution_id
        ).strip()

        if not resolved_execution_id:

            return self._invalid(
                state=state,
                reason="INVALID_EXECUTION_ID",
            )

        if (
            resolved_execution_id
            in
            state.execution_ids
        ):

            return self._invalid(
                state=state,
                reason="DUPLICATE_EXECUTION_ID",
            )

        if not self._has_fields(
            friction_assessment,
            self._REQUIRED_FRICTION_FIELDS,
        ):

            return self._invalid(
                state=state,
                reason="INVALID_FRICTION_ASSESSMENT_SHAPE",
            )

        if bool(
            friction_assessment.live_authorized
        ):

            return self._invalid(
                state=state,
                reason="LIVE_AUTHORIZATION_NOT_ALLOWED",
            )

        if not bool(
            friction_assessment.valid
        ):

            return self._invalid(
                state=state,
                reason="FRICTION_ASSESSMENT_REJECTED",
            )

        if not bool(
            friction_assessment.execution_feasible
        ):

            return self._invalid(
                state=state,
                reason="EXECUTION_FRICTION_BLOCKED",
            )

        estimated_spread = self._number(
            friction_assessment.spread_cost
        )

        estimated_slippage = self._number(
            friction_assessment.estimated_slippage_cost
        )

        estimated_commission = self._number(
            friction_assessment.estimated_commission_cost
        )

        estimated_total = self._number(
            friction_assessment.total_friction_cost
        )

        if (
            not math.isfinite(
                estimated_spread
            )
            or
            not math.isfinite(
                estimated_slippage
            )
            or
            not math.isfinite(
                estimated_commission
            )
            or
            not math.isfinite(
                estimated_total
            )
            or
            estimated_spread < 0.0
            or
            estimated_slippage < 0.0
            or
            estimated_commission < 0.0
            or
            estimated_total < 0.0
        ):

            return self._invalid(
                state=state,
                reason="INVALID_ESTIMATED_EXECUTION_COST",
            )

        component_total = (
            estimated_spread
            +
            estimated_slippage
            +
            estimated_commission
        )

        if (
            abs(
                component_total
                -
                estimated_total
            )
            >
            self._EPSILON
        ):

            return self._invalid(
                state=state,
                reason=(
                    "ESTIMATED_FRICTION_COMPONENT_MISMATCH"
                ),
            )

        spread_available = (
            realized_spread_cost
            is not None
        )

        slippage_available = (
            realized_slippage_cost
            is not None
        )

        commission_available = (
            realized_commission_cost
            is not None
        )

        if not (
            spread_available
            or
            slippage_available
            or
            commission_available
        ):

            return self._invalid(
                state=state,
                reason="NO_REALIZED_COST_OBSERVATION",
            )

        realized_spread: float | None = None

        realized_slippage: float | None = None

        realized_commission: float | None = None

        if spread_available:

            resolved = self._number(
                realized_spread_cost
            )

            if (
                not math.isfinite(
                    resolved
                )
                or
                resolved < 0.0
            ):

                return self._invalid(
                    state=state,
                    reason="INVALID_REALIZED_SPREAD_COST",
                )

            realized_spread = resolved

        if slippage_available:

            resolved = self._number(
                realized_slippage_cost
            )

            if not math.isfinite(
                resolved
            ):

                return self._invalid(
                    state=state,
                    reason="INVALID_REALIZED_SLIPPAGE_COST",
                )

            # Signed value is intentional:
            # negative = favorable slippage / price improvement.
            realized_slippage = resolved

        if commission_available:

            resolved = self._number(
                realized_commission_cost
            )

            if (
                not math.isfinite(
                    resolved
                )
                or
                resolved < 0.0
            ):

                return self._invalid(
                    state=state,
                    reason=(
                        "INVALID_REALIZED_COMMISSION_COST"
                    ),
                )

            realized_commission = resolved

        comparable_estimated = 0.0

        comparable_realized = 0.0

        if spread_available:

            comparable_estimated += (
                estimated_spread
            )

            comparable_realized += float(
                realized_spread
            )

        if slippage_available:

            comparable_estimated += (
                estimated_slippage
            )

            comparable_realized += float(
                realized_slippage
            )

        if commission_available:

            comparable_estimated += (
                estimated_commission
            )

            comparable_realized += float(
                realized_commission
            )

        comparable_variance = (
            comparable_realized
            -
            comparable_estimated
        )

        spread_variance = (
            (
                float(
                    realized_spread
                )
                -
                estimated_spread
            )
            if spread_available
            else None
        )

        slippage_variance = (
            (
                float(
                    realized_slippage
                )
                -
                estimated_slippage
            )
            if slippage_available
            else None
        )

        commission_variance = (
            (
                float(
                    realized_commission
                )
                -
                estimated_commission
            )
            if commission_available
            else None
        )

        complete = (
            spread_available
            and
            slippage_available
            and
            commission_available
        )

        complete_realized_total: float | None = None

        complete_variance: float | None = None

        if complete:

            complete_realized_total = (
                float(
                    realized_spread
                )
                +
                float(
                    realized_slippage
                )
                +
                float(
                    realized_commission
                )
            )

            complete_variance = (
                complete_realized_total
                -
                estimated_total
            )

        record = RealizedExecutionCostRecord(
            execution_id=resolved_execution_id,
            estimated_spread_cost=round(
                estimated_spread,
                8,
            ),
            estimated_slippage_cost=round(
                estimated_slippage,
                8,
            ),
            estimated_commission_cost=round(
                estimated_commission,
                8,
            ),
            estimated_total_friction=round(
                estimated_total,
                8,
            ),
            realized_spread_available=(
                spread_available
            ),
            realized_spread_cost=(
                round(
                    float(
                        realized_spread
                    ),
                    8,
                )
                if spread_available
                else None
            ),
            realized_slippage_available=(
                slippage_available
            ),
            realized_slippage_cost=(
                round(
                    float(
                        realized_slippage
                    ),
                    8,
                )
                if slippage_available
                else None
            ),
            realized_commission_available=(
                commission_available
            ),
            realized_commission_cost=(
                round(
                    float(
                        realized_commission
                    ),
                    8,
                )
                if commission_available
                else None
            ),
            realized_cost_complete=complete,
            comparable_estimated_cost=round(
                comparable_estimated,
                8,
            ),
            comparable_realized_cost=round(
                comparable_realized,
                8,
            ),
            comparable_variance=round(
                comparable_variance,
                8,
            ),
            spread_variance=(
                round(
                    spread_variance,
                    8,
                )
                if spread_variance is not None
                else None
            ),
            slippage_variance=(
                round(
                    slippage_variance,
                    8,
                )
                if slippage_variance is not None
                else None
            ),
            commission_variance=(
                round(
                    commission_variance,
                    8,
                )
                if commission_variance is not None
                else None
            ),
            complete_realized_total_cost=(
                round(
                    complete_realized_total,
                    8,
                )
                if complete_realized_total
                is not None
                else None
            ),
            complete_execution_cost_variance=(
                round(
                    complete_variance,
                    8,
                )
                if complete_variance
                is not None
                else None
            ),
            lifecycle_pnl_delta=0.0,
            live_authorized=False,
        )

        state_after = self._state(
            execution_ids=(
                state.execution_ids
                +
                (
                    resolved_execution_id,
                )
            ),
            observation_count=(
                state.observation_count
                +
                1
            ),
            complete_observation_count=(
                state.complete_observation_count
                +
                (
                    1
                    if complete
                    else 0
                )
            ),
            realized_spread_observation_count=(
                state.realized_spread_observation_count
                +
                (
                    1
                    if spread_available
                    else 0
                )
            ),
            realized_slippage_observation_count=(
                state.realized_slippage_observation_count
                +
                (
                    1
                    if slippage_available
                    else 0
                )
            ),
            realized_commission_observation_count=(
                state.realized_commission_observation_count
                +
                (
                    1
                    if commission_available
                    else 0
                )
            ),
            cumulative_estimated_spread_cost=(
                state.cumulative_estimated_spread_cost
                +
                estimated_spread
            ),
            cumulative_realized_spread_cost=(
                state.cumulative_realized_spread_cost
                +
                (
                    float(
                        realized_spread
                    )
                    if spread_available
                    else 0.0
                )
            ),
            cumulative_estimated_slippage_cost=(
                state.cumulative_estimated_slippage_cost
                +
                estimated_slippage
            ),
            cumulative_realized_slippage_cost=(
                state.cumulative_realized_slippage_cost
                +
                (
                    float(
                        realized_slippage
                    )
                    if slippage_available
                    else 0.0
                )
            ),
            cumulative_estimated_commission_cost=(
                state.cumulative_estimated_commission_cost
                +
                estimated_commission
            ),
            cumulative_realized_commission_cost=(
                state.cumulative_realized_commission_cost
                +
                (
                    float(
                        realized_commission
                    )
                    if commission_available
                    else 0.0
                )
            ),
            cumulative_estimated_total_friction=(
                state.cumulative_estimated_total_friction
                +
                estimated_total
            ),
            cumulative_comparable_estimated_cost=(
                state.cumulative_comparable_estimated_cost
                +
                comparable_estimated
            ),
            cumulative_comparable_realized_cost=(
                state.cumulative_comparable_realized_cost
                +
                comparable_realized
            ),
            cumulative_complete_estimated_cost=(
                state.cumulative_complete_estimated_cost
                +
                (
                    estimated_total
                    if complete
                    else 0.0
                )
            ),
            cumulative_complete_realized_cost=(
                state.cumulative_complete_realized_cost
                +
                (
                    float(
                        complete_realized_total
                    )
                    if complete_realized_total
                    is not None
                    else 0.0
                )
            ),
        )

        return self._transition(
            state_before=state,
            state_after=state_after,
            record=record,
        )


realized_execution_cost_accounting = (
    RealizedExecutionCostAccounting()
)