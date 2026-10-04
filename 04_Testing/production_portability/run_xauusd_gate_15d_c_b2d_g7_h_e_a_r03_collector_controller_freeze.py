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
        str(
            REPO_ROOT
        ),
    )


BASE_AUTHORITY_COMMIT = (
    "d9ad9e5b1c5deb2e3b62f6110a1f5b4ffe934d08"
)

GATE_ID = (
    "GATE_15D_C_B2D_G7_H_E_A_"
    "R03_COLLECTOR_CONTROLLER_FREEZE"
)

CONTROLLER_REL = (
    "02_AI/Models/"
    "r03_prospective_collection_controller.py"
)

RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_h_e_a_"
    "r03_collector_controller_freeze.py"
)

TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g7_h_e_a_"
    "r03_collector_controller_freeze.py"
)

EVIDENCE_REL = (
    "04_Testing/evidence/research/"
    "portable_331/remediation/"
    "xauusd_gate_15d_c_b2d_g7_h_e_a_"
    "r03_collector_controller_freeze.json"
)

EVIDENCE_PATH = (
    REPO_ROOT
    /
    EVIDENCE_REL
)


ALLOWED_LOCAL_PATHS = {
    CONTROLLER_REL,
    RUNNER_REL,
    TEST_REL,
    EVIDENCE_REL,
}


PROTECTED_LEDGER_PATHS = (
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


_controller: Any = importlib.import_module(
    "02_AI.Models."
    "r03_prospective_collection_controller"
)

_runtime: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_r03_prospective_runtime"
)

_maturer: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_r03_prospective_outcome_maturer"
)

_contract: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_r03_prospective_forward_validation_contract"
)


