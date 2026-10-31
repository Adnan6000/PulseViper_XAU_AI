from __future__ import annotations

import hashlib
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


BASE_AUTHORITY_COMMIT = (
    "d138717f1cb1d80584479289f71e95b0c5b9fe6f"
)

GATE_ID = (
    "GATE_15D_C_B2D_G7_H_E_B_R2_"
    "FIRST_GENUINE_R03_CAPTURE_RECOVERY_RUNNER_FREEZE"
)

ORIGINAL_BLOCKED_EVIDENCE_REL = (
    "04_Testing/evidence/research/"
    "portable_331/remediation/"
    "xauusd_gate_15d_c_b2d_g7_h_e_b_"
    "first_genuine_r03_capture_blocked.json"
)

RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_h_e_b_r2_"
    "first_genuine_r03_capture_recovery.py"
)

FREEZE_RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_h_e_b_r2_"
    "first_genuine_r03_capture_recovery_freeze.py"
)

TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g7_h_e_b_r2_"
    "first_genuine_r03_capture_recovery_freeze.py"
)

EVIDENCE_REL = (
    "04_Testing/evidence/research/"
    "portable_331/remediation/"
    "xauusd_gate_15d_c_b2d_g7_h_e_b_r2_"
    "first_genuine_r03_capture_recovery_runner_freeze.json"
)

ORIGINAL_BLOCKED_EVIDENCE_PATH = (
    REPO_ROOT
    /
    ORIGINAL_BLOCKED_EVIDENCE_REL
)

EVIDENCE_PATH = (
    REPO_ROOT
    /
    EVIDENCE_REL
)


ALLOWED_LOCAL_PATHS = {
    ORIGINAL_BLOCKED_EVIDENCE_REL,
    RUNNER_REL,
    FREEZE_RUNNER_REL,
    TEST_REL,
    EVIDENCE_REL,
}


R03_LEDGER_PATHS = (
    (
        "01_Data/Shadow/"
        "xauusd_r03_prospective_observations.jsonl"
    ),
    (
        "01_Data/Shadow/"
        "xauusd_r03_prospective_forward_outcome_anchors.jsonl"
    ),
    (
        "01_Data/Shadow/"
        "xauusd_r03_prospective_forward_outcomes.jsonl"
    ),
)


