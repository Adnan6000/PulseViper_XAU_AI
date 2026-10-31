from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

import pandas as pd


POLICY_VERSION = "R03_SESSION_GAP_POLICY_R3_V1"

HORIZON_BARS = 12
BAR_MINUTES = 5

STATUS_ELIGIBLE = "STRICT_HORIZON_ELIGIBLE"
STATUS_GAP = "STRICT_HORIZON_SESSION_GAP"
STATUS_INSUFFICIENT = "INSUFFICIENT_FUTURE_BARS"


class R03SessionGapPolicyError(RuntimeError):
    pass


@dataclass(frozen=True)
class SessionGapAssessment:
    status: str
    decision_time_utc: str
    available_future_bars: int
    expected_last_utc: str
    actual_last_utc: str | None
    missing_timestamps_utc: tuple[str, ...]

    outcome_maturation_authorized: bool = False
    terminal_disposition_authorized: bool = False
    live_authorized: bool = False
    execution_authorized: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy_version": POLICY_VERSION,
            "status": self.status,
            "decision_time_utc": self.decision_time_utc,
            "available_future_bars": self.available_future_bars,
            "expected_last_utc": self.expected_last_utc,
            "actual_last_utc": self.actual_last_utc,
            "missing_timestamps_utc": list(
                self.missing_timestamps_utc
            ),
            "outcome_maturation_authorized": False,
            "terminal_disposition_authorized": False,
            "live_authorized": False,
            "execution_authorized": False,
        }


def _utc(value: Any) -> pd.Timestamp:
    try:
        result = pd.Timestamp(value)
    except Exception as exc:
        raise R03SessionGapPolicyError(
            "INVALID_TIMESTAMP"
        ) from exc

    if pd.isna(result):
        raise R03SessionGapPolicyError(
            "NULL_TIMESTAMP"
        )

    if result.tzinfo is None:
        raise R03SessionGapPolicyError(
            "UTC_AWARE_TIMESTAMP_REQUIRED"
        )

    return cast(
        pd.Timestamp,
        result.tz_convert("UTC"),
    )


def assess_session_gap(
    *,
    decision_time_utc: Any,
    completed_m5_times: Any,
) -> SessionGapAssessment:

    decision = _utc(decision_time_utc)

    try:
        times = pd.DatetimeIndex(
            pd.to_datetime(
                completed_m5_times,
                utc=True,
            )
        )
    except Exception as exc:
        raise R03SessionGapPolicyError(
            "INVALID_M5_TIMESTAMPS"
        ) from exc

    if times.hasnans:
        raise R03SessionGapPolicyError(
            "NULL_M5_TIMESTAMP"
        )

    if not times.is_monotonic_increasing:
        raise R03SessionGapPolicyError(
            "UNSORTED_M5_HISTORY"
        )

    if not times.is_unique:
        raise R03SessionGapPolicyError(
            "DUPLICATE_M5_TIMESTAMP"
        )

    future = times[
        times >= decision
    ][:HORIZON_BARS]

    expected = pd.date_range(
        start=decision,
        periods=HORIZON_BARS,
        freq=f"{BAR_MINUTES}min",
    )

    # Explicit scalar Timestamp conversion keeps Pyright
    # from treating Index elements as generic Index objects.
    missing = tuple(
        _utc(value).isoformat()
        for value in expected
        if value not in times
    )

    actual_last: str | None = None

    if len(future) > 0:
        actual_last = _utc(
            future[-1]
        ).isoformat()

    if len(future) < HORIZON_BARS:
        status = STATUS_INSUFFICIENT

    elif future.equals(expected):
        status = STATUS_ELIGIBLE

    else:
        status = STATUS_GAP

    return SessionGapAssessment(
        status=status,
        decision_time_utc=decision.isoformat(),
        available_future_bars=len(future),
        expected_last_utc=_utc(
            expected[-1]
        ).isoformat(),
        actual_last_utc=actual_last,
        missing_timestamps_utc=missing,
    )