class G7HEAError(
    RuntimeError
):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:

        raise G7HEAError(
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


def optional_hash(
    path: Path,
) -> str | None:

    if not path.exists():
        return None

    return sha256_file(
        path
    )


def protected_states() -> dict[
    str,
    str | None,
]:

    return {
        relative: optional_hash(
            REPO_ROOT
            /
            relative
        )
        for relative
        in PROTECTED_LEDGER_PATHS
    }


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
        process.returncode
        ==
        0,
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

        value = (
            line[
                3:
            ]
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

        paths.add(
            value
        )

    return paths


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


def verify_authorities() -> dict[
    str,
    Any,
]:

    require(
        _controller.OBSERVATION_LEDGER_RELATIVE_PATH
        ==
        _runtime.OBSERVATION_LEDGER_RELATIVE_PATH,
        "OBSERVATION_LEDGER_AUTHORITY_MISMATCH",
    )

    require(
        _controller.ANCHOR_LEDGER_RELATIVE_PATH
        ==
        _runtime.ANCHOR_LEDGER_RELATIVE_PATH,
        "ANCHOR_LEDGER_AUTHORITY_MISMATCH",
    )

    require(
        _controller.OUTCOME_LEDGER_RELATIVE_PATH
        ==
        _runtime.OUTCOME_LEDGER_RELATIVE_PATH,
        "OUTCOME_LEDGER_RUNTIME_AUTHORITY_MISMATCH",
    )

    require(
        _controller.OUTCOME_LEDGER_RELATIVE_PATH
        ==
        _maturer.OUTCOME_LEDGER_RELATIVE_PATH,
        "OUTCOME_LEDGER_MATURER_AUTHORITY_MISMATCH",
    )

    require(
        _controller.MINIMUM_MATURED_OUTCOMES
        ==
        _contract.MINIMUM_MATURED_OUTCOMES
        ==
        60,
        "MINIMUM_MATURED_OUTCOMES_MISMATCH",
    )

    require(
        _controller.MINIMUM_DISTINCT_OBSERVATION_UTC_DATES
        ==
        _contract.MINIMUM_DISTINCT_OBSERVATION_UTC_DATES
        ==
        5,
        "MINIMUM_DISTINCT_DATES_MISMATCH",
    )

    require(
        _controller.MAX_PENDING_OBSERVATIONS
        ==
        1,
        "MAX_PENDING_POLICY_MISMATCH",
    )

    require(
        _controller.COLLECTION_POLICY
        ==
        "SINGLE_PENDING_NON_OVERLAPPING_PROSPECTIVE_SAMPLE",
        "COLLECTION_POLICY_MISMATCH",
    )

    require(
        _controller.PERFORMANCE_EVALUATION_AUTHORIZED
        is False,
        "PERFORMANCE_AUTHORIZED",
    )

    require(
        _controller.PNL_EVALUATION_AUTHORIZED
        is False,
        "PNL_AUTHORIZED",
    )

    require(
        _controller.LIVE_AUTHORIZED
        is False,
        "LIVE_AUTHORIZED",
    )

    require(
        _controller.EXECUTION_AUTHORIZED
        is False,
        "EXECUTION_AUTHORIZED",
    )

    return {
        "status": "PASS",
        "minimum_matured_outcomes": 60,
        "minimum_distinct_observation_utc_dates": 5,
        "max_pending_observations": 1,
        "collection_policy": (
            _controller.COLLECTION_POLICY
        ),
    }


def verify_empty_state_semantics() -> dict[
    str,
    Any,
]:

    state = (
        _controller
        .derive_state_from_records(
            observations={},
            anchors={},
            outcomes={},
        )
    )

    require(
        state.next_action
        ==
        _controller
        .ACTION_CAPTURE_NEW_OBSERVATION,
        "EMPTY_STATE_ACTION_MISMATCH",
    )

    require(
        state.pending_count
        ==
        0,
        "EMPTY_STATE_PENDING_NONZERO",
    )

    require(
        state.matured_outcome_count
        ==
        0,
        "EMPTY_STATE_MATURED_NONZERO",
    )

    require(
        state.collection_target_reached
        is False,
        "EMPTY_STATE_TARGET_REACHED",
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

    before = protected_states()

    verify_repository()

    authorities = verify_authorities()

    empty_state = (
        verify_empty_state_semantics()
    )

    after = protected_states()

    require(
        before
        ==
        after,
        "RUNTIME_LEDGER_CHANGED_DURING_FREEZE",
    )

    evidence = {
        "gate_id": GATE_ID,
        "status": "PASS",
        "base_authority_commit": (
            BASE_AUTHORITY_COMMIT
        ),
        "controller_version": (
            _controller.CONTROLLER_VERSION
        ),
        "authorities": authorities,
        "empty_state_smoke": (
            empty_state
        ),
        "observation_ledger": (
            _controller
            .OBSERVATION_LEDGER_RELATIVE_PATH
        ),
        "anchor_ledger": (
            _controller
            .ANCHOR_LEDGER_RELATIVE_PATH
        ),
        "outcome_ledger": (
            _controller
            .OUTCOME_LEDGER_RELATIVE_PATH
        ),
        "first_genuine_capture_authorized_in_this_gate": False,
        "real_market_data_loaded": False,
        "runtime_ledgers_created": False,
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
            "GATE_15D_C_B2D_G7_H_E_A_FREEZE_STATUS=BLOCKED"
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
            "REAL_MARKET_DATA_LOADED=false"
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
        "GATE_15D_C_B2D_G7_H_E_A_FREEZE_STATUS=PASS"
    )

    print(
        "BASE_AUTHORITY_COMMIT="
        +
        BASE_AUTHORITY_COMMIT
    )

    print(
        "CONTROLLER_VERSION="
        +
        _controller.CONTROLLER_VERSION
    )

    print(
        "COLLECTION_POLICY="
        +
        _controller.COLLECTION_POLICY
    )

    print(
        "MINIMUM_MATURED_OUTCOMES=60"
    )

    print(
        "MINIMUM_DISTINCT_OBSERVATION_UTC_DATES=5"
    )

    print(
        "MAX_PENDING_OBSERVATIONS=1"
    )

    print(
        "FIRST_GENUINE_CAPTURE_AUTHORIZED_IN_THIS_GATE=false"
    )

    print(
        "REAL_MARKET_DATA_LOADED=false"
    )

    print(
        "RUNTIME_LEDGERS_CREATED=false"
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