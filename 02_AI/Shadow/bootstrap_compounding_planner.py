"""
===============================================================================
Module      : bootstrap_compounding_planner.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Shadow Bootstrap / Compounding Basket Risk Planner
===============================================================================

Status
------
RESEARCH / SHADOW / DEMO ONLY.

This module does NOT:
- connect to MT5
- send orders
- modify positions
- modify SL/TP
- authorize execution
- modify production trade_ready
- modify LEI
- modify RWEI
- change structural stop prices

Core philosophy
---------------
1. Market structure decides SL.

2. The planner NEVER widens a stop merely to consume more risk budget.

3. Tiny-account bootstrap mode may use an absolute basket-loss budget floor.
   Example:
       $3 account
       configured basket budget floor = $0.50

   This means:
       "up to this configured basket budget may be considered"

   It does NOT mean:
       "force every setup to lose at least $0.50"

4. Compounding is optional.

5. When compounding is OFF:
       maximum one active/planned leg.

6. When compounding is ON:
       multiple legs may exist only while the COMBINED basket remains inside:
       - basket stop-loss cap
       - margin cap
       - spread/friction cap
       - maximum leg count
       - maximum total volume

7. Additional legs can optionally require the existing basket to already be
   profitable.

8. Initial simultaneous multi-leg entry is separately configurable.

9. Partial booking:
       if total volume >= 2 * broker minimum volume,
       a broker-valid portion may be released.

   Multiple 0.01 positions can therefore be scaled out by closing one complete
   0.01 leg even when a single 0.01 position cannot be partially closed.

10. Trailing decisions are instructions only.
    This planner does NOT invent an arbitrary trailing stop price.
    Future Trade Management AI must attach trailing to causal structure.

Safety
------
Every returned plan has:

    live_authorized = False
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


# =============================================================================
# Policy
# =============================================================================


@dataclass(
    frozen=True
)
class BootstrapCompoundingPolicy:
    """
    Shadow bootstrap + basket-compounding policy.

    compounding_enabled
        Master switch.

    allow_initial_multi_leg
        When True, more than one leg may be planned at initial entry.
        When False, initial entry starts with one leg and later legs require
        add-on evaluation.

    max_simultaneous_legs
        Hard basket leg-count ceiling.

    max_total_volume
        Hard total-volume ceiling.

    ---------------------------------------------------------------------------
    MICRO / BOOTSTRAP BASKET
    ---------------------------------------------------------------------------

    bootstrap_balance_max
        At or below this risk-base, bootstrap basket budgeting may be used.

    bootstrap_loss_budget_floor_usd
        Absolute minimum AVAILABLE basket-loss cap.

        This is a cap/floor for planning capacity, NOT a mandatory loss.

    bootstrap_loss_budget_percent
        Percentage-based bootstrap basket budget.

    bootstrap_loss_budget_ceiling_usd
        Absolute ceiling for bootstrap basket risk.

    bootstrap_margin_cap_percent
        Maximum basket margin as percentage of free margin.

    ---------------------------------------------------------------------------
    STANDARD COMPOUND BASKET
    ---------------------------------------------------------------------------

    standard_basket_hard_loss_percent
        Combined stop-risk ceiling for all standard-mode legs.

    standard_margin_cap_percent
        Combined margin ceiling.

    ---------------------------------------------------------------------------
    FRICTION
    ---------------------------------------------------------------------------

    max_total_spread_to_basket_loss_ratio
        Combined spread cost cannot dominate allowed basket stop-risk.

    ---------------------------------------------------------------------------
    PYRAMID / ADD-ON
    ---------------------------------------------------------------------------

    add_only_after_profit
        Require current basket floating profit before adding another leg.

    minimum_profit_r_before_add
        Existing floating profit / first-leg initial risk.

    ---------------------------------------------------------------------------
    MANAGEMENT
    ---------------------------------------------------------------------------

    partial_booking_enabled
    partial_booking_r
    partial_booking_fraction

    trail_enabled
    trail_start_r

    runner_r

    These management thresholds create instructions only.
    """

    compounding_enabled: bool = False

    allow_initial_multi_leg: bool = False

    max_simultaneous_legs: int = 3

    max_total_volume: float = 0.03

    # -------------------------------------------------------------------------
    # Bootstrap
    # -------------------------------------------------------------------------

    bootstrap_balance_max: float = 20.0

    bootstrap_loss_budget_floor_usd: float = 0.50

    bootstrap_loss_budget_percent: float = 16.67

    bootstrap_loss_budget_ceiling_usd: float = 2.00

    bootstrap_margin_cap_percent: float = 85.0

    # -------------------------------------------------------------------------
    # Standard
    # -------------------------------------------------------------------------

    standard_basket_hard_loss_percent: float = 2.00

    standard_margin_cap_percent: float = 35.0

    # -------------------------------------------------------------------------
    # Friction
    # -------------------------------------------------------------------------

    max_total_spread_to_basket_loss_ratio: float = 1.00

    # -------------------------------------------------------------------------
    # Add-on
    # -------------------------------------------------------------------------

    add_only_after_profit: bool = True

    minimum_profit_r_before_add: float = 0.25

    # -------------------------------------------------------------------------
    # Management
    # -------------------------------------------------------------------------

    partial_booking_enabled: bool = True

    partial_booking_r: float = 0.75

    partial_booking_fraction: float = 0.50

    trail_enabled: bool = True

    trail_start_r: float = 0.50

    runner_r: float = 1.25

    def __post_init__(
        self,
    ) -> None:

        if self.max_simultaneous_legs < 1:

            raise ValueError(
                "max_simultaneous_legs must be >= 1"
            )

        if (
            not math.isfinite(
                self.max_total_volume
            )
            or
            self.max_total_volume <= 0.0
        ):

            raise ValueError(
                "max_total_volume must be > 0"
            )

        if (
            not math.isfinite(
                self.bootstrap_balance_max
            )
            or
            self.bootstrap_balance_max <= 0.0
        ):

            raise ValueError(
                "bootstrap_balance_max must be > 0"
            )

        if (
            not math.isfinite(
                self.bootstrap_loss_budget_floor_usd
            )
            or
            self.bootstrap_loss_budget_floor_usd <= 0.0
        ):

            raise ValueError(
                "bootstrap_loss_budget_floor_usd must be > 0"
            )

        if (
            not math.isfinite(
                self.bootstrap_loss_budget_percent
            )
            or
            self.bootstrap_loss_budget_percent <= 0.0
        ):

            raise ValueError(
                "bootstrap_loss_budget_percent must be > 0"
            )

        if (
            not math.isfinite(
                self.bootstrap_loss_budget_ceiling_usd
            )
            or
            self.bootstrap_loss_budget_ceiling_usd
            <
            self.bootstrap_loss_budget_floor_usd
        ):

            raise ValueError(
                "bootstrap_loss_budget_ceiling_usd must be "
                ">= bootstrap_loss_budget_floor_usd"
            )

        for (
            name,
            value,
        ) in (
            (
                "bootstrap_margin_cap_percent",
                self.bootstrap_margin_cap_percent,
            ),
            (
                "standard_basket_hard_loss_percent",
                self.standard_basket_hard_loss_percent,
            ),
            (
                "standard_margin_cap_percent",
                self.standard_margin_cap_percent,
            ),
        ):

            if (
                not math.isfinite(
                    value
                )
                or
                value <= 0.0
            ):

                raise ValueError(
                    f"{name} must be > 0"
                )

        if (
            not math.isfinite(
                self.max_total_spread_to_basket_loss_ratio
            )
            or
            self.max_total_spread_to_basket_loss_ratio <= 0.0
        ):

            raise ValueError(
                "max_total_spread_to_basket_loss_ratio must be > 0"
            )

        if (
            not math.isfinite(
                self.minimum_profit_r_before_add
            )
            or
            self.minimum_profit_r_before_add < 0.0
        ):

            raise ValueError(
                "minimum_profit_r_before_add must be >= 0"
            )

        if (
            not math.isfinite(
                self.partial_booking_r
            )
            or
            self.partial_booking_r < 0.0
        ):

            raise ValueError(
                "partial_booking_r must be >= 0"
            )

        if (
            not math.isfinite(
                self.partial_booking_fraction
            )
            or
            self.partial_booking_fraction <= 0.0
            or
            self.partial_booking_fraction >= 1.0
        ):

            raise ValueError(
                "partial_booking_fraction must be in (0, 1)"
            )

        if (
            not math.isfinite(
                self.trail_start_r
            )
            or
            self.trail_start_r < 0.0
        ):

            raise ValueError(
                "trail_start_r must be >= 0"
            )

        if (
            not math.isfinite(
                self.runner_r
            )
            or
            self.runner_r < 0.0
        ):

            raise ValueError(
                "runner_r must be >= 0"
            )


# =============================================================================
# Candidate leg
# =============================================================================


@dataclass(
    frozen=True
)
class BasketLegCandidate:
    """
    One broker-calibrated proposed basket leg.

    projected_stop_loss
        Absolute monetary loss if this leg reaches its structural SL.

    margin_required
        Broker-calculated margin for this leg.

    spread_cost
        Broker-calculated immediate spread/friction cost.

    No price geometry is changed by this planner.
    """

    leg_id: str

    direction: str

    volume: float

    projected_stop_loss: float

    margin_required: float

    spread_cost: float

    structural_stop_distance: float = 0.0


# =============================================================================
# Basket plan
# =============================================================================


@dataclass(
    frozen=True
)
class BasketPlan:
    valid: bool

    reason: str

    mode: str

    version: str

    live_authorized: bool

    basket_mode: str

    direction: str

    risk_base: float

    basket_loss_cap: float

    basket_loss_cap_percent: float

    margin_cap_amount: float

    margin_cap_percent: float

    requested_new_legs: int

    accepted_new_legs: int

    existing_legs: int

    total_legs: int

    existing_volume: float

    added_volume: float

    total_volume: float

    existing_projected_loss: float

    added_projected_loss: float

    total_projected_loss: float

    total_projected_loss_percent: float

    existing_margin: float

    added_margin: float

    total_margin: float

    total_margin_percent_of_free: float

    existing_spread_cost: float

    added_spread_cost: float

    total_spread_cost: float

    spread_to_basket_loss_cap_ratio: float

    existing_floating_profit: float

    first_leg_initial_risk: float

    existing_profit_r: float

    accepted_leg_ids: tuple[
        str,
        ...,
    ]


# =============================================================================
# Management plan
# =============================================================================


@dataclass(
    frozen=True
)
class BasketManagementPlan:
    valid: bool

    reason: str

    mode: str

    version: str

    live_authorized: bool

    current_r: float

    current_volume: float

    close_volume: float

    remaining_volume: float

    partial_booking: bool

    trail_active: bool

    runner_mode: bool

    instruction: str


# =============================================================================
# Planner
# =============================================================================


class BootstrapCompoundingPlanner:
    VERSION = "1.0"

    MODE = "SHADOW_BOOTSTRAP_COMPOUNDING_RESEARCH_ONLY"

    BOOTSTRAP_MODE = "MICRO_BOOTSTRAP_BASKET"

    STANDARD_MODE = "STANDARD_COMPOUND_BASKET"

    _EPSILON = 1e-9

    def __init__(
        self,
        policy: BootstrapCompoundingPolicy | None = None,
    ) -> None:

        self.policy = (
            policy
            if policy is not None
            else BootstrapCompoundingPolicy()
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
    def _pct(
        numerator: float,
        denominator: float,
    ) -> float:

        if (
            denominator <= 0.0
            or
            not math.isfinite(
                denominator
            )
        ):

            return 0.0

        return (
            numerator
            /
            denominator
            *
            100.0
        )

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
    def _volume_precision(
        step: float,
    ) -> int:

        text = (
            f"{step:.12f}"
            .rstrip(
                "0"
            )
            .rstrip(
                "."
            )
        )

        if "." not in text:

            return 0

        return len(
            text.split(
                "."
            )[
                1
            ]
        )

    @classmethod
    def _normalize_volume_down(
        cls,
        volume: float,
        volume_min: float,
        volume_step: float,
    ) -> float:

        if (
            volume <= 0.0
            or
            volume_min <= 0.0
            or
            volume_step <= 0.0
        ):

            return 0.0

        steps = math.floor(
            (
                volume
                /
                volume_step
            )
            +
            cls._EPSILON
        )

        normalized = (
            steps
            *
            volume_step
        )

        precision = max(
            2,
            cls._volume_precision(
                volume_step
            ),
        )

        normalized = round(
            normalized,
            precision,
        )

        if (
            normalized
            +
            cls._EPSILON
            <
            volume_min
        ):

            return 0.0

        return normalized

    # =========================================================================
    # Basket caps
    # =========================================================================

    def basket_loss_cap(
        self,
        risk_base: float,
    ) -> tuple[
        str,
        float,
        float,
    ]:

        if (
            risk_base
            <=
            self.policy.bootstrap_balance_max
            +
            self._EPSILON
        ):

            percentage_amount = (
                risk_base
                *
                self.policy.bootstrap_loss_budget_percent
                /
                100.0
            )

            cap = max(
                self.policy.bootstrap_loss_budget_floor_usd,
                percentage_amount,
            )

            cap = min(
                cap,
                self.policy.bootstrap_loss_budget_ceiling_usd,
            )

            return (
                self.BOOTSTRAP_MODE,
                cap,
                self._pct(
                    cap,
                    risk_base,
                ),
            )

        cap = (
            risk_base
            *
            self.policy.standard_basket_hard_loss_percent
            /
            100.0
        )

        return (
            self.STANDARD_MODE,
            cap,
            self.policy.standard_basket_hard_loss_percent,
        )

    # =========================================================================
    # Main basket plan
    # =========================================================================

    def plan(
        self,
        *,
        account_balance: float,
        account_equity: float,
        free_margin: float,
        candidates: Sequence[
            BasketLegCandidate
        ],
        volume_min: float,
        volume_step: float,
        existing_legs: int = 0,
        existing_direction: str = "",
        existing_volume: float = 0.0,
        existing_projected_loss: float = 0.0,
        existing_margin: float = 0.0,
        existing_spread_cost: float = 0.0,
        existing_floating_profit: float = 0.0,
        first_leg_initial_risk: float = 0.0,
    ) -> BasketPlan:

        balance = self._number(
            account_balance
        )

        equity = self._number(
            account_equity
        )

        margin_free = self._number(
            free_margin
        )

        broker_volume_min = self._number(
            volume_min
        )

        broker_volume_step = self._number(
            volume_step
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
                margin_free
            )
            or
            balance <= 0.0
            or
            equity <= 0.0
            or
            margin_free <= 0.0
        ):

            return self._invalid(
                reason="INVALID_ACCOUNT_STATE",
            )

        if (
            not math.isfinite(
                broker_volume_min
            )
            or
            not math.isfinite(
                broker_volume_step
            )
            or
            broker_volume_min <= 0.0
            or
            broker_volume_step <= 0.0
        ):

            return self._invalid(
                reason="INVALID_VOLUME_METADATA",
            )

        if existing_legs < 0:

            return self._invalid(
                reason="INVALID_EXISTING_LEG_COUNT",
            )

        risk_base = min(
            balance,
            equity,
        )

        (
            basket_mode,
            loss_cap,
            loss_cap_percent,
        ) = self.basket_loss_cap(
            risk_base
        )

        margin_cap_percent = (
            self.policy.bootstrap_margin_cap_percent
            if basket_mode
            ==
            self.BOOTSTRAP_MODE
            else
            self.policy.standard_margin_cap_percent
        )

        margin_cap_amount = (
            margin_free
            *
            margin_cap_percent
            /
            100.0
        )

        # ---------------------------------------------------------------------
        # Existing exposure validation
        # ---------------------------------------------------------------------

        current_volume = max(
            0.0,
            self._number(
                existing_volume
            ),
        )

        current_loss = max(
            0.0,
            self._number(
                existing_projected_loss
            ),
        )

        current_margin = max(
            0.0,
            self._number(
                existing_margin
            ),
        )

        current_spread = max(
            0.0,
            self._number(
                existing_spread_cost
            ),
        )

        floating_profit = self._number(
            existing_floating_profit
        )

        if not math.isfinite(
            floating_profit
        ):

            floating_profit = 0.0

        first_risk = max(
            0.0,
            self._number(
                first_leg_initial_risk
            ),
        )

        existing_profit_r = (
            (
                floating_profit
                /
                first_risk
            )
            if first_risk > 0.0
            else
            0.0
        )

        normalized_existing_direction = (
            self._normalize_direction(
                existing_direction
            )
            if existing_legs > 0
            else
            "INVALID"
        )

        # ---------------------------------------------------------------------
        # Master compounding switch
        # ---------------------------------------------------------------------

        max_new_legs = len(
            candidates
        )

        if not self.policy.compounding_enabled:

            max_new_legs = min(
                max_new_legs,
                max(
                    0,
                    1
                    -
                    existing_legs,
                ),
            )

        elif (
            existing_legs == 0
            and
            not self.policy.allow_initial_multi_leg
        ):

            max_new_legs = min(
                max_new_legs,
                1,
            )

        # ---------------------------------------------------------------------
        # Add-only-after-profit
        # ---------------------------------------------------------------------

        if (
            self.policy.compounding_enabled
            and
            existing_legs > 0
            and
            self.policy.add_only_after_profit
            and
            existing_profit_r
            <
            self.policy.minimum_profit_r_before_add
            -
            self._EPSILON
        ):

            return self._build_plan(
                valid=False,
                reason="ADD_REQUIRES_EXISTING_PROFIT",
                basket_mode=basket_mode,
                direction=(
                    normalized_existing_direction
                    if normalized_existing_direction
                    !=
                    "INVALID"
                    else
                    "UNKNOWN"
                ),
                risk_base=risk_base,
                loss_cap=loss_cap,
                loss_cap_percent=loss_cap_percent,
                margin_cap_amount=margin_cap_amount,
                margin_cap_percent=margin_cap_percent,
                requested_new_legs=len(
                    candidates
                ),
                accepted=(),
                existing_legs=existing_legs,
                existing_volume=current_volume,
                current_loss=current_loss,
                current_margin=current_margin,
                current_spread=current_spread,
                floating_profit=floating_profit,
                first_risk=first_risk,
                existing_profit_r=existing_profit_r,
                free_margin=margin_free,
            )

        accepted: list[
            BasketLegCandidate
        ] = []

        direction = (
            normalized_existing_direction
            if normalized_existing_direction
            !=
            "INVALID"
            else
            ""
        )

        # ---------------------------------------------------------------------
        # Sequential admission
        # ---------------------------------------------------------------------

        for candidate in candidates[
            :max_new_legs
        ]:

            candidate_direction = (
                self._normalize_direction(
                    candidate.direction
                )
            )

            if candidate_direction == "INVALID":

                continue

            if (
                direction
                and
                candidate_direction
                !=
                direction
            ):

                continue

            volume = self._number(
                candidate.volume
            )

            projected_loss = self._number(
                candidate.projected_stop_loss
            )

            required_margin = self._number(
                candidate.margin_required
            )

            spread_cost = self._number(
                candidate.spread_cost
            )

            if (
                not math.isfinite(
                    volume
                )
                or
                not math.isfinite(
                    projected_loss
                )
                or
                not math.isfinite(
                    required_margin
                )
                or
                not math.isfinite(
                    spread_cost
                )
                or
                volume < broker_volume_min
                or
                projected_loss <= 0.0
                or
                required_margin <= 0.0
                or
                spread_cost < 0.0
            ):

                continue

            proposed_leg_count = (
                existing_legs
                +
                len(
                    accepted
                )
                +
                1
            )

            if (
                proposed_leg_count
                >
                self.policy.max_simultaneous_legs
            ):

                break

            proposed_volume = (
                current_volume
                +
                sum(
                    item.volume
                    for item in accepted
                )
                +
                volume
            )

            if (
                proposed_volume
                >
                self.policy.max_total_volume
                +
                self._EPSILON
            ):

                break

            proposed_loss = (
                current_loss
                +
                sum(
                    item.projected_stop_loss
                    for item in accepted
                )
                +
                projected_loss
            )

            if (
                proposed_loss
                >
                loss_cap
                +
                self._EPSILON
            ):

                break

            proposed_margin = (
                current_margin
                +
                sum(
                    item.margin_required
                    for item in accepted
                )
                +
                required_margin
            )

            if (
                proposed_margin
                >
                margin_cap_amount
                +
                self._EPSILON
            ):

                break

            proposed_spread = (
                current_spread
                +
                sum(
                    item.spread_cost
                    for item in accepted
                )
                +
                spread_cost
            )

            if (
                loss_cap > 0.0
                and
                (
                    proposed_spread
                    /
                    loss_cap
                )
                >
                self.policy.max_total_spread_to_basket_loss_ratio
                +
                self._EPSILON
            ):

                break

            accepted.append(
                candidate
            )

            if not direction:

                direction = (
                    candidate_direction
                )

        # ---------------------------------------------------------------------
        # Result reason
        # ---------------------------------------------------------------------

        if not accepted:

            reason = (
                "NO_NEW_LEG_FITS_BASKET_LIMITS"
            )

            valid = False

        elif (
            len(
                accepted
            )
            <
            len(
                candidates
            )
        ):

            reason = (
                "OK_PARTIAL_LEG_ADMISSION"
            )

            valid = True

        elif (
            self.policy.compounding_enabled
        ):

            reason = (
                "OK_COMPOUNDING_BASKET"
            )

            valid = True

        else:

            reason = (
                "OK_SINGLE_LEG"
            )

            valid = True

        return self._build_plan(
            valid=valid,
            reason=reason,
            basket_mode=basket_mode,
            direction=(
                direction
                if direction
                else
                "UNKNOWN"
            ),
            risk_base=risk_base,
            loss_cap=loss_cap,
            loss_cap_percent=loss_cap_percent,
            margin_cap_amount=margin_cap_amount,
            margin_cap_percent=margin_cap_percent,
            requested_new_legs=len(
                candidates
            ),
            accepted=tuple(
                accepted
            ),
            existing_legs=existing_legs,
            existing_volume=current_volume,
            current_loss=current_loss,
            current_margin=current_margin,
            current_spread=current_spread,
            floating_profit=floating_profit,
            first_risk=first_risk,
            existing_profit_r=existing_profit_r,
            free_margin=margin_free,
        )

    # =========================================================================
    # Management
    # =========================================================================

    def management_plan(
        self,
        *,
        current_volume: float,
        volume_min: float,
        volume_step: float,
        current_unrealized_profit: float,
        initial_basket_risk: float,
    ) -> BasketManagementPlan:

        volume = self._number(
            current_volume
        )

        broker_min = self._number(
            volume_min
        )

        broker_step = self._number(
            volume_step
        )

        profit = self._number(
            current_unrealized_profit
        )

        initial_risk = self._number(
            initial_basket_risk
        )

        if (
            not math.isfinite(
                volume
            )
            or
            not math.isfinite(
                broker_min
            )
            or
            not math.isfinite(
                broker_step
            )
            or
            not math.isfinite(
                profit
            )
            or
            not math.isfinite(
                initial_risk
            )
            or
            volume <= 0.0
            or
            broker_min <= 0.0
            or
            broker_step <= 0.0
            or
            initial_risk <= 0.0
        ):

            return BasketManagementPlan(
                valid=False,
                reason="INVALID_MANAGEMENT_STATE",
                mode=self.MODE,
                version=self.VERSION,
                live_authorized=False,
                current_r=0.0,
                current_volume=0.0,
                close_volume=0.0,
                remaining_volume=0.0,
                partial_booking=False,
                trail_active=False,
                runner_mode=False,
                instruction="NO_ACTION",
            )

        current_r = (
            profit
            /
            initial_risk
        )

        trail_active = (
            self.policy.trail_enabled
            and
            current_r
            >=
            self.policy.trail_start_r
        )

        runner_mode = (
            current_r
            >=
            self.policy.runner_r
        )

        close_volume = 0.0

        partial_booking = False

        if (
            self.policy.partial_booking_enabled
            and
            current_r
            >=
            self.policy.partial_booking_r
            and
            volume
            >=
            (
                2.0
                *
                broker_min
            )
            -
            self._EPSILON
        ):

            raw_close = (
                volume
                *
                self.policy.partial_booking_fraction
            )

            close_volume = (
                self._normalize_volume_down(
                    volume=raw_close,
                    volume_min=broker_min,
                    volume_step=broker_step,
                )
            )

            if close_volume > 0.0:

                remaining = (
                    volume
                    -
                    close_volume
                )

                if (
                    remaining
                    <
                    broker_min
                    -
                    self._EPSILON
                ):

                    close_volume = (
                        volume
                        -
                        broker_min
                    )

                    close_volume = (
                        self._normalize_volume_down(
                            volume=close_volume,
                            volume_min=broker_min,
                            volume_step=broker_step,
                        )
                    )

                partial_booking = (
                    close_volume > 0.0
                )

        remaining_volume = max(
            0.0,
            volume
            -
            close_volume,
        )

        if (
            partial_booking
            and
            runner_mode
            and
            trail_active
        ):

            instruction = (
                "BOOK_PARTIAL_AND_TRAIL_RUNNER_ON_STRUCTURE"
            )

        elif (
            partial_booking
            and
            trail_active
        ):

            instruction = (
                "BOOK_PARTIAL_AND_ACTIVATE_STRUCTURE_TRAIL"
            )

        elif trail_active:

            instruction = (
                "ACTIVATE_STRUCTURE_TRAIL"
            )

        elif current_r > 0.0:

            instruction = (
                "HOLD_AND_MONITOR_GIVEBACK"
            )

        else:

            instruction = (
                "NO_PROFIT_PROTECTION_YET"
            )

        return BasketManagementPlan(
            valid=True,
            reason="OK",
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            current_r=round(
                current_r,
                8,
            ),
            current_volume=round(
                volume,
                8,
            ),
            close_volume=round(
                close_volume,
                8,
            ),
            remaining_volume=round(
                remaining_volume,
                8,
            ),
            partial_booking=partial_booking,
            trail_active=trail_active,
            runner_mode=runner_mode,
            instruction=instruction,
        )

    # =========================================================================
    # Builders
    # =========================================================================

    def _invalid(
        self,
        *,
        reason: str,
    ) -> BasketPlan:

        return BasketPlan(
            valid=False,
            reason=reason,
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            basket_mode="BLOCKED",
            direction="UNKNOWN",
            risk_base=0.0,
            basket_loss_cap=0.0,
            basket_loss_cap_percent=0.0,
            margin_cap_amount=0.0,
            margin_cap_percent=0.0,
            requested_new_legs=0,
            accepted_new_legs=0,
            existing_legs=0,
            total_legs=0,
            existing_volume=0.0,
            added_volume=0.0,
            total_volume=0.0,
            existing_projected_loss=0.0,
            added_projected_loss=0.0,
            total_projected_loss=0.0,
            total_projected_loss_percent=0.0,
            existing_margin=0.0,
            added_margin=0.0,
            total_margin=0.0,
            total_margin_percent_of_free=0.0,
            existing_spread_cost=0.0,
            added_spread_cost=0.0,
            total_spread_cost=0.0,
            spread_to_basket_loss_cap_ratio=0.0,
            existing_floating_profit=0.0,
            first_leg_initial_risk=0.0,
            existing_profit_r=0.0,
            accepted_leg_ids=(),
        )

    def _build_plan(
        self,
        *,
        valid: bool,
        reason: str,
        basket_mode: str,
        direction: str,
        risk_base: float,
        loss_cap: float,
        loss_cap_percent: float,
        margin_cap_amount: float,
        margin_cap_percent: float,
        requested_new_legs: int,
        accepted: tuple[
            BasketLegCandidate,
            ...,
        ],
        existing_legs: int,
        existing_volume: float,
        current_loss: float,
        current_margin: float,
        current_spread: float,
        floating_profit: float,
        first_risk: float,
        existing_profit_r: float,
        free_margin: float,
    ) -> BasketPlan:

        added_volume = sum(
            item.volume
            for item in accepted
        )

        added_loss = sum(
            item.projected_stop_loss
            for item in accepted
        )

        added_margin = sum(
            item.margin_required
            for item in accepted
        )

        added_spread = sum(
            item.spread_cost
            for item in accepted
        )

        total_volume = (
            existing_volume
            +
            added_volume
        )

        total_loss = (
            current_loss
            +
            added_loss
        )

        total_margin = (
            current_margin
            +
            added_margin
        )

        total_spread = (
            current_spread
            +
            added_spread
        )

        return BasketPlan(
            valid=valid,
            reason=reason,
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            basket_mode=basket_mode,
            direction=direction,
            risk_base=round(
                risk_base,
                8,
            ),
            basket_loss_cap=round(
                loss_cap,
                8,
            ),
            basket_loss_cap_percent=round(
                loss_cap_percent,
                8,
            ),
            margin_cap_amount=round(
                margin_cap_amount,
                8,
            ),
            margin_cap_percent=round(
                margin_cap_percent,
                8,
            ),
            requested_new_legs=requested_new_legs,
            accepted_new_legs=len(
                accepted
            ),
            existing_legs=existing_legs,
            total_legs=(
                existing_legs
                +
                len(
                    accepted
                )
            ),
            existing_volume=round(
                existing_volume,
                8,
            ),
            added_volume=round(
                added_volume,
                8,
            ),
            total_volume=round(
                total_volume,
                8,
            ),
            existing_projected_loss=round(
                current_loss,
                8,
            ),
            added_projected_loss=round(
                added_loss,
                8,
            ),
            total_projected_loss=round(
                total_loss,
                8,
            ),
            total_projected_loss_percent=round(
                self._pct(
                    total_loss,
                    risk_base,
                ),
                8,
            ),
            existing_margin=round(
                current_margin,
                8,
            ),
            added_margin=round(
                added_margin,
                8,
            ),
            total_margin=round(
                total_margin,
                8,
            ),
            total_margin_percent_of_free=round(
                self._pct(
                    total_margin,
                    free_margin,
                ),
                8,
            ),
            existing_spread_cost=round(
                current_spread,
                8,
            ),
            added_spread_cost=round(
                added_spread,
                8,
            ),
            total_spread_cost=round(
                total_spread,
                8,
            ),
            spread_to_basket_loss_cap_ratio=round(
                (
                    total_spread
                    /
                    loss_cap
                )
                if loss_cap > 0.0
                else
                0.0,
                8,
            ),
            existing_floating_profit=round(
                floating_profit,
                8,
            ),
            first_leg_initial_risk=round(
                first_risk,
                8,
            ),
            existing_profit_r=round(
                existing_profit_r,
                8,
            ),
            accepted_leg_ids=tuple(
                item.leg_id
                for item in accepted
            ),
        )


bootstrap_compounding_planner = (
    BootstrapCompoundingPlanner()
)