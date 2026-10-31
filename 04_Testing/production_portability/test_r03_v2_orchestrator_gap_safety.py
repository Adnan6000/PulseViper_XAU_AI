from __future__ import annotations

import importlib
from types import SimpleNamespace
from typing import Any

import pytest


o = importlib.import_module(
    "04_Testing.production_portability."
    "run_xauusd_r03_v2_orchestrator"
)


def state(
    action: str,
    approved: bool = True,
) -> Any:
    return SimpleNamespace(
        next_action=action,
        protocol_authorized=approved,
        to_dict=lambda: {
            "next_action": action,
            "protocol_authorized": approved,
        },
    )


def forbidden_acquisition() -> Any:
    raise AssertionError("MT5_MUST_NOT_BE_CALLED")


@pytest.mark.parametrize(
    "action,expected",
    [
        (o.LANE.BLOCKED, "BLOCKED_PROTOCOL_AUTHORITY"),
        (
            o.LANE.TERMINAL_BLOCKED,
            "BLOCKED_TERMINAL_POLICY_AUTHORITY",
        ),
        (o.LANE.ORPHAN, "BLOCKED_ORPHAN_ANCHOR"),
        (o.LANE.TARGET, "COLLECTION_TARGET_REACHED"),
    ],
)
def test_blocked_state_never_calls_mt5(
    monkeypatch: pytest.MonkeyPatch,
    action: str,
    expected: str,
) -> None:
    monkeypatch.setattr(
        o.LANE,
        "inspect",
        lambda: state(action),
    )

    result = o.execute(acquire=forbidden_acquisition)

    assert result["action"] == expected
    assert result["live_authorized"] is False
    assert result["execution_authorized"] is False


@pytest.mark.parametrize(
    "reason",
    [
        "INSUFFICIENT_HISTORICAL_COVERAGE",
        "WAIT_HORIZON_NOT_ELAPSED",
    ],
)
def test_unconfirmed_gap_never_writes_outcome(
    monkeypatch: pytest.MonkeyPatch,
    reason: str,
) -> None:
    def frozen_gap(*, snapshot: Any) -> Any:
        raise o.MATURER.R03OutcomeMaturationError(
            "LAST_FUTURE_M5_BAR_NOT_CONTIGUOUS"
        )

    monkeypatch.setattr(
        o.LANE, "mature_from_snapshot", frozen_gap
    )

    monkeypatch.setattr(
        o.GAP,
        "record_pending_gap",
        lambda *, snapshot: {
            "action": reason,
            "evidence_appended": False,
            "capture_slot_released": False,
        },
    )

    result = o.process_maturity(snapshot=object())

    assert result["action"] == "BLOCKED_UNCONFIRMED_M5_GAP"
    assert result["reason"] == reason
    assert result["outcome_matured"] is False
    assert result["evidence_appended"] is False
    assert result["capture_slot_released"] is False


def test_complete_horizon_contradiction_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def frozen_gap(*, snapshot: Any) -> Any:
        raise o.MATURER.R03OutcomeMaturationError(
            "LAST_FUTURE_M5_BAR_NOT_CONTIGUOUS"
        )

    monkeypatch.setattr(
        o.LANE, "mature_from_snapshot", frozen_gap
    )

    monkeypatch.setattr(
        o.GAP,
        "record_pending_gap",
        lambda *, snapshot: {
            "action": "STRICT_M5_HORIZON_COMPLETE",
            "evidence_appended": False,
            "capture_slot_released": False,
        },
    )

    with pytest.raises(
        o.OrchestratorError,
        match="FROZEN_MATURER_GAP_NOT_CORROBORATED",
    ):
        o.process_maturity(snapshot=object())


def test_unconfirmed_gap_through_full_cycle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        o.LANE,
        "inspect",
        lambda: state(o.LANE.MATURE),
    )
    monkeypatch.setattr(
        o.LANE, "authority_valid", lambda: True
    )

    def frozen_gap(*, snapshot: Any) -> Any:
        raise o.MATURER.R03OutcomeMaturationError(
            "FUTURE_M5_HORIZON_HAS_GAP"
        )

    monkeypatch.setattr(
        o.LANE, "mature_from_snapshot", frozen_gap
    )

    monkeypatch.setattr(
        o.GAP,
        "record_pending_gap",
        lambda *, snapshot: {
            "action": "INSUFFICIENT_HISTORICAL_COVERAGE",
            "evidence_appended": False,
            "capture_slot_released": False,
        },
    )

    result = o.execute(
        acquire=lambda: object(),
        verify_snapshot=lambda _: None,
    )

    assert result["action"] == "BLOCKED_UNCONFIRMED_M5_GAP"
    assert result["execution_authorized"] is False


def test_successful_gap_evidence_not_matured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def frozen_gap(*, snapshot: Any) -> Any:
        raise o.MATURER.R03OutcomeMaturationError(
            "FIRST_FUTURE_M5_BAR_NOT_CONTIGUOUS"
        )

    monkeypatch.setattr(
        o.LANE, "mature_from_snapshot", frozen_gap
    )

    monkeypatch.setattr(
        o.GAP,
        "record_pending_gap",
        lambda *, snapshot: {
            "action": "TERMINAL_EVIDENCE_RECORDED",
            "evidence_appended": True,
            "capture_slot_released": False,
        },
    )

    result = o.process_maturity(snapshot=object())

    assert result["action"] == "SESSION_GAP_EVIDENCE_RECORDED"
    assert result["outcome_matured"] is False
    assert result["capture_slot_released"] is False


def test_unrelated_frozen_failure_propagates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unrelated(*, snapshot: Any) -> Any:
        raise o.MATURER.R03OutcomeMaturationError(
            "ANCHOR_ARTIFACT_AUTHORITY_MISMATCH"
        )

    monkeypatch.setattr(
        o.LANE, "mature_from_snapshot", unrelated
    )

    monkeypatch.setattr(
        o.GAP,
        "record_pending_gap",
        lambda *, snapshot: pytest.fail(
            "GAP_RECORDER_MUST_NOT_RUN"
        ),
    )

    with pytest.raises(
        o.MATURER.R03OutcomeMaturationError,
        match="ANCHOR_ARTIFACT_AUTHORITY_MISMATCH",
    ):
        o.process_maturity(snapshot=object())
