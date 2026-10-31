"""
===============================================================================
Module      : compounding_lifecycle_accounting.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Stateful Compounding + P&L Accounting Coordinator
===============================================================================

Status
------
SHADOW / RESEARCH / DEMO ONLY.

This module does NOT:
- connect to MT5
- send orders
- open positions
- close real positions
- modify SL/TP
- authorize live execution
- modify production trade_ready
- modify production RiskEngine

Purpose
-------
Synchronize:

    CompoundingTradeStateMachine
    CompoundingPnLLedger

so that the trade lifecycle and account P&L lifecycle remain consistent.

Important accounting behavior
-----------------------------
1. New exposure immediately pays spread.

2. Management decisions use:

       realized_profit + current_floating_profit

   rather than current floating P/L alone.

3. After partial booking:

       realized profit remains part of lifecycle R.

4. Account balance used for new risk admission becomes:

       starting_balance + realized_profit

5. Account equity becomes:

       starting_balance
       + realized_profit
       + floating_profit

6. Account free margin becomes:

       equity - basket_margin

7. Trade-state active volume/margin and P&L-ledger volume/margin are
   reconciled after every exposure-changing transition.

Safety
------
Every result:

    live_authorized = False
"""

from __future__ import annotations

import importlib
import math
from dataclasses import dataclass
from typing import Any, Sequence


trade_module: Any = importlib.import_module(
    "02_AI.Shadow.compounding_trade_state_machine"
)

pnl_module: Any = importlib.import_module(
    "02_AI.Shadow.compounding_pnl_ledger"
)


CompoundingTradeStateMachine: Any = (
    trade_module.CompoundingTradeStateMachine
)

CompoundingPnLLedger: Any = (
    pnl_module.CompoundingPnLLedger
)


@dataclass(
    frozen=True
)
class CompoundingLifecycleAccountingState:
    trade_state: Any

    pnl_state: Any


@dataclass(
    frozen=True
)
class CompoundingLifecycleAccountingTransition:
    valid: bool

    reason: str

    action: str

    mode: str

    version: str

    live_authorized: bool

    state_before: CompoundingLifecycleAccountingState

    state_after: CompoundingLifecycleAccountingState

    trade_transition: Any

    pnl_transition: Any


