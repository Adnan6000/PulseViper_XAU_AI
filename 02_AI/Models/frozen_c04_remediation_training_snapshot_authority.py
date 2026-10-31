from __future__ import annotations

import hashlib
import json
from typing import Any


CONTRACT_ID = (
    "FROZEN_C04_REMEDIATION_TRAINING_SNAPSHOT_AUTHORITY_V1"
)

SCHEMA_VERSION = "1.0.0"

BASE_AUTHORITY_COMMIT = (
    "5ab1fdbe822e0e1f723f2a6a5f75da3544233f09"
)

G7B_CONTRACT_FINGERPRINT_SHA256 = (
    "5e1d643c9a65d5709593bf7e3163895cc087ffb18eb0330ae0e80886d4fae0f3"
)

RESEARCH_DATA_CUTOFF_UTC = (
    "2026-08-14T20:55:00Z"
)


# ---------------------------------------------------------------------------
# Frozen historical artifact identity
# ---------------------------------------------------------------------------

DATASET_ID = (
    "portable_cff75b0686383a3ab6f8352b"
)

DATASET_SHA256 = (
    "cff75b0686383a3ab6f8352bfcdcd55308b99b7a4c6edbf7d2e7215f6f33dd07"
)

MANIFEST_SHA256 = (
    "1b8e3599b227c9cbbc6b12f8ab0e275ca4deb4a65839fb626ca90720d59512dc"
)

FEATURE_COLUMNS_SHA256 = (
    "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
)

FEATURE_COUNT = 331

TRAINING_CONTRACT_VERSION = (
    "XAUUSD_MTF_PORTABLE_FEATURE_V1"
)

SOURCE_TRAINING_CONTRACT_VERSION = (
    "XAUUSD_MTF_TRAINING_V3"
)

SOURCE_DATASET_ID = (
    "train_66ff363d25d8143d4e2c3410"
)

SOURCE_DATASET_SHA256 = (
    "66ff363d25d8143d4e2c3410964ad26b5bd72f2e98806c3e0997ce420d18413d"
)

SOURCE_MANIFEST_SHA256 = (
    "a205403a6cb5a2d1b17159a2296d1f4afb01ea5b9b90b2710feafa7dd9476aa3"
)


# ---------------------------------------------------------------------------
# Frozen split authority
# ---------------------------------------------------------------------------

TOTAL_ROWS = 99945

TRAIN_ROWS = 69966

VALIDATION_ROWS = 14983

TEST_ROWS = 14996

EXPECTED_SPLIT_COUNTS: dict[str, int] = {
    "TRAIN": TRAIN_ROWS,
    "VALIDATION": VALIDATION_ROWS,
    "TEST": TEST_ROWS,
}

SPLIT_POLICY = (
    "PURGED_CHRONOLOGICAL_TRAIN_VALIDATION_TEST"
)

TRAIN_IS_CONTIGUOUS_PREFIX = True

TRAINING_DATA_MUST_NOT_EXTEND_PAST_RESEARCH_CUTOFF = True


# ---------------------------------------------------------------------------
# Target authority
# ---------------------------------------------------------------------------

TARGET_CONTRACT = (
    "CLEAN_DIRECTIONAL_EXCURSION_V2"
)

TARGET_PROFIT_ATR = 1.25

TARGET_MAX_ADVERSE_ATR = 0.75

TARGET_CLASS_ORDER: tuple[int, ...] = (
    -1,
    0,
    1,
)


# ---------------------------------------------------------------------------
# Scientific access policy
# ---------------------------------------------------------------------------

TRAIN_MAY_BE_USED_FOR_FITTING = True

VALIDATION_MAY_BE_USED_FOR_RESEARCH_SELECTION = True

TEST_MAY_BE_USED_BEFORE_CANDIDATE_FREEZE = False

TEST_MAY_SELECT_MODEL = False

TEST_MAY_SELECT_FEATURES = False

TEST_MAY_SELECT_HYPERPARAMETERS = False

TEST_MAY_SELECT_THRESHOLDS = False

TEST_MAY_SELECT_CALIBRATION = False

FORWARD_30_MAY_BE_JOINED_TO_DATASET = False

FORWARD_30_MAY_BE_USED_FOR_TRAINING = False

FORWARD_30_MAY_BE_USED_FOR_SELECTION = False

FUTURE_FORWARD_DATA_MAY_BE_JOINED_TO_DATASET = False


# ---------------------------------------------------------------------------
# Current gate behavior
# ---------------------------------------------------------------------------

THIS_GATE_DISCOVERS_LOCAL_ARTIFACT = True

THIS_GATE_VERIFIES_DATASET_HASH = True

THIS_GATE_VERIFIES_MANIFEST_HASH = True

THIS_GATE_READS_ONLY_SPLIT_AND_DECISION_TIME_COLUMNS = True

THIS_GATE_READS_MODEL_FEATURE_VALUES = False

THIS_GATE_READS_TARGET_VALUES = False

THIS_GATE_TRAINS_MODEL = False

THIS_GATE_FITS_PREPROCESSOR = False

THIS_GATE_SELECTS_MODEL = False

THIS_GATE_SELECTS_FEATURES = False

THIS_GATE_TUNES_HYPERPARAMETERS = False

THIS_GATE_TUNES_THRESHOLDS = False

THIS_GATE_CALIBRATES_PROBABILITIES = False

THIS_GATE_EVALUATES_VALIDATION = False

THIS_GATE_EVALUATES_TEST = False

THIS_GATE_WRITES_RUNTIME_LEDGERS = False

THIS_GATE_ACQUIRES_MARKET_DATA = False

THIS_GATE_EVALUATES_PNL = False

LIVE_AUTHORIZED = False

EXECUTION_AUTHORIZED = False


