"""
Forward/demo execution evidence capture.

This module preserves the exact executable quote and request metadata observed
immediately before an external execution owner submits an order. It later
reconciles that immutable evidence with an already-completed broker fill and
emits NormalizedActualFillTelemetry for the existing realized-fill bridge.

SHADOW / RESEARCH / DEMO ONLY.

Critical boundary:
- no MT5 connection
- no order_send
- no order/position modification
- no lifecycle/accounting mutation
- no trade_ready mutation
- no production RiskEngine mutation
- no live authorization
"""

from __future__ import annotations

import importlib
import math

from dataclasses import dataclass, replace
from typing import Any


_telemetry_module: Any = importlib.import_module(
    "02_AI.Shadow.realized_fill_telemetry_bridge"
)

NormalizedActualFillTelemetry: Any = (
    _telemetry_module.NormalizedActualFillTelemetry
)


@dataclass(frozen=True)
class ForwardExecutionEvidencePolicy:
    volume_tolerance: float = 1e-8
    numeric_tolerance: float = 1e-10
    max_capture_to_submission_ms: int = 1000


@dataclass(frozen=True)
class CompletedExecutionFill:
    order_ticket: int
    execution_id: str
    symbol: str
    direction: str
    filled_volume: float
    fill_price: float
    commission_cost: float
    live_authorized: bool = False


@dataclass(frozen=True)
class ForwardExecutionEvidenceRecord:
    request_id: str
    symbol: str
    direction: str
    requested_volume: float

    quote_bid: float
    quote_ask: float
    quote_time_msc: int

    captured_at_msc: int
    submitted_at_msc: int
    submission_latency_ms: int

    request_price: float | None
    requested_deviation_points: int | None

    order_ticket: int | None
    status: str
    finalized_execution_id: str

    live_authorized: bool = False


@dataclass(frozen=True)
class ForwardExecutionEvidenceState:
    records: tuple[
        ForwardExecutionEvidenceRecord,
        ...,
    ] = ()


@dataclass(frozen=True)
class ForwardExecutionEvidenceTransition:
    valid: bool
    applied: bool
    reason: str
    action: str
    mode: str
    version: str
    live_authorized: bool

    request_id: str
    order_ticket: int

    quote_side_price: float
    submission_latency_ms: int

    signed_slippage_price: float | None

    telemetry: Any
    record: Any

    state_before: Any
    state_after: Any


