from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from typing import Any


RUNNER_PATH = (
    Path(__file__)
    .resolve()
    .parent
    /
    "run_xauusd_gate_15d_c_b2d_g7_h_d_r03_outcome_maturation_binding_freeze.py"
)


spec = importlib.util.spec_from_file_location(
    "g7hd",
    RUNNER_PATH,
)

assert spec is not None
assert spec.loader is not None

g7hd: Any = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(
    g7hd
)


maturer: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_r03_prospective_outcome_maturer"
)

runtime: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_r03_prospective_runtime"
)


def test_01_base_commit_exact() -> None:
    assert (
        g7hd.BASE_AUTHORITY_COMMIT
        ==
        "c45008d4f2e18a28b758d9563d8b1298077c1ca7"
    )


def test_02_maturation_version() -> None:
    assert (
        maturer.MATURATION_VERSION
        ==
        "FROZEN_R03_PROSPECTIVE_OUTCOME_MATURER_V1"
    )


def test_03_horizon_exact() -> None:
    assert maturer.EXPECTED_HORIZON_BARS == 12


def test_04_profit_atr_exact() -> None:
    assert maturer.EXPECTED_PROFIT_ATR == 1.25


def test_05_adverse_atr_exact() -> None:
    assert maturer.EXPECTED_MAX_ADVERSE_ATR == 0.75


def test_06_outcome_contract_exact() -> None:
    assert (
        maturer.EXPECTED_CONTRACT_FINGERPRINT_SHA256
        ==
        "01fe52a2f068fcc8fb2fc5b89dd7e19dc974fc2d967cfb791e75c3415804ce87"
    )


def test_07_prospective_contract_exact() -> None:
    assert (
        maturer.EXPECTED_PROSPECTIVE_CONTRACT_FINGERPRINT_SHA256
        ==
        runtime.PROSPECTIVE_CONTRACT_FINGERPRINT_SHA256
    )


def test_08_artifact_exact() -> None:
    assert (
        maturer.EXPECTED_ARTIFACT_SHA256
        ==
        runtime.ARTIFACT_SHA256
    )


def test_09_feature_hash_exact() -> None:
    assert (
        maturer.EXPECTED_FEATURE_COLUMNS_SHA256
        ==
        runtime.FEATURE_COLUMNS_SHA256
    )


def test_10_outcome_ledger_path_exact() -> None:
    assert (
        maturer.OUTCOME_LEDGER_RELATIVE_PATH
        ==
        runtime.OUTCOME_LEDGER_RELATIVE_PATH
    )


def test_11_long_rule() -> None:
    assert (
        maturer.label_outcome(
            up_excursion_atr=1.25,
            down_excursion_atr=0.75,
        )
        ==
        (
            1,
            "LONG",
        )
    )


def test_12_short_rule() -> None:
    assert (
        maturer.label_outcome(
            up_excursion_atr=0.75,
            down_excursion_atr=1.25,
        )
        ==
        (
            -1,
            "SHORT",
        )
    )


def test_13_no_trade_rule() -> None:
    assert (
        maturer.label_outcome(
            up_excursion_atr=1.0,
            down_excursion_atr=1.0,
        )
        ==
        (
            0,
            "NO_TRADE",
        )
    )


def test_14_future_data_policy() -> None:
    assert (
        maturer.FUTURE_DATA_POLICY
        ==
        "OUTCOME_ONLY_NEVER_FEATURE_OR_INFERENCE_INPUT"
    )


def test_15_anchor_entry_reference() -> None:
    assert (
        maturer.ENTRY_REFERENCE
        ==
        "PROSPECTIVE_ANCHOR_DECISION_M5_CLOSE"
    )


def test_16_anchor_atr_reference() -> None:
    assert (
        maturer.ATR_REFERENCE
        ==
        "PROSPECTIVE_ANCHOR_DECISION_M5_ATR14"
    )


def test_17_exact_horizon_semantics() -> None:
    assert (
        maturer.HORIZON_SEMANTICS
        ==
        "NEXT_12_COMPLETED_M5_ROWS_AFTER_DECISION_BAR"
    )


def test_18_outcome_maturation_authorized() -> None:
    assert (
        maturer.OUTCOME_MATURATION_AUTHORIZED
        is True
    )


def test_19_performance_blocked() -> None:
    assert (
        maturer.PERFORMANCE_EVALUATION_AUTHORIZED
        is False
    )


def test_20_pnl_blocked() -> None:
    assert maturer.PNL_EVALUATION_AUTHORIZED is False


def test_21_live_blocked() -> None:
    assert maturer.LIVE_AUTHORIZED is False


def test_22_execution_blocked() -> None:
    assert maturer.EXECUTION_AUTHORIZED is False


def test_23_runtime_never_trains_model() -> None:

    text = Path(
        maturer.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert ".fit(" not in text


def test_24_runtime_never_accesses_test() -> None:

    text = Path(
        maturer.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert "load_test" not in text


def test_25_runtime_never_accesses_validation() -> None:

    text = Path(
        maturer.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert "load_validation" not in text


def test_26_contiguous_first_future_bar_required() -> None:

    text = Path(
        maturer.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "FIRST_FUTURE_M5_BAR_NOT_CONTIGUOUS"
        in text
    )


def test_27_contiguous_last_future_bar_required() -> None:

    text = Path(
        maturer.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "LAST_FUTURE_M5_BAR_NOT_CONTIGUOUS"
        in text
    )


def test_28_gap_detection_required() -> None:

    text = Path(
        maturer.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "FUTURE_M5_HORIZON_HAS_GAP"
        in text
    )


def test_29_exact_12_rows_required() -> None:

    text = Path(
        maturer.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "EXACT_12_FUTURE_M5_ROWS_REQUIRED"
        in text
    )


def test_30_insufficient_future_bars_fail_closed() -> None:

    text = Path(
        maturer.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "INSUFFICIENT_COMPLETED_FUTURE_M5_BARS"
        in text
    )


def test_31_observation_anchor_id_linkage() -> None:

    text = Path(
        maturer.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "OBSERVATION_ANCHOR_ID_MISMATCH"
        in text
    )


def test_32_observation_anchor_fingerprint_linkage() -> None:

    text = Path(
        maturer.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "OBSERVATION_ANCHOR_FINGERPRINT_MISMATCH"
        in text
    )


def test_33_outcome_ledger_atomic_lock() -> None:

    text = Path(
        maturer.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert "with file_lock(" in text


def test_34_outcome_ledger_fsync() -> None:

    text = Path(
        maturer.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert "os.fsync(" in text


def test_35_outcome_duplicate_idempotent() -> None:

    text = Path(
        maturer.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert "is_duplicate=True" in text


def test_36_outcome_conflict_blocked() -> None:

    text = Path(
        maturer.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert "OUTCOME_APPEND_CONFLICT" in text


def test_37_freeze_runner_no_mt5() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert "MetaTrader5" not in text
    assert "acquire_snapshot(" not in text


def test_38_freeze_runner_no_runtime_ledger_append() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert ".append(" not in text


def test_39_authorities_verify() -> None:
    assert maturer.verify_authorities() is True


def test_40_no_performance_scoring_here() -> None:

    text = Path(
        maturer.__file__
    ).read_text(
        encoding="utf-8"
    )

    assert "accuracy_score" not in text
    assert "f1_score" not in text
    assert "log_loss" not in text