def canonical_contract_dict() -> dict[str, Any]:

    return {
        "contract_id": CONTRACT_ID,
        "schema_version": SCHEMA_VERSION,
        "base_authority_commit": BASE_AUTHORITY_COMMIT,
        "g7b_contract_fingerprint_sha256": (
            G7B_CONTRACT_FINGERPRINT_SHA256
        ),
        "research_data_cutoff_utc": RESEARCH_DATA_CUTOFF_UTC,
        "dataset_id": DATASET_ID,
        "dataset_sha256": DATASET_SHA256,
        "manifest_sha256": MANIFEST_SHA256,
        "feature_columns_sha256": FEATURE_COLUMNS_SHA256,
        "feature_count": FEATURE_COUNT,
        "training_contract_version": TRAINING_CONTRACT_VERSION,
        "source_training_contract_version": (
            SOURCE_TRAINING_CONTRACT_VERSION
        ),
        "source_dataset_id": SOURCE_DATASET_ID,
        "source_dataset_sha256": SOURCE_DATASET_SHA256,
        "source_manifest_sha256": SOURCE_MANIFEST_SHA256,
        "total_rows": TOTAL_ROWS,
        "train_rows": TRAIN_ROWS,
        "validation_rows": VALIDATION_ROWS,
        "test_rows": TEST_ROWS,
        "expected_split_counts": EXPECTED_SPLIT_COUNTS,
        "split_policy": SPLIT_POLICY,
        "train_is_contiguous_prefix": TRAIN_IS_CONTIGUOUS_PREFIX,
        "training_data_must_not_extend_past_research_cutoff": (
            TRAINING_DATA_MUST_NOT_EXTEND_PAST_RESEARCH_CUTOFF
        ),
        "target_contract": TARGET_CONTRACT,
        "target_profit_atr": TARGET_PROFIT_ATR,
        "target_max_adverse_atr": TARGET_MAX_ADVERSE_ATR,
        "target_class_order": list(TARGET_CLASS_ORDER),
        "train_may_be_used_for_fitting": TRAIN_MAY_BE_USED_FOR_FITTING,
        "validation_may_be_used_for_research_selection": (
            VALIDATION_MAY_BE_USED_FOR_RESEARCH_SELECTION
        ),
        "test_may_be_used_before_candidate_freeze": (
            TEST_MAY_BE_USED_BEFORE_CANDIDATE_FREEZE
        ),
        "test_may_select_model": TEST_MAY_SELECT_MODEL,
        "test_may_select_features": TEST_MAY_SELECT_FEATURES,
        "test_may_select_hyperparameters": (
            TEST_MAY_SELECT_HYPERPARAMETERS
        ),
        "test_may_select_thresholds": TEST_MAY_SELECT_THRESHOLDS,
        "test_may_select_calibration": TEST_MAY_SELECT_CALIBRATION,
        "forward_30_may_be_joined_to_dataset": (
            FORWARD_30_MAY_BE_JOINED_TO_DATASET
        ),
        "forward_30_may_be_used_for_training": (
            FORWARD_30_MAY_BE_USED_FOR_TRAINING
        ),
        "forward_30_may_be_used_for_selection": (
            FORWARD_30_MAY_BE_USED_FOR_SELECTION
        ),
        "future_forward_data_may_be_joined_to_dataset": (
            FUTURE_FORWARD_DATA_MAY_BE_JOINED_TO_DATASET
        ),
        "this_gate_discovers_local_artifact": (
            THIS_GATE_DISCOVERS_LOCAL_ARTIFACT
        ),
        "this_gate_verifies_dataset_hash": (
            THIS_GATE_VERIFIES_DATASET_HASH
        ),
        "this_gate_verifies_manifest_hash": (
            THIS_GATE_VERIFIES_MANIFEST_HASH
        ),
        "this_gate_reads_only_split_and_decision_time_columns": (
            THIS_GATE_READS_ONLY_SPLIT_AND_DECISION_TIME_COLUMNS
        ),
        "this_gate_reads_model_feature_values": (
            THIS_GATE_READS_MODEL_FEATURE_VALUES
        ),
        "this_gate_reads_target_values": THIS_GATE_READS_TARGET_VALUES,
        "this_gate_trains_model": THIS_GATE_TRAINS_MODEL,
        "this_gate_fits_preprocessor": THIS_GATE_FITS_PREPROCESSOR,
        "this_gate_selects_model": THIS_GATE_SELECTS_MODEL,
        "this_gate_selects_features": THIS_GATE_SELECTS_FEATURES,
        "this_gate_tunes_hyperparameters": (
            THIS_GATE_TUNES_HYPERPARAMETERS
        ),
        "this_gate_tunes_thresholds": THIS_GATE_TUNES_THRESHOLDS,
        "this_gate_calibrates_probabilities": (
            THIS_GATE_CALIBRATES_PROBABILITIES
        ),
        "this_gate_evaluates_validation": (
            THIS_GATE_EVALUATES_VALIDATION
        ),
        "this_gate_evaluates_test": THIS_GATE_EVALUATES_TEST,
        "this_gate_writes_runtime_ledgers": (
            THIS_GATE_WRITES_RUNTIME_LEDGERS
        ),
        "this_gate_acquires_market_data": THIS_GATE_ACQUIRES_MARKET_DATA,
        "this_gate_evaluates_pnl": THIS_GATE_EVALUATES_PNL,
        "live_authorized": LIVE_AUTHORIZED,
        "execution_authorized": EXECUTION_AUTHORIZED,
    }


def contract_fingerprint_sha256() -> str:

    payload = json.dumps(
        canonical_contract_dict(),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )

    return hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()


CONTRACT_FINGERPRINT_SHA256 = (
    contract_fingerprint_sha256()
)