from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import pytest


runner: Any = importlib.import_module(
    "04_Testing.production_portability."
    "run_xauusd_r03_session_gap_recovery_r3"
)


def test_diagnostic_version() -> None:
    assert runner.RUNNER_VERSION == (
        "R03_SESSION_GAP_RECOVERY_R3_DIAGNOSTIC_V1"
    )


def test_history_window_is_bounded() -> None:
    assert runner.HISTORY_BARS == 7000


def test_expected_pending_id_is_frozen_for_diagnostic() -> None:
    assert runner.EXPECTED_PENDING_ID == (
        "febaf847ef5cd078cfc0e8223eb2120c81969a91645998968e9a1083caa1c1f8"
    )


def test_no_ledger_or_trading_authorization() -> None:
    assert runner.LEDGER_WRITES_AUTHORIZED is False
    assert runner.TERMINAL_DISPOSITION_AUTHORIZED is False
    assert runner.PERFORMANCE_EVALUATION_AUTHORIZED is False
    assert runner.PNL_EVALUATION_AUTHORIZED is False
    assert runner.LIVE_AUTHORIZED is False
    assert runner.EXECUTION_AUTHORIZED is False


def test_runner_has_no_direct_maturation_or_append() -> None:
    source = Path(runner.__file__).read_text(
        encoding="utf-8"
    )

    forbidden_calls = (
        ".mature_pending_from_snapshot(",
        ".mature_observation(",
        ".append(",
        ".order_send(",
        ".order_check(",
    )

    for call in forbidden_calls:
        assert call not in source


def test_runner_requires_exact_pending_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:

    class FakeState:
        pending_count = 1
        next_action = "CHECK_PENDING_MATURITY"
        pending_logical_observation_id = "wrong-id"

    monkeypatch.setattr(
        runner.controller,
        "inspect_state",
        lambda **kwargs: FakeState(),
    )

    with pytest.raises(
        runner.R03RecoveryDiagnosticError,
        match="UNEXPECTED_PENDING_ID",
    ):
        runner.inspect_pending()