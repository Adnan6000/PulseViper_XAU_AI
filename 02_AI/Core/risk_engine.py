"""
PulseViper Risk Engine

Responsibilities
----------------
- Risk-per-trade calculation
- Small-account fixed-risk mode
- Position / lot-size calculation
- Stop-loss validation
- Take-profit validation
- Risk/reward calculation
- Maximum lot protection
- Confidence-based risk adjustment
- Broker spread protection
- Minimum account balance protection

Important
---------
This module contains calculation and validation logic only.
It does NOT communicate with MT5 and does NOT place trades.

Risk Policy
-----------
1. Balance < $3:
   Trading blocked.

2. Balance $3 to $100:
   Fixed risk = $1 per trade.

3. Balance > $100:
   Percentage risk mode is used.
   Default = 1%.

4. Minimum position size:
   0.01 lot.

5. Position size is normalized to:
   0.01 lot steps.

6. Spread above configured maximum:
   Trading blocked.

The engine does not perform account transfers, cent-account
conversion, or broker order execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ============================================================================
# Result
# ============================================================================


@dataclass(frozen=True)
class RiskResult:
    """Immutable result returned by the risk engine."""

    valid: bool
    risk_amount: float
    risk_percent: float
    stop_distance: float
    position_size: float
    reward_distance: float
    risk_reward_ratio: float
    adjusted_risk_percent: float
    reason: str


# ============================================================================
# Risk Engine
# ============================================================================


class RiskEngine:
    """
    Calculate and validate trade risk.

    Small-account policy:

        $3 <= balance <= $100
            -> fixed $1 risk

        balance > $100
            -> percentage risk

        balance < $3
            -> blocked

    This engine does not communicate with MT5.
    """

    def __init__(
        self,
        default_risk_percent: float = 1.0,
        min_risk_percent: float = 0.1,
        max_risk_percent: float = 2.0,
        max_position_size: float = 100.0,
        min_position_size: float = 0.01,
        position_step: float = 0.01,
        min_risk_reward: float = 1.5,

        # Small-account policy
        small_account_min_balance: float = 3.0,
        small_account_max_balance: float = 100.0,
        small_account_fixed_risk: float = 1.0,

        # Spread protection
        max_spread_points: float = 300.0,
    ) -> None:

        self.default_risk_percent = self._clamp(
            self._to_float(
                default_risk_percent,
                1.0,
            ),
            self._to_float(
                min_risk_percent,
                0.1,
            ),
            self._to_float(
                max_risk_percent,
                2.0,
            ),
        )

        self.min_risk_percent = max(
            0.0,
            self._to_float(
                min_risk_percent,
                0.1,
            ),
        )

        self.max_risk_percent = max(
            self.min_risk_percent,
            self._to_float(
                max_risk_percent,
                2.0,
            ),
        )

        self.max_position_size = max(
            0.0,
            self._to_float(
                max_position_size,
                100.0,
            ),
        )

        self.min_position_size = max(
            0.0,
            self._to_float(
                min_position_size,
                0.01,
            ),
        )

        self.position_step = max(
            0.0001,
            self._to_float(
                position_step,
                0.01,
            ),
        )

        self.min_risk_reward = max(
            0.0,
            self._to_float(
                min_risk_reward,
                1.5,
            ),
        )

        # --------------------------------------------------------------------
        # Small-account policy
        # --------------------------------------------------------------------

        self.small_account_min_balance = max(
            0.0,
            self._to_float(
                small_account_min_balance,
                3.0,
            ),
        )

        self.small_account_max_balance = max(
            self.small_account_min_balance,
            self._to_float(
                small_account_max_balance,
                100.0,
            ),
        )

        self.small_account_fixed_risk = max(
            0.0,
            self._to_float(
                small_account_fixed_risk,
                1.0,
            ),
        )

        # --------------------------------------------------------------------
        # Spread policy
        # --------------------------------------------------------------------

        self.max_spread_points = max(
            0.0,
            self._to_float(
                max_spread_points,
                300.0,
            ),
        )

    # =========================================================================
    # Helpers
    # =========================================================================

    @staticmethod
    def _to_float(
        value: Any,
        default: float = 0.0,
    ) -> float:
        """Safely convert arbitrary input to float."""

        if value is None:
            return default

        if isinstance(value, bool):
            return float(value)

        if isinstance(value, (int, float)):
            return float(value)

        if isinstance(value, str):
            try:
                return float(value.strip())
            except ValueError:
                return default

        return default

    @staticmethod
    def _clamp(
        value: float,
        minimum: float,
        maximum: float,
    ) -> float:
        """Clamp numeric value to a defined range."""

        return max(
            minimum,
            min(
                maximum,
                value,
            ),
        )

    def _normalize_position_size(
        self,
        position_size: float,
    ) -> float:
        """
        Normalize position size to broker-style lot step.

        Example:

            0.997 -> 0.99
            1.004 -> 1.00
            0.011 -> 0.01

        Uses integer-style step calculation to avoid
        floating-point floor errors such as:

            1.0 // 0.01 -> 99
        """

        if position_size <= 0.0:
            return 0.0

        # Determine number of steps without relying on
        # floating-point floor division.
        steps = int(
            (position_size / self.position_step) + 1e-9
        )

        normalized = steps * self.position_step

        normalized = round(
            normalized,
            8,
        )

        if normalized < self.min_position_size:
            return 0.0

        return min(
            normalized,
            self.max_position_size,
        )

    # =========================================================================
    # Account Mode
    # =========================================================================

    def is_small_account(
        self,
        account_balance: float,
    ) -> bool:
        """
        Return True when account is in fixed-risk mode.

        Small-account mode:

            $3 <= balance <= $100
        """

        balance = self._to_float(
            account_balance,
            0.0,
        )

        return (
            balance >= self.small_account_min_balance
            and balance <= self.small_account_max_balance
        )

    def is_tradeable_balance(
        self,
        account_balance: float,
    ) -> bool:
        """
        Check whether account balance is sufficient for
        PulseViper's configured minimum trading balance.
        """

        balance = self._to_float(
            account_balance,
            0.0,
        )

        return balance >= self.small_account_min_balance

    # =========================================================================
    # Risk Percentage
    # =========================================================================

    def calculate_risk_percent(
        self,
        confidence_score: float | None = None,
        requested_risk_percent: float | None = None,
    ) -> float:
        """
        Calculate percentage-based risk.

        This method is used for normal percentage-risk mode.

        Confidence mapping:

            < 50
                -> blocked / 0

            50-64
                -> 50% of requested risk

            65-79
                -> 75% of requested risk

            >= 80
                -> 100% of requested risk
        """

        requested = (
            self.default_risk_percent
            if requested_risk_percent is None
            else self._to_float(
                requested_risk_percent,
                self.default_risk_percent,
            )
        )

        requested = self._clamp(
            requested,
            self.min_risk_percent,
            self.max_risk_percent,
        )

        if confidence_score is None:
            return requested

        confidence = self._clamp(
            self._to_float(
                confidence_score,
                0.0,
            ),
            0.0,
            100.0,
        )

        if confidence < 50.0:
            return 0.0

        if confidence < 65.0:
            multiplier = 0.50

        elif confidence < 80.0:
            multiplier = 0.75

        else:
            multiplier = 1.0

        adjusted = requested * multiplier

        if adjusted <= 0.0:
            return 0.0

        return self._clamp(
            adjusted,
            self.min_risk_percent,
            self.max_risk_percent,
        )

    # =========================================================================
    # Risk Amount
    # =========================================================================

    def calculate_risk_amount(
        self,
        account_balance: float,
        risk_percent: float,
    ) -> float:
        """
        Calculate monetary risk from percentage.

        Formula:

            risk = balance × risk% / 100
        """

        balance = self._to_float(
            account_balance,
            0.0,
        )

        percent = self._clamp(
            self._to_float(
                risk_percent,
                0.0,
            ),
            0.0,
            self.max_risk_percent,
        )

        if balance <= 0.0:
            return 0.0

        return round(
            balance * percent / 100.0,
            2,
        )

    # =========================================================================
    # Small Account Risk
    # =========================================================================

    def calculate_effective_risk_amount(
        self,
        account_balance: float,
        confidence_score: float | None = None,
        requested_risk_percent: float | None = None,
        requested_risk_amount: float | None = None,
    ) -> tuple[float, float]:
        """
        Calculate effective risk amount and effective risk percentage.

        Returns:

            (risk_amount, effective_risk_percent)

        Policy:

            $3-$100
                -> fixed $1 risk

            >$100
                -> percentage risk

        For small accounts, confidence still controls whether
        a trade is allowed.

        We intentionally do NOT increase the $1 risk to compensate
        for a small balance.
        """

        balance = self._to_float(
            account_balance,
            0.0,
        )

        if balance < self.small_account_min_balance:
            return 0.0, 0.0

        # --------------------------------------------------------------------
        # Small account mode
        # --------------------------------------------------------------------

        if self.is_small_account(balance):

            fixed_risk = self.small_account_fixed_risk

            if requested_risk_amount is not None:
                requested_amount = self._to_float(
                    requested_risk_amount,
                    fixed_risk,
                )

                # Never allow requested risk to exceed
                # the configured fixed-risk policy.
                fixed_risk = min(
                    fixed_risk,
                    requested_amount,
                )

            if fixed_risk <= 0.0:
                return 0.0, 0.0

            # A $1 risk on a $3 account is 33.33%.
            # This is intentional under the small-account policy.
            effective_percent = (
                fixed_risk
                / balance
            ) * 100.0

            return (
                round(
                    fixed_risk,
                    2,
                ),
                round(
                    effective_percent,
                    4,
                ),
            )

        # --------------------------------------------------------------------
        # Normal account mode
        # --------------------------------------------------------------------

        effective_percent = self.calculate_risk_percent(
            confidence_score=confidence_score,
            requested_risk_percent=requested_risk_percent,
        )

        if effective_percent <= 0.0:
            return 0.0, 0.0

        risk_amount = self.calculate_risk_amount(
            balance,
            effective_percent,
        )

        return (
            risk_amount,
            effective_percent,
        )

    # =========================================================================
    # Position Size
    # =========================================================================

    def calculate_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss: float,
        risk_percent: float | None = None,
        value_per_price_unit: float = 1.0,
        risk_amount: float | None = None,
    ) -> float:
        """
        Calculate position size from monetary risk.

        Priority:

            1. Explicit risk_amount
            2. Percentage risk

        Formula:

            position_size =
                risk_amount /
                (
                    stop_distance
                    × value_per_price_unit
                )
        """

        balance = self._to_float(
            account_balance,
            0.0,
        )

        entry = self._to_float(
            entry_price,
            0.0,
        )

        stop = self._to_float(
            stop_loss,
            0.0,
        )

        unit_value = self._to_float(
            value_per_price_unit,
            1.0,
        )

        if balance < self.small_account_min_balance:
            return 0.0

        if entry <= 0.0:
            return 0.0

        if stop <= 0.0:
            return 0.0

        if unit_value <= 0.0:
            return 0.0

        stop_distance = abs(
            entry - stop
        )

        if stop_distance <= 0.0:
            return 0.0

        # --------------------------------------------------------------------
        # Determine monetary risk
        # --------------------------------------------------------------------

        if risk_amount is not None:

            effective_risk_amount = self._to_float(
                risk_amount,
                0.0,
            )

        else:

            effective_risk = (
                self.default_risk_percent
                if risk_percent is None
                else self._to_float(
                    risk_percent,
                    self.default_risk_percent,
                )
            )

            effective_risk = self._clamp(
                effective_risk,
                0.0,
                self.max_risk_percent,
            )

            effective_risk_amount = (
                self.calculate_risk_amount(
                    balance,
                    effective_risk,
                )
            )

        if effective_risk_amount <= 0.0:
            return 0.0

        # --------------------------------------------------------------------
        # Position size
        # --------------------------------------------------------------------

        raw_position_size = (
            effective_risk_amount
            / (
                stop_distance
                * unit_value
            )
        )

        return self._normalize_position_size(
            raw_position_size
        )

    # =========================================================================
    # Stop Loss
    # =========================================================================

    @staticmethod
    def validate_stop_loss(
        direction: str,
        entry_price: float,
        stop_loss: float,
    ) -> bool:
        """Validate SL placement for BUY or SELL."""

        direction_value = (
            direction.upper().strip()
        )

        entry = RiskEngine._to_float(
            entry_price,
            0.0,
        )

        stop = RiskEngine._to_float(
            stop_loss,
            0.0,
        )

        if entry <= 0.0 or stop <= 0.0:
            return False

        if direction_value == "BUY":
            return stop < entry

        if direction_value == "SELL":
            return stop > entry

        return False

    # =========================================================================
    # Take Profit
    # =========================================================================

    @staticmethod
    def validate_take_profit(
        direction: str,
        entry_price: float,
        take_profit: float,
    ) -> bool:
        """Validate TP placement for BUY or SELL."""

        direction_value = (
            direction.upper().strip()
        )

        entry = RiskEngine._to_float(
            entry_price,
            0.0,
        )

        target = RiskEngine._to_float(
            take_profit,
            0.0,
        )

        if entry <= 0.0 or target <= 0.0:
            return False

        if direction_value == "BUY":
            return target > entry

        if direction_value == "SELL":
            return target < entry

        return False

    # =========================================================================
    # Risk Reward
    # =========================================================================

    @staticmethod
    def calculate_risk_reward(
        direction: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
    ) -> float:
        """Calculate reward-to-risk ratio."""

        direction_value = (
            direction.upper().strip()
        )

        entry = RiskEngine._to_float(
            entry_price,
            0.0,
        )

        stop = RiskEngine._to_float(
            stop_loss,
            0.0,
        )

        target = RiskEngine._to_float(
            take_profit,
            0.0,
        )

        if entry <= 0.0:
            return 0.0

        if stop <= 0.0 or target <= 0.0:
            return 0.0

        if direction_value == "BUY":

            risk_distance = (
                entry - stop
            )

            reward_distance = (
                target - entry
            )

        elif direction_value == "SELL":

            risk_distance = (
                stop - entry
            )

            reward_distance = (
                entry - target
            )

        else:
            return 0.0

        if risk_distance <= 0.0:
            return 0.0

        if reward_distance <= 0.0:
            return 0.0

        return round(
            reward_distance / risk_distance,
            4,
        )

    # =========================================================================
    # Spread Validation
    # =========================================================================

    def validate_spread(
        self,
        spread_points: float | None,
        max_spread_points: float | None = None,
    ) -> bool:
        """
        Validate current broker spread.

        Example:

            spread = 250
                -> allowed

            spread = 300
                -> allowed

            spread = 301
                -> blocked
        """

        if spread_points is None:
            return True

        spread = self._to_float(
            spread_points,
            0.0,
        )

        maximum = (
            self.max_spread_points
            if max_spread_points is None
            else self._to_float(
                max_spread_points,
                self.max_spread_points,
            )
        )

        if spread < 0.0:
            return False

        return spread <= maximum

    # =========================================================================
    # Complete Risk Assessment
    # =========================================================================

    def assess_trade(
        self,
        account_balance: float,
        direction: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        confidence_score: float | None = None,
        requested_risk_percent: float | None = None,
        value_per_price_unit: float = 1.0,
        spread_points: float | None = None,
        requested_risk_amount: float | None = None,
    ) -> RiskResult:
        """
        Perform complete risk validation and position sizing.
        """

        direction_value = (
            direction.upper().strip()
        )

        balance = self._to_float(
            account_balance,
            0.0,
        )

        entry = self._to_float(
            entry_price,
            0.0,
        )

        stop = self._to_float(
            stop_loss,
            0.0,
        )

        target = self._to_float(
            take_profit,
            0.0,
        )

        # ====================================================================
        # Balance
        # ====================================================================

        if balance < self.small_account_min_balance:

            return RiskResult(
                valid=False,
                risk_amount=0.0,
                risk_percent=0.0,
                stop_distance=0.0,
                position_size=0.0,
                reward_distance=0.0,
                risk_reward_ratio=0.0,
                adjusted_risk_percent=0.0,
                reason=(
                    "Account balance below minimum "
                    f"of ${self.small_account_min_balance:.2f}"
                ),
            )

        # ====================================================================
        # Direction
        # ====================================================================

        if direction_value not in {
            "BUY",
            "SELL",
        }:

            return RiskResult(
                valid=False,
                risk_amount=0.0,
                risk_percent=0.0,
                stop_distance=0.0,
                position_size=0.0,
                reward_distance=0.0,
                risk_reward_ratio=0.0,
                adjusted_risk_percent=0.0,
                reason="Invalid trade direction",
            )

        # ====================================================================
        # Spread
        # ====================================================================

        if not self.validate_spread(
            spread_points,
        ):

            return RiskResult(
                valid=False,
                risk_amount=0.0,
                risk_percent=0.0,
                stop_distance=0.0,
                position_size=0.0,
                reward_distance=0.0,
                risk_reward_ratio=0.0,
                adjusted_risk_percent=0.0,
                reason=(
                    "Spread exceeds configured maximum "
                    f"of {self.max_spread_points:.0f} points"
                ),
            )

        # ====================================================================
        # Stop Loss
        # ====================================================================

        if not self.validate_stop_loss(
            direction_value,
            entry,
            stop,
        ):

            return RiskResult(
                valid=False,
                risk_amount=0.0,
                risk_percent=0.0,
                stop_distance=0.0,
                position_size=0.0,
                reward_distance=0.0,
                risk_reward_ratio=0.0,
                adjusted_risk_percent=0.0,
                reason="Invalid stop loss",
            )

        # ====================================================================
        # Take Profit
        # ====================================================================

        if not self.validate_take_profit(
            direction_value,
            entry,
            target,
        ):

            return RiskResult(
                valid=False,
                risk_amount=0.0,
                risk_percent=0.0,
                stop_distance=0.0,
                position_size=0.0,
                reward_distance=0.0,
                risk_reward_ratio=0.0,
                adjusted_risk_percent=0.0,
                reason="Invalid take profit",
            )

        # ====================================================================
        # Confidence
        # ====================================================================

        if confidence_score is not None:

            confidence = self._clamp(
                self._to_float(
                    confidence_score,
                    0.0,
                ),
                0.0,
                100.0,
            )

            # For every account size, confidence below 50
            # blocks trading.
            if confidence < 50.0:

                return RiskResult(
                    valid=False,
                    risk_amount=0.0,
                    risk_percent=0.0,
                    stop_distance=abs(
                        entry - stop
                    ),
                    position_size=0.0,
                    reward_distance=abs(
                        target - entry
                    ),
                    risk_reward_ratio=self.calculate_risk_reward(
                        direction_value,
                        entry,
                        stop,
                        target,
                    ),
                    adjusted_risk_percent=0.0,
                    reason=(
                        "Confidence below trade-risk threshold"
                    ),
                )

        # ====================================================================
        # Risk calculation
        # ====================================================================

        risk_amount, effective_risk_percent = (
            self.calculate_effective_risk_amount(
                account_balance=balance,
                confidence_score=confidence_score,
                requested_risk_percent=requested_risk_percent,
                requested_risk_amount=requested_risk_amount,
            )
        )

        if risk_amount <= 0.0:

            return RiskResult(
                valid=False,
                risk_amount=0.0,
                risk_percent=0.0,
                stop_distance=abs(
                    entry - stop
                ),
                position_size=0.0,
                reward_distance=abs(
                    target - entry
                ),
                risk_reward_ratio=self.calculate_risk_reward(
                    direction_value,
                    entry,
                    stop,
                    target,
                ),
                adjusted_risk_percent=0.0,
                reason="Risk amount is zero",
            )

        # ====================================================================
        # Distances
        # ====================================================================

        stop_distance = abs(
            entry - stop
        )

        reward_distance = abs(
            target - entry
        )

        risk_reward = self.calculate_risk_reward(
            direction_value,
            entry,
            stop,
            target,
        )

        # ====================================================================
        # Risk / Reward
        # ====================================================================

        if risk_reward < self.min_risk_reward:

            return RiskResult(
                valid=False,
                risk_amount=risk_amount,
                risk_percent=effective_risk_percent,
                stop_distance=stop_distance,
                position_size=0.0,
                reward_distance=reward_distance,
                risk_reward_ratio=risk_reward,
                adjusted_risk_percent=effective_risk_percent,
                reason=(
                    "Risk/reward below minimum threshold"
                ),
            )

        # ====================================================================
        # Position Size
        # ====================================================================

        position_size = self.calculate_position_size(
            account_balance=balance,
            entry_price=entry,
            stop_loss=stop,
            risk_amount=risk_amount,
            value_per_price_unit=value_per_price_unit,
        )

        if position_size <= 0.0:

            return RiskResult(
                valid=False,
                risk_amount=risk_amount,
                risk_percent=effective_risk_percent,
                stop_distance=stop_distance,
                position_size=0.0,
                reward_distance=reward_distance,
                risk_reward_ratio=risk_reward,
                adjusted_risk_percent=effective_risk_percent,
                reason=(
                    "Calculated position size is below "
                    "minimum lot size"
                ),
            )

        # ====================================================================
        # Successful assessment
        # ====================================================================

        return RiskResult(
            valid=True,
            risk_amount=risk_amount,
            risk_percent=effective_risk_percent,
            stop_distance=stop_distance,
            position_size=position_size,
            reward_distance=reward_distance,
            risk_reward_ratio=risk_reward,
            adjusted_risk_percent=effective_risk_percent,
            reason="Risk assessment passed",
        )


# ============================================================================
# Global Engine Instance
# ============================================================================

risk_engine = RiskEngine()