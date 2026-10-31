from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]

GATE_ID = (
    "GATE_15D_C_B2D_G5_30_SAMPLE_FORWARD_COLLECTION_COMPLETION_FREEZE"
)

SCHEMA_VERSION = "1.0.2"

BASE_AUTHORITY_COMMIT = (
    "679cab31cdaef786e7059f545133a0bf660fed7f"
)

EXPECTED_MATURED_COUNT = 30
EXPECTED_PENDING_COUNT = 0
EXPECTED_ANCHOR_COUNT = 30
EXPECTED_OUTCOME_COUNT = 30
EXPECTED_OBSERVATION_COUNT = 32
EXPECTED_UNANCHORED_COUNT = 2
EXPECTED_NEXT_ACTION = "RUN_G1_CAPTURE"


G3_RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g3_forward_sample_controller.py"
)

G41_RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g4_1_resilient_autonomous_forward_collector.py"
)

G5_RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g5_30_sample_completion_freeze.py"
)

G5_TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g5_30_sample_completion_freeze.py"
)

EVIDENCE_REL = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g5_30_sample_completion_freeze_evidence.json"
)

EVIDENCE_PATH = (
    REPO_ROOT
    / EVIDENCE_REL
)


OBSERVATION_LEDGER_REL = (
    "01_Data/Shadow/"
    "xauusd_frozen_c04_shadow_observations.jsonl"
)

ANCHOR_LEDGER_REL = (
    "01_Data/Shadow/"
    "xauusd_frozen_c04_forward_outcome_anchors.jsonl"
)

OUTCOME_LEDGER_REL = (
    "01_Data/Shadow/"
    "xauusd_frozen_c04_forward_outcomes.jsonl"
)


HASH_BOUND_DEPENDENCIES = (
    "02_AI/Adapters/"
    "mt5_read_only_forward_acquisition_adapter.py",

    "02_AI/Adapters/"
    "xauusd_broker_adapter.py",

    "02_AI/Models/"
    "frozen_c04_shadow_observer.py",

    "02_AI/Models/"
    "frozen_c04_forward_outcome_anchor.py",

    "02_AI/Models/"
    "frozen_c04_forward_outcome_maturer.py",

    "02_AI/Models/"
    "frozen_c04_forward_outcome_ledger.py",

    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g1_genuine_anchored_forward_capture.py",

    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g2_genuine_outcome_maturation.py",

    G3_RUNNER_REL,
    G41_RUNNER_REL,
    G5_RUNNER_REL,
    G5_TEST_REL,
)


ALLOWED_LOCAL_PATHS = {
    G5_RUNNER_REL,
    G5_TEST_REL,
    EVIDENCE_REL,
}


