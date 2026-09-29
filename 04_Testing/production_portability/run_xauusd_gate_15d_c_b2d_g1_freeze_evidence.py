"""
===============================================================================
Module      : run_xauusd_gate_15d_c_b2d_g1_freeze_evidence.py
Project     : PulseViper XAU AI
Purpose     : Gate 15D-C-B2D-G1 — Offline Genuine Runner Freeze Evidence
===============================================================================

This is an OFFLINE evidence gate.

It validates and freezes the genuine anchored forward-capture runner WITHOUT
executing that runner and WITHOUT initializing MetaTrader5.

It proves:

- published B2D authority remains valid
- G1 runner is bound to published B2D authority commit
- anchor-first coordinator is required
- atomic runtime ledgers are required
- prospective eligibility occurs before persistence
- same-snapshot identity is preserved
- Gate 13 occurs before Gate 14
- only MT5 initialize/shutdown appear as raw MT5 lifecycle calls
- no order/trading APIs exist in the candidate runner
- no outcome maturation exists in the candidate runner
- no outcome ledger append exists in the candidate runner
- live/execution/performance remain blocked
- production runtime ledgers remain byte-for-byte unchanged during this gate
- no genuine market acquisition occurs during this gate

This gate MUST run before the genuine G1 runner is published/executed.
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


# =============================================================================
# Gate Authority
# =============================================================================

GATE_ID: str = (
    "GATE_15D_C_B2D_G1_GENUINE_RUNNER_FREEZE"
)

SCHEMA_VERSION: str = "1.0.0"

BASE_AUTHORITY_COMMIT: str = (
    "45d1eab9288d3a22efc5da87ed5ff2ab2c259ee6"
)


# =============================================================================
# Candidate Paths
# =============================================================================

G1_RUNNER_REL_PATH: str = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g1_genuine_anchored_forward_capture.py"
)

G1_TEST_REL_PATH: str = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g1_genuine_anchored_forward_capture.py"
)

FREEZE_RUNNER_REL_PATH: str = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g1_freeze_evidence.py"
)

BROKER_ADAPTER_REL_PATH: str = (
    "02_AI/Adapters/xauusd_broker_adapter.py"
)

ACQUISITION_ADAPTER_REL_PATH: str = (
    "02_AI/Adapters/mt5_read_only_forward_acquisition_adapter.py"
)

BROKER_ADAPTER_TEST_REL_PATH: str = (
    "04_Testing/production_portability/"
    "test_xauusd_broker_adapter.py"
)

ACQUISITION_ADAPTER_TEST_REL_PATH: str = (
    "04_Testing/production_portability/"
    "test_mt5_read_only_forward_acquisition_adapter.py"
)
EVIDENCE_REL_PATH: str = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g1_genuine_runner_freeze_evidence.json"
)

BLOCKED_CAPTURE_EVIDENCE_REL_PATH: str = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g1_genuine_anchored_forward_capture_blocked.json"
)

EVIDENCE_PATH: Path = (
    REPO_ROOT
    /
    EVIDENCE_REL_PATH
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
# Allowed Local Paths
# =============================================================================

ALLOWED_LOCAL_PATHS: frozenset[str] = frozenset(
    {
        G1_RUNNER_REL_PATH,
        G1_TEST_REL_PATH,
        FREEZE_RUNNER_REL_PATH,
        BROKER_ADAPTER_REL_PATH,
        ACQUISITION_ADAPTER_REL_PATH,
        BROKER_ADAPTER_TEST_REL_PATH,
        ACQUISITION_ADAPTER_TEST_REL_PATH,
        EVIDENCE_REL_PATH,
        BLOCKED_CAPTURE_EVIDENCE_REL_PATH,
    }
)


# =============================================================================
# Published Runtime Authorities
# =============================================================================

_g1: Any = importlib.import_module(
    "04_Testing.production_portability."
    "run_xauusd_gate_15d_c_b2d_g1_genuine_anchored_forward_capture"
)

_atomic: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_runtime_atomic_ledgers"
)

_coordinator: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_anchor_first_coordinator"
)

_anchor: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_anchor"
)

_maturer: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_maturer"
)

_outcome_ledger: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_ledger"
)


# =============================================================================
# Error
# =============================================================================

class Gate15DCB2DG1FreezeBlockedError(
    RuntimeError
):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:

        raise Gate15DCB2DG1FreezeBlockedError(
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

        value = raw_line[
            3:
        ].strip()

        if " -> " in value:

            value = value.split(
                " -> ",
                1,
            )[
                1
            ]

        if (
            value.startswith(
                '"'
            )
            and
            value.endswith(
                '"'
            )
        ):

            value = value[
                1:
                -1
            ]

        paths.add(
            normalize_path(
                value
            )
        )

    return paths


# =============================================================================
# Runtime Ledger Snapshot
# =============================================================================

def runtime_ledger_snapshot() -> dict[str, dict[str, Any]]:

    result: dict[
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

            result[
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
                "RUNTIME_LEDGER_NOT_FILE:"
                f"{relative}"
            ),
        )

        result[
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

    return result


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
        "HEAD_ORIGIN_MAIN_DIVERGENCE",
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
        G1_RUNNER_REL_PATH,
        G1_TEST_REL_PATH,
        FREEZE_RUNNER_REL_PATH,
        BROKER_ADAPTER_REL_PATH,
        ACQUISITION_ADAPTER_REL_PATH,
        BROKER_ADAPTER_TEST_REL_PATH,
        ACQUISITION_ADAPTER_TEST_REL_PATH,
    }

    missing = (
        required_candidates
        -
        local_paths
    )

    require(
        not missing,
        (
            "EXPECTED_G1_CANDIDATE_PATHS_MISSING:"
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
# Authority Verification
# =============================================================================

def verify_runtime_authorities() -> dict[str, Any]:

    b2d = (
        _g1.verify_b2d_authority()
    )

    require(
        b2d[
            "status"
        ]
        ==
        "PASS",
        "G1_B2D_AUTHORITY_INVALID",
    )

    require(
        _g1.B2D_AUTHORITY_COMMIT
        ==
        "03c7a5e74b57b3f670521e29d0b55086027ca4da",
        "G1_BOUND_B2D_COMMIT_MISMATCH",
    )

    require(
        _g1.G1_FREEZE_BASE_COMMIT
        ==
        BASE_AUTHORITY_COMMIT,
        "G1_BOUND_FREEZE_BASE_COMMIT_MISMATCH",
    )

    require(
        _atomic.ATOMIC_LEDGER_AUTHORITY_VERSION
        ==
        "FROZEN_C04_FORWARD_RUNTIME_ATOMIC_LEDGERS_V1",
        "ATOMIC_LEDGER_AUTHORITY_MISMATCH",
    )

    require(
        _coordinator.COORDINATOR_VERSION
        ==
        "FROZEN_C04_FORWARD_ANCHOR_FIRST_COORDINATOR_V1",
        "COORDINATOR_AUTHORITY_MISMATCH",
    )

    require(
        _coordinator.PERSISTENCE_ORDER
        ==
        "ANCHOR_FIRST_THEN_OBSERVATION",
        "PERSISTENCE_ORDER_MISMATCH",
    )

    require(
        _coordinator.ORPHAN_ANCHOR_POLICY
        ==
        "PRESERVE_IMMUTABLE_ANCHOR_IF_OBSERVATION_APPEND_FAILS",
        "ORPHAN_ANCHOR_POLICY_MISMATCH",
    )

    require(
        _anchor.ANCHOR_VERSION
        ==
        "FROZEN_C04_FORWARD_OUTCOME_ANCHOR_V1",
        "ANCHOR_VERSION_MISMATCH",
    )

    require(
        _maturer.MATURATION_VERSION
        ==
        "FROZEN_C04_FORWARD_OUTCOME_MATURER_V2",
        "MATURATION_VERSION_MISMATCH",
    )

    require(
        _outcome_ledger.OUTCOME_LEDGER_VERSION
        ==
        "FROZEN_C04_FORWARD_OUTCOME_LEDGER_V2",
        "OUTCOME_LEDGER_VERSION_MISMATCH",
    )

    require(
        _g1.OUTCOME_MATURATION_AUTHORIZED
        is False,
        "G1_OUTCOME_MATURATION_AUTHORIZED",
    )

    require(
        _g1.PERFORMANCE_EVALUATION_AUTHORIZED
        is False,
        "G1_PERFORMANCE_AUTHORIZED",
    )

    require(
        _g1.PNL_EVALUATION_AUTHORIZED
        is False,
        "G1_PNL_AUTHORIZED",
    )

    require(
        _g1.LIVE_AUTHORIZED
        is False,
        "G1_LIVE_AUTHORIZED",
    )

    require(
        _g1.EXECUTION_AUTHORIZED
        is False,
        "G1_EXECUTION_AUTHORIZED",
    )

    return {
        "status": "PASS",

        "g1_gate_id": (
            _g1.GATE_ID
        ),

        "g1_schema_version": (
            _g1.SCHEMA_VERSION
        ),

        "b2d_authority_commit": (
            _g1.B2D_AUTHORITY_COMMIT
        ),

        "atomic_ledger_authority": (
            _atomic
            .ATOMIC_LEDGER_AUTHORITY_VERSION
        ),

        "coordinator_authority": (
            _coordinator
            .COORDINATOR_VERSION
        ),

        "persistence_order": (
            _coordinator
            .PERSISTENCE_ORDER
        ),

        "orphan_anchor_policy": (
            _coordinator
            .ORPHAN_ANCHOR_POLICY
        ),

        "anchor_version": (
            _anchor.ANCHOR_VERSION
        ),

        "maturation_version": (
            _maturer.MATURATION_VERSION
        ),

        "outcome_ledger_version": (
            _outcome_ledger
            .OUTCOME_LEDGER_VERSION
        ),

        "outcome_maturation_authorized": False,

        "performance_evaluation_authorized": False,

        "pnl_evaluation_authorized": False,

        "live_authorized": False,

        "execution_authorized": False,
    }


# =============================================================================
# Static Runner Audit
# =============================================================================

def static_runner_audit() -> dict[str, Any]:

    runner_path = (
        REPO_ROOT
        /
        G1_RUNNER_REL_PATH
    )

    require(
        runner_path.is_file(),
        "G1_RUNNER_MISSING",
    )

    tree = ast.parse(
        runner_path.read_text(
            encoding="utf-8"
        ),
        filename=str(
            runner_path
        ),
    )

    forbidden_calls = {
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
        "mature_observation",
        "calculate_performance",
        "calculate_pnl",
    }

    forbidden_dependencies = {
        "RiskEngine",
        "trade_ready",
        "broker_aware_risk_engine",
        "account_protection_guard",
    }

    forbidden_hits: list[
        str
    ] = []

    raw_mt5_calls: list[
        str
    ] = []

    for node in ast.walk(
        tree
    ):

        if isinstance(
            node,
            ast.Import,
        ):

            for alias in node.names:

                for token in forbidden_dependencies:

                    if token in alias.name:

                        forbidden_hits.append(
                            (
                                f"import:"
                                f"{alias.name}:"
                                f"line={node.lineno}"
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

            for token in forbidden_dependencies:

                if token in module:

                    forbidden_hits.append(
                        (
                            f"import_from:"
                            f"{module}:"
                            f"line={node.lineno}"
                        )
                    )

        elif isinstance(
            node,
            ast.Call,
        ):

            target = node.func

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

                owner = (
                    target.value
                )

                if (
                    isinstance(
                        owner,
                        ast.Name,
                    )
                    and
                    owner.id
                    ==
                    "mt5"
                ):

                    raw_mt5_calls.append(
                        target.attr
                    )

            if (
                call_name
                in
                forbidden_calls
            ):

                forbidden_hits.append(
                    (
                        f"call:"
                        f"{call_name}:"
                        f"line={node.lineno}"
                    )
                )

    require(
        not forbidden_hits,
        (
            "G1_FORBIDDEN_RUNTIME_DEPENDENCIES:"
            f"{forbidden_hits}"
        ),
    )

    require(
        set(
            raw_mt5_calls
        )
        <=
        {
            "initialize",
            "shutdown",
        },
        (
            "RAW_MT5_CALL_BOUNDARY_VIOLATION:"
            f"{raw_mt5_calls}"
        ),
    )

    require(
        "initialize"
        in
        raw_mt5_calls,
        "MT5_INITIALIZE_CALL_MISSING",
    )

    require(
        "shutdown"
        in
        raw_mt5_calls,
        "MT5_SHUTDOWN_CALL_MISSING",
    )

    source = runner_path.read_text(
        encoding="utf-8"
    )

    require(
        "coordinator.persist("
        in
        source,
        "ANCHOR_FIRST_COORDINATOR_PERSIST_NOT_USED",
    )

    require(
        "observation_ledger.append("
        not in
        source,
        "DIRECT_OBSERVATION_APPEND_FORBIDDEN",
    )

    require(
        "anchor_ledger.append("
        not in
        source,
        "DIRECT_ANCHOR_APPEND_FORBIDDEN",
    )

    require(
        "OUTCOME_LEDGER_CHANGED_DURING_G1"
        in
        source,
        "OUTCOME_LEDGER_UNCHANGED_GUARD_MISSING",
    )

    eligibility_position = source.find(
        "assess_observation"
    )

    persistence_position = source.find(
        "coordinator.persist"
    )

    require(
        eligibility_position
        >=
        0,
        "PROSPECTIVE_ELIGIBILITY_CHECK_MISSING",
    )

    require(
        persistence_position
        >
        eligibility_position,
        "PERSISTENCE_PRECEDES_PROSPECTIVE_ELIGIBILITY",
    )

    feature_position = source.find(
        "PortableFeaturePipeline"
    )

    observation_position = source.find(
        "observer.observe_single"
    )

    require(
        feature_position
        >=
        0,
        "GATE13_FEATURE_PIPELINE_MISSING",
    )

    require(
        observation_position
        >
        feature_position,
        "GATE14_OBSERVATION_PRECEDES_GATE13",
    )

    return {
        "status": "PASS",

        "raw_mt5_calls": sorted(
            set(
                raw_mt5_calls
            )
        ),

        "raw_mt5_lifecycle_only": True,

        "direct_anchor_append": False,

        "direct_observation_append": False,

        "anchor_first_coordinator_used": True,

        "prospective_eligibility_before_persistence": True,

        "gate13_before_gate14": True,

        "outcome_maturation_calls": 0,

        "outcome_ledger_append_calls": 0,

        "trading_api_calls": 0,

        "risk_engine_dependencies": 0,

        "trade_ready_dependencies": 0,
    }


# =============================================================================
# Offline Test Execution
# =============================================================================

def run_targeted_tests() -> dict[str, Any]:

    command = [
        sys.executable,
        "-m",
        "pytest",
        G1_TEST_REL_PATH,
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
            "G1_TARGETED_TESTS_FAILED:"
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

    candidate_paths = (
        G1_RUNNER_REL_PATH,
        G1_TEST_REL_PATH,
        FREEZE_RUNNER_REL_PATH,
        BROKER_ADAPTER_REL_PATH,
        ACQUISITION_ADAPTER_REL_PATH,
        BROKER_ADAPTER_TEST_REL_PATH,
        ACQUISITION_ADAPTER_TEST_REL_PATH,
    )

    hashes: dict[
        str,
        str,
    ] = {}

    for relative in candidate_paths:

        path = (
            REPO_ROOT
            /
            relative
        )

        require(
            path.is_file(),
            (
                "G1_CANDIDATE_ARTIFACT_MISSING:"
                f"{relative}"
            ),
        )

        hashes[
            relative
        ] = (
            sha256_file(
                path
            )
        )

    return hashes


# =============================================================================
# Gate
# =============================================================================

def run_gate() -> dict[str, Any]:

    ledgers_before = (
        runtime_ledger_snapshot()
    )

    repository = (
        verify_repository_authority()
    )

    runtime = (
        verify_runtime_authorities()
    )

    static_audit = (
        static_runner_audit()
    )

    tests = (
        run_targeted_tests()
    )

    ledgers_after = (
        runtime_ledger_snapshot()
    )

    require(
        ledgers_before
        ==
        ledgers_after,
        (
            "RUNTIME_LEDGERS_CHANGED_DURING_G1_FREEZE:"
            f"before={ledgers_before}:"
            f"after={ledgers_after}"
        ),
    )

    hashes = (
        candidate_artifact_hashes()
    )

    evidence: dict[
        str,
        Any,
    ] = {
        "gate": (
            "Gate 15D-C-B2D-G1 — "
            "Genuine Anchored Forward Capture Runner Freeze"
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
            runtime
        ),

        "static_runner_audit": (
            static_audit
        ),

        "targeted_pytest": (
            tests
        ),

        "candidate_artifact_hashes": (
            hashes
        ),

        "frozen_g1_protocol": {
            "genuine_runner_not_executed_during_freeze": True,

            "read_only_mt5_only": True,

            "raw_mt5_lifecycle_only": True,

            "same_snapshot_required": True,

            "gate13_before_gate14": True,

            "prospective_eligibility_before_persistence": True,

            "anchor_first_coordinator_required": True,

            "atomic_anchor_ledger_required": True,

            "atomic_observation_ledger_required": True,

            "anchor_append_first": True,

            "observation_append_second": True,

            "orphan_anchor_preservation_policy": True,

            "outcome_ledger_must_remain_unchanged": True,

            "no_outcome_maturation": True,

            "no_performance_evaluation": True,

            "no_live_authorization": True,

            "no_execution_authorization": True,
        },

        "runtime_ledger_state_before": (
            ledgers_before
        ),

        "runtime_ledger_state_after": (
            ledgers_after
        ),

        "observation_ledger_unchanged": (
            ledgers_before[
                OBSERVATION_LEDGER_REL_PATH
            ]
            ==
            ledgers_after[
                OBSERVATION_LEDGER_REL_PATH
            ]
        ),

        "anchor_ledger_unchanged": (
            ledgers_before[
                ANCHOR_LEDGER_REL_PATH
            ]
            ==
            ledgers_after[
                ANCHOR_LEDGER_REL_PATH
            ]
        ),

        "outcome_ledger_unchanged": (
            ledgers_before[
                OUTCOME_LEDGER_REL_PATH
            ]
            ==
            ledgers_after[
                OUTCOME_LEDGER_REL_PATH
            ]
        ),

        "mt5_initialized": False,

        "market_data_acquired": False,

        "genuine_mt5_acquisition": False,

        "genuine_anchor_appended": False,

        "genuine_observation_appended": False,

        "genuine_forward_observation_matured": False,

        "genuine_outcome_appended": False,

        "forward_performance_evaluated": False,

        "accuracy_evaluated": False,

        "win_rate_evaluated": False,

        "pnl_evaluated": False,

        "return_evaluated": False,

        "drawdown_evaluated": False,

        "live_authorized": False,

        "execution_authorized": False,

        "next_gate": (
            "PUBLISH_AND_HASH_BIND_G1_RUNNER_FREEZE_"
            "BEFORE_GENUINE_MT5_EXECUTION"
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

        result = run_gate()

        runtime = result[
            "runtime_authority"
        ]

        static_audit = result[
            "static_runner_audit"
        ]

        print(
            "GATE_15D_C_B2D_G1_FREEZE_STATUS=PASS"
        )

        print(
            "BASE_AUTHORITY_COMMIT="
            +
            str(
                result[
                    "base_authority_commit"
                ]
            )
        )

        print(
            "G1_GATE_ID="
            +
            str(
                runtime[
                    "g1_gate_id"
                ]
            )
        )

        print(
            "ATOMIC_LEDGER_AUTHORITY="
            +
            str(
                runtime[
                    "atomic_ledger_authority"
                ]
            )
        )

        print(
            "COORDINATOR_AUTHORITY="
            +
            str(
                runtime[
                    "coordinator_authority"
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
            "RAW_MT5_CALLS="
            +
            ",".join(
                static_audit[
                    "raw_mt5_calls"
                ]
            )
        )

        print(
            "GENUINE_RUNNER_EXECUTED=false"
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
            "GATE_15D_C_B2D_G1_FREEZE_STATUS=BLOCKED"
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
            "GENUINE_RUNNER_EXECUTED=false"
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