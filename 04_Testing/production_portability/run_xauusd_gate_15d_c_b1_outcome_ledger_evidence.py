"""
===============================================================================
Module      : run_xauusd_gate_15d_c_b1_outcome_ledger_evidence.py
Project     : PulseViper XAU AI
Purpose     : Gate 15D-C-B1 — Frozen Forward Outcome Ledger Evidence
===============================================================================

OFFLINE ONLY.

This runner proves that the separate matured-outcome ledger authority is:
- append-only
- durable
- idempotent
- conflict-detecting
- corruption-detecting
- isolated from the TRUE_FORWARD observation ledger

It does NOT:
- initialize MT5
- acquire market data
- mature any genuine observation
- create/mutate the real runtime outcome ledger
- mutate the TRUE_FORWARD observation ledger
- evaluate accuracy / win rate / PnL / return / drawdown
- authorize live trading or execution
===============================================================================
"""

from __future__ import annotations

import ast
import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping


REPO_ROOT: Path = (
    Path(__file__)
    .resolve()
    .parents[2]
)

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(REPO_ROOT),
    )


# =============================================================================
# Gate Authority
# =============================================================================

GATE_ID: str = (
    "GATE_15D_C_B1_FROZEN_FORWARD_OUTCOME_LEDGER"
)

SCHEMA_VERSION: str = "1.0.0"

GATE_15D_C_A_EVIDENCE_AUTHORITY_COMMIT: str = (
    "a024db1a6007528de547cbded31251e0083a7a1c"
)

LEDGER_REL_PATH: str = (
    "02_AI/Models/"
    "frozen_c04_forward_outcome_ledger.py"
)

LEDGER_TEST_REL_PATH: str = (
    "04_Testing/production_portability/"
    "test_frozen_c04_forward_outcome_ledger.py"
)

RUNNER_REL_PATH: str = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b1_outcome_ledger_evidence.py"
)

EVIDENCE_REL_PATH: str = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b1_outcome_ledger_evidence.json"
)

EVIDENCE_PATH: Path = (
    REPO_ROOT
    /
    EVIDENCE_REL_PATH
)

OBSERVATION_LEDGER_PATH: Path = (
    REPO_ROOT
    /
    "01_Data"
    /
    "Shadow"
    /
    "xauusd_frozen_c04_shadow_observations.jsonl"
)

RUNTIME_OUTCOME_LEDGER_PATH: Path = (
    REPO_ROOT
    /
    "01_Data"
    /
    "Shadow"
    /
    "xauusd_frozen_c04_forward_outcomes.jsonl"
)

ALLOWED_GATE_PATHS: frozenset[str] = frozenset(
    {
        LEDGER_REL_PATH,
        LEDGER_TEST_REL_PATH,
        RUNNER_REL_PATH,
        EVIDENCE_REL_PATH,
    }
)

FORBIDDEN_IMPORT_ROOTS: frozenset[str] = frozenset(
    {
        "MetaTrader5",
    }
)

FORBIDDEN_BROKER_CALLS: frozenset[str] = frozenset(
    {
        "initialize",
        "shutdown",
        "symbols_get",
        "symbol_info",
        "symbol_info_tick",
        "copy_rates_from_pos",
        "order_send",
        "order_check",
        "order_calc_margin",
        "order_calc_profit",
        "positions_get",
        "positions_total",
        "orders_get",
        "orders_total",
        "history_orders_get",
        "history_deals_get",
    }
)


# =============================================================================
# Existing Authorities
# =============================================================================

_ledger: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_ledger"
)

_maturer: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_maturer"
)

_contract: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_contract"
)

_eligibility: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_eligibility"
)


# =============================================================================
# Error / Generic Utilities
# =============================================================================

class Gate15DCB1Error(
    RuntimeError
):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise Gate15DCB1Error(
            reason
        )


