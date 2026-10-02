from __future__ import annotations

import hashlib
import importlib
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
    "GATE_15D_C_B2D_G6_A_FORWARD_EVALUATION_PROTOCOL_FREEZE"
)

SCHEMA_VERSION = "1.0.0"

BASE_AUTHORITY_COMMIT = (
    "c82abaf6008e9239cecae5fef4fde24936ad6358"
)


CONTRACT_REL = (
    "02_AI/Models/"
    "frozen_c04_forward_performance_evaluation_contract.py"
)

G5_RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g5_30_sample_completion_freeze.py"
)

G5_EVIDENCE_REL = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g5_30_sample_completion_freeze_evidence.json"
)

G6A_RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g6_a_forward_evaluation_protocol_freeze.py"
)

G6A_TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g6_a_forward_evaluation_protocol_freeze.py"
)

EVIDENCE_REL = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g6_a_forward_evaluation_protocol_freeze_evidence.json"
)

EVIDENCE_PATH = (
    REPO_ROOT
    / EVIDENCE_REL
)


ALLOWED_LOCAL_PATHS = {
    CONTRACT_REL,
    G6A_RUNNER_REL,
    G6A_TEST_REL,
    EVIDENCE_REL,
}


HASH_BOUND_DEPENDENCIES = (
    CONTRACT_REL,
    G5_RUNNER_REL,
    G5_EVIDENCE_REL,
    G6A_RUNNER_REL,
    G6A_TEST_REL,
)


_contract: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_performance_evaluation_contract"
)


class G6AFreezeError(RuntimeError):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise G6AFreezeError(
            reason
        )


