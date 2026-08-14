"""
===============================================================================
Module      : account_protection_guard.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Stateful Shadow Cooldown + Peak-Drawdown Protection
===============================================================================

Status
------
SHADOW / RESEARCH / DEMO ONLY.

Purpose
-------
Provide a deterministic account-protection layer above entry/admission logic.

The guard tracks:

1. Peak-equity watermark.
2. Current and maximum observed drawdown from that peak.
3. Consecutive losing basket closures.
4. Cooldown bars after a losing basket.
5. Extended cooldown after a configured losing streak.
6. A fail-closed hard lock when peak drawdown reaches the configured limit.

Design boundary
---------------
This module intentionally does NOT know about:

- MT5
- orders
- symbols
- stop loss placement
- position sizing
- setup confidence
- production trade_ready
- production RiskEngine
- compounding planner internals
- execution friction internals

It only answers:

    "Given account protection state, may NEW exposure be considered?"

Existing exposure management remains outside this guard.

Important semantics
-------------------
- Bar indices are monotonic integer research clocks.
- If a loss closes on bar N and cooldown_bars_after_loss == 5,
  new exposure is blocked on bars N..N+4 and becomes eligible on N+5.
- A winning close resets the consecutive-loss streak but never shortens an
  already-active cooldown.
- A flat close does not reset the loss streak.
- Hard drawdown lock is sticky. Equity recovery does not silently unlock it.
  Reset/re-authorization is intentionally outside v1.
- All policy defaults are provisional research defaults, not production policy.

Safety
------
Every state/result:
    live_authorized = False
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(
    frozen=True,
)
class AccountProtectionPolicy:
    """
    Provisional SHADOW policy.

    These defaults are research scaffolding only. They must be independently
    validated before any future promotion.
    """

    max_peak_drawdown_percent: float = 10.0

    cooldown_bars_after_loss: int = 5

    loss_streak_threshold: int = 3

    cooldown_bars_after_loss_streak: int = 30

    flat_pnl_epsilon: float = 1e-9

    def __post_init__(
        self,
    ) -> None:

        if (
            not math.isfinite(
                self.max_peak_drawdown_percent
            )
            or
            self.max_peak_drawdown_percent <= 0.0
            or
            self.max_peak_drawdown_percent > 100.0
        ):

            raise ValueError(
                "max_peak_drawdown_percent must be in (0, 100]"
            )

        if (
            isinstance(
                self.cooldown_bars_after_loss,
                bool,
            )
            or
            not isinstance(
                self.cooldown_bars_after_loss,
                int,
            )
            or
            self.cooldown_bars_after_loss < 0
        ):

            raise ValueError(
                "cooldown_bars_after_loss must be an integer >= 0"
            )

        if (
            isinstance(
                self.loss_streak_threshold,
                bool,
            )
            or
            not isinstance(
                self.loss_streak_threshold,
                int,
            )
            or
            self.loss_streak_threshold < 1
        ):

            raise ValueError(
                "loss_streak_threshold must be an integer >= 1"
            )

        if (
            isinstance(
                self.cooldown_bars_after_loss_streak,
                bool,
            )
            or
            not isinstance(
                self.cooldown_bars_after_loss_streak,
                int,
            )
            or
            self.cooldown_bars_after_loss_streak < 0
        ):

            raise ValueError(
                "cooldown_bars_after_loss_streak "
                "must be an integer >= 0"
            )

        if (
            self.cooldown_bars_after_loss_streak
            <
            self.cooldown_bars_after_loss
        ):

            raise ValueError(
                "cooldown_bars_after_loss_streak cannot be shorter "
                "than cooldown_bars_after_loss"
            )

        if (
            not math.isfinite(
                self.flat_pnl_epsilon
            )
            or
            self.flat_pnl_epsilon < 0.0
        ):

            raise ValueError(
                "flat_pnl_epsilon must be finite and >= 0"
            )


@dataclass(
    frozen=True,
)
class AccountProtectionState:
    starting_equity: float

    peak_equity: float

    current_equity: float

    current_drawdown_amount: float

    current_drawdown_percent: float

    max_observed_drawdown_percent: float

    consecutive_losses: int

    total_closed_baskets: int

    last_closed_pnl: float

    cooldown_until_bar: int

    last_observed_bar: int

    hard_locked: bool

    hard_lock_reason: str

    live_authorized: bool


@dataclass(
    frozen=True,
)
class AccountProtectionTransition:
    valid: bool

    reason: str

    action: str

    mode: str

    version: str

    live_authorized: bool

    state_before: AccountProtectionState

    state_after: AccountProtectionState


@dataclass(
    frozen=True,
)
class AccountProtectionAssessment:
    valid: bool

    exposure_allowed: bool

    reason: str

    mode: str

    version: str

    live_authorized: bool

    current_bar: int

    cooldown_until_bar: int

    cooldown_remaining_bars: int

    hard_locked: bool

    hard_lock_reason: str

    consecutive_losses: int

    current_drawdown_percent: float

    max_observed_drawdown_percent: float

    state_before: AccountProtectionState

    state_after: AccountProtectionState


class AccountProtectionGuard:
    """
    Stateful SHADOW cooldown and account drawdown guard.
    """

    VERSION = "1.0"

    MODE = "SHADOW_ACCOUNT_PROTECTION_RESEARCH_ONLY"

    HARD_LOCK_REASON = "PEAK_DRAWDOWN_LIMIT_REACHED"

    _EPSILON = 1e-12

    def __init__(
        self,
        policy: AccountProtectionPolicy | None = None,
    ) -> None:

        self.policy = (
            policy
            if policy is not None
            else AccountProtectionPolicy()
        )

    # =========================================================================
    # Numeric / bar helpers
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
    def _bar(
        value: int,
    ) -> int | None:

        if (
            isinstance(
                value,
                bool,
            )
            or
            not isinstance(
                value,
                int,
            )
            or
            value < 0
        ):

            return None

        return value

    # =========================================================================
    # Initial state
    # =========================================================================

    def initial_state(
        self,
        *,
        equity: float,
        current_bar: int = 0,
    ) -> AccountProtectionState:

        resolved_equity = self._number(
            equity
        )

        resolved_bar = self._bar(
            current_bar
        )

        if (
            not math.isfinite(
                resolved_equity
            )
            or
            resolved_equity <= 0.0
        ):

            raise ValueError(
                "equity must be finite and > 0"
            )

        if resolved_bar is None:

            raise ValueError(
                "current_bar must be an integer >= 0"
            )

        return AccountProtectionState(
            starting_equity=round(
                resolved_equity,
                8,
            ),
            peak_equity=round(
                resolved_equity,
                8,
            ),
            current_equity=round(
                resolved_equity,
                8,
            ),
            current_drawdown_amount=0.0,
            current_drawdown_percent=0.0,
            max_observed_drawdown_percent=0.0,
            consecutive_losses=0,
            total_closed_baskets=0,
            last_closed_pnl=0.0,
            cooldown_until_bar=resolved_bar,
            last_observed_bar=resolved_bar,
            hard_locked=False,
            hard_lock_reason="",
            live_authorized=False,
        )

    # =========================================================================
    # State update helper
    # =========================================================================

    def _observe(
        self,
        *,
        state: AccountProtectionState,
        current_equity: float,
        current_bar: int,
    ) -> tuple[
        bool,
        str,
        AccountProtectionState,
    ]:

        equity = self._number(
            current_equity
        )

        bar = self._bar(
            current_bar
        )

        if (
            not math.isfinite(
                equity
            )
            or
            equity < 0.0
        ):

            return (
                False,
                "INVALID_CURRENT_EQUITY",
                state,
            )

        if bar is None:

            return (
                False,
                "INVALID_CURRENT_BAR",
                state,
            )

        if (
            bar
            <
            state.last_observed_bar
        ):

            return (
                False,
                "NON_MONOTONIC_BAR",
                state,
            )

        peak_equity = max(
            float(
                state.peak_equity
            ),
            equity,
        )

        drawdown_amount = max(
            0.0,
            peak_equity
            -
            equity,
        )

        if (
            peak_equity
            <=
            self._EPSILON
        ):

            drawdown_percent = 0.0

        else:

            drawdown_percent = (
                drawdown_amount
                /
                peak_equity
            ) * 100.0

        max_observed_drawdown_percent = max(
            float(
                state.max_observed_drawdown_percent
            ),
            drawdown_percent,
        )

        hard_locked = bool(
            state.hard_locked
        )

        hard_lock_reason = str(
            state.hard_lock_reason
        )

        if (
            not hard_locked
            and
            drawdown_percent
            +
            self._EPSILON
            >=
            self.policy.max_peak_drawdown_percent
        ):

            hard_locked = True

            hard_lock_reason = (
                self.HARD_LOCK_REASON
            )

        state_after = AccountProtectionState(
            starting_equity=state.starting_equity,
            peak_equity=round(
                peak_equity,
                8,
            ),
            current_equity=round(
                equity,
                8,
            ),
            current_drawdown_amount=round(
                drawdown_amount,
                8,
            ),
            current_drawdown_percent=round(
                drawdown_percent,
                8,
            ),
            max_observed_drawdown_percent=round(
                max_observed_drawdown_percent,
                8,
            ),
            consecutive_losses=state.consecutive_losses,
            total_closed_baskets=state.total_closed_baskets,
            last_closed_pnl=state.last_closed_pnl,
            cooldown_until_bar=state.cooldown_until_bar,
            last_observed_bar=bar,
            hard_locked=hard_locked,
            hard_lock_reason=hard_lock_reason,
            live_authorized=False,
        )

        return (
            True,
            "OK_EQUITY_OBSERVED",
            state_after,
        )

    # =========================================================================
    # Public equity observation
    # =========================================================================

    def observe_equity(
        self,
        *,
        state: AccountProtectionState,
        current_equity: float,
        current_bar: int,
    ) -> AccountProtectionTransition:

        valid, reason, state_after = (
            self._observe(
                state=state,
                current_equity=current_equity,
                current_bar=current_bar,
            )
        )

        return AccountProtectionTransition(
            valid=valid,
            reason=reason,
            action=(
                "OBSERVE_EQUITY"
                if valid
                else "NO_ACTION"
            ),
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            state_before=state,
            state_after=state_after,
        )

    # =========================================================================
    # Basket close accounting
    # =========================================================================

    def record_basket_close(
        self,
        *,
        state: AccountProtectionState,
        realized_pnl: float,
        equity_after_close: float,
        current_bar: int,
    ) -> AccountProtectionTransition:

        pnl = self._number(
            realized_pnl
        )

        if not math.isfinite(
            pnl
        ):

            return AccountProtectionTransition(
                valid=False,
                reason="INVALID_REALIZED_PNL",
                action="NO_ACTION",
                mode=self.MODE,
                version=self.VERSION,
                live_authorized=False,
                state_before=state,
                state_after=state,
            )

        observed_valid, observed_reason, observed_state = (
            self._observe(
                state=state,
                current_equity=equity_after_close,
                current_bar=current_bar,
            )
        )

        if not observed_valid:

            return AccountProtectionTransition(
                valid=False,
                reason=observed_reason,
                action="NO_ACTION",
                mode=self.MODE,
                version=self.VERSION,
                live_authorized=False,
                state_before=state,
                state_after=state,
            )

        bar = int(
            current_bar
        )

        consecutive_losses = (
            observed_state.consecutive_losses
        )

        cooldown_until_bar = (
            observed_state.cooldown_until_bar
        )

        if (
            pnl
            <
            -
            self.policy.flat_pnl_epsilon
        ):

            consecutive_losses += 1

            cooldown_bars = (
                self.policy.cooldown_bars_after_loss
            )

            if (
                consecutive_losses
                >=
                self.policy.loss_streak_threshold
            ):

                cooldown_bars = max(
                    cooldown_bars,
                    self.policy.cooldown_bars_after_loss_streak,
                )

            cooldown_until_bar = max(
                cooldown_until_bar,
                bar
                +
                cooldown_bars,
            )

            action = "RECORD_LOSS"

        elif (
            pnl
            >
            self.policy.flat_pnl_epsilon
        ):

            consecutive_losses = 0

            action = "RECORD_WIN"

        else:

            action = "RECORD_FLAT"

        state_after = AccountProtectionState(
            starting_equity=observed_state.starting_equity,
            peak_equity=observed_state.peak_equity,
            current_equity=observed_state.current_equity,
            current_drawdown_amount=(
                observed_state.current_drawdown_amount
            ),
            current_drawdown_percent=(
                observed_state.current_drawdown_percent
            ),
            max_observed_drawdown_percent=(
                observed_state.max_observed_drawdown_percent
            ),
            consecutive_losses=consecutive_losses,
            total_closed_baskets=(
                observed_state.total_closed_baskets
                +
                1
            ),
            last_closed_pnl=round(
                pnl,
                8,
            ),
            cooldown_until_bar=cooldown_until_bar,
            last_observed_bar=observed_state.last_observed_bar,
            hard_locked=observed_state.hard_locked,
            hard_lock_reason=observed_state.hard_lock_reason,
            live_authorized=False,
        )

        return AccountProtectionTransition(
            valid=True,
            reason="OK_BASKET_CLOSE_RECORDED",
            action=action,
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            state_before=state,
            state_after=state_after,
        )

    # =========================================================================
    # New exposure assessment
    # =========================================================================

    def assess_new_exposure(
        self,
        *,
        state: AccountProtectionState,
        current_equity: float,
        current_bar: int,
    ) -> AccountProtectionAssessment:

        valid, reason, state_after = (
            self._observe(
                state=state,
                current_equity=current_equity,
                current_bar=current_bar,
            )
        )

        if not valid:

            return AccountProtectionAssessment(
                valid=False,
                exposure_allowed=False,
                reason=reason,
                mode=self.MODE,
                version=self.VERSION,
                live_authorized=False,
                current_bar=(
                    state.last_observed_bar
                ),
                cooldown_until_bar=(
                    state.cooldown_until_bar
                ),
                cooldown_remaining_bars=max(
                    0,
                    state.cooldown_until_bar
                    -
                    state.last_observed_bar,
                ),
                hard_locked=state.hard_locked,
                hard_lock_reason=(
                    state.hard_lock_reason
                ),
                consecutive_losses=(
                    state.consecutive_losses
                ),
                current_drawdown_percent=(
                    state.current_drawdown_percent
                ),
                max_observed_drawdown_percent=(
                    state.max_observed_drawdown_percent
                ),
                state_before=state,
                state_after=state,
            )

        bar = int(
            current_bar
        )

        cooldown_remaining = max(
            0,
            state_after.cooldown_until_bar
            -
            bar,
        )

        if state_after.hard_locked:

            exposure_allowed = False

            decision_reason = (
                "HARD_DRAWDOWN_LOCK"
            )

        elif cooldown_remaining > 0:

            exposure_allowed = False

            decision_reason = (
                "LOSS_COOLDOWN_ACTIVE"
            )

        else:

            exposure_allowed = True

            decision_reason = (
                "OK_ACCOUNT_PROTECTION"
            )

        return AccountProtectionAssessment(
            valid=True,
            exposure_allowed=exposure_allowed,
            reason=decision_reason,
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            current_bar=bar,
            cooldown_until_bar=(
                state_after.cooldown_until_bar
            ),
            cooldown_remaining_bars=(
                cooldown_remaining
            ),
            hard_locked=(
                state_after.hard_locked
            ),
            hard_lock_reason=(
                state_after.hard_lock_reason
            ),
            consecutive_losses=(
                state_after.consecutive_losses
            ),
            current_drawdown_percent=(
                state_after.current_drawdown_percent
            ),
            max_observed_drawdown_percent=(
                state_after.max_observed_drawdown_percent
            ),
            state_before=state,
            state_after=state_after,
        )


account_protection_guard = (
    AccountProtectionGuard()
)