def sha256_file(
    path: Path,
) -> str:

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as handle:

        while True:

            chunk = handle.read(
                1024
                *
                1024
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

    if not path.is_file():
        return None

    return sha256_file(
        path
    )


def normalize_path(
    value: str,
) -> str:

    return (
        value.strip()
        .replace(
            "\\",
            "/",
        )
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
        process.returncode
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
            process.stderr.strip()
        ),
    )

    return process.stdout.rstrip(
        "\r\n"
    )


def write_json(
    path: Path,
    document: Mapping[str, Any],
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
            document,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        +
        "\n",
        encoding="utf-8",
    )

    temporary.replace(
        path
    )


# =============================================================================
# Repository Authority
# =============================================================================

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

        path = line[
            3:
        ].strip()

        if " -> " in path:
            path = path.split(
                " -> ",
                1,
            )[1]

        if (
            path.startswith(
                '"'
            )
            and
            path.endswith(
                '"'
            )
        ):
            path = path[
                1:
                -1
            ]

        paths.add(
            normalize_path(
                path
            )
        )

    return paths


def verify_repository_authority() -> dict[str, Any]:

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
            f"{branch}"
        ),
    )

    require(
        head
        ==
        origin_main,
        (
            "HEAD_ORIGIN_MAIN_DIVERGENCE:"
            f"{head}!="
            f"{origin_main}"
        ),
    )

    ancestor = git_process(
        "merge-base",
        "--is-ancestor",
        GATE_15D_C_A_EVIDENCE_AUTHORITY_COMMIT,
        head,
    )

    require(
        ancestor.returncode
        ==
        0,
        "GATE_15D_C_A_AUTHORITY_NOT_ANCESTOR",
    )

    committed_since_authority = {
        normalize_path(
            item
        )
        for item
        in git_output(
            "diff",
            "--name-only",
            (
                f"{GATE_15D_C_A_EVIDENCE_AUTHORITY_COMMIT}"
                f"..{head}"
            ),
        ).splitlines()
        if item.strip()
    }

    unexpected_committed = (
        committed_since_authority
        -
        set(
            ALLOWED_GATE_PATHS
        )
    )

    require(
        not unexpected_committed,
        (
            "UNEXPECTED_COMMITTED_PATHS:"
            f"{sorted(unexpected_committed)}"
        ),
    )

    local_paths = (
        status_paths()
    )

    unexpected_local = (
        local_paths
        -
        set(
            ALLOWED_GATE_PATHS
        )
    )

    require(
        not unexpected_local,
        (
            "UNEXPECTED_LOCAL_PATHS:"
            f"{sorted(unexpected_local)}"
        ),
    )

    return {
        "status": "PASS",
        "branch": branch,
        "head": head,
        "origin_main": origin_main,
        "head_equals_origin_main": True,

        "gate_15d_c_a_authority_commit": (
            GATE_15D_C_A_EVIDENCE_AUTHORITY_COMMIT
        ),

        "gate_15d_c_a_authority_is_ancestor": True,

        "committed_since_gate_15d_c_a": sorted(
            committed_since_authority
        ),

        "local_gate_paths": sorted(
            local_paths
        ),

        "unexpected_committed_paths": [],

        "unexpected_local_paths": [],
    }


# =============================================================================
# Runtime Authority
# =============================================================================

