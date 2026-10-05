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


BASE_AUTHORITY_COMMIT = (
    "76902059fc972c4f7088f39cd5bed36da949acba"
)

GATE_ID = (
    "GATE_15D_C_B2D_G7_H_E_C_"
    "R03_PENDING_MATURITY_RUNNER_FREEZE"
)

R2_CAPTURE_EVIDENCE_REL = (
    "04_Testing/evidence/research/"
    "portable_331/remediation/"
    "xauusd_gate_15d_c_b2d_g7_h_e_b_r2_"
    "first_genuine_r03_capture_recovery.json"
)

RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_h_e_c_"
    "r03_pending_maturity.py"
)

FREEZE_RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_h_e_c_"
    "r03_pending_maturity_freeze.py"
)

TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g7_h_e_c_"
    "r03_pending_maturity_freeze.py"
)

EVIDENCE_REL = (
    "04_Testing/evidence/research/"
    "portable_331/remediation/"
    "xauusd_gate_15d_c_b2d_g7_h_e_c_"
    "r03_pending_maturity_runner_freeze.json"
)

EVIDENCE_PATH = (
    REPO_ROOT
    /
    EVIDENCE_REL
)


_controller: Any = importlib.import_module(
    "02_AI.Models."
    "r03_prospective_collection_controller"
)


OBSERVATION_LEDGER_REL = str(
    _controller
    .OBSERVATION_LEDGER_RELATIVE_PATH
)

ANCHOR_LEDGER_REL = str(
    _controller
    .ANCHOR_LEDGER_RELATIVE_PATH
)

OUTCOME_LEDGER_REL = str(
    _controller
    .OUTCOME_LEDGER_RELATIVE_PATH
)


ALLOWED_LOCAL_PATHS = {
    R2_CAPTURE_EVIDENCE_REL,
    RUNNER_REL,
    FREEZE_RUNNER_REL,
    TEST_REL,
    EVIDENCE_REL,
    OBSERVATION_LEDGER_REL,
    ANCHOR_LEDGER_REL,
    OUTCOME_LEDGER_REL,
}


class G7HECFreezeError(
    RuntimeError
):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise G7HECFreezeError(
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


def optional_sha256(
    path: Path,
) -> str | None:

    if not path.exists():
        return None

    return sha256_file(
        path
    )


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
        "mature_pending_from_snapshot",
        "WAIT_FOR_MORE_COMPLETED_M5_BARS",
        "MATURED_PENDING_OUTCOME",
        "PERFORMANCE_EVALUATED=false",
        "PNL_EVALUATED=false",
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
        "capture_new_observation_from_snapshot(",
        "PortableFeaturePipeline(",
        ".fit(",
        "load_test(",
        "load_validation(",
        "order_send(",
        "order_check(",
        "RiskEngine(",
        "trade_ready",
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
        "FREEZE_EVIDENCE_ALREADY_EXISTS",
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

    before = (
        _controller.inspect_state(
            repo_root=REPO_ROOT
        )
    )

    require(
        before.observation_count == 1,
        (
            "EXPECTED_ONE_OBSERVATION:"
            f"{before.observation_count}"
        ),
    )

    require(
        before.anchor_count == 1,
        (
            "EXPECTED_ONE_ANCHOR:"
            f"{before.anchor_count}"
        ),
    )

    require(
        before.matured_outcome_count == 0,
        (
            "EXPECTED_ZERO_OUTCOMES:"
            f"{before.matured_outcome_count}"
        ),
    )

    require(
        before.pending_count == 1,
        (
            "EXPECTED_ONE_PENDING:"
            f"{before.pending_count}"
        ),
    )

    require(
        before.next_action
        ==
        _controller.ACTION_CHECK_PENDING_MATURITY,
        (
            "EXPECTED_MATURITY_ACTION:"
            f"{before.next_action}"
        ),
    )

    ledger_paths = {
        "observation": (
            REPO_ROOT
            /
            OBSERVATION_LEDGER_REL
        ),
        "anchor": (
            REPO_ROOT
            /
            ANCHOR_LEDGER_REL
        ),
        "outcome": (
            REPO_ROOT
            /
            OUTCOME_LEDGER_REL
        ),
    }

    ledger_hashes_before = {
        name: optional_sha256(
            path
        )
        for name, path
        in ledger_paths.items()
    }

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

    after = (
        _controller.inspect_state(
            repo_root=REPO_ROOT
        )
    )

    ledger_hashes_after = {
        name: optional_sha256(
            path
        )
        for name, path
        in ledger_paths.items()
    }

    require(
        ledger_hashes_before
        ==
        ledger_hashes_after,
        "FREEZE_MUTATED_RUNTIME_LEDGER",
    )

    require(
        before.to_dict()
        ==
        after.to_dict(),
        "FREEZE_CHANGED_COLLECTION_STATE",
    )

    evidence = {
        "gate_id": GATE_ID,
        "status": "PASS",
        "base_authority_commit": (
            BASE_AUTHORITY_COMMIT
        ),
        "candidate_artifact_hashes": (
            candidate_hashes
        ),
        "collection_state_at_freeze": (
            before.to_dict()
        ),
        "runtime_ledger_hashes_at_freeze": (
            ledger_hashes_before
        ),
        "maturation_executed": False,
        "real_market_data_loaded": False,
        "runtime_ledgers_written": False,
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
            "GATE_15D_C_B2D_G7_H_E_C_FREEZE_STATUS=BLOCKED"
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
            "MATURATION_EXECUTED=false"
        )

        print(
            "RUNTIME_LEDGERS_WRITTEN=false"
        )

        print(
            "LIVE_AUTHORIZED=false"
        )

        print(
            "EXECUTION_AUTHORIZED=false"
        )

        return 2

    print(
        "GATE_15D_C_B2D_G7_H_E_C_FREEZE_STATUS=PASS"
    )

    print(
        "BASE_AUTHORITY_COMMIT="
        +
        BASE_AUTHORITY_COMMIT
    )

    print(
        "PENDING_OUTCOMES=1"
    )

    print(
        "MATURATION_EXECUTED=false"
    )

    print(
        "REAL_MARKET_DATA_LOADED=false"
    )

    print(
        "RUNTIME_LEDGERS_WRITTEN=false"
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