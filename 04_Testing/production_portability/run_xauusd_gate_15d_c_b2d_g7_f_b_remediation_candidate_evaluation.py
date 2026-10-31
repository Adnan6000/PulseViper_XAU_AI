from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

import numpy as np


REPO_ROOT = Path(
    __file__
).resolve().parents[2]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(REPO_ROOT),
    )


GATE_ID = (
    "GATE_15D_C_B2D_G7_F_B_"
    "REMEDIATION_CANDIDATE_EVALUATION"
)

BASE_AUTHORITY_COMMIT = (
    "4870dcfd432ff0fa2dd242a5e2bd2d2845fbd806"
)

EXPECTED_G7E_REGISTRY_FINGERPRINT = (
    "4556eb982086da0ea19ab910a30b5ab58788c7e5b7488ef8e3453e46289c0deb"
)

EXPECTED_G7FA_ACCESS_FINGERPRINT = (
    "bfd0cfee283dcb29cff79feff6a5366772a596c9635e470e06d56e70ead74b3e"
)

EVALUATOR_REL = (
    "02_AI/Models/"
    "remediation_candidate_evaluator.py"
)

RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_f_b_"
    "remediation_candidate_evaluation.py"
)

TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g7_f_b_"
    "remediation_candidate_evaluation.py"
)

EVIDENCE_REL = (
    "04_Testing/evidence/research/"
    "portable_331/remediation/"
    "xauusd_gate_15d_c_b2d_g7_f_b_"
    "remediation_candidate_evaluation.json"
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
    EVALUATOR_REL,
    RUNNER_REL,
    TEST_REL,
    EVIDENCE_REL,
}


_registry: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_c04_remediation_candidate_registry"
)

_access: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_c04_remediation_train_validation_access_contract"
)

_loader_module: Any = importlib.import_module(
    "02_AI.Dataset."
    "portable_331_remediation_train_validation_loader"
)

_evaluator: Any = importlib.import_module(
    "02_AI.Models."
    "remediation_candidate_evaluator"
)


