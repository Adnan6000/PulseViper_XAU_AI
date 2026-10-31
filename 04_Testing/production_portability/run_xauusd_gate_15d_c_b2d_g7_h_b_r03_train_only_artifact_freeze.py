from __future__ import annotations

import hashlib
import importlib
import json
import platform
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

import joblib
import numpy as np
import sklearn


REPO_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

if str(
    REPO_ROOT
) not in sys.path:

    sys.path.insert(
        0,
        str(
            REPO_ROOT
        ),
    )


GATE_ID = (
    "GATE_15D_C_B2D_G7_H_B_"
    "R03_TRAIN_ONLY_ARTIFACT_FREEZE"
)

BASE_AUTHORITY_COMMIT = (
    "439f8409efbc15a571180100533808042291b4ed"
)

EXPECTED_PROSPECTIVE_CONTRACT_FINGERPRINT = (
    "e70d8e26c8f4734c456022689d47de406fe3f8daf1827d01b7f0f0d7fe752b9e"
)

EXPECTED_WINNER_CANDIDATE_FINGERPRINT = (
    "ae644c7272a015c26daeaaa7e655120bd7a3e4d267b2acd0d1f235e10bfa2e5f"
)

EXPECTED_FEATURE_COLUMNS_SHA256 = (
    "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
)


BUILDER_REL = (
    "02_AI/Models/"
    "r03_train_only_frozen_artifact_builder.py"
)

RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_h_b_"
    "r03_train_only_artifact_freeze.py"
)

TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g7_h_b_"
    "r03_train_only_artifact_freeze.py"
)

ARTIFACT_REL = (
    "02_AI/Models/artifacts/"
    "xauusd_r03_train_only_frozen.joblib"
)

MANIFEST_REL = (
    "02_AI/Models/artifacts/"
    "xauusd_r03_train_only_frozen_manifest.json"
)

EVIDENCE_REL = (
    "04_Testing/evidence/research/"
    "portable_331/remediation/"
    "xauusd_gate_15d_c_b2d_g7_h_b_"
    "r03_train_only_artifact_freeze.json"
)


ARTIFACT_PATH = (
    REPO_ROOT
    /
    ARTIFACT_REL
)

MANIFEST_PATH = (
    REPO_ROOT
    /
    MANIFEST_REL
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
    BUILDER_REL,
    RUNNER_REL,
    TEST_REL,
    ARTIFACT_REL,
    MANIFEST_REL,
    EVIDENCE_REL,
}


_builder: Any = importlib.import_module(
    "02_AI.Models."
    "r03_train_only_frozen_artifact_builder"
)

_loader_module: Any = importlib.import_module(
    "02_AI.Dataset."
    "portable_331_training_input_loader"
)

_prospective_contract: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_r03_prospective_forward_validation_contract"
)


class G7HBError(RuntimeError):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:

        raise G7HBError(
            reason
        )


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


def write_json_create_only(
    path: Path,
    value: Mapping[str, Any],
) -> None:

    require(
        not path.exists(),
        (
            "CREATE_ONLY_FILE_ALREADY_EXISTS:"
            f"{path}"
        ),
    )

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

    with path.open(
        "x",
        encoding="utf-8",
    ) as handle:

        handle.write(
            encoded
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
        (
            "UNEXPECTED_BRANCH:"
            f"{branch}"
        ),
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
        not MANIFEST_PATH.exists(),
        "FROZEN_ARTIFACT_MANIFEST_ALREADY_EXISTS",
    )

    require(
        not EVIDENCE_PATH.exists(),
        "FROZEN_ARTIFACT_EVIDENCE_ALREADY_EXISTS",
    )

    return {
        "status": "PASS",
        "branch": branch,
        "head": head,
        "origin_main": origin,
        "preexisting_orphan_artifact": (
            ARTIFACT_PATH.exists()
        ),
    }


def verify_authorities() -> dict[str, Any]:

    require(
        _prospective_contract.CONTRACT_FINGERPRINT_SHA256
        ==
        EXPECTED_PROSPECTIVE_CONTRACT_FINGERPRINT,
        "PROSPECTIVE_CONTRACT_FINGERPRINT_MISMATCH",
    )

    require(
        _prospective_contract.WINNER_CANDIDATE_FINGERPRINT_SHA256
        ==
        EXPECTED_WINNER_CANDIDATE_FINGERPRINT,
        "WINNER_CANDIDATE_FINGERPRINT_MISMATCH",
    )

    require(
        _prospective_contract.FEATURE_COLUMNS_SHA256
        ==
        EXPECTED_FEATURE_COLUMNS_SHA256,
        "FEATURE_COLUMNS_HASH_MISMATCH",
    )

    require(
        _prospective_contract.MODEL_ARTIFACT_MUST_BE_FROZEN_BEFORE_COLLECTION
        is True,
        "MODEL_ARTIFACT_FREEZE_NOT_REQUIRED",
    )

    require(
        _prospective_contract.MODEL_ARTIFACT_TRAIN_ONLY_REQUIRED
        is True,
        "TRAIN_ONLY_ARTIFACT_NOT_REQUIRED",
    )

    require(
        _prospective_contract.TRAIN_PLUS_VALIDATION_REFIT_ALLOWED
        is False,
        "TRAIN_VALIDATION_REFIT_ENABLED",
    )

    return {
        "status": "PASS",
        "prospective_contract_fingerprint_sha256": (
            _prospective_contract.CONTRACT_FINGERPRINT_SHA256
        ),
        "winner_candidate_fingerprint_sha256": (
            EXPECTED_WINNER_CANDIDATE_FINGERPRINT
        ),
        "feature_columns_sha256": (
            EXPECTED_FEATURE_COLUMNS_SHA256
        ),
    }


