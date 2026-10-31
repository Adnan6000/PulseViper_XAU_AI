"""
===============================================================================
Module      : compounding_trade_state_machine.py
Project     : PulseViper XAU AI
Version     : 1.0.1
Purpose     : Stateful Shadow Bootstrap / Compounding Trade Lifecycle
===============================================================================

Status
------
SHADOW / RESEARCH / DEMO ONLY.

This module does NOT:
- connect to MT5
- send orders
- open positions
- close positions
- modify SL
- modify TP
- authorize execution
- modify production trade_ready
- modify LEI
- modify RWEI
- modify production RiskEngine

Purpose
-------
Coordinate:

    BootstrapCompoundingPlanner
    CompoundingAccountStateAdapter

into a stateful basket lifecycle.

Lifecycle
---------

    FLAT
      |
      v
    LEG_1_ACTIVE
      |
      | favorable move / add-on proof
      v
    PYRAMID_ACTIVE
      |
      | partial booking threshold
      v
    PROTECTED
      |
      | stronger continuation
      v
    RUNNER
      |
      | optional account-safe add-on
      v
    RUNNER / PYRAMID_ACTIVE
      |
      | structure invalidation
      v
    CLOSED

v1.0.1
------
Important R-reference fix.

When a basket grows:

    1 leg risk = 0.50
    2 leg risk = 1.00

the lifecycle R reference must NOT fall back to 0.50 merely because one leg is
later partially booked.

The field:

    initial_basket_risk

is retained for API compatibility, but after pyramiding it acts as a
NON-DECREASING LIFECYCLE RISK WATERMARK.

Example:

    Leg-1 risk             = 0.50
    Leg-2 added
    combined risk          = 1.00
    lifecycle watermark    = 1.00

    partial close
    current active risk    = 0.50
    lifecycle watermark    = 1.00

Therefore:

    partial at 0.85R       = +0.85
    runner at 1.50R        = +1.50

and NOT:

    partial at +0.85
    runner later at +0.75

This prevents management thresholds moving backwards after scale-out.

Design principles
-----------------
1. Structural SL remains external.

2. Adding a new leg requires:
   - basket approval
   - account-state approval
   - free margin
   - combined risk
   - basket margin
   - friction limits
   - optional profit proof

3. Partial booking has priority over a new add-on on the same evaluation step.

4. Trailing instructions are structural instructions only.

5. Paid spread is tracked cumulatively.

6. Position reductions are simulated only.

Safety
------
Every transition:

    live_authorized = False
"""

from __future__ import annotations

import importlib
import math
from dataclasses import dataclass
from typing import Any, Sequence


basket_module: Any = importlib.import_module(
    "02_AI.Shadow.bootstrap_compounding_planner"
)

adapter_module: Any = importlib.import_module(
    "02_AI.Shadow.compounding_account_state_adapter"
)


BasketLegCandidate: Any = (
    basket_module.BasketLegCandidate
)

BootstrapCompoundingPlanner: Any = (
    basket_module.BootstrapCompoundingPlanner
)

CompoundingAccountStateAdapter: Any = (
    adapter_module.CompoundingAccountStateAdapter
)


@dataclass(
    frozen=True
)
class CompoundingLegState:
    leg_id: str

    direction: str

    volume: float

    projected_stop_loss: float

    margin_required: float

    spread_cost_paid: float

    structural_stop_distance: float


@dataclass(
    frozen=True
)
class CompoundingTradeState:
    status: str

    direction: str

    sequence_step: int

    active_legs: tuple[
        CompoundingLegState,
        ...,
    ]

    active_volume: float

    projected_stop_loss: float

    basket_margin: float

    cumulative_spread_cost: float

    # API name retained.
    #
    # Semantics:
    # non-decreasing lifecycle R-risk watermark.
    initial_basket_risk: float

    first_leg_initial_risk: float

    floating_profit: float

    current_r: float

    trail_active: bool

    runner_mode: bool

    partial_booking_count: int