class G7FBError(RuntimeError):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:
    if not condition:
        raise G7FBError(
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
        raise G7FBError(
            reason
        )

    return value


def require_list(
    value: Any,
    reason: str,
) -> list[Any]:
    if not isinstance(
        value,
        list,
    ):
        raise G7FBError(
            reason
        )

    return value


def sha256_file(
    path: Path,
) -> str:
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
            + " ".join(
                args
            )
            + ":"
            + result.stderr.strip()
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
        if len(line) < 4:
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


def write_json(
    path: Path,
    value: Mapping[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix
        +
        ".tmp"
    )

    temporary.write_text(
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
        "\n",
        encoding="utf-8",
    )

    temporary.replace(
        path
    )


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
        (
            "HEAD_ORIGIN_MAIN_DIVERGENCE:"
            f"{head}:"
            f"{origin}"
        ),
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

    return {
        "status": "PASS",
        "branch": branch,
        "head": head,
        "origin_main": origin,
    }


def verify_authorities() -> dict[str, Any]:
    require(
        _registry.REGISTRY_FINGERPRINT_SHA256
        ==
        EXPECTED_G7E_REGISTRY_FINGERPRINT,
        "G7E_REGISTRY_FINGERPRINT_MISMATCH",
    )

    require(
        _access.CONTRACT_FINGERPRINT_SHA256
        ==
        EXPECTED_G7FA_ACCESS_FINGERPRINT,
        "G7FA_ACCESS_FINGERPRINT_MISMATCH",
    )

    require(
        _access.TRAIN_FEATURE_ACCESS_AUTHORIZED
        is True,
        "TRAIN_FEATURE_ACCESS_NOT_AUTHORIZED",
    )

    require(
        _access.TRAIN_TARGET_ACCESS_AUTHORIZED
        is True,
        "TRAIN_TARGET_ACCESS_NOT_AUTHORIZED",
    )

    require(
        _access.VALIDATION_FEATURE_ACCESS_AUTHORIZED
        is True,
        "VALIDATION_FEATURE_ACCESS_NOT_AUTHORIZED",
    )

    require(
        _access.VALIDATION_TARGET_ACCESS_AUTHORIZED
        is True,
        "VALIDATION_TARGET_ACCESS_NOT_AUTHORIZED",
    )

    require(
        _access.TEST_FEATURE_ACCESS_AUTHORIZED
        is False,
        "TEST_FEATURE_ACCESS_ENABLED",
    )

    require(
        _access.TEST_TARGET_ACCESS_AUTHORIZED
        is False,
        "TEST_TARGET_ACCESS_ENABLED",
    )

    require(
        _registry.CANDIDATE_COUNT
        ==
        6,
        "FROZEN_CANDIDATE_COUNT_CHANGED",
    )

    require(
        len(
            _registry.CANDIDATES
        )
        ==
        6,
        "FROZEN_CANDIDATE_REGISTRY_CHANGED",
    )

    return {
        "status": "PASS",
        "g7e_registry_fingerprint_sha256": (
            EXPECTED_G7E_REGISTRY_FINGERPRINT
        ),
        "g7fa_access_fingerprint_sha256": (
            EXPECTED_G7FA_ACCESS_FINGERPRINT
        ),
        "candidate_count": 6,
    }


def verify_temporal_alignment(
    train_time: Any,
    validation_time: Any,
) -> dict[str, Any]:
    train = np.asarray(
        train_time,
        dtype="datetime64[ns]",
    )

    validation = np.asarray(
        validation_time,
        dtype="datetime64[ns]",
    )

    require(
        train.ndim
        ==
        1,
        "TRAIN_TIME_NOT_1D",
    )

    require(
        validation.ndim
        ==
        1,
        "VALIDATION_TIME_NOT_1D",
    )

    require(
        train.shape[0]
        ==
        _access.TRAIN_ROWS,
        "TRAIN_TIME_ROW_COUNT_MISMATCH",
    )

    require(
        validation.shape[0]
        ==
        _access.VALIDATION_ROWS,
        "VALIDATION_TIME_ROW_COUNT_MISMATCH",
    )

    require(
        not bool(
            np.isnat(
                train
            ).any()
        ),
        "TRAIN_TIME_NAT",
    )

    require(
        not bool(
            np.isnat(
                validation
            ).any()
        ),
        "VALIDATION_TIME_NAT",
    )

    require(
        bool(
            np.all(
                train[
                    1:
                ]
                >
                train[
                    :-1
                ]
            )
        ),
        "TRAIN_TIME_NOT_STRICTLY_MONOTONIC",
    )

    require(
        bool(
            np.all(
                validation[
                    1:
                ]
                >
                validation[
                    :-1
                ]
            )
        ),
        "VALIDATION_TIME_NOT_STRICTLY_MONOTONIC",
    )

    require(
        bool(
            train[
                -1
            ]
            <
            validation[
                0
            ]
        ),
        (
            "TRAIN_VALIDATION_TEMPORAL_"
            "BOUNDARY_INVALID"
        ),
    )

    return {
        "status": "PASS",
        "train_first": str(
            train[
                0
            ]
        ),
        "train_last": str(
            train[
                -1
            ]
        ),
        "validation_first": str(
            validation[
                0
            ]
        ),
        "validation_last": str(
            validation[
                -1
            ]
        ),
        "train_before_validation": True,
    }


def run_gate() -> dict[str, Any]:
    protected_before = (
        protected_hashes()
    )

    repository = verify_repository()

    authorities = verify_authorities()

    loader_cls: Any = (
        _loader_module
        .Portable331RemediationTrainValidationLoader
    )

    loader: Any = loader_cls(
        REPO_ROOT
    )

    train = (
        loader.load_train_supervised()
    )

    validation = (
        loader.load_validation_supervised()
    )

    require(
        train.dataset_id
        ==
        _access.DATASET_ID,
        "TRAIN_DATASET_ID_MISMATCH",
    )

    require(
        validation.dataset_id
        ==
        _access.DATASET_ID,
        "VALIDATION_DATASET_ID_MISMATCH",
    )

    require(
        train.dataset_sha256
        ==
        _access.DATASET_SHA256,
        "TRAIN_DATASET_SHA256_MISMATCH",
    )

    require(
        validation.dataset_sha256
        ==
        _access.DATASET_SHA256,
        "VALIDATION_DATASET_SHA256_MISMATCH",
    )

    require(
        train.feature_columns_sha256
        ==
        _access.FEATURE_COLUMNS_SHA256,
        "TRAIN_FEATURE_HASH_MISMATCH",
    )

    require(
        validation.feature_columns_sha256
        ==
        _access.FEATURE_COLUMNS_SHA256,
        "VALIDATION_FEATURE_HASH_MISMATCH",
    )

    require(
        tuple(
            train.feature_columns
        )
        ==
        tuple(
            validation.feature_columns
        ),
        "TRAIN_VALIDATION_FEATURE_ORDER_MISMATCH",
    )

    require(
        train.row_count
        ==
        _access.TRAIN_ROWS,
        "TRAIN_ROW_COUNT_MISMATCH",
    )

    require(
        validation.row_count
        ==
        _access.VALIDATION_ROWS,
        "VALIDATION_ROW_COUNT_MISMATCH",
    )

    temporal = verify_temporal_alignment(
        train.decision_time,
        validation.decision_time,
    )

    evaluation = (
        _evaluator.evaluate_frozen_registry(
            _registry.CANDIDATES,
            _registry.ELIGIBILITY_POLICY,
            _registry.SELECTION_POLICY,
            train.X,
            train.target_class,
            train.target_tradeable,
            validation.X,
            validation.target_class,
            validation.target_tradeable,
            expected_feature_count=(
                _access.FEATURE_COUNT
            ),
        )
    )

    protected_after = (
        protected_hashes()
    )

    require(
        protected_before
        ==
        protected_after,
        "PROTECTED_LEDGER_CHANGED_DURING_G7FB",
    )

    selection = require_mapping(
        evaluation.get(
            "selection"
        ),
        "SELECTION_BLOCK_MISSING",
    )

    candidate_reports = require_list(
        evaluation.get(
            "candidate_reports"
        ),
        "CANDIDATE_REPORTS_MISSING",
    )

    require(
        len(
            candidate_reports
        )
        ==
        6,
        "CANDIDATE_REPORT_COUNT_MISMATCH",
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
                _access.DATASET_ID
            ),
            "dataset_sha256": (
                _access.DATASET_SHA256
            ),
            "manifest_sha256": (
                _access.MANIFEST_SHA256
            ),
            "feature_columns_sha256": (
                _access.FEATURE_COLUMNS_SHA256
            ),
            "feature_count": (
                _access.FEATURE_COUNT
            ),
            "train_rows": (
                _access.TRAIN_ROWS
            ),
            "validation_rows": (
                _access.VALIDATION_ROWS
            ),
            "test_rows": (
                _access.TEST_ROWS
            ),
        },
        "temporal_authority": temporal,
        "evaluation": evaluation,
        "winner_candidate_id": (
            selection.get(
                "winner_candidate_id"
            )
        ),
        "protected_ledger_sha256": (
            protected_after
        ),
        "train_values_loaded": True,
        "validation_values_loaded": True,
        "test_values_loaded": False,
        "model_training_performed": True,
        "candidate_evaluation_performed": True,
        "winner_selection_performed": (
            selection.get(
                "status"
            )
            ==
            "VALIDATION_WINNER_SELECTED"
        ),
        "test_evaluation_performed": False,
        "forward_30_used": False,
        "probability_calibration_performed": False,
        "threshold_tuning_performed": False,
        "pnl_evaluated": False,
        "market_data_acquired": False,
        "runtime_ledger_write_performed": False,
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
            "GATE_15D_C_B2D_G7_F_B_STATUS=BLOCKED"
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
            "TEST_VALUES_LOADED=false"
        )

        print(
            "FORWARD_30_USED=false"
        )

        print(
            "TEST_EVALUATION_PERFORMED=false"
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

        return 2

    evaluation = require_mapping(
        evidence.get(
            "evaluation"
        ),
        "EVALUATION_BLOCK_MISSING",
    )

    selection = require_mapping(
        evaluation.get(
            "selection"
        ),
        "SELECTION_BLOCK_MISSING",
    )

    reports = require_list(
        evaluation.get(
            "candidate_reports"
        ),
        "REPORT_LIST_MISSING",
    )

    print(
        "GATE_15D_C_B2D_G7_F_B_STATUS=PASS"
    )

    print(
        "BASE_AUTHORITY_COMMIT="
        +
        BASE_AUTHORITY_COMMIT
    )

    print(
        "G7E_REGISTRY_FINGERPRINT_SHA256="
        +
        EXPECTED_G7E_REGISTRY_FINGERPRINT
    )

    print(
        "G7FA_ACCESS_FINGERPRINT_SHA256="
        +
        EXPECTED_G7FA_ACCESS_FINGERPRINT
    )

    print(
        "TRAIN_ROWS="
        +
        str(
            _access.TRAIN_ROWS
        )
    )

    print(
        "VALIDATION_ROWS="
        +
        str(
            _access.VALIDATION_ROWS
        )
    )

    print(
        "CANDIDATE_COUNT="
        +
        str(
            len(
                reports
            )
        )
    )

    for report_raw in reports:
        report = require_mapping(
            report_raw,
            "INVALID_CANDIDATE_REPORT",
        )

        metrics = require_mapping(
            report.get(
                "validation_metrics"
            ),
            "CANDIDATE_METRICS_MISSING",
        )

        print(
            "CANDIDATE="
            +
            str(
                report.get(
                    "candidate_id"
                )
            )
            +
            "|ELIGIBLE="
            +
            str(
                report.get(
                    "eligible"
                )
            ).lower()
            +
            "|MACRO_F1="
            +
            f"{float(metrics['macro_f1']):.9f}"
            +
            "|BAL_ACC="
            +
            f"{float(metrics['balanced_accuracy']):.9f}"
            +
            "|MIN_RECALL="
            +
            f"{float(metrics['minimum_per_class_recall']):.9f}"
            +
            "|BRIER="
            +
            f"{float(metrics['multiclass_brier']):.9f}"
            +
            "|LOG_LOSS="
            +
            f"{float(metrics['multiclass_log_loss']):.9f}"
        )

    print(
        "SELECTION_STATUS="
        +
        str(
            selection.get(
                "status"
            )
        )
    )

    print(
        "WINNER_CANDIDATE_ID="
        +
        str(
            selection.get(
                "winner_candidate_id"
            )
        )
    )

    print(
        "TRAIN_VALUES_LOADED=true"
    )

    print(
        "VALIDATION_VALUES_LOADED=true"
    )

    print(
        "TEST_VALUES_LOADED=false"
    )

    print(
        "MODEL_TRAINING_PERFORMED=true"
    )

    print(
        "CANDIDATE_EVALUATION_PERFORMED=true"
    )

    print(
        "TEST_EVALUATION_PERFORMED=false"
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