class ForwardExecutionEvidenceCapture:
    VERSION = "1.0"

    MODE = (
        "SHADOW_FORWARD_EXECUTION_EVIDENCE_CAPTURE_ONLY"
    )

    _REQUIRED_FILL_FIELDS = (
        "order_ticket",
        "execution_id",
        "symbol",
        "direction",
        "filled_volume",
        "fill_price",
        "commission_cost",
        "live_authorized",
    )

    def __init__(
        self,
        *,
        policy: ForwardExecutionEvidencePolicy | None = None,
    ) -> None:
        self.policy = (
            policy
            if policy is not None
            else ForwardExecutionEvidencePolicy()
        )

        self._validate_policy()

    # =========================================================================
    # Policy / state
    # =========================================================================

    def _validate_policy(
        self,
    ) -> None:
        try:
            volume_tolerance = float(
                self.policy.volume_tolerance
            )

            numeric_tolerance = float(
                self.policy.numeric_tolerance
            )

        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                "numeric policy values must be numbers"
            ) from exc

        if (
            not math.isfinite(
                volume_tolerance
            )
            or
            volume_tolerance <= 0.0
        ):
            raise ValueError(
                "volume_tolerance must be positive"
            )

        if (
            not math.isfinite(
                numeric_tolerance
            )
            or
            numeric_tolerance <= 0.0
        ):
            raise ValueError(
                "numeric_tolerance must be positive"
            )

        if (
            not isinstance(
                self.policy.max_capture_to_submission_ms,
                int,
            )
            or
            self.policy.max_capture_to_submission_ms < 0
        ):
            raise ValueError(
                "max_capture_to_submission_ms "
                "must be a non-negative integer"
            )

    @staticmethod
    def initial_state(
    ) -> ForwardExecutionEvidenceState:
        return ForwardExecutionEvidenceState()

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
        value: Any,
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
    def _integer(
        value: Any,
    ) -> int | None:
        if isinstance(
            value,
            bool,
        ):
            return None

        try:
            return int(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _direction(
        value: Any,
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

    def _volume_close(
        self,
        left: float,
        right: float,
    ) -> bool:
        return math.isclose(
            left,
            right,
            rel_tol=0.0,
            abs_tol=self.policy.volume_tolerance,
        )

    @staticmethod
    def _valid_state(
        state: Any,
    ) -> bool:
        return (
            isinstance(
                state,
                ForwardExecutionEvidenceState,
            )
            and
            isinstance(
                state.records,
                tuple,
            )
            and
            all(
                isinstance(
                    record,
                    ForwardExecutionEvidenceRecord,
                )
                for record
                in state.records
            )
        )

    @staticmethod
    def _find_request(
        state: ForwardExecutionEvidenceState,
        request_id: str,
    ) -> ForwardExecutionEvidenceRecord | None:
        for record in state.records:
            if (
                record.request_id
                ==
                request_id
            ):
                return record

        return None

    @staticmethod
    def _find_order(
        state: ForwardExecutionEvidenceState,
        order_ticket: int,
    ) -> ForwardExecutionEvidenceRecord | None:
        for record in state.records:
            if (
                record.order_ticket
                ==
                order_ticket
            ):
                return record

        return None

    @staticmethod
    def _replace_record(
        state: ForwardExecutionEvidenceState,
        updated: ForwardExecutionEvidenceRecord,
    ) -> ForwardExecutionEvidenceState:
        return ForwardExecutionEvidenceState(
            records=tuple(
                updated
                if (
                    record.request_id
                    ==
                    updated.request_id
                )
                else record
                for record
                in state.records
            )
        )

    # =========================================================================
    # Result helpers
    # =========================================================================

    def _transition(
        self,
        *,
        valid: bool,
        applied: bool,
        reason: str,
        state_before: Any,
        state_after: Any,
        request_id: str = "",
        order_ticket: int = 0,
        quote_side_price: float = 0.0,
        submission_latency_ms: int = 0,
        signed_slippage_price: float | None = None,
        telemetry: Any = None,
        record: Any = None,
    ) -> ForwardExecutionEvidenceTransition:
        if applied:
            if telemetry is not None:
                action = (
                    "FINALIZE_FORWARD_EXECUTION_EVIDENCE"
                )

            elif order_ticket > 0:
                action = (
                    "BIND_FORWARD_EXECUTION_ORDER"
                )

            else:
                action = (
                    "CAPTURE_FORWARD_EXECUTION_SUBMISSION"
                )

        else:
            action = "NO_ACTION"

        return ForwardExecutionEvidenceTransition(
            valid=valid,
            applied=applied,
            reason=reason,
            action=action,
            mode=self.MODE,
            version=self.VERSION,
            live_authorized=False,
            request_id=request_id,
            order_ticket=order_ticket,
            quote_side_price=quote_side_price,
            submission_latency_ms=(
                submission_latency_ms
            ),
            signed_slippage_price=(
                signed_slippage_price
            ),
            telemetry=telemetry,
            record=record,
            state_before=state_before,
            state_after=state_after,
        )

    def _invalid(
        self,
        *,
        reason: str,
        state: Any,
        request_id: str = "",
        order_ticket: int = 0,
        record: Any = None,
    ) -> ForwardExecutionEvidenceTransition:
        return self._transition(
            valid=False,
            applied=False,
            reason=reason,
            state_before=state,
            state_after=state,
            request_id=request_id,
            order_ticket=order_ticket,
            record=record,
        )

    # =========================================================================
    # Stage 1: capture pre-submit evidence
    # =========================================================================

    def capture_submission(
        self,
        *,
        state: Any,
        request_id: str,
        symbol: str,
        direction: str,
        requested_volume: float,
        quote_bid: float,
        quote_ask: float,
        quote_time_msc: int,
        captured_at_msc: int,
        submitted_at_msc: int,
        request_price: float | None = None,
        requested_deviation_points: int | None = None,
        live_authorized: bool = False,
    ) -> ForwardExecutionEvidenceTransition:
        if not self._valid_state(
            state
        ):
            return self._invalid(
                reason="INVALID_EVIDENCE_STATE_SHAPE",
                state=state,
            )

        if live_authorized:
            return self._invalid(
                reason="LIVE_AUTHORIZATION_NOT_ALLOWED",
                state=state,
            )

        resolved_request_id = str(
            request_id
        ).strip()

        if not resolved_request_id:
            return self._invalid(
                reason="INVALID_REQUEST_ID",
                state=state,
            )

        if (
            self._find_request(
                state,
                resolved_request_id,
            )
            is not None
        ):
            return self._invalid(
                reason="DUPLICATE_REQUEST_ID",
                state=state,
                request_id=resolved_request_id,
            )

        resolved_symbol = str(
            symbol
        ).strip()

        if not resolved_symbol:
            return self._invalid(
                reason="INVALID_SYMBOL",
                state=state,
                request_id=resolved_request_id,
            )

        resolved_direction = self._direction(
            direction
        )

        if (
            resolved_direction
            ==
            "INVALID"
        ):
            return self._invalid(
                reason="INVALID_DIRECTION",
                state=state,
                request_id=resolved_request_id,
            )

        volume = self._number(
            requested_volume
        )

        if (
            not math.isfinite(
                volume
            )
            or
            volume <= 0.0
        ):
            return self._invalid(
                reason="INVALID_REQUESTED_VOLUME",
                state=state,
                request_id=resolved_request_id,
            )

        bid = self._number(
            quote_bid
        )

        ask = self._number(
            quote_ask
        )

        if (
            not math.isfinite(
                bid
            )
            or
            not math.isfinite(
                ask
            )
            or
            bid <= 0.0
            or
            ask <= 0.0
        ):
            return self._invalid(
                reason="INVALID_SUBMISSION_QUOTE",
                state=state,
                request_id=resolved_request_id,
            )

        if (
            ask
            <
            (
                bid
                -
                self.policy.numeric_tolerance
            )
        ):
            return self._invalid(
                reason="SUBMISSION_QUOTE_INVERTED",
                state=state,
                request_id=resolved_request_id,
            )

        if ask < bid:
            ask = bid

        quote_time = self._integer(
            quote_time_msc
        )

        captured_at = self._integer(
            captured_at_msc
        )

        submitted_at = self._integer(
            submitted_at_msc
        )

        if (
            quote_time is None
            or
            captured_at is None
            or
            submitted_at is None
            or
            quote_time <= 0
            or
            captured_at <= 0
            or
            submitted_at <= 0
        ):
            return self._invalid(
                reason="INVALID_SUBMISSION_TIMESTAMPS",
                state=state,
                request_id=resolved_request_id,
            )

        if (
            submitted_at
            <
            captured_at
        ):
            return self._invalid(
                reason="SUBMISSION_TIME_PRECEDES_CAPTURE",
                state=state,
                request_id=resolved_request_id,
            )

        submission_latency = (
            submitted_at
            -
            captured_at
        )

        if (
            submission_latency
            >
            self.policy.max_capture_to_submission_ms
        ):
            return self._invalid(
                reason=(
                    "CAPTURE_TO_SUBMISSION_DELAY_EXCEEDED"
                ),
                state=state,
                request_id=resolved_request_id,
            )

        resolved_request_price: float | None = (
            None
        )

        if request_price is not None:
            price = self._number(
                request_price
            )

            if (
                not math.isfinite(
                    price
                )
                or
                price <= 0.0
            ):
                return self._invalid(
                    reason="INVALID_REQUEST_PRICE",
                    state=state,
                    request_id=resolved_request_id,
                )

            resolved_request_price = price

        resolved_deviation: int | None = None

        if requested_deviation_points is not None:
            deviation = self._integer(
                requested_deviation_points
            )

            if (
                deviation is None
                or
                deviation < 0
            ):
                return self._invalid(
                    reason=(
                        "INVALID_REQUESTED_DEVIATION"
                    ),
                    state=state,
                    request_id=resolved_request_id,
                )

            resolved_deviation = deviation

        quote_side = (
            ask
            if resolved_direction == "LONG"
            else bid
        )

        record = ForwardExecutionEvidenceRecord(
            request_id=resolved_request_id,
            symbol=resolved_symbol,
            direction=resolved_direction,
            requested_volume=volume,
            quote_bid=bid,
            quote_ask=ask,
            quote_time_msc=quote_time,
            captured_at_msc=captured_at,
            submitted_at_msc=submitted_at,
            submission_latency_ms=(
                submission_latency
            ),
            request_price=resolved_request_price,
            requested_deviation_points=(
                resolved_deviation
            ),
            order_ticket=None,
            status="CAPTURED",
            finalized_execution_id="",
            live_authorized=False,
        )

        state_after = ForwardExecutionEvidenceState(
            records=(
                state.records
                +
                (
                    record,
                )
            )
        )

        return self._transition(
            valid=True,
            applied=True,
            reason=(
                "OK_FORWARD_EXECUTION_SUBMISSION_CAPTURED"
            ),
            state_before=state,
            state_after=state_after,
            request_id=resolved_request_id,
            quote_side_price=quote_side,
            submission_latency_ms=(
                submission_latency
            ),
            record=record,
        )

    # =========================================================================
    # Stage 2: externally returned broker order ticket binding
    # =========================================================================

    def bind_order(
        self,
        *,
        state: Any,
        request_id: str,
        order_ticket: int,
        live_authorized: bool = False,
    ) -> ForwardExecutionEvidenceTransition:
        if not self._valid_state(
            state
        ):
            return self._invalid(
                reason="INVALID_EVIDENCE_STATE_SHAPE",
                state=state,
            )

        resolved_request_id = str(
            request_id
        ).strip()

        if not resolved_request_id:
            return self._invalid(
                reason="INVALID_REQUEST_ID",
                state=state,
            )

        if live_authorized:
            return self._invalid(
                reason="LIVE_AUTHORIZATION_NOT_ALLOWED",
                state=state,
                request_id=resolved_request_id,
            )

        order = self._integer(
            order_ticket
        )

        if (
            order is None
            or
            order <= 0
        ):
            return self._invalid(
                reason="INVALID_ORDER_TICKET",
                state=state,
                request_id=resolved_request_id,
            )

        record = self._find_request(
            state,
            resolved_request_id,
        )

        if record is None:
            return self._invalid(
                reason="REQUEST_EVIDENCE_NOT_FOUND",
                state=state,
                request_id=resolved_request_id,
                order_ticket=order,
            )

        if (
            record.status
            !=
            "CAPTURED"
            or
            record.order_ticket is not None
        ):
            return self._invalid(
                reason=(
                    "REQUEST_ALREADY_BOUND_OR_FINALIZED"
                ),
                state=state,
                request_id=resolved_request_id,
                order_ticket=order,
                record=record,
            )

        existing_order = self._find_order(
            state,
            order,
        )

        if existing_order is not None:
            return self._invalid(
                reason="DUPLICATE_ORDER_TICKET_BINDING",
                state=state,
                request_id=resolved_request_id,
                order_ticket=order,
                record=record,
            )

        updated = replace(
            record,
            order_ticket=order,
            status="BOUND",
        )

        state_after = self._replace_record(
            state,
            updated,
        )

        quote_side = (
            updated.quote_ask
            if updated.direction == "LONG"
            else updated.quote_bid
        )

        return self._transition(
            valid=True,
            applied=True,
            reason=(
                "OK_FORWARD_EXECUTION_ORDER_BOUND"
            ),
            state_before=state,
            state_after=state_after,
            request_id=resolved_request_id,
            order_ticket=order,
            quote_side_price=quote_side,
            submission_latency_ms=(
                updated.submission_latency_ms
            ),
            record=updated,
        )

    # =========================================================================
    # Stage 3: reconcile actual completed broker fill
    # =========================================================================

    def reconcile_completed_fill(
        self,
        *,
        state: Any,
        completed_fill: Any,
    ) -> ForwardExecutionEvidenceTransition:
        if not self._valid_state(
            state
        ):
            return self._invalid(
                reason="INVALID_EVIDENCE_STATE_SHAPE",
                state=state,
            )

        if not self._has_fields(
            completed_fill,
            self._REQUIRED_FILL_FIELDS,
        ):
            return self._invalid(
                reason="INVALID_COMPLETED_FILL_SHAPE",
                state=state,
            )

        if bool(
            completed_fill.live_authorized
        ):
            return self._invalid(
                reason=(
                    "COMPLETED_FILL_LIVE_AUTHORIZATION_NOT_ALLOWED"
                ),
                state=state,
            )

        order = self._integer(
            completed_fill.order_ticket
        )

        if (
            order is None
            or
            order <= 0
        ):
            return self._invalid(
                reason=(
                    "INVALID_COMPLETED_FILL_ORDER_TICKET"
                ),
                state=state,
            )

        record = self._find_order(
            state,
            order,
        )

        if record is None:
            return self._invalid(
                reason="ORDER_EVIDENCE_NOT_FOUND",
                state=state,
                order_ticket=order,
            )

        if (
            record.status
            ==
            "FINALIZED"
        ):
            return self._invalid(
                reason=(
                    "ORDER_EVIDENCE_ALREADY_FINALIZED"
                ),
                state=state,
                request_id=record.request_id,
                order_ticket=order,
                record=record,
            )

        if (
            record.status
            !=
            "BOUND"
        ):
            return self._invalid(
                reason="ORDER_EVIDENCE_NOT_BOUND",
                state=state,
                request_id=record.request_id,
                order_ticket=order,
                record=record,
            )

        execution_id = str(
            completed_fill.execution_id
        ).strip()

        if not execution_id:
            return self._invalid(
                reason=(
                    "INVALID_COMPLETED_FILL_EXECUTION_ID"
                ),
                state=state,
                request_id=record.request_id,
                order_ticket=order,
                record=record,
            )

        if any(
            (
                existing.finalized_execution_id
                ==
                execution_id
            )
            for existing
            in state.records
            if existing.finalized_execution_id
        ):
            return self._invalid(
                reason="DUPLICATE_COMPLETED_EXECUTION_ID",
                state=state,
                request_id=record.request_id,
                order_ticket=order,
                record=record,
            )

        symbol = str(
            completed_fill.symbol
        ).strip()

        if not symbol:
            return self._invalid(
                reason="INVALID_COMPLETED_FILL_SYMBOL",
                state=state,
                request_id=record.request_id,
                order_ticket=order,
                record=record,
            )

        if (
            symbol.upper()
            !=
            record.symbol.upper()
        ):
            return self._invalid(
                reason="COMPLETED_FILL_SYMBOL_MISMATCH",
                state=state,
                request_id=record.request_id,
                order_ticket=order,
                record=record,
            )

        direction = self._direction(
            completed_fill.direction
        )

        if (
            direction
            ==
            "INVALID"
        ):
            return self._invalid(
                reason=(
                    "INVALID_COMPLETED_FILL_DIRECTION"
                ),
                state=state,
                request_id=record.request_id,
                order_ticket=order,
                record=record,
            )

        if (
            direction
            !=
            record.direction
        ):
            return self._invalid(
                reason=(
                    "COMPLETED_FILL_DIRECTION_MISMATCH"
                ),
                state=state,
                request_id=record.request_id,
                order_ticket=order,
                record=record,
            )

        volume = self._number(
            completed_fill.filled_volume
        )

        if (
            not math.isfinite(
                volume
            )
            or
            volume <= 0.0
        ):
            return self._invalid(
                reason="INVALID_COMPLETED_FILL_VOLUME",
                state=state,
                request_id=record.request_id,
                order_ticket=order,
                record=record,
            )

        if not self._volume_close(
            volume,
            record.requested_volume,
        ):
            return self._invalid(
                reason=(
                    "COMPLETED_FILL_VOLUME_MISMATCH"
                ),
                state=state,
                request_id=record.request_id,
                order_ticket=order,
                record=record,
            )

        fill_price = self._number(
            completed_fill.fill_price
        )

        if (
            not math.isfinite(
                fill_price
            )
            or
            fill_price <= 0.0
        ):
            return self._invalid(
                reason="INVALID_COMPLETED_FILL_PRICE",
                state=state,
                request_id=record.request_id,
                order_ticket=order,
                record=record,
            )

        commission = self._number(
            completed_fill.commission_cost
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
                    "INVALID_COMPLETED_FILL_COMMISSION"
                ),
                state=state,
                request_id=record.request_id,
                order_ticket=order,
                record=record,
            )

        if (
            commission
            <
            self.policy.numeric_tolerance
        ):
            commission = 0.0

        quote_side = (
            record.quote_ask
            if direction == "LONG"
            else record.quote_bid
        )

        signed_slippage = (
            (
                fill_price
                -
                quote_side
            )
            if direction == "LONG"
            else
            (
                quote_side
                -
                fill_price
            )
        )

        telemetry = NormalizedActualFillTelemetry(
            execution_id=execution_id,
            filled_volume=volume,
            fill_price=fill_price,
            quote_bid=record.quote_bid,
            quote_ask=record.quote_ask,
            commission_cost=commission,
            live_authorized=False,
        )

        updated = replace(
            record,
            status="FINALIZED",
            finalized_execution_id=execution_id,
        )

        state_after = self._replace_record(
            state,
            updated,
        )

        return self._transition(
            valid=True,
            applied=True,
            reason=(
                "OK_FORWARD_EXECUTION_EVIDENCE_RECONCILED"
            ),
            state_before=state,
            state_after=state_after,
            request_id=record.request_id,
            order_ticket=order,
            quote_side_price=quote_side,
            submission_latency_ms=(
                record.submission_latency_ms
            ),
            signed_slippage_price=(
                signed_slippage
            ),
            telemetry=telemetry,
            record=updated,
        )


forward_execution_evidence_capture = (
    ForwardExecutionEvidenceCapture()
)