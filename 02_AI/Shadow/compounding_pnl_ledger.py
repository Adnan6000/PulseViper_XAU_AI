"""
===============================================================================
Module      : compounding_pnl_ledger.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Shadow Compounding Realized / Floating P&L Ledger
===============================================================================

Status
------
SHADOW / RESEARCH / DEMO ONLY.

This module does NOT:
- connect to MT5
- send orders
- modify positions
- modify SL/TP
- authorize execution
- modify production trade_ready
- modify production RiskEngine

Purpose
-------
Maintain consistent lifecycle P&L accounting for a compounding basket.

The ledger distinguishes:

    realized_profit
    floating_profit
    lifecycle_profit = realized_profit + floating_profit

This matters after partial booking.

Example
-------
Peak lifecycle risk:
    $1.00

Before partial:
    floating = +$0.85
    realized = $0.00
    lifecycle = +$0.85
    R = 0.85

Close half the basket:

    realized = +$0.425
    floating = +$0.425
    lifecycle = +$0.85
    R = 0.85

The profit milestone must NOT disappear merely because part of the position
was booked.

Spread
------
Opening new exposure creates an immediate spread/friction drag.

Example:

    existing lifecycle profit = +$0.175
    new 0.01 leg spread        =  $0.260

Immediately after add:

    lifecycle profit           = -$0.085

This prevents pyramiding from pretending that the new leg has zero entry
friction.

Safety
------
All calculations are observational.

live_authorized = False
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(
    frozen=True
)
class CompoundingPnLState:
    balance_start: float

    realized_profit: float

    floating_profit: float

    lifecycle_profit: float

    equity: float

    active_volume: float

    margin_used: float

    free_margin: float

    cumulative_spread_cost: float

    lifecycle_risk_watermark: float

    lifecycle_r: float

    live_authorized: bool


@dataclass(
    frozen=True
)
class CompoundingPnLTransition:
    valid: bool

    reason: str

    action: str

    mode: str

    version: str

    live_authorized: bool

    state_before: CompoundingPnLState

    state_after: CompoundingPnLState

    realized_delta: float

    spread_delta: float

    volume_delta: float

    margin_delta: float


class CompoundingPnLLedger:
    VERSION = "1.0"

    MODE = "SHADOW_COMPOUNDING_PNL_ACCOUNTING_ONLY"

    _EPSILON = 1e-9

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

    @staticmethod
    def _lifecycle_r(
        lifecycle_profit: float,
        risk_watermark: float,
    ) -> float:

        if risk_watermark <= 0.0:

            return 0.0

        return (
            lifecycle_profit
            /
            risk_watermark
        )

    # =========================================================================
    # State builder
    # =========================================================================

    def _state(
        self,
        *,
        balance_start: float,
        realized_profit: float,
        floating_profit: float,
        active_volume: float,
        margin_used: float,
        cumulative_spread_cost: float,
        lifecycle_risk_watermark: float,
    ) -> CompoundingPnLState:

        lifecycle_profit = (
            realized_profit
            +
            floating_profit
        )

        equity = (
            balance_start
            +
            lifecycle_profit
        )

        free_margin = (
            equity
            -
            margin_used
        )

        lifecycle_r = (
            self._lifecycle_r(
                lifecycle_profit,
                lifecycle_risk_watermark,
            )
        )

        return CompoundingPnLState(
            balance_start=round(
                balance_start,
                8,
            ),
            realized_profit=round(
                realized_profit,
                8,
            ),
            floating_profit=round(
                floating_profit,
                8,
            ),
            lifecycle_profit=round(
                lifecycle_profit,
                8,
            ),
            equity=round(
                equity,
                8,
            ),
            active_volume=round(
                active_volume,
                8,
            ),
            margin_used=round(
                margin_used,
                8,
            ),
            free_margin=round(
                free_margin,
                8,
            ),
            cumulative_spread_cost=round(
                cumulative_spread_cost,
                8,
            ),
            lifecycle_risk_watermark=round(
                lifecycle_risk_watermark,
                8,
            ),
            lifecycle_r=round(
                lifecycle_r,
                8,
            ),
            live_authorized=False,
        )

    # =========================================================================
    # Initial state
    # =========================================================================

    def initial_state(
        self,
        *,
        balance: float,
    ) -> CompoundingPnLState:

        resolved_balance = self._number(
            balance
        )

        if (
            not math.isfinite(
                resolved_balance
            )
            or
            resolved_balance <= 0.0
        ):

            raise ValueError(
                "balance must be finite and > 0"
            )

        return self._state(
            balance_start=resolved_balance,
            realized_profit=0.0,
            floating_profit=0.0,
            active_volume=0.0,
            margin_used=0.0,
            cumulative_spread_cost=0.0,
            lifecycle_risk_watermark=0.0,
        )

    # =========================================================================
    # Mark to market
    # =========================================================================

    def mark_to_market(
        self,
        *,
        state: CompoundingPnLState,
        floating_profit: float,
    ) -> CompoundingPnLTransition:

        resolved_floating = self._number(
            floating_profit
        )

        if not math.isfinite(
            resolved_floating
        ):

            return self._invalid(
                state=state,
                reason="INVALID_FLOATING_PROFIT",
            )

        state_after = self._state(
            balance_start=state.balance_start,
            realized_profit=state.realized_profit,
            floating_profit=resolved_floating,
            active_volume=state.active_volume,
            margin_used=state.margin_used,
            cumulative_spread_cost=(
                state.cumulative_spread_cost
            ),
            lifecycle_risk_watermark=(
                state.lifecycle_risk_watermark
            ),
        )

        return self._transition(
            state_before=state,
            state_after=state_after,
            reason="OK_MARK_TO_MARKET",
            action="MARK_TO_MARKET",
        )

    # =========================================================================
    # Open / add exposure
    # =========================================================================

    def add_exposure(
        self,
        *,
        state: CompoundingPnLState,
        added_volume: float,
        added_margin: float,
        added_spread_cost: float,
        new_projected_basket_risk: float,
    ) -> CompoundingPnLTransition:

        volume = self._number(
            added_volume
        )

        margin = self._number(
            added_margin
        )

        spread = self._number(
            added_spread_cost
        )

        projected_risk = self._number(
            new_projected_basket_risk
        )

        if (
            not math.isfinite(
                volume
            )
            or
            not math.isfinite(
                margin
            )
            or
            not math.isfinite(
                spread
            )
            or
            not math.isfinite(
                projected_risk
            )
            or
            volume <= 0.0
            or
            margin <= 0.0
            or
            spread < 0.0
            or
            projected_risk <= 0.0
        ):

            return self._invalid(
                state=state,
                reason="INVALID_EXPOSURE_ADDITION",
            )

        # New position is immediately marked through the spread.
        new_floating = (
            state.floating_profit
            -
            spread
        )

        risk_watermark = max(
            state.lifecycle_risk_watermark,
            projected_risk,
        )

        state_after = self._state(
            balance_start=state.balance_start,
            realized_profit=state.realized_profit,
            floating_profit=new_floating,
            active_volume=(
                state.active_volume
                +
                volume
            ),
            margin_used=(
                state.margin_used
                +
                margin
            ),
            cumulative_spread_cost=(
                state.cumulative_spread_cost
                +
                spread
            ),
            lifecycle_risk_watermark=(
                risk_watermark
            ),
        )

        return self._transition(
            state_before=state,
            state_after=state_after,
            reason="OK_EXPOSURE_ADDED",
            action="ADD_EXPOSURE",
            spread_delta=spread,
            volume_delta=volume,
            margin_delta=margin,
        )

    # =========================================================================
    # Partial booking
    # =========================================================================

    def partial_close(
        self,
        *,
        state: CompoundingPnLState,
        close_volume: float,
        remaining_margin: float,
    ) -> CompoundingPnLTransition:

        close = self._number(
            close_volume
        )

        margin_after = self._number(
            remaining_margin
        )

        if (
            not math.isfinite(
                close
            )
            or
            not math.isfinite(
                margin_after
            )
            or
            close <= 0.0
            or
            state.active_volume <= 0.0
            or
            close
            >
            state.active_volume
            +
            self._EPSILON
            or
            margin_after < 0.0
            or
            margin_after
            >
            state.margin_used
            +
            self._EPSILON
        ):

            return self._invalid(
                state=state,
                reason="INVALID_PARTIAL_CLOSE",
            )

        close_ratio = min(
            1.0,
            close
            /
            state.active_volume,
        )

        realized_delta = (
            state.floating_profit
            *
            close_ratio
        )

        realized_after = (
            state.realized_profit
            +
            realized_delta
        )

        floating_after = (
            state.floating_profit
            -
            realized_delta
        )

        volume_after = max(
            0.0,
            state.active_volume
            -
            close,
        )

        state_after = self._state(
            balance_start=state.balance_start,
            realized_profit=realized_after,
            floating_profit=floating_after,
            active_volume=volume_after,
            margin_used=margin_after,
            cumulative_spread_cost=(
                state.cumulative_spread_cost
            ),

            # NEVER shrink R watermark after partial booking.
            lifecycle_risk_watermark=(
                state.lifecycle_risk_watermark
            ),
        )

        return self._transition(
            state_before=state,
            state_after=state_after,
            reason="OK_PARTIAL_CLOSE",
            action="PARTIAL_BOOK",
            realized_delta=realized_delta,
            volume_delta=-close,
            margin_delta=(
                margin_after
                -
                state.margin_used
            ),
        )

    # =========================================================================
    # Close all
    # =========================================================================

    def close_all(
        self,
        *,
        state: CompoundingPnLState,
    ) -> CompoundingPnLTransition:

        if state.active_volume <= 0.0:

            return self._invalid(
                state=state,
                reason="NO_ACTIVE_EXPOSURE",
            )

        realized_delta = (
            state.floating_profit
        )

        realized_after = (
            state.realized_profit
            +
            realized_delta
        )

        state_after = self._state(
            balance_start=state.balance_start,
            realized_profit=realized_after,
            floating_profit=0.0,
            active_volume=0.0,
            margin_used=0.0,
            cumulative_spread_cost=(
                state.cumulative_spread_cost
            ),
            lifecycle_risk_watermark=(
                state.lifecycle_risk_watermark
            ),
        )

        return self._transition(
            state_before=state,
            state_after=state_after,
            reason="OK_CLOSE_ALL",
            action="CLOSE_ALL",
            realized_delta=realized_delta,
            volume_delta=-state.active_volume,
            margin_delta=-state.margin_used,
        )

    # =========================================================================
    # Builders
    # =========================================================================

    def _invalid(
        self,
        *,
        state: CompoundingPnLState,
        reason: str,
    ) -> CompoundingPnLTransition:

        return CompoundingPnLTransition(
            valid=False,
            reason=reason,
            action="NO_ACTION",
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            state_before=state,
            state_after=state,
            realized_delta=0.0,
            spread_delta=0.0,
            volume_delta=0.0,
            margin_delta=0.0,
        )

    def _transition(
        self,
        *,
        state_before: CompoundingPnLState,
        state_after: CompoundingPnLState,
        reason: str,
        action: str,
        realized_delta: float = 0.0,
        spread_delta: float = 0.0,
        volume_delta: float = 0.0,
        margin_delta: float = 0.0,
    ) -> CompoundingPnLTransition:

        return CompoundingPnLTransition(
            valid=True,
            reason=reason,
            action=action,
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            state_before=state_before,
            state_after=state_after,
            realized_delta=round(
                realized_delta,
                8,
            ),
            spread_delta=round(
                spread_delta,
                8,
            ),
            volume_delta=round(
                volume_delta,
                8,
            ),
            margin_delta=round(
                margin_delta,
                8,
            ),
        )


compounding_pnl_ledger = (
    CompoundingPnLLedger()
)