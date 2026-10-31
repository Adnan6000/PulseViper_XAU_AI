"""
===============================================================================
Module      : execution_friction_model.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Shadow Execution Friction / Cost Feasibility Model
===============================================================================

Status
------
RESEARCH / SHADOW / DEMO ONLY.

This module does NOT:
- connect to MT5
- send orders
- modify positions
- modify SL/TP
- authorize live execution
- modify production trade_ready
- modify production RiskEngine
- modify LEI / RWEI / Institutional Zone policy

Purpose
-------
Evaluate whether a broker-calibrated candidate is economically executable after
including:

    spread
    + estimated slippage
    + estimated commission

The model intentionally separates:

    market validity

from:

    execution feasibility

A setup can remain structurally valid while execution friction makes it too
expensive to trade under the current broker/account conditions.

Core principles
---------------
1. Structural stop geometry is never changed by this model.

2. Monetary stop risk and execution friction are tracked separately.

3. All-in adverse exposure is:

       projected_stop_loss + total_friction_cost

4. Spread/slippage are also compared with structural stop distance because a
   small absolute cost can still dominate a tight M1 scalp.

5. `execution_feasible` is SHADOW research output only. It is NOT production
   authorization and does not alter `trade_ready`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(
    frozen=True,
)
class ExecutionFrictionPolicy:
    """
    Provisional SHADOW execution-cost policy.

    These thresholds are research defaults, not final production policy.

    max_spread_to_stop_distance_ratio
        spread_price / structural_stop_distance.

    max_slippage_to_stop_distance_ratio
        estimated_slippage_price / structural_stop_distance.

    max_total_friction_to_stop_risk_ratio
        (spread + slippage + commission) / projected_stop_loss.

    max_all_in_loss_to_budget_ratio
        (projected_stop_loss + total_friction) / hard_loss_budget.
    """

    max_spread_to_stop_distance_ratio: float = 0.60

    max_slippage_to_stop_distance_ratio: float = 0.20

    max_total_friction_to_stop_risk_ratio: float = 0.80

    max_all_in_loss_to_budget_ratio: float = 1.00

    def __post_init__(
        self,
    ) -> None:

        for (
            name,
            value,
        ) in (
            (
                "max_spread_to_stop_distance_ratio",
                self.max_spread_to_stop_distance_ratio,
            ),
            (
                "max_slippage_to_stop_distance_ratio",
                self.max_slippage_to_stop_distance_ratio,
            ),
            (
                "max_total_friction_to_stop_risk_ratio",
                self.max_total_friction_to_stop_risk_ratio,
            ),
            (
                "max_all_in_loss_to_budget_ratio",
                self.max_all_in_loss_to_budget_ratio,
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


@dataclass(
    frozen=True,
)
class ExecutionFrictionAssessment:
    valid: bool

    execution_feasible: bool

    reason: str

    violations: tuple[
        str,
        ...,
    ]

    mode: str

    version: str

    live_authorized: bool

    direction: str

    volume: float

    balance: float

    risk_base: float

    hard_loss_budget: float

    entry_price: float

    stop_loss: float

    stop_distance_price: float

    point: float

    stop_distance_points: float

    spread_price: float

    spread_points: float

    spread_cost: float

    estimated_slippage_price: float

    estimated_slippage_points: float

    estimated_slippage_cost: float

    estimated_commission_cost: float

    total_friction_cost: float

    projected_stop_loss: float

    all_in_adverse_loss: float

    spread_to_stop_distance_ratio: float

    slippage_to_stop_distance_ratio: float

    total_friction_to_stop_risk_ratio: float

    all_in_loss_to_budget_ratio: float

    projected_stop_loss_percent_of_risk_base: float

    total_friction_percent_of_risk_base: float

    all_in_loss_percent_of_risk_base: float


class ExecutionFrictionModel:
    VERSION = "1.0"

    MODE = (
        "SHADOW_EXECUTION_FRICTION_RESEARCH_ONLY"
    )

    PASS = "PASS"

    BLOCKED = "BLOCKED"

    def __init__(
        self,
        policy: ExecutionFrictionPolicy | None = None,
    ) -> None:

        self.policy = (
            policy
            if policy is not None
            else ExecutionFrictionPolicy()
        )

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
    def _ratio(
        numerator: float,
        denominator: float,
    ) -> float:

        if denominator <= 0.0:

            return 0.0

        return round(
            numerator
            /
            denominator,
            8,
        )

    @staticmethod
    def _percentage(
        numerator: float,
        denominator: float,
    ) -> float:

        if denominator <= 0.0:

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

    def _invalid(
        self,
        *,
        reason: str,
        direction: str = "INVALID",
    ) -> ExecutionFrictionAssessment:

        return ExecutionFrictionAssessment(
            valid=False,
            execution_feasible=False,
            reason=reason,
            violations=(
                reason,
            ),
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            direction=direction,
            volume=0.0,
            balance=0.0,
            risk_base=0.0,
            hard_loss_budget=0.0,
            entry_price=0.0,
            stop_loss=0.0,
            stop_distance_price=0.0,
            point=0.0,
            stop_distance_points=0.0,
            spread_price=0.0,
            spread_points=0.0,
            spread_cost=0.0,
            estimated_slippage_price=0.0,
            estimated_slippage_points=0.0,
            estimated_slippage_cost=0.0,
            estimated_commission_cost=0.0,
            total_friction_cost=0.0,
            projected_stop_loss=0.0,
            all_in_adverse_loss=0.0,
            spread_to_stop_distance_ratio=0.0,
            slippage_to_stop_distance_ratio=0.0,
            total_friction_to_stop_risk_ratio=0.0,
            all_in_loss_to_budget_ratio=0.0,
            projected_stop_loss_percent_of_risk_base=0.0,
            total_friction_percent_of_risk_base=0.0,
            all_in_loss_percent_of_risk_base=0.0,
        )

    def evaluate(
        self,
        *,
        direction: str,
        volume: float,
        balance: float,
        equity: float,
        hard_loss_budget: float,
        entry_price: float,
        stop_loss: float,
        point: float,
        spread_price: float,
        spread_cost: float,
        projected_stop_loss: float,
        estimated_slippage_price: float = 0.0,
        estimated_slippage_cost: float = 0.0,
        estimated_commission_cost: float = 0.0,
    ) -> ExecutionFrictionAssessment:

        normalized_direction = (
            self._normalize_direction(
                direction
            )
        )

        if normalized_direction == "INVALID":

            return self._invalid(
                reason="INVALID_DIRECTION",
            )

        values = {
            "volume": self._number(
                volume
            ),
            "balance": self._number(
                balance
            ),
            "equity": self._number(
                equity
            ),
            "hard_loss_budget": self._number(
                hard_loss_budget
            ),
            "entry_price": self._number(
                entry_price
            ),
            "stop_loss": self._number(
                stop_loss
            ),
            "point": self._number(
                point
            ),
            "spread_price": self._number(
                spread_price
            ),
            "spread_cost": self._number(
                spread_cost
            ),
            "projected_stop_loss": self._number(
                projected_stop_loss
            ),
            "estimated_slippage_price": self._number(
                estimated_slippage_price
            ),
            "estimated_slippage_cost": self._number(
                estimated_slippage_cost
            ),
            "estimated_commission_cost": self._number(
                estimated_commission_cost
            ),
        }

        for (
            name,
            value,
        ) in values.items():

            if not math.isfinite(
                value
            ):

                return self._invalid(
                    reason=(
                        f"INVALID_{name.upper()}"
                    ),
                    direction=normalized_direction,
                )

        positive_fields = (
            "volume",
            "balance",
            "equity",
            "hard_loss_budget",
            "entry_price",
            "stop_loss",
            "point",
            "projected_stop_loss",
        )

        for name in positive_fields:

            if values[
                name
            ] <= 0.0:

                return self._invalid(
                    reason=(
                        f"NON_POSITIVE_{name.upper()}"
                    ),
                    direction=normalized_direction,
                )

        non_negative_fields = (
            "spread_price",
            "spread_cost",
            "estimated_slippage_price",
            "estimated_slippage_cost",
            "estimated_commission_cost",
        )

        for name in non_negative_fields:

            if values[
                name
            ] < 0.0:

                return self._invalid(
                    reason=(
                        f"NEGATIVE_{name.upper()}"
                    ),
                    direction=normalized_direction,
                )

        stop_distance_price = abs(
            values[
                "entry_price"
            ]
            -
            values[
                "stop_loss"
            ]
        )

        if stop_distance_price <= 0.0:

            return self._invalid(
                reason=(
                    "ZERO_STRUCTURAL_STOP_DISTANCE"
                ),
                direction=normalized_direction,
            )

        risk_base = min(
            values[
                "balance"
            ],
            values[
                "equity"
            ],
        )

        if risk_base <= 0.0:

            return self._invalid(
                reason="NON_POSITIVE_RISK_BASE",
                direction=normalized_direction,
            )

        stop_distance_points = (
            stop_distance_price
            /
            values[
                "point"
            ]
        )

        spread_points = (
            values[
                "spread_price"
            ]
            /
            values[
                "point"
            ]
        )

        estimated_slippage_points = (
            values[
                "estimated_slippage_price"
            ]
            /
            values[
                "point"
            ]
        )

        total_friction_cost = (
            values[
                "spread_cost"
            ]
            +
            values[
                "estimated_slippage_cost"
            ]
            +
            values[
                "estimated_commission_cost"
            ]
        )

        all_in_adverse_loss = (
            values[
                "projected_stop_loss"
            ]
            +
            total_friction_cost
        )

        spread_to_stop_distance_ratio = (
            self._ratio(
                values[
                    "spread_price"
                ],
                stop_distance_price,
            )
        )

        slippage_to_stop_distance_ratio = (
            self._ratio(
                values[
                    "estimated_slippage_price"
                ],
                stop_distance_price,
            )
        )

        total_friction_to_stop_risk_ratio = (
            self._ratio(
                total_friction_cost,
                values[
                    "projected_stop_loss"
                ],
            )
        )

        all_in_loss_to_budget_ratio = (
            self._ratio(
                all_in_adverse_loss,
                values[
                    "hard_loss_budget"
                ],
            )
        )

        violations: list[
            str
        ] = []

        if (
            spread_to_stop_distance_ratio
            >
            self.policy
            .max_spread_to_stop_distance_ratio
        ):

            violations.append(
                "SPREAD_DOMINATES_STRUCTURAL_STOP"
            )

        if (
            slippage_to_stop_distance_ratio
            >
            self.policy
            .max_slippage_to_stop_distance_ratio
        ):

            violations.append(
                "SLIPPAGE_DOMINATES_STRUCTURAL_STOP"
            )

        if (
            total_friction_to_stop_risk_ratio
            >
            self.policy
            .max_total_friction_to_stop_risk_ratio
        ):

            violations.append(
                "TOTAL_FRICTION_DOMINATES_STOP_RISK"
            )

        if (
            all_in_loss_to_budget_ratio
            >
            self.policy
            .max_all_in_loss_to_budget_ratio
        ):

            violations.append(
                "ALL_IN_LOSS_EXCEEDS_HARD_BUDGET"
            )

        execution_feasible = (
            not violations
        )

        reason = (
            self.PASS
            if execution_feasible
            else violations[
                0
            ]
        )

        return ExecutionFrictionAssessment(
            valid=True,
            execution_feasible=(
                execution_feasible
            ),
            reason=reason,
            violations=tuple(
                violations
            ),
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            direction=normalized_direction,
            volume=values[
                "volume"
            ],
            balance=values[
                "balance"
            ],
            risk_base=risk_base,
            hard_loss_budget=values[
                "hard_loss_budget"
            ],
            entry_price=values[
                "entry_price"
            ],
            stop_loss=values[
                "stop_loss"
            ],
            stop_distance_price=(
                stop_distance_price
            ),
            point=values[
                "point"
            ],
            stop_distance_points=(
                stop_distance_points
            ),
            spread_price=values[
                "spread_price"
            ],
            spread_points=spread_points,
            spread_cost=values[
                "spread_cost"
            ],
            estimated_slippage_price=(
                values[
                    "estimated_slippage_price"
                ]
            ),
            estimated_slippage_points=(
                estimated_slippage_points
            ),
            estimated_slippage_cost=(
                values[
                    "estimated_slippage_cost"
                ]
            ),
            estimated_commission_cost=(
                values[
                    "estimated_commission_cost"
                ]
            ),
            total_friction_cost=(
                total_friction_cost
            ),
            projected_stop_loss=values[
                "projected_stop_loss"
            ],
            all_in_adverse_loss=(
                all_in_adverse_loss
            ),
            spread_to_stop_distance_ratio=(
                spread_to_stop_distance_ratio
            ),
            slippage_to_stop_distance_ratio=(
                slippage_to_stop_distance_ratio
            ),
            total_friction_to_stop_risk_ratio=(
                total_friction_to_stop_risk_ratio
            ),
            all_in_loss_to_budget_ratio=(
                all_in_loss_to_budget_ratio
            ),
            projected_stop_loss_percent_of_risk_base=(
                self._percentage(
                    values[
                        "projected_stop_loss"
                    ],
                    risk_base,
                )
            ),
            total_friction_percent_of_risk_base=(
                self._percentage(
                    total_friction_cost,
                    risk_base,
                )
            ),
            all_in_loss_percent_of_risk_base=(
                self._percentage(
                    all_in_adverse_loss,
                    risk_base,
                )
            ),
        )


execution_friction_model = (
    ExecutionFrictionModel()
)