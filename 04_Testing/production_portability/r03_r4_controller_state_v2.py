from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

MINIMUM_MATURED_OUTCOMES = 60
MINIMUM_DISTINCT_UTC_DATES = 5

VERSION = "R03_R4_CONTROLLER_STATE_V2"

ACTION_CAPTURE = "CAPTURE_NEW_OBSERVATION"
ACTION_MATURE = "CHECK_PENDING_MATURITY"
ACTION_TARGET = "COLLECTION_TARGET_REACHED"
ACTION_BLOCKED = "BLOCKED_MULTIPLE_PENDING"


class R4ControllerError(RuntimeError):
    pass


@dataclass(frozen=True)
class R4State:
    observation_count: int
    anchor_count: int
    matured_count: int
    terminal_count: int
    pending_count: int
    pending_ids: tuple[str, ...]
    distinct_matured_dates: int
    target_reached: bool
    proposed_next_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": VERSION,
            "observation_count": self.observation_count,
            "anchor_count": self.anchor_count,
            "matured_outcome_count": self.matured_count,
            "terminal_disposition_count": self.terminal_count,
            "pending_count": self.pending_count,
            "pending_ids": list(self.pending_ids),
            "distinct_matured_dates": self.distinct_matured_dates,
            "minimum_matured_outcomes": MINIMUM_MATURED_OUTCOMES,
            "minimum_distinct_utc_dates": MINIMUM_DISTINCT_UTC_DATES,
            "collection_target_reached": self.target_reached,
            "proposed_next_action": self.proposed_next_action,
            "capture_authorized": False,
            "terminal_disposition_authorized": False,
            "ledger_writes_authorized": False,
            "performance_evaluated": False,
            "pnl_evaluated": False,
            "live_authorized": False,
            "execution_authorized": False,
        }


def derive_r4_state(
    *,
    observations: Mapping[str, str],
    anchors: set[str],
    outcomes: set[str],
    authorized_terminal_ids: set[str],
) -> R4State:
    """
    Pure state derivation only.

    observations maps logical IDs to ISO UTC decision dates,
    e.g. {"id": "2026-10-05"}.

    IMPORTANT: authorized_terminal_ids must eventually come
    from a separately verified authority. This function does
    not grant authorization or read diagnostic evidence.
    """

    observation_ids = set(observations)

    if not observation_ids <= anchors:
        raise R4ControllerError(
            "OBSERVATION_WITHOUT_ANCHOR"
        )

    if not outcomes <= observation_ids:
        raise R4ControllerError(
            "OUTCOME_WITHOUT_OBSERVATION"
        )

    if not authorized_terminal_ids <= observation_ids:
        raise R4ControllerError(
            "TERMINAL_WITHOUT_OBSERVATION"
        )

    if outcomes & authorized_terminal_ids:
        raise R4ControllerError(
            "OUTCOME_TERMINAL_CONFLICT"
        )

    pending = tuple(
        sorted(
            observation_ids
            - outcomes
            - authorized_terminal_ids
        )
    )

    matured_dates = {
        observations[logical_id]
        for logical_id in outcomes
    }

    matured_count = len(outcomes)

    target_reached = (
        matured_count >= MINIMUM_MATURED_OUTCOMES
        and len(matured_dates) >= MINIMUM_DISTINCT_UTC_DATES
    )

    if len(pending) > 1:
        next_action = ACTION_BLOCKED

    elif pending:
        next_action = ACTION_MATURE

    elif target_reached:
        next_action = ACTION_TARGET

    else:
        next_action = ACTION_CAPTURE

    return R4State(
        observation_count=len(observation_ids),
        anchor_count=len(anchors),
        matured_count=matured_count,
        terminal_count=len(authorized_terminal_ids),
        pending_count=len(pending),
        pending_ids=pending,
        distinct_matured_dates=len(matured_dates),
        target_reached=target_reached,
        proposed_next_action=next_action,
    )