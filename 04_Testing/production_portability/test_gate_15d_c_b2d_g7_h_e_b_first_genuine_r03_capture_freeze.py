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
    "run_xauusd_gate_15d_c_b2d_g7_h_e_b_first_genuine_r03_capture.py"
)

FREEZE_PATH = (
    Path(__file__)
    .resolve()
    .parent
    /
    "run_xauusd_gate_15d_c_b2d_g7_h_e_b_first_genuine_r03_capture_freeze.py"
)


spec = importlib.util.spec_from_file_location(
    "g7hebfreeze",
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


def test_01_base_authority_exact() -> None:

    assert (
        freeze.BASE_AUTHORITY_COMMIT
        ==
        "8d29e05cc20a26730366e8d684bdd3af3fd4578f"
    )


def test_02_actual_runner_exists() -> None:

    assert RUNNER_PATH.is_file()


def test_03_read_only_capability_used() -> None:

    assert (
        "MT5ReadOnlyCapabilityFacade"
        in
        runner_text()
    )


def test_04_read_only_acquisition_used() -> None:

    assert (
        "MT5ReadOnlyForwardAcquisitionAdapter"
        in
        runner_text()
    )


def test_05_forward_boundaries_enforced() -> None:

    assert (
        "enforce_forward_boundaries=True"
        in
        runner_text()
    )


def test_06_genuine_snapshot_required() -> None:

    assert (
        "SNAPSHOT_NOT_GENUINE"
        in
        runner_text()
    )


def test_07_feature_pipeline_used() -> None:

    assert (
        "PortableFeaturePipeline"
        in
        runner_text()
    )


def test_08_r03_controller_used() -> None:

    assert (
        "capture_new_observation_from_snapshot"
        in
        runner_text()
    )


def test_09_anchor_first_semantics_present() -> None:

    assert (
        "ANCHOR_FIRST_THEN_OBSERVATION"
        in
        runner_text()
    )


def test_10_zero_observation_required() -> None:

    assert (
        "FIRST_CAPTURE_REQUIRES_ZERO_R03_OBSERVATIONS"
        in
        runner_text()
    )


def test_11_zero_anchor_required() -> None:

    assert (
        "FIRST_CAPTURE_REQUIRES_ZERO_R03_ANCHORS"
        in
        runner_text()
    )


def test_12_zero_outcome_required() -> None:

    assert (
        "FIRST_CAPTURE_REQUIRES_ZERO_R03_OUTCOMES"
        in
        runner_text()
    )


def test_13_post_capture_one_observation() -> None:

    assert (
        "POST_CAPTURE_OBSERVATION_COUNT_NOT_ONE"
        in
        runner_text()
    )


def test_14_post_capture_one_anchor() -> None:

    assert (
        "POST_CAPTURE_ANCHOR_COUNT_NOT_ONE"
        in
        runner_text()
    )


def test_15_post_capture_pending_one() -> None:

    assert (
        "POST_CAPTURE_PENDING_COUNT_NOT_ONE"
        in
        runner_text()
    )


def test_16_no_outcome_maturation() -> None:

    assert (
        "mature_pending_from_snapshot("
        not in
        runner_text()
    )


def test_17_no_prospective_evaluation() -> None:

    assert (
        "evaluate_prospective_confirmation("
        not in
        runner_text()
    )


def test_18_no_model_fit() -> None:

    assert ".fit(" not in runner_text()


def test_19_no_test_partition() -> None:

    assert "load_test(" not in runner_text()


def test_20_no_validation_partition() -> None:

    assert "load_validation(" not in runner_text()


def test_21_no_order_send() -> None:

    assert "order_send(" not in runner_text()


def test_22_no_order_check() -> None:

    assert "order_check(" not in runner_text()


def test_23_no_risk_engine() -> None:

    assert "RiskEngine(" not in runner_text()


def test_24_no_trade_ready() -> None:

    assert "trade_ready" not in runner_text()


def test_25_live_blocked() -> None:

    assert (
        "LIVE_AUTHORIZED=false"
        in
        runner_text()
    )


def test_26_execution_blocked() -> None:

    assert (
        "EXECUTION_AUTHORIZED=false"
        in
        runner_text()
    )


def test_27_performance_blocked() -> None:

    assert (
        "PERFORMANCE_EVALUATED=false"
        in
        runner_text()
    )


def test_28_pnl_blocked() -> None:

    assert (
        "PNL_EVALUATED=false"
        in
        runner_text()
    )


def test_29_freeze_does_not_initialize_mt5() -> None:

    assert "mt5.initialize(" not in freeze_text()


def test_30_freeze_does_not_capture() -> None:

    assert (
        "capture_new_observation_from_snapshot("
        not in
        freeze_text()
    )


def test_31_freeze_preserves_ledgers() -> None:

    assert (
        "LEDGER_CHANGED_DURING_RUNNER_FREEZE"
        in
        freeze_text()
    )


def test_32_freeze_create_only_evidence() -> None:

    assert (
        'open(\n        "x"'
        in
        freeze_text()
    )


def test_33_runner_verifies_freeze_evidence() -> None:

    assert (
        "verify_freeze_authority()"
        in
        runner_text()
    )


def test_34_runner_verifies_published_hashes() -> None:

    assert (
        "PUBLISHED_CAPTURE_ARTIFACT_CHANGED"
        in
        runner_text()
    )


def test_35_runner_requires_head_origin_parity() -> None:

    assert (
        "HEAD_ORIGIN_MAIN_DIVERGENCE"
        in
        runner_text()
    )


def test_36_first_capture_evidence_create_only() -> None:

    assert (
        'open(\n        "x"'
        in
        runner_text()
    )