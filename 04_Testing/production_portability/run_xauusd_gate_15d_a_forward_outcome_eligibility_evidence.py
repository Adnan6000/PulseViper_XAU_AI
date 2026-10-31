"""
===============================================================================
Module      : run_xauusd_gate_15d_a_forward_outcome_eligibility_evidence.py
Project     : PulseViper XAU AI
Purpose     : Gate 15D-A — Prospective Forward Outcome Eligibility Evidence
===============================================================================

OFFLINE / READ-ONLY AUTHORITY RUNNER.

This runner proves:
- Gate 15C outcome contract is established and unchanged.
- Gate 15D-A prospective eligibility boundary is explicit.
- Observations at or before Gate 15C activation remain permanently excluded
  from formal forward-performance evaluation.
- The existing first genuine TRUE_FORWARD observation is PRE_CONTRACT.
- No market outcome is calculated.
- No performance metric is calculated.
- No broker access occurs.
- No shadow ledger mutation occurs.
- No model/feature/risk/execution authority changes occur.

This runner does NOT:
- acquire market data
- mature outcomes
- calculate accuracy / win rate / PnL / return / drawdown
- access validation/test holdouts
- retrain/refit/calibrate/tune/reselect the frozen model
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
# Gate Authorities
# =============================================================================

GATE_ID: str = (
    "GATE_15D_A_PROSPECTIVE_FORWARD_OUTCOME_ELIGIBILITY"
)

SCHEMA_VERSION: str = "1.0.0"

GATE_15C_EVIDENCE_AUTHORITY_COMMIT: str = (
    "59f5b6815f0c8d0a51725aa5123812595566b530"
)

GATE_15C_ACTIVATION_UTC: str = (
    "2026-09-28T11:16:59Z"
)


ELIGIBILITY_REL_PATH: str = (
    "02_AI/Models/"
    "frozen_c04_forward_outcome_eligibility.py"
)

ELIGIBILITY_TEST_REL_PATH: str = (
    "04_Testing/production_portability/"
    "test_frozen_c04_forward_outcome_eligibility.py"
)

CONTRACT_TEST_REL_PATH: str = (
    "04_Testing/production_portability/"
    "test_frozen_c04_forward_outcome_contract.py"
)

RUNNER_REL_PATH: str = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_a_forward_outcome_eligibility_evidence.py"
)

EVIDENCE_REL_PATH: str = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_a_forward_outcome_eligibility_evidence.json"
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


ALLOWED_GATE_15D_A_PATHS: frozenset[str] = frozenset(
    {
        ELIGIBILITY_REL_PATH,
        ELIGIBILITY_TEST_REL_PATH,
        RUNNER_REL_PATH,
        EVIDENCE_REL_PATH,
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


FORBIDDEN_IMPORT_ROOTS: frozenset[str] = frozenset(
    {
        "MetaTrader5",
    }
)


FORBIDDEN_IMPORTED_NAMES: frozenset[str] = frozenset(
    {
        "RiskEngine",
        "broker_aware_risk_engine",
        "account_protection_guard",
        "trade_ready",
    }
)


# =============================================================================
# Modules
# =============================================================================

_eligibility: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_eligibility"
)

_outcome_contract: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_contract"
)


# =============================================================================
# Error
# =============================================================================

class Gate15DAError(
    RuntimeError
):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise Gate15DAError(
            reason
        )


# =============================================================================
# Generic Helpers
# =============================================================================

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
# Git Authority
# =============================================================================

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

        path = raw_line[
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
            and path.endswith(
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
        GATE_15C_EVIDENCE_AUTHORITY_COMMIT,
        head,
    )

    require(
        ancestor.returncode
        ==
        0,
        "GATE_15C_AUTHORITY_NOT_ANCESTOR",
    )

    committed_since_gate_15c = {
        normalize_path(
            value
        )
        for value
        in git_output(
            "diff",
            "--name-only",
            (
                f"{GATE_15C_EVIDENCE_AUTHORITY_COMMIT}"
                f"..{head}"
            ),
        ).splitlines()
        if value.strip()
    }

    unexpected_committed = (
        committed_since_gate_15c
        -
        set(
            ALLOWED_GATE_15D_A_PATHS
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
            ALLOWED_GATE_15D_A_PATHS
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
        "gate_15c_authority_commit": (
            GATE_15C_EVIDENCE_AUTHORITY_COMMIT
        ),
        "gate_15c_authority_is_ancestor": True,
        "committed_since_gate_15c": sorted(
            committed_since_gate_15c
        ),
        "local_gate_15d_a_paths": sorted(
            local_paths
        ),
        "unexpected_committed_paths": [],
        "unexpected_local_paths": [],
    }


# =============================================================================
# Ledger Read-Only Verification
# =============================================================================

def load_observation_ledger() -> list[dict[str, Any]]:

    require(
        OBSERVATION_LEDGER_PATH.is_file(),
        "OBSERVATION_LEDGER_MISSING",
    )

    records: list[
        dict[str, Any]
    ] = []

    with OBSERVATION_LEDGER_PATH.open(
        "r",
        encoding="utf-8",
    ) as handle:

        for line_number, raw_line in enumerate(
            handle,
            start=1,
        ):

            line = raw_line.strip()

            if not line:
                continue

            try:

                value = json.loads(
                    line
                )

            except Exception as exc:

                raise Gate15DAError(
                    (
                        "OBSERVATION_LEDGER_JSON_INVALID:"
                        f"{line_number}"
                    )
                ) from exc

            require(
                isinstance(
                    value,
                    dict,
                ),
                (
                    "OBSERVATION_LEDGER_RECORD_NOT_OBJECT:"
                    f"{line_number}"
                ),
            )

            records.append(
                value
            )

    require(
        bool(
            records
        ),
        "OBSERVATION_LEDGER_EMPTY",
    )

    return records


def verify_existing_forward_observation() -> dict[str, Any]:

    ledger_hash_before = sha256_file(
        OBSERVATION_LEDGER_PATH
    )

    records = (
        load_observation_ledger()
    )

    true_forward = [
        record
        for record in records
        if (
            record.get(
                "source_provenance"
            )
            ==
            "TRUE_FORWARD_OBSERVATION"
        )
    ]

    require(
        bool(
            true_forward
        ),
        "TRUE_FORWARD_OBSERVATION_NOT_FOUND",
    )

    assessed = [
        _eligibility.assess_observation(
            record
        )
        for record in true_forward
    ]

    assessed = sorted(
        assessed,
        key=lambda item: (
            item.decision_time_utc
        ),
    )

    first = assessed[
        0
    ]

    require(
        first.eligible_for_formal_maturation
        is False,
        (
            "FIRST_EXISTING_OBSERVATION_"
            "UNEXPECTEDLY_ELIGIBLE"
        ),
    )

    require(
        first.eligibility_reason
        ==
        "PRE_CONTRACT_OBSERVATION",
        (
            "FIRST_EXISTING_OBSERVATION_"
            "PRE_CONTRACT_REASON_MISMATCH"
        ),
    )

    require(
        first.decision_time_utc
        ==
        "2026-09-28T10:15:00Z",
        (
            "FIRST_EXISTING_OBSERVATION_"
            "DECISION_TIME_MISMATCH:"
            f"{first.decision_time_utc}"
        ),
    )

    eligible_count = sum(
        1
        for decision in assessed
        if (
            decision
            .eligible_for_formal_maturation
        )
    )

    pre_contract_count = sum(
        1
        for decision in assessed
        if (
            not decision
            .eligible_for_formal_maturation
        )
    )

    ledger_hash_after = sha256_file(
        OBSERVATION_LEDGER_PATH
    )

    require(
        ledger_hash_before
        ==
        ledger_hash_after,
        "OBSERVATION_LEDGER_CHANGED_DURING_READ_ONLY_VERIFICATION",
    )

    return {
        "status": "PASS",
        "ledger_sha256_before": (
            ledger_hash_before
        ),
        "ledger_sha256_after": (
            ledger_hash_after
        ),
        "ledger_unchanged": True,
        "total_records": len(
            records
        ),
        "true_forward_records": len(
            true_forward
        ),
        "formal_maturation_eligible_count": (
            eligible_count
        ),
        "pre_contract_excluded_count": (
            pre_contract_count
        ),
        "first_true_forward": {
            "logical_observation_id": (
                first.logical_observation_id
            ),
            "decision_time_utc": (
                first.decision_time_utc
            ),
            "eligible_for_formal_maturation": (
                first
                .eligible_for_formal_maturation
            ),
            "eligibility_reason": (
                first.eligibility_reason
            ),
        },
    }


# =============================================================================
# Contract / Eligibility Verification
# =============================================================================

def verify_contract_authorities() -> dict[str, Any]:

    require(
        bool(
            _outcome_contract
            .verify_frozen_contract()
        ),
        "GATE_15C_OUTCOME_CONTRACT_INVALID",
    )

    require(
        bool(
            _eligibility
            .verify_authorities()
        ),
        "GATE_15D_A_ELIGIBILITY_AUTHORITY_INVALID",
    )

    require(
        _eligibility
        .GATE_15C_EVIDENCE_AUTHORITY_COMMIT
        ==
        GATE_15C_EVIDENCE_AUTHORITY_COMMIT,
        "GATE_15C_COMMIT_AUTHORITY_MISMATCH",
    )

    require(
        _eligibility
        .GATE_15C_ACTIVATION_UTC
        ==
        GATE_15C_ACTIVATION_UTC,
        "GATE_15C_ACTIVATION_TIME_MISMATCH",
    )

    require(
        _eligibility
        .PERFORMANCE_EVALUATION_AUTHORIZED
        is False,
        "PERFORMANCE_EVALUATION_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _eligibility
        .OUTCOME_MATURATION_AUTHORIZED
        is False,
        "OUTCOME_MATURATION_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _eligibility
        .MT5_ACCESS_AUTHORIZED
        is False,
        "MT5_ACCESS_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _eligibility
        .LIVE_AUTHORIZED
        is False,
        "LIVE_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _eligibility
        .EXECUTION_AUTHORIZED
        is False,
        "EXECUTION_UNEXPECTEDLY_AUTHORIZED",
    )

    return {
        "status": "PASS",
        "gate_15c_contract_fingerprint_sha256": (
            _outcome_contract
            .compute_contract_fingerprint()
        ),
        "eligibility_version": (
            _eligibility
            .ELIGIBILITY_VERSION
        ),
        "activation_authority_commit": (
            GATE_15C_EVIDENCE_AUTHORITY_COMMIT
        ),
        "activation_utc": (
            GATE_15C_ACTIVATION_UTC
        ),
        "pre_contract_policy": (
            _eligibility
            .PRE_CONTRACT_POLICY
        ),
    }


# =============================================================================
# Static Safety
# =============================================================================

def static_safety_audit() -> dict[str, Any]:

    audited_paths = [
        REPO_ROOT
        /
        ELIGIBILITY_REL_PATH,

        REPO_ROOT
        /
        RUNNER_REL_PATH,
    ]

    violations: list[
        dict[str, str]
    ] = []

    for path in audited_paths:

        require(
            path.is_file(),
            (
                "STATIC_AUDIT_FILE_MISSING:"
                f"{path}"
            ),
        )

        source = path.read_text(
            encoding="utf-8"
        )

        tree = ast.parse(
            source
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
                                "file": str(
                                    path.relative_to(
                                        REPO_ROOT
                                    )
                                ).replace(
                                    "\\",
                                    "/",
                                ),
                                "type": (
                                    "forbidden_import"
                                ),
                                "symbol": (
                                    alias.name
                                ),
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

                module_root = (
                    module_name.split(
                        ".",
                        1,
                    )[0]
                    if module_name
                    else ""
                )

                if (
                    module_root
                    in FORBIDDEN_IMPORT_ROOTS
                ):
                    violations.append(
                        {
                            "file": str(
                                path.relative_to(
                                    REPO_ROOT
                                )
                            ).replace(
                                "\\",
                                "/",
                            ),
                            "type": (
                                "forbidden_import_from"
                            ),
                            "symbol": (
                                module_name
                            ),
                        }
                    )

                for alias in node.names:

                    if (
                        alias.name
                        in FORBIDDEN_IMPORTED_NAMES
                    ):
                        violations.append(
                            {
                                "file": str(
                                    path.relative_to(
                                        REPO_ROOT
                                    )
                                ).replace(
                                    "\\",
                                    "/",
                                ),
                                "type": (
                                    "forbidden_imported_name"
                                ),
                                "symbol": (
                                    alias.name
                                ),
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
                    name = (
                        function.id
                    )

                elif isinstance(
                    function,
                    ast.Attribute,
                ):
                    name = (
                        function.attr
                    )

                else:
                    name = ""

                if (
                    name
                    in FORBIDDEN_BROKER_CALLS
                ):
                    violations.append(
                        {
                            "file": str(
                                path.relative_to(
                                    REPO_ROOT
                                )
                            ).replace(
                                "\\",
                                "/",
                            ),
                            "type": (
                                "forbidden_broker_call"
                            ),
                            "symbol": (
                                name
                            ),
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
            for path in audited_paths
        ],
        "violation_count": 0,
        "violations": [],
    }


# =============================================================================
# Tests
# =============================================================================

def run_targeted_tests() -> dict[str, Any]:

    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            CONTRACT_TEST_REL_PATH,
            ELIGIBILITY_TEST_REL_PATH,
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
                -1500:
            ]
            +
            process.stderr[
                -1500:
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
                -1000:
            ]
        ),
    }


# =============================================================================
# Main Gate
# =============================================================================

def run_gate() -> dict[str, Any]:

    repository = (
        verify_repository_authority()
    )

    authority = (
        verify_contract_authorities()
    )

    static_safety = (
        static_safety_audit()
    )

    ledger = (
        verify_existing_forward_observation()
    )

    tests = (
        run_targeted_tests()
    )

    artifact_hashes: dict[
        str,
        str,
    ] = {}

    for relative_path in (
        ELIGIBILITY_REL_PATH,
        ELIGIBILITY_TEST_REL_PATH,
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
                "GATE_15D_A_ARTIFACT_MISSING:"
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
            "Gate 15D-A — Prospective "
            "Forward Outcome Eligibility Authority"
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

        "authority": (
            authority
        ),

        "existing_forward_observation": (
            ledger
        ),

        "static_safety": (
            static_safety
        ),

        "targeted_tests": (
            tests
        ),

        "candidate_artifact_hashes": (
            artifact_hashes
        ),

        "prospective_activation_defined": True,

        "pre_contract_observations_permanently_excluded_from_formal_performance": (
            True
        ),

        "outcome_maturation_authorized": False,

        "forward_outcomes_matured": False,

        "forward_outcomes_evaluated": False,

        "forward_performance_evaluated": False,

        "accuracy_evaluated": False,

        "win_rate_evaluated": False,

        "pnl_evaluated": False,

        "return_evaluated": False,

        "drawdown_evaluated": False,

        "new_forward_observation_acquired": False,

        "broker_initialized": False,

        "observation_ledger_mutated": False,

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

        evidence = run_gate()

        existing = evidence[
            "existing_forward_observation"
        ]

        authority = evidence[
            "authority"
        ]

        print(
            "GATE_15D_A_STATUS=PASS"
        )

        print(
            "ELIGIBILITY_VERSION="
            +
            str(
                authority[
                    "eligibility_version"
                ]
            )
        )

        print(
            "ACTIVATION_AUTHORITY_COMMIT="
            +
            str(
                authority[
                    "activation_authority_commit"
                ]
            )
        )

        print(
            "ACTIVATION_UTC="
            +
            str(
                authority[
                    "activation_utc"
                ]
            )
        )

        print(
            "TRUE_FORWARD_RECORDS="
            +
            str(
                existing[
                    "true_forward_records"
                ]
            )
        )

        print(
            "PRE_CONTRACT_EXCLUDED="
            +
            str(
                existing[
                    "pre_contract_excluded_count"
                ]
            )
        )

        print(
            "FORMAL_MATURATION_ELIGIBLE="
            +
            str(
                existing[
                    "formal_maturation_eligible_count"
                ]
            )
        )

        print(
            "FIRST_OBSERVATION_DECISION_TIME="
            +
            str(
                existing[
                    "first_true_forward"
                ][
                    "decision_time_utc"
                ]
            )
        )

        print(
            "FIRST_OBSERVATION_ELIGIBILITY="
            +
            str(
                existing[
                    "first_true_forward"
                ][
                    "eligibility_reason"
                ]
            )
        )

        print(
            "OUTCOME_MATURATION_AUTHORIZED=false"
        )

        print(
            "FORWARD_OUTCOMES_EVALUATED=false"
        )

        print(
            "FORWARD_PERFORMANCE_EVALUATED=false"
        )

        print(
            "NEW_FORWARD_OBSERVATION_ACQUIRED=false"
        )

        print(
            "BROKER_INITIALIZED=false"
        )

        print(
            "OBSERVATION_LEDGER_MUTATED=false"
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
            "GATE_15D_A_STATUS=FAIL"
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
            "OUTCOME_MATURATION_AUTHORIZED=false"
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