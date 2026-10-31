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
    "GATE_15D_C_B2D_G7_H_A_"
    "R03_PROSPECTIVE_FORWARD_CONTRACT_FREEZE"
)

BASE_AUTHORITY_COMMIT = (
    "a520c646aa6fb8bff139219f7101eb0d4aa07b43"
)

EXPECTED_WINNER_FINGERPRINT = (
    "ae644c7272a015c26daeaaa7e655120bd7a3e4d267b2acd0d1f235e10bfa2e5f"
)

EXPECTED_FINAL_WINNER_CONTRACT_FINGERPRINT = (
    "1c0a7e91b318973f319de4a01b9f850e80f236c9211b4866f52cbb330a973f91"
)

EXPECTED_TEST_CONTRACT_FINGERPRINT = (
    "bc1633761ad6dc68923351735abd6ec940ac84871a38c2620ef668666cffe305"
)

EXPECTED_FORWARD_OUTCOME_CONTRACT_FINGERPRINT = (
    "01fe52a2f068fcc8fb2fc5b89dd7e19dc974fc2d967cfb791e75c3415804ce87"
)

EXPECTED_TEST_EVIDENCE_SHA256 = (
    "df6de696e413ade5a1a6cf52bd6ec4c290a46895d97c1fff2c30e9e7e6e09e0b"
)

EXPECTED_TEST_ACCESS_MARKER_SHA256 = (
    "d4555e29b4938ed12fe624d9e3b8853b5b59d2e8c35e494225fdd34f89f8ae72"
)


CONTRACT_REL = (
    "02_AI/Models/"
    "frozen_r03_prospective_forward_validation_contract.py"
)

RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_h_a_"
    "r03_prospective_forward_contract_freeze.py"
)

TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g7_h_a_"
    "r03_prospective_forward_contract_freeze.py"
)

EVIDENCE_REL = (
    "04_Testing/evidence/research/"
    "portable_331/remediation/"
    "xauusd_gate_15d_c_b2d_g7_h_a_"
    "r03_prospective_forward_contract_freeze.json"
)

SEALED_TEST_EVIDENCE_REL = (
    "04_Testing/evidence/research/"
    "portable_331/remediation/"
    "xauusd_gate_15d_c_b2d_g7_g_b_"
    "one_shot_sealed_test_evaluation.json"
)

SEALED_TEST_MARKER_REL = (
    "04_Testing/evidence/research/"
    "portable_331/remediation/"
    "xauusd_gate_15d_c_b2d_g7_g_b_"
    "sealed_test_one_shot_access_marker.json"
)

EVIDENCE_PATH = (
    REPO_ROOT
    /
    EVIDENCE_REL
)


OLD_PROTECTED_LEDGER_RELS = (
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
    "frozen_r03_prospective_forward_validation_contract"
)

_winner: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_c04_remediation_final_winner_contract"
)

_test_contract: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_c04_remediation_test_confirmation_contract"
)

_forward_contract: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_c04_forward_outcome_contract"
)


class G7HAError(RuntimeError):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise G7HAError(
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
        in OLD_PROTECTED_LEDGER_RELS
    }


