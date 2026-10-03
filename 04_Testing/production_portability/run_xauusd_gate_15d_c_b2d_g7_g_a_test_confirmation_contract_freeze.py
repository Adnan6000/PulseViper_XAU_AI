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
    "GATE_15D_C_B2D_G7_G_A_TEST_CONFIRMATION_CONTRACT_FREEZE"
)

BASE_AUTHORITY_COMMIT = (
    "648939914f74ae993829105274e10146c137414e"
)

EXPECTED_FINAL_WINNER_CONTRACT_FINGERPRINT = (
    "1c0a7e91b318973f319de4a01b9f850e80f236c9211b4866f52cbb330a973f91"
)

EXPECTED_WINNER_ID = (
    "R03_FLAT_EXTRA_TREES_SMOOTH"
)

EXPECTED_WINNER_FINGERPRINT = (
    "ae644c7272a015c26daeaaa7e655120bd7a3e4d267b2acd0d1f235e10bfa2e5f"
)


CONTRACT_REL = (
    "02_AI/Models/"
    "frozen_c04_remediation_test_confirmation_contract.py"
)

RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_g_a_"
    "test_confirmation_contract_freeze.py"
)

TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g7_g_a_"
    "test_confirmation_contract_freeze.py"
)

EVIDENCE_REL = (
    "04_Testing/evidence/research/"
    "portable_331/remediation/"
    "xauusd_gate_15d_c_b2d_g7_g_a_"
    "test_confirmation_contract_freeze.json"
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
    CONTRACT_REL,
    RUNNER_REL,
    TEST_REL,
    EVIDENCE_REL,
}


_contract: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_c04_remediation_test_confirmation_contract"
)

_winner: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_c04_remediation_final_winner_contract"
)


