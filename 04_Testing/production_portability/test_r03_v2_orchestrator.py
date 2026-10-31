
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
    *,
    approved: bool = False,
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


def configure_action(
    monkeypatch: pytest.MonkeyPatch,
    action: str,
    *,
    approved: bool = True,
) -> None:
    monkeypatch.setattr(
        o.LANE,
        "inspect",
        lambda: state(action, approved=approved),
    )

    monkeypatch.setattr(
        o.LANE,
        "authority_valid",
        lambda: approved,
    )


def test_unapproved_does_not_touch_mt5(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_action(
        monkeypatch,
        o.LANE.BLOCKED,
        approved=False,
    )

    result = o.execute(
        acquire=forbidden_acquisition
    )

    assert result["action"] == (
        "BLOCKED_PROTOCOL_AUTHORITY"
    )


def test_orphan_never_touches_mt5(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_action(
        monkeypatch,
        o.LANE.ORPHAN,
    )

    result = o.execute(
        acquire=forbidden_acquisition
    )

    assert result["action"] == (
        "BLOCKED_ORPHAN_ANCHOR"
    )


def test_target_never_touches_mt5(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_action(
        monkeypatch,
        o.LANE.TARGET,
    )

    result = o.execute(
        acquire=forbidden_acquisition
    )

    assert result["action"] == (
        "COLLECTION_TARGET_REACHED"
    )


def test_revoked_authority_blocks_before_mt5(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_action(
        monkeypatch,
        o.LANE.CAPTURE,
    )

    monkeypatch.setattr(
        o.LANE,
        "authority_valid",
        lambda: False,
    )

    with pytest.raises(
        o.OrchestratorError,
        match="AUTHORITY_REVOKED",
    ):
        o.run_cycle(
            acquire=forbidden_acquisition
        )


def test_capture_routes_to_v2(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_action(
        monkeypatch,
        o.LANE.CAPTURE,
    )

    snapshot = object()
    features = object()

    def capture(
        *,
        snapshot: Any,
        feature_result: Any,
    ) -> dict[str, Any]:
        assert snapshot is expected_snapshot
        assert feature_result is expected_features
        return {
            "action": "CAPTURED_RESEARCH_ONLY"
        }

    expected_snapshot = snapshot
    expected_features = features

    monkeypatch.setattr(
        o.LANE,
        "capture_from_snapshot",
        capture,
    )

    result = o.execute(
        acquire=lambda: snapshot,
        features=lambda _: features,
        verify_snapshot=lambda _: None,
    )

    assert result["action"] == (
        "CAPTURED_RESEARCH_ONLY"
    )

    assert result["live_authorized"] is False


def test_maturity_routes_to_v2(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_action(
        monkeypatch,
        o.LANE.MATURE,
    )

    monkeypatch.setattr(
        o.LANE,
        "mature_from_snapshot",
        lambda *, snapshot: {
            "action": "MATURED_RESEARCH_ONLY"
        },
    )

    result = o.execute(
        acquire=lambda: object(),
        verify_snapshot=lambda _: None,
    )

    assert result["action"] == (
        "MATURED_RESEARCH_ONLY"
    )


def test_insufficient_bars_waits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_action(
        monkeypatch,
        o.LANE.MATURE,
    )

    monkeypatch.setattr(
        o.LANE,
        "mature_from_snapshot",
        lambda *, snapshot: {
            "action": "WAIT",
            "reason": "INSUFFICIENT_FUTURE_BARS",
        },
    )

    result = o.execute(
        acquire=lambda: object(),
        verify_snapshot=lambda _: None,
    )

    assert result["action"] == "WAIT"


def test_unrecognized_action_blocks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_action(
        monkeypatch,
        "UNKNOWN",
    )

    with pytest.raises(
        o.OrchestratorError,
        match="UNSUPPORTED_ACTION",
    ):
        o.run_cycle(
            acquire=forbidden_acquisition
        )


def test_capture_without_approval_blocks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_action(
        monkeypatch,
        o.LANE.CAPTURE,
        approved=False,
    )

    with pytest.raises(
        o.OrchestratorError,
        match="PROTOCOL_NOT_AUTHORIZED",
    ):
        o.run_cycle(
            acquire=forbidden_acquisition
        )


@pytest.mark.parametrize(
    "reason",
    sorted(o.STRICT_GAP_ERRORS),
)
def test_frozen_gap_routes_to_evidence(
    monkeypatch: pytest.MonkeyPatch,
    reason: str,
) -> None:
    configure_action(
        monkeypatch,
        o.LANE.MATURE,
    )

    def raise_gap(*, snapshot: Any) -> Any:
        raise o.MATURER.R03OutcomeMaturationError(
            reason
        )

    monkeypatch.setattr(
        o.LANE,
        "mature_from_snapshot",
        raise_gap,
    )

    monkeypatch.setattr(
        o.GAP,
        "record_pending_gap",
        lambda *, snapshot: {
            "action": "TERMINAL_EVIDENCE_RECORDED",
            "capture_slot_released": False,
        },
    )

    result = o.execute(
        acquire=lambda: object(),
        verify_snapshot=lambda _: None,
    )

    assert result["action"] == (
        "SESSION_GAP_EVIDENCE_RECORDED"
    )

    assert result["outcome_matured"] is False
    assert result["capture_slot_released"] is False


def test_duplicate_evidence_is_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_action(
        monkeypatch,
        o.LANE.MATURE,
    )

    def raise_gap(*, snapshot: Any) -> Any:
        raise o.MATURER.R03OutcomeMaturationError(
            "LAST_FUTURE_M5_BAR_NOT_CONTIGUOUS"
        )

    monkeypatch.setattr(
        o.LANE,
        "mature_from_snapshot",
        raise_gap,
    )

    monkeypatch.setattr(
        o.GAP,
        "record_pending_gap",
        lambda *, snapshot: {
            "action": "TERMINAL_EVIDENCE_ALREADY_PRESENT",
            "capture_slot_released": False,
        },
    )

    result = o.execute(
        acquire=lambda: object(),
        verify_snapshot=lambda _: None,
    )

    assert result["action"] == (
        "SESSION_GAP_EVIDENCE_ALREADY_PRESENT"
    )


def test_unrelated_maturer_error_not_swallowed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_action(
        monkeypatch,
        o.LANE.MATURE,
    )

    def raise_unrelated(*, snapshot: Any) -> Any:
        raise o.MATURER.R03OutcomeMaturationError(
            "ANCHOR_ARTIFACT_AUTHORITY_MISMATCH"
        )

    monkeypatch.setattr(
        o.LANE,
        "mature_from_snapshot",
        raise_unrelated,
    )

    monkeypatch.setattr(
        o.GAP,
        "record_pending_gap",
        lambda *, snapshot: pytest.fail(
            "GAP_RECORDING_MUST_NOT_RUN"
        ),
    )

    with pytest.raises(
        o.MATURER.R03OutcomeMaturationError,
        match="ANCHOR_ARTIFACT_AUTHORITY_MISMATCH",
    ):
        o.run_cycle(
            acquire=lambda: object(),
            verify_snapshot=lambda _: None,
        )


def test_gap_requires_independent_corroboration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_action(
        monkeypatch,
        o.LANE.MATURE,
    )

    def raise_gap(*, snapshot: Any) -> Any:
        raise o.MATURER.R03OutcomeMaturationError(
            "LAST_FUTURE_M5_BAR_NOT_CONTIGUOUS"
        )

    monkeypatch.setattr(
        o.LANE,
        "mature_from_snapshot",
        raise_gap,
    )

    monkeypatch.setattr(
        o.GAP,
        "record_pending_gap",
        lambda *, snapshot: {
            "action": "STRICT_M5_HORIZON_COMPLETE",
            "capture_slot_released": False,
        },
    )

    with pytest.raises(
        o.OrchestratorError,
        match="FROZEN_MATURER_GAP_NOT_CORROBORATED",
    ):
        o.run_cycle(
            acquire=lambda: object(),
            verify_snapshot=lambda _: None,
        )


def test_gap_cannot_release_capture_slot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_action(
        monkeypatch,
        o.LANE.MATURE,
    )

    def raise_gap(*, snapshot: Any) -> Any:
        raise o.MATURER.R03OutcomeMaturationError(
            "FUTURE_M5_HORIZON_HAS_GAP"
        )

    monkeypatch.setattr(
        o.LANE,
        "mature_from_snapshot",
        raise_gap,
    )

    monkeypatch.setattr(
        o.GAP,
        "record_pending_gap",
        lambda *, snapshot: {
            "action": "TERMINAL_EVIDENCE_RECORDED",
            "capture_slot_released": True,
        },
    )

    with pytest.raises(
        o.OrchestratorError,
        match="UNAUTHORIZED_SLOT_RELEASE",
    ):
        o.run_cycle(
            acquire=lambda: object(),
            verify_snapshot=lambda _: None,
        )


def test_trade_result_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    configure_action(
        monkeypatch,
        o.LANE.CAPTURE,
    )

    monkeypatch.setattr(
        o.LANE,
        "capture_from_snapshot",
        lambda **_: {
            "action": "EXECUTED_TRADE"
        },
    )

    with pytest.raises(
        o.OrchestratorError,
        match="UNEXPECTED_COLLECTION_RESULT",
    ):
        o.run_cycle(
            acquire=lambda: object(),
            features=lambda _: object(),
            verify_snapshot=lambda _: None,
        )
