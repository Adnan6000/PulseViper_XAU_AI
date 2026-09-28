"""
===============================================================================
Module      : run_xauusd_gate_15d_c_b2bc_anchor_required_maturation_ledger_v2_evidence.py
Project     : PulseViper XAU AI
Purpose     : Gate 15D-C-B2B/B2C — Anchor-Required Maturation + Ledger V2
===============================================================================

OFFLINE ONLY.

This gate supersedes the post-hoc decision-reference reconstruction path.

B2B:
- Frozen maturer V2 requires a validated prospective anchor.
- Entry close comes ONLY from the prospective anchor.
- Decision ATR14 comes ONLY from the prospective anchor.
- Later completed M5 data supplies only the decision-row location and the
  next 12 completed future M5 rows.
- Reconstructing entry close or ATR14 from later data is forbidden.

B2C:
- Frozen outcome ledger V2 accepts only Maturer V2 outcomes.
- Every stored outcome must carry:
    source observation fingerprint
    source anchor fingerprint
    source anchor version
    anchor-only entry reference
    anchor-only ATR reference
    post-hoc reconstruction forbidden policy
- Append-only / locked / flush + fsync behavior remains required.

CRITICAL PROTOCOL BOUNDARY:
- Existing 2026-09-28T11:45Z genuine observation did NOT receive a prospective
  anchor at acquisition time.
- It remains acquisition/prospective-timing evidence only.
- It is permanently excluded from formal scoring under this protocol.
- This runner does NOT retroactively anchor or mature it.

This runner does NOT:
- initialize MT5
- acquire market data
- create a genuine prospective anchor
- append observation ledger
- append anchor ledger
- append outcome ledger
- mature any genuine forward observation
- calculate aggregate performance
- calculate accuracy / win rate / PnL / return / drawdown
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


# =============================================================================
# Gate Authority
# =============================================================================

GATE_ID: str = (
    "GATE_15D_C_B2BC_ANCHOR_REQUIRED_MATURATION_LEDGER_V2"
)

SCHEMA_VERSION: str = (
    "2.0.0"
)

BASE_REPOSITORY_AUTHORITY_COMMIT: str = (
    "3279038818c92b6e11bdbcbe175fd6ffc4878587"
)

SUPERSEDES_MATURATION_VERSION: str = (
    "FROZEN_C04_FORWARD_OUTCOME_MATURER_V1_1"
)

SUPERSEDES_OUTCOME_LEDGER_VERSION: str = (
    "FROZEN_C04_FORWARD_OUTCOME_LEDGER_V1_1"
)

EXPECTED_MATURATION_VERSION: str = (
    "FROZEN_C04_FORWARD_OUTCOME_MATURER_V2"
)

EXPECTED_OUTCOME_LEDGER_VERSION: str = (
    "FROZEN_C04_FORWARD_OUTCOME_LEDGER_V2"
)

EXPECTED_ANCHOR_VERSION: str = (
    "FROZEN_C04_FORWARD_OUTCOME_ANCHOR_V1"
)

EXPECTED_ANCHOR_LEDGER_VERSION: str = (
    "FROZEN_C04_FORWARD_OUTCOME_ANCHOR_LEDGER_V1"
)

EXPECTED_ENTRY_REFERENCE: str = (
    "PROSPECTIVE_ANCHOR_DECISION_M5_CLOSE"
)

EXPECTED_ATR_REFERENCE: str = (
    "PROSPECTIVE_ANCHOR_DECISION_M5_ATR14"
)

EXPECTED_ANCHOR_REQUIREMENT: str = (
    "VALIDATED_PROSPECTIVE_ANCHOR_REQUIRED"
)

EXPECTED_REFERENCE_RECONSTRUCTION_POLICY: str = (
    "POST_HOC_ENTRY_AND_ATR_RECONSTRUCTION_FORBIDDEN"
)

EXPECTED_HORIZON_SEMANTICS: str = (
    "NEXT_12_COMPLETED_M5_ROWS_AFTER_DECISION_BAR"
)

EXPECTED_DECISION_BAR_SEMANTICS: str = (
    "M5_BAR_OPEN_EQUALS_DECISION_TIME_MINUS_5_MINUTES"
)


# =============================================================================
# Paths
# =============================================================================

ANCHOR_REL_PATH: str = (
    "02_AI/Models/"
    "frozen_c04_forward_outcome_anchor.py"
)

MATURER_REL_PATH: str = (
    "02_AI/Models/"
    "frozen_c04_forward_outcome_maturer.py"
)

OUTCOME_LEDGER_REL_PATH: str = (
    "02_AI/Models/"
    "frozen_c04_forward_outcome_ledger.py"
)

MATURER_TEST_REL_PATH: str = (
    "04_Testing/production_portability/"
    "test_frozen_c04_forward_outcome_maturer.py"
)

OUTCOME_LEDGER_TEST_REL_PATH: str = (
    "04_Testing/production_portability/"
    "test_frozen_c04_forward_outcome_ledger.py"
)

ANCHOR_TEST_REL_PATH: str = (
    "04_Testing/production_portability/"
    "test_frozen_c04_forward_outcome_anchor.py"
)

RUNNER_REL_PATH: str = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2bc_"
    "anchor_required_maturation_ledger_v2_evidence.py"
)

EVIDENCE_REL_PATH: str = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2bc_"
    "anchor_required_maturation_ledger_v2_evidence.json"
)

EVIDENCE_PATH: Path = (
    REPO_ROOT
    /
    EVIDENCE_REL_PATH
)


# =============================================================================
# Runtime Ledgers
# =============================================================================

OBSERVATION_LEDGER_PATH: Path = (
    REPO_ROOT
    /
    "01_Data"
    /
    "Shadow"
    /
    "xauusd_frozen_c04_shadow_observations.jsonl"
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

OUTCOME_LEDGER_PATH: Path = (
    REPO_ROOT
    /
    "01_Data"
    /
    "Shadow"
    /
    "xauusd_frozen_c04_forward_outcomes.jsonl"
)


# =============================================================================
# Allowed Local Candidate Files
# =============================================================================

ALLOWED_LOCAL_PATHS: frozenset[str] = frozenset(
    {
        MATURER_REL_PATH,
        OUTCOME_LEDGER_REL_PATH,
        MATURER_TEST_REL_PATH,
        OUTCOME_LEDGER_TEST_REL_PATH,
        RUNNER_REL_PATH,
        EVIDENCE_REL_PATH,
    }
)


# =============================================================================
# Safety
# =============================================================================

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

_contract: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_contract"
)

_eligibility: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_eligibility"
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

class Gate15DCB2BCError(
    RuntimeError
):
    pass


# =============================================================================
# Helpers
# =============================================================================

def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:

        raise Gate15DCB2BCError(
            reason
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


def sha256_file(
    path: Path,
) -> str:

    digest = (
        hashlib.sha256()
    )

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

    return (
        digest.hexdigest()
    )


def optional_sha256(
    path: Path,
) -> str | None:

    if not path.is_file():

        return None

    return sha256_file(
        path
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

        path = (
            line[
                3:
            ]
            .strip()
        )

        if " -> " in path:

            path = (
                path.split(
                    " -> ",
                    1,
                )[1]
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

    temporary = (
        path.with_suffix(
            path.suffix
            +
            ".tmp"
        )
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
            f"{head}:"
            f"expected="
            f"{BASE_REPOSITORY_AUTHORITY_COMMIT}"
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

    return {
        "status": "PASS",

        "branch": (
            branch
        ),

        "head": (
            head
        ),

        "origin_main": (
            origin_main
        ),

        "head_equals_origin_main": True,

        "base_repository_authority_commit": (
            BASE_REPOSITORY_AUTHORITY_COMMIT
        ),

        "candidate_local_paths": (
            sorted(
                local_paths
            )
        ),

        "unexpected_local_paths": [],
    }


# =============================================================================
# Runtime Authority Verification
# =============================================================================

def verify_runtime_authorities() -> dict[str, Any]:

    require(
        bool(
            _contract.verify_frozen_contract()
        ),
        "CONTRACT_AUTHORITY_INVALID",
    )

    require(
        bool(
            _eligibility.verify_authorities()
        ),
        "ELIGIBILITY_AUTHORITY_INVALID",
    )

    require(
        bool(
            _anchor.verify_authorities()
        ),
        "ANCHOR_AUTHORITY_INVALID",
    )

    require(
        bool(
            _maturer.verify_authorities()
        ),
        "MATURER_V2_AUTHORITY_INVALID",
    )

    require(
        bool(
            _outcome_ledger.verify_authorities()
        ),
        "OUTCOME_LEDGER_V2_AUTHORITY_INVALID",
    )

    require(
        _anchor.ANCHOR_VERSION
        ==
        EXPECTED_ANCHOR_VERSION,
        "ANCHOR_VERSION_MISMATCH",
    )

    require(
        _anchor.ANCHOR_LEDGER_VERSION
        ==
        EXPECTED_ANCHOR_LEDGER_VERSION,
        "ANCHOR_LEDGER_VERSION_MISMATCH",
    )

    require(
        _maturer.MATURATION_VERSION
        ==
        EXPECTED_MATURATION_VERSION,
        "MATURATION_VERSION_MISMATCH",
    )

    require(
        _maturer.SUPERSEDES_MATURATION_VERSION
        ==
        SUPERSEDES_MATURATION_VERSION,
        "MATURATION_SUPERSESSION_MISMATCH",
    )

    require(
        _outcome_ledger.OUTCOME_LEDGER_VERSION
        ==
        EXPECTED_OUTCOME_LEDGER_VERSION,
        "OUTCOME_LEDGER_VERSION_MISMATCH",
    )

    require(
        _outcome_ledger.SUPERSEDES_OUTCOME_LEDGER_VERSION
        ==
        SUPERSEDES_OUTCOME_LEDGER_VERSION,
        "OUTCOME_LEDGER_SUPERSESSION_MISMATCH",
    )

    require(
        _outcome_ledger.EXPECTED_MATURATION_VERSION
        ==
        EXPECTED_MATURATION_VERSION,
        "LEDGER_MATURER_VERSION_MISMATCH",
    )

    require(
        _maturer.EXPECTED_ANCHOR_VERSION
        ==
        EXPECTED_ANCHOR_VERSION,
        "MATURER_ANCHOR_VERSION_MISMATCH",
    )

    require(
        _outcome_ledger.EXPECTED_ANCHOR_VERSION
        ==
        EXPECTED_ANCHOR_VERSION,
        "LEDGER_ANCHOR_VERSION_MISMATCH",
    )

    require(
        _maturer.FORMAL_MATURATION_REQUIRES_ANCHOR
        is True,
        "MATURER_DOES_NOT_REQUIRE_ANCHOR",
    )

    require(
        _maturer.ANCHOR_REQUIREMENT
        ==
        EXPECTED_ANCHOR_REQUIREMENT,
        "MATURER_ANCHOR_REQUIREMENT_MISMATCH",
    )

    require(
        _outcome_ledger.EXPECTED_ANCHOR_REQUIREMENT
        ==
        EXPECTED_ANCHOR_REQUIREMENT,
        "LEDGER_ANCHOR_REQUIREMENT_MISMATCH",
    )

    require(
        _maturer.ENTRY_REFERENCE
        ==
        EXPECTED_ENTRY_REFERENCE,
        "MATURER_ENTRY_REFERENCE_MISMATCH",
    )

    require(
        _outcome_ledger.EXPECTED_ENTRY_REFERENCE
        ==
        EXPECTED_ENTRY_REFERENCE,
        "LEDGER_ENTRY_REFERENCE_MISMATCH",
    )

    require(
        _maturer.ATR_REFERENCE
        ==
        EXPECTED_ATR_REFERENCE,
        "MATURER_ATR_REFERENCE_MISMATCH",
    )

    require(
        _outcome_ledger.EXPECTED_ATR_REFERENCE
        ==
        EXPECTED_ATR_REFERENCE,
        "LEDGER_ATR_REFERENCE_MISMATCH",
    )

    require(
        _maturer.REFERENCE_RECONSTRUCTION_POLICY
        ==
        EXPECTED_REFERENCE_RECONSTRUCTION_POLICY,
        "MATURER_RECONSTRUCTION_POLICY_MISMATCH",
    )

    require(
        _outcome_ledger.EXPECTED_REFERENCE_RECONSTRUCTION_POLICY
        ==
        EXPECTED_REFERENCE_RECONSTRUCTION_POLICY,
        "LEDGER_RECONSTRUCTION_POLICY_MISMATCH",
    )

    require(
        _maturer.HORIZON_SEMANTICS
        ==
        EXPECTED_HORIZON_SEMANTICS,
        "MATURER_HORIZON_SEMANTICS_MISMATCH",
    )

    require(
        _outcome_ledger.EXPECTED_HORIZON_SEMANTICS
        ==
        EXPECTED_HORIZON_SEMANTICS,
        "LEDGER_HORIZON_SEMANTICS_MISMATCH",
    )

    require(
        _maturer.DECISION_BAR_SEMANTICS
        ==
        EXPECTED_DECISION_BAR_SEMANTICS,
        "MATURER_DECISION_BAR_SEMANTICS_MISMATCH",
    )

    require(
        _outcome_ledger.EXPECTED_DECISION_BAR_SEMANTICS
        ==
        EXPECTED_DECISION_BAR_SEMANTICS,
        "LEDGER_DECISION_BAR_SEMANTICS_MISMATCH",
    )

    require(
        _maturer.PERFORMANCE_EVALUATION_AUTHORIZED
        is False,
        "MATURER_PERFORMANCE_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _maturer.PNL_EVALUATION_AUTHORIZED
        is False,
        "MATURER_PNL_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _maturer.LIVE_AUTHORIZED
        is False,
        "MATURER_LIVE_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _maturer.EXECUTION_AUTHORIZED
        is False,
        "MATURER_EXECUTION_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _outcome_ledger.PERFORMANCE_EVALUATION_AUTHORIZED
        is False,
        "LEDGER_PERFORMANCE_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _outcome_ledger.PNL_EVALUATION_AUTHORIZED
        is False,
        "LEDGER_PNL_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _outcome_ledger.LIVE_AUTHORIZED
        is False,
        "LEDGER_LIVE_UNEXPECTEDLY_AUTHORIZED",
    )

    require(
        _outcome_ledger.EXECUTION_AUTHORIZED
        is False,
        "LEDGER_EXECUTION_UNEXPECTEDLY_AUTHORIZED",
    )

    return {
        "status": "PASS",

        "anchor_version": (
            _anchor.ANCHOR_VERSION
        ),

        "anchor_ledger_version": (
            _anchor.ANCHOR_LEDGER_VERSION
        ),

        "maturation_version": (
            _maturer.MATURATION_VERSION
        ),

        "supersedes_maturation_version": (
            _maturer.SUPERSEDES_MATURATION_VERSION
        ),

        "outcome_ledger_version": (
            _outcome_ledger.OUTCOME_LEDGER_VERSION
        ),

        "supersedes_outcome_ledger_version": (
            _outcome_ledger.SUPERSEDES_OUTCOME_LEDGER_VERSION
        ),

        "decision_bar_semantics": (
            _maturer.DECISION_BAR_SEMANTICS
        ),

        "entry_reference": (
            _maturer.ENTRY_REFERENCE
        ),

        "atr_reference": (
            _maturer.ATR_REFERENCE
        ),

        "horizon_semantics": (
            _maturer.HORIZON_SEMANTICS
        ),

        "anchor_requirement": (
            _maturer.ANCHOR_REQUIREMENT
        ),

        "reference_reconstruction_policy": (
            _maturer.REFERENCE_RECONSTRUCTION_POLICY
        ),

        "formal_maturation_requires_anchor": True,

        "performance_evaluation_authorized": False,

        "pnl_evaluation_authorized": False,

        "live_authorized": False,

        "execution_authorized": False,
    }


# =============================================================================
# Static Safety
# =============================================================================

def static_safety_audit() -> dict[str, Any]:

    paths = (
        REPO_ROOT
        /
        MATURER_REL_PATH,

        REPO_ROOT
        /
        OUTCOME_LEDGER_REL_PATH,

        REPO_ROOT
        /
        RUNNER_REL_PATH,
    )

    violations: list[
        dict[str, str]
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

                    root = (
                        alias.name.split(
                            ".",
                            1,
                        )[0]
                    )

                    if root in FORBIDDEN_IMPORT_ROOTS:

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

                if root in FORBIDDEN_IMPORT_ROOTS:

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

                function = (
                    node.func
                )

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

                if name in FORBIDDEN_BROKER_CALLS:

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
            for path in paths
        ],

        "violation_count": 0,

        "violations": [],
    }


# =============================================================================
# Targeted Regression Tests
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

            ANCHOR_TEST_REL_PATH,

            MATURER_TEST_REL_PATH,

            OUTCOME_LEDGER_TEST_REL_PATH,

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
                -1600:
            ]
        ),
    }


# =============================================================================
# Candidate Artifact Hashes
# =============================================================================

def candidate_artifact_hashes() -> dict[str, str]:

    result: dict[
        str,
        str,
    ] = {}

    for relative_path in (
        MATURER_REL_PATH,
        OUTCOME_LEDGER_REL_PATH,
        MATURER_TEST_REL_PATH,
        OUTCOME_LEDGER_TEST_REL_PATH,
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

        result[
            relative_path
        ] = (
            sha256_file(
                path
            )
        )

    return result


# =============================================================================
# Gate Execution
# =============================================================================

def run_gate() -> dict[str, Any]:

    observation_hash_before = (
        optional_sha256(
            OBSERVATION_LEDGER_PATH
        )
    )

    observation_exists_before = (
        OBSERVATION_LEDGER_PATH.exists()
    )

    anchor_hash_before = (
        optional_sha256(
            ANCHOR_LEDGER_PATH
        )
    )

    anchor_exists_before = (
        ANCHOR_LEDGER_PATH.exists()
    )

    outcome_hash_before = (
        optional_sha256(
            OUTCOME_LEDGER_PATH
        )
    )

    outcome_exists_before = (
        OUTCOME_LEDGER_PATH.exists()
    )

    repository_authority = (
        verify_repository_authority()
    )

    runtime_authorities = (
        verify_runtime_authorities()
    )

    static_safety = (
        static_safety_audit()
    )

    targeted_tests = (
        run_targeted_tests()
    )

    artifact_hashes = (
        candidate_artifact_hashes()
    )

    observation_hash_after = (
        optional_sha256(
            OBSERVATION_LEDGER_PATH
        )
    )

    observation_exists_after = (
        OBSERVATION_LEDGER_PATH.exists()
    )

    anchor_hash_after = (
        optional_sha256(
            ANCHOR_LEDGER_PATH
        )
    )

    anchor_exists_after = (
        ANCHOR_LEDGER_PATH.exists()
    )

    outcome_hash_after = (
        optional_sha256(
            OUTCOME_LEDGER_PATH
        )
    )

    outcome_exists_after = (
        OUTCOME_LEDGER_PATH.exists()
    )

    require(
        observation_exists_before
        ==
        observation_exists_after,
        "OBSERVATION_LEDGER_EXISTENCE_CHANGED",
    )

    require(
        observation_hash_before
        ==
        observation_hash_after,
        "OBSERVATION_LEDGER_CHANGED",
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

    evidence: dict[
        str,
        Any,
    ] = {
        "gate": (
            "Gate 15D-C-B2B/B2C — "
            "Anchor-Required Maturation + Outcome Ledger V2"
        ),

        "gate_id": (
            GATE_ID
        ),

        "schema_version": (
            SCHEMA_VERSION
        ),

        "status": "PASS",

        "repository_authority": (
            repository_authority
        ),

        "runtime_authorities": (
            runtime_authorities
        ),

        "static_safety": (
            static_safety
        ),

        "targeted_tests": (
            targeted_tests
        ),

        "candidate_artifact_hashes": (
            artifact_hashes
        ),

        "supersession": {
            "maturation_version": {
                "supersedes": (
                    SUPERSEDES_MATURATION_VERSION
                ),

                "replacement": (
                    EXPECTED_MATURATION_VERSION
                ),
            },

            "outcome_ledger_version": {
                "supersedes": (
                    SUPERSEDES_OUTCOME_LEDGER_VERSION
                ),

                "replacement": (
                    EXPECTED_OUTCOME_LEDGER_VERSION
                ),
            },

            "historical_commits_rewritten": False,

            "historical_evidence_deleted": False,
        },

        "protocol_boundary": {
            "prospective_anchor_required": True,

            "entry_close_must_come_from_anchor": True,

            "decision_atr14_must_come_from_anchor": True,

            "post_hoc_entry_reconstruction_forbidden": True,

            "post_hoc_atr_reconstruction_forbidden": True,

            "later_m5_data_used_only_for_future_outcome_rows": True,

            "existing_2026_09_28_1145_observation_formally_scoreable": False,

            "existing_2026_09_28_1145_exclusion_reason": (
                "POST_CONTRACT_ACQUISITION_PROOF_"
                "EXCLUDED_FROM_FORMAL_SCORING_"
                "MISSING_PROSPECTIVE_ANCHOR"
            ),
        },

        "true_forward_observation_ledger": {
            "path": (
                "01_Data/Shadow/"
                "xauusd_frozen_c04_shadow_observations.jsonl"
            ),

            "existed_before": (
                observation_exists_before
            ),

            "exists_after": (
                observation_exists_after
            ),

            "sha256_before": (
                observation_hash_before
            ),

            "sha256_after": (
                observation_hash_after
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

        "genuine_forward_observation_captured": False,

        "genuine_anchor_appended": False,

        "genuine_forward_observation_matured": False,

        "genuine_outcome_appended": False,

        "mt5_initialized": False,

        "market_data_acquired": False,

        "validation_partition_accessed": False,

        "test_partition_accessed": False,

        "model_changed": False,

        "features_changed": False,

        "forward_performance_evaluated": False,

        "accuracy_evaluated": False,

        "win_rate_evaluated": False,

        "pnl_evaluated": False,

        "return_evaluated": False,

        "drawdown_evaluated": False,

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
                "runtime_authorities"
            ]
        )

        print(
            "GATE_15D_C_B2BC_STATUS=PASS"
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
            "SUPERSEDES_MATURATION_VERSION="
            +
            str(
                authority[
                    "supersedes_maturation_version"
                ]
            )
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
            "SUPERSEDES_OUTCOME_LEDGER_VERSION="
            +
            str(
                authority[
                    "supersedes_outcome_ledger_version"
                ]
            )
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
            "ANCHOR_REQUIREMENT="
            +
            str(
                authority[
                    "anchor_requirement"
                ]
            )
        )

        print(
            "REFERENCE_RECONSTRUCTION_POLICY="
            +
            str(
                authority[
                    "reference_reconstruction_policy"
                ]
            )
        )

        print(
            "FORMAL_MATURATION_REQUIRES_ANCHOR=true"
        )

        print(
            "LEGACY_1145_OBSERVATION_FORMALLY_SCOREABLE=false"
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
            "GENUINE_OUTCOME_APPENDED=false"
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
            "GATE_15D_C_B2BC_STATUS=FAIL"
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
            "GENUINE_OUTCOME_APPENDED=false"
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