@dataclass(
    frozen=True
)
class CompoundingTransition:
    valid: bool

    reason: str

    action: str

    mode: str

    version: str

    live_authorized: bool

    state_before: CompoundingTradeState

    state_after: CompoundingTradeState

    account_plan: Any

    management_plan: Any

    admitted_leg_ids: tuple[
        str,
        ...,
    ]

    fully_closed_leg_ids: tuple[
        str,
        ...,
    ]

    reduced_leg_ids: tuple[
        str,
        ...,
    ]

    simulated_close_volume: float


class CompoundingTradeStateMachine:
    VERSION = "1.0.1"

    MODE = "SHADOW_STATEFUL_COMPOUNDING_LIFECYCLE_ONLY"

    STATUS_FLAT = "FLAT"

    STATUS_ACTIVE = "LEG_1_ACTIVE"

    STATUS_PYRAMID = "PYRAMID_ACTIVE"

    STATUS_PROTECTED = "PROTECTED"

    STATUS_RUNNER = "RUNNER"

    STATUS_CLOSED = "CLOSED"

    _EPSILON = 1e-9

    def __init__(
        self,
        *,
        planner: Any | None = None,
        adapter: Any | None = None,
    ) -> None:

        resolved_planner = (
            planner
            if planner is not None
            else BootstrapCompoundingPlanner()
        )

        self.planner = (
            resolved_planner
        )

        self.adapter = (
            adapter
            if adapter is not None
            else CompoundingAccountStateAdapter(
                planner=resolved_planner
            )
        )

    # =========================================================================
    # Empty state
    # =========================================================================

    def empty_state(
        self,
    ) -> CompoundingTradeState:

        return CompoundingTradeState(
            status=self.STATUS_FLAT,
            direction="NONE",
            sequence_step=0,
            active_legs=(),
            active_volume=0.0,
            projected_stop_loss=0.0,
            basket_margin=0.0,
            cumulative_spread_cost=0.0,
            initial_basket_risk=0.0,
            first_leg_initial_risk=0.0,
            floating_profit=0.0,
            current_r=0.0,
            trail_active=False,
            runner_mode=False,
            partial_booking_count=0,
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
    def _normalize_direction(
        direction: str,
    ) -> str:

        value = str(
            direction
        ).strip().upper()

        if value in {
            "BUY",
            "LONG",
            "BULLISH",
        }:

            return "LONG"

        if value in {
            "SELL",
            "SHORT",
            "BEARISH",
        }:

            return "SHORT"

        return "INVALID"

    @staticmethod
    def _candidate_ids_unique(
        candidates: Sequence[
            Any
        ],
    ) -> bool:

        ids = [
            str(
                candidate.leg_id
            )
            for candidate in candidates
        ]

        return (
            len(
                ids
            )
            ==
            len(
                set(
                    ids
                )
            )
        )

    @staticmethod
    def _candidate_to_leg(
        candidate: Any,
    ) -> CompoundingLegState:

        return CompoundingLegState(
            leg_id=str(
                candidate.leg_id
            ),
            direction=str(
                candidate.direction
            ).strip().upper(),
            volume=float(
                candidate.volume
            ),
            projected_stop_loss=float(
                candidate.projected_stop_loss
            ),
            margin_required=float(
                candidate.margin_required
            ),
            spread_cost_paid=float(
                candidate.spread_cost
            ),
            structural_stop_distance=float(
                candidate.structural_stop_distance
            ),
        )

    @staticmethod
    def _aggregates(
        legs: Sequence[
            CompoundingLegState
        ],
    ) -> tuple[
        float,
        float,
        float,
    ]:

        volume = sum(
            leg.volume
            for leg in legs
        )

        projected_loss = sum(
            leg.projected_stop_loss
            for leg in legs
        )

        margin = sum(
            leg.margin_required
            for leg in legs
        )

        return (
            volume,
            projected_loss,
            margin,
        )

    def _status(
        self,
        *,
        legs: Sequence[
            CompoundingLegState
        ],
        trail_active: bool,
        runner_mode: bool,
    ) -> str:

        if not legs:

            return self.STATUS_CLOSED

        if runner_mode:

            return self.STATUS_RUNNER

        if trail_active:

            return self.STATUS_PROTECTED

        if len(
            legs
        ) > 1:

            return self.STATUS_PYRAMID

        return self.STATUS_ACTIVE

    # =========================================================================
    # Transition helper
    # =========================================================================

    def _transition(
        self,
        *,
        valid: bool,
        reason: str,
        action: str,
        state_before: CompoundingTradeState,
        state_after: CompoundingTradeState,
        account_plan: Any = None,
        management_plan: Any = None,
        admitted_leg_ids: tuple[
            str,
            ...,
        ] = (),
        fully_closed_leg_ids: tuple[
            str,
            ...,
        ] = (),
        reduced_leg_ids: tuple[
            str,
            ...,
        ] = (),
        simulated_close_volume: float = 0.0,
    ) -> CompoundingTransition:

        return CompoundingTransition(
            valid=valid,
            reason=reason,
            action=action,
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            state_before=state_before,
            state_after=state_after,
            account_plan=account_plan,
            management_plan=management_plan,
            admitted_leg_ids=admitted_leg_ids,
            fully_closed_leg_ids=fully_closed_leg_ids,
            reduced_leg_ids=reduced_leg_ids,
            simulated_close_volume=round(
                simulated_close_volume,
                8,
            ),
        )

    # =========================================================================
    # Start basket
    # =========================================================================

    def start(
        self,
        *,
        state: CompoundingTradeState,
        account_balance: float,
        account_equity: float,
        account_free_margin: float,
        account_margin_used: float,
        candidates: Sequence[
            Any
        ],
        volume_min: float,
        volume_step: float,
    ) -> CompoundingTransition:

        if state.status != self.STATUS_FLAT:

            return self._transition(
                valid=False,
                reason="SESSION_NOT_FLAT",
                action="NO_ACTION",
                state_before=state,
                state_after=state,
            )

        candidates_tuple = tuple(
            candidates
        )

        if not candidates_tuple:

            return self._transition(
                valid=False,
                reason="NO_INITIAL_CANDIDATES",
                action="NO_ACTION",
                state_before=state,
                state_after=state,
            )

        if not self._candidate_ids_unique(
            candidates_tuple
        ):

            return self._transition(
                valid=False,
                reason="DUPLICATE_LEG_ID",
                action="NO_ACTION",
                state_before=state,
                state_after=state,
            )

        first_direction = (
            self._normalize_direction(
                candidates_tuple[
                    0
                ].direction
            )
        )

        if first_direction == "INVALID":

            return self._transition(
                valid=False,
                reason="INVALID_DIRECTION",
                action="NO_ACTION",
                state_before=state,
                state_after=state,
            )

        for candidate in candidates_tuple:

            if (
                self._normalize_direction(
                    candidate.direction
                )
                !=
                first_direction
            ):

                return self._transition(
                    valid=False,
                    reason="MIXED_INITIAL_DIRECTIONS",
                    action="NO_ACTION",
                    state_before=state,
                    state_after=state,
                )

        account_plan = (
            self.adapter.plan_addition(
                account_balance=account_balance,
                account_equity=account_equity,
                account_free_margin=account_free_margin,
                account_margin_used=account_margin_used,
                candidates=candidates_tuple,
                volume_min=volume_min,
                volume_step=volume_step,
            )
        )

        if (
            not account_plan.valid
            or
            account_plan.accepted_new_legs <= 0
        ):

            return self._transition(
                valid=False,
                reason=account_plan.reason,
                action="NO_ACTION",
                state_before=state,
                state_after=state,
                account_plan=account_plan,
            )

        accepted_ids = tuple(
            account_plan.accepted_leg_ids
        )

        accepted_set = set(
            accepted_ids
        )

        accepted_candidates = [
            candidate
            for candidate in candidates_tuple
            if candidate.leg_id
            in accepted_set
        ]

        accepted_legs = tuple(
            self._candidate_to_leg(
                candidate
            )
            for candidate in accepted_candidates
        )

        (
            active_volume,
            projected_loss,
            basket_margin,
        ) = self._aggregates(
            accepted_legs
        )

        cumulative_spread = sum(
            leg.spread_cost_paid
            for leg in accepted_legs
        )

        first_leg_initial_risk = (
            accepted_legs[
                0
            ].projected_stop_loss
        )

        status = self._status(
            legs=accepted_legs,
            trail_active=False,
            runner_mode=False,
        )

        state_after = CompoundingTradeState(
            status=status,
            direction=first_direction,
            sequence_step=1,
            active_legs=accepted_legs,
            active_volume=round(
                active_volume,
                8,
            ),
            projected_stop_loss=round(
                projected_loss,
                8,
            ),
            basket_margin=round(
                basket_margin,
                8,
            ),
            cumulative_spread_cost=round(
                cumulative_spread,
                8,
            ),

            # Initial watermark.
            initial_basket_risk=round(
                projected_loss,
                8,
            ),

            first_leg_initial_risk=round(
                first_leg_initial_risk,
                8,
            ),
            floating_profit=0.0,
            current_r=0.0,
            trail_active=False,
            runner_mode=False,
            partial_booking_count=0,
        )

        return self._transition(
            valid=True,
            reason=account_plan.reason,
            action="START_BASKET",
            state_before=state,
            state_after=state_after,
            account_plan=account_plan,
            admitted_leg_ids=accepted_ids,
        )

    # =========================================================================
    # Simulated scale-out
    # =========================================================================

    def _simulate_reduce_volume(
        self,
        *,
        legs: tuple[
            CompoundingLegState,
            ...,
        ],
        close_volume: float,
    ) -> tuple[
        tuple[
            CompoundingLegState,
            ...,
        ],
        tuple[
            str,
            ...,
        ],
        tuple[
            str,
            ...,
        ],
        float,
    ]:

        remaining_to_close = max(
            0.0,
            float(
                close_volume
            ),
        )

        resulting_legs: list[
            CompoundingLegState
        ] = []

        fully_closed: list[
            str
        ] = []

        reduced: list[
            str
        ] = []

        actual_closed = 0.0

        for leg in legs:

            if (
                remaining_to_close
                <=
                self._EPSILON
            ):

                resulting_legs.append(
                    leg
                )

                continue

            take = min(
                leg.volume,
                remaining_to_close,
            )

            if take <= self._EPSILON:

                resulting_legs.append(
                    leg
                )

                continue

            actual_closed += (
                take
            )

            remaining_to_close -= (
                take
            )

            residual_volume = (
                leg.volume
                -
                take
            )

            reduced.append(
                leg.leg_id
            )

            if (
                residual_volume
                <=
                self._EPSILON
            ):

                fully_closed.append(
                    leg.leg_id
                )

                continue

            remaining_ratio = (
                residual_volume
                /
                leg.volume
            )

            resulting_legs.append(
                CompoundingLegState(
                    leg_id=leg.leg_id,
                    direction=leg.direction,
                    volume=round(
                        residual_volume,
                        8,
                    ),
                    projected_stop_loss=round(
                        leg.projected_stop_loss
                        *
                        remaining_ratio,
                        8,
                    ),
                    margin_required=round(
                        leg.margin_required
                        *
                        remaining_ratio,
                        8,
                    ),
                    spread_cost_paid=round(
                        leg.spread_cost_paid
                        *
                        remaining_ratio,
                        8,
                    ),
                    structural_stop_distance=(
                        leg.structural_stop_distance
                    ),
                )
            )

        return (
            tuple(
                resulting_legs
            ),
            tuple(
                fully_closed
            ),
            tuple(
                reduced
            ),
            actual_closed,
        )

    # =========================================================================
    # Step
    # =========================================================================

    def step(
        self,
        *,
        state: CompoundingTradeState,
        account_balance: float,
        account_equity: float,
        account_free_margin: float,
        account_margin_used: float,
        current_floating_profit: float,
        volume_min: float,
        volume_step: float,
        add_candidates: Sequence[
            Any
        ] = (),
        structure_invalidated: bool = False,
    ) -> CompoundingTransition:

        if state.status in {
            self.STATUS_FLAT,
            self.STATUS_CLOSED,
        }:

            return self._transition(
                valid=False,
                reason="NO_ACTIVE_BASKET",
                action="NO_ACTION",
                state_before=state,
                state_after=state,
            )

        floating_profit = self._number(
            current_floating_profit
        )

        if not math.isfinite(
            floating_profit
        ):

            return self._transition(
                valid=False,
                reason="INVALID_FLOATING_PROFIT",
                action="NO_ACTION",
                state_before=state,
                state_after=state,
            )

        # =====================================================================
        # Structural invalidation
        # =====================================================================

        if structure_invalidated:

            closed_ids = tuple(
                leg.leg_id
                for leg in state.active_legs
            )

            closed_state = CompoundingTradeState(
                status=self.STATUS_CLOSED,
                direction=state.direction,
                sequence_step=(
                    state.sequence_step
                    +
                    1
                ),
                active_legs=(),
                active_volume=0.0,
                projected_stop_loss=0.0,
                basket_margin=0.0,
                cumulative_spread_cost=(
                    state.cumulative_spread_cost
                ),
                initial_basket_risk=(
                    state.initial_basket_risk
                ),
                first_leg_initial_risk=(
                    state.first_leg_initial_risk
                ),
                floating_profit=round(
                    floating_profit,
                    8,
                ),
                current_r=0.0,
                trail_active=False,
                runner_mode=False,
                partial_booking_count=(
                    state.partial_booking_count
                ),
            )

            return self._transition(
                valid=True,
                reason="STRUCTURE_INVALIDATED",
                action="EXIT_BASKET_ON_STRUCTURE_INVALIDATION",
                state_before=state,
                state_after=closed_state,
                fully_closed_leg_ids=closed_ids,
                reduced_leg_ids=closed_ids,
                simulated_close_volume=(
                    state.active_volume
                ),
            )

        # =====================================================================
        # Management R reference.
        #
        # initial_basket_risk is now a NON-DECREASING risk watermark.
        # =====================================================================

        management_risk_reference = max(
            state.initial_basket_risk,
            state.projected_stop_loss,
        )

        management_plan = (
            self.planner.management_plan(
                current_volume=state.active_volume,
                volume_min=volume_min,
                volume_step=volume_step,
                current_unrealized_profit=floating_profit,
                initial_basket_risk=management_risk_reference,
            )
        )

        if not management_plan.valid:

            return self._transition(
                valid=False,
                reason=management_plan.reason,
                action="NO_ACTION",
                state_before=state,
                state_after=state,
                management_plan=management_plan,
            )

        # =====================================================================
        # Partial booking has priority
        # =====================================================================

        if (
            management_plan.partial_booking
            and
            management_plan.close_volume > 0.0
        ):

            (
                remaining_legs,
                fully_closed_ids,
                reduced_ids,
                actual_closed_volume,
            ) = self._simulate_reduce_volume(
                legs=state.active_legs,
                close_volume=management_plan.close_volume,
            )

            (
                active_volume,
                projected_loss,
                basket_margin,
            ) = self._aggregates(
                remaining_legs
            )

            status = self._status(
                legs=remaining_legs,
                trail_active=(
                    management_plan.trail_active
                ),
                runner_mode=(
                    management_plan.runner_mode
                ),
            )

            state_after = CompoundingTradeState(
                status=status,
                direction=state.direction,
                sequence_step=(
                    state.sequence_step
                    +
                    1
                ),
                active_legs=remaining_legs,
                active_volume=round(
                    active_volume,
                    8,
                ),
                projected_stop_loss=round(
                    projected_loss,
                    8,
                ),
                basket_margin=round(
                    basket_margin,
                    8,
                ),

                # Historical paid spread remains cumulative.
                cumulative_spread_cost=(
                    state.cumulative_spread_cost
                ),

                # IMPORTANT:
                # Never shrink lifecycle R watermark after scale-out.
                initial_basket_risk=(
                    state.initial_basket_risk
                ),

                first_leg_initial_risk=(
                    state.first_leg_initial_risk
                ),
                floating_profit=round(
                    floating_profit,
                    8,
                ),
                current_r=(
                    management_plan.current_r
                ),
                trail_active=(
                    management_plan.trail_active
                ),
                runner_mode=(
                    management_plan.runner_mode
                ),
                partial_booking_count=(
                    state.partial_booking_count
                    +
                    1
                ),
            )

            return self._transition(
                valid=True,
                reason="OK_MANAGEMENT_PRIORITY",
                action=management_plan.instruction,
                state_before=state,
                state_after=state_after,
                management_plan=management_plan,
                fully_closed_leg_ids=(
                    fully_closed_ids
                ),
                reduced_leg_ids=reduced_ids,
                simulated_close_volume=(
                    actual_closed_volume
                ),
            )

        # =====================================================================
        # New candidate validation
        # =====================================================================

        candidates_tuple = tuple(
            add_candidates
        )

        if candidates_tuple:

            if not self._candidate_ids_unique(
                candidates_tuple
            ):

                return self._transition(
                    valid=False,
                    reason="DUPLICATE_CANDIDATE_LEG_ID",
                    action="NO_ACTION",
                    state_before=state,
                    state_after=state,
                    management_plan=management_plan,
                )

            active_ids = {
                leg.leg_id
                for leg in state.active_legs
            }

            if any(
                candidate.leg_id
                in active_ids
                for candidate
                in candidates_tuple
            ):

                return self._transition(
                    valid=False,
                    reason="LEG_ID_ALREADY_ACTIVE",
                    action="NO_ACTION",
                    state_before=state,
                    state_after=state,
                    management_plan=management_plan,
                )

            for candidate in candidates_tuple:

                if (
                    self._normalize_direction(
                        candidate.direction
                    )
                    !=
                    state.direction
                ):

                    return self._transition(
                        valid=False,
                        reason="ADD_DIRECTION_MISMATCH",
                        action="NO_ACTION",
                        state_before=state,
                        state_after=state,
                        management_plan=management_plan,
                    )

            account_plan = (
                self.adapter.plan_addition(
                    account_balance=account_balance,
                    account_equity=account_equity,
                    account_free_margin=account_free_margin,
                    account_margin_used=account_margin_used,
                    candidates=candidates_tuple,
                    volume_min=volume_min,
                    volume_step=volume_step,
                    existing_legs=len(
                        state.active_legs
                    ),
                    existing_direction=(
                        state.direction
                    ),
                    existing_volume=(
                        state.active_volume
                    ),
                    existing_projected_loss=(
                        state.projected_stop_loss
                    ),
                    existing_basket_margin=(
                        state.basket_margin
                    ),
                    existing_spread_cost=(
                        state.cumulative_spread_cost
                    ),
                    existing_floating_profit=(
                        floating_profit
                    ),
                    first_leg_initial_risk=(
                        state.first_leg_initial_risk
                    ),
                )
            )

            if (
                account_plan.valid
                and
                account_plan.accepted_new_legs > 0
            ):

                accepted_ids = tuple(
                    account_plan.accepted_leg_ids
                )

                accepted_set = set(
                    accepted_ids
                )

                accepted_candidates = [
                    candidate
                    for candidate in candidates_tuple
                    if candidate.leg_id
                    in accepted_set
                ]

                new_legs = tuple(
                    self._candidate_to_leg(
                        candidate
                    )
                    for candidate
                    in accepted_candidates
                )

                combined_legs = (
                    state.active_legs
                    +
                    new_legs
                )

                (
                    active_volume,
                    projected_loss,
                    basket_margin,
                ) = self._aggregates(
                    combined_legs
                )

                added_spread = sum(
                    leg.spread_cost_paid
                    for leg in new_legs
                )

                # =============================================================
                # CRITICAL FIX
                #
                # Capture maximum committed basket risk as non-decreasing
                # lifecycle R watermark.
                # =============================================================

                lifecycle_risk_watermark = max(
                    state.initial_basket_risk,
                    projected_loss,
                )

                status = self._status(
                    legs=combined_legs,
                    trail_active=(
                        management_plan.trail_active
                    ),
                    runner_mode=(
                        management_plan.runner_mode
                    ),
                )

                state_after = CompoundingTradeState(
                    status=status,
                    direction=state.direction,
                    sequence_step=(
                        state.sequence_step
                        +
                        1
                    ),
                    active_legs=combined_legs,
                    active_volume=round(
                        active_volume,
                        8,
                    ),
                    projected_stop_loss=round(
                        projected_loss,
                        8,
                    ),
                    basket_margin=round(
                        basket_margin,
                        8,
                    ),
                    cumulative_spread_cost=round(
                        state.cumulative_spread_cost
                        +
                        added_spread,
                        8,
                    ),
                    initial_basket_risk=round(
                        lifecycle_risk_watermark,
                        8,
                    ),
                    first_leg_initial_risk=(
                        state.first_leg_initial_risk
                    ),
                    floating_profit=round(
                        floating_profit,
                        8,
                    ),
                    current_r=(
                        management_plan.current_r
                    ),
                    trail_active=(
                        management_plan.trail_active
                    ),
                    runner_mode=(
                        management_plan.runner_mode
                    ),
                    partial_booking_count=(
                        state.partial_booking_count
                    ),
                )

                return self._transition(
                    valid=True,
                    reason=account_plan.reason,
                    action="ADD_COMPOUNDING_LEGS",
                    state_before=state,
                    state_after=state_after,
                    account_plan=account_plan,
                    management_plan=management_plan,
                    admitted_leg_ids=accepted_ids,
                )

            add_rejection_reason = (
                account_plan.reason
            )

        else:

            account_plan = None

            add_rejection_reason = ""

        # =====================================================================
        # No partial / no admitted add-on
        # =====================================================================

        status = self._status(
            legs=state.active_legs,
            trail_active=(
                management_plan.trail_active
            ),
            runner_mode=(
                management_plan.runner_mode
            ),
        )

        state_after = CompoundingTradeState(
            status=status,
            direction=state.direction,
            sequence_step=(
                state.sequence_step
                +
                1
            ),
            active_legs=state.active_legs,
            active_volume=state.active_volume,
            projected_stop_loss=(
                state.projected_stop_loss
            ),
            basket_margin=(
                state.basket_margin
            ),
            cumulative_spread_cost=(
                state.cumulative_spread_cost
            ),
            initial_basket_risk=(
                state.initial_basket_risk
            ),
            first_leg_initial_risk=(
                state.first_leg_initial_risk
            ),
            floating_profit=round(
                floating_profit,
                8,
            ),
            current_r=(
                management_plan.current_r
            ),
            trail_active=(
                management_plan.trail_active
            ),
            runner_mode=(
                management_plan.runner_mode
            ),
            partial_booking_count=(
                state.partial_booking_count
            ),
        )

        if candidates_tuple:

            return self._transition(
                valid=False,
                reason=add_rejection_reason,
                action=management_plan.instruction,
                state_before=state,
                state_after=state_after,
                account_plan=account_plan,
                management_plan=management_plan,
            )

        return self._transition(
            valid=True,
            reason="OK_MANAGEMENT_UPDATE",
            action=management_plan.instruction,
            state_before=state,
            state_after=state_after,
            management_plan=management_plan,
        )


compounding_trade_state_machine = (
    CompoundingTradeStateMachine()
)