from __future__ import annotations

import hashlib
import json
from typing import Any


CONTRACT_ID = (
    "FROZEN_C04_REMEDIATION_TRAIN_VALIDATION_ACCESS_CONTRACT_V1"
)

SCHEMA_VERSION = "1.0.0"

BASE_AUTHORITY_COMMIT = (
    "b650eff40e191b154c3055caadd9159e0eb0812a"
)

G7E_REGISTRY_VERSION = (
    "XAUUSD_REMEDIATION_CANDIDATE_REGISTRY_V1"
)

G7E_REGISTRY_FINGERPRINT_SHA256 = (
    "4556eb982086da0ea19ab910a30b5ab58788c7e5b7488ef8e3453e46289c0deb"
)

G7D_CONTRACT_FINGERPRINT_SHA256 = (
    "c6270f03fed45ba749d40ea4c556b95e683ad934575c9dc958664bef83f86638"
)

G7C_CONTRACT_FINGERPRINT_SHA256 = (
    "11302c424f05aab2fbd640d644b30d3df0b013d3b9e1b559b29e325ee2f99b50"
)

G7B_CONTRACT_FINGERPRINT_SHA256 = (
    "5e1d643c9a65d5709593bf7e3163895cc087ffb18eb0330ae0e80886d4fae0f3"
)


# =============================================================================
# Frozen dataset
# =============================================================================

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

TOTAL_ROWS = 99945

TRAIN_ROWS = 69966

VALIDATION_ROWS = 14983

TEST_ROWS = 14996


# =============================================================================
# Target
# =============================================================================

TARGET_CONTRACT = (
    "CLEAN_DIRECTIONAL_EXCURSION_V2"
)

TARGET_CLASS_ORDER = (
    -1,
    0,
    1,
)

TARGET_COLUMNS = (
    "target_class",
    "target_tradeable",
)


# =============================================================================
# Split authority
# =============================================================================

TRAIN_ROLE = (
    "MODEL_AND_PREPROCESSOR_FIT"
)

VALIDATION_ROLE = (
    "REMEDIATION_CANDIDATE_SELECTION"
)

TEST_ROLE = (
    "SEALED_ONE_SHOT_FINAL_OFFLINE_CONFIRMATION"
)

TRAIN_FEATURE_ACCESS_AUTHORIZED = True

TRAIN_TARGET_ACCESS_AUTHORIZED = True

VALIDATION_FEATURE_ACCESS_AUTHORIZED = True

VALIDATION_TARGET_ACCESS_AUTHORIZED = True

TEST_FEATURE_ACCESS_AUTHORIZED = False

TEST_TARGET_ACCESS_AUTHORIZED = False

TEST_STRUCTURAL_SPLIT_INSPECTION_ONLY = True


# =============================================================================
# Historical validation audit distinction
# =============================================================================

HISTORICAL_VALIDATION_LEDGER_VERSION = (
    "XAUUSD_PORTABLE_331_ONE_TIME_VALIDATION_ACCESS_LEDGER_V1"
)

HISTORICAL_VALIDATION_STATUS = (
    "VALIDATION_COMPLETE_ACCEPTED"
)

HISTORICAL_VALIDATION_WAS_FOR_OLD_C04_CYCLE = True

HISTORICAL_VALIDATION_LEDGER_MAY_BE_REWRITTEN = False

HISTORICAL_VALIDATION_LEDGER_MAY_BE_RESET = False

HISTORICAL_VALIDATION_LEDGER_GOVERNS_REMEDIATION_ACCESS = False

REMEDIATION_VALIDATION_AUTHORITY_SOURCE = (
    "G7B_G7D_G7E_REMEDIATION_PROTOCOL"
)


# =============================================================================
# Loader rules
# =============================================================================

LOADER_VERSION = "1.0"

VALIDATION_MUST_BE_EXACT_CONTIGUOUS_SPLIT = True

TRAIN_MUST_REMAIN_EXACT_CONTIGUOUS_PREFIX = True

TEST_VALUES_MUST_NOT_BE_READ = True

VALIDATION_READ_MUST_STOP_BEFORE_TEST = True

ALL_ARRAYS_READ_ONLY = True

DECISION_TIME_ALIGNMENT_REQUIRED = True

NO_DUPLICATE_DECISION_TIME_ALLOWED = True

NO_SHUFFLE_ALLOWED = True

NO_MODEL_FIT_IN_LOADER = True

NO_PREPROCESSOR_FIT_IN_LOADER = True

NO_METRICS_IN_LOADER = True

NO_ARTIFACT_WRITE_IN_LOADER = True


# =============================================================================
# G7-F-A current gate
# =============================================================================

THIS_GATE_IMPLEMENTATION_FREEZE_ONLY = True

THIS_GATE_LOADS_TRAIN_VALUES = False

THIS_GATE_LOADS_VALIDATION_VALUES = False

THIS_GATE_LOADS_TEST_VALUES = False

THIS_GATE_TRAINS_MODELS = False

THIS_GATE_FITS_PREPROCESSORS = False

THIS_GATE_EVALUATES_CANDIDATES = False

THIS_GATE_SELECTS_WINNER = False

THIS_GATE_EVALUATES_TEST = False

THIS_GATE_EVALUATES_PNL = False

THIS_GATE_ACQUIRES_MARKET_DATA = False

THIS_GATE_WRITES_RUNTIME_LEDGERS = False

LIVE_AUTHORIZED = False

EXECUTION_AUTHORIZED = False


