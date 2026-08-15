"""
===============================================================================
Module      : realized_fill_telemetry_bridge.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Shadow Actual-Fill Telemetry -> Realized Cost Observation Bridge
===============================================================================

Status
------
SHADOW / RESEARCH / DEMO ONLY.

Purpose
-------
Normalize broker-agnostic actual-fill telemetry, derive realized spread and
signed slippage cost, and forward those observations to the existing
RealizedExecutionCostLifecycleObserver.

Critical accounting boundary
----------------------------
The lifecycle remains authoritative for RAW spread P&L booking. This bridge:
- never connects to MT5 or sends orders,
- never opens/closes/modifies positions,
- never changes SL/TP or structural stop geometry,
- never books spread/slippage/commission into lifecycle P&L,
- never mutates lifecycle state or candidate.spread_cost,
- never modifies trade_ready or production RiskEngine,
- never authorizes live execution.

Successful observations always preserve lifecycle_pnl_delta == 0.0.

Telemetry semantics
-------------------
filled_volume
    Must exactly match the lifecycle-admitted candidate volume. Partial fills
    fail closed in v1; a future broker adapter may aggregate multiple deals
    into one normalized fill before this boundary.

quote_bid / quote_ask
    Optional, but must be supplied together. If present, realized spread is
    derived from the quote. If fill_price is also present, signed slippage is
    derived versus the executable quote side.

commission_cost
    Optional normalized non-negative cost. Broker-specific signed commission
    fields must be normalized by a broker adapter before reaching this module.

Slippage sign
-------------
LONG : fill_price - quote_ask
SHORT: quote_bid - fill_price

Positive = adverse execution.
Negative = favorable execution / price improvement.
"""

from __future__ import annotations

import importlib
import math
from dataclasses import dataclass
from typing import Any


observer_module: Any = importlib.import_module(
    "02_AI.Shadow.realized_execution_cost_lifecycle_observer"
)

RealizedExecutionCostLifecycleObserver: Any = (
    observer_module.RealizedExecutionCostLifecycleObserver
)


@dataclass(frozen=True)
class NormalizedActualFillTelemetry:
    execution_id: str
    filled_volume: float
    fill_price: float | None = None
    quote_bid: float | None = None
    quote_ask: float | None = None
    commission_cost: float | None = None
    live_authorized: bool = False


@dataclass(frozen=True)
class RealizedFillTelemetryObservation:
    valid: bool
    observed: bool
    reason: str
    observer_reason: str
    cost_reason: str
    action: str
    mode: str
    version: str
    live_authorized: bool
    observer_invoked: bool

    execution_id: str
    direction: str
    expected_volume: float
    filled_volume: float

    fill_price_available: bool
    fill_price: float | None

    quote_available: bool
    quote_bid: float | None
    quote_ask: float | None

    realized_spread_price: float | None

    point_available: bool
    point: float | None
    realized_spread_points: float | None

    realized_slippage_price_available: bool
    realized_slippage_price: float | None
    realized_slippage_points: float | None

    monetary_cost_per_price_unit: float

    monetary_scale_cross_checks: tuple[
        tuple[
            str,
            float,
        ],
        ...,
    ]

    realized_spread_available: bool
    realized_spread_cost: float | None

    realized_slippage_available: bool
    realized_slippage_cost: float | None

    realized_commission_available: bool
    realized_commission_cost: float | None

    lifecycle_pnl_delta: float

    lifecycle_transition: Any
    telemetry: Any

    cost_state_before: Any
    cost_state_after: Any

    observer_result: Any


