from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

import numpy as np


REPO_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(REPO_ROOT),
    )


GATE_ID = (
    "GATE_15D_C_B2D_G7_G_B_ONE_SHOT_SEALED_TEST"
)

BASE_AUTHORITY_COMMIT = (
    "fcc2f282e9c617708ca75b599e337dbeb879283e"
)

EXPECTED_TEST_CONFIRMATION_CONTRACT_FINGERPRINT = (
    "bc1633761ad6dc68923351735abd6ec940ac84871a38c2620ef668666cffe305"
)

EXPECTED_FINAL_WINNER_CONTRACT_FINGERPRINT = (
    "1c0a7e91b318973f319de4a01b9f850e80f236c9211b4866f52cbb330a973f91"
)

EXPECTED_G7E_REGISTRY_FINGERPRINT = (
    "4556eb982086da0ea19ab910a30b5ab58788c7e5b7488ef8e3453e46289c0deb"
)

EXPECTED_WINNER_ID = (
    "R03_FLAT_EXTRA_TREES_SMOOTH"
)

EXPECTED_WINNER_FINGERPRINT = (
    "ae644c7272a015c26daeaaa7e655120bd7a3e4d267b2acd0d1f235e10bfa2e5f"
)


LOADER_REL = (
    "02_AI/Dataset/"
    "portable_331_remediation_sealed_test_loader.py"
)

RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_g_b_"
    "one_shot_sealed_test.py"
)

TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g7_g_b_"
    "one_shot_sealed_test.py"
)

ACCESS_MARKER_REL = (
    "04_Testing/evidence/research/"
    "portable_331/remediation/"
    "xauusd_gate_15d_c_b2d_g7_g_b_"
    "sealed_test_one_shot_access_marker.json"
)

EVIDENCE_REL = (
    "04_Testing/evidence/research/"
    "portable_331/remediation/"
    "xauusd_gate_15d_c_b2d_g7_g_b_"
    "one_shot_sealed_test_evaluation.json"
)

ACCESS_MARKER_PATH = (
    REPO_ROOT
    /
    ACCESS_MARKER_REL
)

EVIDENCE_PATH = (
    REPO_ROOT
    /
    EVIDENCE_REL
)


PROTECTED_LEDGER_RELS = (
    (
        "01_Data/Shadow/"
        "xauusd_frozen_c04_shadow_observations.jsonl"
    ),
    (
        "01_Data/Shadow/"
        "xauusd_frozen_c04_forward_outcome_anchors.jsonl"
    ),
    (
        "01_Data/Shadow/"
        "xauusd_frozen_c04_forward_outcomes.jsonl"
    ),
    (
        "xauusd_portable_331_"
        "one_time_validation_access_ledger.json"
    ),
)


ALLOWED_LOCAL_PATHS = {
    LOADER_REL,
    RUNNER_REL,
    TEST_REL,
    ACCESS_MARKER_REL,
    EVIDENCE_REL,
}


_contract: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_c04_remediation_test_confirmation_contract"
)

_winner_contract: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_c04_remediation_final_winner_contract"
)

_registry: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_c04_remediation_candidate_registry"
)

_evaluator: Any = importlib.import_module(
    "02_AI.Models."
    "remediation_candidate_evaluator"
)

_loader_module: Any = importlib.import_module(
    "02_AI.Dataset."
    "portable_331_remediation_sealed_test_loader"
)


RUN_STATE: dict[str, bool] = {
    "access_marker_created": False,
    "train_values_loaded": False,
    "test_values_loaded": False,
    "model_training_performed": False,
    "test_evaluation_performed": False,
}


class G7GBError(RuntimeError):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise G7GBError(
            reason
        )


def require_mapping(
    value: Any,
    reason: str,
) -> Mapping[str, Any]:

    if not isinstance(
        value,
        Mapping,
    ):
        raise G7GBError(
            reason
        )

    return value


