from __future__ import annotations

import hashlib
import importlib
import inspect
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(REPO_ROOT),
    )


GATE_ID = (
    "GATE_15D_C_B2D_G7_B_REMEDIATION_DATA_AUTHORITY_FREEZE"
)

SCHEMA_VERSION = "1.0.0"

BASE_AUTHORITY_COMMIT = (
    "144d4359eae9835563f1bf8d01a4dee35ef8c4c2"
)

EXPECTED_G7A_FINGERPRINT = (
    "3af5ccd2d84950dd37c3dda5f9d5872af5a303e9b8fdf5515c52dc5b92ad6f6c"
)


CONTRACT_REL = (
    "02_AI/Models/"
    "frozen_c04_remediation_data_authority_contract.py"
)

G7A_CONTRACT_REL = (
    "02_AI/Models/"
    "frozen_c04_model_remediation_protocol_contract.py"
)

TRAINING_MATRIX_BUILDER_REL = (
    "02_AI/Dataset/training_matrix_builder.py"
)

MODEL_TRAINER_REL = (
    "02_AI/Models/xauusd_model_trainer.py"
)

G7A_EVIDENCE_REL = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g7_a_model_remediation_protocol_freeze_evidence.json"
)

OBSERVATION_LEDGER_REL = (
    "01_Data/Shadow/"
    "xauusd_frozen_c04_shadow_observations.jsonl"
)

ANCHOR_LEDGER_REL = (
    "01_Data/Shadow/"
    "xauusd_frozen_c04_forward_outcome_anchors.jsonl"
)

OUTCOME_LEDGER_REL = (
    "01_Data/Shadow/"
    "xauusd_frozen_c04_forward_outcomes.jsonl"
)

G7B_RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_b_remediation_data_authority_freeze.py"
)

G7B_TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g7_b_remediation_data_authority_freeze.py"
)

EVIDENCE_REL = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g7_b_remediation_data_authority_freeze_evidence.json"
)

EVIDENCE_PATH = (
    REPO_ROOT
    / EVIDENCE_REL
)


ALLOWED_LOCAL_PATHS = {
    CONTRACT_REL,
    G7B_RUNNER_REL,
    G7B_TEST_REL,
    EVIDENCE_REL,
}


HASH_BOUND_DEPENDENCIES = (
    CONTRACT_REL,
    G7A_CONTRACT_REL,
    TRAINING_MATRIX_BUILDER_REL,
    MODEL_TRAINER_REL,
    G7A_EVIDENCE_REL,
    G7B_RUNNER_REL,
    G7B_TEST_REL,
)


_contract: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_remediation_data_authority_contract"
)

_g7a_contract: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_model_remediation_protocol_contract"
)

_training_matrix: Any = importlib.import_module(
    "02_AI.Dataset.training_matrix_builder"
)

_model_trainer: Any = importlib.import_module(
    "02_AI.Models.xauusd_model_trainer"
)


class G7BFreezeError(RuntimeError):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise G7BFreezeError(reason)


def git_process(
    *args: str,
) -> subprocess.CompletedProcess[str]:

    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def git_output(
    *args: str,
) -> str:

    process = git_process(*args)

    require(
        process.returncode == 0,
        (
            "GIT_COMMAND_FAILED:"
            + " ".join(args)
            + ":"
            + process.stderr.strip()
        ),
    )

    return process.stdout.rstrip("\r\n")


def status_paths() -> set[str]:

    output = git_output(
        "status",
        "--porcelain",
        "--untracked-files=all",
    )

    result: set[str] = set()

    for line in output.splitlines():

        if len(line) < 4:
            continue

        value = line[3:].strip()

        if " -> " in value:
            value = value.split(
                " -> ",
                1,
            )[1]

        if (
            value.startswith('"')
            and value.endswith('"')
        ):
            value = value[1:-1]

        result.add(
            value.replace("\\", "/")
        )

    return result


