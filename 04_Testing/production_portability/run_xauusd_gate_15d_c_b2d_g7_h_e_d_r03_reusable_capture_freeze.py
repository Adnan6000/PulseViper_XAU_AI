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
    "80c05a1270081cafd136cac40309f27302796d15"
)

GATE_ID = (
    "GATE_15D_C_B2D_G7_H_E_D_"
    "R03_REUSABLE_CAPTURE_RUNNER_FREEZE"
)

RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_h_e_d_"
    "r03_reusable_capture.py"
)

FREEZE_RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_h_e_d_"
    "r03_reusable_capture_freeze.py"
)

TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g7_h_e_d_"
    "r03_reusable_capture_freeze.py"
)

EVIDENCE_REL = (
    "04_Testing/evidence/research/"
    "portable_331/remediation/"
    "xauusd_gate_15d_c_b2d_g7_h_e_d_"
    "r03_reusable_capture_runner_freeze.json"
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
    RUNNER_REL,
    FREEZE_RUNNER_REL,
    TEST_REL,
    EVIDENCE_REL,
    OBSERVATION_LEDGER_REL,
    ANCHOR_LEDGER_REL,
    OUTCOME_LEDGER_REL,
}


class G7HEDFreezeError(
    RuntimeError
):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise G7HEDFreezeError(
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


def ledger_hash(
    relative: str,
) -> str | None:

    path = (
        REPO_ROOT
        /
        relative
    )

    if not path.exists():
        return None

    return sha256_file(
        path
    )


def runtime_ledger_hashes() -> dict[
    str,
    str | None,
]:

    return {
        "observation": (
            ledger_hash(
                OBSERVATION_LEDGER_REL
            )
        ),
        "anchor": (
            ledger_hash(
                ANCHOR_LEDGER_REL
            )
        ),
        "outcome": (
            ledger_hash(
                OUTCOME_LEDGER_REL
            )
        ),
    }


def verify_repository() -> None:

    fetch = git_process(
        "fetch",
        "origin",
    )

    require(
        fetch.returncode == 0,
        "GIT_FETCH_ORIGIN_FAILED",
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
        "PortableFeaturePipeline",
        "capture_new_observation_from_snapshot",
        "ANCHOR_FIRST_THEN_OBSERVATION=true",
        "CAPTURE_REQUIRES_ZERO_PENDING",
        "COLLECTION_TARGET_ALREADY_REACHED",
        "OUTCOME_MATURED=false",
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
        "mature_pending_from_snapshot(",
        "evaluate_prospective_confirmation(",
        "order_send(",
        "order_check(",
        "RiskEngine(",
        "trade_ready",
        ".fit(",
        "load_test(",
        "load_validation(",
    )

    for token in forbidden:

        require(
            token not in runner_text,
            (
                "FORBIDDEN_TOKEN_PRESENT:"
                f"{token}"
            ),
        )


def verify_collection_state() -> dict[
    str,
    Any,
]:

    state = (
        _controller.inspect_state(
            repo_root=REPO_ROOT
        )
    )

    require(
        state.observation_count == 1,
        (
            "EXPECTED_ONE_OBSERVATION:"
            f"{state.observation_count}"
        ),
    )

    require(
        state.anchor_count == 1,
        (
            "EXPECTED_ONE_ANCHOR:"
            f"{state.anchor_count}"
        ),
    )

    require(
        state.matured_outcome_count == 1,
        (
            "EXPECTED_ONE_MATURED_OUTCOME:"
            f"{state.matured_outcome_count}"
        ),
    )

    require(
        state.pending_count == 0,
        (
            "EXPECTED_ZERO_PENDING:"
            f"{state.pending_count}"
        ),
    )

    require(
        state.orphan_anchor_count == 0,
        (
            "EXPECTED_ZERO_ORPHAN_ANCHORS:"
            f"{state.orphan_anchor_count}"
        ),
    )

    require(
        state.next_action
        ==
        _controller.ACTION_CAPTURE_NEW_OBSERVATION,
        (
            "CAPTURE_ACTION_NOT_AUTHORIZED:"
            f"{state.next_action}"
        ),
    )

    require(
        state.collection_target_reached
        is False,
        "COLLECTION_TARGET_UNEXPECTEDLY_REACHED",
    )

    return state.to_dict()


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

    ledger_hashes_before = (
        runtime_ledger_hashes()
    )

    state_before = (
        verify_collection_state()
    )

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

    state_after = (
        verify_collection_state()
    )

    ledger_hashes_after = (
        runtime_ledger_hashes()
    )

    require(
        state_after
        ==
        state_before,
        "FREEZE_CHANGED_COLLECTION_STATE",
    )

    require(
        ledger_hashes_after
        ==
        ledger_hashes_before,
        "FREEZE_MUTATED_RUNTIME_LEDGER",
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
            state_before
        ),
        "runtime_ledger_hashes_at_freeze": (
            ledger_hashes_before
        ),
        "capture_executed": False,
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
            "GATE_15D_C_B2D_G7_H_E_D_FREEZE_STATUS=BLOCKED"
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
            "CAPTURE_EXECUTED=false"
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
        "GATE_15D_C_B2D_G7_H_E_D_FREEZE_STATUS=PASS"
    )

    print(
        "BASE_AUTHORITY_COMMIT="
        +
        BASE_AUTHORITY_COMMIT
    )

    print(
        "OBSERVATION_COUNT=1"
    )

    print(
        "ANCHOR_COUNT=1"
    )

    print(
        "MATURED_OUTCOME_COUNT=1"
    )

    print(
        "PENDING_OUTCOMES=0"
    )

    print(
        "CAPTURE_EXECUTED=false"
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