class RecoveryFreezeError(
    RuntimeError
):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise RecoveryFreezeError(
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

            chunk = handle.read(
                1024 * 1024
            )

            if not chunk:
                break

            digest.update(
                chunk
            )

    return digest.hexdigest()


def git_output(
    *args: str,
) -> str:

    process = subprocess.run(
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
        process.returncode == 0,
        (
            "GIT_COMMAND_FAILED:"
            +
            " ".join(
                args
            )
        ),
    )

    return process.stdout.rstrip(
        "\r\n"
    )


def status_paths() -> set[str]:

    raw = git_output(
        "status",
        "--porcelain",
        "--untracked-files=all",
    )

    output: set[str] = set()

    for line in raw.splitlines():

        if len(line) < 4:
            continue

        value = (
            line[3:]
            .strip()
            .replace(
                "\\",
                "/",
            )
        )

        if " -> " in value:
            value = value.split(
                " -> ",
                1,
            )[1]

        output.add(
            value
        )

    return output


def verify_repository() -> None:

    git_output(
        "fetch",
        "origin",
    )

    require(
        git_output(
            "branch",
            "--show-current",
        )
        ==
        "main",
        "UNEXPECTED_BRANCH",
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
        head == origin,
        "HEAD_ORIGIN_MAIN_DIVERGENCE",
    )

    require(
        head
        ==
        BASE_AUTHORITY_COMMIT,
        (
            "BASE_AUTHORITY_MISMATCH:"
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


def verify_original_blocked_evidence() -> dict[
    str,
    Any,
]:

    require(
        ORIGINAL_BLOCKED_EVIDENCE_PATH.is_file(),
        "ORIGINAL_BLOCKED_EVIDENCE_MISSING",
    )

    raw = json.loads(
        ORIGINAL_BLOCKED_EVIDENCE_PATH
        .read_text(
            encoding="utf-8"
        )
    )

    require(
        isinstance(
            raw,
            dict,
        ),
        "ORIGINAL_BLOCKED_EVIDENCE_INVALID",
    )

    require(
        raw.get(
            "status"
        )
        ==
        "BLOCKED",
        "ORIGINAL_BLOCKED_STATUS_MISMATCH",
    )

    require(
        raw.get(
            "error_type"
        )
        ==
        "TimestampBasisResolutionError",
        "ORIGINAL_BLOCK_ERROR_TYPE_MISMATCH",
    )

    error = raw.get(
        "error"
    )

    require(
        isinstance(
            error,
            str,
        )
        and
        "TIMESTAMP_BASIS_NOT_UNIQUELY_PROVEN"
        in
        error,
        "ORIGINAL_TIMESTAMP_BASIS_ERROR_MISSING",
    )

    return {
        "sha256": (
            sha256_file(
                ORIGINAL_BLOCKED_EVIDENCE_PATH
            )
        ),
        "error_type": (
            raw.get(
                "error_type"
            )
        ),
        "error": error,
    }


def verify_r03_ledgers_absent() -> None:

    for relative in R03_LEDGER_PATHS:

        require(
            not (
                REPO_ROOT
                /
                relative
            ).exists(),
            (
                "R03_LEDGER_ALREADY_EXISTS:"
                f"{relative}"
            ),
        )


def static_safety_audit() -> None:

    runner_text = (
        REPO_ROOT
        /
        RUNNER_REL
    ).read_text(
        encoding="utf-8"
    )

    required = (
        "MT5ReadOnlyCapabilityFacade",
        "MT5ReadOnlyForwardAcquisitionAdapter",
        'timestamp_basis="AUTO"',
        "enforce_forward_boundaries=True",
        "PortableFeaturePipeline",
        "capture_new_observation_from_snapshot",
        "ANCHOR_FIRST_THEN_OBSERVATION",
        "ORIGINAL_BLOCKED_ATTEMPT_PRESERVED=true",
        "LIVE_AUTHORIZED=false",
        "EXECUTION_AUTHORIZED=false",
    )

    for token in required:

        require(
            token in runner_text,
            (
                "REQUIRED_TOKEN_MISSING:"
                f"{token}"
            ),
        )

    forbidden = (
        "order_send(",
        "order_check(",
        "RiskEngine(",
        "trade_ready",
        ".fit(",
        "load_test(",
        "load_validation(",
        "mature_pending_from_snapshot(",
        "evaluate_prospective_confirmation(",
    )

    for token in forbidden:

        require(
            token not in runner_text,
            (
                "FORBIDDEN_TOKEN_PRESENT:"
                f"{token}"
            ),
        )


def write_evidence(
    document: Mapping[
        str,
        Any,
    ],
) -> None:

    require(
        not EVIDENCE_PATH.exists(),
        "EVIDENCE_ALREADY_EXISTS",
    )

    EVIDENCE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with EVIDENCE_PATH.open(
        "x",
        encoding="utf-8",
    ) as handle:

        handle.write(
            json.dumps(
                dict(
                    document
                ),
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
            )
            +
            "\n"
        )


def run_gate() -> dict[
    str,
    Any,
]:

    verify_repository()

    original = (
        verify_original_blocked_evidence()
    )

    verify_r03_ledgers_absent()

    static_safety_audit()

    candidate_hashes = {
        relative: sha256_file(
            REPO_ROOT
            /
            relative
        )
        for relative
        in (
            RUNNER_REL,
            FREEZE_RUNNER_REL,
            TEST_REL,
        )
    }

    verify_r03_ledgers_absent()

    evidence = {
        "gate_id": GATE_ID,
        "status": "PASS",
        "base_authority_commit": (
            BASE_AUTHORITY_COMMIT
        ),
        "original_blocked_evidence_path": (
            ORIGINAL_BLOCKED_EVIDENCE_REL
        ),
        "original_blocked_evidence_sha256": (
            original[
                "sha256"
            ]
        ),
        "original_block_reason": {
            "error_type": (
                original[
                    "error_type"
                ]
            ),
            "error": (
                original[
                    "error"
                ]
            ),
        },
        "candidate_artifact_hashes": (
            candidate_hashes
        ),
        "recovery_capture_executed": False,
        "real_market_data_loaded": False,
        "r03_ledgers_created": False,
        "r03_ledgers_written": False,
        "performance_evaluated": False,
        "pnl_evaluated": False,
        "live_authorized": False,
        "execution_authorized": False,
    }

    write_evidence(
        evidence
    )

    return evidence


def main() -> int:

    try:

        _ = run_gate()

    except Exception as exc:

        print(
            "GATE_15D_C_B2D_G7_H_E_B_R2_FREEZE_STATUS=BLOCKED"
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
            "R03_LEDGERS_WRITTEN=false"
        )

        print(
            "LIVE_AUTHORIZED=false"
        )

        print(
            "EXECUTION_AUTHORIZED=false"
        )

        return 2

    print(
        "GATE_15D_C_B2D_G7_H_E_B_R2_FREEZE_STATUS=PASS"
    )

    print(
        "BASE_AUTHORITY_COMMIT="
        +
        BASE_AUTHORITY_COMMIT
    )

    print(
        "ORIGINAL_BLOCKED_EVIDENCE_PRESERVED=true"
    )

    print(
        "RECOVERY_CAPTURE_EXECUTED=false"
    )

    print(
        "REAL_MARKET_DATA_LOADED=false"
    )

    print(
        "R03_LEDGERS_CREATED=false"
    )

    print(
        "R03_LEDGERS_WRITTEN=false"
    )

    print(
        "PERFORMANCE_EVALUATED=false"
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