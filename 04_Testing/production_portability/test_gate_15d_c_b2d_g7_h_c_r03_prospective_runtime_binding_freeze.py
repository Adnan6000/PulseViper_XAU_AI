from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from typing import Any

import numpy as np


RUNNER_PATH = (
    Path(__file__)
    .resolve()
    .parent
    /
    "run_xauusd_gate_15d_c_b2d_g7_h_c_r03_prospective_runtime_binding_freeze.py"
)


spec = importlib.util.spec_from_file_location(
    "g7hc",
    RUNNER_PATH,
)

assert spec is not None
assert spec.loader is not None

g7hc: Any = (
    importlib.util.module_from_spec(
        spec
    )
)

spec.loader.exec_module(
    g7hc
)


runtime: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_r03_prospective_runtime"
)

contract: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_r03_prospective_forward_validation_contract"
)


def test_01_base_authority_exact() -> None:

    assert (
        g7hc.BASE_AUTHORITY_COMMIT
        ==
        "22f1ca6d0da30131ec5c9f0ce44ac46d03b82da4"
    )


def test_02_artifact_hash_exact() -> None:

    assert (
        runtime.ARTIFACT_SHA256
        ==
        "b5da550921ef227b847207cfbfe5774e86f083f1d3354069a9624a5029ea2a03"
    )


def test_03_manifest_hash_exact() -> None:

    assert (
        runtime.MANIFEST_SHA256
        ==
        "a1507666518e3289b0678525c0808fc91b45d54105ef1fb59f3c22fe5d52baf6"
    )


def test_04_prospective_contract_linkage() -> None:

    assert (
        runtime.PROSPECTIVE_CONTRACT_FINGERPRINT_SHA256
        ==
        contract.CONTRACT_FINGERPRINT_SHA256
    )


def test_05_feature_hash_exact() -> None:

    assert (
        runtime.FEATURE_COLUMNS_SHA256
        ==
        "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
    )


def test_06_feature_count_exact() -> None:

    assert (
        runtime.FEATURE_COUNT
        ==
        331
    )


def test_07_class_order_exact() -> None:

    assert (
        runtime.CLASS_ORDER
        ==
        (
            -1,
            0,
            1,
        )
    )


def test_08_artifact_adapter_loads() -> None:

    adapter = (
        runtime
        .R03FrozenArtifactInferenceAdapter()
    )

    assert (
        adapter.artifact_sha256
        ==
        runtime.ARTIFACT_SHA256
    )


def test_09_artifact_feature_order_331() -> None:

    adapter = (
        runtime
        .R03FrozenArtifactInferenceAdapter()
    )

    assert (
        len(
            adapter.feature_columns
        )
        ==
        331
    )


def test_10_artifact_smoke_inference() -> None:

    adapter = (
        runtime
        .R03FrozenArtifactInferenceAdapter()
    )

    result = adapter.infer_single(
        np.zeros(
            331,
            dtype=np.float64,
        )
    )

    total = (
        result.probability_short
        +
        result.probability_no_trade
        +
        result.probability_long
    )

    assert np.isclose(
        total,
        1.0,
    )

    assert (
        result.predicted_class
        in
        {
            -1,
            0,
            1,
        }
    )


def test_11_runtime_never_trains_model() -> None:

    text = Path(
        runtime.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert ".fit(" not in text


def test_12_runtime_never_accesses_test() -> None:

    text = Path(
        runtime.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert "load_test" not in text
    assert "TEST_ROWS" not in text


def test_13_runtime_never_accesses_validation() -> None:

    text = Path(
        runtime.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert "load_validation" not in text


def test_14_freshness_boundary_exact() -> None:

    assert (
        runtime.EARLIEST_PROSPECTIVE_AUTHORITY_TIME_UTC
        ==
        "2026-10-03T04:32:41Z"
    )


def test_15_boundary_time_rejected() -> None:

    try:

        runtime.enforce_prospective_freshness(
            "2026-10-03T04:32:41Z"
        )

    except runtime.ProspectiveFreshnessError:

        return

    raise AssertionError(
        "boundary decision time was accepted"
    )


def test_16_post_boundary_time_accepted() -> None:

    runtime.enforce_prospective_freshness(
        "2026-10-03T04:32:42Z"
    )


def test_17_dedicated_observation_ledger() -> None:

    assert (
        runtime.OBSERVATION_LEDGER_RELATIVE_PATH
        ==
        "01_Data/Shadow/xauusd_r03_prospective_observations.jsonl"
    )


def test_18_dedicated_anchor_ledger() -> None:

    assert (
        runtime.ANCHOR_LEDGER_RELATIVE_PATH
        ==
        "01_Data/Shadow/xauusd_r03_prospective_forward_outcome_anchors.jsonl"
    )


def test_19_dedicated_outcome_ledger_reserved() -> None:

    assert (
        runtime.OUTCOME_LEDGER_RELATIVE_PATH
        ==
        "01_Data/Shadow/xauusd_r03_prospective_forward_outcomes.jsonl"
    )


def test_20_old_c04_paths_not_reused() -> None:

    assert (
        "frozen_c04"
        not in
        runtime.OBSERVATION_LEDGER_RELATIVE_PATH
    )

    assert (
        "frozen_c04"
        not in
        runtime.ANCHOR_LEDGER_RELATIVE_PATH
    )


def test_21_acquisition_verification_is_separate_from_r03_model() -> None:

    text = Path(
        runtime.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "expected_model_sha256=("
        in text
    )

    assert (
        "_acquisition.FROZEN_MODEL_SHA256"
        in text
    )

    assert (
        "ARTIFACT_SHA256"
        in text
    )


def test_22_observation_identity_includes_r03_artifact() -> None:

    first = (
        runtime
        .compute_observation_logical_id(
            decision_time_utc=(
                "2026-10-05T10:05:00Z"
            )
        )
    )

    second = (
        runtime
        .compute_observation_logical_id(
            decision_time_utc=(
                "2026-10-05T10:10:00Z"
            )
        )
    )

    assert first != second
    assert len(first) == 64


def test_23_observation_validator_requires_r03_artifact() -> None:

    text = Path(
        runtime.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "OBSERVATION_ARTIFACT_HASH_MISMATCH"
        in text
    )


def test_24_anchor_requires_r03_artifact() -> None:

    text = Path(
        runtime.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "ANCHOR_ARTIFACT_HASH_MISMATCH"
        in text
    )


def test_25_anchor_requires_outcome_contract() -> None:

    assert (
        runtime.FORWARD_OUTCOME_CONTRACT_FINGERPRINT_SHA256
        ==
        "01fe52a2f068fcc8fb2fc5b89dd7e19dc974fc2d967cfb791e75c3415804ce87"
    )


def test_26_anchor_first_persistence_frozen() -> None:

    text = Path(
        runtime.__file__
    ).read_text(
        encoding="utf-8"
    )

    anchor_position = text.index(
        "anchor_ledger.append("
    )

    observation_position = text.index(
        "observation_ledger.append("
    )

    assert (
        anchor_position
        <
        observation_position
    )


def test_27_orphan_anchor_preserved_on_observation_failure() -> None:

    text = Path(
        runtime.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "OBSERVATION_APPEND_FAILED_AFTER_ANCHOR_PRESERVED"
        in text
    )


def test_28_atomic_append_uses_lock() -> None:

    text = Path(
        runtime.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "with file_lock("
        in text
    )


def test_29_atomic_append_uses_fsync() -> None:

    text = Path(
        runtime.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "os.fsync("
        in text
    )


def test_30_idempotent_duplicate_supported() -> None:

    text = Path(
        runtime.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "is_duplicate=True"
        in text
    )


def test_31_conflicting_duplicate_blocked() -> None:

    text = Path(
        runtime.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "LEDGER_APPEND_CONFLICT"
        in text
    )


def test_32_gate_does_not_load_market_data() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert "MetaTrader5" not in text
    assert "acquire_snapshot(" not in text


def test_33_gate_does_not_write_runtime_ledgers() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "prospective_ledgers_written"
        in text
    )

    assert (
        '"prospective_ledgers_written": False'
        in text
    )


def test_34_no_performance_evaluation() -> None:

    assert (
        runtime.PERFORMANCE_EVALUATION_AUTHORIZED
        is False
    )


def test_35_no_pnl_evaluation() -> None:

    assert (
        runtime.PNL_EVALUATION_AUTHORIZED
        is False
    )


def test_36_live_blocked() -> None:

    assert (
        runtime.LIVE_AUTHORIZED
        is False
    )


def test_37_execution_blocked() -> None:

    assert (
        runtime.EXECUTION_AUTHORIZED
        is False
    )


def test_38_outcome_maturation_not_implemented_here() -> None:

    text = Path(
        runtime.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert "mature_outcome" not in text
    assert "OUTCOME_CLASS" not in text


def test_39_current_gate_only_freezes_binding() -> None:

    assert (
        runtime.RUNTIME_VERSION
        ==
        "FROZEN_R03_PROSPECTIVE_RUNTIME_V1"
    )


def test_40_runner_base_is_latest_artifact_commit() -> None:

    assert (
        g7hc.BASE_AUTHORITY_COMMIT
        ==
        "22f1ca6d0da30131ec5c9f0ce44ac46d03b82da4"
    )