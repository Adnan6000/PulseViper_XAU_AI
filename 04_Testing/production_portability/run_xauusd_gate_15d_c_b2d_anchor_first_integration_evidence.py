"""
===============================================================================
Module      : run_xauusd_gate_15d_c_b2d_anchor_first_integration_evidence.py
Project     : PulseViper XAU AI
Purpose     : Gate 15D-C-B2D — Offline Anchor-First Integration Evidence
===============================================================================

Freezes offline evidence for the B2D forward persistence protocol.

This gate proves:

- hardened runtime ledgers perform duplicate/conflict decisions under lock
- current on-disk state is re-read inside the append lock
- prospective anchor persistence occurs BEFORE observation persistence
- observation persistence cannot occur if anchor persistence fails
- if observation persistence fails after successful anchor persistence,
  the anchor is preserved as immutable orphan audit history
- same-snapshot prospective anchor capture is mandatory
- future M5 rows are forbidden during anchor capture
- exact retries are idempotent
- legacy non-atomic ledgers are rejected by the B2D coordinator
- no genuine MT5 acquisition occurs
- no runtime production ledger changes occur
- no outcome maturation occurs
- no performance evaluation occurs
- no live/execution authorization occurs

This runner is OFFLINE ONLY.

It MUST NOT:
- initialize MT5
- request market data
- append genuine runtime observations
- append genuine runtime anchors
- append genuine outcomes
- calculate performance
- authorize live trading
- authorize execution
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


# =============================================================================
# Repository
# =============================================================================

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


GATE_ID: str = (
    "GATE_15D_C_B2D_ANCHOR_FIRST_FORWARD_PERSISTENCE_INTEGRATION"
)

SCHEMA_VERSION: str = "1.0.0"

BASE_AUTHORITY_COMMIT: str = (
    "1664c1d638ab45652812885b58fc011c6054dc33"
)


# =============================================================================
# Paths
# =============================================================================

ATOMIC_LEDGER_REL_PATH: str = (
    "02_AI/Models/"
    "frozen_c04_forward_runtime_atomic_ledgers.py"
)

COORDINATOR_REL_PATH: str = (
    "02_AI/Models/"
    "frozen_c04_forward_anchor_first_coordinator.py"
)

ATOMIC_LEDGER_TEST_REL_PATH: str = (
    "04_Testing/production_portability/"
    "test_forward_runtime_ledger_append_atomicity.py"
)

COORDINATOR_TEST_REL_PATH: str = (
    "04_Testing/production_portability/"
    "test_frozen_c04_forward_anchor_first_coordinator.py"
)

RUNNER_REL_PATH: str = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_anchor_first_integration_evidence.py"
)

EVIDENCE_REL_PATH: str = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_anchor_first_integration_evidence.json"
)

EVIDENCE_PATH: Path = (
    REPO_ROOT
    /
    EVIDENCE_REL_PATH
)


# =============================================================================
# Existing Regression Tests
# =============================================================================

ELIGIBILITY_TEST_REL_PATH: str = (
    "04_Testing/production_portability/"
    "test_frozen_c04_forward_outcome_eligibility.py"
)

ANCHOR_TEST_REL_PATH: str = (
    "04_Testing/production_portability/"
    "test_frozen_c04_forward_outcome_anchor.py"
)


# =============================================================================
# Runtime Ledgers — MUST REMAIN UNCHANGED
# =============================================================================

OBSERVATION_LEDGER_REL_PATH: str = (
    "01_Data/Shadow/"
    "xauusd_frozen_c04_shadow_observations.jsonl"
)

ANCHOR_LEDGER_REL_PATH: str = (
    "01_Data/Shadow/"
    "xauusd_frozen_c04_forward_outcome_anchors.jsonl"
)

OUTCOME_LEDGER_REL_PATH: str = (
    "01_Data/Shadow/"
    "xauusd_frozen_c04_forward_outcomes.jsonl"
)

RUNTIME_LEDGER_PATHS: tuple[str, ...] = (
    OBSERVATION_LEDGER_REL_PATH,
    ANCHOR_LEDGER_REL_PATH,
    OUTCOME_LEDGER_REL_PATH,
)


# =============================================================================
# Allowed Local Candidate Paths
# =============================================================================

ALLOWED_LOCAL_PATHS: frozenset[str] = frozenset(
    {
        ATOMIC_LEDGER_REL_PATH,
        COORDINATOR_REL_PATH,
        ATOMIC_LEDGER_TEST_REL_PATH,
        COORDINATOR_TEST_REL_PATH,
        RUNNER_REL_PATH,
        EVIDENCE_REL_PATH,
    }
)


# =============================================================================
# Authorities
# =============================================================================

_atomic_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_runtime_atomic_ledgers"
)

_coordinator_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_anchor_first_coordinator"
)

_anchor_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_anchor"
)

_eligibility_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_eligibility"
)

_maturer_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_maturer"
)

_outcome_ledger_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_ledger"
)


# =============================================================================
# Errors
# =============================================================================

class Gate15DCB2DBlockedError(
    RuntimeError
):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise Gate15DCB2DBlockedError(
            reason
        )


# =============================================================================
# Generic Utilities
# =============================================================================

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


def status_paths() -> set[str]:

    output = git_output(
        "status",
        "--porcelain",
        "--untracked-files=all",
    )

    paths: set[str] = set()

    for raw_line in output.splitlines():

        if len(
            raw_line
        ) < 4:
            continue

        path = (
            raw_line[
                3:
            ]
            .strip()
        )

        if " -> " in path:

            path = (
                path.split(
                    " -> ",
                    1,
                )[
                    1
                ]
            )

        if (
            path.startswith(
                '"'
            )
            and
            path.endswith(
                '"'
            )
        ):

            path = (
                path[
                    1:
                    -1
                ]
            )

        paths.add(
            normalize_path(
                path
            )
        )

    return paths


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
# Runtime Ledger Snapshots
# =============================================================================

def runtime_ledger_snapshot() -> dict[str, dict[str, Any]]:

    output: dict[
        str,
        dict[str, Any],
    ] = {}

    for relative in RUNTIME_LEDGER_PATHS:

        path = (
            REPO_ROOT
            /
            relative
        )

        if not path.exists():

            output[
                relative
            ] = {
                "exists": False,
                "size_bytes": 0,
                "sha256": None,
            }

            continue

        require(
            path.is_file(),
            (
                "RUNTIME_LEDGER_PATH_NOT_FILE:"
                f"{relative}"
            ),
        )

        output[
            relative
        ] = {
            "exists": True,
            "size_bytes": (
                path.stat()
                .st_size
            ),
            "sha256": (
                sha256_file(
                    path
                )
            ),
        }

    return output


# =============================================================================
# Repository Authority
# =============================================================================

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
        BASE_AUTHORITY_COMMIT,
        (
            "UNEXPECTED_BASE_HEAD:"
            f"{head}!="
            f"{BASE_AUTHORITY_COMMIT}"
        ),
    )

    require(
        origin_main
        ==
        BASE_AUTHORITY_COMMIT,
        (
            "UNEXPECTED_ORIGIN_MAIN:"
            f"{origin_main}!="
            f"{BASE_AUTHORITY_COMMIT}"
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

    local_paths = (
        status_paths()
    )

    unexpected = (
        local_paths
        -
        set(
            ALLOWED_LOCAL_PATHS
        )
    )

    require(
        not unexpected,
        (
            "UNEXPECTED_LOCAL_PATHS:"
            f"{sorted(unexpected)}"
        ),
    )

    required_candidates = {
        ATOMIC_LEDGER_REL_PATH,
        COORDINATOR_REL_PATH,
        ATOMIC_LEDGER_TEST_REL_PATH,
        COORDINATOR_TEST_REL_PATH,
        RUNNER_REL_PATH,
    }

    missing = (
        required_candidates
        -
        local_paths
    )

    require(
        not missing,
        (
            "EXPECTED_B2D_CANDIDATE_PATHS_MISSING:"
            f"{sorted(missing)}"
        ),
    )

    return {
        "status": "PASS",
        "branch": branch,
        "base_authority_commit": (
            BASE_AUTHORITY_COMMIT
        ),
        "execution_head": head,
        "origin_main": origin_main,
        "head_equals_origin_main": True,
        "allowed_local_paths_only": True,
        "local_candidate_paths": sorted(
            local_paths
        ),
    }


# =============================================================================
# Runtime Authority Verification
# =============================================================================

def verify_runtime_authorities() -> dict[str, Any]:

    require(
        bool(
            _atomic_mod.verify_authorities()
        ),
        "ATOMIC_LEDGER_AUTHORITY_INVALID",
    )

    require(
        bool(
            _coordinator_mod.verify_authorities()
        ),
        "ANCHOR_FIRST_COORDINATOR_AUTHORITY_INVALID",
    )

    require(
        bool(
            _anchor_mod.verify_authorities()
        ),
        "ANCHOR_AUTHORITY_INVALID",
    )

    require(
        bool(
            _eligibility_mod.verify_authorities()
        ),
        "ELIGIBILITY_AUTHORITY_INVALID",
    )

    require(
        _atomic_mod.ATOMIC_LEDGER_AUTHORITY_VERSION
        ==
        "FROZEN_C04_FORWARD_RUNTIME_ATOMIC_LEDGERS_V1",
        "ATOMIC_LEDGER_VERSION_MISMATCH",
    )

    require(
        _atomic_mod.LOCK_TRANSACTION_POLICY
        ==
        "LOCK_THEN_REBUILD_DISK_INDEX_THEN_DECIDE_THEN_APPEND_FSYNC",
        "ATOMIC_LOCK_TRANSACTION_POLICY_MISMATCH",
    )

    require(
        _atomic_mod.APPEND_ONLY
        is True,
        "ATOMIC_LEDGER_APPEND_ONLY_POLICY_MISMATCH",
    )

    require(
        _coordinator_mod.COORDINATOR_VERSION
        ==
        "FROZEN_C04_FORWARD_ANCHOR_FIRST_COORDINATOR_V1",
        "COORDINATOR_VERSION_MISMATCH",
    )

    require(
        _coordinator_mod.PERSISTENCE_ORDER
        ==
        "ANCHOR_FIRST_THEN_OBSERVATION",
        "ANCHOR_FIRST_PERSISTENCE_ORDER_MISMATCH",
    )

    require(
        _coordinator_mod.ORPHAN_ANCHOR_POLICY
        ==
        "PRESERVE_IMMUTABLE_ANCHOR_IF_OBSERVATION_APPEND_FAILS",
        "ORPHAN_ANCHOR_POLICY_MISMATCH",
    )

    require(
        _anchor_mod.ANCHOR_VERSION
        ==
        "FROZEN_C04_FORWARD_OUTCOME_ANCHOR_V1",
        "ANCHOR_VERSION_MISMATCH",
    )

    require(
        _anchor_mod.FORMAL_MATURATION_REQUIRES_ANCHOR
        is True,
        "FORMAL_MATURATION_ANCHOR_REQUIREMENT_MISSING",
    )

    require(
        _maturer_mod.MATURATION_VERSION
        ==
        "FROZEN_C04_FORWARD_OUTCOME_MATURER_V2",
        "MATURATION_V2_AUTHORITY_MISMATCH",
    )

    require(
        _outcome_ledger_mod.OUTCOME_LEDGER_VERSION
        ==
        "FROZEN_C04_FORWARD_OUTCOME_LEDGER_V2",
        "OUTCOME_LEDGER_V2_AUTHORITY_MISMATCH",
    )

    require(
        _maturer_mod.FORMAL_MATURATION_REQUIRES_ANCHOR
        is True,
        "MATURER_DOES_NOT_REQUIRE_ANCHOR",
    )

    require(
        _coordinator_mod.OUTCOME_MATURATION_AUTHORIZED
        is False,
        "B2D_OUTCOME_MATURATION_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _coordinator_mod.PERFORMANCE_EVALUATION_AUTHORIZED
        is False,
        "B2D_PERFORMANCE_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _coordinator_mod.PNL_EVALUATION_AUTHORIZED
        is False,
        "B2D_PNL_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _coordinator_mod.LIVE_AUTHORIZED
        is False,
        "B2D_LIVE_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _coordinator_mod.EXECUTION_AUTHORIZED
        is False,
        "B2D_EXECUTION_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _atomic_mod.PERFORMANCE_EVALUATION_AUTHORIZED
        is False,
        "ATOMIC_LEDGER_PERFORMANCE_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _atomic_mod.LIVE_AUTHORIZED
        is False,
        "ATOMIC_LEDGER_LIVE_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _atomic_mod.EXECUTION_AUTHORIZED
        is False,
        "ATOMIC_LEDGER_EXECUTION_UNEXPECTEDLY_AUTHORIZED",
    )

    return {
        "status": "PASS",

        "atomic_ledger_authority_version": (
            _atomic_mod
            .ATOMIC_LEDGER_AUTHORITY_VERSION
        ),

        "lock_transaction_policy": (
            _atomic_mod
            .LOCK_TRANSACTION_POLICY
        ),

        "append_only": True,

        "coordinator_version": (
            _coordinator_mod
            .COORDINATOR_VERSION
        ),

        "persistence_order": (
            _coordinator_mod
            .PERSISTENCE_ORDER
        ),

        "orphan_anchor_policy": (
            _coordinator_mod
            .ORPHAN_ANCHOR_POLICY
        ),

        "anchor_version": (
            _anchor_mod
            .ANCHOR_VERSION
        ),

        "maturation_version": (
            _maturer_mod
            .MATURATION_VERSION
        ),

        "outcome_ledger_version": (
            _outcome_ledger_mod
            .OUTCOME_LEDGER_VERSION
        ),

        "formal_maturation_requires_anchor": True,

        "outcome_maturation_authorized": False,

        "performance_evaluation_authorized": False,

        "pnl_evaluation_authorized": False,

        "live_authorized": False,

        "execution_authorized": False,
    }


# =============================================================================
# Static Safety Audit
# =============================================================================

FORBIDDEN_IMPORT_ROOTS: frozenset[str] = frozenset(
    {
        "MetaTrader5",
    }
)

FORBIDDEN_CALL_NAMES: frozenset[str] = frozenset(
    {
        "order_send",
        "order_check",
        "order_calc_margin",
        "order_calc_profit",
        "positions_get",
        "positions_total",
        "orders_get",
        "orders_total",
        "history_orders_get",
        "history_orders_total",
        "history_deals_get",
        "history_deals_total",
    }
)


def static_safety_audit() -> dict[str, Any]:

    audited_paths = (
        ATOMIC_LEDGER_REL_PATH,
        COORDINATOR_REL_PATH,
        ATOMIC_LEDGER_TEST_REL_PATH,
        COORDINATOR_TEST_REL_PATH,
        RUNNER_REL_PATH,
    )

    forbidden_import_hits: list[
        str
    ] = []

    forbidden_call_hits: list[
        str
    ] = []

    for relative in audited_paths:

        path = (
            REPO_ROOT
            /
            relative
        )

        require(
            path.is_file(),
            (
                "STATIC_AUDIT_FILE_MISSING:"
                f"{relative}"
            ),
        )

        source = path.read_text(
            encoding="utf-8"
        )

        tree = ast.parse(
            source,
            filename=(
                str(
                    path
                )
            ),
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
                        alias.name
                        .split(
                            ".",
                            1,
                        )[
                            0
                        ]
                    )

                    if root in FORBIDDEN_IMPORT_ROOTS:

                        forbidden_import_hits.append(
                            (
                                f"{relative}:"
                                f"{node.lineno}:"
                                f"import:{alias.name}"
                            )
                        )

            elif isinstance(
                node,
                ast.ImportFrom,
            ):

                module = (
                    node.module
                    or
                    ""
                )

                root = (
                    module.split(
                        ".",
                        1,
                    )[
                        0
                    ]
                )

                if root in FORBIDDEN_IMPORT_ROOTS:

                    forbidden_import_hits.append(
                        (
                            f"{relative}:"
                            f"{node.lineno}:"
                            f"from:{module}"
                        )
                    )

            elif isinstance(
                node,
                ast.Call,
            ):

                target = (
                    node.func
                )

                call_name: str | None = None

                if isinstance(
                    target,
                    ast.Name,
                ):

                    call_name = (
                        target.id
                    )

                elif isinstance(
                    target,
                    ast.Attribute,
                ):

                    call_name = (
                        target.attr
                    )

                if (
                    call_name
                    in
                    FORBIDDEN_CALL_NAMES
                ):

                    forbidden_call_hits.append(
                        (
                            f"{relative}:"
                            f"{node.lineno}:"
                            f"{call_name}"
                        )
                    )

    require(
        not forbidden_import_hits,
        (
            "FORBIDDEN_MT5_IMPORTS_FOUND:"
            f"{forbidden_import_hits}"
        ),
    )

    require(
        not forbidden_call_hits,
        (
            "FORBIDDEN_BROKER_CALLS_FOUND:"
            f"{forbidden_call_hits}"
        ),
    )

    return {
        "status": "PASS",
        "audited_paths": list(
            audited_paths
        ),
        "forbidden_mt5_import_count": 0,
        "forbidden_broker_call_count": 0,
        "mt5_initialized": False,
        "market_data_acquired": False,
        "broker_write_calls": 0,
    }


# =============================================================================
# Targeted Offline Regression
# =============================================================================

def run_targeted_pytest() -> dict[str, Any]:

    command = [
        sys.executable,
        "-m",
        "pytest",
        ELIGIBILITY_TEST_REL_PATH,
        ANCHOR_TEST_REL_PATH,
        ATOMIC_LEDGER_TEST_REL_PATH,
        COORDINATOR_TEST_REL_PATH,
        "-q",
    ]

    process = subprocess.run(
        command,
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
            "TARGETED_PYTEST_FAILED:"
            +
            process.stdout[
                -3000:
            ]
            +
            process.stderr[
                -3000:
            ]
        ),
    )

    return {
        "status": "PASS",
        "returncode": (
            process.returncode
        ),
        "command": (
            " ".join(
                command
            )
        ),
        "stdout_tail": (
            process.stdout[
                -2000:
            ]
        ),
    }


# =============================================================================
# Candidate Hashes
# =============================================================================

def candidate_artifact_hashes() -> dict[str, str]:

    paths = (
        ATOMIC_LEDGER_REL_PATH,
        COORDINATOR_REL_PATH,
        ATOMIC_LEDGER_TEST_REL_PATH,
        COORDINATOR_TEST_REL_PATH,
        RUNNER_REL_PATH,
    )

    output: dict[
        str,
        str,
    ] = {}

    for relative in paths:

        path = (
            REPO_ROOT
            /
            relative
        )

        require(
            path.is_file(),
            (
                "CANDIDATE_ARTIFACT_MISSING:"
                f"{relative}"
            ),
        )

        output[
            relative
        ] = (
            sha256_file(
                path
            )
        )

    return output


# =============================================================================
# Gate
# =============================================================================

def run_gate() -> dict[str, Any]:

    runtime_before = (
        runtime_ledger_snapshot()
    )

    repository = (
        verify_repository_authority()
    )

    runtime_authority = (
        verify_runtime_authorities()
    )

    safety = (
        static_safety_audit()
    )

    tests = (
        run_targeted_pytest()
    )

    runtime_after = (
        runtime_ledger_snapshot()
    )

    require(
        runtime_before
        ==
        runtime_after,
        (
            "RUNTIME_LEDGER_STATE_CHANGED_DURING_OFFLINE_GATE:"
            f"before={runtime_before}:"
            f"after={runtime_after}"
        ),
    )

    candidate_hashes = (
        candidate_artifact_hashes()
    )

    evidence: dict[
        str,
        Any,
    ] = {
        "gate": (
            "Gate 15D-C-B2D — "
            "Anchor-First Forward Persistence Integration"
        ),

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

        "runtime_authority": (
            runtime_authority
        ),

        "static_safety_audit": (
            safety
        ),

        "targeted_pytest": (
            tests
        ),

        "candidate_artifact_hashes": (
            candidate_hashes
        ),

        "persistence_protocol": {
            "prospective_eligibility_before_persistence": True,
            "same_snapshot_anchor_required": True,
            "anchor_append_first": True,
            "anchor_integrity_before_observation_append": True,
            "observation_append_second": True,
            "observation_integrity_after_append": True,
            "legacy_non_atomic_ledgers_rejected": True,
            "future_m5_rows_during_anchor_capture_forbidden": True,
            "exact_retry_idempotent": True,
            "anchor_append_failure_blocks_observation_append": True,
            "observation_append_failure_preserves_anchor": True,
            "orphan_anchor_deleted": False,
            "orphan_anchor_rewritten": False,
            "orphan_anchor_truncated": False,
        },

        "runtime_ledger_state_before": (
            runtime_before
        ),

        "runtime_ledger_state_after": (
            runtime_after
        ),

        "observation_ledger_unchanged": (
            runtime_before[
                OBSERVATION_LEDGER_REL_PATH
            ]
            ==
            runtime_after[
                OBSERVATION_LEDGER_REL_PATH
            ]
        ),

        "anchor_ledger_unchanged": (
            runtime_before[
                ANCHOR_LEDGER_REL_PATH
            ]
            ==
            runtime_after[
                ANCHOR_LEDGER_REL_PATH
            ]
        ),

        "outcome_ledger_unchanged": (
            runtime_before[
                OUTCOME_LEDGER_REL_PATH
            ]
            ==
            runtime_after[
                OUTCOME_LEDGER_REL_PATH
            ]
        ),

        "genuine_mt5_acquisition": False,

        "genuine_forward_observation_captured": False,

        "genuine_anchor_appended": False,

        "genuine_forward_observation_appended": False,

        "genuine_forward_observation_matured": False,

        "genuine_outcome_appended": False,

        "market_data_acquired": False,

        "mt5_initialized": False,

        "forward_performance_evaluated": False,

        "accuracy_evaluated": False,

        "win_rate_evaluated": False,

        "pnl_evaluated": False,

        "return_evaluated": False,

        "drawdown_evaluated": False,

        "live_authorized": False,

        "execution_authorized": False,

        "next_gate": (
            "PUBLISH_AND_HASH_BIND_B2D_OFFLINE_AUTHORITY_"
            "BEFORE_ANY_GENUINE_MT5_CAPTURE"
        ),
    }

    require(
        evidence[
            "observation_ledger_unchanged"
        ]
        is True,
        "OBSERVATION_LEDGER_CHANGED",
    )

    require(
        evidence[
            "anchor_ledger_unchanged"
        ]
        is True,
        "ANCHOR_LEDGER_CHANGED",
    )

    require(
        evidence[
            "outcome_ledger_unchanged"
        ]
        is True,
        "OUTCOME_LEDGER_CHANGED",
    )

    write_json(
        EVIDENCE_PATH,
        evidence,
    )

    return evidence


# =============================================================================
# Entrypoint
# =============================================================================

def main() -> int:

    try:

        result = (
            run_gate()
        )

        runtime = (
            result[
                "runtime_authority"
            ]
        )

        print(
            "GATE_15D_C_B2D_STATUS=PASS"
        )

        print(
            "ATOMIC_LEDGER_AUTHORITY_VERSION="
            +
            str(
                runtime[
                    "atomic_ledger_authority_version"
                ]
            )
        )

        print(
            "LOCK_TRANSACTION_POLICY="
            +
            str(
                runtime[
                    "lock_transaction_policy"
                ]
            )
        )

        print(
            "COORDINATOR_VERSION="
            +
            str(
                runtime[
                    "coordinator_version"
                ]
            )
        )

        print(
            "PERSISTENCE_ORDER="
            +
            str(
                runtime[
                    "persistence_order"
                ]
            )
        )

        print(
            "ORPHAN_ANCHOR_POLICY="
            +
            str(
                runtime[
                    "orphan_anchor_policy"
                ]
            )
        )

        print(
            "ANCHOR_VERSION="
            +
            str(
                runtime[
                    "anchor_version"
                ]
            )
        )

        print(
            "MATURATION_VERSION="
            +
            str(
                runtime[
                    "maturation_version"
                ]
            )
        )

        print(
            "OUTCOME_LEDGER_VERSION="
            +
            str(
                runtime[
                    "outcome_ledger_version"
                ]
            )
        )

        print(
            "GENUINE_MT5_ACQUISITION=false"
        )

        print(
            "GENUINE_FORWARD_OBSERVATION_CAPTURED=false"
        )

        print(
            "GENUINE_ANCHOR_APPENDED=false"
        )

        print(
            "GENUINE_FORWARD_OBSERVATION_APPENDED=false"
        )

        print(
            "GENUINE_FORWARD_OBSERVATION_MATURED=false"
        )

        print(
            "GENUINE_OUTCOME_APPENDED=false"
        )

        print(
            "MT5_INITIALIZED=false"
        )

        print(
            "MARKET_DATA_ACQUIRED=false"
        )

        print(
            "OBSERVATION_LEDGER_UNCHANGED="
            +
            (
                "true"
                if result[
                    "observation_ledger_unchanged"
                ]
                else
                "false"
            )
        )

        print(
            "ANCHOR_LEDGER_UNCHANGED="
            +
            (
                "true"
                if result[
                    "anchor_ledger_unchanged"
                ]
                else
                "false"
            )
        )

        print(
            "OUTCOME_LEDGER_UNCHANGED="
            +
            (
                "true"
                if result[
                    "outcome_ledger_unchanged"
                ]
                else
                "false"
            )
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
            "GATE_15D_C_B2D_STATUS=BLOCKED"
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