def git_output(
    *args: str,
) -> str:

    result = subprocess.run(
        [
            "git",
            *args,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    require(
        result.returncode
        ==
        0,
        (
            "GIT_COMMAND_FAILED:"
            +
            " ".join(
                args
            )
            +
            ":"
            +
            result.stderr.strip()
        ),
    )

    return result.stdout.rstrip(
        "\r\n"
    )


def status_paths() -> set[str]:

    output = git_output(
        "status",
        "--porcelain",
        "--untracked-files=all",
    )

    paths: set[str] = set()

    for line in output.splitlines():

        if len(
            line
        ) < 4:
            continue

        value = line[
            3:
        ].strip()

        if " -> " in value:
            value = value.split(
                " -> ",
                1,
            )[1]

        paths.add(
            value.replace(
                "\\",
                "/",
            )
        )

    return paths


def sha256_file(
    path: Path,
) -> str:

    import hashlib

    require(
        path.is_file(),
        f"FILE_MISSING:{path}",
    )

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as handle:

        while True:

            block = handle.read(
                1024 * 1024
            )

            if not block:
                break

            digest.update(
                block
            )

    return digest.hexdigest()


def protected_hashes() -> dict[str, str]:

    return {
        relative: sha256_file(
            REPO_ROOT
            /
            relative
        )
        for relative
        in PROTECTED_LEDGER_RELS
    }


def write_json_new(
    path: Path,
    value: Mapping[str, Any],
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    encoded = (
        json.dumps(
            dict(
                value
            ),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        +
        "\n"
    )

    try:

        with path.open(
            "x",
            encoding="utf-8",
        ) as handle:

            handle.write(
                encoded
            )

            handle.flush()

            os.fsync(
                handle.fileno()
            )

    except FileExistsError as exc:

        raise G7GBError(
            (
                "ONE_SHOT_ARTIFACT_ALREADY_EXISTS:"
                f"{path}"
            )
        ) from exc


def verify_repository() -> dict[str, Any]:

    git_output(
        "fetch",
        "origin",
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
        branch
        ==
        "main",
        f"UNEXPECTED_BRANCH:{branch}",
    )

    require(
        head
        ==
        origin,
        "HEAD_ORIGIN_MAIN_DIVERGENCE",
    )

    require(
        head
        ==
        BASE_AUTHORITY_COMMIT,
        (
            "UNEXPECTED_BASE_AUTHORITY:"
            f"{head}"
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

    require(
        not ACCESS_MARKER_PATH.exists(),
        "SEALED_TEST_ALREADY_CONSUMED",
    )

    require(
        not EVIDENCE_PATH.exists(),
        "SEALED_TEST_EVIDENCE_ALREADY_EXISTS",
    )

    return {
        "status": "PASS",
        "branch": branch,
        "head": head,
        "origin_main": origin,
    }


def find_winner_candidate() -> Mapping[str, Any]:

    matches = [
        candidate
        for candidate
        in _registry.CANDIDATES
        if candidate.get(
            "candidate_id"
        )
        ==
        EXPECTED_WINNER_ID
    ]

    require(
        len(
            matches
        )
        ==
        1,
        "WINNER_NOT_UNIQUE_IN_REGISTRY",
    )

    return require_mapping(
        matches[0],
        "WINNER_REGISTRY_ENTRY_INVALID",
    )


def verify_authorities() -> dict[str, Any]:

    require(
        _contract.CONTRACT_FINGERPRINT_SHA256
        ==
        EXPECTED_TEST_CONFIRMATION_CONTRACT_FINGERPRINT,
        "TEST_CONFIRMATION_CONTRACT_FINGERPRINT_MISMATCH",
    )

    require(
        _winner_contract.CONTRACT_FINGERPRINT_SHA256
        ==
        EXPECTED_FINAL_WINNER_CONTRACT_FINGERPRINT,
        "FINAL_WINNER_CONTRACT_FINGERPRINT_MISMATCH",
    )

    require(
        _registry.REGISTRY_FINGERPRINT_SHA256
        ==
        EXPECTED_G7E_REGISTRY_FINGERPRINT,
        "G7E_REGISTRY_FINGERPRINT_MISMATCH",
    )

    require(
        _contract.WINNER_CANDIDATE_ID
        ==
        EXPECTED_WINNER_ID,
        "TEST_CONTRACT_WINNER_ID_MISMATCH",
    )

    require(
        _winner_contract.WINNER_CANDIDATE_ID
        ==
        EXPECTED_WINNER_ID,
        "WINNER_CONTRACT_ID_MISMATCH",
    )

    candidate = (
        find_winner_candidate()
    )

    fingerprint = (
        _registry.candidate_fingerprint_sha256(
            candidate
        )
    )

    require(
        fingerprint
        ==
        EXPECTED_WINNER_FINGERPRINT,
        "WINNER_CANDIDATE_FINGERPRINT_MISMATCH",
    )

    require(
        _contract.TEST_ACCESS_COUNT_MAXIMUM
        ==
        1,
        "TEST_ACCESS_NOT_ONE_SHOT",
    )

    require(
        _contract.TRAIN_ONLY_MODEL_FIT_REQUIRED
        is True,
        "TRAIN_ONLY_FIT_NOT_REQUIRED",
    )

    require(
        _contract.TRAIN_PLUS_VALIDATION_REFIT_ALLOWED
        is False,
        "TRAIN_VALIDATION_REFIT_ENABLED",
    )

    require(
        _contract.VALIDATION_REEVALUATION_ALLOWED_DURING_TEST
        is False,
        "VALIDATION_REEVALUATION_ENABLED",
    )

    require(
        _contract.OLD_FORWARD_30_USE_ALLOWED_DURING_TEST
        is False,
        "FORWARD30_USE_ENABLED",
    )

    return {
        "status": "PASS",
        "test_confirmation_contract_fingerprint_sha256": (
            _contract.CONTRACT_FINGERPRINT_SHA256
        ),
        "final_winner_contract_fingerprint_sha256": (
            _winner_contract.CONTRACT_FINGERPRINT_SHA256
        ),
        "registry_fingerprint_sha256": (
            _registry.REGISTRY_FINGERPRINT_SHA256
        ),
        "winner_candidate_id": (
            EXPECTED_WINNER_ID
        ),
        "winner_candidate_fingerprint_sha256": (
            fingerprint
        ),
    }


def verify_train_batch(
    train: Any,
) -> None:

    require(
        train.dataset_id
        ==
        _contract.DATASET_ID,
        "TRAIN_DATASET_ID_MISMATCH",
    )

    require(
        train.dataset_sha256
        ==
        _contract.DATASET_SHA256,
        "TRAIN_DATASET_SHA256_MISMATCH",
    )

    require(
        train.feature_columns_sha256
        ==
        _contract.FEATURE_COLUMNS_SHA256,
        "TRAIN_FEATURE_HASH_MISMATCH",
    )

    require(
        train.row_count
        ==
        _contract.TRAIN_ROWS,
        "TRAIN_ROW_COUNT_MISMATCH",
    )

    require(
        train.X.shape
        ==
        (
            _contract.TRAIN_ROWS,
            _contract.FEATURE_COUNT,
        ),
        "TRAIN_MATRIX_SHAPE_MISMATCH",
    )


def verify_test_batch(
    test: Any,
    train: Any,
) -> dict[str, Any]:

    require(
        test.dataset_id
        ==
        _contract.DATASET_ID,
        "TEST_DATASET_ID_MISMATCH",
    )

    require(
        test.dataset_sha256
        ==
        _contract.DATASET_SHA256,
        "TEST_DATASET_SHA256_MISMATCH",
    )

    require(
        test.feature_columns_sha256
        ==
        _contract.FEATURE_COLUMNS_SHA256,
        "TEST_FEATURE_HASH_MISMATCH",
    )

    require(
        test.row_count
        ==
        _contract.TEST_ROWS,
        "TEST_ROW_COUNT_MISMATCH",
    )

    require(
        tuple(
            train.feature_columns
        )
        ==
        tuple(
            test.feature_columns
        ),
        "TRAIN_TEST_FEATURE_ORDER_MISMATCH",
    )

    require(
        test.X.shape
        ==
        (
            _contract.TEST_ROWS,
            _contract.FEATURE_COUNT,
        ),
        "TEST_MATRIX_SHAPE_MISMATCH",
    )

    train_time = np.asarray(
        train.decision_time,
        dtype="datetime64[ns]",
    )

    test_time = np.asarray(
        test.decision_time,
        dtype="datetime64[ns]",
    )

    require(
        bool(
            np.all(
                test_time[
                    1:
                ]
                >
                test_time[
                    :-1
                ]
            )
        ),
        "TEST_TIME_NOT_STRICTLY_MONOTONIC",
    )

    require(
        bool(
            train_time[
                -1
            ]
            <
            test_time[
                0
            ]
        ),
        "TRAIN_TEST_TEMPORAL_BOUNDARY_INVALID",
    )

    return {
        "status": "PASS",
        "test_first": str(
            test_time[
                0
            ]
        ),
        "test_last": str(
            test_time[
                -1
            ]
        ),
        "test_time_strictly_monotonic": True,
        "train_before_test": True,
    }


def create_access_marker(
    authorities: Mapping[str, Any],
) -> None:

    marker = {
        "gate_id": GATE_ID,
        "status": (
            "SEALED_TEST_ACCESS_CONSUMED"
        ),
        "access_event_number": 1,
        "maximum_authorized_access_count": 1,
        "base_authority_commit": (
            BASE_AUTHORITY_COMMIT
        ),
        "winner_candidate_id": (
            EXPECTED_WINNER_ID
        ),
        "winner_candidate_fingerprint_sha256": (
            EXPECTED_WINNER_FINGERPRINT
        ),
        "test_confirmation_contract_fingerprint_sha256": (
            EXPECTED_TEST_CONFIRMATION_CONTRACT_FINGERPRINT
        ),
        "authorities": dict(
            authorities
        ),
        "test_rows": (
            _contract.TEST_ROWS
        ),
        "marker_created_before_test_value_read": True,
        "marker_may_not_be_deleted_reset_or_overwritten": True,
        "same_test_rerun_authorized": False,
        "live_authorized": False,
        "execution_authorized": False,
    }

    write_json_new(
        ACCESS_MARKER_PATH,
        marker,
    )

    RUN_STATE[
        "access_marker_created"
    ] = True


def run_gate() -> dict[str, Any]:

    protected_before = (
        protected_hashes()
    )

    repository = (
        verify_repository()
    )

    authorities = (
        verify_authorities()
    )

    loader_cls: Any = (
        _loader_module
        .Portable331RemediationSealedTestLoader
    )

    loader: Any = loader_cls(
        REPO_ROOT
    )

    train = (
        loader.load_train_supervised()
    )

    RUN_STATE[
        "train_values_loaded"
    ] = True

    verify_train_batch(
        train
    )

    # -------------------------------------------------------------------------
    # Irreversible one-shot boundary.
    # Everything above this point is allowed to fail without consuming TEST.
    # Once this marker exists, this TEST is considered consumed.
    # -------------------------------------------------------------------------

    create_access_marker(
        authorities
    )

    test = (
        loader.load_test_supervised()
    )

    RUN_STATE[
        "test_values_loaded"
    ] = True

    temporal = verify_test_batch(
        test,
        train,
    )

    candidate = (
        find_winner_candidate()
    )

    (
        train_matrix,
        train_class,
        train_tradeable,
        test_matrix,
        test_class,
        _test_tradeable,
    ) = _evaluator.validate_supervised_inputs(
        train.X,
        train.target_class,
        train.target_tradeable,
        test.X,
        test.target_class,
        test.target_tradeable,
        expected_feature_count=(
            _contract.FEATURE_COUNT
        ),
    )

    probabilities = (
        _evaluator.fit_predict_candidate(
            candidate,
            train_matrix,
            train_class,
            train_tradeable,
            test_matrix,
        )
    )

    RUN_STATE[
        "model_training_performed"
    ] = True

    metrics = (
        _evaluator.compute_validation_metrics(
            test_class,
            probabilities,
        )
    )

    RUN_STATE[
        "test_evaluation_performed"
    ] = True

    confirmation = (
        _contract.evaluate_test_confirmation(
            metrics
        )
    )

    require(
        isinstance(
            confirmation.get(
                "passed"
            ),
            bool,
        ),
        "TEST_CONFIRMATION_RESULT_INVALID",
    )

    protected_after = (
        protected_hashes()
    )

    require(
        protected_before
        ==
        protected_after,
        "PROTECTED_LEDGER_CHANGED_DURING_G7GB",
    )

    evidence = {
        "gate_id": GATE_ID,
        "status": "PASS",
        "base_authority_commit": (
            BASE_AUTHORITY_COMMIT
        ),
        "repository": repository,
        "authorities": authorities,
        "data_identity": {
            "dataset_id": (
                _contract.DATASET_ID
            ),
            "dataset_sha256": (
                _contract.DATASET_SHA256
            ),
            "feature_columns_sha256": (
                _contract.FEATURE_COLUMNS_SHA256
            ),
            "feature_count": (
                _contract.FEATURE_COUNT
            ),
            "train_rows": (
                _contract.TRAIN_ROWS
            ),
            "validation_rows_not_loaded": (
                _contract.VALIDATION_ROWS
            ),
            "test_rows": (
                _contract.TEST_ROWS
            ),
        },
        "temporal_authority": temporal,
        "winner_candidate_id": (
            EXPECTED_WINNER_ID
        ),
        "winner_candidate_fingerprint_sha256": (
            EXPECTED_WINNER_FINGERPRINT
        ),
        "test_metrics": metrics,
        "test_confirmation": confirmation,
        "sealed_test_access_marker_relative_path": (
            ACCESS_MARKER_REL
        ),
        "sealed_test_access_marker_sha256": (
            sha256_file(
                ACCESS_MARKER_PATH
            )
        ),
        "protected_ledger_sha256": (
            protected_after
        ),
        "access_marker_created": True,
        "train_values_loaded": True,
        "validation_values_loaded": False,
        "test_values_loaded": True,
        "model_training_performed": True,
        "train_only_model_fit": True,
        "train_plus_validation_refit_performed": False,
        "validation_evaluation_performed": False,
        "test_evaluation_performed": True,
        "test_access_count": 1,
        "same_test_rerun_authorized": False,
        "forward_30_used": False,
        "probability_calibration_performed": False,
        "threshold_tuning_performed": False,
        "feature_selection_performed": False,
        "hyperparameter_change_performed": False,
        "candidate_replacement_performed": False,
        "pnl_evaluated": False,
        "market_data_acquired": False,
        "runtime_ledger_write_performed": False,
        "live_authorized": False,
        "execution_authorized": False,
    }

    write_json_new(
        EVIDENCE_PATH,
        evidence,
    )

    return evidence


def bool_text(
    value: bool,
) -> str:

    return (
        "true"
        if value
        else "false"
    )


def main() -> int:

    try:

        evidence = run_gate()

    except Exception as exc:

        print(
            "GATE_15D_C_B2D_G7_G_B_STATUS=BLOCKED"
        )

        print(
            "ERROR_TYPE="
            +
            type(
                exc
            ).__name__
        )

        print(
            "ERROR="
            +
            str(
                exc
            )
        )

        print(
            "ACCESS_MARKER_CREATED="
            +
            bool_text(
                RUN_STATE[
                    "access_marker_created"
                ]
            )
        )

        print(
            "TRAIN_VALUES_LOADED="
            +
            bool_text(
                RUN_STATE[
                    "train_values_loaded"
                ]
            )
        )

        print(
            "VALIDATION_VALUES_LOADED=false"
        )

        print(
            "TEST_VALUES_LOADED="
            +
            bool_text(
                RUN_STATE[
                    "test_values_loaded"
                ]
            )
        )

        print(
            "MODEL_TRAINING_PERFORMED="
            +
            bool_text(
                RUN_STATE[
                    "model_training_performed"
                ]
            )
        )

        print(
            "TEST_EVALUATION_PERFORMED="
            +
            bool_text(
                RUN_STATE[
                    "test_evaluation_performed"
                ]
            )
        )

        print(
            "SAME_TEST_RERUN_AUTHORIZED=false"
        )

        print(
            "LIVE_AUTHORIZED=false"
        )

        print(
            "EXECUTION_AUTHORIZED=false"
        )

        return 2

    metrics = require_mapping(
        evidence.get(
            "test_metrics"
        ),
        "TEST_METRICS_MISSING",
    )

    confirmation = require_mapping(
        evidence.get(
            "test_confirmation"
        ),
        "TEST_CONFIRMATION_MISSING",
    )

    failures_raw = confirmation.get(
        "failures",
        [],
    )

    failures = (
        failures_raw
        if isinstance(
            failures_raw,
            list,
        )
        else []
    )

    print(
        "GATE_15D_C_B2D_G7_G_B_STATUS=PASS"
    )

    print(
        "BASE_AUTHORITY_COMMIT="
        +
        BASE_AUTHORITY_COMMIT
    )

    print(
        "WINNER_CANDIDATE_ID="
        +
        EXPECTED_WINNER_ID
    )

    print(
        "TEST_ROWS="
        +
        str(
            _contract.TEST_ROWS
        )
    )

    print(
        "TEST_EXACT_CLASS_ACCURACY="
        +
        f"{float(metrics['exact_class_accuracy']):.9f}"
    )

    print(
        "TEST_MACRO_F1="
        +
        f"{float(metrics['macro_f1']):.9f}"
    )

    print(
        "TEST_BALANCED_ACCURACY="
        +
        f"{float(metrics['balanced_accuracy']):.9f}"
    )

    print(
        "TEST_MINIMUM_PER_CLASS_RECALL="
        +
        f"{float(metrics['minimum_per_class_recall']):.9f}"
    )

    print(
        "TEST_SHORT_RECALL="
        +
        f"{float(metrics['short_recall']):.9f}"
    )

    print(
        "TEST_NO_TRADE_RECALL="
        +
        f"{float(metrics['no_trade_recall']):.9f}"
    )

    print(
        "TEST_LONG_RECALL="
        +
        f"{float(metrics['long_recall']):.9f}"
    )

    print(
        "TEST_MULTICLASS_BRIER="
        +
        f"{float(metrics['multiclass_brier']):.9f}"
    )

    print(
        "TEST_MULTICLASS_LOG_LOSS="
        +
        f"{float(metrics['multiclass_log_loss']):.9f}"
    )

    print(
        "SEALED_TEST_CONFIRMATION_STATUS="
        +
        str(
            confirmation.get(
                "status"
            )
        )
    )

    print(
        "SEALED_TEST_CONFIRMED="
        +
        bool_text(
            confirmation.get(
                "passed"
            )
            is True
        )
    )

    print(
        "CONFIRMATION_FAILURES="
        +
        (
            ",".join(
                str(
                    value
                )
                for value
                in failures
            )
            if failures
            else "NONE"
        )
    )

    print(
        "ACCESS_MARKER_CREATED=true"
    )

    print(
        "TRAIN_VALUES_LOADED=true"
    )

    print(
        "VALIDATION_VALUES_LOADED=false"
    )

    print(
        "TEST_VALUES_LOADED=true"
    )

    print(
        "MODEL_TRAINING_PERFORMED=true"
    )

    print(
        "TRAIN_PLUS_VALIDATION_REFIT_PERFORMED=false"
    )

    print(
        "TEST_EVALUATION_PERFORMED=true"
    )

    print(
        "TEST_ACCESS_COUNT=1"
    )

    print(
        "SAME_TEST_RERUN_AUTHORIZED=false"
    )

    print(
        "FORWARD_30_USED=false"
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