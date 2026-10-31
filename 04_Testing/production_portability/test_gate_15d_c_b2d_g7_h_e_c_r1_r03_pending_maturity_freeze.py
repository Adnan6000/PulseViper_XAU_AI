from __future__ import annotations

from pathlib import Path


ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

HERE = (
    Path(__file__)
    .resolve()
    .parent
)

RUNNER = (
    HERE
    /
    "run_xauusd_gate_15d_c_b2d_g7_h_e_c_r1_r03_pending_maturity.py"
)

FREEZE = (
    HERE
    /
    "run_xauusd_gate_15d_c_b2d_g7_h_e_c_r1_r03_pending_maturity_freeze.py"
)


def runner_text() -> str:

    return RUNNER.read_text(
        encoding="utf-8"
    )


def freeze_text() -> str:

    return FREEZE.read_text(
        encoding="utf-8"
    )


def test_01_runner_exists() -> None:
    assert RUNNER.is_file()


def test_02_freeze_exists() -> None:
    assert FREEZE.is_file()


def test_03_base_commit_exact() -> None:
    assert (
        "2ad29322d7032e2ba11cba984554788ae5975ab8"
        in
        freeze_text()
    )


def test_04_read_only_facade() -> None:
    assert (
        "MT5ReadOnlyCapabilityFacade"
        in
        runner_text()
    )


def test_05_read_only_adapter() -> None:
    assert (
        "MT5ReadOnlyForwardAcquisitionAdapter"
        in
        runner_text()
    )


def test_06_auto_timestamp_basis() -> None:
    assert (
        'timestamp_basis="AUTO"'
        in
        runner_text()
    )


def test_07_forward_boundaries() -> None:
    assert (
        "enforce_forward_boundaries=True"
        in
        runner_text()
    )


def test_08_controller_maturation() -> None:
    assert (
        "mature_pending_from_snapshot"
        in
        runner_text()
    )


def test_09_wait_action_supported() -> None:
    assert (
        "WAIT_FOR_MORE_COMPLETED_M5_BARS"
        in
        runner_text()
    )


def test_10_matured_action_supported() -> None:
    assert (
        "MATURED_PENDING_OUTCOME"
        in
        runner_text()
    )


def test_11_no_new_capture() -> None:
    assert (
        "capture_new_observation_from_snapshot("
        not in
        runner_text()
    )


def test_12_no_feature_pipeline() -> None:
    assert (
        "PortableFeaturePipeline("
        not in
        runner_text()
    )


def test_13_no_model_fit() -> None:
    assert ".fit(" not in runner_text()


def test_14_no_test_access() -> None:
    assert "load_test(" not in runner_text()


def test_15_no_validation_access() -> None:
    assert "load_validation(" not in runner_text()


def test_16_no_order_send() -> None:
    assert "order_send(" not in runner_text()


def test_17_no_order_check() -> None:
    assert "order_check(" not in runner_text()


def test_18_no_risk_engine() -> None:
    assert "RiskEngine(" not in runner_text()


def test_19_no_trade_ready() -> None:
    assert "trade_ready" not in runner_text()


def test_20_no_performance_eval() -> None:
    assert (
        "evaluate_prospective_confirmation("
        not in
        runner_text()
    )


def test_21_wait_does_not_append() -> None:
    assert (
        "OUTCOME_APPENDED=false"
        in
        runner_text()
    )


def test_22_pending_required() -> None:
    assert (
        "PENDING_MATURITY_NOT_AUTHORIZED"
        in
        runner_text()
    )


def test_23_exact_one_pending_required() -> None:
    assert (
        "PENDING_COUNT_NOT_ONE"
        in
        runner_text()
    )


def test_24_freeze_requires_one_observation() -> None:
    assert (
        "EXPECTED_ONE_OBSERVATION"
        in
        freeze_text()
    )


def test_25_freeze_requires_one_anchor() -> None:
    assert (
        "EXPECTED_ONE_ANCHOR"
        in
        freeze_text()
    )


def test_26_freeze_requires_zero_outcomes() -> None:
    assert (
        "EXPECTED_ZERO_OUTCOMES"
        in
        freeze_text()
    )


def test_27_freeze_requires_one_pending() -> None:
    assert (
        "EXPECTED_ONE_PENDING"
        in
        freeze_text()
    )


def test_28_freeze_no_mt5_initialize() -> None:
    assert (
        "mt5.initialize("
        not in
        freeze_text()
    )


def test_29_freeze_no_maturation_call() -> None:
    assert (
        "mature_pending_from_snapshot("
        not in
        freeze_text()
    )


def test_30_freeze_protects_ledger_hashes() -> None:
    assert (
        "FREEZE_MUTATED_RUNTIME_LEDGER"
        in
        freeze_text()
    )


def test_31_freeze_protects_state() -> None:
    assert (
        "FREEZE_CHANGED_COLLECTION_STATE"
        in
        freeze_text()
    )


def test_32_freeze_evidence_create_only() -> None:
    assert (
        'open(\n        "x"'
        in
        freeze_text()
    )


def test_33_runner_verifies_artifact_hashes() -> None:
    assert (
        "MATURITY_ARTIFACT_CHANGED"
        in
        runner_text()
    )


def test_34_performance_false() -> None:
    assert (
        "PERFORMANCE_EVALUATED=false"
        in
        runner_text()
    )


def test_35_pnl_false() -> None:
    assert (
        "PNL_EVALUATED=false"
        in
        runner_text()
    )


def test_36_live_false() -> None:
    assert (
        "LIVE_AUTHORIZED=false"
        in
        runner_text()
    )


def test_37_execution_false() -> None:
    assert (
        "EXECUTION_AUTHORIZED=false"
        in
        runner_text()
    )