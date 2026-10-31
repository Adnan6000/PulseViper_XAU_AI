from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any


ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

RUNNER_PATH = (
    Path(__file__)
    .resolve()
    .parent
    /
    "run_xauusd_gate_15d_c_b2d_g7_h_e_b_r1_first_genuine_r03_capture_recovery.py"
)

FREEZE_PATH = (
    Path(__file__)
    .resolve()
    .parent
    /
    "run_xauusd_gate_15d_c_b2d_g7_h_e_b_r1_first_genuine_r03_capture_recovery_freeze.py"
)


spec = importlib.util.spec_from_file_location(
    "g7hebr1freeze",
    FREEZE_PATH,
)

assert spec is not None
assert spec.loader is not None

freeze: Any = (
    importlib.util.module_from_spec(
        spec
    )
)

spec.loader.exec_module(
    freeze
)


def runner_text() -> str:

    return RUNNER_PATH.read_text(
        encoding="utf-8"
    )


def freeze_text() -> str:

    return FREEZE_PATH.read_text(
        encoding="utf-8"
    )


def test_01_base_commit_exact() -> None:
    assert (
        freeze.BASE_AUTHORITY_COMMIT
        ==
        "212f8edec98401a12f26d6d057cdfbae17065a92"
    )


def test_02_original_blocked_evidence_required() -> None:
    assert (
        "ORIGINAL_BLOCKED_EVIDENCE_MISSING"
        in
        freeze_text()
    )


def test_03_original_failure_must_be_blocked() -> None:
    assert (
        "ORIGINAL_BLOCKED_STATUS_MISMATCH"
        in
        freeze_text()
    )


def test_04_timestamp_failure_required() -> None:
    assert (
        "TimestampBasisResolutionError"
        in
        freeze_text()
    )


def test_05_timestamp_error_signature_required() -> None:
    assert (
        "TIMESTAMP_BASIS_NOT_UNIQUELY_PROVEN"
        in
        freeze_text()
    )


def test_06_r03_ledgers_absent_before_recovery() -> None:
    assert (
        "R03_LEDGER_ALREADY_EXISTS"
        in
        freeze_text()
    )


def test_07_recovery_uses_read_only_facade() -> None:
    assert (
        "MT5ReadOnlyCapabilityFacade"
        in
        runner_text()
    )


def test_08_recovery_uses_read_only_acquisition() -> None:
    assert (
        "MT5ReadOnlyForwardAcquisitionAdapter"
        in
        runner_text()
    )


def test_09_auto_timestamp_detection_preserved() -> None:
    assert (
        'timestamp_basis="AUTO"'
        in
        runner_text()
    )


def test_10_forward_boundaries_preserved() -> None:
    assert (
        "enforce_forward_boundaries=True"
        in
        runner_text()
    )


def test_11_feature_pipeline_used() -> None:
    assert (
        "PortableFeaturePipeline"
        in
        runner_text()
    )


def test_12_r03_controller_used() -> None:
    assert (
        "capture_new_observation_from_snapshot"
        in
        runner_text()
    )


def test_13_anchor_first_preserved() -> None:
    assert (
        "ANCHOR_FIRST_THEN_OBSERVATION"
        in
        runner_text()
    )


def test_14_zero_observations_required() -> None:
    assert (
        "RECOVERY_REQUIRES_ZERO_R03_OBSERVATIONS"
        in
        runner_text()
    )


def test_15_zero_anchors_required() -> None:
    assert (
        "RECOVERY_REQUIRES_ZERO_R03_ANCHORS"
        in
        runner_text()
    )


def test_16_zero_outcomes_required() -> None:
    assert (
        "RECOVERY_REQUIRES_ZERO_R03_OUTCOMES"
        in
        runner_text()
    )


def test_17_original_failure_preserved() -> None:
    assert (
        "ORIGINAL_BLOCKED_ATTEMPT_PRESERVED=true"
        in
        runner_text()
    )


def test_18_original_evidence_hash_verified() -> None:
    assert (
        "ORIGINAL_BLOCKED_EVIDENCE_CHANGED"
        in
        runner_text()
    )


def test_19_freeze_does_not_initialize_mt5() -> None:
    assert (
        "mt5.initialize("
        not in
        freeze_text()
    )


def test_20_freeze_does_not_capture() -> None:
    assert (
        "capture_new_observation_from_snapshot("
        not in
        freeze_text()
    )


def test_21_no_order_send() -> None:
    assert "order_send(" not in runner_text()


def test_22_no_order_check() -> None:
    assert "order_check(" not in runner_text()


def test_23_no_risk_engine() -> None:
    assert "RiskEngine(" not in runner_text()


def test_24_no_trade_ready() -> None:
    assert "trade_ready" not in runner_text()


def test_25_no_fit() -> None:
    assert ".fit(" not in runner_text()


def test_26_no_test_access() -> None:
    assert "load_test(" not in runner_text()


def test_27_no_validation_access() -> None:
    assert "load_validation(" not in runner_text()


def test_28_no_maturation_in_capture() -> None:
    assert (
        "mature_pending_from_snapshot("
        not in
        runner_text()
    )


def test_29_no_performance_evaluation() -> None:
    assert (
        "evaluate_prospective_confirmation("
        not in
        runner_text()
    )


def test_30_live_blocked() -> None:
    assert (
        "LIVE_AUTHORIZED=false"
        in
        runner_text()
    )


def test_31_execution_blocked() -> None:
    assert (
        "EXECUTION_AUTHORIZED=false"
        in
        runner_text()
    )


def test_32_performance_blocked() -> None:
    assert (
        "PERFORMANCE_EVALUATED=false"
        in
        runner_text()
    )


def test_33_pnl_blocked() -> None:
    assert (
        "PNL_EVALUATED=false"
        in
        runner_text()
    )


def test_34_recovery_evidence_create_only() -> None:
    assert (
        'open(\n        "x"'
        in
        runner_text()
    )


def test_35_freeze_evidence_create_only() -> None:
    assert (
        'open(\n        "x"'
        in
        freeze_text()
    )


def test_36_published_hash_verification_required() -> None:
    assert (
        "RECOVERY_ARTIFACT_CHANGED"
        in
        runner_text()
    )