class G5FreezeError(RuntimeError):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise G5FreezeError(
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

    result = git_process(
        *args
    )

    require(
        result.returncode == 0,
        (
            "GIT_COMMAND_FAILED:"
            + " ".join(args)
            + ":"
            + result.stderr.strip()
        ),
    )

    return result.stdout.rstrip(
        "\r\n"
    )


def normalize_status_path(
    line: str,
) -> str:

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

    return value.replace(
        "\\",
        "/",
    )


def status_paths() -> set[str]:

    output = git_output(
        "status",
        "--porcelain",
        "--untracked-files=all",
    )

    return {
        normalize_status_path(line)
        for line in output.splitlines()
        if len(line) >= 4
    }


def canonical_sha256(
    path: Path,
) -> str:

    data = path.read_bytes()

    normalized = (
        data
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
        normalized
    ).hexdigest()


def raw_sha256(
    path: Path,
) -> str:

    require(
        path.is_file(),
        f"RUNTIME_LEDGER_MISSING:{path}",
    )

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def write_json(
    path: Path,
    document: Mapping[str, Any],
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp = path.with_suffix(
        path.suffix + ".tmp"
    )

    temp.write_text(
        json.dumps(
            dict(document),
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )

    temp.replace(
        path
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

    origin_main = git_output(
        "rev-parse",
        "origin/main",
    )

    require(
        branch == "main",
        f"UNEXPECTED_BRANCH:{branch}",
    )

    require(
        head == origin_main,
        (
            "HEAD_ORIGIN_MAIN_DIVERGENCE:"
            f"{head}!={origin_main}"
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

    local = status_paths()

    unexpected = (
        local
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
        "origin_main": origin_main,
        "allowed_local_paths": sorted(
            local
        ),
    }


def load_g3_module() -> Any:

    path = (
        REPO_ROOT
        / G3_RUNNER_REL
    )

    require(
        path.is_file(),
        "G3_RUNNER_MISSING",
    )

    spec = importlib.util.spec_from_file_location(
        "gate_15d_c_b2d_g3_completion_authority",
        path,
    )

    if spec is None:
        raise G5FreezeError(
            "G3_IMPORT_SPEC_UNAVAILABLE"
        )

    if spec.loader is None:
        raise G5FreezeError(
            "G3_IMPORT_LOADER_UNAVAILABLE"
        )

    module = importlib.util.module_from_spec(
        spec
    )

    spec.loader.exec_module(
        module
    )

    return module


def run_g3_read_only_verification() -> dict[str, Any]:
    """
    Reuse published G3 runtime authority and ledger-state logic directly.

    G3.run_controller() is deliberately not executed because that controller
    requires a completely clean worktree. During creation of G5, the G5
    runner/test/evidence files are intentionally local.

    evaluate_oldest_pending() is also deliberately not executed. The G5
    completion freeze requires pending_count == 0, so no MT5 initialization
    or market-data acquisition is necessary.
    """

    g3 = load_g3_module()

    require(
        hasattr(
            g3,
            "verify_runtime_authorities",
        ),
        "G3_RUNTIME_AUTHORITY_VERIFIER_MISSING",
    )

    require(
        hasattr(
            g3,
            "load_runtime_state",
        ),
        "G3_RUNTIME_STATE_LOADER_MISSING",
    )

    require(
        getattr(
            g3,
            "PERFORMANCE_EVALUATION_AUTHORIZED",
            None,
        )
        is False,
        "G3_PERFORMANCE_AUTHORIZATION_NOT_FALSE",
    )

    require(
        getattr(
            g3,
            "PNL_EVALUATION_AUTHORIZED",
            None,
        )
        is False,
        "G3_PNL_AUTHORIZATION_NOT_FALSE",
    )

    require(
        getattr(
            g3,
            "LIVE_AUTHORIZED",
            None,
        )
        is False,
        "G3_LIVE_AUTHORIZATION_NOT_FALSE",
    )

    require(
        getattr(
            g3,
            "EXECUTION_AUTHORIZED",
            None,
        )
        is False,
        "G3_EXECUTION_AUTHORIZATION_NOT_FALSE",
    )


    g3.verify_runtime_authorities()

    state = g3.load_runtime_state()


    observation_count = int(
        state[
            "observation_count"
        ]
    )

    anchor_count = int(
        state[
            "anchor_count"
        ]
    )

    outcome_count = int(
        state[
            "outcome_count"
        ]
    )

    matured_count = int(
        state[
            "matured_count"
        ]
    )

    pending_count = int(
        state[
            "pending_count"
        ]
    )

    unanchored_count = int(
        state[
            "unanchored_observation_count"
        ]
    )


    require(
        observation_count
        ==
        EXPECTED_OBSERVATION_COUNT,
        (
            "OBSERVATION_COUNT_MISMATCH:"
            f"{observation_count}"
        ),
    )

    require(
        anchor_count
        ==
        EXPECTED_ANCHOR_COUNT,
        (
            "ANCHOR_COUNT_MISMATCH:"
            f"{anchor_count}"
        ),
    )

    require(
        outcome_count
        ==
        EXPECTED_OUTCOME_COUNT,
        (
            "OUTCOME_COUNT_MISMATCH:"
            f"{outcome_count}"
        ),
    )

    require(
        matured_count
        ==
        EXPECTED_MATURED_COUNT,
        (
            "MATURED_COUNT_MISMATCH:"
            f"{matured_count}"
        ),
    )

    require(
        pending_count
        ==
        EXPECTED_PENDING_COUNT,
        (
            "PENDING_COUNT_MISMATCH:"
            f"{pending_count}"
        ),
    )

    require(
        unanchored_count
        ==
        EXPECTED_UNANCHORED_COUNT,
        (
            "UNANCHORED_COUNT_MISMATCH:"
            f"{unanchored_count}"
        ),
    )


    pending = state.get(
        "pending",
        [],
    )

    require(
        len(pending) == 0,
        (
            "PENDING_RUNTIME_RECORDS_PRESENT:"
            f"{len(pending)}"
        ),
    )


    next_action = (
        "RUN_G1_CAPTURE"
        if pending_count == 0
        else "UNRESOLVED"
    )

    require(
        next_action
        ==
        EXPECTED_NEXT_ACTION,
        (
            "UNEXPECTED_G3_NEXT_ACTION:"
            f"{next_action}:expected="
            f"{EXPECTED_NEXT_ACTION}"
        ),
    )


    return {
        "status": "PASS",

        "observation_count": (
            observation_count
        ),

        "anchor_count": (
            anchor_count
        ),

        "outcome_count": (
            outcome_count
        ),

        "matured_count": (
            matured_count
        ),

        "pending_count": (
            pending_count
        ),

        "unanchored_observation_count": (
            unanchored_count
        ),

        "next_action": (
            next_action
        ),

        "g3_runtime_authorities_verified": (
            True
        ),

        "g3_runtime_state_loader_reused": (
            True
        ),

        "g3_controller_executed": False,

        "mt5_initialized": False,

        "market_data_acquired": False,

        "performance_evaluated": False,

        "pnl_evaluated": False,

        "live_authorized": False,

        "execution_authorized": False,
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

    observation_path = (
        REPO_ROOT
        / OBSERVATION_LEDGER_REL
    )

    anchor_path = (
        REPO_ROOT
        / ANCHOR_LEDGER_REL
    )

    outcome_path = (
        REPO_ROOT
        / OUTCOME_LEDGER_REL
    )


    runtime_before = {
        "observation": raw_sha256(
            observation_path
        ),
        "anchor": raw_sha256(
            anchor_path
        ),
        "outcome": raw_sha256(
            outcome_path
        ),
    }


    repository = (
        verify_repository()
    )

    g3 = (
        run_g3_read_only_verification()
    )

    hashes = (
        dependency_hashes()
    )


    runtime_after = {
        "observation": raw_sha256(
            observation_path
        ),
        "anchor": raw_sha256(
            anchor_path
        ),
        "outcome": raw_sha256(
            outcome_path
        ),
    }


    require(
        runtime_before
        ==
        runtime_after,
        "RUNTIME_LEDGER_CHANGED_DURING_FREEZE",
    )


    evidence = {
        "gate_id": GATE_ID,

        "schema_version": (
            SCHEMA_VERSION
        ),

        "status": "PASS",

        "base_authority_commit": (
            BASE_AUTHORITY_COMMIT
        ),

        "repository_authority": (
            repository
        ),

        "forward_collection_completion": (
            g3
        ),

        "target_matured_samples": (
            EXPECTED_MATURED_COUNT
        ),

        "target_reached": True,

        "runtime_ledger_raw_sha256": (
            runtime_after
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

        "g3_controller_executed": False,

        "collector_executed": False,

        "mt5_initialized": False,

        "market_data_acquired": False,

        "ledger_write_performed": False,

        "observation_ledger_unchanged": True,

        "anchor_ledger_unchanged": True,

        "outcome_ledger_unchanged": True,

        "performance_evaluation_authorized": False,

        "performance_evaluated": False,

        "pnl_evaluation_authorized": False,

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
            "GATE_15D_C_B2D_G5_FREEZE_STATUS=BLOCKED"
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
            "G3_CONTROLLER_EXECUTED=false"
        )

        print(
            "MT5_INITIALIZED=false"
        )

        print(
            "MARKET_DATA_ACQUIRED=false"
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

        return 2


    completion = evidence[
        "forward_collection_completion"
    ]

    print(
        "GATE_15D_C_B2D_G5_FREEZE_STATUS=PASS"
    )

    print(
        "BASE_AUTHORITY_COMMIT="
        + evidence[
            "base_authority_commit"
        ]
    )

    print(
        "OBSERVATION_COUNT="
        + str(
            completion[
                "observation_count"
            ]
        )
    )

    print(
        "ANCHOR_COUNT="
        + str(
            completion[
                "anchor_count"
            ]
        )
    )

    print(
        "OUTCOME_COUNT="
        + str(
            completion[
                "outcome_count"
            ]
        )
    )

    print(
        "MATURED_COUNT="
        + str(
            completion[
                "matured_count"
            ]
        )
    )

    print(
        "PENDING_COUNT="
        + str(
            completion[
                "pending_count"
            ]
        )
    )

    print(
        "UNANCHORED_OBSERVATION_COUNT="
        + str(
            completion[
                "unanchored_observation_count"
            ]
        )
    )

    print(
        "NEXT_ACTION="
        + str(
            completion[
                "next_action"
            ]
        )
    )

    print(
        "TARGET_REACHED=true"
    )

    print(
        "G3_RUNTIME_AUTHORITIES_VERIFIED=true"
    )

    print(
        "G3_RUNTIME_STATE_LOADER_REUSED=true"
    )

    print(
        "G3_CONTROLLER_EXECUTED=false"
    )

    print(
        "HASH_BOUND_FILE_COUNT="
        + str(
            evidence[
                "hash_bound_file_count"
            ]
        )
    )

    print(
        "MT5_INITIALIZED=false"
    )

    print(
        "MARKET_DATA_ACQUIRED=false"
    )

    print(
        "LEDGER_WRITE_PERFORMED=false"
    )

    print(
        "OBSERVATION_LEDGER_UNCHANGED=true"
    )

    print(
        "ANCHOR_LEDGER_UNCHANGED=true"
    )

    print(
        "OUTCOME_LEDGER_UNCHANGED=true"
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