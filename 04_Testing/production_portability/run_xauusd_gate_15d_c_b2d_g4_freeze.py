from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]

GATE_ID = "GATE_15D_C_B2D_G4_FREEZE"
SCHEMA_VERSION = "1.0.0"

BASE_AUTHORITY_COMMIT = (
    "546859dd3dda214f6a77fb462be13974ab1a4070"
)


G1_RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g1_genuine_anchored_forward_capture.py"
)

G2_RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g2_genuine_outcome_maturation.py"
)

G3_RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g3_forward_sample_controller.py"
)

G4_RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g4_autonomous_forward_collector.py"
)

G4_TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g4_autonomous_forward_collector.py"
)

G4_FREEZE_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g4_freeze.py"
)

EVIDENCE_REL = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g4_freeze_evidence.json"
)

EVIDENCE_PATH = (
    REPO_ROOT
    /
    EVIDENCE_REL
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

    G1_RUNNER_REL,
    G2_RUNNER_REL,
    G3_RUNNER_REL,
    G4_RUNNER_REL,
    G4_TEST_REL,
    G4_FREEZE_REL,
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


ALLOWED_LOCAL_PATHS = {
    G4_RUNNER_REL,
    G4_TEST_REL,
    G4_FREEZE_REL,
    EVIDENCE_REL,
}


class G4FreezeError(
    RuntimeError
):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:

        raise G4FreezeError(
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


def normalize_path(
    value: str,
) -> str:

    return (
        value
        .strip()
        .replace(
            "\\",
            "/",
        )
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

        item = line[3:].strip()

        if " -> " in item:

            item = item.split(
                " -> ",
                1,
            )[1]

        if (
            item.startswith('"')
            and
            item.endswith('"')
        ):

            item = item[1:-1]

        paths.add(
            normalize_path(
                item
            )
        )

    return paths


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


def optional_raw_sha256(
    path: Path,
) -> str | None:

    if not path.is_file():

        return None

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def write_json(
    path: Path,
    document: Mapping[
        str,
        Any,
    ],
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
                document
            ),
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        +
        "\n",
        encoding="utf-8",
    )

    temp.replace(
        path
    )


def verify_repository() -> dict[
    str,
    Any,
]:

    fetch = git_process(
        "fetch",
        "origin",
    )

    require(
        fetch.returncode
        ==
        0,
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
        branch
        ==
        "main",
        (
            "UNEXPECTED_BRANCH:"
            +
            branch
        ),
    )

    require(
        head
        ==
        origin_main,
        (
            "HEAD_ORIGIN_MAIN_DIVERGENCE:"
            +
            head
            +
            "!="
            +
            origin_main
        ),
    )

    require(
        head
        ==
        BASE_AUTHORITY_COMMIT,
        (
            "UNEXPECTED_BASE_HEAD:"
            +
            head
            +
            ":expected="
            +
            BASE_AUTHORITY_COMMIT
        ),
    )

    local = status_paths()

    unexpected = (
        local
        -
        ALLOWED_LOCAL_PATHS
    )

    require(
        not unexpected,
        (
            "UNEXPECTED_LOCAL_PATHS:"
            +
            str(
                sorted(
                    unexpected
                )
            )
        ),
    )

    return {
        "status": "PASS",
        "branch": branch,
        "head": head,
        "origin_main": (
            origin_main
        ),
        "allowed_local_paths": (
            sorted(
                local
            )
        ),
    }


def run_validation() -> dict[
    str,
    Any,
]:

    python = str(
        REPO_ROOT
        /
        ".venv/Scripts/python.exe"
    )

    compile_process = subprocess.run(
        [
            python,
            "-m",
            "py_compile",

            str(
                REPO_ROOT
                /
                G4_RUNNER_REL
            ),

            str(
                REPO_ROOT
                /
                G4_TEST_REL
            ),

            str(
                REPO_ROOT
                /
                G4_FREEZE_REL
            ),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    require(
        compile_process.returncode
        ==
        0,
        (
            "PY_COMPILE_FAILED:"
            +
            compile_process.stderr[
                -2000:
            ]
        ),
    )

    pyright_process = subprocess.run(
        [
            python,
            "-m",
            "pyright",
            G4_RUNNER_REL,
            G4_TEST_REL,
            G4_FREEZE_REL,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    require(
        pyright_process.returncode
        ==
        0,
        (
            "PYRIGHT_FAILED:"
            +
            pyright_process.stdout[
                -2500:
            ]
            +
            pyright_process.stderr[
                -2500:
            ]
        ),
    )

    pytest_process = subprocess.run(
        [
            python,
            "-m",
            "pytest",
            G4_TEST_REL,
            "-q",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    require(
        pytest_process.returncode
        ==
        0,
        (
            "PYTEST_FAILED:"
            +
            pytest_process.stdout[
                -2500:
            ]
            +
            pytest_process.stderr[
                -2500:
            ]
        ),
    )

    return {
        "status": "PASS",
        "py_compile": True,

        "pyright_stdout": (
            pyright_process
            .stdout
            .strip()
        ),

        "pytest_stdout": (
            pytest_process
            .stdout
            .strip()
        ),
    }


def static_safety_audit() -> dict[
    str,
    Any,
]:

    source = (
        REPO_ROOT
        /
        G4_RUNNER_REL
    ).read_text(
        encoding="utf-8"
    )

    forbidden_capabilities = (
        "order_send(",
        "order_check(",
        "order_calc_margin(",
        "order_calc_profit(",
        "positions_get(",
        "orders_get(",
        "history_orders_get(",
        "history_deals_get(",
    )

    present = [
        item
        for item
        in forbidden_capabilities
        if item in source
    ]

    require(
        not present,
        (
            "FORBIDDEN_CAPABILITY_PRESENT:"
            +
            str(
                present
            )
        ),
    )


    forbidden_git = (
        "--force",
        "--force-with-lease",
        'git("reset"',
        'git("restore"',
        'git("checkout"',
        'git("clean"',
    )

    git_present = [
        item
        for item
        in forbidden_git
        if item in source
    ]

    require(
        not git_present,
        (
            "FORBIDDEN_GIT_OPERATION_PRESENT:"
            +
            str(
                git_present
            )
        ),
    )


    require(
        "MetaTrader5"
        not in source,
        "DIRECT_MT5_IMPORT_PRESENT",
    )


    require(
        "G1_RUNNER"
        in source,
        "G1_RUNNER_REFERENCE_MISSING",
    )

    require(
        "G2_RUNNER"
        in source,
        "G2_RUNNER_REFERENCE_MISSING",
    )

    require(
        "G3_RUNNER"
        in source,
        "G3_RUNNER_REFERENCE_MISSING",
    )


    require(
        "DEFAULT_TARGET_MATURED = 30"
        in source,
        "TARGET_30_NOT_FROZEN",
    )


    require(
        "run_g2_dry"
        in source,
        "G2_DRY_RUN_SEQUENCE_MISSING",
    )

    require(
        "run_g2_first_append"
        in source,
        "G2_FIRST_APPEND_SEQUENCE_MISSING",
    )

    require(
        "run_g2_idempotency"
        in source,
        "G2_IDEMPOTENCY_SEQUENCE_MISSING",
    )


    dry_position = source.find(
        "run_g2_dry"
    )

    append_position = source.find(
        "run_g2_first_append"
    )

    idempotency_position = (
        source.find(
            "run_g2_idempotency"
        )
    )


    require(
        dry_position >= 0,
        "G2_DRY_POSITION_MISSING",
    )

    require(
        append_position >= 0,
        "G2_APPEND_POSITION_MISSING",
    )

    require(
        idempotency_position >= 0,
        "G2_IDEMPOTENCY_POSITION_MISSING",
    )


    require(
        dry_position
        <
        append_position
        <
        idempotency_position,
        "G2_SEQUENCE_ORDER_INVALID",
    )


    require(
        "REMOTE_MOVED_BEFORE_EVIDENCE_COMMIT"
        in source,
        "REMOTE_PRECOMMIT_GUARD_MISSING",
    )

    require(
        "REMOTE_MOVED_AFTER_LOCAL_COMMIT"
        in source,
        "REMOTE_POSTCOMMIT_GUARD_MISSING",
    )


    require(
        "PERFORMANCE_EVALUATION_AUTHORIZED = False"
        in source,
        "PERFORMANCE_AUTHORIZATION_NOT_FALSE",
    )

    require(
        "PNL_EVALUATION_AUTHORIZED = False"
        in source,
        "PNL_AUTHORIZATION_NOT_FALSE",
    )

    require(
        "LIVE_AUTHORIZED = False"
        in source,
        "LIVE_AUTHORIZATION_NOT_FALSE",
    )

    require(
        "EXECUTION_AUTHORIZED = False"
        in source,
        "EXECUTION_AUTHORIZATION_NOT_FALSE",
    )


    require(
        "01_Data/Shadow/"
        in source,
        "MASTER_LOG_NOT_IN_SHADOW_RUNTIME_AREA",
    )


    return {
        "status": "PASS",

        "direct_mt5_access": False,

        "order_capabilities_present": (
            False
        ),

        "force_push_present": False,

        "destructive_git_recovery_present": (
            False
        ),

        "target_matured_samples": 30,

        "g1_orchestrated": True,

        "g2_dry_run_orchestrated": (
            True
        ),

        "g2_append_orchestrated": (
            True
        ),

        "g2_idempotency_orchestrated": (
            True
        ),

        "g3_orchestrated": True,

        "performance_evaluation_authorized": (
            False
        ),

        "pnl_evaluation_authorized": (
            False
        ),

        "live_authorized": False,

        "execution_authorized": False,
    }


def dependency_hashes() -> dict[
    str,
    str,
]:

    result: dict[
        str,
        str,
    ] = {}

    for relative in (
        HASH_BOUND_DEPENDENCIES
    ):

        path = (
            REPO_ROOT
            /
            relative
        )

        require(
            path.is_file(),
            (
                "HASH_BOUND_FILE_MISSING:"
                +
                relative
            ),
        )

        result[
            relative
        ] = canonical_sha256(
            path
        )

    return result


def run_gate() -> dict[
    str,
    Any,
]:

    observation_before = (
        optional_raw_sha256(
            REPO_ROOT
            /
            OBSERVATION_LEDGER_REL
        )
    )

    anchor_before = (
        optional_raw_sha256(
            REPO_ROOT
            /
            ANCHOR_LEDGER_REL
        )
    )

    outcome_before = (
        optional_raw_sha256(
            REPO_ROOT
            /
            OUTCOME_LEDGER_REL
        )
    )


    repository = (
        verify_repository()
    )

    safety = (
        static_safety_audit()
    )

    validation = (
        run_validation()
    )

    hashes = (
        dependency_hashes()
    )


    observation_after = (
        optional_raw_sha256(
            REPO_ROOT
            /
            OBSERVATION_LEDGER_REL
        )
    )

    anchor_after = (
        optional_raw_sha256(
            REPO_ROOT
            /
            ANCHOR_LEDGER_REL
        )
    )

    outcome_after = (
        optional_raw_sha256(
            REPO_ROOT
            /
            OUTCOME_LEDGER_REL
        )
    )


    require(
        observation_before
        ==
        observation_after,
        "OBSERVATION_LEDGER_CHANGED",
    )

    require(
        anchor_before
        ==
        anchor_after,
        "ANCHOR_LEDGER_CHANGED",
    )

    require(
        outcome_before
        ==
        outcome_after,
        "OUTCOME_LEDGER_CHANGED",
    )


    evidence = {
        "gate_id": (
            GATE_ID
        ),

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

        "static_safety": (
            safety
        ),

        "validation": (
            validation
        ),

        "hashing_semantics": (
            "GIT_TEXT_CANONICAL_LF_SHA256"
        ),

        "hash_bound_dependencies": (
            hashes
        ),

        "hash_bound_file_count": (
            len(
                hashes
            )
        ),

        "collector_executed": False,

        "mt5_initialized": False,

        "market_data_acquired": False,

        "observation_ledger_unchanged": (
            True
        ),

        "anchor_ledger_unchanged": (
            True
        ),

        "outcome_ledger_unchanged": (
            True
        ),

        "ledger_write_performed": (
            False
        ),

        "evidence_commit_performed": (
            False
        ),

        "git_push_performed": (
            False
        ),

        "performance_evaluated": (
            False
        ),

        "pnl_evaluated": (
            False
        ),

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
            "GATE_15D_C_B2D_G4_FREEZE_STATUS=BLOCKED"
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
            "COLLECTOR_EXECUTED=false"
        )

        print(
            "LIVE_AUTHORIZED=false"
        )

        print(
            "EXECUTION_AUTHORIZED=false"
        )

        return 2


    print(
        "GATE_15D_C_B2D_G4_FREEZE_STATUS=PASS"
    )

    print(
        "BASE_AUTHORITY_COMMIT="
        +
        evidence[
            "base_authority_commit"
        ]
    )

    print(
        "HASHING_SEMANTICS="
        +
        evidence[
            "hashing_semantics"
        ]
    )

    print(
        "HASH_BOUND_FILE_COUNT="
        +
        str(
            evidence[
                "hash_bound_file_count"
            ]
        )
    )

    print(
        "COLLECTOR_EXECUTED=false"
    )

    print(
        "MT5_INITIALIZED=false"
    )

    print(
        "MARKET_DATA_ACQUIRED=false"
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
        "LEDGER_WRITE_PERFORMED=false"
    )

    print(
        "EVIDENCE_COMMIT_PERFORMED=false"
    )

    print(
        "GIT_PUSH_PERFORMED=false"
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