class RealizedFillTelemetryBridge:
    VERSION = "1.0"

    MODE = (
        "SHADOW_REALIZED_FILL_TELEMETRY_BRIDGE_ONLY"
    )

    _EPSILON = 1e-8
    _REL_TOLERANCE = 1e-6

    _REQUIRED_LIFECYCLE_FIELDS = (
        "valid",
        "exposure_applied",
        "live_authorized",
        "lifecycle_invoked",
        "protected_admission_result",
    )

    _REQUIRED_PROTECTED_FIELDS = (
        "live_authorized",
        "admission_result",
    )

    _REQUIRED_ADMISSION_FIELDS = (
        "valid",
        "admitted",
        "live_authorized",
        "risk_plan",
        "friction_assessment",
        "candidate",
    )

    _REQUIRED_RISK_FIELDS = (
        "valid",
        "live_authorized",
        "direction",
        "selected_volume",
        "entry_price",
        "stop_distance_price",
        "stop_distance_points",
        "estimated_stop_loss_amount",
        "spread_price",
        "spread_points",
        "spread_cost",
    )

    _REQUIRED_FRICTION_FIELDS = (
        "valid",
        "execution_feasible",
        "live_authorized",
        "direction",
        "volume",
        "entry_price",
        "stop_distance_price",
        "projected_stop_loss",
        "spread_price",
        "spread_cost",
    )

    _REQUIRED_CANDIDATE_FIELDS = (
        "direction",
        "volume",
        "projected_stop_loss",
        "spread_cost",
        "structural_stop_distance",
    )

    _REQUIRED_TELEMETRY_FIELDS = (
        "execution_id",
        "filled_volume",
        "fill_price",
        "quote_bid",
        "quote_ask",
        "commission_cost",
        "live_authorized",
    )

    _REQUIRED_OBSERVER_FIELDS = (
        "valid",
        "observed",
        "reason",
        "cost_reason",
        "live_authorized",
        "lifecycle_pnl_delta",
        "cost_state_after",
    )

    def __init__(
        self,
        *,
        observer: Any | None = None,
    ) -> None:

        self.observer = (
            observer
            if observer is not None
            else RealizedExecutionCostLifecycleObserver()
        )

    # =========================================================================
    # State
    # =========================================================================

    def initial_cost_state(
        self,
    ) -> Any:

        return self.observer.accounting.initial_state()

    # =========================================================================
    # Generic helpers
    # =========================================================================

    @staticmethod
    def _has_fields(
        value: Any,
        fields: tuple[
            str,
            ...,
        ],
    ) -> bool:

        return (
            value is not None
            and
            all(
                hasattr(
                    value,
                    field,
                )
                for field
                in fields
            )
        )

    @staticmethod
    def _number(
        value: float | int | None,
    ) -> float:

        try:

            resolved = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return math.nan

        if not math.isfinite(
            resolved
        ):

            return math.nan

        return resolved

    @staticmethod
    def _direction(
        value: str,
    ) -> str:

        resolved = str(
            value
        ).strip().upper()

        if resolved in {
            "LONG",
            "BUY",
            "BULLISH",
        }:

            return "LONG"

        if resolved in {
            "SHORT",
            "SELL",
            "BEARISH",
        }:

            return "SHORT"

        return "INVALID"

    @classmethod
    def _close(
        cls,
        left: float,
        right: float,
    ) -> bool:

        return math.isclose(
            left,
            right,
            rel_tol=cls._REL_TOLERANCE,
            abs_tol=cls._EPSILON,
        )

    # =========================================================================
    # Result helpers
    # =========================================================================

    def _build(
        self,
        *,
        valid: bool,
        observed: bool,
        reason: str,
        lifecycle_transition: Any,
        telemetry: Any,
        cost_state_before: Any,
        cost_state_after: Any,
        observer_result: Any = None,
        observer_invoked: bool = False,
        observer_reason: str = "",
        cost_reason: str = "",
        ctx: dict[str, Any] | None = None,
    ) -> RealizedFillTelemetryObservation:

        values = (
            {}
            if ctx is None
            else dict(
                ctx
            )
        )

        def rounded(
            name: str,
            digits: int = 8,
        ) -> float | None:

            value = values.get(
                name
            )

            if value is None:

                return None

            return round(
                float(
                    value
                ),
                digits,
            )

        checks = tuple(
            (
                str(
                    name
                ),
                round(
                    float(
                        value
                    ),
                    8,
                ),
            )
            for (
                name,
                value,
            )
            in values.get(
                "monetary_scale_cross_checks",
                (),
            )
        )

        return RealizedFillTelemetryObservation(
            valid=valid,
            observed=observed,
            reason=reason,
            observer_reason=observer_reason,
            cost_reason=cost_reason,
            action=(
                "OBSERVE_NORMALIZED_ACTUAL_FILL"
                if observed
                else
                "NO_ACTION"
            ),
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            observer_invoked=observer_invoked,
            execution_id=str(
                values.get(
                    "execution_id",
                    "",
                )
            ),
            direction=str(
                values.get(
                    "direction",
                    "",
                )
            ),
            expected_volume=round(
                float(
                    values.get(
                        "expected_volume",
                        0.0,
                    )
                ),
                8,
            ),
            filled_volume=round(
                float(
                    values.get(
                        "filled_volume",
                        0.0,
                    )
                ),
                8,
            ),
            fill_price_available=bool(
                values.get(
                    "fill_price_available",
                    False,
                )
            ),
            fill_price=rounded(
                "fill_price"
            ),
            quote_available=bool(
                values.get(
                    "quote_available",
                    False,
                )
            ),
            quote_bid=rounded(
                "quote_bid"
            ),
            quote_ask=rounded(
                "quote_ask"
            ),
            realized_spread_price=rounded(
                "realized_spread_price"
            ),
            point_available=bool(
                values.get(
                    "point_available",
                    False,
                )
            ),
            point=rounded(
                "point",
                12,
            ),
            realized_spread_points=rounded(
                "realized_spread_points"
            ),
            realized_slippage_price_available=bool(
                values.get(
                    "realized_slippage_price_available",
                    False,
                )
            ),
            realized_slippage_price=rounded(
                "realized_slippage_price"
            ),
            realized_slippage_points=rounded(
                "realized_slippage_points"
            ),
            monetary_cost_per_price_unit=round(
                float(
                    values.get(
                        "monetary_cost_per_price_unit",
                        0.0,
                    )
                ),
                8,
            ),
            monetary_scale_cross_checks=checks,
            realized_spread_available=bool(
                values.get(
                    "realized_spread_available",
                    False,
                )
            ),
            realized_spread_cost=rounded(
                "realized_spread_cost"
            ),
            realized_slippage_available=bool(
                values.get(
                    "realized_slippage_available",
                    False,
                )
            ),
            realized_slippage_cost=rounded(
                "realized_slippage_cost"
            ),
            realized_commission_available=bool(
                values.get(
                    "realized_commission_available",
                    False,
                )
            ),
            realized_commission_cost=rounded(
                "realized_commission_cost"
            ),
            lifecycle_pnl_delta=0.0,
            lifecycle_transition=lifecycle_transition,
            telemetry=telemetry,
            cost_state_before=cost_state_before,
            cost_state_after=cost_state_after,
            observer_result=observer_result,
        )

    def _invalid(
        self,
        *,
        reason: str,
        lifecycle_transition: Any,
        telemetry: Any,
        cost_state: Any,
        ctx: dict[str, Any] | None = None,
        observer_result: Any = None,
        observer_invoked: bool = False,
        observer_reason: str = "",
        cost_reason: str = "",
    ) -> RealizedFillTelemetryObservation:

        return self._build(
            valid=False,
            observed=False,
            reason=reason,
            lifecycle_transition=lifecycle_transition,
            telemetry=telemetry,
            cost_state_before=cost_state,
            cost_state_after=cost_state,
            observer_result=observer_result,
            observer_invoked=observer_invoked,
            observer_reason=observer_reason,
            cost_reason=cost_reason,
            ctx=ctx,
        )

    # =========================================================================
    # Upstream linkage
    # =========================================================================

    def _resolve_upstream(
        self,
        lifecycle_transition: Any,
    ) -> tuple[
        bool,
        str,
        Any,
        Any,
        Any,
    ]:

        if not self._has_fields(
            lifecycle_transition,
            self._REQUIRED_LIFECYCLE_FIELDS,
        ):

            return (
                False,
                "INVALID_LIFECYCLE_TRANSITION_SHAPE",
                None,
                None,
                None,
            )

        if bool(
            lifecycle_transition.live_authorized
        ):

            return (
                False,
                "LIFECYCLE_LIVE_AUTHORIZATION_NOT_ALLOWED",
                None,
                None,
                None,
            )

        if (
            not bool(
                lifecycle_transition.valid
            )
            or
            not bool(
                lifecycle_transition.exposure_applied
            )
        ):

            return (
                False,
                "LIFECYCLE_EXPOSURE_NOT_APPLIED",
                None,
                None,
                None,
            )

        if not bool(
            lifecycle_transition.lifecycle_invoked
        ):

            return (
                False,
                "LIFECYCLE_NOT_INVOKED",
                None,
                None,
                None,
            )

        protected = (
            lifecycle_transition.protected_admission_result
        )

        if not self._has_fields(
            protected,
            self._REQUIRED_PROTECTED_FIELDS,
        ):

            return (
                False,
                "INVALID_PROTECTED_ADMISSION_SHAPE",
                None,
                None,
                None,
            )

        if bool(
            protected.live_authorized
        ):

            return (
                False,
                "PROTECTED_LIVE_AUTHORIZATION_NOT_ALLOWED",
                None,
                None,
                None,
            )

        admission = (
            protected.admission_result
        )

        if not self._has_fields(
            admission,
            self._REQUIRED_ADMISSION_FIELDS,
        ):

            return (
                False,
                "INVALID_EXECUTION_ADMISSION_SHAPE",
                None,
                None,
                None,
            )

        if bool(
            admission.live_authorized
        ):

            return (
                False,
                "ADMISSION_LIVE_AUTHORIZATION_NOT_ALLOWED",
                None,
                None,
                None,
            )

        if (
            not bool(
                admission.valid
            )
            or
            not bool(
                admission.admitted
            )
        ):

            return (
                False,
                "EXECUTION_ADMISSION_REJECTED",
                None,
                None,
                None,
            )

        risk_plan = (
            admission.risk_plan
        )

        friction = (
            admission.friction_assessment
        )

        candidate = (
            admission.candidate
        )

        if not self._has_fields(
            risk_plan,
            self._REQUIRED_RISK_FIELDS,
        ):

            return (
                False,
                "INVALID_BROKER_RISK_PLAN_SHAPE",
                None,
                None,
                None,
            )

        if not self._has_fields(
            friction,
            self._REQUIRED_FRICTION_FIELDS,
        ):

            return (
                False,
                "INVALID_FRICTION_ASSESSMENT_SHAPE",
                None,
                None,
                None,
            )

        if not self._has_fields(
            candidate,
            self._REQUIRED_CANDIDATE_FIELDS,
        ):

            return (
                False,
                "INVALID_CANDIDATE_SHAPE",
                None,
                None,
                None,
            )

        if bool(
            risk_plan.live_authorized
        ):

            return (
                False,
                "RISK_PLAN_LIVE_AUTHORIZATION_NOT_ALLOWED",
                None,
                None,
                None,
            )

        if bool(
            friction.live_authorized
        ):

            return (
                False,
                "FRICTION_LIVE_AUTHORIZATION_NOT_ALLOWED",
                None,
                None,
                None,
            )

        if not bool(
            risk_plan.valid
        ):

            return (
                False,
                "BROKER_RISK_PLAN_REJECTED",
                None,
                None,
                None,
            )

        if (
            not bool(
                friction.valid
            )
            or
            not bool(
                friction.execution_feasible
            )
        ):

            return (
                False,
                "EXECUTION_FRICTION_REJECTED",
                None,
                None,
                None,
            )

        return (
            True,
            "",
            risk_plan,
            friction,
            candidate,
        )

    # =========================================================================
    # Point resolution
    # =========================================================================

    def _resolve_point(
        self,
        risk_plan: Any,
    ) -> tuple[
        bool,
        str,
        float | None,
    ]:

        spread_price = self._number(
            risk_plan.spread_price
        )

        spread_points = self._number(
            risk_plan.spread_points
        )

        stop_price = self._number(
            risk_plan.stop_distance_price
        )

        stop_points = self._number(
            risk_plan.stop_distance_points
        )

        if any(
            not math.isfinite(
                value
            )
            for value
            in (
                spread_price,
                spread_points,
                stop_price,
                stop_points,
            )
        ):

            return (
                False,
                "INVALID_RISK_POINT_METADATA",
                None,
            )

        if (
            spread_price < 0.0
            or
            spread_points < 0.0
        ):

            return (
                False,
                "INVALID_RISK_POINT_METADATA",
                None,
            )

        if (
            stop_price <= 0.0
            or
            stop_points <= 0.0
        ):

            return (
                False,
                "INVALID_RISK_POINT_METADATA",
                None,
            )

        candidates = [
            (
                stop_price
                /
                stop_points
            )
        ]

        if (
            spread_price
            >
            self._EPSILON
        ):

            if (
                spread_points
                <=
                self._EPSILON
            ):

                return (
                    False,
                    "INVALID_RISK_POINT_METADATA",
                    None,
                )

            candidates.append(
                spread_price
                /
                spread_points
            )

        elif (
            spread_points
            >
            self._EPSILON
        ):

            return (
                False,
                "INVALID_RISK_POINT_METADATA",
                None,
            )

        if any(
            (
                not math.isfinite(
                    value
                )
                or
                value <= 0.0
            )
            for value
            in candidates
        ):

            return (
                False,
                "INVALID_RISK_POINT_SCALE",
                None,
            )

        if any(
            not self._close(
                candidates[0],
                value,
            )
            for value
            in candidates[
                1:
            ]
        ):

            return (
                False,
                "RISK_POINT_RESOLUTION_MISMATCH",
                None,
            )

        return (
            True,
            "",
            candidates[0],
        )

    # =========================================================================
    # Monetary scale
    # =========================================================================

    def _resolve_monetary_scale(
        self,
        risk_plan: Any,
        friction: Any,
        candidate: Any,
    ) -> tuple[
        bool,
        str,
        float,
        tuple[
            tuple[
                str,
                float,
            ],
            ...,
        ],
    ]:

        risk_stop = self._number(
            risk_plan.stop_distance_price
        )

        risk_loss = self._number(
            risk_plan.estimated_stop_loss_amount
        )

        if (
            not math.isfinite(
                risk_stop
            )
            or
            not math.isfinite(
                risk_loss
            )
            or
            risk_stop <= 0.0
            or
            risk_loss <= 0.0
        ):

            return (
                False,
                "INVALID_RISK_STOP_MONETARY_SCALE",
                0.0,
                (),
            )

        authoritative = (
            risk_loss
            /
            risk_stop
        )

        if (
            not math.isfinite(
                authoritative
            )
            or
            authoritative <= 0.0
        ):

            return (
                False,
                "INVALID_MONETARY_COST_SCALE",
                0.0,
                (),
            )

        checks: list[
            tuple[
                str,
                float,
            ]
        ] = [
            (
                "RISK_STOP",
                authoritative,
            )
        ]

        def append_scale(
            name: str,
            cost_value: Any,
            distance_value: Any,
            *,
            allow_zero_pair: bool = False,
        ) -> tuple[
            bool,
            str,
        ]:

            cost = self._number(
                cost_value
            )

            distance = self._number(
                distance_value
            )

            if (
                not math.isfinite(
                    cost
                )
                or
                not math.isfinite(
                    distance
                )
            ):

                return (
                    False,
                    f"INVALID_{name}_MONETARY_SCALE",
                )

            if (
                allow_zero_pair
                and
                abs(
                    distance
                )
                <=
                self._EPSILON
            ):

                if (
                    abs(
                        cost
                    )
                    <=
                    self._EPSILON
                ):

                    return (
                        True,
                        "",
                    )

                return (
                    False,
                    f"INVALID_{name}_ZERO_DISTANCE_COST",
                )

            if (
                distance <= 0.0
                or
                cost < 0.0
            ):

                return (
                    False,
                    f"INVALID_{name}_MONETARY_SCALE",
                )

            scale = (
                cost
                /
                distance
            )

            if (
                not math.isfinite(
                    scale
                )
                or
                scale <= 0.0
            ):

                return (
                    False,
                    f"INVALID_{name}_MONETARY_SCALE",
                )

            checks.append(
                (
                    name,
                    scale,
                )
            )

            return (
                True,
                "",
            )

        inputs = (
            (
                "RISK_SPREAD",
                risk_plan.spread_cost,
                risk_plan.spread_price,
                True,
            ),
            (
                "FRICTION_STOP",
                friction.projected_stop_loss,
                friction.stop_distance_price,
                False,
            ),
            (
                "FRICTION_SPREAD",
                friction.spread_cost,
                friction.spread_price,
                True,
            ),
            (
                "CANDIDATE_STOP",
                candidate.projected_stop_loss,
                candidate.structural_stop_distance,
                False,
            ),
        )

        for (
            name,
            cost,
            distance,
            allow_zero,
        ) in inputs:

            ok, reason = append_scale(
                name,
                cost,
                distance,
                allow_zero_pair=allow_zero,
            )

            if not ok:

                return (
                    False,
                    reason,
                    authoritative,
                    tuple(
                        checks
                    ),
                )

        if any(
            not self._close(
                authoritative,
                scale,
            )
            for (
                _,
                scale,
            )
            in checks[
                1:
            ]
        ):

            return (
                False,
                "MONETARY_COST_SCALE_MISMATCH",
                authoritative,
                tuple(
                    checks
                ),
            )

        return (
            True,
            "",
            authoritative,
            tuple(
                checks
            ),
        )

    # =========================================================================
    # Main observer bridge
    # =========================================================================

    def observe_fill(
        self,
        *,
        cost_state: Any,
        lifecycle_transition: Any,
        telemetry: Any,
    ) -> RealizedFillTelemetryObservation:

        ctx: dict[
            str,
            Any,
        ] = {}

        # ---------------------------------------------------------------------
        # Telemetry shape / live safety
        # ---------------------------------------------------------------------

        if not self._has_fields(
            telemetry,
            self._REQUIRED_TELEMETRY_FIELDS,
        ):

            return self._invalid(
                reason="INVALID_FILL_TELEMETRY_SHAPE",
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
            )

        if bool(
            telemetry.live_authorized
        ):

            return self._invalid(
                reason=(
                    "FILL_TELEMETRY_LIVE_AUTHORIZATION_NOT_ALLOWED"
                ),
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
            )

        execution_id = str(
            telemetry.execution_id
        ).strip()

        ctx[
            "execution_id"
        ] = execution_id

        if not execution_id:

            return self._invalid(
                reason="INVALID_EXECUTION_ID",
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
            )

        filled_volume = self._number(
            telemetry.filled_volume
        )

        if (
            not math.isfinite(
                filled_volume
            )
            or
            filled_volume <= 0.0
        ):

            return self._invalid(
                reason="INVALID_FILLED_VOLUME",
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
            )

        ctx[
            "filled_volume"
        ] = filled_volume

        # ---------------------------------------------------------------------
        # Upstream lifecycle/admission linkage
        # ---------------------------------------------------------------------

        (
            upstream_valid,
            upstream_reason,
            risk_plan,
            friction,
            candidate,
        ) = self._resolve_upstream(
            lifecycle_transition
        )

        if not upstream_valid:

            return self._invalid(
                reason=upstream_reason,
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
            )

        direction = self._direction(
            risk_plan.direction
        )

        friction_direction = self._direction(
            friction.direction
        )

        candidate_direction = self._direction(
            candidate.direction
        )

        ctx[
            "direction"
        ] = direction

        if direction == "INVALID":

            return self._invalid(
                reason="INVALID_RISK_DIRECTION",
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
            )

        if (
            friction_direction
            !=
            direction
            or
            candidate_direction
            !=
            direction
        ):

            return self._invalid(
                reason=(
                    "EXECUTION_DIRECTION_LINKAGE_MISMATCH"
                ),
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
            )

        # ---------------------------------------------------------------------
        # Exact volume linkage
        # ---------------------------------------------------------------------

        expected_volume = self._number(
            risk_plan.selected_volume
        )

        friction_volume = self._number(
            friction.volume
        )

        candidate_volume = self._number(
            candidate.volume
        )

        ctx[
            "expected_volume"
        ] = (
            expected_volume
            if math.isfinite(
                expected_volume
            )
            else
            0.0
        )

        if any(
            (
                not math.isfinite(
                    value
                )
                or
                value <= 0.0
            )
            for value
            in (
                expected_volume,
                friction_volume,
                candidate_volume,
            )
        ):

            return self._invalid(
                reason=(
                    "INVALID_EXECUTION_VOLUME_LINKAGE"
                ),
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
            )

        if (
            not self._close(
                expected_volume,
                friction_volume,
            )
            or
            not self._close(
                expected_volume,
                candidate_volume,
            )
        ):

            return self._invalid(
                reason=(
                    "UPSTREAM_EXECUTION_VOLUME_MISMATCH"
                ),
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
            )

        if not self._close(
            filled_volume,
            expected_volume,
        ):

            return self._invalid(
                reason="FILLED_VOLUME_MISMATCH",
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
            )

        # ---------------------------------------------------------------------
        # RAW spread linkage
        # ---------------------------------------------------------------------

        spread_link = tuple(
            self._number(
                value
            )
            for value
            in (
                risk_plan.spread_cost,
                friction.spread_cost,
                candidate.spread_cost,
            )
        )

        if any(
            (
                not math.isfinite(
                    value
                )
                or
                value < 0.0
            )
            for value
            in spread_link
        ):

            return self._invalid(
                reason="INVALID_RAW_SPREAD_LINKAGE",
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
            )

        if (
            not self._close(
                spread_link[0],
                spread_link[1],
            )
            or
            not self._close(
                spread_link[0],
                spread_link[2],
            )
        ):

            return self._invalid(
                reason=(
                    "RISK_PLAN_SPREAD_LINKAGE_MISMATCH"
                ),
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
            )

        # ---------------------------------------------------------------------
        # Spread-price linkage
        # ---------------------------------------------------------------------

        risk_spread_price = self._number(
            risk_plan.spread_price
        )

        friction_spread_price = self._number(
            friction.spread_price
        )

        if (
            not math.isfinite(
                risk_spread_price
            )
            or
            not math.isfinite(
                friction_spread_price
            )
            or
            risk_spread_price < 0.0
            or
            friction_spread_price < 0.0
        ):

            return self._invalid(
                reason="INVALID_SPREAD_PRICE_LINKAGE",
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
            )

        if not self._close(
            risk_spread_price,
            friction_spread_price,
        ):

            return self._invalid(
                reason=(
                    "RISK_FRICTION_SPREAD_PRICE_MISMATCH"
                ),
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
            )

        # ---------------------------------------------------------------------
        # Structural stop linkage
        # ---------------------------------------------------------------------

        stop_distances = tuple(
            self._number(
                value
            )
            for value
            in (
                risk_plan.stop_distance_price,
                friction.stop_distance_price,
                candidate.structural_stop_distance,
            )
        )

        if any(
            (
                not math.isfinite(
                    value
                )
                or
                value <= 0.0
            )
            for value
            in stop_distances
        ):

            return self._invalid(
                reason="INVALID_UPSTREAM_STOP_GEOMETRY",
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
            )

        if any(
            not self._close(
                stop_distances[0],
                value,
            )
            for value
            in stop_distances[
                1:
            ]
        ):

            return self._invalid(
                reason="UPSTREAM_STOP_GEOMETRY_MISMATCH",
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
            )

        stop_risks = tuple(
            self._number(
                value
            )
            for value
            in (
                risk_plan.estimated_stop_loss_amount,
                friction.projected_stop_loss,
                candidate.projected_stop_loss,
            )
        )

        if any(
            (
                not math.isfinite(
                    value
                )
                or
                value <= 0.0
            )
            for value
            in stop_risks
        ):

            return self._invalid(
                reason="INVALID_UPSTREAM_STOP_RISK",
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
            )

        if any(
            not self._close(
                stop_risks[0],
                value,
            )
            for value
            in stop_risks[
                1:
            ]
        ):

            return self._invalid(
                reason="UPSTREAM_STOP_RISK_MISMATCH",
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
            )

        # ---------------------------------------------------------------------
        # Planned entry linkage
        # ---------------------------------------------------------------------

        risk_entry = self._number(
            risk_plan.entry_price
        )

        friction_entry = self._number(
            friction.entry_price
        )

        if (
            not math.isfinite(
                risk_entry
            )
            or
            not math.isfinite(
                friction_entry
            )
            or
            risk_entry <= 0.0
            or
            friction_entry <= 0.0
        ):

            return self._invalid(
                reason="INVALID_EXECUTION_ENTRY_LINKAGE",
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
            )

        if not self._close(
            risk_entry,
            friction_entry,
        ):

            return self._invalid(
                reason="RISK_FRICTION_ENTRY_MISMATCH",
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
            )

        # ---------------------------------------------------------------------
        # Monetary scale / point
        # ---------------------------------------------------------------------

        (
            scale_valid,
            scale_reason,
            monetary_scale,
            scale_checks,
        ) = self._resolve_monetary_scale(
            risk_plan,
            friction,
            candidate,
        )

        ctx[
            "monetary_cost_per_price_unit"
        ] = monetary_scale

        ctx[
            "monetary_scale_cross_checks"
        ] = scale_checks

        if not scale_valid:

            return self._invalid(
                reason=scale_reason,
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
            )

        (
            point_valid,
            point_reason,
            point,
        ) = self._resolve_point(
            risk_plan
        )

        if not point_valid:

            return self._invalid(
                reason=point_reason,
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
            )

        ctx[
            "point_available"
        ] = (
            point is not None
        )

        ctx[
            "point"
        ] = point

        # ---------------------------------------------------------------------
        # Fill price
        # ---------------------------------------------------------------------

        fill_available = (
            telemetry.fill_price
            is not None
        )

        ctx[
            "fill_price_available"
        ] = fill_available

        fill_price: float | None = None

        if fill_available:

            fill_price = self._number(
                telemetry.fill_price
            )

            if (
                not math.isfinite(
                    fill_price
                )
                or
                fill_price <= 0.0
            ):

                return self._invalid(
                    reason="INVALID_FILL_PRICE",
                    lifecycle_transition=lifecycle_transition,
                    telemetry=telemetry,
                    cost_state=cost_state,
                    ctx=ctx,
                )

            ctx[
                "fill_price"
            ] = fill_price

        # ---------------------------------------------------------------------
        # Quote
        # ---------------------------------------------------------------------

        bid_supplied = (
            telemetry.quote_bid
            is not None
        )

        ask_supplied = (
            telemetry.quote_ask
            is not None
        )

        if (
            bid_supplied
            !=
            ask_supplied
        ):

            return self._invalid(
                reason="PARTIAL_EXECUTION_QUOTE",
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
            )

        quote_available = (
            bid_supplied
            and
            ask_supplied
        )

        ctx[
            "quote_available"
        ] = quote_available

        if quote_available:

            quote_bid = self._number(
                telemetry.quote_bid
            )

            quote_ask = self._number(
                telemetry.quote_ask
            )

            if (
                not math.isfinite(
                    quote_bid
                )
                or
                not math.isfinite(
                    quote_ask
                )
                or
                quote_bid <= 0.0
                or
                quote_ask <= 0.0
                or
                quote_ask < quote_bid
            ):

                return self._invalid(
                    reason="INVALID_EXECUTION_QUOTE",
                    lifecycle_transition=lifecycle_transition,
                    telemetry=telemetry,
                    cost_state=cost_state,
                    ctx=ctx,
                )

            ctx[
                "quote_bid"
            ] = quote_bid

            ctx[
                "quote_ask"
            ] = quote_ask

            realized_spread_price = (
                quote_ask
                -
                quote_bid
            )

            realized_spread_cost = (
                realized_spread_price
                *
                monetary_scale
            )

            ctx[
                "realized_spread_price"
            ] = realized_spread_price

            ctx[
                "realized_spread_available"
            ] = True

            ctx[
                "realized_spread_cost"
            ] = realized_spread_cost

            if point is not None:

                ctx[
                    "realized_spread_points"
                ] = (
                    realized_spread_price
                    /
                    point
                )

            # -------------------------------------------------------------
            # Signed slippage
            # -------------------------------------------------------------

            if fill_available:

                if direction == "LONG":

                    realized_slippage_price = (
                        float(
                            fill_price
                        )
                        -
                        quote_ask
                    )

                else:

                    realized_slippage_price = (
                        quote_bid
                        -
                        float(
                            fill_price
                        )
                    )

                realized_slippage_cost = (
                    realized_slippage_price
                    *
                    monetary_scale
                )

                ctx[
                    "realized_slippage_price_available"
                ] = True

                ctx[
                    "realized_slippage_price"
                ] = realized_slippage_price

                ctx[
                    "realized_slippage_available"
                ] = True

                ctx[
                    "realized_slippage_cost"
                ] = realized_slippage_cost

                if point is not None:

                    ctx[
                        "realized_slippage_points"
                    ] = (
                        realized_slippage_price
                        /
                        point
                    )

        # ---------------------------------------------------------------------
        # Normalized commission
        # ---------------------------------------------------------------------

        commission_available = (
            telemetry.commission_cost
            is not None
        )

        ctx[
            "realized_commission_available"
        ] = commission_available

        if commission_available:

            commission = self._number(
                telemetry.commission_cost
            )

            if (
                not math.isfinite(
                    commission
                )
                or
                commission < 0.0
            ):

                return self._invalid(
                    reason=(
                        "INVALID_NORMALIZED_COMMISSION_COST"
                    ),
                    lifecycle_transition=lifecycle_transition,
                    telemetry=telemetry,
                    cost_state=cost_state,
                    ctx=ctx,
                )

            ctx[
                "realized_commission_cost"
            ] = commission

        # Need at least one realized cost component.
        if (
            not quote_available
            and
            not commission_available
        ):

            return self._invalid(
                reason="NO_REALIZED_COST_OBSERVATION",
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
            )

        # ---------------------------------------------------------------------
        # Existing lifecycle observer remains authoritative.
        # ---------------------------------------------------------------------

        try:

            observer_result = self.observer.observe(
                cost_state=cost_state,
                execution_id=execution_id,
                lifecycle_transition=lifecycle_transition,
                realized_spread_cost=(
                    ctx.get(
                        "realized_spread_cost"
                    )
                    if quote_available
                    else
                    None
                ),
                realized_slippage_cost=(
                    ctx.get(
                        "realized_slippage_cost"
                    )
                    if ctx.get(
                        "realized_slippage_available",
                        False,
                    )
                    else
                    None
                ),
                realized_commission_cost=(
                    ctx.get(
                        "realized_commission_cost"
                    )
                    if commission_available
                    else
                    None
                ),
            )

        except Exception:

            return self._invalid(
                reason="REALIZED_COST_OBSERVER_EXCEPTION",
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
                observer_invoked=True,
            )

        if not self._has_fields(
            observer_result,
            self._REQUIRED_OBSERVER_FIELDS,
        ):

            return self._invalid(
                reason=(
                    "INVALID_REALIZED_COST_OBSERVER_RESULT"
                ),
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
                observer_result=observer_result,
                observer_invoked=True,
            )

        observer_reason = str(
            observer_result.reason
        )

        cost_reason = str(
            observer_result.cost_reason
        )

        if (
            not bool(
                observer_result.valid
            )
            or
            not bool(
                observer_result.observed
            )
        ):

            return self._invalid(
                reason="REALIZED_COST_OBSERVER_REJECTED",
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
                observer_result=observer_result,
                observer_invoked=True,
                observer_reason=observer_reason,
                cost_reason=cost_reason,
            )

        observer_delta = self._number(
            observer_result.lifecycle_pnl_delta
        )

        if (
            bool(
                observer_result.live_authorized
            )
            or
            not math.isfinite(
                observer_delta
            )
            or
            abs(
                observer_delta
            )
            >
            self._EPSILON
        ):

            return self._invalid(
                reason=(
                    "REALIZED_COST_OBSERVER_BOUNDARY_VIOLATION"
                ),
                lifecycle_transition=lifecycle_transition,
                telemetry=telemetry,
                cost_state=cost_state,
                ctx=ctx,
                observer_result=observer_result,
                observer_invoked=True,
                observer_reason=observer_reason,
                cost_reason=cost_reason,
            )

        return self._build(
            valid=True,
            observed=True,
            reason="OK_NORMALIZED_ACTUAL_FILL_OBSERVED",
            lifecycle_transition=lifecycle_transition,
            telemetry=telemetry,
            cost_state_before=cost_state,
            cost_state_after=(
                observer_result.cost_state_after
            ),
            observer_result=observer_result,
            observer_invoked=True,
            observer_reason=observer_reason,
            cost_reason=cost_reason,
            ctx=ctx,
        )


realized_fill_telemetry_bridge = (
    RealizedFillTelemetryBridge()
)