def verify_runtime_authority() -> dict[str, Any]:

    require(
        bool(
            _contract.verify_frozen_contract()
        ),
        "FROZEN_OUTCOME_CONTRACT_INVALID",
    )

    require(
        bool(
            _eligibility.verify_authorities()
        ),
        "PROSPECTIVE_ELIGIBILITY_AUTHORITY_INVALID",
    )

    require(
        bool(
            _maturer.verify_authorities()
        ),
        "MATURATION_AUTHORITY_INVALID",
    )

    require(
        bool(
            _ledger.verify_authorities()
        ),
        "OUTCOME_LEDGER_AUTHORITY_INVALID",
    )

    require(
        _ledger.OUTCOME_LEDGER_VERSION
        ==
        "FROZEN_C04_FORWARD_OUTCOME_LEDGER_V1",
        "OUTCOME_LEDGER_VERSION_MISMATCH",
    )

    require(
        _ledger.EXPECTED_MATURATION_VERSION
        ==
        _maturer.MATURATION_VERSION,
        "LEDGER_MATURATION_VERSION_MISMATCH",
    )

    require(
        _ledger.EXPECTED_HORIZON_BARS
        ==
        12,
        "LEDGER_HORIZON_BARS_MISMATCH",
    )

    require(
        _ledger.EXPECTED_HORIZON_SEMANTICS
        ==
        (
            "NEXT_12_COMPLETED_M5_ROWS_"
            "AFTER_DECISION_ROW"
        ),
        "LEDGER_HORIZON_SEMANTICS_MISMATCH",
    )

    require(
        _ledger.PERFORMANCE_EVALUATION_AUTHORIZED
        is False,
        "PERFORMANCE_EVALUATION_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _ledger.PNL_EVALUATION_AUTHORIZED
        is False,
        "PNL_EVALUATION_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _ledger.LIVE_AUTHORIZED
        is False,
        "LIVE_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _ledger.EXECUTION_AUTHORIZED
        is False,
        "EXECUTION_UNEXPECTEDLY_AUTHORIZED",
    )

    return {
        "status": "PASS",

        "outcome_ledger_version": (
            _ledger.OUTCOME_LEDGER_VERSION
        ),

        "maturation_version": (
            _maturer.MATURATION_VERSION
        ),

        "outcome_contract_fingerprint_sha256": (
            _contract.compute_contract_fingerprint()
        ),

        "horizon_bars": (
            _ledger.EXPECTED_HORIZON_BARS
        ),

        "horizon_semantics": (
            _ledger.EXPECTED_HORIZON_SEMANTICS
        ),

        "duplicate_policy_available": [
            "FAIL_CLOSED",
            "IDEMPOTENT_IGNORE",
        ],

        "performance_evaluation_authorized": False,

        "pnl_evaluation_authorized": False,

        "live_authorized": False,

        "execution_authorized": False,
    }


# =============================================================================
# Static Safety
# =============================================================================

def static_safety_audit() -> dict[str, Any]:

    files = [
        REPO_ROOT
        /
        LEDGER_REL_PATH,

        REPO_ROOT
        /
        RUNNER_REL_PATH,
    ]

    violations: list[
        dict[str, str]
    ] = []

    for path in files:

        require(
            path.is_file(),
            (
                "STATIC_AUDIT_FILE_MISSING:"
                f"{path}"
            ),
        )

        tree = ast.parse(
            path.read_text(
                encoding="utf-8"
            )
        )

        for node in ast.walk(
            tree
        ):

            if isinstance(
                node,
                ast.Import,
            ):

                for alias in node.names:

                    root = (
                        alias.name.split(
                            ".",
                            1,
                        )[0]
                    )

                    if (
                        root
                        in FORBIDDEN_IMPORT_ROOTS
                    ):
                        violations.append(
                            {
                                "file": path.name,
                                "type": "forbidden_import",
                                "symbol": alias.name,
                            }
                        )

            elif isinstance(
                node,
                ast.ImportFrom,
            ):

                module_name = (
                    node.module
                    or ""
                )

                root = (
                    module_name.split(
                        ".",
                        1,
                    )[0]
                    if module_name
                    else ""
                )

                if (
                    root
                    in FORBIDDEN_IMPORT_ROOTS
                ):
                    violations.append(
                        {
                            "file": path.name,
                            "type": "forbidden_import_from",
                            "symbol": module_name,
                        }
                    )

            elif isinstance(
                node,
                ast.Call,
            ):

                function = node.func

                if isinstance(
                    function,
                    ast.Name,
                ):
                    name = function.id

                elif isinstance(
                    function,
                    ast.Attribute,
                ):
                    name = function.attr

                else:
                    name = ""

                if (
                    name
                    in FORBIDDEN_BROKER_CALLS
                ):
                    violations.append(
                        {
                            "file": path.name,
                            "type": "forbidden_broker_call",
                            "symbol": name,
                        }
                    )

    require(
        not violations,
        (
            "STATIC_SAFETY_VIOLATIONS:"
            f"{violations}"
        ),
    )

    return {
        "status": "PASS",

        "audited_files": [
            str(
                path.relative_to(
                    REPO_ROOT
                )
            ).replace(
                "\\",
                "/",
            )
            for path in files
        ],

        "violation_count": 0,

        "violations": [],
    }


