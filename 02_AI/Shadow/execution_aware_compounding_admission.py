"""
===============================================================================
Module      : execution_aware_compounding_admission.py
Project     : PulseViper XAU AI
Version     : 1.0.1
Purpose     : Shadow Broker-Risk + Friction + Compounding Admission Bridge
===============================================================================

RESEARCH / SHADOW / DEMO ONLY.

Flow:
    BrokerRiskPlan
        -> ExecutionFrictionModel
        -> BasketLegCandidate
        -> CompoundingAccountStateAdapter

This module never sends orders, authorizes live execution, changes structural
stops, modifies production trade_ready, or modifies production RiskEngine.

Important v1 boundary:
- the incoming leg gets an all-in spread/slippage/commission assessment;
- BasketLegCandidate.spread_cost remains RAW spread cost because existing
  planner/lifecycle state currently uses spread semantics;
- basket-wide slippage/commission state is intentionally NOT introduced here.

v1.0.1
------
Compatibility fix:
BrokerRiskPlan v1.1 does not expose raw `point`. It exposes broker-derived
price/point telemetry instead:

    spread_price
    spread_points
    stop_distance_price
    stop_distance_points

The bridge therefore derives `point` without changing the upstream risk-engine
contract.
"""

from __future__ import annotations

import importlib
import math
from dataclasses import dataclass
from typing import Any


friction_module: Any = importlib.import_module(
    "02_AI.Shadow.execution_friction_model"
)

basket_module: Any = importlib.import_module(
    "02_AI.Shadow.bootstrap_compounding_planner"
)

adapter_module: Any = importlib.import_module(
    "02_AI.Shadow.compounding_account_state_adapter"
)


ExecutionFrictionModel: Any = (
    friction_module.ExecutionFrictionModel
)

BasketLegCandidate: Any = (
    basket_module.BasketLegCandidate
)

CompoundingAccountStateAdapter: Any = (
    adapter_module.CompoundingAccountStateAdapter
)


@dataclass(
    frozen=True,
)
class ExecutionAwareCompoundingAdmission:
    valid: bool

    admitted: bool

    reason: str

    mode: str

    version: str

    live_authorized: bool

    leg_id: str

    direction: str

    risk_mode: str

    risk_reason: str

    friction_reason: str

    account_reason: str

    risk_plan: Any

    friction_assessment: Any

    candidate: Any

    account_plan: Any