def canonical_contract_dict() -> dict[str, Any]:

    return {
        "contract_id": CONTRACT_ID,
        "schema_version": SCHEMA_VERSION,
        "base_authority_commit": BASE_AUTHORITY_COMMIT,
        "g7e_registry_version": G7E_REGISTRY_VERSION,
        "g7e_registry_fingerprint_sha256": (
            G7E_REGISTRY_FINGERPRINT_SHA256
        ),
        "g7d_contract_fingerprint_sha256": (
            G7D_CONTRACT_FINGERPRINT_SHA256
        ),
        "g7c_contract_fingerprint_sha256": (
            G7C_CONTRACT_FINGERPRINT_SHA256
        ),
        "g7b_contract_fingerprint_sha256": (
            G7B_CONTRACT_FINGERPRINT_SHA256
        ),
        "dataset": {
            "dataset_id": DATASET_ID,
            "dataset_sha256": DATASET_SHA256,
            "manifest_sha256": MANIFEST_SHA256,
            "feature_columns_sha256": FEATURE_COLUMNS_SHA256,
            "feature_count": FEATURE_COUNT,
            "total_rows": TOTAL_ROWS,
            "train_rows": TRAIN_ROWS,
            "validation_rows": VALIDATION_ROWS,
            "test_rows": TEST_ROWS,
        },
        "target": {
            "contract": TARGET_CONTRACT,
            "class_order": list(TARGET_CLASS_ORDER),
            "target_columns": list(TARGET_COLUMNS),
        },
        "split_authority": {
            "train_role": TRAIN_ROLE,
            "validation_role": VALIDATION_ROLE,
            "test_role": TEST_ROLE,
            "train_feature_access": TRAIN_FEATURE_ACCESS_AUTHORIZED,
            "train_target_access": TRAIN_TARGET_ACCESS_AUTHORIZED,
            "validation_feature_access": (
                VALIDATION_FEATURE_ACCESS_AUTHORIZED
            ),
            "validation_target_access": (
                VALIDATION_TARGET_ACCESS_AUTHORIZED
            ),
            "test_feature_access": TEST_FEATURE_ACCESS_AUTHORIZED,
            "test_target_access": TEST_TARGET_ACCESS_AUTHORIZED,
            "test_structural_split_inspection_only": (
                TEST_STRUCTURAL_SPLIT_INSPECTION_ONLY
            ),
        },
        "historical_validation_audit": {
            "ledger_version": HISTORICAL_VALIDATION_LEDGER_VERSION,
            "historical_status": HISTORICAL_VALIDATION_STATUS,
            "old_c04_cycle": (
                HISTORICAL_VALIDATION_WAS_FOR_OLD_C04_CYCLE
            ),
            "ledger_rewrite_allowed": (
                HISTORICAL_VALIDATION_LEDGER_MAY_BE_REWRITTEN
            ),
            "ledger_reset_allowed": (
                HISTORICAL_VALIDATION_LEDGER_MAY_BE_RESET
            ),
            "governs_remediation_access": (
                HISTORICAL_VALIDATION_LEDGER_GOVERNS_REMEDIATION_ACCESS
            ),
            "remediation_authority_source": (
                REMEDIATION_VALIDATION_AUTHORITY_SOURCE
            ),
        },
        "loader_policy": {
            "version": LOADER_VERSION,
            "validation_exact_contiguous_split": (
                VALIDATION_MUST_BE_EXACT_CONTIGUOUS_SPLIT
            ),
            "train_exact_contiguous_prefix": (
                TRAIN_MUST_REMAIN_EXACT_CONTIGUOUS_PREFIX
            ),
            "test_values_must_not_be_read": TEST_VALUES_MUST_NOT_BE_READ,
            "validation_stops_before_test": (
                VALIDATION_READ_MUST_STOP_BEFORE_TEST
            ),
            "arrays_read_only": ALL_ARRAYS_READ_ONLY,
            "decision_time_alignment": DECISION_TIME_ALIGNMENT_REQUIRED,
            "duplicate_decision_time_allowed": (
                not NO_DUPLICATE_DECISION_TIME_ALLOWED
            ),
            "shuffle_allowed": not NO_SHUFFLE_ALLOWED,
            "model_fit_in_loader": not NO_MODEL_FIT_IN_LOADER,
            "preprocessor_fit_in_loader": (
                not NO_PREPROCESSOR_FIT_IN_LOADER
            ),
            "metrics_in_loader": not NO_METRICS_IN_LOADER,
            "artifact_write_in_loader": not NO_ARTIFACT_WRITE_IN_LOADER,
        },
        "current_gate": {
            "implementation_freeze_only": (
                THIS_GATE_IMPLEMENTATION_FREEZE_ONLY
            ),
            "train_values_loaded": THIS_GATE_LOADS_TRAIN_VALUES,
            "validation_values_loaded": THIS_GATE_LOADS_VALIDATION_VALUES,
            "test_values_loaded": THIS_GATE_LOADS_TEST_VALUES,
            "model_training": THIS_GATE_TRAINS_MODELS,
            "preprocessor_fit": THIS_GATE_FITS_PREPROCESSORS,
            "candidate_evaluation": THIS_GATE_EVALUATES_CANDIDATES,
            "winner_selection": THIS_GATE_SELECTS_WINNER,
            "test_evaluation": THIS_GATE_EVALUATES_TEST,
            "pnl_evaluation": THIS_GATE_EVALUATES_PNL,
            "market_data_acquisition": THIS_GATE_ACQUIRES_MARKET_DATA,
            "runtime_ledger_write": THIS_GATE_WRITES_RUNTIME_LEDGERS,
            "live_authorized": LIVE_AUTHORIZED,
            "execution_authorized": EXECUTION_AUTHORIZED,
        },
    }


def contract_fingerprint_sha256() -> str:

    payload = json.dumps(
        canonical_contract_dict(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")

    return hashlib.sha256(
        payload
    ).hexdigest()


CONTRACT_FINGERPRINT_SHA256 = (
    contract_fingerprint_sha256()
)