"""
===============================================================================
Module      : compounding_account_state_adapter.py
Project     : PulseViper XAU AI
Version     : 1.0.1
Purpose     : Account-State-Aware Shadow Compounding Admission
===============================================================================

Status
------
SHADOW / RESEARCH / DEMO ONLY.

This adapter sits above BootstrapCompoundingPlanner.

Why it exists
-------------
The basket planner evaluates the basket itself.

When a real account already has positions open, however:

    account free margin

is NOT the same thing as:

    total basket margin capacity.

For every new compounding leg we therefore require BOTH:

1. The basket remains inside its configured basket margin/risk/friction caps.
2. The newly-added margin is actually available from CURRENT account free
   margin.

This prevents optimistic pyramiding calculations.

v1.0.1
------
Fix:
A basket-valid candidate set that failed only the CURRENT account free-margin
check was previously not retained as the best evaluated basket.

That could incorrectly return:

    BASKET_PLANNER_FAILED

instead of:

    INSUFFICIENT_CURRENT_FREE_MARGIN

The adapter now explicitly tracks whether any basket-feasible candidate set
was rejected only because of current account free margin.

Safety
------
This module does NOT:
- connect to MT5
- send orders
- modify positions
- modify SL/TP
- authorize trading

Every result:
    live_authorized = False
"""

from __future__ import annotations

import importlib
import math
from dataclasses import dataclass
from typing import Any, Sequence


planner_module: Any = importlib.import_module(
    "02_AI.Shadow.bootstrap_compounding_planner"
)

BootstrapCompoundingPlanner: Any = (
    planner_module.BootstrapCompoundingPlanner
)

BasketLegCandidate: Any = (
    planner_module.BasketLegCandidate
)


@dataclass(
    frozen=True
)
class AccountAwareCompoundingPlan:
    valid: bool

    reason: str

    mode: str

    version: str

    live_authorized: bool

    requested_new_legs: int

    accepted_new_legs: int

    account_balance: float

    account_equity: float

    free_margin_before: float

    account_margin_used_before: float

    basket_margin_before: float

    added_margin: float

    estimated_free_margin_after: float

    estimated_account_margin_after: float

    accepted_leg_ids: tuple[
        str,
        ...,
    ]

    basket_plan: Any


