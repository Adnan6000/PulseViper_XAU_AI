"""
===============================================================================
Module      : run_xauusd_gate_15d_c_a_forward_outcome_maturation_evidence.py
Project     : PulseViper XAU AI
Purpose     : Gate 15D-C-A — Frozen Forward Outcome Maturation Evidence
===============================================================================

OFFLINE ONLY.

This runner proves that forward-outcome maturation semantics are frozen and
aligned with the accepted historical target construction.

It does NOT:
- initialize MT5
- acquire market data
- mature the genuine 11:45 UTC observation
- write any outcome ledger
- mutate the TRUE_FORWARD observation ledger
- calculate accuracy / win rate / PnL / return / drawdown
- access validation/test holdouts
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
# Authorities
# =============================================================================

GATE_ID: str = (
    "GATE_15D_C_A_FROZEN_FORWARD_OUTCOME_MATURATION"
)

SCHEMA_VERSION: str = "1.0.0"

GATE_15D_B_EVIDENCE_AUTHORITY_COMMIT: str = (
    "9d14734e36667a28738b2fe4f4c610553e7269e1"
)

MATURER_REL_PATH: str = (
    "02_AI/Models/"
    "frozen_c04_forward_outcome_maturer.py"
)

MATURER_TEST_REL_PATH: str = (
    "04_Testing/production_portability/"
    "test_frozen_c04_forward_outcome_maturer.py"
)

RUNNER_REL_PATH: str = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_a_forward_outcome_maturation_evidence.py"
)

EVIDENCE_REL_PATH: str = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_a_forward_outcome_maturation_evidence.json"
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

SOURCE_AUTHORITY_PATHS: tuple[str, ...] = (
    "02_AI/Dataset/training_matrix_builder.py",
    "02_AI/Dataset/training_target_relabeler.py",
    "02_AI/Features/feature_generator.py",
    "02_AI/Features/volatility_features.py",
)

ALLOWED_GATE_PATHS: frozenset[str] = frozenset(
    {
        MATURER_REL_PATH,
        MATURER_TEST_REL_PATH,
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


# =============================================================================
# Existing Authorities
# =============================================================================

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
# Error / Helpers
# =============================================================================

class Gate15DCAError(
    RuntimeError
):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise Gate15DCAError(
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

    temp = path.with_suffix(
        path.suffix
        +
        ".tmp"
    )

    temp.write_text(
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

    temp.replace(
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
        GATE_15D_B_EVIDENCE_AUTHORITY_COMMIT,
        head,
    )

    require(
        ancestor.returncode
        ==
        0,
        "GATE_15D_B_AUTHORITY_NOT_ANCESTOR",
    )

    committed_since_gate = {
        normalize_path(
            item
        )
        for item
        in git_output(
            "diff",
            "--name-only",
            (
                f"{GATE_15D_B_EVIDENCE_AUTHORITY_COMMIT}"
                f"..{head}"
            ),
        ).splitlines()
        if item.strip()
    }

    unexpected_committed = (
        committed_since_gate
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
        "gate_15d_b_authority_commit": (
            GATE_15D_B_EVIDENCE_AUTHORITY_COMMIT
        ),
        "gate_15d_b_authority_is_ancestor": True,
        "committed_since_gate_15d_b": sorted(
            committed_since_gate
        ),
        "local_gate_paths": sorted(
            local_paths
        ),
        "unexpected_committed_paths": [],
        "unexpected_local_paths": [],
    }


# =============================================================================
# Frozen Source Semantics
# =============================================================================

def verify_source_semantics() -> dict[str, Any]:

    hashes: dict[
        str,
        str,
    ] = {}

    texts: dict[
        str,
        str,
    ] = {}

    for relative_path in (
        SOURCE_AUTHORITY_PATHS
    ):

        path = (
            REPO_ROOT
            /
            relative_path
        )

        require(
            path.is_file(),
            (
                "SOURCE_AUTHORITY_MISSING:"
                f"{relative_path}"
            ),
        )

        hashes[
            relative_path
        ] = sha256_file(
            path
        )

        texts[
            relative_path
        ] = path.read_text(
            encoding="utf-8"
        )

    builder = texts[
        "02_AI/Dataset/training_matrix_builder.py"
    ]

    relabeler = texts[
        "02_AI/Dataset/training_target_relabeler.py"
    ]

    volatility = texts[
        "02_AI/Features/volatility_features.py"
    ]

    require(
        "featured_frame[" in builder
        and '"atr14"' in builder,
        "TRAINING_ATR14_REFERENCE_NOT_FOUND",
    )

    require(
        "future_slice = slice(" in builder,
        "TRAINING_FUTURE_SLICE_NOT_FOUND",
    )

    require(
        "index\n                +\n                1" in builder,
        "TRAINING_FUTURE_SLICE_START_NOT_FOUND",
    )

    require(
        "horizon_bars\n                +\n                1" in builder,
        "TRAINING_FUTURE_SLICE_END_NOT_FOUND",
    )

    require(
        "target_up_excursion_atr" in builder,
        "TRAINING_UP_EXCURSION_NOT_FOUND",
    )

    require(
        "target_down_excursion_atr" in builder,
        "TRAINING_DOWN_EXCURSION_NOT_FOUND",
    )

    require(
        "up >= profit" in relabeler,
        "RELABEL_LONG_UP_RULE_NOT_FOUND",
    )

    require(
        "down <= adverse" in relabeler,
        "RELABEL_LONG_ADVERSE_RULE_NOT_FOUND",
    )

    require(
        "down >= profit" in relabeler,
        "RELABEL_SHORT_DOWN_RULE_NOT_FOUND",
    )

    require(
        "up <= adverse" in relabeler,
        "RELABEL_SHORT_ADVERSE_RULE_NOT_FOUND",
    )

    require(
        ".rolling(period).mean()" in volatility,
        "ATR14_ROLLING_MEAN_AUTHORITY_NOT_FOUND",
    )

    return {
        "status": "PASS",
        "source_hashes": hashes,
        "horizon_semantics": (
            "NEXT_12_COMPLETED_M5_ROWS_AFTER_DECISION_ROW"
        ),
        "entry_reference": (
            "DECISION_M5_CLOSE"
        ),
        "atr_reference": (
            "DECISION_M5_ATR14"
        ),
        "atr_algorithm": (
            "TRUE_RANGE_ROLLING_14_SIMPLE_MEAN"
        ),
        "profit_atr": 1.25,
        "max_adverse_atr": 0.75,
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
        _maturer.HORIZON_SEMANTICS
        ==
        "NEXT_12_COMPLETED_M5_ROWS_AFTER_DECISION_ROW",
        "MATURATION_HORIZON_SEMANTICS_MISMATCH",
    )

    require(
        _maturer.OUTCOME_MATURATION_AUTHORIZED
        is True,
        "OUTCOME_MATURATION_NOT_AUTHORIZED",
    )

    require(
        _maturer.PERFORMANCE_EVALUATION_AUTHORIZED
        is False,
        "PERFORMANCE_EVALUATION_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _maturer.PNL_EVALUATION_AUTHORIZED
        is False,
        "PNL_EVALUATION_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _maturer.LIVE_AUTHORIZED
        is False,
        "LIVE_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _maturer.EXECUTION_AUTHORIZED
        is False,
        "EXECUTION_UNEXPECTEDLY_AUTHORIZED",
    )

    return {
        "status": "PASS",
        "maturation_version": (
            _maturer.MATURATION_VERSION
        ),
        "outcome_contract_fingerprint_sha256": (
            _contract.compute_contract_fingerprint()
        ),
        "base_timeframe": (
            _maturer.EXPECTED_BASE_TIMEFRAME
        ),
        "horizon_bars": (
            _maturer.EXPECTED_HORIZON_BARS
        ),
        "horizon_semantics": (
            _maturer.HORIZON_SEMANTICS
        ),
        "profit_atr": (
            _maturer.EXPECTED_PROFIT_ATR
        ),
        "max_adverse_atr": (
            _maturer.EXPECTED_MAX_ADVERSE_ATR
        ),
    }


# =============================================================================
# Static Safety
# =============================================================================

def static_safety_audit() -> dict[str, Any]:

    files = [
        REPO_ROOT
        /
        MATURER_REL_PATH,

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
# Tests
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
            MATURER_TEST_REL_PATH,
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
# Gate
# =============================================================================

def run_gate() -> dict[str, Any]:

    observation_ledger_hash_before = (
        optional_sha256(
            OBSERVATION_LEDGER_PATH
        )
    )

    repository = (
        verify_repository_authority()
    )

    source_semantics = (
        verify_source_semantics()
    )

    runtime_authority = (
        verify_runtime_authority()
    )

    static_safety = (
        static_safety_audit()
    )

    tests = (
        run_targeted_tests()
    )

    observation_ledger_hash_after = (
        optional_sha256(
            OBSERVATION_LEDGER_PATH
        )
    )

    require(
        observation_ledger_hash_before
        ==
        observation_ledger_hash_after,
        "OBSERVATION_LEDGER_CHANGED",
    )

    artifact_hashes: dict[
        str,
        str,
    ] = {}

    for relative_path in (
        MATURER_REL_PATH,
        MATURER_TEST_REL_PATH,
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
            "Gate 15D-C-A — Frozen "
            "Forward Outcome Maturation Authority"
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

        "source_semantics": (
            source_semantics
        ),

        "runtime_authority": (
            runtime_authority
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

        "observation_ledger": {
            "sha256_before": (
                observation_ledger_hash_before
            ),
            "sha256_after": (
                observation_ledger_hash_after
            ),
            "unchanged": True,
        },

        "maturation_semantics_frozen": True,

        "genuine_forward_observation_matured": False,

        "outcome_ledger_created": False,

        "outcome_ledger_mutated": False,

        "forward_performance_evaluated": False,

        "accuracy_evaluated": False,

        "win_rate_evaluated": False,

        "pnl_evaluated": False,

        "return_evaluated": False,

        "drawdown_evaluated": False,

        "mt5_initialized": False,

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

        authority = evidence[
            "runtime_authority"
        ]

        print(
            "GATE_15D_C_A_STATUS=PASS"
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
            "BASE_TIMEFRAME="
            +
            str(
                authority[
                    "base_timeframe"
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
            "PROFIT_ATR="
            +
            str(
                authority[
                    "profit_atr"
                ]
            )
        )

        print(
            "MAX_ADVERSE_ATR="
            +
            str(
                authority[
                    "max_adverse_atr"
                ]
            )
        )

        print(
            "MATURATION_SEMANTICS_FROZEN=true"
        )

        print(
            "GENUINE_FORWARD_OBSERVATION_MATURED=false"
        )

        print(
            "OUTCOME_LEDGER_CREATED=false"
        )

        print(
            "FORWARD_PERFORMANCE_EVALUATED=false"
        )

        print(
            "MT5_INITIALIZED=false"
        )

        print(
            "OBSERVATION_LEDGER_UNCHANGED=true"
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
            "GATE_15D_C_A_STATUS=FAIL"
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