def write_json(
    path: Path,
    value: Mapping[str, Any],
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp = path.with_suffix(
        path.suffix
        +
        ".tmp"
    )

    temp.write_text(
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

    temp.replace(
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


def verify_upstream() -> dict[str, Any]:

    require(
        _winner.CONTRACT_FINGERPRINT_SHA256
        ==
        EXPECTED_FINAL_WINNER_CONTRACT_FINGERPRINT,
        "FINAL_WINNER_CONTRACT_FINGERPRINT_MISMATCH",
    )

    require(
        _winner.WINNER_CANDIDATE_FINGERPRINT_SHA256
        ==
        EXPECTED_WINNER_FINGERPRINT,
        "WINNER_FINGERPRINT_MISMATCH",
    )

    require(
        _test_contract.CONTRACT_FINGERPRINT_SHA256
        ==
        EXPECTED_TEST_CONTRACT_FINGERPRINT,
        "TEST_CONFIRMATION_CONTRACT_FINGERPRINT_MISMATCH",
    )

    require(
        _forward_contract.compute_contract_fingerprint()
        ==
        EXPECTED_FORWARD_OUTCOME_CONTRACT_FINGERPRINT,
        "FORWARD_OUTCOME_CONTRACT_FINGERPRINT_MISMATCH",
    )

    test_evidence_hash = sha256_file(
        REPO_ROOT
        /
        SEALED_TEST_EVIDENCE_REL
    )

    marker_hash = sha256_file(
        REPO_ROOT
        /
        SEALED_TEST_MARKER_REL
    )

    require(
        test_evidence_hash
        ==
        EXPECTED_TEST_EVIDENCE_SHA256,
        "SEALED_TEST_EVIDENCE_HASH_MISMATCH",
    )

    require(
        marker_hash
        ==
        EXPECTED_TEST_ACCESS_MARKER_SHA256,
        "SEALED_TEST_ACCESS_MARKER_HASH_MISMATCH",
    )

    return {
        "status": "PASS",
        "winner_candidate_fingerprint_sha256": (
            EXPECTED_WINNER_FINGERPRINT
        ),
        "final_winner_contract_fingerprint_sha256": (
            EXPECTED_FINAL_WINNER_CONTRACT_FINGERPRINT
        ),
        "test_confirmation_contract_fingerprint_sha256": (
            EXPECTED_TEST_CONTRACT_FINGERPRINT
        ),
        "forward_outcome_contract_fingerprint_sha256": (
            EXPECTED_FORWARD_OUTCOME_CONTRACT_FINGERPRINT
        ),
        "sealed_test_evidence_sha256": (
            test_evidence_hash
        ),
        "sealed_test_access_marker_sha256": (
            marker_hash
        ),
    }


def verify_contract() -> dict[str, Any]:

    require(
        _contract.BASE_AUTHORITY_COMMIT
        ==
        BASE_AUTHORITY_COMMIT,
        "CONTRACT_BASE_AUTHORITY_MISMATCH",
    )

    require(
        _contract.MODEL_ARTIFACT_MUST_BE_FROZEN_BEFORE_COLLECTION
        is True,
        "MODEL_ARTIFACT_FREEZE_NOT_REQUIRED",
    )

    require(
        _contract.FRESH_SAMPLE_ONLY
        is True,
        "FRESH_SAMPLE_ONLY_NOT_REQUIRED",
    )

    require(
        _contract.OLD_FORWARD_30_ELIGIBLE_FOR_ACCEPTANCE
        is False,
        "OLD_FORWARD30_ACCEPTANCE_ENABLED",
    )

    require(
        _contract.OLD_FORWARD_30_ELIGIBLE_FOR_TUNING
        is False,
        "OLD_FORWARD30_TUNING_ENABLED",
    )

    require(
        _contract.SEALED_TEST_ELIGIBLE_FOR_FURTHER_TUNING
        is False,
        "SEALED_TEST_TUNING_ENABLED",
    )

    require(
        _contract.MINIMUM_MATURED_OUTCOMES
        ==
        60,
        "MINIMUM_MATURED_OUTCOMES_CHANGED",
    )

    require(
        _contract.MINIMUM_DISTINCT_OBSERVATION_UTC_DATES
        ==
        5,
        "MINIMUM_OBSERVATION_DATES_CHANGED",
    )

    require(
        _contract.WEEKLY_REPORTS_ARE_DESCRIPTIVE_ONLY
        is True,
        "WEEKLY_REPORTS_NOT_DESCRIPTIVE_ONLY",
    )

    require(
        _contract.WEEKLY_REPORTS_MAY_TRIGGER_PASS_FAIL
        is False,
        "WEEKLY_PASS_FAIL_ENABLED",
    )

    require(
        _contract.REAL_TICK_VALIDATION_REQUIRED_AFTER_PROSPECTIVE_PASS
        is True,
        "REAL_TICK_VALIDATION_NOT_REQUIRED",
    )

    require(
        _contract.BROKER_EXECUTION_VALIDATION_REQUIRED_AFTER_PROSPECTIVE_PASS
        is True,
        "BROKER_EXECUTION_VALIDATION_NOT_REQUIRED",
    )

    require(
        _contract.PROSPECTIVE_PASS_AUTHORIZES_LIVE
        is False,
        "PROSPECTIVE_PASS_AUTHORIZES_LIVE",
    )

    require(
        _contract.PROSPECTIVE_PASS_AUTHORIZES_EXECUTION
        is False,
        "PROSPECTIVE_PASS_AUTHORIZES_EXECUTION",
    )

    return {
        "status": "PASS",
        "contract_id": (
            _contract.CONTRACT_ID
        ),
        "contract_fingerprint_sha256": (
            _contract.CONTRACT_FINGERPRINT_SHA256
        ),
        "minimum_matured_outcomes": (
            _contract.MINIMUM_MATURED_OUTCOMES
        ),
        "minimum_distinct_observation_utc_dates": (
            _contract.MINIMUM_DISTINCT_OBSERVATION_UTC_DATES
        ),
        "thresholds": (
            _contract.acceptance_thresholds_dict()
        ),
    }


def verify_decision_function() -> dict[str, Any]:

    passing_metrics = {
        "macro_f1": (
            _contract.PROSPECTIVE_MACRO_F1_MINIMUM
        ),
        "balanced_accuracy": (
            _contract.PROSPECTIVE_BALANCED_ACCURACY_MINIMUM
        ),
        "minimum_per_class_recall": (
            _contract.PROSPECTIVE_MINIMUM_PER_CLASS_RECALL_MINIMUM
        ),
        "short_recall": 0.25,
        "no_trade_recall": 0.25,
        "long_recall": 0.25,
        "multiclass_brier": (
            _contract.PROSPECTIVE_MULTICLASS_BRIER_MAXIMUM
        ),
        "multiclass_log_loss": (
            _contract.PROSPECTIVE_MULTICLASS_LOG_LOSS_MAXIMUM
        ),
        "prediction_counts": {
            "SHORT": 18,
            "NO_TRADE": 18,
            "LONG": 24,
        },
        "prediction_shares": {
            "SHORT": 0.30,
            "NO_TRADE": 0.30,
            "LONG": 0.40,
        },
    }

    immature = (
        _contract.evaluate_prospective_confirmation(
            passing_metrics,
            matured_outcomes=59,
            distinct_observation_utc_dates=5,
        )
    )

    require(
        immature.get(
            "status"
        )
        ==
        _contract.NOT_MATURE_STATUS,
        "IMMATURE_SAMPLE_NOT_BLOCKED",
    )

    boundary_pass = (
        _contract.evaluate_prospective_confirmation(
            passing_metrics,
            matured_outcomes=60,
            distinct_observation_utc_dates=5,
        )
    )

    require(
        boundary_pass.get(
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
        _contract.PROSPECTIVE_MACRO_F1_MINIMUM
        -
        0.000001
    )

    failure = (
        _contract.evaluate_prospective_confirmation(
            failing_metrics,
            matured_outcomes=60,
            distinct_observation_utc_dates=5,
        )
    )

    require(
        failure.get(
            "passed"
        )
        is False,
        "BELOW_THRESHOLD_CASE_PASSED",
    )

    failures = failure.get(
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
        "EXPECTED_MACRO_FAILURE_MISSING",
    )

    return {
        "status": "PASS",
        "immature_sample_blocked": True,
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

    upstream = (
        verify_upstream()
    )

    contract = (
        verify_contract()
    )

    decision_function = (
        verify_decision_function()
    )

    protected_after = (
        protected_hashes()
    )

    require(
        protected_before
        ==
        protected_after,
        "PROTECTED_LEDGER_CHANGED_DURING_G7HA",
    )

    evidence = {
        "gate_id": GATE_ID,
        "status": "PASS",
        "base_authority_commit": (
            BASE_AUTHORITY_COMMIT
        ),
        "repository": repository,
        "upstream_authorities": (
            upstream
        ),
        "prospective_contract": (
            contract
        ),
        "decision_function_test": (
            decision_function
        ),
        "protected_old_ledger_sha256": (
            protected_after
        ),
        "market_data_loaded": False,
        "old_forward_outcomes_loaded": False,
        "test_values_loaded": False,
        "model_training_performed": False,
        "model_serialization_performed": False,
        "prospective_ledgers_created": False,
        "prospective_ledger_write_performed": False,
        "prospective_evaluation_performed": False,
        "pnl_evaluated": False,
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
            "GATE_15D_C_B2D_G7_H_A_FREEZE_STATUS=BLOCKED"
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
            "MARKET_DATA_LOADED=false"
        )

        print(
            "OLD_FORWARD_OUTCOMES_LOADED=false"
        )

        print(
            "TEST_VALUES_LOADED=false"
        )

        print(
            "MODEL_TRAINING_PERFORMED=false"
        )

        print(
            "PROSPECTIVE_LEDGER_WRITE_PERFORMED=false"
        )

        print(
            "LIVE_AUTHORIZED=false"
        )

        print(
            "EXECUTION_AUTHORIZED=false"
        )

        return 2

    print(
        "GATE_15D_C_B2D_G7_H_A_FREEZE_STATUS=PASS"
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
        "PROSPECTIVE_CONTRACT_FINGERPRINT_SHA256="
        +
        _contract.CONTRACT_FINGERPRINT_SHA256
    )

    print(
        "MINIMUM_MATURED_OUTCOMES="
        +
        str(
            _contract.MINIMUM_MATURED_OUTCOMES
        )
    )

    print(
        "MINIMUM_DISTINCT_OBSERVATION_UTC_DATES="
        +
        str(
            _contract.MINIMUM_DISTINCT_OBSERVATION_UTC_DATES
        )
    )

    print(
        "PROSPECTIVE_MACRO_F1_MINIMUM="
        +
        str(
            _contract.PROSPECTIVE_MACRO_F1_MINIMUM
        )
    )

    print(
        "PROSPECTIVE_BALANCED_ACCURACY_MINIMUM="
        +
        str(
            _contract.PROSPECTIVE_BALANCED_ACCURACY_MINIMUM
        )
    )

    print(
        "PROSPECTIVE_MINIMUM_PER_CLASS_RECALL_MINIMUM="
        +
        str(
            _contract.PROSPECTIVE_MINIMUM_PER_CLASS_RECALL_MINIMUM
        )
    )

    print(
        "PROSPECTIVE_MULTICLASS_BRIER_MAXIMUM="
        +
        str(
            _contract.PROSPECTIVE_MULTICLASS_BRIER_MAXIMUM
        )
    )

    print(
        "PROSPECTIVE_MULTICLASS_LOG_LOSS_MAXIMUM="
        +
        str(
            _contract.PROSPECTIVE_MULTICLASS_LOG_LOSS_MAXIMUM
        )
    )

    print(
        "MODEL_ARTIFACT_REQUIRED_BEFORE_COLLECTION=true"
    )

    print(
        "OLD_FORWARD_30_ELIGIBLE=false"
    )

    print(
        "MARKET_DATA_LOADED=false"
    )

    print(
        "PROSPECTIVE_LEDGER_WRITE_PERFORMED=false"
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