class CompoundingAccountStateAdapter:
    """
    Account-state admission layer for compounding baskets.
    """

    VERSION = "1.0.1"

    MODE = "SHADOW_ACCOUNT_AWARE_COMPOUNDING_ONLY"

    _EPSILON = 1e-9

    def __init__(
        self,
        planner: Any | None = None,
    ) -> None:

        self.planner = (
            planner
            if planner is not None
            else BootstrapCompoundingPlanner()
        )

    # =========================================================================
    # Numeric helpers
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

    # =========================================================================
    # Invalid result helper
    # =========================================================================

    def _invalid(
        self,
        *,
        reason: str,
        balance: float = 0.0,
        equity: float = 0.0,
        free_margin: float = 0.0,
        account_margin_used: float = 0.0,
        basket_margin: float = 0.0,
        requested: int = 0,
        basket_plan: Any = None,
    ) -> AccountAwareCompoundingPlan:

        return AccountAwareCompoundingPlan(
            valid=False,
            reason=reason,
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            requested_new_legs=requested,
            accepted_new_legs=0,
            account_balance=round(
                balance,
                8,
            ),
            account_equity=round(
                equity,
                8,
            ),
            free_margin_before=round(
                free_margin,
                8,
            ),
            account_margin_used_before=round(
                account_margin_used,
                8,
            ),
            basket_margin_before=round(
                basket_margin,
                8,
            ),
            added_margin=0.0,
            estimated_free_margin_after=round(
                free_margin,
                8,
            ),
            estimated_account_margin_after=round(
                account_margin_used,
                8,
            ),
            accepted_leg_ids=(),
            basket_plan=basket_plan,
        )

    # =========================================================================
    # Main admission
    # =========================================================================

    def plan_addition(
        self,
        *,
        account_balance: float,
        account_equity: float,
        account_free_margin: float,
        account_margin_used: float,
        candidates: Sequence[
            Any
        ],
        volume_min: float,
        volume_step: float,
        existing_legs: int = 0,
        existing_direction: str = "",
        existing_volume: float = 0.0,
        existing_projected_loss: float = 0.0,
        existing_basket_margin: float = 0.0,
        existing_spread_cost: float = 0.0,
        existing_floating_profit: float = 0.0,
        first_leg_initial_risk: float = 0.0,
    ) -> AccountAwareCompoundingPlan:

        # =====================================================================
        # Account state
        # =====================================================================

        balance = self._number(
            account_balance
        )

        equity = self._number(
            account_equity
        )

        free_margin = self._number(
            account_free_margin
        )

        margin_used = self._number(
            account_margin_used
        )

        basket_margin = self._number(
            existing_basket_margin
        )

        if (
            not math.isfinite(
                balance
            )
            or
            not math.isfinite(
                equity
            )
            or
            not math.isfinite(
                free_margin
            )
            or
            not math.isfinite(
                margin_used
            )
            or
            not math.isfinite(
                basket_margin
            )
            or
            balance <= 0.0
            or
            equity <= 0.0
            or
            free_margin < 0.0
            or
            margin_used < 0.0
            or
            basket_margin < 0.0
        ):

            return self._invalid(
                reason="INVALID_ACCOUNT_MARGIN_STATE",
                requested=len(
                    candidates
                ),
            )

        # =====================================================================
        # Existing account / basket consistency
        # =====================================================================

        if (
            basket_margin
            >
            margin_used
            +
            self._EPSILON
        ):

            return self._invalid(
                reason="BASKET_MARGIN_EXCEEDS_ACCOUNT_MARGIN",
                balance=balance,
                equity=equity,
                free_margin=free_margin,
                account_margin_used=margin_used,
                basket_margin=basket_margin,
                requested=len(
                    candidates
                ),
            )

        if existing_legs < 0:

            return self._invalid(
                reason="INVALID_EXISTING_LEG_COUNT",
                balance=balance,
                equity=equity,
                free_margin=free_margin,
                account_margin_used=margin_used,
                basket_margin=basket_margin,
                requested=len(
                    candidates
                ),
            )

        candidates_tuple = tuple(
            candidates
        )

        if not candidates_tuple:

            return self._invalid(
                reason="NO_CANDIDATE_LEGS",
                balance=balance,
                equity=equity,
                free_margin=free_margin,
                account_margin_used=margin_used,
                basket_margin=basket_margin,
            )

        # =====================================================================
        # Search state
        # =====================================================================

        best_plan: Any = None

        selected_plan: Any = None

        selected_added_margin = 0.0

        selected_accepted_ids: tuple[
            str,
            ...,
        ] = ()

        # True when the underlying basket planner says at least one leg is
        # acceptable, but CURRENT account free margin cannot fund it.
        saw_basket_feasible_but_free_margin_blocked = False

        # =====================================================================
        # Try largest candidate set first.
        #
        # Basket planner:
        #     evaluates TOTAL basket risk/margin/friction policy.
        #
        # Account adapter:
        #     separately evaluates CURRENT available free margin for NEW legs.
        #
        # We intentionally use account EQUITY as the total basket margin-policy
        # base because current free margin is checked independently below.
        # =====================================================================

        for candidate_count in range(
            len(
                candidates_tuple
            ),
            0,
            -1,
        ):

            subset = candidates_tuple[
                :candidate_count
            ]

            basket_plan = self.planner.plan(
                account_balance=balance,
                account_equity=equity,

                # Total basket margin policy base.
                free_margin=equity,

                candidates=subset,
                volume_min=volume_min,
                volume_step=volume_step,
                existing_legs=existing_legs,
                existing_direction=existing_direction,
                existing_volume=existing_volume,
                existing_projected_loss=existing_projected_loss,
                existing_margin=basket_margin,
                existing_spread_cost=existing_spread_cost,
                existing_floating_profit=existing_floating_profit,
                first_leg_initial_risk=first_leg_initial_risk,
            )

            # Always retain the latest evaluated plan.
            #
            # This is important because a VALID basket may later fail only the
            # account-free-margin check.
            best_plan = basket_plan

            # =================================================================
            # Underlying basket policy rejected candidate set.
            # =================================================================

            if (
                not basket_plan.valid
                or
                basket_plan.accepted_new_legs <= 0
            ):

                continue

            # =================================================================
            # Resolve accepted candidates from accepted IDs.
            # =================================================================

            accepted_ids = tuple(
                basket_plan.accepted_leg_ids
            )

            accepted_id_set = set(
                accepted_ids
            )

            accepted_candidates = [
                candidate
                for candidate
                in subset
                if candidate.leg_id
                in accepted_id_set
            ]

            added_margin = sum(
                float(
                    candidate.margin_required
                )
                for candidate
                in accepted_candidates
            )

            # =================================================================
            # CURRENT account free-margin admission.
            #
            # This check is intentionally separate from basket policy.
            # =================================================================

            if (
                added_margin
                <=
                free_margin
                +
                self._EPSILON
            ):

                selected_plan = (
                    basket_plan
                )

                selected_added_margin = (
                    added_margin
                )

                selected_accepted_ids = (
                    accepted_ids
                )

                break

            # Basket itself was valid.
            # Only current account free margin prevented admission.
            saw_basket_feasible_but_free_margin_blocked = (
                True
            )

        # =====================================================================
        # No planner result at all
        # =====================================================================

        if best_plan is None:

            return self._invalid(
                reason="BASKET_PLANNER_FAILED",
                balance=balance,
                equity=equity,
                free_margin=free_margin,
                account_margin_used=margin_used,
                basket_margin=basket_margin,
                requested=len(
                    candidates_tuple
                ),
            )

        # =====================================================================
        # No account-admissible candidate set
        # =====================================================================

        if selected_plan is None:

            if (
                saw_basket_feasible_but_free_margin_blocked
            ):

                reason = (
                    "INSUFFICIENT_CURRENT_FREE_MARGIN"
                )

            else:

                reason = (
                    best_plan.reason
                )

            return self._invalid(
                reason=reason,
                balance=balance,
                equity=equity,
                free_margin=free_margin,
                account_margin_used=margin_used,
                basket_margin=basket_margin,
                requested=len(
                    candidates_tuple
                ),
                basket_plan=best_plan,
            )

        # =====================================================================
        # Account state after hypothetical admission
        # =====================================================================

        estimated_free_after = max(
            0.0,
            free_margin
            -
            selected_added_margin,
        )

        estimated_account_margin_after = (
            margin_used
            +
            selected_added_margin
        )

        # =====================================================================
        # Result reason
        # =====================================================================

        if (
            len(
                selected_accepted_ids
            )
            <
            len(
                candidates_tuple
            )
        ):

            reason = (
                "OK_ACCOUNT_STATE_PARTIAL_ADMISSION"
            )

        else:

            reason = (
                "OK_ACCOUNT_STATE_ADMISSION"
            )

        # =====================================================================
        # Final shadow result
        # =====================================================================

        return AccountAwareCompoundingPlan(
            valid=True,
            reason=reason,
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            requested_new_legs=len(
                candidates_tuple
            ),
            accepted_new_legs=len(
                selected_accepted_ids
            ),
            account_balance=round(
                balance,
                8,
            ),
            account_equity=round(
                equity,
                8,
            ),
            free_margin_before=round(
                free_margin,
                8,
            ),
            account_margin_used_before=round(
                margin_used,
                8,
            ),
            basket_margin_before=round(
                basket_margin,
                8,
            ),
            added_margin=round(
                selected_added_margin,
                8,
            ),
            estimated_free_margin_after=round(
                estimated_free_after,
                8,
            ),
            estimated_account_margin_after=round(
                estimated_account_margin_after,
                8,
            ),
            accepted_leg_ids=selected_accepted_ids,
            basket_plan=selected_plan,
        )


compounding_account_state_adapter = (
    CompoundingAccountStateAdapter()
)