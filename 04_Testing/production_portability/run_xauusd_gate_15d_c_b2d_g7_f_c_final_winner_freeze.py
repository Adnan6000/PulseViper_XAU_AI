from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping


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
    "GATE_15D_C_B2D_G7_F_C_FINAL_WINNER_FREEZE"
)

BASE_AUTHORITY_COMMIT = (
    "74ba1f9bc074de6bb8e6081758b9f31efa32b066"
)

EXPECTED_G7E_REGISTRY_FINGERPRINT = (
    "4556eb982086da0ea19ab910a30b5ab58788c7e5b7488ef8e3453e46289c0deb"
)

EXPECTED_G7FA_ACCESS_FINGERPRINT = (
    "bfd0cfee283dcb29cff79feff6a5366772a596c9635e470e06d56e70ead74b3e"
)

EXPECTED_G7FB_EVIDENCE_SHA256 = (
    "34a90921c81fdc1f482330b6cc91e7b34a54339295f4d6e272838057078727b4"
)

EXPECTED_WINNER_ID = (
    "R03_FLAT_EXTRA_TREES_SMOOTH"
)

EXPECTED_WINNER_FINGERPRINT = (
    "ae644c7272a015c26daeaaa7e655120bd7a3e4d267b2acd0d1f235e10bfa2e5f"
)


CONTRACT_REL = (
    "02_AI/Models/"
    "frozen_c04_remediation_final_winner_contract.py"
)

RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_f_c_"
    "final_winner_freeze.py"
)

TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g7_f_c_"
    "final_winner_freeze.py"
)

SOURCE_EVIDENCE_REL = (
    "04_Testing/evidence/research/"
    "portable_331/remediation/"
    "xauusd_gate_15d_c_b2d_g7_f_b_"
    "remediation_candidate_evaluation.json"
)

FREEZE_EVIDENCE_REL = (
    "04_Testing/evidence/research/"
    "portable_331/remediation/"
    "xauusd_gate_15d_c_b2d_g7_f_c_"
    "final_winner_freeze.json"
)

SOURCE_EVIDENCE_PATH = (
    REPO_ROOT
    /
    SOURCE_EVIDENCE_REL
)

FREEZE_EVIDENCE_PATH = (
    REPO_ROOT
    /
    FREEZE_EVIDENCE_REL
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
    CONTRACT_REL,
    RUNNER_REL,
    TEST_REL,
    FREEZE_EVIDENCE_REL,
}


_contract: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_c04_remediation_final_winner_contract"
)

_registry: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_c04_remediation_candidate_registry"
)

_access: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_c04_remediation_train_validation_access_contract"
)