def build_and_freeze() -> dict[str, Any]:

    loader_cls: Any = (
        _loader_module
        .Portable331TrainingInputLoader
    )

    loader: Any = loader_cls(
        REPO_ROOT
    )

    train = (
        loader.load_train_supervised()
    )

    require(
        train.row_count
        ==
        69966,
        "TRAIN_ROW_COUNT_MISMATCH",
    )

    require(
        train.X.shape
        ==
        (
            69966,
            331,
        ),
        "TRAIN_MATRIX_SHAPE_MISMATCH",
    )

    (
        fresh_bundle,
        build_metadata,
    ) = _builder.build_artifact_bundle(
        train_batch=train
    )

    artifact_recovery_mode = (
        ARTIFACT_PATH.exists()
    )

    if not artifact_recovery_mode:

        _builder.save_bundle_create_only(
            bundle=fresh_bundle,
            artifact_path=(
                ARTIFACT_PATH
            ),
        )

    artifact_sha = sha256_file(
        ARTIFACT_PATH
    )

    loaded = _builder.load_bundle(
        ARTIFACT_PATH
    )

    reference_probabilities_raw: Any = (
        build_metadata[
            "reference_probe_probabilities"
        ]
    )

    reference_probabilities = np.asarray(
        reference_probabilities_raw,
        dtype=np.float64,
    )

    reload_verification = (
        _builder.verify_loaded_bundle(
            bundle=loaded,
            train_batch=train,
            reference_probe_probabilities=(
                reference_probabilities
            ),
        )
    )

    manifest = {
        "artifact_schema_version": (
            _builder.ARTIFACT_SCHEMA_VERSION
        ),
        "artifact_relative_path": (
            ARTIFACT_REL
        ),
        "artifact_sha256": (
            artifact_sha
        ),
        "artifact_recovery_mode": (
            artifact_recovery_mode
        ),
        "artifact_overwritten": False,
        "candidate_id": (
            _builder.WINNER_CANDIDATE_ID
        ),
        "candidate_fingerprint_sha256": (
            _builder.WINNER_CANDIDATE_FINGERPRINT_SHA256
        ),
        "dataset_id": (
            train.dataset_id
        ),
        "dataset_sha256": (
            train.dataset_sha256
        ),
        "portable_manifest_sha256": (
            train.manifest_sha256
        ),
        "feature_columns_sha256": (
            train.feature_columns_sha256
        ),
        "feature_count": (
            len(
                train.feature_columns
            )
        ),
        "feature_columns": list(
            train.feature_columns
        ),
        "train_rows": (
            train.row_count
        ),
        "train_only_fit": True,
        "validation_values_loaded": False,
        "test_values_loaded": False,
        "old_forward_30_used": False,
        "standard_scaler": False,
        "prediction_rule": (
            _builder.PREDICTION_RULE
        ),
        "probability_class_order": list(
            _builder.PROBABILITY_CLASS_ORDER
        ),
        "probe_rows": (
            reload_verification[
                "probe_rows"
            ]
        ),
        "reference_probe_probability_sha256": (
            reload_verification[
                "reference_probe_probability_sha256"
            ]
        ),
        "loaded_probe_probability_sha256": (
            reload_verification[
                "loaded_probe_probability_sha256"
            ]
        ),
        "max_absolute_probability_difference": (
            reload_verification[
                "max_absolute_probability_difference"
            ]
        ),
        "mean_absolute_probability_difference": (
            reload_verification[
                "mean_absolute_probability_difference"
            ]
        ),
        "parity_rtol": (
            reload_verification[
                "parity_rtol"
            ]
        ),
        "parity_atol": (
            reload_verification[
                "parity_atol"
            ]
        ),
        "numeric_probability_parity": True,
        "argmax_prediction_parity": True,
        "python_version": (
            platform.python_version()
        ),
        "numpy_version": (
            np.__version__
        ),
        "scikit_learn_version": (
            sklearn.__version__
        ),
        "joblib_version": (
            joblib.__version__
        ),
        "live_authorized": False,
        "execution_authorized": False,
    }

    write_json_create_only(
        MANIFEST_PATH,
        manifest,
    )

    return {
        "status": "PASS",
        "artifact_sha256": (
            artifact_sha
        ),
        "manifest_sha256": (
            sha256_file(
                MANIFEST_PATH
            )
        ),
        "artifact_recovery_mode": (
            artifact_recovery_mode
        ),
        "artifact_overwritten": False,
        "reference_probe_probability_sha256": (
            reload_verification[
                "reference_probe_probability_sha256"
            ]
        ),
        "loaded_probe_probability_sha256": (
            reload_verification[
                "loaded_probe_probability_sha256"
            ]
        ),
        "max_absolute_probability_difference": (
            reload_verification[
                "max_absolute_probability_difference"
            ]
        ),
        "mean_absolute_probability_difference": (
            reload_verification[
                "mean_absolute_probability_difference"
            ]
        ),
        "numeric_probability_parity": True,
        "argmax_prediction_parity": True,
        "train_rows": (
            train.row_count
        ),
        "feature_count": 331,
    }


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

    artifact = (
        build_and_freeze()
    )

    protected_after = (
        protected_hashes()
    )

    require(
        protected_before
        ==
        protected_after,
        "PROTECTED_LEDGER_CHANGED_DURING_G7HB",
    )

    evidence = {
        "gate_id": GATE_ID,
        "status": "PASS",
        "base_authority_commit": (
            BASE_AUTHORITY_COMMIT
        ),
        "repository": repository,
        "authorities": authorities,
        "artifact": artifact,
        "artifact_relative_path": (
            ARTIFACT_REL
        ),
        "manifest_relative_path": (
            MANIFEST_REL
        ),
        "protected_ledger_sha256": (
            protected_after
        ),
        "train_values_loaded": True,
        "validation_values_loaded": False,
        "test_values_loaded": False,
        "old_forward_30_used": False,
        "model_training_performed": True,
        "model_serialization_performed": (
            not artifact[
                "artifact_recovery_mode"
            ]
        ),
        "existing_artifact_recovered": (
            artifact[
                "artifact_recovery_mode"
            ]
        ),
        "artifact_overwritten": False,
        "prospective_market_data_loaded": False,
        "prospective_ledgers_written": False,
        "pnl_evaluated": False,
        "live_authorized": False,
        "execution_authorized": False,
    }

    write_json_create_only(
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
            "GATE_15D_C_B2D_G7_H_B_FREEZE_STATUS=BLOCKED"
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
            "VALIDATION_VALUES_LOADED=false"
        )

        print(
            "TEST_VALUES_LOADED=false"
        )

        print(
            "OLD_FORWARD_30_USED=false"
        )

        print(
            "LIVE_AUTHORIZED=false"
        )

        print(
            "EXECUTION_AUTHORIZED=false"
        )

        return 2

    artifact = evidence[
        "artifact"
    ]

    print(
        "GATE_15D_C_B2D_G7_H_B_FREEZE_STATUS=PASS"
    )

    print(
        "BASE_AUTHORITY_COMMIT="
        +
        BASE_AUTHORITY_COMMIT
    )

    print(
        "WINNER_CANDIDATE_ID="
        +
        _builder.WINNER_CANDIDATE_ID
    )

    print(
        "TRAIN_ROWS="
        +
        str(
            artifact[
                "train_rows"
            ]
        )
    )

    print(
        "FEATURE_COUNT="
        +
        str(
            artifact[
                "feature_count"
            ]
        )
    )

    print(
        "ARTIFACT_SHA256="
        +
        str(
            artifact[
                "artifact_sha256"
            ]
        )
    )

    print(
        "MANIFEST_SHA256="
        +
        str(
            artifact[
                "manifest_sha256"
            ]
        )
    )

    print(
        "ARTIFACT_RECOVERY_MODE="
        +
        bool_text(
            bool(
                artifact[
                    "artifact_recovery_mode"
                ]
            )
        )
    )

    print(
        "ARTIFACT_OVERWRITTEN=false"
    )

    print(
        "REFERENCE_PROBE_PROBABILITY_SHA256="
        +
        str(
            artifact[
                "reference_probe_probability_sha256"
            ]
        )
    )

    print(
        "LOADED_PROBE_PROBABILITY_SHA256="
        +
        str(
            artifact[
                "loaded_probe_probability_sha256"
            ]
        )
    )

    print(
        "MAX_ABSOLUTE_PROBABILITY_DIFFERENCE="
        +
        str(
            artifact[
                "max_absolute_probability_difference"
            ]
        )
    )

    print(
        "MEAN_ABSOLUTE_PROBABILITY_DIFFERENCE="
        +
        str(
            artifact[
                "mean_absolute_probability_difference"
            ]
        )
    )

    print(
        "NUMERIC_PROBABILITY_PARITY=true"
    )

    print(
        "ARGMAX_PREDICTION_PARITY=true"
    )

    print(
        "TRAIN_VALUES_LOADED=true"
    )

    print(
        "VALIDATION_VALUES_LOADED=false"
    )

    print(
        "TEST_VALUES_LOADED=false"
    )

    print(
        "OLD_FORWARD_30_USED=false"
    )

    print(
        "PROSPECTIVE_MARKET_DATA_LOADED=false"
    )

    print(
        "PROSPECTIVE_LEDGERS_WRITTEN=false"
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