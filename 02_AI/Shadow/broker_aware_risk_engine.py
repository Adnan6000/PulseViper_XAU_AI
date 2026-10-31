"""
===============================================================================
Module      : broker_aware_risk_engine.py
Project     : PulseViper XAU AI
Version     : 1.1
Purpose     : Dual-Mode Shadow Broker-Aware Risk Planning
===============================================================================

Status
------
RESEARCH / SHADOW / DEMO ONLY.

This module does NOT:
- connect to MT5
- place orders
- modify positions
- modify pending orders
- modify production trade_ready
- modify LEI
- modify RWEI
- replace the existing production RiskEngine
- authorize live trading

Core philosophy
---------------
MARKET STRUCTURE DECIDES STOP LOSS.

The risk engine does NOT widen or tighten a structural stop merely to force a
trade into a monetary-risk budget.

NORMAL / STANDARD MODE
----------------------
STANDARD_COMPOUND

- use min(balance, equity) as risk base
- soft target risk
- hard maximum risk
- choose broker-valid volume
- normalize down to volume step
- verify exact monetary stop loss
- verify margin
- verify catastrophic spread cost
- balance growth naturally allows larger volume

MICRO MODE
----------
MICRO_BOOTSTRAP

Purpose:
Allow research/demo testing of very small balances where broker minimum volume
cannot fit inside normal percentage-risk rules.

Important:
MICRO_BOOTSTRAP is intentionally aggressive.
It is NOT normal capital-preservation risk management.

Rules:
- available only inside configured bootstrap balance range
- always use broker MINIMUM volume
- never increase lot in micro mode
- never alter the structural stop
- minimum lot stop-risk must remain below micro hard cap
- margin usage must remain below micro margin cap
- spread must not dominate the stop risk
- stop must not become excessively wide relative to current friction
- once STANDARD_COMPOUND becomes feasible, STANDARD wins automatically

This gives the intended transition:

small balance
    -> minimum lot bootstrap

balance grows
    -> same structural stop
    -> standard percentage risk becomes feasible

balance grows further
    -> lot size increases

The market stop is not enlarged simply because the account grew.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable


MoneyEstimator = Callable[
    [float],
    float | None,
]


# =============================================================================
# Policy
# =============================================================================


@dataclass(
    frozen=True
)
class BrokerRiskPolicy:
    """
    Provisional SHADOW research policy.

    STANDARD
    --------
    target_risk_percent:
        soft desired risk.

    hard_max_risk_percent:
        hard standard risk ceiling.

    max_margin_percent_of_free:
        maximum free-margin utilization.

    max_spread_cost_to_hard_risk_ratio:
        catastrophic spread ceiling relative to standard hard-risk budget.

    MICRO
    -----
    micro_enabled:
        allow minimum-lot bootstrap fallback.

    micro_min_balance:
        minimum risk-base required even for bootstrap research.

    micro_max_balance:
        bootstrap mode cannot continue indefinitely as account grows.

    micro_hard_max_risk_percent:
        maximum monetary stop-loss percentage in bootstrap mode.

    micro_max_margin_percent_of_free:
        maximum margin utilization for the minimum lot.

    micro_max_spread_cost_to_stop_risk_ratio:
        spread cost / structural stop risk ceiling.

        Example:
            0.26 spread cost
            0.30 stop risk
            ratio = 0.8667

    micro_max_stop_to_spread_risk_ratio:
        prevents extremely wide stops in a fast bootstrap strategy.

        Example:
            1.00 stop risk
            0.26 spread
            ratio = 3.846

        With default 4.0 this passes.

        A 2.00 stop with same spread:
            ratio = 7.69
            -> rejected in MICRO mode.

    All parameters remain research parameters until independently validated.
    """

    # -------------------------------------------------------------------------
    # Standard compound policy
    # -------------------------------------------------------------------------

    target_risk_percent: float = 0.75

    hard_max_risk_percent: float = 1.00

    max_margin_percent_of_free: float = 25.0

    max_spread_cost_to_hard_risk_ratio: float = 1.00

    # -------------------------------------------------------------------------
    # Micro bootstrap policy
    # -------------------------------------------------------------------------

    micro_enabled: bool = True

    micro_min_balance: float = 3.0

    micro_max_balance: float = 20.0

    micro_hard_max_risk_percent: float = 12.0

    micro_max_margin_percent_of_free: float = 80.0

    micro_max_spread_cost_to_stop_risk_ratio: float = 1.0

    micro_max_stop_to_spread_risk_ratio: float = 4.0

    def __post_init__(
        self,
    ) -> None:

        # =====================================================================
        # Standard
        # =====================================================================

        if (
            not math.isfinite(
                self.target_risk_percent
            )
            or
            self.target_risk_percent <= 0.0
        ):

            raise ValueError(
                "target_risk_percent must be > 0"
            )

        if (
            not math.isfinite(
                self.hard_max_risk_percent
            )
            or
            self.hard_max_risk_percent <= 0.0
        ):

            raise ValueError(
                "hard_max_risk_percent must be > 0"
            )

        if (
            self.target_risk_percent
            >
            self.hard_max_risk_percent
        ):

            raise ValueError(
                "target_risk_percent cannot exceed "
                "hard_max_risk_percent"
            )

        if (
            not math.isfinite(
                self.max_margin_percent_of_free
            )
            or
            self.max_margin_percent_of_free <= 0.0
            or
            self.max_margin_percent_of_free > 100.0
        ):

            raise ValueError(
                "max_margin_percent_of_free must be in (0, 100]"
            )

        if (
            not math.isfinite(
                self.max_spread_cost_to_hard_risk_ratio
            )
            or
            self.max_spread_cost_to_hard_risk_ratio <= 0.0
        ):

            raise ValueError(
                "max_spread_cost_to_hard_risk_ratio must be > 0"
            )

        # =====================================================================
        # Micro
        # =====================================================================

        if (
            not math.isfinite(
                self.micro_min_balance
            )
            or
            self.micro_min_balance <= 0.0
        ):

            raise ValueError(
                "micro_min_balance must be > 0"
            )

        if (
            not math.isfinite(
                self.micro_max_balance
            )
            or
            self.micro_max_balance
            <
            self.micro_min_balance
        ):

            raise ValueError(
                "micro_max_balance must be >= micro_min_balance"
            )

        if (
            not math.isfinite(
                self.micro_hard_max_risk_percent
            )
            or
            self.micro_hard_max_risk_percent <= 0.0
        ):

            raise ValueError(
                "micro_hard_max_risk_percent must be > 0"
            )

        if (
            not math.isfinite(
                self.micro_max_margin_percent_of_free
            )
            or
            self.micro_max_margin_percent_of_free <= 0.0
            or
            self.micro_max_margin_percent_of_free > 100.0
        ):

            raise ValueError(
                "micro_max_margin_percent_of_free must be in (0, 100]"
            )

        if (
            not math.isfinite(
                self.micro_max_spread_cost_to_stop_risk_ratio
            )
            or
            self.micro_max_spread_cost_to_stop_risk_ratio <= 0.0
        ):

            raise ValueError(
                "micro_max_spread_cost_to_stop_risk_ratio must be > 0"
            )

        if (
            not math.isfinite(
                self.micro_max_stop_to_spread_risk_ratio
            )
            or
            self.micro_max_stop_to_spread_risk_ratio <= 0.0
        ):

            raise ValueError(
                "micro_max_stop_to_spread_risk_ratio must be > 0"
            )


# =============================================================================
# Result
# =============================================================================


@dataclass(
    frozen=True
)
class BrokerRiskPlan:
    """
    Immutable broker-aware SHADOW risk result.
    """

    valid: bool

    reason: str

    mode: str

    version: str

    risk_mode: str

    live_authorized: bool

    direction: str

    risk_base: float

    requested_risk_percent: float

    target_risk_percent: float

    hard_max_risk_percent: float

    target_risk_amount: float

    hard_max_risk_amount: float

    balance: float

    equity: float

    free_margin: float

    bid: float

    ask: float

    spread_price: float

    spread_points: float

    entry_price: float

    stop_loss: float

    stop_distance_price: float

    stop_distance_points: float

    operational_min_stop_price: float

    operational_min_stop_points: float

    volume_min: float

    volume_max: float

    volume_step: float

    selected_volume: float

    minimum_volume_loss: float

    estimated_stop_loss_amount: float

    actual_risk_percent: float

    risk_target_utilization_percent: float

    margin_required: float

    margin_percent_of_free: float

    spread_cost: float

    spread_cost_to_hard_risk_ratio: float

    spread_cost_to_stop_risk_ratio: float

    stop_risk_to_spread_cost_ratio: float


# =============================================================================
# Engine
# =============================================================================


class BrokerAwareRiskEngine:
    """
    Broker-aware shadow risk planner.

    Broker monetary calculations are injected through callbacks.

    This keeps MT5 outside the engine and makes the engine deterministic and
    offline-testable.
    """

    VERSION = "1.1"

    MODE = "SHADOW_BROKER_AWARE_RISK_RESEARCH_ONLY"

    STANDARD_MODE = "STANDARD_COMPOUND"

    MICRO_MODE = "MICRO_BOOTSTRAP"

    BLOCKED_MODE = "BLOCKED"

    _EPSILON = 1e-9

    def __init__(
        self,
        policy: BrokerRiskPolicy | None = None,
    ) -> None:

        self.policy = (
            policy
            if policy is not None
            else BrokerRiskPolicy()
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

    @staticmethod
    def _money(
        value: float,
    ) -> float:

        return round(
            float(
                value
            ),
            8,
        )

    @staticmethod
    def _percentage(
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

        return round(
            (
                numerator
                /
                denominator
            )
            *
            100.0,
            8,
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

    # =========================================================================
    # Volume helpers
    # =========================================================================

    @staticmethod
    def _volume_precision(
        volume_step: float,
    ) -> int:

        text = (
            f"{volume_step:.12f}"
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
        *,
        volume: float,
        volume_min: float,
        volume_max: float,
        volume_step: float,
    ) -> float:

        if (
            volume <= 0.0
            or
            volume_min <= 0.0
            or
            volume_max < volume_min
            or
            volume_step <= 0.0
        ):

            return 0.0

        bounded = min(
            volume,
            volume_max,
        )

        if bounded < volume_min:

            return 0.0

        steps = math.floor(
            (
                bounded
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

        return min(
            normalized,
            volume_max,
        )

    @classmethod
    def _previous_volume(
        cls,
        *,
        volume: float,
        volume_min: float,
        volume_step: float,
    ) -> float:

        previous = (
            volume
            -
            volume_step
        )

        if (
            previous
            +
            cls._EPSILON
            <
            volume_min
        ):

            return 0.0

        precision = max(
            2,
            cls._volume_precision(
                volume_step
            ),
        )

        return round(
            previous,
            precision,
        )

    # =========================================================================
    # Estimator
    # =========================================================================

    @classmethod
    def _estimate_positive(
        cls,
        estimator: MoneyEstimator,
        volume: float,
    ) -> float | None:

        try:

            result = estimator(
                volume
            )

        except Exception:

            return None

        if result is None:

            return None

        value = cls._number(
            result
        )

        if not math.isfinite(
            value
        ):

            return None

        value = abs(
            value
        )

        if value <= 0.0:

            return None

        return value

    # =========================================================================
    # Result helper
    # =========================================================================

    def _result(
        self,
        *,
        valid: bool,
        reason: str,
        risk_mode: str = BLOCKED_MODE,
        direction: str = "INVALID",
        risk_base: float = 0.0,
        requested_risk_percent: float = 0.0,
        target_risk_percent: float = 0.0,
        hard_max_risk_percent: float = 0.0,
        target_risk_amount: float = 0.0,
        hard_max_risk_amount: float = 0.0,
        balance: float = 0.0,
        equity: float = 0.0,
        free_margin: float = 0.0,
        bid: float = 0.0,
        ask: float = 0.0,
        spread_price: float = 0.0,
        spread_points: float = 0.0,
        entry_price: float = 0.0,
        stop_loss: float = 0.0,
        stop_distance_price: float = 0.0,
        stop_distance_points: float = 0.0,
        operational_min_stop_price: float = 0.0,
        operational_min_stop_points: float = 0.0,
        volume_min: float = 0.0,
        volume_max: float = 0.0,
        volume_step: float = 0.0,
        selected_volume: float = 0.0,
        minimum_volume_loss: float = 0.0,
        estimated_stop_loss_amount: float = 0.0,
        actual_risk_percent: float = 0.0,
        risk_target_utilization_percent: float = 0.0,
        margin_required: float = 0.0,
        margin_percent_of_free: float = 0.0,
        spread_cost: float = 0.0,
        spread_cost_to_hard_risk_ratio: float = 0.0,
        spread_cost_to_stop_risk_ratio: float = 0.0,
        stop_risk_to_spread_cost_ratio: float = 0.0,
    ) -> BrokerRiskPlan:

        return BrokerRiskPlan(
            valid=valid,
            reason=reason,
            mode=self.MODE,
            version=self.VERSION,
            risk_mode=risk_mode,
            live_authorized=False,
            direction=direction,
            risk_base=self._money(
                risk_base
            ),
            requested_risk_percent=round(
                requested_risk_percent,
                8,
            ),
            target_risk_percent=round(
                target_risk_percent,
                8,
            ),
            hard_max_risk_percent=round(
                hard_max_risk_percent,
                8,
            ),
            target_risk_amount=self._money(
                target_risk_amount
            ),
            hard_max_risk_amount=self._money(
                hard_max_risk_amount
            ),
            balance=self._money(
                balance
            ),
            equity=self._money(
                equity
            ),
            free_margin=self._money(
                free_margin
            ),
            bid=self._money(
                bid
            ),
            ask=self._money(
                ask
            ),
            spread_price=self._money(
                spread_price
            ),
            spread_points=round(
                spread_points,
                8,
            ),
            entry_price=self._money(
                entry_price
            ),
            stop_loss=self._money(
                stop_loss
            ),
            stop_distance_price=self._money(
                stop_distance_price
            ),
            stop_distance_points=round(
                stop_distance_points,
                8,
            ),
            operational_min_stop_price=self._money(
                operational_min_stop_price
            ),
            operational_min_stop_points=round(
                operational_min_stop_points,
                8,
            ),
            volume_min=round(
                volume_min,
                8,
            ),
            volume_max=round(
                volume_max,
                8,
            ),
            volume_step=round(
                volume_step,
                8,
            ),
            selected_volume=round(
                selected_volume,
                8,
            ),
            minimum_volume_loss=self._money(
                minimum_volume_loss
            ),
            estimated_stop_loss_amount=self._money(
                estimated_stop_loss_amount
            ),
            actual_risk_percent=round(
                actual_risk_percent,
                8,
            ),
            risk_target_utilization_percent=round(
                risk_target_utilization_percent,
                8,
            ),
            margin_required=self._money(
                margin_required
            ),
            margin_percent_of_free=round(
                margin_percent_of_free,
                8,
            ),
            spread_cost=self._money(
                spread_cost
            ),
            spread_cost_to_hard_risk_ratio=round(
                spread_cost_to_hard_risk_ratio,
                8,
            ),
            spread_cost_to_stop_risk_ratio=round(
                spread_cost_to_stop_risk_ratio,
                8,
            ),
            stop_risk_to_spread_cost_ratio=round(
                stop_risk_to_spread_cost_ratio,
                8,
            ),
        )

    # =========================================================================
    # Public plan
    # =========================================================================

    def plan(
        self,
        *,
        direction: str,
        account_balance: float,
        account_equity: float,
        free_margin: float,
        bid: float,
        ask: float,
        stop_loss: float,
        point: float,
        tick_size: float,
        volume_min: float,
        volume_max: float,
        volume_step: float,
        stops_level_points: float,
        loss_estimator: MoneyEstimator,
        margin_estimator: MoneyEstimator,
        spread_cost_estimator: MoneyEstimator | None = None,
        requested_risk_percent: float | None = None,
    ) -> BrokerRiskPlan:
        """
        Build broker-aware SHADOW risk plan.

        Priority
        --------
        1. Validate market / stop / broker metadata.
        2. Measure exact minimum-volume loss.
        3. Try STANDARD_COMPOUND.
        4. If standard cannot support broker minimum volume:
               optionally try MICRO_BOOTSTRAP.
        5. Never change stop_loss.
        """

        # =====================================================================
        # Direction
        # =====================================================================

        normalized_direction = (
            self._normalize_direction(
                direction
            )
        )

        if normalized_direction == "INVALID":

            return self._result(
                valid=False,
                reason="INVALID_DIRECTION",
            )

        # =====================================================================
        # Account
        # =====================================================================

        balance = self._number(
            account_balance
        )

        equity = self._number(
            account_equity
        )

        margin_free = self._number(
            free_margin
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

            return self._result(
                valid=False,
                reason="INVALID_ACCOUNT_STATE",
                direction=normalized_direction,
            )

        risk_base = min(
            balance,
            equity,
        )

        # =====================================================================
        # Standard monetary budget
        # =====================================================================

        requested = (
            self.policy.target_risk_percent
            if requested_risk_percent is None
            else self._number(
                requested_risk_percent
            )
        )

        if (
            not math.isfinite(
                requested
            )
            or
            requested <= 0.0
        ):

            return self._result(
                valid=False,
                reason="INVALID_REQUESTED_RISK",
                direction=normalized_direction,
                risk_base=risk_base,
                balance=balance,
                equity=equity,
                free_margin=margin_free,
            )

        standard_target_percent = min(
            requested,
            self.policy.hard_max_risk_percent,
        )

        standard_hard_percent = (
            self.policy.hard_max_risk_percent
        )

        standard_target_amount = (
            risk_base
            *
            standard_target_percent
            /
            100.0
        )

        standard_hard_amount = (
            risk_base
            *
            standard_hard_percent
            /
            100.0
        )

        # =====================================================================
        # Market
        # =====================================================================

        market_bid = self._number(
            bid
        )

        market_ask = self._number(
            ask
        )

        stop = self._number(
            stop_loss
        )

        point_value = self._number(
            point
        )

        tick_value = self._number(
            tick_size
        )

        if (
            not math.isfinite(
                market_bid
            )
            or
            not math.isfinite(
                market_ask
            )
            or
            not math.isfinite(
                stop
            )
            or
            not math.isfinite(
                point_value
            )
            or
            not math.isfinite(
                tick_value
            )
            or
            market_bid <= 0.0
            or
            market_ask <= 0.0
            or
            market_ask < market_bid
            or
            stop <= 0.0
            or
            point_value <= 0.0
            or
            tick_value <= 0.0
        ):

            return self._result(
                valid=False,
                reason="INVALID_MARKET_STATE",
                direction=normalized_direction,
                risk_base=risk_base,
                requested_risk_percent=requested,
                target_risk_percent=standard_target_percent,
                hard_max_risk_percent=standard_hard_percent,
                target_risk_amount=standard_target_amount,
                hard_max_risk_amount=standard_hard_amount,
                balance=balance,
                equity=equity,
                free_margin=margin_free,
            )

        spread_price = (
            market_ask
            -
            market_bid
        )

        spread_points = (
            spread_price
            /
            point_value
        )

        # =====================================================================
        # Stop geometry
        # =====================================================================

        stops_points = self._number(
            stops_level_points
        )

        if (
            not math.isfinite(
                stops_points
            )
            or
            stops_points < 0.0
        ):

            return self._result(
                valid=False,
                reason="INVALID_STOPS_LEVEL",
                direction=normalized_direction,
                risk_base=risk_base,
                balance=balance,
                equity=equity,
                free_margin=margin_free,
            )

        broker_stop_buffer = max(
            stops_points
            *
            point_value,
            tick_value,
        )

        operational_min_stop_price = (
            spread_price
            +
            broker_stop_buffer
        )

        operational_min_stop_points = (
            operational_min_stop_price
            /
            point_value
        )

        if normalized_direction == "LONG":

            entry = market_ask

            maximum_valid_stop = (
                market_bid
                -
                broker_stop_buffer
            )

            if (
                stop
                >
                maximum_valid_stop
                +
                self._EPSILON
            ):

                return self._result(
                    valid=False,
                    reason="STOP_NOT_BEYOND_CURRENT_BID",
                    direction=normalized_direction,
                    risk_base=risk_base,
                    requested_risk_percent=requested,
                    target_risk_percent=standard_target_percent,
                    hard_max_risk_percent=standard_hard_percent,
                    target_risk_amount=standard_target_amount,
                    hard_max_risk_amount=standard_hard_amount,
                    balance=balance,
                    equity=equity,
                    free_margin=margin_free,
                    bid=market_bid,
                    ask=market_ask,
                    spread_price=spread_price,
                    spread_points=spread_points,
                    entry_price=entry,
                    stop_loss=stop,
                    stop_distance_price=abs(
                        entry
                        -
                        stop
                    ),
                    stop_distance_points=abs(
                        entry
                        -
                        stop
                    )
                    /
                    point_value,
                    operational_min_stop_price=operational_min_stop_price,
                    operational_min_stop_points=operational_min_stop_points,
                )

        else:

            entry = market_bid

            minimum_valid_stop = (
                market_ask
                +
                broker_stop_buffer
            )

            if (
                stop
                <
                minimum_valid_stop
                -
                self._EPSILON
            ):

                return self._result(
                    valid=False,
                    reason="STOP_NOT_BEYOND_CURRENT_ASK",
                    direction=normalized_direction,
                    risk_base=risk_base,
                    requested_risk_percent=requested,
                    target_risk_percent=standard_target_percent,
                    hard_max_risk_percent=standard_hard_percent,
                    target_risk_amount=standard_target_amount,
                    hard_max_risk_amount=standard_hard_amount,
                    balance=balance,
                    equity=equity,
                    free_margin=margin_free,
                    bid=market_bid,
                    ask=market_ask,
                    spread_price=spread_price,
                    spread_points=spread_points,
                    entry_price=entry,
                    stop_loss=stop,
                    stop_distance_price=abs(
                        entry
                        -
                        stop
                    ),
                    stop_distance_points=abs(
                        entry
                        -
                        stop
                    )
                    /
                    point_value,
                    operational_min_stop_price=operational_min_stop_price,
                    operational_min_stop_points=operational_min_stop_points,
                )

        stop_distance_price = abs(
            entry
            -
            stop
        )

        stop_distance_points = (
            stop_distance_price
            /
            point_value
        )

        # =====================================================================
        # Broker volume metadata
        # =====================================================================

        broker_volume_min = self._number(
            volume_min
        )

        broker_volume_max = self._number(
            volume_max
        )

        broker_volume_step = self._number(
            volume_step
        )

        if (
            not math.isfinite(
                broker_volume_min
            )
            or
            not math.isfinite(
                broker_volume_max
            )
            or
            not math.isfinite(
                broker_volume_step
            )
            or
            broker_volume_min <= 0.0
            or
            broker_volume_max < broker_volume_min
            or
            broker_volume_step <= 0.0
        ):

            return self._result(
                valid=False,
                reason="INVALID_VOLUME_CONSTRAINTS",
                direction=normalized_direction,
                risk_base=risk_base,
                requested_risk_percent=requested,
                target_risk_percent=standard_target_percent,
                hard_max_risk_percent=standard_hard_percent,
                target_risk_amount=standard_target_amount,
                hard_max_risk_amount=standard_hard_amount,
                balance=balance,
                equity=equity,
                free_margin=margin_free,
                bid=market_bid,
                ask=market_ask,
                spread_price=spread_price,
                spread_points=spread_points,
                entry_price=entry,
                stop_loss=stop,
                stop_distance_price=stop_distance_price,
                stop_distance_points=stop_distance_points,
                operational_min_stop_price=operational_min_stop_price,
                operational_min_stop_points=operational_min_stop_points,
            )

        # =====================================================================
        # Exact broker minimum-volume estimates
        # =====================================================================

        min_loss = self._estimate_positive(
            loss_estimator,
            broker_volume_min,
        )

        if min_loss is None:

            return self._result(
                valid=False,
                reason="LOSS_ESTIMATOR_FAILED",
                direction=normalized_direction,
                risk_base=risk_base,
                balance=balance,
                equity=equity,
                free_margin=margin_free,
                bid=market_bid,
                ask=market_ask,
                spread_price=spread_price,
                spread_points=spread_points,
                entry_price=entry,
                stop_loss=stop,
                stop_distance_price=stop_distance_price,
                stop_distance_points=stop_distance_points,
                operational_min_stop_price=operational_min_stop_price,
                operational_min_stop_points=operational_min_stop_points,
                volume_min=broker_volume_min,
                volume_max=broker_volume_max,
                volume_step=broker_volume_step,
            )

        min_margin = self._estimate_positive(
            margin_estimator,
            broker_volume_min,
        )

        if min_margin is None:

            return self._result(
                valid=False,
                reason="MARGIN_ESTIMATOR_FAILED",
                direction=normalized_direction,
                risk_base=risk_base,
                balance=balance,
                equity=equity,
                free_margin=margin_free,
                bid=market_bid,
                ask=market_ask,
                spread_price=spread_price,
                spread_points=spread_points,
                entry_price=entry,
                stop_loss=stop,
                stop_distance_price=stop_distance_price,
                stop_distance_points=stop_distance_points,
                operational_min_stop_price=operational_min_stop_price,
                operational_min_stop_points=operational_min_stop_points,
                volume_min=broker_volume_min,
                volume_max=broker_volume_max,
                volume_step=broker_volume_step,
                minimum_volume_loss=min_loss,
            )

        min_spread_cost = 0.0

        if spread_cost_estimator is not None:

            spread_result = self._estimate_positive(
                spread_cost_estimator,
                broker_volume_min,
            )

            if spread_result is None:

                return self._result(
                    valid=False,
                    reason="SPREAD_ESTIMATOR_FAILED",
                    direction=normalized_direction,
                    risk_base=risk_base,
                    balance=balance,
                    equity=equity,
                    free_margin=margin_free,
                    bid=market_bid,
                    ask=market_ask,
                    spread_price=spread_price,
                    spread_points=spread_points,
                    entry_price=entry,
                    stop_loss=stop,
                    stop_distance_price=stop_distance_price,
                    stop_distance_points=stop_distance_points,
                    operational_min_stop_price=operational_min_stop_price,
                    operational_min_stop_points=operational_min_stop_points,
                    volume_min=broker_volume_min,
                    volume_max=broker_volume_max,
                    volume_step=broker_volume_step,
                    minimum_volume_loss=min_loss,
                    margin_required=min_margin,
                )

            min_spread_cost = (
                spread_result
            )

        min_actual_risk_percent = (
            self._percentage(
                min_loss,
                risk_base,
            )
        )

        min_margin_percent = (
            self._percentage(
                min_margin,
                margin_free,
            )
        )

        spread_to_stop = (
            (
                min_spread_cost
                /
                min_loss
            )
            if (
                min_spread_cost > 0.0
                and
                min_loss > 0.0
            )
            else
            0.0
        )

        stop_to_spread = (
            (
                min_loss
                /
                min_spread_cost
            )
            if min_spread_cost > 0.0
            else
            0.0
        )

        # =====================================================================
        # STANDARD feasibility
        # =====================================================================

        standard_margin_cap = (
            margin_free
            *
            self.policy.max_margin_percent_of_free
            /
            100.0
        )

        standard_spread_cap = (
            standard_hard_amount
            *
            self.policy.max_spread_cost_to_hard_risk_ratio
        )

        standard_min_loss_ok = (
            min_loss
            <=
            standard_hard_amount
            +
            self._EPSILON
        )

        standard_min_margin_ok = (
            min_margin
            <=
            standard_margin_cap
            +
            self._EPSILON
        )

        standard_min_spread_ok = (
            spread_cost_estimator is None
            or
            min_spread_cost
            <=
            standard_spread_cap
            +
            self._EPSILON
        )

        standard_possible = (
            standard_min_loss_ok
            and
            standard_min_margin_ok
            and
            standard_min_spread_ok
        )

        # =====================================================================
        # STANDARD_COMPOUND
        # =====================================================================

        if standard_possible:

            raw_risk_volume = (
                standard_target_amount
                /
                min_loss
                *
                broker_volume_min
            )

            # The soft target may fall slightly below broker minimum while the
            # hard standard ceiling still permits minimum volume.
            if raw_risk_volume < broker_volume_min:

                raw_risk_volume = (
                    broker_volume_min
                )

            raw_margin_volume = (
                standard_margin_cap
                /
                min_margin
                *
                broker_volume_min
            )

            raw_spread_volume = (
                broker_volume_max
            )

            if (
                spread_cost_estimator is not None
                and
                min_spread_cost > 0.0
            ):

                raw_spread_volume = (
                    standard_spread_cap
                    /
                    min_spread_cost
                    *
                    broker_volume_min
                )

            raw_volume = min(
                broker_volume_max,
                raw_risk_volume,
                raw_margin_volume,
                raw_spread_volume,
            )

            selected_volume = (
                self._normalize_volume_down(
                    volume=raw_volume,
                    volume_min=broker_volume_min,
                    volume_max=broker_volume_max,
                    volume_step=broker_volume_step,
                )
            )

            if selected_volume <= 0.0:

                selected_volume = (
                    broker_volume_min
                )

            safety_capped = False

            final_loss = 0.0

            final_margin = 0.0

            final_spread = 0.0

            while (
                selected_volume
                >=
                broker_volume_min
                -
                self._EPSILON
            ):

                exact_loss = (
                    self._estimate_positive(
                        loss_estimator,
                        selected_volume,
                    )
                )

                exact_margin = (
                    self._estimate_positive(
                        margin_estimator,
                        selected_volume,
                    )
                )

                if (
                    exact_loss is None
                    or
                    exact_margin is None
                ):

                    return self._result(
                        valid=False,
                        reason="BROKER_VERIFICATION_FAILED",
                        direction=normalized_direction,
                        risk_base=risk_base,
                        balance=balance,
                        equity=equity,
                        free_margin=margin_free,
                        selected_volume=selected_volume,
                    )

                exact_spread = 0.0

                if spread_cost_estimator is not None:

                    spread_value = (
                        self._estimate_positive(
                            spread_cost_estimator,
                            selected_volume,
                        )
                    )

                    if spread_value is None:

                        return self._result(
                            valid=False,
                            reason="BROKER_SPREAD_VERIFICATION_FAILED",
                            direction=normalized_direction,
                            risk_base=risk_base,
                            balance=balance,
                            equity=equity,
                            free_margin=margin_free,
                            selected_volume=selected_volume,
                        )

                    exact_spread = spread_value

                loss_ok = (
                    exact_loss
                    <=
                    standard_hard_amount
                    +
                    self._EPSILON
                )

                margin_ok = (
                    exact_margin
                    <=
                    standard_margin_cap
                    +
                    self._EPSILON
                )

                spread_ok = (
                    spread_cost_estimator is None
                    or
                    exact_spread
                    <=
                    standard_spread_cap
                    +
                    self._EPSILON
                )

                if (
                    loss_ok
                    and
                    margin_ok
                    and
                    spread_ok
                ):

                    final_loss = exact_loss

                    final_margin = exact_margin

                    final_spread = exact_spread

                    break

                safety_capped = True

                selected_volume = (
                    self._previous_volume(
                        volume=selected_volume,
                        volume_min=broker_volume_min,
                        volume_step=broker_volume_step,
                    )
                )

                if selected_volume <= 0.0:

                    return self._result(
                        valid=False,
                        reason="NO_STANDARD_VOLUME_SATISFIES_HARD_LIMITS",
                        direction=normalized_direction,
                        risk_base=risk_base,
                        balance=balance,
                        equity=equity,
                        free_margin=margin_free,
                        minimum_volume_loss=min_loss,
                    )

            actual_risk_percent = (
                self._percentage(
                    final_loss,
                    risk_base,
                )
            )

            target_utilization = (
                self._percentage(
                    final_loss,
                    standard_target_amount,
                )
            )

            margin_percent = (
                self._percentage(
                    final_margin,
                    margin_free,
                )
            )

            spread_to_hard = (
                (
                    final_spread
                    /
                    standard_hard_amount
                )
                if (
                    final_spread > 0.0
                    and
                    standard_hard_amount > 0.0
                )
                else
                0.0
            )

            spread_to_stop_final = (
                (
                    final_spread
                    /
                    final_loss
                )
                if (
                    final_spread > 0.0
                    and
                    final_loss > 0.0
                )
                else
                0.0
            )

            stop_to_spread_final = (
                (
                    final_loss
                    /
                    final_spread
                )
                if final_spread > 0.0
                else
                0.0
            )

            if (
                final_loss
                >
                standard_target_amount
                +
                self._EPSILON
            ):

                reason = (
                    "OK_MIN_VOLUME_QUANTIZED_ABOVE_TARGET"
                )

            elif safety_capped:

                reason = (
                    "OK_STANDARD_SAFETY_CAPPED"
                )

            elif (
                requested
                >
                standard_hard_percent
                +
                self._EPSILON
            ):

                reason = (
                    "OK_REQUEST_CAPPED_TO_STANDARD_HARD_MAX"
                )

            else:

                reason = "OK"

            return self._result(
                valid=True,
                reason=reason,
                risk_mode=self.STANDARD_MODE,
                direction=normalized_direction,
                risk_base=risk_base,
                requested_risk_percent=requested,
                target_risk_percent=standard_target_percent,
                hard_max_risk_percent=standard_hard_percent,
                target_risk_amount=standard_target_amount,
                hard_max_risk_amount=standard_hard_amount,
                balance=balance,
                equity=equity,
                free_margin=margin_free,
                bid=market_bid,
                ask=market_ask,
                spread_price=spread_price,
                spread_points=spread_points,
                entry_price=entry,
                stop_loss=stop,
                stop_distance_price=stop_distance_price,
                stop_distance_points=stop_distance_points,
                operational_min_stop_price=operational_min_stop_price,
                operational_min_stop_points=operational_min_stop_points,
                volume_min=broker_volume_min,
                volume_max=broker_volume_max,
                volume_step=broker_volume_step,
                selected_volume=selected_volume,
                minimum_volume_loss=min_loss,
                estimated_stop_loss_amount=final_loss,
                actual_risk_percent=actual_risk_percent,
                risk_target_utilization_percent=target_utilization,
                margin_required=final_margin,
                margin_percent_of_free=margin_percent,
                spread_cost=final_spread,
                spread_cost_to_hard_risk_ratio=spread_to_hard,
                spread_cost_to_stop_risk_ratio=spread_to_stop_final,
                stop_risk_to_spread_cost_ratio=stop_to_spread_final,
            )

        # =====================================================================
        # MICRO fallback eligibility
        # =====================================================================

        if not self.policy.micro_enabled:

            return self._result(
                valid=False,
                reason="STANDARD_UNAVAILABLE_MICRO_DISABLED",
                direction=normalized_direction,
                risk_base=risk_base,
                balance=balance,
                equity=equity,
                free_margin=margin_free,
                minimum_volume_loss=min_loss,
                actual_risk_percent=min_actual_risk_percent,
            )

        if (
            risk_base
            <
            self.policy.micro_min_balance
            -
            self._EPSILON
        ):

            return self._result(
                valid=False,
                reason="MICRO_BALANCE_BELOW_MINIMUM",
                direction=normalized_direction,
                risk_base=risk_base,
                balance=balance,
                equity=equity,
                free_margin=margin_free,
                minimum_volume_loss=min_loss,
                actual_risk_percent=min_actual_risk_percent,
            )

        if (
            risk_base
            >
            self.policy.micro_max_balance
            +
            self._EPSILON
        ):

            return self._result(
                valid=False,
                reason="MICRO_BALANCE_ABOVE_BOOTSTRAP_MAX",
                direction=normalized_direction,
                risk_base=risk_base,
                balance=balance,
                equity=equity,
                free_margin=margin_free,
                minimum_volume_loss=min_loss,
                actual_risk_percent=min_actual_risk_percent,
            )

        # =====================================================================
        # MICRO_BOOTSTRAP
        #
        # IMPORTANT:
        # Always minimum lot.
        # =====================================================================

        micro_hard_percent = (
            self.policy.micro_hard_max_risk_percent
        )

        micro_hard_amount = (
            risk_base
            *
            micro_hard_percent
            /
            100.0
        )

        if (
            min_loss
            >
            micro_hard_amount
            +
            self._EPSILON
        ):

            return self._result(
                valid=False,
                reason="MICRO_MIN_VOLUME_EXCEEDS_HARD_RISK",
                risk_mode=self.MICRO_MODE,
                direction=normalized_direction,
                risk_base=risk_base,
                requested_risk_percent=requested,
                target_risk_percent=micro_hard_percent,
                hard_max_risk_percent=micro_hard_percent,
                target_risk_amount=micro_hard_amount,
                hard_max_risk_amount=micro_hard_amount,
                balance=balance,
                equity=equity,
                free_margin=margin_free,
                bid=market_bid,
                ask=market_ask,
                spread_price=spread_price,
                spread_points=spread_points,
                entry_price=entry,
                stop_loss=stop,
                stop_distance_price=stop_distance_price,
                stop_distance_points=stop_distance_points,
                operational_min_stop_price=operational_min_stop_price,
                operational_min_stop_points=operational_min_stop_points,
                volume_min=broker_volume_min,
                volume_max=broker_volume_max,
                volume_step=broker_volume_step,
                minimum_volume_loss=min_loss,
                actual_risk_percent=min_actual_risk_percent,
                spread_cost=min_spread_cost,
                spread_cost_to_stop_risk_ratio=spread_to_stop,
                stop_risk_to_spread_cost_ratio=stop_to_spread,
            )

        micro_margin_cap = (
            margin_free
            *
            self.policy.micro_max_margin_percent_of_free
            /
            100.0
        )

        if (
            min_margin
            >
            micro_margin_cap
            +
            self._EPSILON
        ):

            return self._result(
                valid=False,
                reason="MICRO_MIN_VOLUME_EXCEEDS_MARGIN_CAP",
                risk_mode=self.MICRO_MODE,
                direction=normalized_direction,
                risk_base=risk_base,
                balance=balance,
                equity=equity,
                free_margin=margin_free,
                minimum_volume_loss=min_loss,
                actual_risk_percent=min_actual_risk_percent,
                margin_required=min_margin,
                margin_percent_of_free=min_margin_percent,
                spread_cost=min_spread_cost,
                spread_cost_to_stop_risk_ratio=spread_to_stop,
                stop_risk_to_spread_cost_ratio=stop_to_spread,
            )

        if (
            spread_cost_estimator is not None
            and
            spread_to_stop
            >
            self.policy.micro_max_spread_cost_to_stop_risk_ratio
            +
            self._EPSILON
        ):

            return self._result(
                valid=False,
                reason="MICRO_SPREAD_DOMINATES_STOP_RISK",
                risk_mode=self.MICRO_MODE,
                direction=normalized_direction,
                risk_base=risk_base,
                balance=balance,
                equity=equity,
                free_margin=margin_free,
                minimum_volume_loss=min_loss,
                actual_risk_percent=min_actual_risk_percent,
                margin_required=min_margin,
                margin_percent_of_free=min_margin_percent,
                spread_cost=min_spread_cost,
                spread_cost_to_stop_risk_ratio=spread_to_stop,
                stop_risk_to_spread_cost_ratio=stop_to_spread,
            )

        if (
            spread_cost_estimator is not None
            and
            min_spread_cost > 0.0
            and
            stop_to_spread
            >
            self.policy.micro_max_stop_to_spread_risk_ratio
            +
            self._EPSILON
        ):

            return self._result(
                valid=False,
                reason="MICRO_STOP_TOO_WIDE_FOR_FRICTION",
                risk_mode=self.MICRO_MODE,
                direction=normalized_direction,
                risk_base=risk_base,
                balance=balance,
                equity=equity,
                free_margin=margin_free,
                minimum_volume_loss=min_loss,
                actual_risk_percent=min_actual_risk_percent,
                margin_required=min_margin,
                margin_percent_of_free=min_margin_percent,
                spread_cost=min_spread_cost,
                spread_cost_to_stop_risk_ratio=spread_to_stop,
                stop_risk_to_spread_cost_ratio=stop_to_spread,
            )

        # =====================================================================
        # Exact minimum-lot verification
        # =====================================================================

        final_loss = self._estimate_positive(
            loss_estimator,
            broker_volume_min,
        )

        final_margin = self._estimate_positive(
            margin_estimator,
            broker_volume_min,
        )

        if (
            final_loss is None
            or
            final_margin is None
        ):

            return self._result(
                valid=False,
                reason="MICRO_BROKER_VERIFICATION_FAILED",
                risk_mode=self.MICRO_MODE,
                direction=normalized_direction,
                risk_base=risk_base,
            )

        final_spread = 0.0

        if spread_cost_estimator is not None:

            spread_value = self._estimate_positive(
                spread_cost_estimator,
                broker_volume_min,
            )

            if spread_value is None:

                return self._result(
                    valid=False,
                    reason="MICRO_SPREAD_VERIFICATION_FAILED",
                    risk_mode=self.MICRO_MODE,
                    direction=normalized_direction,
                    risk_base=risk_base,
                )

            final_spread = spread_value

        actual_risk_percent = (
            self._percentage(
                final_loss,
                risk_base,
            )
        )

        margin_percent = (
            self._percentage(
                final_margin,
                margin_free,
            )
        )

        spread_to_stop_final = (
            (
                final_spread
                /
                final_loss
            )
            if (
                final_spread > 0.0
                and
                final_loss > 0.0
            )
            else
            0.0
        )

        stop_to_spread_final = (
            (
                final_loss
                /
                final_spread
            )
            if final_spread > 0.0
            else
            0.0
        )

        return self._result(
            valid=True,
            reason="OK_MICRO_BOOTSTRAP_MIN_VOLUME",
            risk_mode=self.MICRO_MODE,
            direction=normalized_direction,
            risk_base=risk_base,
            requested_risk_percent=requested,
            target_risk_percent=micro_hard_percent,
            hard_max_risk_percent=micro_hard_percent,
            target_risk_amount=micro_hard_amount,
            hard_max_risk_amount=micro_hard_amount,
            balance=balance,
            equity=equity,
            free_margin=margin_free,
            bid=market_bid,
            ask=market_ask,
            spread_price=spread_price,
            spread_points=spread_points,
            entry_price=entry,
            stop_loss=stop,
            stop_distance_price=stop_distance_price,
            stop_distance_points=stop_distance_points,
            operational_min_stop_price=operational_min_stop_price,
            operational_min_stop_points=operational_min_stop_points,
            volume_min=broker_volume_min,
            volume_max=broker_volume_max,
            volume_step=broker_volume_step,
            selected_volume=broker_volume_min,
            minimum_volume_loss=min_loss,
            estimated_stop_loss_amount=final_loss,
            actual_risk_percent=actual_risk_percent,
            risk_target_utilization_percent=(
                self._percentage(
                    final_loss,
                    micro_hard_amount,
                )
            ),
            margin_required=final_margin,
            margin_percent_of_free=margin_percent,
            spread_cost=final_spread,
            spread_cost_to_hard_risk_ratio=(
                (
                    final_spread
                    /
                    micro_hard_amount
                )
                if (
                    final_spread > 0.0
                    and
                    micro_hard_amount > 0.0
                )
                else
                0.0
            ),
            spread_cost_to_stop_risk_ratio=spread_to_stop_final,
            stop_risk_to_spread_cost_ratio=stop_to_spread_final,
        )


broker_aware_risk_engine = BrokerAwareRiskEngine()