class G7FCFreezeError(RuntimeError):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise G7FCFreezeError(
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
        raise G7FCFreezeError(
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
        raise G7FCFreezeError(
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


def load_json(
    path: Path,
) -> Mapping[str, Any]:

    payload = json.loads(
        path.read_text(
            encoding="utf-8-sig"
        )
    )

    return require_mapping(
        payload,
        f"JSON_ROOT_NOT_MAPPING:{path}",
    )


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

    return {
        "status": "PASS",
        "branch": branch,
        "head": head,
        "origin_main": origin,
    }


def find_registry_winner() -> Mapping[str, Any]:

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


def verify_registry_authority() -> dict[str, Any]:

    require(
        _registry.REGISTRY_FINGERPRINT_SHA256
        ==
        EXPECTED_G7E_REGISTRY_FINGERPRINT,
        "G7E_REGISTRY_FINGERPRINT_MISMATCH",
    )

    candidate = find_registry_winner()

    candidate_fingerprint = (
        _registry.candidate_fingerprint_sha256(
            candidate
        )
    )

    require(
        candidate_fingerprint
        ==
        EXPECTED_WINNER_FINGERPRINT,
        "WINNER_CANDIDATE_FINGERPRINT_MISMATCH",
    )

    require(
        candidate_fingerprint
        ==
        _contract.WINNER_CANDIDATE_FINGERPRINT_SHA256,
        "WINNER_CONTRACT_FINGERPRINT_MISMATCH",
    )

    require(
        dict(
            candidate.get(
                "estimator",
                {},
            )
        )
        ==
        _contract.WINNER_ESTIMATOR_CONFIG,
        "WINNER_ESTIMATOR_CONFIG_MISMATCH",
    )

    require(
        dict(
            candidate.get(
                "preprocessing",
                {},
            )
        )
        ==
        _contract.WINNER_PREPROCESSING,
        "WINNER_PREPROCESSING_MISMATCH",
    )

    return {
        "status": "PASS",
        "registry_fingerprint_sha256": (
            _registry.REGISTRY_FINGERPRINT_SHA256
        ),
        "winner_candidate_id": (
            EXPECTED_WINNER_ID
        ),
        "winner_candidate_fingerprint_sha256": (
            candidate_fingerprint
        ),
    }


def verify_access_authority() -> dict[str, Any]:

    require(
        _access.CONTRACT_FINGERPRINT_SHA256
        ==
        EXPECTED_G7FA_ACCESS_FINGERPRINT,
        "G7FA_ACCESS_FINGERPRINT_MISMATCH",
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

    return {
        "status": "PASS",
        "access_contract_fingerprint_sha256": (
            _access.CONTRACT_FINGERPRINT_SHA256
        ),
        "test_values_still_blocked": True,
    }


def verify_g7fb_evidence() -> dict[str, Any]:

    source_sha = sha256_file(
        SOURCE_EVIDENCE_PATH
    )

    require(
        source_sha
        ==
        EXPECTED_G7FB_EVIDENCE_SHA256,
        "G7FB_EVIDENCE_SHA256_MISMATCH",
    )

    require(
        source_sha
        ==
        _contract.G7FB_EVIDENCE_SHA256,
        "CONTRACT_G7FB_EVIDENCE_SHA256_MISMATCH",
    )

    payload = load_json(
        SOURCE_EVIDENCE_PATH
    )

    require(
        payload.get(
            "status"
        )
        ==
        "PASS",
        "G7FB_STATUS_NOT_PASS",
    )

    require(
        payload.get(
            "winner_candidate_id"
        )
        ==
        EXPECTED_WINNER_ID,
        "G7FB_WINNER_ID_MISMATCH",
    )

    require(
        payload.get(
            "test_values_loaded"
        )
        is False,
        "G7FB_TEST_VALUES_WERE_LOADED",
    )

    require(
        payload.get(
            "forward_30_used"
        )
        is False,
        "G7FB_FORWARD30_WAS_USED",
    )

    evaluation = require_mapping(
        payload.get(
            "evaluation"
        ),
        "G7FB_EVALUATION_MISSING",
    )

    require(
        evaluation.get(
            "candidate_count"
        )
        ==
        6,
        "G7FB_CANDIDATE_COUNT_MISMATCH",
    )

    selection = require_mapping(
        evaluation.get(
            "selection"
        ),
        "G7FB_SELECTION_MISSING",
    )

    require(
        selection.get(
            "status"
        )
        ==
        _contract.SELECTION_STATUS,
        "G7FB_SELECTION_STATUS_MISMATCH",
    )

    require(
        selection.get(
            "winner_candidate_id"
        )
        ==
        EXPECTED_WINNER_ID,
        "G7FB_SELECTION_WINNER_MISMATCH",
    )

    reports = require_list(
        evaluation.get(
            "candidate_reports"
        ),
        "G7FB_CANDIDATE_REPORTS_MISSING",
    )

    winner_reports = [
        require_mapping(
            report,
            "INVALID_G7FB_REPORT",
        )
        for report
        in reports
        if isinstance(
            report,
            Mapping,
        )
        and report.get(
            "candidate_id"
        )
        ==
        EXPECTED_WINNER_ID
    ]

    require(
        len(
            winner_reports
        )
        ==
        1,
        "G7FB_WINNER_REPORT_NOT_UNIQUE",
    )

    winner_report = (
        winner_reports[0]
    )

    require(
        winner_report.get(
            "eligible"
        )
        is True,
        "G7FB_WINNER_NOT_ELIGIBLE",
    )

    metrics = require_mapping(
        winner_report.get(
            "validation_metrics"
        ),
        "G7FB_WINNER_METRICS_MISSING",
    )

    expected_metrics = {
        "exact_class_accuracy": (
            _contract.VALIDATION_EXACT_CLASS_ACCURACY
        ),
        "macro_f1": (
            _contract.VALIDATION_MACRO_F1
        ),
        "balanced_accuracy": (
            _contract.VALIDATION_BALANCED_ACCURACY
        ),
        "minimum_per_class_recall": (
            _contract.VALIDATION_MINIMUM_PER_CLASS_RECALL
        ),
        "multiclass_brier": (
            _contract.VALIDATION_MULTICLASS_BRIER
        ),
        "multiclass_log_loss": (
            _contract.VALIDATION_MULTICLASS_LOG_LOSS
        ),
        "short_recall": (
            _contract.VALIDATION_SHORT_RECALL
        ),
        "no_trade_recall": (
            _contract.VALIDATION_NO_TRADE_RECALL
        ),
        "long_recall": (
            _contract.VALIDATION_LONG_RECALL
        ),
    }

    for key, expected in (
        expected_metrics.items()
    ):

        require(
            float(
                metrics[
                    key
                ]
            )
            ==
            float(
                expected
            ),
            (
                "G7FB_WINNER_METRIC_MISMATCH:"
                f"{key}"
            ),
        )

    require(
        dict(
            metrics[
                "prediction_counts"
            ]
        )
        ==
        _contract.VALIDATION_PREDICTION_COUNTS,
        "G7FB_PREDICTION_COUNTS_MISMATCH",
    )

    require(
        dict(
            metrics[
                "outcome_counts"
            ]
        )
        ==
        _contract.VALIDATION_OUTCOME_COUNTS,
        "G7FB_OUTCOME_COUNTS_MISMATCH",
    )

    return {
        "status": "PASS",
        "g7fb_evidence_sha256": (
            source_sha
        ),
        "winner_candidate_id": (
            EXPECTED_WINNER_ID
        ),
        "winner_metrics_bound": True,
    }


def verify_contract_safety() -> dict[str, Any]:

    require(
        _contract.WINNER_IS_FINAL_FOR_SEALED_TEST
        is True,
        "WINNER_NOT_FINAL_FOR_TEST",
    )

    require(
        _contract.WINNER_CONFIG_MAY_CHANGE_BEFORE_TEST
        is False,
        "WINNER_CONFIG_CHANGE_ENABLED",
    )

    require(
        _contract.WINNER_FEATURES_MAY_CHANGE_BEFORE_TEST
        is False,
        "WINNER_FEATURE_CHANGE_ENABLED",
    )

    require(
        _contract.VALIDATION_MAY_BE_REUSED_FOR_FURTHER_SELECTION
        is False,
        "VALIDATION_REUSE_ENABLED",
    )

    require(
        _contract.OLD_FORWARD_30_MAY_BE_USED_FOR_TUNING
        is False,
        "FORWARD30_TUNING_ENABLED",
    )

    require(
        _contract.TEST_VALUES_AUTHORIZED_IN_THIS_GATE
        is False,
        "TEST_VALUES_AUTHORIZED_TOO_EARLY",
    )

    require(
        _contract.TEST_EVALUATION_AUTHORIZED_IN_THIS_GATE
        is False,
        "TEST_EVALUATION_AUTHORIZED_TOO_EARLY",
    )

    require(
        _contract.TEST_FAILURE_MAY_TRIGGER_SAME_TEST_TUNING
        is False,
        "SAME_TEST_TUNING_ENABLED",
    )

    require(
        _contract.LIVE_AUTHORIZED
        is False,
        "LIVE_AUTHORIZED",
    )

    require(
        _contract.EXECUTION_AUTHORIZED
        is False,
        "EXECUTION_AUTHORIZED",
    )

    return {
        "status": "PASS",
        "test_values_loaded": False,
        "test_evaluation_performed": False,
        "live_authorized": False,
        "execution_authorized": False,
    }


def run_gate() -> dict[str, Any]:

    protected_before = (
        protected_hashes()
    )

    repository = verify_repository()

    registry = (
        verify_registry_authority()
    )

    access = (
        verify_access_authority()
    )

    source_evidence = (
        verify_g7fb_evidence()
    )

    safety = (
        verify_contract_safety()
    )

    protected_after = (
        protected_hashes()
    )

    require(
        protected_before
        ==
        protected_after,
        "PROTECTED_LEDGER_CHANGED_DURING_G7FC",
    )

    evidence = {
        "gate_id": GATE_ID,
        "status": "PASS",
        "base_authority_commit": (
            BASE_AUTHORITY_COMMIT
        ),
        "contract_id": (
            _contract.CONTRACT_ID
        ),
        "contract_fingerprint_sha256": (
            _contract.CONTRACT_FINGERPRINT_SHA256
        ),
        "repository": repository,
        "registry_authority": registry,
        "access_authority": access,
        "g7fb_source_evidence": (
            source_evidence
        ),
        "safety": safety,
        "winner_candidate_id": (
            _contract.WINNER_CANDIDATE_ID
        ),
        "winner_candidate_fingerprint_sha256": (
            _contract.WINNER_CANDIDATE_FINGERPRINT_SHA256
        ),
        "protected_ledger_sha256": (
            protected_after
        ),
        "train_values_loaded": False,
        "validation_values_loaded": False,
        "test_values_loaded": False,
        "model_training_performed": False,
        "validation_reevaluation_performed": False,
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
        FREEZE_EVIDENCE_PATH,
        evidence,
    )

    return evidence


def main() -> int:

    try:

        evidence = run_gate()

    except Exception as exc:

        print(
            "GATE_15D_C_B2D_G7_F_C_FREEZE_STATUS=BLOCKED"
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
            "TRAIN_VALUES_LOADED=false"
        )

        print(
            "VALIDATION_VALUES_LOADED=false"
        )

        print(
            "TEST_VALUES_LOADED=false"
        )

        print(
            "MODEL_TRAINING_PERFORMED=false"
        )

        print(
            "TEST_EVALUATION_PERFORMED=false"
        )

        print(
            "LIVE_AUTHORIZED=false"
        )

        print(
            "EXECUTION_AUTHORIZED=false"
        )

        return 2

    print(
        "GATE_15D_C_B2D_G7_F_C_FREEZE_STATUS=PASS"
    )

    print(
        "BASE_AUTHORITY_COMMIT="
        +
        BASE_AUTHORITY_COMMIT
    )

    print(
        "WINNER_CANDIDATE_ID="
        +
        _contract.WINNER_CANDIDATE_ID
    )

    print(
        "WINNER_CANDIDATE_FINGERPRINT_SHA256="
        +
        _contract.WINNER_CANDIDATE_FINGERPRINT_SHA256
    )

    print(
        "G7FB_EVIDENCE_SHA256="
        +
        _contract.G7FB_EVIDENCE_SHA256
    )

    print(
        "FINAL_WINNER_CONTRACT_FINGERPRINT_SHA256="
        +
        _contract.CONTRACT_FINGERPRINT_SHA256
    )

    print(
        "WINNER_FINAL_FOR_SEALED_TEST=true"
    )

    print(
        "TEST_VALUES_LOADED=false"
    )

    print(
        "TEST_EVALUATION_PERFORMED=false"
    )

    print(
        "FORWARD_30_USED=false"
    )

    print(
        "MODEL_TRAINING_PERFORMED=false"
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

    _ = evidence

    return 0


if __name__ == "__main__":

    raise SystemExit(
        main()
    )