class CompoundingLifecycleAccounting:
    VERSION = "1.0"

    MODE = "SHADOW_COMPOUNDING_LIFECYCLE_ACCOUNTING_ONLY"

    _EPSILON = 1e-8

    def __init__(
        self,
        *,
        machine: Any | None = None,
        ledger: Any | None = None,
    ) -> None:

        self.machine = (
            machine
            if machine is not None
            else CompoundingTradeStateMachine()
        )

        self.ledger = (
            ledger
            if ledger is not None
            else CompoundingPnLLedger()
        )

    # =========================================================================
    # Initial state
    # =========================================================================

    def initial_state(
        self,
        *,
        balance: float,
    ) -> CompoundingLifecycleAccountingState:

        return CompoundingLifecycleAccountingState(
            trade_state=self.machine.empty_state(),
            pnl_state=self.ledger.initial_state(
                balance=balance
            ),
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
    def _accepted_candidates(
        *,
        candidates: Sequence[
            Any
        ],
        accepted_ids: Sequence[
            str
        ],
    ) -> tuple[
        Any,
        ...,
    ]:

        accepted_set = set(
            accepted_ids
        )

        return tuple(
            candidate
            for candidate in candidates
            if candidate.leg_id
            in accepted_set
        )

    @staticmethod
    def _sum_candidate_field(
        candidates: Sequence[
            Any
        ],
        field: str,
    ) -> float:

        return sum(
            float(
                getattr(
                    candidate,
                    field,
                )
            )
            for candidate in candidates
        )

    def _effective_balance(
        self,
        pnl_state: Any,
    ) -> float:

        return (
            float(
                pnl_state.balance_start
            )
            +
            float(
                pnl_state.realized_profit
            )
        )

    def _reconciled(
        self,
        *,
        trade_state: Any,
        pnl_state: Any,
    ) -> bool:

        if (
            abs(
                float(
                    trade_state.active_volume
                )
                -
                float(
                    pnl_state.active_volume
                )
            )
            >
            self._EPSILON
        ):

            return False

        if (
            abs(
                float(
                    trade_state.basket_margin
                )
                -
                float(
                    pnl_state.margin_used
                )
            )
            >
            self._EPSILON
        ):

            return False

        return True

    # =========================================================================
    # Transition builder
    # =========================================================================

    def _transition(
        self,
        *,
        valid: bool,
        reason: str,
        action: str,
        state_before: CompoundingLifecycleAccountingState,
        state_after: CompoundingLifecycleAccountingState,
        trade_transition: Any = None,
        pnl_transition: Any = None,
    ) -> CompoundingLifecycleAccountingTransition:

        return CompoundingLifecycleAccountingTransition(
            valid=valid,
            reason=reason,
            action=action,
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            state_before=state_before,
            state_after=state_after,
            trade_transition=trade_transition,
            pnl_transition=pnl_transition,
        )

    # =========================================================================
    # Start
    # =========================================================================

    def start(
        self,
        *,
        state: CompoundingLifecycleAccountingState,
        candidates: Sequence[
            Any
        ],
        volume_min: float,
        volume_step: float,
    ) -> CompoundingLifecycleAccountingTransition:

        candidates_tuple = tuple(
            candidates
        )

        pnl_before = (
            state.pnl_state
        )

        effective_balance = (
            self._effective_balance(
                pnl_before
            )
        )

        trade_transition = (
            self.machine.start(
                state=state.trade_state,
                account_balance=effective_balance,
                account_equity=pnl_before.equity,
                account_free_margin=pnl_before.free_margin,
                account_margin_used=pnl_before.margin_used,
                candidates=candidates_tuple,
                volume_min=volume_min,
                volume_step=volume_step,
            )
        )

        if not trade_transition.valid:

            return self._transition(
                valid=False,
                reason=trade_transition.reason,
                action=trade_transition.action,
                state_before=state,
                state_after=state,
                trade_transition=trade_transition,
            )

        accepted_candidates = (
            self._accepted_candidates(
                candidates=candidates_tuple,
                accepted_ids=(
                    trade_transition.admitted_leg_ids
                ),
            )
        )

        if not accepted_candidates:

            return self._transition(
                valid=False,
                reason="NO_ACCEPTED_CANDIDATE_RECONCILIATION",
                action="NO_ACTION",
                state_before=state,
                state_after=state,
                trade_transition=trade_transition,
            )

        added_volume = (
            self._sum_candidate_field(
                accepted_candidates,
                "volume",
            )
        )

        added_margin = (
            self._sum_candidate_field(
                accepted_candidates,
                "margin_required",
            )
        )

        added_spread = (
            self._sum_candidate_field(
                accepted_candidates,
                "spread_cost",
            )
        )

        pnl_transition = (
            self.ledger.add_exposure(
                state=pnl_before,
                added_volume=added_volume,
                added_margin=added_margin,
                added_spread_cost=added_spread,
                new_projected_basket_risk=(
                    trade_transition
                    .state_after
                    .initial_basket_risk
                ),
            )
        )

        if not pnl_transition.valid:

            return self._transition(
                valid=False,
                reason=pnl_transition.reason,
                action="NO_ACTION",
                state_before=state,
                state_after=state,
                trade_transition=trade_transition,
                pnl_transition=pnl_transition,
            )

        state_after = (
            CompoundingLifecycleAccountingState(
                trade_state=(
                    trade_transition.state_after
                ),
                pnl_state=(
                    pnl_transition.state_after
                ),
            )
        )

        if not self._reconciled(
            trade_state=state_after.trade_state,
            pnl_state=state_after.pnl_state,
        ):

            return self._transition(
                valid=False,
                reason="STATE_RECONCILIATION_FAILED",
                action="NO_ACTION",
                state_before=state,
                state_after=state_after,
                trade_transition=trade_transition,
                pnl_transition=pnl_transition,
            )

        return self._transition(
            valid=True,
            reason="OK_LIFECYCLE_STARTED",
            action="START_BASKET",
            state_before=state,
            state_after=state_after,
            trade_transition=trade_transition,
            pnl_transition=pnl_transition,
        )

    # =========================================================================
    # Step
    # =========================================================================

    def step(
        self,
        *,
        state: CompoundingLifecycleAccountingState,
        current_market_floating_profit: float,
        volume_min: float,
        volume_step: float,
        add_candidates: Sequence[
            Any
        ] = (),
        structure_invalidated: bool = False,
    ) -> CompoundingLifecycleAccountingTransition:

        resolved_floating = self._number(
            current_market_floating_profit
        )

        if not math.isfinite(
            resolved_floating
        ):

            return self._transition(
                valid=False,
                reason="INVALID_MARKET_FLOATING_PROFIT",
                action="NO_ACTION",
                state_before=state,
                state_after=state,
            )

        # =====================================================================
        # First update broker-style current floating P/L.
        # =====================================================================

        marked_transition = (
            self.ledger.mark_to_market(
                state=state.pnl_state,
                floating_profit=resolved_floating,
            )
        )

        if not marked_transition.valid:

            return self._transition(
                valid=False,
                reason=marked_transition.reason,
                action="NO_ACTION",
                state_before=state,
                state_after=state,
                pnl_transition=marked_transition,
            )

        marked_pnl = (
            marked_transition.state_after
        )

        effective_balance = (
            self._effective_balance(
                marked_pnl
            )
        )

        candidates_tuple = tuple(
            add_candidates
        )

        # =====================================================================
        # Management / admission uses realized + floating lifecycle P/L.
        # =====================================================================

        trade_transition = (
            self.machine.step(
                state=state.trade_state,
                account_balance=effective_balance,
                account_equity=marked_pnl.equity,
                account_free_margin=marked_pnl.free_margin,
                account_margin_used=marked_pnl.margin_used,
                current_floating_profit=(
                    marked_pnl.lifecycle_profit
                ),
                volume_min=volume_min,
                volume_step=volume_step,
                add_candidates=candidates_tuple,
                structure_invalidated=structure_invalidated,
            )
        )

        # =====================================================================
        # Determine accounting action from trade transition.
        # =====================================================================

        pnl_transition: Any = (
            marked_transition
        )

        pnl_after = (
            marked_pnl
        )

        # ---------------------------------------------------------------------
        # Full basket exit
        # ---------------------------------------------------------------------

        if (
            trade_transition.action
            ==
            "EXIT_BASKET_ON_STRUCTURE_INVALIDATION"
            and
            marked_pnl.active_volume > 0.0
        ):

            pnl_transition = (
                self.ledger.close_all(
                    state=marked_pnl
                )
            )

            if pnl_transition.valid:

                pnl_after = (
                    pnl_transition.state_after
                )

        # ---------------------------------------------------------------------
        # Partial booking
        # ---------------------------------------------------------------------

        elif (
            trade_transition.simulated_close_volume
            >
            self._EPSILON
        ):

            pnl_transition = (
                self.ledger.partial_close(
                    state=marked_pnl,
                    close_volume=(
                        trade_transition
                        .simulated_close_volume
                    ),
                    remaining_margin=(
                        trade_transition
                        .state_after
                        .basket_margin
                    ),
                )
            )

            if pnl_transition.valid:

                pnl_after = (
                    pnl_transition.state_after
                )

        # ---------------------------------------------------------------------
        # Add new compounding exposure
        # ---------------------------------------------------------------------

        elif trade_transition.admitted_leg_ids:

            accepted_candidates = (
                self._accepted_candidates(
                    candidates=candidates_tuple,
                    accepted_ids=(
                        trade_transition
                        .admitted_leg_ids
                    ),
                )
            )

            if not accepted_candidates:

                return self._transition(
                    valid=False,
                    reason="NO_ACCEPTED_ADDON_RECONCILIATION",
                    action="NO_ACTION",
                    state_before=state,
                    state_after=state,
                    trade_transition=trade_transition,
                    pnl_transition=marked_transition,
                )

            added_volume = (
                self._sum_candidate_field(
                    accepted_candidates,
                    "volume",
                )
            )

            added_margin = (
                self._sum_candidate_field(
                    accepted_candidates,
                    "margin_required",
                )
            )

            added_spread = (
                self._sum_candidate_field(
                    accepted_candidates,
                    "spread_cost",
                )
            )

            pnl_transition = (
                self.ledger.add_exposure(
                    state=marked_pnl,
                    added_volume=added_volume,
                    added_margin=added_margin,
                    added_spread_cost=added_spread,
                    new_projected_basket_risk=(
                        trade_transition
                        .state_after
                        .initial_basket_risk
                    ),
                )
            )

            if pnl_transition.valid:

                pnl_after = (
                    pnl_transition.state_after
                )

        # =====================================================================
        # Accounting operation itself must succeed.
        # =====================================================================

        if not pnl_transition.valid:

            state_after = (
                CompoundingLifecycleAccountingState(
                    trade_state=(
                        trade_transition.state_after
                    ),
                    pnl_state=marked_pnl,
                )
            )

            return self._transition(
                valid=False,
                reason=pnl_transition.reason,
                action="NO_ACTION",
                state_before=state,
                state_after=state_after,
                trade_transition=trade_transition,
                pnl_transition=pnl_transition,
            )

        state_after = (
            CompoundingLifecycleAccountingState(
                trade_state=(
                    trade_transition.state_after
                ),
                pnl_state=pnl_after,
            )
        )

        # =====================================================================
        # Exposure reconciliation.
        # =====================================================================

        if not self._reconciled(
            trade_state=state_after.trade_state,
            pnl_state=state_after.pnl_state,
        ):

            return self._transition(
                valid=False,
                reason="STATE_RECONCILIATION_FAILED",
                action="NO_ACTION",
                state_before=state,
                state_after=state_after,
                trade_transition=trade_transition,
                pnl_transition=pnl_transition,
            )

        return self._transition(
            valid=trade_transition.valid,
            reason=trade_transition.reason,
            action=trade_transition.action,
            state_before=state,
            state_after=state_after,
            trade_transition=trade_transition,
            pnl_transition=pnl_transition,
        )


compounding_lifecycle_accounting = (
    CompoundingLifecycleAccounting()
)