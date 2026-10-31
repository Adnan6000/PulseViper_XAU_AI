"""
===============================================================================
Module      : run_xauusd_gate_15c_forward_outcome_contract_evidence.py
Project     : PulseViper XAU AI
Purpose     : Gate 15C — Frozen Forward Outcome Contract Evidence
===============================================================================

OFFLINE ONLY.

This runner proves that the frozen C04 forward outcome definition has been
predefined before any forward-performance evaluation.

It does NOT:
- initialize MT5
- acquire new forward data
- mutate the shadow ledger
- evaluate any matured observation
- calculate accuracy, win rate, PnL, return, or drawdown
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

if str(
    REPO_ROOT
) not in sys.path:
    sys.path.insert(
        0,
        str(
            REPO_ROOT
        ),
    )


# =============================================================================
# Authorities
# =============================================================================

GATE_15B_B_ACCEPTED_BASELINE: str = (
    "811202d429165c89e4424b944ceaffb18b6d6f65"
)

GATE_ID: str = (
    "GATE_15C_FROZEN_FORWARD_OUTCOME_CONTRACT"
)

SCHEMA_VERSION: str = "1.0.0"


CONTRACT_REL_PATH: str = (
    "02_AI/Models/"
    "frozen_c04_forward_outcome_contract.py"
)

TEST_REL_PATH: str = (
    "04_Testing/production_portability/"
    "test_frozen_c04_forward_outcome_contract.py"
)

RUNNER_REL_PATH: str = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15c_forward_outcome_contract_evidence.py"
)

EVIDENCE_REL_PATH: str = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15c_forward_outcome_contract_evidence.json"
)

EVIDENCE_PATH: Path = (
    REPO_ROOT
    /
    EVIDENCE_REL_PATH
)

LEDGER_PATH: Path = (
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
    (
        "04_Testing/research/portable_331/train/"
        "design_xauusd_portable_331_train_model_research_protocol.py"
    ),
)


ALLOWED_GATE_15C_PATHS: frozenset[str] = frozenset(
    {
        CONTRACT_REL_PATH,
        TEST_REL_PATH,
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


FORBIDDEN_DEPENDENCIES: frozenset[str] = frozenset(
    {
        "MetaTrader5",
        "RiskEngine",
        "trade_ready",
        "broker_aware_risk_engine",
        "account_protection_guard",
    }
)


# =============================================================================
# Contract Module
# =============================================================================

_contract: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_contract"
)


# =============================================================================
# Helpers
# =============================================================================

class Gate15CError(
    RuntimeError
):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:
    if not condition:
        raise Gate15CError(
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
    process = git_process(
        *args
    )

    require(
        process.returncode
        == 0,
        (
            "GIT_COMMAND_FAILED:"
            + " ".join(
                args
            )
            + ":"
            + process.stderr.strip()
        ),
    )

    return process.stdout.rstrip(
        "\r\n"
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


def optional_file_sha256(
    path: Path,
) -> str | None:
    if not path.is_file():
        return None

    return sha256_file(
        path
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
        + ".tmp"
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

def parse_status_paths() -> set[str]:
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
        == 0,
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
        GATE_15B_B_ACCEPTED_BASELINE,
        head,
    )

    require(
        ancestor.returncode
        == 0,
        "GATE_15B_B_BASELINE_NOT_ANCESTOR",
    )

    committed_since_baseline = {
        normalize_path(
            path
        )
        for path
        in git_output(
            "diff",
            "--name-only",
            (
                f"{GATE_15B_B_ACCEPTED_BASELINE}"
                f"..{head}"
            ),
        ).splitlines()
        if path.strip()
    }

    unexpected_committed = (
        committed_since_baseline
        -
        set(
            ALLOWED_GATE_15C_PATHS
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
        parse_status_paths()
    )

    unexpected_local = (
        local_paths
        -
        set(
            ALLOWED_GATE_15C_PATHS
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
        "gate_15b_b_baseline": (
            GATE_15B_B_ACCEPTED_BASELINE
        ),
        "gate_15b_b_baseline_is_ancestor": True,
        "committed_since_baseline": sorted(
            committed_since_baseline
        ),
        "local_gate_15c_paths": sorted(
            local_paths
        ),
        "unexpected_committed_paths": [],
        "unexpected_local_paths": [],
    }


# =============================================================================
# Source Authority Verification
# =============================================================================

def verify_source_authorities() -> dict[str, Any]:
    hashes: dict[
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

    builder_text = (
        REPO_ROOT
        /
        SOURCE_AUTHORITY_PATHS[
            0
        ]
    ).read_text(
        encoding="utf-8"
    )

    relabeler_text = (
        REPO_ROOT
        /
        SOURCE_AUTHORITY_PATHS[
            1
        ]
    ).read_text(
        encoding="utf-8"
    )

    protocol_text = (
        REPO_ROOT
        /
        SOURCE_AUTHORITY_PATHS[
            2
        ]
    ).read_text(
        encoding="utf-8"
    )

    builder_requirements = (
        'base_timeframe: str = "M5"',
        "horizon_bars: int = 12",
        'featured_frame[\n                "atr14"\n            ]',
        "index\n                +\n                1",
        "horizon_bars\n                +\n                1",
    )

    for token in builder_requirements:
        require(
            token
            in builder_text,
            (
                "TRAINING_MATRIX_SOURCE_"
                "SEMANTIC_TOKEN_MISSING:"
                f"{token}"
            ),
        )

    relabeler_requirements = (
        "CLEAN_DIRECTIONAL_EXCURSION_V2",
        "up >= profit",
        "down <= adverse",
        "down >= profit",
        "up <= adverse",
        "NO_CLEAN_DIRECTIONAL_EXCURSION",
    )

    for token in relabeler_requirements:
        require(
            token
            in relabeler_text,
            (
                "TARGET_RELABELER_SOURCE_"
                "SEMANTIC_TOKEN_MISSING:"
                f"{token}"
            ),
        )

    protocol_requirements = (
        "TARGET_HORIZON_BARS = 12",
        "purge_rows_before_each_validation",
    )

    for token in protocol_requirements:
        require(
            token
            in protocol_text,
            (
                "RESEARCH_PROTOCOL_SOURCE_"
                "SEMANTIC_TOKEN_MISSING:"
                f"{token}"
            ),
        )

    return {
        "status": "PASS",
        "source_authority_hashes": (
            hashes
        ),
        "base_timeframe_verified": (
            "M5"
        ),
        "target_horizon_bars_verified": 12,
        "target_contract_verified": (
            "CLEAN_DIRECTIONAL_EXCURSION_V2"
        ),
        "profit_atr_verified": 1.25,
        "max_adverse_atr_verified": 0.75,
    }


# =============================================================================
# Static Safety
# =============================================================================

def static_safety_audit() -> dict[str, Any]:
    paths = (
        REPO_ROOT
        /
        CONTRACT_REL_PATH,
        REPO_ROOT
        /
        RUNNER_REL_PATH,
    )

    violations: list[
        dict[str, Any]
    ] = []

    for path in paths:

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
                    if (
                        alias.name
                        in FORBIDDEN_DEPENDENCIES
                    ):
                        violations.append(
                            {
                                "file": path.name,
                                "type": "import",
                                "symbol": (
                                    alias.name
                                ),
                            }
                        )

            elif isinstance(
                node,
                ast.ImportFrom,
            ):
                module = (
                    node.module
                    or ""
                )

                if any(
                    dependency
                    in module
                    for dependency
                    in FORBIDDEN_DEPENDENCIES
                ):
                    violations.append(
                        {
                            "file": path.name,
                            "type": "import_from",
                            "symbol": module,
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
                    symbol = function.id

                elif isinstance(
                    function,
                    ast.Attribute,
                ):
                    symbol = function.attr

                else:
                    symbol = ""

                if (
                    symbol
                    in FORBIDDEN_BROKER_CALLS
                ):
                    violations.append(
                        {
                            "file": path.name,
                            "type": "call",
                            "symbol": symbol,
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
            for path in paths
        ],
        "violation_count": 0,
        "violations": [],
    }


# =============================================================================
# Contract Verification
# =============================================================================

def verify_contract() -> dict[str, Any]:
    require(
        bool(
            _contract.verify_frozen_contract()
        ),
        "FROZEN_CONTRACT_VERIFICATION_FAILED",
    )

    require(
        _contract.CONTRACT_STATUS
        ==
        "DEFINED_NOT_YET_MATURED_OR_EVALUATED",
        "GATE_15C_CONTRACT_STATUS_MISMATCH",
    )

    require(
        _contract.MODEL_TARGET_CONTRACT
        ==
        "CLEAN_DIRECTIONAL_EXCURSION_V2",
        "MODEL_TARGET_CONTRACT_MISMATCH",
    )

    require(
        _contract.BASE_TIMEFRAME
        ==
        "M5",
        "BASE_TIMEFRAME_MISMATCH",
    )

    require(
        _contract.HORIZON_BARS
        ==
        12,
        "HORIZON_BARS_MISMATCH",
    )

    require(
        _contract.HORIZON_MINUTES
        ==
        60,
        "HORIZON_MINUTES_MISMATCH",
    )

    require(
        _contract.PROFIT_ATR
        ==
        1.25,
        "PROFIT_ATR_MISMATCH",
    )

    require(
        _contract.MAX_ADVERSE_ATR
        ==
        0.75,
        "MAX_ADVERSE_ATR_MISMATCH",
    )

    require(
        _contract.CLASS_MAPPING
        ==
        {
            "SHORT": -1,
            "NO_TRADE": 0,
            "LONG": 1,
        },
        "CLASS_MAPPING_MISMATCH",
    )

    require(
        _contract.PERFORMANCE_EVALUATION_AUTHORIZED
        is False,
        "PERFORMANCE_EVALUATION_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _contract.PNL_EVALUATION_AUTHORIZED
        is False,
        "PNL_EVALUATION_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _contract.LIVE_AUTHORIZED
        is False,
        "LIVE_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _contract.EXECUTION_AUTHORIZED
        is False,
        "EXECUTION_UNEXPECTEDLY_AUTHORIZED",
    )

    return {
        "status": "PASS",
        "contract_version": (
            _contract.CONTRACT_VERSION
        ),
        "contract_status": (
            _contract.CONTRACT_STATUS
        ),
        "contract_fingerprint_sha256": (
            _contract.compute_contract_fingerprint()
        ),
        "target_contract": (
            _contract.MODEL_TARGET_CONTRACT
        ),
        "base_timeframe": (
            _contract.BASE_TIMEFRAME
        ),
        "horizon_bars": (
            _contract.HORIZON_BARS
        ),
        "horizon_minutes": (
            _contract.HORIZON_MINUTES
        ),
        "reference_price": (
            _contract.REFERENCE_PRICE
        ),
        "reference_volatility": (
            _contract.REFERENCE_VOLATILITY
        ),
        "profit_atr": (
            _contract.PROFIT_ATR
        ),
        "max_adverse_atr": (
            _contract.MAX_ADVERSE_ATR
        ),
        "class_mapping": dict(
            _contract.CLASS_MAPPING
        ),
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
            TEST_REL_PATH,
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
            process.stdout[-1500:]
            +
            process.stderr[-1500:]
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
    ledger_hash_before = (
        optional_file_sha256(
            LEDGER_PATH
        )
    )

    repository = (
        verify_repository_authority()
    )

    sources = (
        verify_source_authorities()
    )

    safety = (
        static_safety_audit()
    )

    contract = (
        verify_contract()
    )

    tests = (
        run_targeted_tests()
    )

    ledger_hash_after = (
        optional_file_sha256(
            LEDGER_PATH
        )
    )

    require(
        ledger_hash_before
        ==
        ledger_hash_after,
        "SHADOW_LEDGER_CHANGED_DURING_GATE_15C",
    )

    artifact_hashes: dict[
        str,
        str,
    ] = {}

    for relative_path in (
        CONTRACT_REL_PATH,
        TEST_REL_PATH,
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
                "GATE_15C_ARTIFACT_MISSING:"
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
            "Gate 15C — Frozen C04 "
            "Forward Outcome Contract"
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
        "source_authority": (
            sources
        ),
        "contract": (
            contract
        ),
        "targeted_tests": (
            tests
        ),
        "static_safety": (
            safety
        ),
        "candidate_artifact_hashes": (
            artifact_hashes
        ),
        "shadow_ledger": {
            "sha256_before": (
                ledger_hash_before
            ),
            "sha256_after": (
                ledger_hash_after
            ),
            "unchanged": True,
        },
        "forward_outcome_definition_predefined": True,
        "forward_outcomes_matured": False,
        "forward_outcomes_evaluated": False,
        "forward_performance_evaluated": False,
        "accuracy_evaluated": False,
        "win_rate_evaluated": False,
        "pnl_evaluated": False,
        "return_evaluated": False,
        "drawdown_evaluated": False,
        "transaction_cost_evaluated": False,
        "new_forward_observation_acquired": False,
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

        print(
            "GATE_15C_STATUS=PASS"
        )

        print(
            "CONTRACT_VERSION="
            +
            str(
                evidence[
                    "contract"
                ][
                    "contract_version"
                ]
            )
        )

        print(
            "CONTRACT_FINGERPRINT_SHA256="
            +
            str(
                evidence[
                    "contract"
                ][
                    "contract_fingerprint_sha256"
                ]
            )
        )

        print(
            "MODEL_TARGET_CONTRACT="
            +
            str(
                evidence[
                    "contract"
                ][
                    "target_contract"
                ]
            )
        )

        print(
            "BASE_TIMEFRAME=M5"
        )

        print(
            "HORIZON_BARS=12"
        )

        print(
            "HORIZON_MINUTES=60"
        )

        print(
            "PROFIT_ATR=1.25"
        )

        print(
            "MAX_ADVERSE_ATR=0.75"
        )

        print(
            "FORWARD_OUTCOME_DEFINITION_PREDEFINED=true"
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
            "MT5_INITIALIZED=false"
        )

        print(
            "SHADOW_LEDGER_UNCHANGED=true"
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
            "GATE_15C_STATUS=FAIL"
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
            "FORWARD_OUTCOMES_EVALUATED=false"
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