# =============================================================================
# Targeted Offline Tests
# =============================================================================

def run_targeted_tests() -> dict[str, Any]:

    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",

            (
                "04_Testing/production_portability/"
                "test_frozen_c04_forward_outcome_contract.py"
            ),

            (
                "04_Testing/production_portability/"
                "test_frozen_c04_forward_outcome_eligibility.py"
            ),

            (
                "04_Testing/production_portability/"
                "test_frozen_c04_forward_outcome_maturer.py"
            ),

            LEDGER_TEST_REL_PATH,

            "-q",
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
            "TARGETED_TESTS_FAILED:"
            +
            process.stdout[
                -2000:
            ]
            +
            process.stderr[
                -2000:
            ]
        ),
    )

    return {
        "status": "PASS",

        "returncode": (
            process.returncode
        ),

        "stdout_tail": (
            process.stdout[
                -1200:
            ]
        ),
    }


# =============================================================================
# Gate
# =============================================================================

def run_gate() -> dict[str, Any]:

    observation_hash_before = (
        optional_sha256(
            OBSERVATION_LEDGER_PATH
        )
    )

    outcome_exists_before = (
        RUNTIME_OUTCOME_LEDGER_PATH.exists()
    )

    outcome_hash_before = (
        optional_sha256(
            RUNTIME_OUTCOME_LEDGER_PATH
        )
    )

    repository = (
        verify_repository_authority()
    )

    runtime_authority = (
        verify_runtime_authority()
    )

    safety = (
        static_safety_audit()
    )

    tests = (
        run_targeted_tests()
    )

    observation_hash_after = (
        optional_sha256(
            OBSERVATION_LEDGER_PATH
        )
    )

    outcome_exists_after = (
        RUNTIME_OUTCOME_LEDGER_PATH.exists()
    )

    outcome_hash_after = (
        optional_sha256(
            RUNTIME_OUTCOME_LEDGER_PATH
        )
    )

    require(
        observation_hash_before
        ==
        observation_hash_after,
        "TRUE_FORWARD_OBSERVATION_LEDGER_CHANGED",
    )

    require(
        outcome_exists_before
        ==
        outcome_exists_after,
        "RUNTIME_OUTCOME_LEDGER_EXISTENCE_CHANGED",
    )

    require(
        outcome_hash_before
        ==
        outcome_hash_after,
        "RUNTIME_OUTCOME_LEDGER_CHANGED",
    )

    artifact_hashes: dict[
        str,
        str,
    ] = {}

    for relative_path in (
        LEDGER_REL_PATH,
        LEDGER_TEST_REL_PATH,
        RUNNER_REL_PATH,
    ):

        path = (
            REPO_ROOT
            /
            relative_path
        )

        require(
            path.is_file(),
            (
                "GATE_ARTIFACT_MISSING:"
                f"{relative_path}"
            ),
        )

        artifact_hashes[
            relative_path
        ] = sha256_file(
            path
        )

    evidence: dict[
        str,
        Any,
    ] = {
        "gate": (
            "Gate 15D-C-B1 — Frozen "
            "Forward Outcome Ledger Authority"
        ),

        "gate_id": (
            GATE_ID
        ),

        "schema_version": (
            SCHEMA_VERSION
        ),

        "status": "PASS",

        "repository_authority": (
            repository
        ),

        "runtime_authority": (
            runtime_authority
        ),

        "static_safety": (
            safety
        ),

        "targeted_tests": (
            tests
        ),

        "candidate_artifact_hashes": (
            artifact_hashes
        ),

        "true_forward_observation_ledger": {
            "sha256_before": (
                observation_hash_before
            ),
            "sha256_after": (
                observation_hash_after
            ),
            "unchanged": True,
        },

        "runtime_outcome_ledger": {
            "path": (
                "01_Data/Shadow/"
                "xauusd_frozen_c04_forward_outcomes.jsonl"
            ),
            "existed_before": (
                outcome_exists_before
            ),
            "exists_after": (
                outcome_exists_after
            ),
            "sha256_before": (
                outcome_hash_before
            ),
            "sha256_after": (
                outcome_hash_after
            ),
            "unchanged": True,
        },

        "append_only_outcome_ledger_authority_frozen": True,

        "locked_append_required": True,

        "flush_and_fsync_required": True,

        "idempotent_duplicate_supported": True,

        "conflicting_outcome_fails_closed": True,

        "corrupted_outcome_ledger_fails_closed": True,

        "genuine_forward_observation_matured": False,

        "outcome_record_appended": False,

        "mt5_initialized": False,

        "forward_performance_evaluated": False,

        "accuracy_evaluated": False,

        "win_rate_evaluated": False,

        "pnl_evaluated": False,

        "return_evaluated": False,

        "drawdown_evaluated": False,

        "validation_partition_accessed": False,

        "test_partition_accessed": False,

        "model_changed": False,

        "features_changed": False,

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

        result = run_gate()

        authority = result[
            "runtime_authority"
        ]

        print(
            "GATE_15D_C_B1_STATUS=PASS"
        )

        print(
            "OUTCOME_LEDGER_VERSION="
            +
            str(
                authority[
                    "outcome_ledger_version"
                ]
            )
        )

        print(
            "MATURATION_VERSION="
            +
            str(
                authority[
                    "maturation_version"
                ]
            )
        )

        print(
            "HORIZON_BARS="
            +
            str(
                authority[
                    "horizon_bars"
                ]
            )
        )

        print(
            "HORIZON_SEMANTICS="
            +
            str(
                authority[
                    "horizon_semantics"
                ]
            )
        )

        print(
            "APPEND_ONLY_OUTCOME_LEDGER_AUTHORITY_FROZEN=true"
        )

        print(
            "LOCKED_APPEND_REQUIRED=true"
        )

        print(
            "FLUSH_AND_FSYNC_REQUIRED=true"
        )

        print(
            "IDEMPOTENT_DUPLICATE_SUPPORTED=true"
        )

        print(
            "CONFLICTING_OUTCOME_FAILS_CLOSED=true"
        )

        print(
            "GENUINE_FORWARD_OBSERVATION_MATURED=false"
        )

        print(
            "OUTCOME_RECORD_APPENDED=false"
        )

        print(
            "MT5_INITIALIZED=false"
        )

        print(
            "OBSERVATION_LEDGER_UNCHANGED=true"
        )

        print(
            "RUNTIME_OUTCOME_LEDGER_UNCHANGED=true"
        )

        print(
            "FORWARD_PERFORMANCE_EVALUATED=false"
        )

        print(
            "LIVE_AUTHORIZED=false"
        )

        print(
            "EXECUTION_AUTHORIZED=false"
        )

        print(
            "EVIDENCE_PATH="
            +
            str(
                EVIDENCE_PATH
            )
        )

        return 0

    except Exception as exc:

        print(
            "GATE_15D_C_B1_STATUS=FAIL"
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
            "GENUINE_FORWARD_OBSERVATION_MATURED=false"
        )

        print(
            "OUTCOME_RECORD_APPENDED=false"
        )

        print(
            "MT5_INITIALIZED=false"
        )

        print(
            "FORWARD_PERFORMANCE_EVALUATED=false"
        )

        print(
            "LIVE_AUTHORIZED=false"
        )

        print(
            "EXECUTION_AUTHORIZED=false"
        )

        return 2


if __name__ == "__main__":

    raise SystemExit(
        main()
    )