def raw_sha256(
    path: Path,
) -> str:

    require(
        path.is_file(),
        f"FILE_MISSING:{path}",
    )

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def canonical_sha256(
    path: Path,
) -> str:

    require(
        path.is_file(),
        f"FILE_MISSING:{path}",
    )

    data = (
        path.read_bytes()
        .replace(b"\r\n", b"\n")
        .replace(b"\r", b"\n")
    )

    return hashlib.sha256(
        data
    ).hexdigest()


def load_json(
    relative: str,
) -> dict[str, Any]:

    path = REPO_ROOT / relative

    require(
        path.is_file(),
        f"JSON_FILE_MISSING:{relative}",
    )

    value = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(value, dict):
        raise G7BFreezeError(
            f"JSON_ROOT_NOT_OBJECT:{relative}"
        )

    return value


def write_json(
    path: Path,
    document: Mapping[str, Any],
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp = path.with_suffix(
        path.suffix + ".tmp"
    )

    temp.write_text(
        json.dumps(
            dict(document),
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )

    temp.replace(path)


def verify_repository() -> dict[str, Any]:

    fetch = git_process(
        "fetch",
        "origin",
    )

    require(
        fetch.returncode == 0,
        "GIT_FETCH_ORIGIN_FAILED",
    )

    branch = git_output(
        "branch",
        "--show-current",
    )

    head = git_output(
        "rev-parse",
        "HEAD",
    )

    origin = git_output(
        "rev-parse",
        "origin/main",
    )

    require(
        branch == "main",
        f"UNEXPECTED_BRANCH:{branch}",
    )

    require(
        head == origin,
        (
            "HEAD_ORIGIN_MAIN_DIVERGENCE:"
            f"{head}!={origin}"
        ),
    )

    require(
        head == BASE_AUTHORITY_COMMIT,
        (
            "UNEXPECTED_BASE_HEAD:"
            f"{head}:expected="
            f"{BASE_AUTHORITY_COMMIT}"
        ),
    )

    unexpected = (
        status_paths()
        -
        ALLOWED_LOCAL_PATHS
    )

    require(
        not unexpected,
        (
            "UNEXPECTED_LOCAL_PATHS:"
            f"{sorted(unexpected)}"
        ),
    )

    return {
        "status": "PASS",
        "branch": branch,
        "head": head,
        "origin_main": origin,
    }


def verify_g7a() -> dict[str, Any]:

    evidence = load_json(
        G7A_EVIDENCE_REL
    )

    require(
        evidence.get("status")
        ==
        "PASS",
        "G7A_STATUS_NOT_PASS",
    )

    contract_evidence = evidence.get(
        "remediation_contract"
    )

    if not isinstance(
        contract_evidence,
        dict,
    ):
        raise G7BFreezeError(
            "G7A_CONTRACT_EVIDENCE_MISSING"
        )

    require(
        contract_evidence.get(
            "contract_fingerprint_sha256"
        )
        ==
        EXPECTED_G7A_FINGERPRINT,
        "G7A_FINGERPRINT_MISMATCH",
    )

    current = (
        _g7a_contract.contract_fingerprint_sha256()
    )

    require(
        current
        ==
        EXPECTED_G7A_FINGERPRINT,
        "CURRENT_G7A_CONTRACT_FINGERPRINT_MISMATCH",
    )

    require(
        _g7a_contract.FORWARD_HOLDOUT_CAN_BE_USED_FOR_TRAINING
        is False,
        "G7A_FORWARD_HOLDOUT_TRAINING_ALLOWED",
    )

    require(
        _g7a_contract.OLD_30_FORWARD_HOLDOUT_MAY_SELECT_NEW_CANDIDATE
        is False,
        "G7A_FORWARD_HOLDOUT_SELECTION_ALLOWED",
    )

    return {
        "status": "PASS",
        "contract_fingerprint_sha256": current,
    }


def verify_pipeline_authority() -> dict[str, Any]:

    builder = (
        _training_matrix.TrainingMatrixBuilder
    )

    trainer = (
        _model_trainer.XAUUSDModelTrainer
    )

    build_signature = inspect.signature(
        builder.build
    )

    train_fraction = (
        build_signature.parameters[
            "train_fraction"
        ].default
    )

    validation_fraction = (
        build_signature.parameters[
            "validation_fraction"
        ].default
    )

    require(
        float(train_fraction)
        ==
        _contract.TRAIN_FRACTION,
        "TRAIN_FRACTION_PIPELINE_MISMATCH",
    )

    require(
        float(validation_fraction)
        ==
        _contract.VALIDATION_FRACTION,
        "VALIDATION_FRACTION_PIPELINE_MISMATCH",
    )

    require(
        abs(
            (
                float(train_fraction)
                +
                float(validation_fraction)
                +
                _contract.TEST_FRACTION
            )
            -
            1.0
        )
        <=
        1e-15,
        "SPLIT_FRACTION_SUM_MISMATCH",
    )

    builder_source = inspect.getsource(
        builder._assign_chronological_splits
    )

    require(
        '"TRAIN"' in builder_source,
        "TRAIN_SPLIT_NOT_FOUND",
    )

    require(
        '"VALIDATION"' in builder_source,
        "VALIDATION_SPLIT_NOT_FOUND",
    )

    require(
        '"TEST"' in builder_source,
        "TEST_SPLIT_NOT_FOUND",
    )

    require(
        "purge" in builder_source.lower()
        or
        "safe_end" in builder_source,
        "PURGED_SPLIT_LOGIC_NOT_FOUND",
    )

    trainer_source = inspect.getsource(
        trainer.train
    )

    require(
        "x_train_raw" in trainer_source,
        "TRAIN_FRAME_NOT_FOUND",
    )

    require(
        "scaler" in trainer_source.lower(),
        "TRAINER_SCALER_LOGIC_NOT_FOUND",
    )

    require(
        "validation_metrics" in trainer_source,
        "VALIDATION_METRICS_NOT_FOUND",
    )

    require(
        "test_metrics" in trainer_source,
        "TEST_METRICS_NOT_FOUND",
    )

    return {
        "status": "PASS",
        "split_policy": (
            _contract.SPLIT_POLICY
        ),
        "train_fraction": (
            float(train_fraction)
        ),
        "validation_fraction": (
            float(validation_fraction)
        ),
        "test_fraction": (
            _contract.TEST_FRACTION
        ),
        "purged_chronological_split_verified": True,
        "trainer_train_validation_test_contract_verified": True,
    }


def verify_contract() -> dict[str, Any]:

    require(
        _contract.CONTRACT_ID
        ==
        "FROZEN_C04_REMEDIATION_DATA_AUTHORITY_CONTRACT_V1",
        "CONTRACT_ID_MISMATCH",
    )

    require(
        _contract.BASE_AUTHORITY_COMMIT
        ==
        BASE_AUTHORITY_COMMIT,
        "CONTRACT_BASE_AUTHORITY_MISMATCH",
    )

    require(
        _contract.G7A_CONTRACT_FINGERPRINT_SHA256
        ==
        EXPECTED_G7A_FINGERPRINT,
        "G7A_CONTRACT_LINKAGE_MISMATCH",
    )

    require(
        _contract.DEVELOPMENT_DATA_SCOPE
        ==
        "IMMUTABLE_PRE_FORWARD_HISTORICAL_RESEARCH_DATA_ONLY",
        "DEVELOPMENT_SCOPE_MISMATCH",
    )

    require(
        _contract.POST_RESEARCH_CUTOFF_ROWS_ALLOWED
        is False,
        "POST_CUTOFF_ROWS_ALLOWED",
    )

    require(
        _contract.CURRENT_FORWARD_30_ALLOWED
        is False,
        "CURRENT_FORWARD_30_ALLOWED",
    )

    require(
        _contract.FUTURE_PROSPECTIVE_FORWARD_ROWS_ALLOWED
        is False,
        "FUTURE_FORWARD_ROWS_ALLOWED",
    )

    require(
        _contract.RUNTIME_SHADOW_LEDGERS_ALLOWED_AS_DEVELOPMENT_DATA
        is False,
        "SHADOW_LEDGER_DEVELOPMENT_USE_ALLOWED",
    )

    require(
        _contract.SPLIT_POLICY
        ==
        "PURGED_CHRONOLOGICAL_TRAIN_VALIDATION_TEST",
        "SPLIT_POLICY_MISMATCH",
    )

    require(
        _contract.MODEL_FIT_ALLOWED_SPLITS
        ==
        ("TRAIN",),
        "MODEL_FIT_SPLIT_MISMATCH",
    )

    require(
        _contract.PREPROCESSOR_FIT_ALLOWED_SPLITS
        ==
        ("TRAIN",),
        "PREPROCESSOR_FIT_SPLIT_MISMATCH",
    )

    require(
        _contract.TEST_MAY_SELECT_MODEL
        is False,
        "TEST_MODEL_SELECTION_ALLOWED",
    )

    require(
        _contract.TEST_MAY_SELECT_FEATURES
        is False,
        "TEST_FEATURE_SELECTION_ALLOWED",
    )

    require(
        _contract.TEST_MAY_SELECT_HYPERPARAMETERS
        is False,
        "TEST_HYPERPARAMETER_SELECTION_ALLOWED",
    )

    require(
        _contract.TEST_MAY_SELECT_CALIBRATION
        is False,
        "TEST_CALIBRATION_SELECTION_ALLOWED",
    )

    require(
        _contract.TEST_MAY_SELECT_THRESHOLDS
        is False,
        "TEST_THRESHOLD_SELECTION_ALLOWED",
    )

    require(
        _contract.TEST_MAY_TRIGGER_ITERATIVE_TUNING
        is False,
        "TEST_ITERATIVE_TUNING_ALLOWED",
    )

    require(
        _contract.TARGET_CONTRACT
        ==
        "CLEAN_DIRECTIONAL_EXCURSION_V2",
        "TARGET_CONTRACT_MISMATCH",
    )

    require(
        _contract.TARGET_PROFIT_ATR
        ==
        1.25,
        "TARGET_PROFIT_ATR_MISMATCH",
    )

    require(
        _contract.TARGET_MAX_ADVERSE_ATR
        ==
        0.75,
        "TARGET_MAX_ADVERSE_ATR_MISMATCH",
    )

    require(
        _contract.TARGET_CONTRACT_MODIFICATION_ALLOWED
        is False,
        "TARGET_MODIFICATION_ALLOWED",
    )

    require(
        _contract.FORMING_CANDLE_ALLOWED
        is False,
        "FORMING_CANDLE_ALLOWED",
    )

    require(
        _contract.FUTURE_FEATURE_DATA_ALLOWED
        is False,
        "FUTURE_FEATURE_DATA_ALLOWED",
    )

    require(
        _contract.LEAKAGE_ACROSS_SPLITS_ALLOWED
        is False,
        "SPLIT_LEAKAGE_ALLOWED",
    )

    require(
        _contract.CANDIDATE_COMPARISON_MAY_USE_TEST_METRICS
        is False,
        "TEST_METRIC_CANDIDATE_SELECTION_ALLOWED",
    )

    require(
        _contract.FORWARD_30_MAY_SELECT_CANDIDATE
        is False,
        "FORWARD_HOLDOUT_SELECTION_ALLOWED",
    )

    require(
        _contract.SELECTED_CANDIDATE_MUST_BE_FROZEN_BEFORE_TEST
        is True,
        "CANDIDATE_NOT_FROZEN_BEFORE_TEST",
    )

    require(
        _contract.SELECTED_CANDIDATE_MUST_PASS_ONE_SHOT_TEST
        is True,
        "ONE_SHOT_TEST_NOT_REQUIRED",
    )

    require(
        _contract.FAILED_TEST_MAY_NOT_BE_TUNED_AGAINST_SAME_TEST
        is True,
        "FAILED_TEST_REUSE_ALLOWED",
    )

    require(
        _contract.PROSPECTIVE_FORWARD_REQUIRED_AFTER_OFFLINE_FREEZE
        is True,
        "PROSPECTIVE_FORWARD_NOT_REQUIRED",
    )

    require(
        _contract.MINIMUM_NEW_WEEKLY_SAMPLE_COUNT
        ==
        0,
        "WEEKLY_FIXED_MINIMUM_PRESENT",
    )

    require(
        _contract.FIXED_COUNT_FORWARD_WAIT_REQUIRED
        is False,
        "FIXED_COUNT_FORWARD_WAIT_PRESENT",
    )

    current_actions = (
        _contract.THIS_GATE_DISCOVERS_DATASET,
        _contract.THIS_GATE_LOADS_TRAINING_ROWS,
        _contract.THIS_GATE_TRAINS_MODEL,
        _contract.THIS_GATE_FITS_PREPROCESSOR,
        _contract.THIS_GATE_SELECTS_FEATURES,
        _contract.THIS_GATE_TUNES_HYPERPARAMETERS,
        _contract.THIS_GATE_CALIBRATES_PROBABILITIES,
        _contract.THIS_GATE_TUNES_THRESHOLDS,
        _contract.THIS_GATE_SELECTS_MODEL,
        _contract.THIS_GATE_EVALUATES_TEST,
        _contract.THIS_GATE_ACQUIRES_MARKET_DATA,
        _contract.THIS_GATE_WRITES_RUNTIME_LEDGERS,
        _contract.THIS_GATE_EVALUATES_PNL,
        _contract.LIVE_AUTHORIZED,
        _contract.EXECUTION_AUTHORIZED,
    )

    require(
        not any(current_actions),
        "G7B_FORBIDDEN_ACTION_ENABLED",
    )

    fingerprint = (
        _contract.contract_fingerprint_sha256()
    )

    require(
        fingerprint
        ==
        _contract.CONTRACT_FINGERPRINT_SHA256,
        "CONTRACT_FINGERPRINT_MISMATCH",
    )

    return {
        "status": "PASS",
        "contract_id": (
            _contract.CONTRACT_ID
        ),
        "contract_fingerprint_sha256": fingerprint,
        "research_data_cutoff_utc": (
            _contract.RESEARCH_DATA_CUTOFF_UTC
        ),
        "split_policy": _contract.SPLIT_POLICY,
        "train_fraction": _contract.TRAIN_FRACTION,
        "validation_fraction": (
            _contract.VALIDATION_FRACTION
        ),
        "test_fraction": _contract.TEST_FRACTION,
        "test_is_one_shot_confirmation": True,
        "forward_holdout_development_use": False,
    }


def verify_runtime_ledgers_unchanged(
    before: Mapping[str, str],
) -> dict[str, str]:

    after = {
        "observation": raw_sha256(
            REPO_ROOT
            / OBSERVATION_LEDGER_REL
        ),
        "anchor": raw_sha256(
            REPO_ROOT
            / ANCHOR_LEDGER_REL
        ),
        "outcome": raw_sha256(
            REPO_ROOT
            / OUTCOME_LEDGER_REL
        ),
    }

    require(
        dict(before)
        ==
        after,
        "RUNTIME_LEDGER_CHANGED_DURING_G7B_FREEZE",
    )

    return after


def dependency_hashes() -> dict[str, str]:

    result: dict[str, str] = {}

    for relative in HASH_BOUND_DEPENDENCIES:

        path = REPO_ROOT / relative

        require(
            path.is_file(),
            (
                "HASH_BOUND_FILE_MISSING:"
                f"{relative}"
            ),
        )

        result[relative] = (
            canonical_sha256(path)
        )

    return result


def run_gate() -> dict[str, Any]:

    before = {
        "observation": raw_sha256(
            REPO_ROOT
            / OBSERVATION_LEDGER_REL
        ),
        "anchor": raw_sha256(
            REPO_ROOT
            / ANCHOR_LEDGER_REL
        ),
        "outcome": raw_sha256(
            REPO_ROOT
            / OUTCOME_LEDGER_REL
        ),
    }

    repository = verify_repository()

    g7a = verify_g7a()

    pipeline = verify_pipeline_authority()

    contract = verify_contract()

    after = verify_runtime_ledgers_unchanged(
        before
    )

    hashes = dependency_hashes()

    evidence = {
        "gate_id": GATE_ID,
        "schema_version": SCHEMA_VERSION,
        "status": "PASS",
        "base_authority_commit": (
            BASE_AUTHORITY_COMMIT
        ),
        "repository_authority": repository,
        "g7a_authority": g7a,
        "pipeline_authority": pipeline,
        "data_authority_contract": contract,
        "runtime_ledger_raw_sha256": after,
        "hashing_semantics": (
            "GIT_TEXT_CANONICAL_LF_SHA256"
        ),
        "hash_bound_dependencies": hashes,
        "hash_bound_file_count": len(hashes),
        "dataset_discovered": False,
        "training_rows_loaded": False,
        "forward_holdout_used_for_development": False,
        "retraining_performed": False,
        "refitting_performed": False,
        "feature_reselection_performed": False,
        "hyperparameter_tuning_performed": False,
        "calibration_performed": False,
        "threshold_tuning_performed": False,
        "model_reselection_performed": False,
        "test_evaluated": False,
        "pnl_evaluated": False,
        "market_data_acquired": False,
        "ledger_write_performed": False,
        "live_authorized": False,
        "execution_authorized": False,
    }

    write_json(
        EVIDENCE_PATH,
        evidence,
    )

    return evidence


def main() -> int:

    try:

        evidence = run_gate()

    except Exception as exc:

        print(
            "GATE_15D_C_B2D_G7_B_FREEZE_STATUS=BLOCKED"
        )
        print(
            "ERROR_TYPE="
            + type(exc).__name__
        )
        print(
            "ERROR="
            + str(exc)
        )
        print("DATASET_DISCOVERED=false")
        print("RETRAINING_PERFORMED=false")
        print("MODEL_RESELECTION_PERFORMED=false")
        print("TEST_EVALUATED=false")
        print("PNL_EVALUATED=false")
        print("LIVE_AUTHORIZED=false")
        print("EXECUTION_AUTHORIZED=false")

        return 2

    contract = evidence[
        "data_authority_contract"
    ]

    pipeline = evidence[
        "pipeline_authority"
    ]

    print(
        "GATE_15D_C_B2D_G7_B_FREEZE_STATUS=PASS"
    )

    print(
        "BASE_AUTHORITY_COMMIT="
        + evidence[
            "base_authority_commit"
        ]
    )

    print(
        "CONTRACT_ID="
        + contract[
            "contract_id"
        ]
    )

    print(
        "CONTRACT_FINGERPRINT_SHA256="
        + contract[
            "contract_fingerprint_sha256"
        ]
    )

    print(
        "RESEARCH_DATA_CUTOFF_UTC="
        + contract[
            "research_data_cutoff_utc"
        ]
    )

    print(
        "SPLIT_POLICY="
        + contract[
            "split_policy"
        ]
    )

    print(
        "TRAIN_FRACTION="
        + format(
            float(
                pipeline[
                    "train_fraction"
                ]
            ),
            ".2f",
        )
    )

    print(
        "VALIDATION_FRACTION="
        + format(
            float(
                pipeline[
                    "validation_fraction"
                ]
            ),
            ".2f",
        )
    )

    print(
        "TEST_FRACTION="
        + format(
            float(
                pipeline[
                    "test_fraction"
                ]
            ),
            ".2f",
        )
    )

    print(
        "FORWARD_HOLDOUT_DEVELOPMENT_USE=false"
    )

    print(
        "TEST_ROLE=ONE_SHOT_FINAL_OFFLINE_CONFIRMATION"
    )

    print(
        "DATASET_DISCOVERED=false"
    )

    print(
        "TRAINING_ROWS_LOADED=false"
    )

    print(
        "RETRAINING_PERFORMED=false"
    )

    print(
        "MODEL_RESELECTION_PERFORMED=false"
    )

    print(
        "TEST_EVALUATED=false"
    )

    print(
        "PNL_EVALUATED=false"
    )

    print(
        "LIVE_AUTHORIZED=false"
    )

    print(
        "EXECUTION_AUTHORIZED=false"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )