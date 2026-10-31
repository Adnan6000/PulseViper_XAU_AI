"""
===============================================================================
Module      : run_xauusd_gate_15d_c_b2a_forward_outcome_anchor_evidence.py
Project     : PulseViper XAU AI
Purpose     : Gate 15D-C-B2A — Prospective Forward Outcome Anchor Evidence
===============================================================================

OFFLINE ONLY.

This gate freezes the prospective outcome-anchor authority required before any
new genuine forward observation can become formally scoreable.

Frozen anchor semantics:
- raw M5 timestamp = candle OPEN time
- decision_time = completed M5 candle close / availability time
- decision_bar_open_time = decision_time - 5 minutes
- decision_m5_close = completed decision candle CLOSE
- decision_m5_atr14 = completed decision candle ATR14
- anchor must be derived from the SAME acquisition snapshot used by observation
- source_snapshot_id must cryptographically match that snapshot
- acquisition snapshot must terminate exactly at the decision candle
- no future M5 outcome row may be present at anchor capture time

Anchor storage:
- separate append-only JSONL runtime ledger
- local / gitignored under 01_Data/Shadow
- locked append
- flush + fsync
- idempotent exact duplicate supported
- conflicting anchor fails closed
- corrupt ledger fails closed

This runner does NOT:
- initialize MT5
- acquire genuine market data
- create a genuine runtime anchor
- append the production anchor ledger
- mutate the TRUE_FORWARD observation ledger
- mutate the forward outcome ledger
- mature any genuine observation
- evaluate performance / PnL / accuracy / win rate / return / drawdown
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
# Gate Authority
# =============================================================================

GATE_ID: str = (
    "GATE_15D_C_B2A_PROSPECTIVE_FORWARD_OUTCOME_ANCHOR"
)

SCHEMA_VERSION: str = "1.0.0"

BASE_REPOSITORY_AUTHORITY_COMMIT: str = (
    "d6ea813c407d68b2ecd12e56cf9eeae8a6f95ffb"
)

ANCHOR_REL_PATH: str = (
    "02_AI/Models/"
    "frozen_c04_forward_outcome_anchor.py"
)

ANCHOR_TEST_REL_PATH: str = (
    "04_Testing/production_portability/"
    "test_frozen_c04_forward_outcome_anchor.py"
)

RUNNER_REL_PATH: str = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2a_"
    "forward_outcome_anchor_evidence.py"
)

EVIDENCE_REL_PATH: str = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2a_"
    "forward_outcome_anchor_evidence.json"
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

OUTCOME_LEDGER_PATH: Path = (
    REPO_ROOT
    /
    "01_Data"
    /
    "Shadow"
    /
    "xauusd_frozen_c04_forward_outcomes.jsonl"
)

ANCHOR_LEDGER_PATH: Path = (
    REPO_ROOT
    /
    "01_Data"
    /
    "Shadow"
    /
    "xauusd_frozen_c04_forward_outcome_anchors.jsonl"
)

MATURER_REL_PATH: str = (
    "02_AI/Models/"
    "frozen_c04_forward_outcome_maturer.py"
)

OUTCOME_LEDGER_REL_PATH: str = (
    "02_AI/Models/"
    "frozen_c04_forward_outcome_ledger.py"
)

ACQUISITION_REL_PATH: str = (
    "02_AI/Adapters/"
    "mt5_read_only_forward_acquisition_adapter.py"
)

FEATURE_GENERATOR_REL_PATH: str = (
    "02_AI/Features/"
    "feature_generator.py"
)

ELIGIBILITY_REL_PATH: str = (
    "02_AI/Models/"
    "frozen_c04_forward_outcome_eligibility.py"
)

CONTRACT_REL_PATH: str = (
    "02_AI/Models/"
    "frozen_c04_forward_outcome_contract.py"
)


ALLOWED_LOCAL_PATHS: frozenset[str] = frozenset(
    {
        ANCHOR_REL_PATH,
        ANCHOR_TEST_REL_PATH,
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
# Runtime Authorities
# =============================================================================

_anchor: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_anchor"
)

_maturer: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_maturer"
)

_outcome_ledger: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_ledger"
)

_contract: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_contract"
)

_eligibility: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_eligibility"
)


# =============================================================================
# Errors / Utilities
# =============================================================================

class Gate15DCB2AError(
    RuntimeError
):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:

        raise Gate15DCB2AError(
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

    require(
        head
        ==
        BASE_REPOSITORY_AUTHORITY_COMMIT,
        (
            "UNEXPECTED_BASE_HEAD:"
            f"{head}:expected="
            f"{BASE_REPOSITORY_AUTHORITY_COMMIT}"
        ),
    )

    local_paths = (
        status_paths()
    )

    unexpected_local = (
        local_paths
        -
        set(
            ALLOWED_LOCAL_PATHS
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

        "base_repository_authority_commit": (
            BASE_REPOSITORY_AUTHORITY_COMMIT
        ),

        "local_gate_paths": sorted(
            local_paths
        ),

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
        "OUTCOME_CONTRACT_INVALID",
    )

    require(
        bool(
            _eligibility.verify_authorities()
        ),
        "ELIGIBILITY_AUTHORITY_INVALID",
    )

    require(
        bool(
            _maturer.verify_authorities()
        ),
        "MATURATION_AUTHORITY_INVALID",
    )

    require(
        bool(
            _outcome_ledger.verify_authorities()
        ),
        "OUTCOME_LEDGER_AUTHORITY_INVALID",
    )

    require(
        bool(
            _anchor.verify_authorities()
        ),
        "ANCHOR_AUTHORITY_INVALID",
    )

    require(
        _anchor.ANCHOR_VERSION
        ==
        "FROZEN_C04_FORWARD_OUTCOME_ANCHOR_V1",
        "ANCHOR_VERSION_MISMATCH",
    )

    require(
        _anchor.ANCHOR_LEDGER_VERSION
        ==
        "FROZEN_C04_FORWARD_OUTCOME_ANCHOR_LEDGER_V1",
        "ANCHOR_LEDGER_VERSION_MISMATCH",
    )

    require(
        _anchor.EXPECTED_ACQUISITION_AUTHORITY
        ==
        "MT5ReadOnlyForwardAcquisitionAdapter:2.1.0",
        "ACQUISITION_AUTHORITY_MISMATCH",
    )

    require(
        _anchor.EXPECTED_CONTRACT_FINGERPRINT_SHA256
        ==
        _contract.compute_contract_fingerprint(),
        "ANCHOR_CONTRACT_FINGERPRINT_MISMATCH",
    )

    require(
        _anchor.EXPECTED_FEATURE_COLUMNS_SHA256
        ==
        (
            "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
        ),
        "ANCHOR_FEATURE_AUTHORITY_MISMATCH",
    )

    require(
        _anchor.EXPECTED_MODEL_SHA256
        ==
        (
            "48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769"
        ),
        "ANCHOR_MODEL_AUTHORITY_MISMATCH",
    )

    require(
        _anchor.DECISION_BAR_SEMANTICS
        ==
        _maturer.DECISION_BAR_SEMANTICS,
        "ANCHOR_MATURER_DECISION_SEMANTICS_MISMATCH",
    )

    require(
        _anchor.ENTRY_REFERENCE
        ==
        _maturer.ENTRY_REFERENCE,
        "ANCHOR_MATURER_ENTRY_REFERENCE_MISMATCH",
    )

    require(
        _anchor.ATR_REFERENCE
        ==
        _maturer.ATR_REFERENCE,
        "ANCHOR_MATURER_ATR_REFERENCE_MISMATCH",
    )

    require(
        _anchor.FORMAL_MATURATION_REQUIRES_ANCHOR
        is True,
        "FORMAL_MATURATION_ANCHOR_REQUIREMENT_NOT_FROZEN",
    )

    require(
        _anchor.PROSPECTIVE_CAPTURE_POLICY
        ==
        "SAME_ACQUISITION_SNAPSHOT_NO_FUTURE_M5_ROWS",
        "PROSPECTIVE_CAPTURE_POLICY_MISMATCH",
    )

    require(
        _anchor.PERFORMANCE_EVALUATION_AUTHORIZED
        is False,
        "ANCHOR_PERFORMANCE_AUTHORIZATION_VIOLATION",
    )

    require(
        _anchor.PNL_EVALUATION_AUTHORIZED
        is False,
        "ANCHOR_PNL_AUTHORIZATION_VIOLATION",
    )

    require(
        _anchor.LIVE_AUTHORIZED
        is False,
        "ANCHOR_LIVE_AUTHORIZATION_VIOLATION",
    )

    require(
        _anchor.EXECUTION_AUTHORIZED
        is False,
        "ANCHOR_EXECUTION_AUTHORIZATION_VIOLATION",
    )

    return {
        "status": "PASS",

        "anchor_version": (
            _anchor.ANCHOR_VERSION
        ),

        "anchor_ledger_version": (
            _anchor.ANCHOR_LEDGER_VERSION
        ),

        "acquisition_authority": (
            _anchor.EXPECTED_ACQUISITION_AUTHORITY
        ),

        "contract_fingerprint_sha256": (
            _anchor.EXPECTED_CONTRACT_FINGERPRINT_SHA256
        ),

        "feature_columns_sha256": (
            _anchor.EXPECTED_FEATURE_COLUMNS_SHA256
        ),

        "model_sha256": (
            _anchor.EXPECTED_MODEL_SHA256
        ),

        "decision_bar_semantics": (
            _anchor.DECISION_BAR_SEMANTICS
        ),

        "entry_reference": (
            _anchor.ENTRY_REFERENCE
        ),

        "atr_reference": (
            _anchor.ATR_REFERENCE
        ),

        "prospective_capture_policy": (
            _anchor.PROSPECTIVE_CAPTURE_POLICY
        ),

        "formal_maturation_requires_anchor": True,

        "performance_evaluation_authorized": False,

        "pnl_evaluation_authorized": False,

        "live_authorized": False,

        "execution_authorized": False,
    }


# =============================================================================
# Static Safety Audit
# =============================================================================

def static_safety_audit() -> dict[str, Any]:

    files = [
        REPO_ROOT
        /
        ANCHOR_REL_PATH,

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
# Source Authority Hashes
# =============================================================================

def source_authority_hashes() -> dict[str, str]:

    paths = (
        MATURER_REL_PATH,
        OUTCOME_LEDGER_REL_PATH,
        ACQUISITION_REL_PATH,
        FEATURE_GENERATOR_REL_PATH,
        ELIGIBILITY_REL_PATH,
        CONTRACT_REL_PATH,
    )

    result: dict[
        str,
        str,
    ] = {}

    for relative_path in paths:

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

        result[
            relative_path
        ] = sha256_file(
            path
        )

    return result


# =============================================================================
# Targeted Tests
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

            (
                "04_Testing/production_portability/"
                "test_frozen_c04_forward_outcome_ledger.py"
            ),

            ANCHOR_TEST_REL_PATH,

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

        "stdout_tail": (
            process.stdout[
                -1500:
            ]
        ),
    }


# =============================================================================
# Gate Execution
# =============================================================================

def run_gate() -> dict[str, Any]:

    observation_hash_before = (
        optional_sha256(
            OBSERVATION_LEDGER_PATH
        )
    )

    outcome_exists_before = (
        OUTCOME_LEDGER_PATH.exists()
    )

    outcome_hash_before = (
        optional_sha256(
            OUTCOME_LEDGER_PATH
        )
    )

    anchor_exists_before = (
        ANCHOR_LEDGER_PATH.exists()
    )

    anchor_hash_before = (
        optional_sha256(
            ANCHOR_LEDGER_PATH
        )
    )

    repository = (
        verify_repository_authority()
    )

    runtime_authority = (
        verify_runtime_authority()
    )

    static_safety = (
        static_safety_audit()
    )

    authority_hashes = (
        source_authority_hashes()
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
        OUTCOME_LEDGER_PATH.exists()
    )

    outcome_hash_after = (
        optional_sha256(
            OUTCOME_LEDGER_PATH
        )
    )

    anchor_exists_after = (
        ANCHOR_LEDGER_PATH.exists()
    )

    anchor_hash_after = (
        optional_sha256(
            ANCHOR_LEDGER_PATH
        )
    )

    require(
        observation_hash_before
        ==
        observation_hash_after,
        "OBSERVATION_LEDGER_CHANGED",
    )

    require(
        outcome_exists_before
        ==
        outcome_exists_after,
        "OUTCOME_LEDGER_EXISTENCE_CHANGED",
    )

    require(
        outcome_hash_before
        ==
        outcome_hash_after,
        "OUTCOME_LEDGER_CHANGED",
    )

    require(
        anchor_exists_before
        ==
        anchor_exists_after,
        "ANCHOR_LEDGER_EXISTENCE_CHANGED",
    )

    require(
        anchor_hash_before
        ==
        anchor_hash_after,
        "ANCHOR_LEDGER_CHANGED",
    )

    candidate_artifact_hashes: dict[
        str,
        str,
    ] = {}

    for relative_path in (
        ANCHOR_REL_PATH,
        ANCHOR_TEST_REL_PATH,
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
                "CANDIDATE_ARTIFACT_MISSING:"
                f"{relative_path}"
            ),
        )

        candidate_artifact_hashes[
            relative_path
        ] = sha256_file(
            path
        )

    evidence: dict[
        str,
        Any,
    ] = {
        "gate": (
            "Gate 15D-C-B2A — "
            "Prospective Forward Outcome Anchor Authority"
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
            static_safety
        ),

        "source_authority_hashes": (
            authority_hashes
        ),

        "targeted_tests": (
            tests
        ),

        "candidate_artifact_hashes": (
            candidate_artifact_hashes
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

        "runtime_anchor_ledger": {
            "path": (
                "01_Data/Shadow/"
                "xauusd_frozen_c04_forward_outcome_anchors.jsonl"
            ),

            "existed_before": (
                anchor_exists_before
            ),

            "exists_after": (
                anchor_exists_after
            ),

            "sha256_before": (
                anchor_hash_before
            ),

            "sha256_after": (
                anchor_hash_after
            ),

            "unchanged": True,
        },

        "same_snapshot_anchor_required": True,

        "source_snapshot_hash_match_required": True,

        "decision_snapshot_must_end_at_decision_bar": True,

        "future_m5_rows_forbidden_at_anchor_capture": True,

        "decision_m5_close_frozen_prospectively": True,

        "decision_m5_atr14_frozen_prospectively": True,

        "formal_maturation_requires_anchor": True,

        "append_only_anchor_ledger_authority_frozen": True,

        "locked_append_required": True,

        "flush_and_fsync_required": True,

        "idempotent_duplicate_supported": True,

        "conflicting_anchor_fails_closed": True,

        "corrupted_anchor_ledger_fails_closed": True,

        "genuine_forward_observation_captured": False,

        "genuine_anchor_appended": False,

        "genuine_forward_observation_matured": False,

        "outcome_record_appended": False,

        "mt5_initialized": False,

        "market_data_acquired": False,

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


# =============================================================================
# CLI
# =============================================================================

def main() -> int:

    try:

        evidence = (
            run_gate()
        )

        authority = (
            evidence[
                "runtime_authority"
            ]
        )

        print(
            "GATE_15D_C_B2A_STATUS=PASS"
        )

        print(
            "ANCHOR_VERSION="
            +
            str(
                authority[
                    "anchor_version"
                ]
            )
        )

        print(
            "ANCHOR_LEDGER_VERSION="
            +
            str(
                authority[
                    "anchor_ledger_version"
                ]
            )
        )

        print(
            "ACQUISITION_AUTHORITY="
            +
            str(
                authority[
                    "acquisition_authority"
                ]
            )
        )

        print(
            "DECISION_BAR_SEMANTICS="
            +
            str(
                authority[
                    "decision_bar_semantics"
                ]
            )
        )

        print(
            "ENTRY_REFERENCE="
            +
            str(
                authority[
                    "entry_reference"
                ]
            )
        )

        print(
            "ATR_REFERENCE="
            +
            str(
                authority[
                    "atr_reference"
                ]
            )
        )

        print(
            "PROSPECTIVE_CAPTURE_POLICY="
            +
            str(
                authority[
                    "prospective_capture_policy"
                ]
            )
        )

        print(
            "FORMAL_MATURATION_REQUIRES_ANCHOR=true"
        )

        print(
            "APPEND_ONLY_ANCHOR_LEDGER_AUTHORITY_FROZEN=true"
        )

        print(
            "SAME_SNAPSHOT_ANCHOR_REQUIRED=true"
        )

        print(
            "FUTURE_M5_ROWS_FORBIDDEN_AT_ANCHOR_CAPTURE=true"
        )

        print(
            "GENUINE_FORWARD_OBSERVATION_CAPTURED=false"
        )

        print(
            "GENUINE_ANCHOR_APPENDED=false"
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
            "MARKET_DATA_ACQUIRED=false"
        )

        print(
            "OBSERVATION_LEDGER_UNCHANGED=true"
        )

        print(
            "OUTCOME_LEDGER_UNCHANGED=true"
        )

        print(
            "ANCHOR_LEDGER_UNCHANGED=true"
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
            "GATE_15D_C_B2A_STATUS=FAIL"
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
            "GENUINE_FORWARD_OBSERVATION_CAPTURED=false"
        )

        print(
            "GENUINE_ANCHOR_APPENDED=false"
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