class G7GAFError(RuntimeError):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise G7GAFError(
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


def verify_winner_authority() -> dict[str, Any]:

    require(
        _winner.CONTRACT_FINGERPRINT_SHA256
        ==
        EXPECTED_FINAL_WINNER_CONTRACT_FINGERPRINT,
        "FINAL_WINNER_CONTRACT_FINGERPRINT_MISMATCH",
    )

    require(
        _winner.WINNER_CANDIDATE_ID
        ==
        EXPECTED_WINNER_ID,
        "WINNER_ID_MISMATCH",
    )

    require(
        _winner.WINNER_CANDIDATE_FINGERPRINT_SHA256
        ==
        EXPECTED_WINNER_FINGERPRINT,
        "WINNER_FINGERPRINT_MISMATCH",
    )

    require(
        _winner.WINNER_IS_FINAL_FOR_SEALED_TEST
        is True,
        "WINNER_NOT_FINAL_FOR_TEST",
    )

    require(
        _winner.TEST_VALUES_AUTHORIZED_IN_THIS_GATE
        is False,
        "UPSTREAM_TEST_VALUES_ALREADY_AUTHORIZED",
    )

    require(
        _winner.TEST_EVALUATION_AUTHORIZED_IN_THIS_GATE
        is False,
        "UPSTREAM_TEST_EVALUATION_ALREADY_AUTHORIZED",
    )

    return {
        "status": "PASS",
        "winner_contract_fingerprint_sha256": (
            _winner.CONTRACT_FINGERPRINT_SHA256
        ),
        "winner_candidate_id": (
            _winner.WINNER_CANDIDATE_ID
        ),
        "winner_candidate_fingerprint_sha256": (
            _winner.WINNER_CANDIDATE_FINGERPRINT_SHA256
        ),
    }


def verify_confirmation_contract() -> dict[str, Any]:

    require(
        _contract.FINAL_WINNER_CONTRACT_FINGERPRINT_SHA256
        ==
        EXPECTED_FINAL_WINNER_CONTRACT_FINGERPRINT,
        "TEST_CONTRACT_WINNER_LINKAGE_MISMATCH",
    )

    require(
        _contract.WINNER_CANDIDATE_ID
        ==
        EXPECTED_WINNER_ID,
        "TEST_CONTRACT_WINNER_ID_MISMATCH",
    )

    require(
        _contract.WINNER_CANDIDATE_FINGERPRINT_SHA256
        ==
        EXPECTED_WINNER_FINGERPRINT,
        "TEST_CONTRACT_WINNER_FINGERPRINT_MISMATCH",
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

    require(
        _contract.TEST_RESULT_MAY_NOT_BE_USED_FOR_SAME_TEST_TUNING
        is True,
        "SAME_TEST_TUNING_NOT_BLOCKED",
    )

    require(
        _contract.ALL_CONFIRMATION_CRITERIA_MUST_PASS
        is True,
        "ALL_CRITERIA_NOT_REQUIRED",
    )

    require(
        _contract.NO_POST_HOC_EXCEPTION_ALLOWED
        is True,
        "POST_HOC_EXCEPTION_ENABLED",
    )

    require(
        _contract.NO_MANUAL_OVERRIDE_TO_PASS_ALLOWED
        is True,
        "MANUAL_PASS_OVERRIDE_ENABLED",
    )

    require(
        _contract.THIS_GATE_LOADS_TEST_VALUES
        is False,
        "TEST_VALUES_LOADED_IN_FREEZE_GATE",
    )

    require(
        _contract.THIS_GATE_EVALUATES_TEST
        is False,
        "TEST_EVALUATION_IN_FREEZE_GATE",
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

    expected_macro = (
        _contract.VALIDATION_MACRO_F1
        *
        _contract.MACRO_F1_VALIDATION_RETENTION_RATIO
    )

    expected_balanced = (
        _contract.VALIDATION_BALANCED_ACCURACY
        *
        _contract.BALANCED_ACCURACY_VALIDATION_RETENTION_RATIO
    )

    expected_min_recall = (
        _contract.VALIDATION_MINIMUM_PER_CLASS_RECALL
        *
        _contract.MINIMUM_PER_CLASS_RECALL_RETENTION_RATIO
    )

    expected_brier = (
        _contract.VALIDATION_MULTICLASS_BRIER
        +
        _contract.MAXIMUM_BRIER_DEGRADATION
    )

    expected_logloss = (
        _contract.VALIDATION_MULTICLASS_LOG_LOSS
        +
        _contract.MAXIMUM_LOG_LOSS_DEGRADATION
    )

    require(
        _contract.TEST_MACRO_F1_MINIMUM
        ==
        expected_macro,
        "MACRO_F1_THRESHOLD_MISMATCH",
    )

    require(
        _contract.TEST_BALANCED_ACCURACY_MINIMUM
        ==
        expected_balanced,
        "BALANCED_ACCURACY_THRESHOLD_MISMATCH",
    )

    require(
        _contract.TEST_MINIMUM_PER_CLASS_RECALL_MINIMUM
        ==
        expected_min_recall,
        "MIN_RECALL_THRESHOLD_MISMATCH",
    )

    require(
        _contract.TEST_MULTICLASS_BRIER_MAXIMUM
        ==
        expected_brier,
        "BRIER_THRESHOLD_MISMATCH",
    )

    require(
        _contract.TEST_MULTICLASS_LOG_LOSS_MAXIMUM
        ==
        expected_logloss,
        "LOGLOSS_THRESHOLD_MISMATCH",
    )

    return {
        "status": "PASS",
        "contract_id": (
            _contract.CONTRACT_ID
        ),
        "contract_fingerprint_sha256": (
            _contract.CONTRACT_FINGERPRINT_SHA256
        ),
        "thresholds": (
            _contract.test_thresholds_dict()
        ),
        "test_access_count_maximum": (
            _contract.TEST_ACCESS_COUNT_MAXIMUM
        ),
    }


def verify_confirmation_function() -> dict[str, Any]:

    passing_metrics = {
        "macro_f1": (
            _contract.TEST_MACRO_F1_MINIMUM
        ),
        "balanced_accuracy": (
            _contract.TEST_BALANCED_ACCURACY_MINIMUM
        ),
        "minimum_per_class_recall": (
            _contract.TEST_MINIMUM_PER_CLASS_RECALL_MINIMUM
        ),
        "short_recall": 0.30,
        "no_trade_recall": 0.30,
        "long_recall": 0.30,
        "multiclass_brier": (
            _contract.TEST_MULTICLASS_BRIER_MAXIMUM
        ),
        "multiclass_log_loss": (
            _contract.TEST_MULTICLASS_LOG_LOSS_MAXIMUM
        ),
        "prediction_counts": {
            "SHORT": 4500,
            "NO_TRADE": 5000,
            "LONG": 5496,
        },
        "prediction_shares": {
            "SHORT": 4500 / 14996,
            "NO_TRADE": 5000 / 14996,
            "LONG": 5496 / 14996,
        },
    }

    result = (
        _contract.evaluate_test_confirmation(
            passing_metrics
        )
    )

    require(
        result.get(
            "passed"
        )
        is True,
        "BOUNDARY_PASS_CASE_FAILED",
    )

    failing_metrics = dict(
        passing_metrics
    )

    failing_metrics[
        "macro_f1"
    ] = (
        _contract.TEST_MACRO_F1_MINIMUM
        -
        0.000001
    )

    result_fail = (
        _contract.evaluate_test_confirmation(
            failing_metrics
        )
    )

    require(
        result_fail.get(
            "passed"
        )
        is False,
        "BELOW_THRESHOLD_CASE_PASSED",
    )

    failures = result_fail.get(
        "failures"
    )

    require(
        isinstance(
            failures,
            list,
        ),
        "FAILURE_LIST_MISSING",
    )

    require(
        "MACRO_F1_BELOW_MINIMUM"
        in failures,
        "EXPECTED_MACRO_F1_FAILURE_MISSING",
    )

    return {
        "status": "PASS",
        "boundary_pass_verified": True,
        "below_threshold_failure_verified": True,
    }


def run_gate() -> dict[str, Any]:

    protected_before = (
        protected_hashes()
    )

    repository = (
        verify_repository()
    )

    winner = (
        verify_winner_authority()
    )

    contract = (
        verify_confirmation_contract()
    )

    function_test = (
        verify_confirmation_function()
    )

    protected_after = (
        protected_hashes()
    )

    require(
        protected_before
        ==
        protected_after,
        "PROTECTED_LEDGER_CHANGED_DURING_G7GA",
    )

    evidence = {
        "gate_id": GATE_ID,
        "status": "PASS",
        "base_authority_commit": (
            BASE_AUTHORITY_COMMIT
        ),
        "repository": repository,
        "winner_authority": winner,
        "confirmation_contract": (
            contract
        ),
        "confirmation_function_test": (
            function_test
        ),
        "protected_ledger_sha256": (
            protected_after
        ),
        "train_values_loaded": False,
        "validation_values_loaded": False,
        "test_values_loaded": False,
        "model_training_performed": False,
        "validation_evaluation_performed": False,
        "test_evaluation_performed": False,
        "forward_30_used": False,
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
            "GATE_15D_C_B2D_G7_G_A_FREEZE_STATUS=BLOCKED"
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
            "TEST_EVALUATION_PERFORMED=false"
        )

        print(
            "MODEL_TRAINING_PERFORMED=false"
        )

        print(
            "LIVE_AUTHORIZED=false"
        )

        print(
            "EXECUTION_AUTHORIZED=false"
        )

        return 2

    print(
        "GATE_15D_C_B2D_G7_G_A_FREEZE_STATUS=PASS"
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
        "TEST_CONFIRMATION_CONTRACT_FINGERPRINT_SHA256="
        +
        _contract.CONTRACT_FINGERPRINT_SHA256
    )

    print(
        "TEST_MACRO_F1_MINIMUM="
        +
        str(
            _contract.TEST_MACRO_F1_MINIMUM
        )
    )

    print(
        "TEST_BALANCED_ACCURACY_MINIMUM="
        +
        str(
            _contract.TEST_BALANCED_ACCURACY_MINIMUM
        )
    )

    print(
        "TEST_MINIMUM_PER_CLASS_RECALL_MINIMUM="
        +
        str(
            _contract.TEST_MINIMUM_PER_CLASS_RECALL_MINIMUM
        )
    )

    print(
        "TEST_MULTICLASS_BRIER_MAXIMUM="
        +
        str(
            _contract.TEST_MULTICLASS_BRIER_MAXIMUM
        )
    )

    print(
        "TEST_MULTICLASS_LOG_LOSS_MAXIMUM="
        +
        str(
            _contract.TEST_MULTICLASS_LOG_LOSS_MAXIMUM
        )
    )

    print(
        "TEST_ONE_SHOT_POLICY_FROZEN=true"
    )

    print(
        "TEST_VALUES_LOADED=false"
    )

    print(
        "TEST_EVALUATION_PERFORMED=false"
    )

    print(
        "MODEL_TRAINING_PERFORMED=false"
    )

    print(
        "FORWARD_30_USED=false"
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