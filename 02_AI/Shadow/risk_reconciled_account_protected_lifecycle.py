"""
===============================================================================
Module      : risk_reconciled_account_protected_lifecycle.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Protected + Risk-Reconciled Shadow Lifecycle Coordinator
===============================================================================

Status
------
SHADOW / RESEARCH / DEMO ONLY.

Flow
----
    AccountProtectionGuard
        -> ExecutionAwareCompoundingAdmissionEngine
            -> ExecutionFrictionModel
            -> CompoundingAccountStateAdapter
        -> RiskModeBasketReconciliationEngine
        -> ExecutionAwareLifecycleGate
            -> CompoundingLifecycleAccounting

Purpose
-------
Provide the final SHADOW new-exposure coordination boundary between:

1. account protection,
2. execution/friction/account admission,
3. upstream risk-mode versus basket-policy reconciliation,
4. lifecycle accounting.

Safety invariants
-----------------
1. Account-protection rejection never reaches reconciliation or lifecycle.
2. Execution/account/friction rejection never reaches reconciliation or
   lifecycle.
3. Risk-mode/basket reconciliation rejection never reaches lifecycle.
4. Protection watermark observations remain returned even when later stages
   reject.
5. Lifecycle state changes only through ExecutionAwareLifecycleGate.
6. This coordinator never books spread, slippage, commission, margin, or P&L.
7. Existing-position management is outside this NEW-exposure coordinator.
8. live_authorized is always False.

Important boundary
------------------
This coordinator is for:

    START_NEW_EXPOSURE
    ADD_NEW_EXPOSURE

It must not block independent management or exit handling of already-existing
positions.

This module does NOT:
- connect to MT5
- send orders
- open/close positions
- modify SL/TP
- modify production trade_ready
- modify production RiskEngine
- authorize live execution
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any


protected_module: Any = importlib.import_module(
    "02_AI.Shadow.account_protected_compounding_admission"
)

reconciliation_module: Any = importlib.import_module(
    "02_AI.Shadow.risk_mode_basket_reconciliation"
)

lifecycle_gate_module: Any = importlib.import_module(
    "02_AI.Shadow.execution_aware_lifecycle_gate"
)


AccountProtectedCompoundingAdmissionEngine: Any = (
    protected_module.AccountProtectedCompoundingAdmissionEngine
)

RiskModeBasketReconciliationEngine: Any = (
    reconciliation_module.RiskModeBasketReconciliationEngine
)

ExecutionAwareLifecycleGate: Any = (
    lifecycle_gate_module.ExecutionAwareLifecycleGate
)


@dataclass(
    frozen=True,
)
class RiskReconciledAccountProtectedLifecycleTransition:
    valid: bool

    exposure_applied: bool

    reason: str

    action: str

    protected_admission_reason: str

    reconciliation_reason: str

    lifecycle_reason: str

    mode: str

    version: str

    live_authorized: bool

    protected_admission_invoked: bool

    downstream_admission_invoked: bool

    reconciliation_invoked: bool

    lifecycle_gate_invoked: bool

    lifecycle_invoked: bool

    protection_state_before: Any

    protection_state_after: Any

    lifecycle_state_before: Any

    lifecycle_state_after: Any

    protected_admission_result: Any

    reconciliation_result: Any

    lifecycle_gate_result: Any


class RiskReconciledAccountProtectedLifecycleCoordinator:
    VERSION = "1.0"

    MODE = (
        "SHADOW_RISK_RECONCILED_ACCOUNT_PROTECTED_LIFECYCLE_ONLY"
    )

    _REQUIRED_PROTECTED_FIELDS = (
        "valid",
        "admitted",
        "reason",
        "live_authorized",
        "downstream_invoked",
        "protection_state_after",
        "admission_result",
    )

    _REQUIRED_RECONCILIATION_FIELDS = (
        "valid",
        "reconciled",
        "reason",
        "live_authorized",
    )

    _REQUIRED_LIFECYCLE_FIELDS = (
        "valid",
        "reason",
        "action",
        "live_authorized",
        "lifecycle_invoked",
        "state_after",
    )

    def __init__(
        self,
        *,
        protected_admission_engine: Any | None = None,
        reconciliation_engine: Any | None = None,
        lifecycle_gate: Any | None = None,
    ) -> None:

        self.protected_admission_engine = (
            protected_admission_engine
            if protected_admission_engine is not None
            else AccountProtectedCompoundingAdmissionEngine()
        )

        self.reconciliation_engine = (
            reconciliation_engine
            if reconciliation_engine is not None
            else RiskModeBasketReconciliationEngine()
        )

        self.lifecycle_gate = (
            lifecycle_gate
            if lifecycle_gate is not None
            else ExecutionAwareLifecycleGate()
        )

    # =========================================================================
    # Helpers
    # =========================================================================

    @staticmethod
    def _has_fields(
        value: Any,
        fields: tuple[
            str,
            ...,
        ],
    ) -> bool:

        if value is None:

            return False

        return all(
            hasattr(
                value,
                field,
            )
            for field
            in fields
        )

    def _transition(
        self,
        *,
        valid: bool,
        exposure_applied: bool,
        reason: str,
        action: str,
        protected_admission_reason: str,
        reconciliation_reason: str,
        lifecycle_reason: str,
        protected_admission_invoked: bool,
        downstream_admission_invoked: bool,
        reconciliation_invoked: bool,
        lifecycle_gate_invoked: bool,
        lifecycle_invoked: bool,
        protection_state_before: Any,
        protection_state_after: Any,
        lifecycle_state_before: Any,
        lifecycle_state_after: Any,
        protected_admission_result: Any = None,
        reconciliation_result: Any = None,
        lifecycle_gate_result: Any = None,
    ) -> RiskReconciledAccountProtectedLifecycleTransition:

        return RiskReconciledAccountProtectedLifecycleTransition(
            valid=valid,
            exposure_applied=exposure_applied,
            reason=reason,
            action=action,
            protected_admission_reason=protected_admission_reason,
            reconciliation_reason=reconciliation_reason,
            lifecycle_reason=lifecycle_reason,
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            protected_admission_invoked=protected_admission_invoked,
            downstream_admission_invoked=downstream_admission_invoked,
            reconciliation_invoked=reconciliation_invoked,
            lifecycle_gate_invoked=lifecycle_gate_invoked,
            lifecycle_invoked=lifecycle_invoked,
            protection_state_before=protection_state_before,
            protection_state_after=protection_state_after,
            lifecycle_state_before=lifecycle_state_before,
            lifecycle_state_after=lifecycle_state_after,
            protected_admission_result=protected_admission_result,
            reconciliation_result=reconciliation_result,
            lifecycle_gate_result=lifecycle_gate_result,
        )

    # =========================================================================
    # Protected admission
    # =========================================================================

    def _protected_admission(
        self,
        *,
        protection_state: Any,
        current_bar: int,
        risk_plan: Any,
        leg_id: str,
        account_margin_used: float,
        estimated_slippage_price: float,
        estimated_slippage_cost: float,
        estimated_commission_cost: float,
        existing_legs: int,
        existing_direction: str,
        existing_volume: float,
        existing_projected_loss: float,
        existing_basket_margin: float,
        existing_spread_cost: float,
        existing_floating_profit: float,
        first_leg_initial_risk: float,
    ) -> Any:

        return self.protected_admission_engine.admit(
            protection_state=protection_state,
            current_bar=current_bar,
            risk_plan=risk_plan,
            leg_id=leg_id,
            account_margin_used=account_margin_used,
            estimated_slippage_price=estimated_slippage_price,
            estimated_slippage_cost=estimated_slippage_cost,
            estimated_commission_cost=estimated_commission_cost,
            existing_legs=existing_legs,
            existing_direction=existing_direction,
            existing_volume=existing_volume,
            existing_projected_loss=existing_projected_loss,
            existing_basket_margin=existing_basket_margin,
            existing_spread_cost=existing_spread_cost,
            existing_floating_profit=existing_floating_profit,
            first_leg_initial_risk=first_leg_initial_risk,
        )

    # =========================================================================
    # Protected-result validation
    # =========================================================================

    def _validate_protected_result(
        self,
        *,
        protection_state: Any,
        lifecycle_state: Any,
        protected_result: Any,
    ) -> RiskReconciledAccountProtectedLifecycleTransition | None:

        if not self._has_fields(
            protected_result,
            self._REQUIRED_PROTECTED_FIELDS,
        ):

            return self._transition(
                valid=False,
                exposure_applied=False,
                reason="INVALID_PROTECTED_ADMISSION_RESULT",
                action="NO_ACTION",
                protected_admission_reason="",
                reconciliation_reason="",
                lifecycle_reason="",
                protected_admission_invoked=True,
                downstream_admission_invoked=False,
                reconciliation_invoked=False,
                lifecycle_gate_invoked=False,
                lifecycle_invoked=False,
                protection_state_before=protection_state,
                protection_state_after=protection_state,
                lifecycle_state_before=lifecycle_state,
                lifecycle_state_after=lifecycle_state,
                protected_admission_result=protected_result,
            )

        protected_reason = str(
            protected_result.reason
        )

        protection_after = (
            protected_result.protection_state_after
        )

        downstream_invoked = bool(
            protected_result.downstream_invoked
        )

        if bool(
            protected_result.live_authorized
        ):

            return self._transition(
                valid=False,
                exposure_applied=False,
                reason="PROTECTED_LIVE_AUTHORIZATION_NOT_ALLOWED",
                action="NO_ACTION",
                protected_admission_reason=protected_reason,
                reconciliation_reason="",
                lifecycle_reason="",
                protected_admission_invoked=True,
                downstream_admission_invoked=downstream_invoked,
                reconciliation_invoked=False,
                lifecycle_gate_invoked=False,
                lifecycle_invoked=False,
                protection_state_before=protection_state,
                protection_state_after=protection_after,
                lifecycle_state_before=lifecycle_state,
                lifecycle_state_after=lifecycle_state,
                protected_admission_result=protected_result,
            )

        if (
            not bool(
                protected_result.valid
            )
            or
            not bool(
                protected_result.admitted
            )
        ):

            return self._transition(
                valid=False,
                exposure_applied=False,
                reason="PROTECTED_ADMISSION_REJECTED",
                action="NO_ACTION",
                protected_admission_reason=protected_reason,
                reconciliation_reason="",
                lifecycle_reason="",
                protected_admission_invoked=True,
                downstream_admission_invoked=downstream_invoked,
                reconciliation_invoked=False,
                lifecycle_gate_invoked=False,
                lifecycle_invoked=False,
                protection_state_before=protection_state,
                protection_state_after=protection_after,
                lifecycle_state_before=lifecycle_state,
                lifecycle_state_after=lifecycle_state,
                protected_admission_result=protected_result,
            )

        if protected_result.admission_result is None:

            return self._transition(
                valid=False,
                exposure_applied=False,
                reason="MISSING_EXECUTION_ADMISSION_RESULT",
                action="NO_ACTION",
                protected_admission_reason=protected_reason,
                reconciliation_reason="",
                lifecycle_reason="",
                protected_admission_invoked=True,
                downstream_admission_invoked=downstream_invoked,
                reconciliation_invoked=False,
                lifecycle_gate_invoked=False,
                lifecycle_invoked=False,
                protection_state_before=protection_state,
                protection_state_after=protection_after,
                lifecycle_state_before=lifecycle_state,
                lifecycle_state_after=lifecycle_state,
                protected_admission_result=protected_result,
            )

        return None

    # =========================================================================
    # Reconciliation
    # =========================================================================

    def _reconcile(
        self,
        *,
        protection_state: Any,
        lifecycle_state: Any,
        protected_result: Any,
    ) -> tuple[
        Any,
        RiskReconciledAccountProtectedLifecycleTransition | None,
    ]:

        reconciliation = (
            self.reconciliation_engine.evaluate(
                admission_result=(
                    protected_result.admission_result
                )
            )
        )

        protected_reason = str(
            protected_result.reason
        )

        protection_after = (
            protected_result.protection_state_after
        )

        downstream_invoked = bool(
            protected_result.downstream_invoked
        )

        if not self._has_fields(
            reconciliation,
            self._REQUIRED_RECONCILIATION_FIELDS,
        ):

            return (
                reconciliation,
                self._transition(
                    valid=False,
                    exposure_applied=False,
                    reason="INVALID_RECONCILIATION_RESULT",
                    action="NO_ACTION",
                    protected_admission_reason=protected_reason,
                    reconciliation_reason="",
                    lifecycle_reason="",
                    protected_admission_invoked=True,
                    downstream_admission_invoked=downstream_invoked,
                    reconciliation_invoked=True,
                    lifecycle_gate_invoked=False,
                    lifecycle_invoked=False,
                    protection_state_before=protection_state,
                    protection_state_after=protection_after,
                    lifecycle_state_before=lifecycle_state,
                    lifecycle_state_after=lifecycle_state,
                    protected_admission_result=protected_result,
                    reconciliation_result=reconciliation,
                ),
            )

        reconciliation_reason = str(
            reconciliation.reason
        )

        if bool(
            reconciliation.live_authorized
        ):

            return (
                reconciliation,
                self._transition(
                    valid=False,
                    exposure_applied=False,
                    reason="RECONCILIATION_LIVE_AUTHORIZATION_NOT_ALLOWED",
                    action="NO_ACTION",
                    protected_admission_reason=protected_reason,
                    reconciliation_reason=reconciliation_reason,
                    lifecycle_reason="",
                    protected_admission_invoked=True,
                    downstream_admission_invoked=downstream_invoked,
                    reconciliation_invoked=True,
                    lifecycle_gate_invoked=False,
                    lifecycle_invoked=False,
                    protection_state_before=protection_state,
                    protection_state_after=protection_after,
                    lifecycle_state_before=lifecycle_state,
                    lifecycle_state_after=lifecycle_state,
                    protected_admission_result=protected_result,
                    reconciliation_result=reconciliation,
                ),
            )

        if (
            not bool(
                reconciliation.valid
            )
            or
            not bool(
                reconciliation.reconciled
            )
        ):

            return (
                reconciliation,
                self._transition(
                    valid=False,
                    exposure_applied=False,
                    reason=(
                        "RISK_MODE_BASKET_RECONCILIATION_REJECTED"
                    ),
                    action="NO_ACTION",
                    protected_admission_reason=protected_reason,
                    reconciliation_reason=reconciliation_reason,
                    lifecycle_reason="",
                    protected_admission_invoked=True,
                    downstream_admission_invoked=downstream_invoked,
                    reconciliation_invoked=True,
                    lifecycle_gate_invoked=False,
                    lifecycle_invoked=False,
                    protection_state_before=protection_state,
                    protection_state_after=protection_after,
                    lifecycle_state_before=lifecycle_state,
                    lifecycle_state_after=lifecycle_state,
                    protected_admission_result=protected_result,
                    reconciliation_result=reconciliation,
                ),
            )

        return (
            reconciliation,
            None,
        )

    # =========================================================================
    # Lifecycle result
    # =========================================================================

    def _from_lifecycle(
        self,
        *,
        protection_state: Any,
        lifecycle_state: Any,
        protected_result: Any,
        reconciliation: Any,
        lifecycle_result: Any,
    ) -> RiskReconciledAccountProtectedLifecycleTransition:

        protected_reason = str(
            protected_result.reason
        )

        reconciliation_reason = str(
            reconciliation.reason
        )

        protection_after = (
            protected_result.protection_state_after
        )

        downstream_invoked = bool(
            protected_result.downstream_invoked
        )

        if not self._has_fields(
            lifecycle_result,
            self._REQUIRED_LIFECYCLE_FIELDS,
        ):

            return self._transition(
                valid=False,
                exposure_applied=False,
                reason="INVALID_LIFECYCLE_GATE_RESULT",
                action="NO_ACTION",
                protected_admission_reason=protected_reason,
                reconciliation_reason=reconciliation_reason,
                lifecycle_reason="",
                protected_admission_invoked=True,
                downstream_admission_invoked=downstream_invoked,
                reconciliation_invoked=True,
                lifecycle_gate_invoked=True,
                lifecycle_invoked=False,
                protection_state_before=protection_state,
                protection_state_after=protection_after,
                lifecycle_state_before=lifecycle_state,
                lifecycle_state_after=lifecycle_state,
                protected_admission_result=protected_result,
                reconciliation_result=reconciliation,
                lifecycle_gate_result=lifecycle_result,
            )

        lifecycle_reason = str(
            lifecycle_result.reason
        )

        lifecycle_action = str(
            lifecycle_result.action
        )

        lifecycle_invoked = bool(
            lifecycle_result.lifecycle_invoked
        )

        if bool(
            lifecycle_result.live_authorized
        ):

            return self._transition(
                valid=False,
                exposure_applied=False,
                reason="LIFECYCLE_LIVE_AUTHORIZATION_NOT_ALLOWED",
                action="NO_ACTION",
                protected_admission_reason=protected_reason,
                reconciliation_reason=reconciliation_reason,
                lifecycle_reason=lifecycle_reason,
                protected_admission_invoked=True,
                downstream_admission_invoked=downstream_invoked,
                reconciliation_invoked=True,
                lifecycle_gate_invoked=True,
                lifecycle_invoked=lifecycle_invoked,
                protection_state_before=protection_state,
                protection_state_after=protection_after,
                lifecycle_state_before=lifecycle_state,
                lifecycle_state_after=lifecycle_state,
                protected_admission_result=protected_result,
                reconciliation_result=reconciliation,
                lifecycle_gate_result=lifecycle_result,
            )

        if not bool(
            lifecycle_result.valid
        ):

            return self._transition(
                valid=False,
                exposure_applied=False,
                reason="LIFECYCLE_GATE_REJECTED",
                action=lifecycle_action,
                protected_admission_reason=protected_reason,
                reconciliation_reason=reconciliation_reason,
                lifecycle_reason=lifecycle_reason,
                protected_admission_invoked=True,
                downstream_admission_invoked=downstream_invoked,
                reconciliation_invoked=True,
                lifecycle_gate_invoked=True,
                lifecycle_invoked=lifecycle_invoked,
                protection_state_before=protection_state,
                protection_state_after=protection_after,
                lifecycle_state_before=lifecycle_state,
                lifecycle_state_after=(
                    lifecycle_result.state_after
                ),
                protected_admission_result=protected_result,
                reconciliation_result=reconciliation,
                lifecycle_gate_result=lifecycle_result,
            )

        return self._transition(
            valid=True,
            exposure_applied=True,
            reason=(
                "OK_RISK_RECONCILED_ACCOUNT_PROTECTED_LIFECYCLE"
            ),
            action=lifecycle_action,
            protected_admission_reason=protected_reason,
            reconciliation_reason=reconciliation_reason,
            lifecycle_reason=lifecycle_reason,
            protected_admission_invoked=True,
            downstream_admission_invoked=downstream_invoked,
            reconciliation_invoked=True,
            lifecycle_gate_invoked=True,
            lifecycle_invoked=lifecycle_invoked,
            protection_state_before=protection_state,
            protection_state_after=protection_after,
            lifecycle_state_before=lifecycle_state,
            lifecycle_state_after=(
                lifecycle_result.state_after
            ),
            protected_admission_result=protected_result,
            reconciliation_result=reconciliation,
            lifecycle_gate_result=lifecycle_result,
        )

    # =========================================================================
    # Start new basket
    # =========================================================================

    def start(
        self,
        *,
        protection_state: Any,
        lifecycle_state: Any,
        current_bar: int,
        risk_plan: Any,
        leg_id: str,
        account_margin_used: float,
        volume_min: float,
        volume_step: float,
        estimated_slippage_price: float = 0.0,
        estimated_slippage_cost: float = 0.0,
        estimated_commission_cost: float = 0.0,
    ) -> RiskReconciledAccountProtectedLifecycleTransition:

        protected_result = self._protected_admission(
            protection_state=protection_state,
            current_bar=current_bar,
            risk_plan=risk_plan,
            leg_id=leg_id,
            account_margin_used=account_margin_used,
            estimated_slippage_price=estimated_slippage_price,
            estimated_slippage_cost=estimated_slippage_cost,
            estimated_commission_cost=estimated_commission_cost,
            existing_legs=0,
            existing_direction="",
            existing_volume=0.0,
            existing_projected_loss=0.0,
            existing_basket_margin=0.0,
            existing_spread_cost=0.0,
            existing_floating_profit=0.0,
            first_leg_initial_risk=0.0,
        )

        blocked = self._validate_protected_result(
            protection_state=protection_state,
            lifecycle_state=lifecycle_state,
            protected_result=protected_result,
        )

        if blocked is not None:

            return blocked

        reconciliation, blocked = self._reconcile(
            protection_state=protection_state,
            lifecycle_state=lifecycle_state,
            protected_result=protected_result,
        )

        if blocked is not None:

            return blocked

        lifecycle_result = (
            self.lifecycle_gate.apply_start_admission(
                state=lifecycle_state,
                admission_result=(
                    protected_result.admission_result
                ),
                volume_min=volume_min,
                volume_step=volume_step,
            )
        )

        return self._from_lifecycle(
            protection_state=protection_state,
            lifecycle_state=lifecycle_state,
            protected_result=protected_result,
            reconciliation=reconciliation,
            lifecycle_result=lifecycle_result,
        )

    # =========================================================================
    # Add new compounding exposure
    # =========================================================================

    def add(
        self,
        *,
        protection_state: Any,
        lifecycle_state: Any,
        current_bar: int,
        risk_plan: Any,
        leg_id: str,
        account_margin_used: float,
        current_market_floating_profit: float,
        volume_min: float,
        volume_step: float,
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
    ) -> RiskReconciledAccountProtectedLifecycleTransition:

        protected_result = self._protected_admission(
            protection_state=protection_state,
            current_bar=current_bar,
            risk_plan=risk_plan,
            leg_id=leg_id,
            account_margin_used=account_margin_used,
            estimated_slippage_price=estimated_slippage_price,
            estimated_slippage_cost=estimated_slippage_cost,
            estimated_commission_cost=estimated_commission_cost,
            existing_legs=existing_legs,
            existing_direction=existing_direction,
            existing_volume=existing_volume,
            existing_projected_loss=existing_projected_loss,
            existing_basket_margin=existing_basket_margin,
            existing_spread_cost=existing_spread_cost,
            existing_floating_profit=existing_floating_profit,
            first_leg_initial_risk=first_leg_initial_risk,
        )

        blocked = self._validate_protected_result(
            protection_state=protection_state,
            lifecycle_state=lifecycle_state,
            protected_result=protected_result,
        )

        if blocked is not None:

            return blocked

        reconciliation, blocked = self._reconcile(
            protection_state=protection_state,
            lifecycle_state=lifecycle_state,
            protected_result=protected_result,
        )

        if blocked is not None:

            return blocked

        lifecycle_result = (
            self.lifecycle_gate.apply_addon_admission(
                state=lifecycle_state,
                admission_result=(
                    protected_result.admission_result
                ),
                current_market_floating_profit=(
                    current_market_floating_profit
                ),
                volume_min=volume_min,
                volume_step=volume_step,

                # Entry/add coordinator must never hijack
                # structure-invalidated exit management.
                structure_invalidated=False,
            )
        )

        return self._from_lifecycle(
            protection_state=protection_state,
            lifecycle_state=lifecycle_state,
            protected_result=protected_result,
            reconciliation=reconciliation,
            lifecycle_result=lifecycle_result,
        )


risk_reconciled_account_protected_lifecycle_coordinator = (
    RiskReconciledAccountProtectedLifecycleCoordinator()
)