class ExecutionAwareCompoundingAdmissionEngine:
    VERSION = "1.0.1"

    MODE = (
        "SHADOW_EXECUTION_AWARE_COMPOUNDING_ADMISSION_ONLY"
    )

    REQUIRED_RISK_PLAN_FIELDS = (
        "valid",
        "reason",
        "risk_mode",
        "direction",
        "balance",
        "equity",
        "free_margin",
        "hard_max_risk_amount",
        "entry_price",
        "stop_loss",
        "spread_price",
        "spread_points",
        "spread_cost",
        "selected_volume",
        "estimated_stop_loss_amount",
        "margin_required",
        "stop_distance_price",
        "stop_distance_points",
        "volume_min",
        "volume_step",
    )

    _EPSILON = 1e-12

    def __init__(
        self,
        *,
        friction_model: Any | None = None,
        adapter: Any | None = None,
    ) -> None:

        self.friction_model = (
            friction_model
            if friction_model is not None
            else ExecutionFrictionModel()
        )

        self.adapter = (
            adapter
            if adapter is not None
            else CompoundingAccountStateAdapter()
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

    def _result(
        self,
        *,
        valid: bool,
        admitted: bool,
        reason: str,
        leg_id: str = "",
        direction: str = "",
        risk_mode: str = "",
        risk_reason: str = "",
        friction_reason: str = "",
        account_reason: str = "",
        risk_plan: Any = None,
        friction_assessment: Any = None,
        candidate: Any = None,
        account_plan: Any = None,
    ) -> ExecutionAwareCompoundingAdmission:

        return ExecutionAwareCompoundingAdmission(
            valid=valid,
            admitted=admitted,
            reason=reason,
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            leg_id=leg_id,
            direction=direction,
            risk_mode=risk_mode,
            risk_reason=risk_reason,
            friction_reason=friction_reason,
            account_reason=account_reason,
            risk_plan=risk_plan,
            friction_assessment=friction_assessment,
            candidate=candidate,
            account_plan=account_plan,
        )

    def _has_required_shape(
        self,
        risk_plan: Any,
    ) -> bool:

        if risk_plan is None:

            return False

        return all(
            hasattr(
                risk_plan,
                field,
            )
            for field
            in self.REQUIRED_RISK_PLAN_FIELDS
        )

    def _resolve_point(
        self,
        risk_plan: Any,
    ) -> float:

        spread_price = self._number(
            risk_plan.spread_price
        )

        spread_points = self._number(
            risk_plan.spread_points
        )

        if (
            math.isfinite(
                spread_price
            )
            and
            math.isfinite(
                spread_points
            )
            and
            spread_price > 0.0
            and
            spread_points > self._EPSILON
        ):

            point = (
                spread_price
                /
                spread_points
            )

            if (
                math.isfinite(
                    point
                )
                and
                point > 0.0
            ):

                return point

        stop_distance_price = self._number(
            risk_plan.stop_distance_price
        )

        stop_distance_points = self._number(
            risk_plan.stop_distance_points
        )

        if (
            math.isfinite(
                stop_distance_price
            )
            and
            math.isfinite(
                stop_distance_points
            )
            and
            stop_distance_price > 0.0
            and
            stop_distance_points > self._EPSILON
        ):

            point = (
                stop_distance_price
                /
                stop_distance_points
            )

            if (
                math.isfinite(
                    point
                )
                and
                point > 0.0
            ):

                return point

        return math.nan

    def admit(
        self,
        *,
        risk_plan: Any,
        leg_id: str,
        account_margin_used: float,
        estimated_slippage_price: float = 0.0,
        estimated_slippage_cost: float = 0.0,
        estimated_commission_cost: float = 0.0,
        existing_legs: int = 0,
        existing_direction: str = "",
        existing_volume: float = 0.0,
        existing_projected_loss: float = 0.0,
        existing_basket_margin: float = 0.0,
        existing_spread_cost: float = 0.0,
        existing_floating_profit: float = 0.0,
        first_leg_initial_risk: float = 0.0,
    ) -> ExecutionAwareCompoundingAdmission:

        resolved_leg_id = str(
            leg_id
        ).strip()

        if not resolved_leg_id:

            return self._result(
                valid=False,
                admitted=False,
                reason="INVALID_LEG_ID",
                risk_plan=risk_plan,
            )

        if not self._has_required_shape(
            risk_plan
        ):

            return self._result(
                valid=False,
                admitted=False,
                reason="INVALID_BROKER_RISK_PLAN_SHAPE",
                leg_id=resolved_leg_id,
                risk_plan=risk_plan,
            )

        direction = str(
            risk_plan.direction
        )

        risk_mode = str(
            risk_plan.risk_mode
        )

        risk_reason = str(
            risk_plan.reason
        )

        if not bool(
            risk_plan.valid
        ):

            return self._result(
                valid=False,
                admitted=False,
                reason="BROKER_RISK_PLAN_REJECTED",
                leg_id=resolved_leg_id,
                direction=direction,
                risk_mode=risk_mode,
                risk_reason=risk_reason,
                risk_plan=risk_plan,
            )

        resolved_point = self._resolve_point(
            risk_plan
        )

        if (
            not math.isfinite(
                resolved_point
            )
            or
            resolved_point <= 0.0
        ):

            return self._result(
                valid=False,
                admitted=False,
                reason="BROKER_POINT_RESOLUTION_FAILED",
                leg_id=resolved_leg_id,
                direction=direction,
                risk_mode=risk_mode,
                risk_reason=risk_reason,
                risk_plan=risk_plan,
            )

        friction = (
            self.friction_model.evaluate(
                direction=direction,
                volume=(
                    risk_plan.selected_volume
                ),
                balance=(
                    risk_plan.balance
                ),
                equity=(
                    risk_plan.equity
                ),
                hard_loss_budget=(
                    risk_plan.hard_max_risk_amount
                ),
                entry_price=(
                    risk_plan.entry_price
                ),
                stop_loss=(
                    risk_plan.stop_loss
                ),
                point=resolved_point,
                spread_price=(
                    risk_plan.spread_price
                ),
                spread_cost=(
                    risk_plan.spread_cost
                ),
                projected_stop_loss=(
                    risk_plan.estimated_stop_loss_amount
                ),
                estimated_slippage_price=(
                    estimated_slippage_price
                ),
                estimated_slippage_cost=(
                    estimated_slippage_cost
                ),
                estimated_commission_cost=(
                    estimated_commission_cost
                ),
            )
        )

        friction_reason = str(
            friction.reason
        )

        if not bool(
            friction.valid
        ):

            return self._result(
                valid=False,
                admitted=False,
                reason="FRICTION_ASSESSMENT_INVALID",
                leg_id=resolved_leg_id,
                direction=direction,
                risk_mode=risk_mode,
                risk_reason=risk_reason,
                friction_reason=friction_reason,
                risk_plan=risk_plan,
                friction_assessment=friction,
            )

        if not bool(
            friction.execution_feasible
        ):

            return self._result(
                valid=False,
                admitted=False,
                reason="EXECUTION_FRICTION_BLOCKED",
                leg_id=resolved_leg_id,
                direction=direction,
                risk_mode=risk_mode,
                risk_reason=risk_reason,
                friction_reason=friction_reason,
                risk_plan=risk_plan,
                friction_assessment=friction,
            )

        candidate = (
            BasketLegCandidate(
                leg_id=resolved_leg_id,
                direction=direction,
                volume=float(
                    risk_plan.selected_volume
                ),
                projected_stop_loss=float(
                    risk_plan.estimated_stop_loss_amount
                ),
                margin_required=float(
                    risk_plan.margin_required
                ),

                # Preserve current planner/lifecycle semantics.
                # This remains RAW spread only.
                spread_cost=float(
                    risk_plan.spread_cost
                ),

                structural_stop_distance=float(
                    risk_plan.stop_distance_price
                ),
            )
        )

        account_plan = (
            self.adapter.plan_addition(
                account_balance=(
                    risk_plan.balance
                ),
                account_equity=(
                    risk_plan.equity
                ),
                account_free_margin=(
                    risk_plan.free_margin
                ),
                account_margin_used=(
                    account_margin_used
                ),
                candidates=[
                    candidate
                ],
                volume_min=(
                    risk_plan.volume_min
                ),
                volume_step=(
                    risk_plan.volume_step
                ),
                existing_legs=existing_legs,
                existing_direction=(
                    existing_direction
                ),
                existing_volume=(
                    existing_volume
                ),
                existing_projected_loss=(
                    existing_projected_loss
                ),
                existing_basket_margin=(
                    existing_basket_margin
                ),
                existing_spread_cost=(
                    existing_spread_cost
                ),
                existing_floating_profit=(
                    existing_floating_profit
                ),
                first_leg_initial_risk=(
                    first_leg_initial_risk
                ),
            )
        )

        account_reason = str(
            account_plan.reason
        )

        if not bool(
            account_plan.valid
        ):

            return self._result(
                valid=False,
                admitted=False,
                reason=(
                    "ACCOUNT_COMPOUNDING_ADMISSION_REJECTED"
                ),
                leg_id=resolved_leg_id,
                direction=direction,
                risk_mode=risk_mode,
                risk_reason=risk_reason,
                friction_reason=friction_reason,
                account_reason=account_reason,
                risk_plan=risk_plan,
                friction_assessment=friction,
                candidate=candidate,
                account_plan=account_plan,
            )

        if (
            resolved_leg_id
            not in
            set(
                account_plan.accepted_leg_ids
            )
        ):

            return self._result(
                valid=False,
                admitted=False,
                reason="ACCOUNT_ADMISSION_DID_NOT_ACCEPT_LEG",
                leg_id=resolved_leg_id,
                direction=direction,
                risk_mode=risk_mode,
                risk_reason=risk_reason,
                friction_reason=friction_reason,
                account_reason=account_reason,
                risk_plan=risk_plan,
                friction_assessment=friction,
                candidate=candidate,
                account_plan=account_plan,
            )

        return self._result(
            valid=True,
            admitted=True,
            reason="OK_EXECUTION_AWARE_COMPOUNDING_ADMISSION",
            leg_id=resolved_leg_id,
            direction=direction,
            risk_mode=risk_mode,
            risk_reason=risk_reason,
            friction_reason=friction_reason,
            account_reason=account_reason,
            risk_plan=risk_plan,
            friction_assessment=friction,
            candidate=candidate,
            account_plan=account_plan,
        )


execution_aware_compounding_admission_engine = (
    ExecutionAwareCompoundingAdmissionEngine()
)