def git_process(
    *args: str,
) -> subprocess.CompletedProcess[str]:

    return subprocess.run(
        [
            "git",
            *args,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def git_output(
    *args: str,
) -> str:

    process = git_process(
        *args
    )

    require(
        process.returncode == 0,
        (
            "GIT_COMMAND_FAILED:"
            + " ".join(args)
            + ":"
            + process.stderr.strip()
        ),
    )

    return process.stdout.rstrip(
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

        paths.add(
            value.replace(
                "\\",
                "/",
            )
        )

    return paths


def canonical_sha256(
    path: Path,
) -> str:

    data = (
        path.read_bytes()
        .replace(
            b"\r\n",
            b"\n",
        )
        .replace(
            b"\r",
            b"\n",
        )
    )

    return hashlib.sha256(
        data
    ).hexdigest()


def write_json(
    path: Path,
    document: Mapping[str, Any],
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            dict(document),
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


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

    dirty = status_paths()

    unexpected = (
        dirty
        - ALLOWED_LOCAL_PATHS
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
        "allowed_local_paths": sorted(
            dirty
        ),
    }


def verify_g5_baseline() -> dict[str, Any]:

    path = (
        REPO_ROOT
        / G5_EVIDENCE_REL
    )

    require(
        path.is_file(),
        "G5_EVIDENCE_MISSING",
    )

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    require(
        data.get(
            "status"
        )
        ==
        "PASS",
        "G5_STATUS_NOT_PASS",
    )

    require(
        data.get(
            "target_reached"
        )
        is True,
        "G5_TARGET_NOT_REACHED",
    )

    completion = data.get(
        "forward_collection_completion"
    )

    require(
        isinstance(
            completion,
            dict,
        ),
        "G5_COMPLETION_MISSING",
    )

    require(
        int(
            completion.get(
                "matured_count",
                -1,
            )
        )
        ==
        30,
        "G5_MATURED_COUNT_NOT_30",
    )

    require(
        int(
            completion.get(
                "pending_count",
                -1,
            )
        )
        ==
        0,
        "G5_PENDING_COUNT_NOT_ZERO",
    )

    require(
        data.get(
            "performance_evaluated"
        )
        is False,
        "G5_PERFORMANCE_ALREADY_EVALUATED",
    )

    require(
        data.get(
            "pnl_evaluated"
        )
        is False,
        "G5_PNL_ALREADY_EVALUATED",
    )

    require(
        data.get(
            "live_authorized"
        )
        is False,
        "G5_LIVE_ALREADY_AUTHORIZED",
    )

    require(
        data.get(
            "execution_authorized"
        )
        is False,
        "G5_EXECUTION_ALREADY_AUTHORIZED",
    )

    return {
        "status": "PASS",
        "matured_count": 30,
        "pending_count": 0,
        "g5_evidence_sha256": (
            canonical_sha256(
                path
            )
        ),
    }


def verify_contract() -> dict[str, Any]:

    require(
        _contract.CONTRACT_ID
        ==
        "FROZEN_C04_FORWARD_PERFORMANCE_EVALUATION_CONTRACT_V1",
        "CONTRACT_ID_MISMATCH",
    )

    require(
        _contract.BASELINE_G5_AUTHORITY_COMMIT
        ==
        BASE_AUTHORITY_COMMIT,
        "BASELINE_G5_AUTHORITY_MISMATCH",
    )

    require(
        _contract.BASELINE_MATURED_OUTCOME_COUNT
        ==
        30,
        "BASELINE_COUNT_MISMATCH",
    )

    require(
        _contract.EVALUATION_CADENCE
        ==
        "WEEKLY",
        "WEEKLY_CADENCE_NOT_FROZEN",
    )

    require(
        _contract.MINIMUM_NEW_WEEKLY_SAMPLE_COUNT
        ==
        0,
        "MINIMUM_WEEKLY_SAMPLE_WAIT_PRESENT",
    )

    require(
        _contract.FIXED_COUNT_WAIT_REQUIRED
        is False,
        "FIXED_COUNT_WAIT_PRESENT",
    )

    require(
        _contract.MULTI_DAY_FIXED_SAMPLE_COLLECTION_REQUIRED
        is False,
        "MULTI_DAY_FIXED_COLLECTION_PRESENT",
    )

    require(
        _contract.PROBABILITY_CALIBRATION_ALLOWED
        is False,
        "CALIBRATION_ALLOWED",
    )

    require(
        _contract.RETRAINING_ALLOWED
        is False,
        "RETRAINING_ALLOWED",
    )

    require(
        _contract.MODEL_RESELECTION_ALLOWED
        is False,
        "MODEL_RESELECTION_ALLOWED",
    )

    require(
        _contract.THRESHOLD_TUNING_ALLOWED
        is False,
        "THRESHOLD_TUNING_ALLOWED",
    )

    require(
        _contract.PASS_FAIL_THRESHOLD_DEFINED
        is False,
        "PASS_FAIL_THRESHOLD_PREMATURELY_DEFINED",
    )

    require(
        _contract.PNL_EVALUATION_AUTHORIZED
        is False,
        "PNL_EVALUATION_AUTHORIZED",
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
        "contract_fingerprint_sha256": (
            fingerprint
        ),
        "evaluation_cadence": "WEEKLY",
        "minimum_new_weekly_sample_count": 0,
        "fixed_count_wait_required": False,
        "metric_count": len(
            _contract.FROZEN_METRICS
        ),
    }


def dependency_hashes() -> dict[str, str]:

    result: dict[str, str] = {}

    for relative in (
        HASH_BOUND_DEPENDENCIES
    ):

        path = (
            REPO_ROOT
            / relative
        )

        require(
            path.is_file(),
            (
                "HASH_BOUND_FILE_MISSING:"
                f"{relative}"
            ),
        )

        result[
            relative
        ] = canonical_sha256(
            path
        )

    return result


def run_gate() -> dict[str, Any]:

    repository = (
        verify_repository()
    )

    baseline = (
        verify_g5_baseline()
    )

    contract = (
        verify_contract()
    )

    hashes = (
        dependency_hashes()
    )

    evidence = {
        "gate_id": GATE_ID,
        "schema_version": SCHEMA_VERSION,
        "status": "PASS",
        "base_authority_commit": (
            BASE_AUTHORITY_COMMIT
        ),
        "repository_authority": (
            repository
        ),
        "g5_baseline": (
            baseline
        ),
        "evaluation_contract": (
            contract
        ),
        "hashing_semantics": (
            "GIT_TEXT_CANONICAL_LF_SHA256"
        ),
        "hash_bound_dependencies": (
            hashes
        ),
        "hash_bound_file_count": (
            len(hashes)
        ),
        "performance_calculated": False,
        "pnl_evaluated": False,
        "retraining_performed": False,
        "calibration_performed": False,
        "model_reselection_performed": False,
        "threshold_tuning_performed": False,
        "ledger_write_performed": False,
        "market_data_acquired": False,
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
            "GATE_15D_C_B2D_G6_A_FREEZE_STATUS=BLOCKED"
        )
        print(
            "ERROR_TYPE="
            + type(exc).__name__
        )
        print(
            "ERROR="
            + str(exc)
        )
        print(
            "PERFORMANCE_CALCULATED=false"
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

    contract = evidence[
        "evaluation_contract"
    ]

    print(
        "GATE_15D_C_B2D_G6_A_FREEZE_STATUS=PASS"
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
        "EVALUATION_CADENCE=WEEKLY"
    )
    print(
        "BASELINE_MATURED_OUTCOMES=30"
    )
    print(
        "MINIMUM_NEW_WEEKLY_SAMPLE_COUNT=0"
    )
    print(
        "FIXED_COUNT_WAIT_REQUIRED=false"
    )
    print(
        "PERFORMANCE_CALCULATED=false"
    )
    print(
        "PNL_EVALUATED=false"
    )
    print(
        "RETRAINING_PERFORMED=false"
    )
    print(
        "CALIBRATION_PERFORMED=false"
    )
    print(
        "MODEL_RESELECTION_PERFORMED=false"
    )
    print(
        "THRESHOLD_TUNING_PERFORMED=false"
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