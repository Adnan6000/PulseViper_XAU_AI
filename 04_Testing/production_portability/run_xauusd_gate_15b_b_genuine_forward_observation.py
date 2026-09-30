"""
===============================================================================
Module      : run_xauusd_gate_15b_b_genuine_forward_observation.py
Project     : PulseViper XAU AI
Purpose     : Gate 15B-B — First Genuine Read-Only Forward Observation
===============================================================================

REAL MT5
  -> initialize lifecycle only
  -> immediate approved read-only capability facade
  -> Gate 15B-A v2.1 exact supported-symbol authority
  -> genuine acquisition with fail-closed timestamp-basis detection
  -> attested normalized tick freshness
  -> completed multi-timeframe bars only
  -> representation-only pandas ns/UTC normalization
  -> Gate 13 frozen 331 features
  -> Gate 14 frozen C04 inference
  -> Gate 15A TRUE_FORWARD observation
  -> append-only operational shadow ledger

NON-NEGOTIABLE SAFETY:
- No broker writes.
- No order submission/check/calculation.
- No position/order/history access.
- No RiskEngine.
- No trade_ready.
- No broker-aware risk engine.
- No account protection engine.
- No execution dependency.
- No forming candle.
- No validation/test holdout access.
- No performance evaluation.
- No outcome evaluation.
- No post-hoc outcome horizon.
- No timestamp offset invented by this runner.
- Timestamp authority belongs exclusively to accepted Gate 15B-A v2.1.
- live_authorized = False.
- execution_authorized = False.
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
from typing import Any, Mapping, cast

import pandas as pd
import sklearn


# =============================================================================
# Repository
# =============================================================================

REPO_ROOT: Path = Path(__file__).resolve().parents[2]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(REPO_ROOT),
    )


# Formal Gate 15B-A v2.1 accepted evidence commit.
GATE_15B_A_AUTHORITY_COMMIT: str = (
    "e4359f4888c4051b8dc547740bf196f23b245003"
)

GATE_ID: str = (
    "GATE_15B_B_FIRST_GENUINE_FORWARD_OBSERVATION"
)

SCHEMA_VERSION: str = "2.0.0"

EXPECTED_SKLEARN_VERSION: str = "1.9.0"


RUNNER_REL_PATH: str = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15b_b_genuine_forward_observation.py"
)

DIAGNOSTIC_REL_PATH: str = (
    "04_Testing/production_portability/"
    "diagnose_xauusd_icmarkets_server_time_history.py"
)

PASS_EVIDENCE_REL_PATH: str = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15b_b_first_genuine_forward_observation_evidence.json"
)

BLOCKED_EVIDENCE_REL_PATH: str = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15b_b_first_genuine_forward_observation_blocked.json"
)

GATE_15B_A_EVIDENCE_REL_PATH: str = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15b_a_read_only_forward_acquisition_evidence.json"
)

GATE_15B_A_ADAPTER_REL_PATH: str = (
    "02_AI/Adapters/"
    "mt5_read_only_forward_acquisition_adapter.py"
)

GATE_15B_A_TEST_REL_PATH: str = (
    "04_Testing/production_portability/"
    "test_mt5_read_only_forward_acquisition_adapter.py"
)

GATE_15B_A_RUNNER_REL_PATH: str = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15b_a_read_only_forward_acquisition_evidence.py"
)


LEDGER_PATH: Path = (
    REPO_ROOT
    / "01_Data"
    / "Shadow"
    / "xauusd_frozen_c04_shadow_observations.jsonl"
)

PASS_EVIDENCE_PATH: Path = (
    REPO_ROOT
    / PASS_EVIDENCE_REL_PATH
)

BLOCKED_EVIDENCE_PATH: Path = (
    REPO_ROOT
    / BLOCKED_EVIDENCE_REL_PATH
)

GATE_15B_A_EVIDENCE_PATH: Path = (
    REPO_ROOT
    / GATE_15B_A_EVIDENCE_REL_PATH
)


# Once Gate 15B-A v2.1 authority is established, any later committed change
# before/during Gate 15B-B must be explicitly restricted to Gate 15B-B artifacts.
ALLOWED_POST_AUTHORITY_TRACKED_PATHS: frozenset[str] = frozenset(
    {
        RUNNER_REL_PATH,
        PASS_EVIDENCE_REL_PATH,
        BLOCKED_EVIDENCE_REL_PATH,
    }
)

ALLOWED_UNTRACKED_PATHS: frozenset[str] = frozenset(
    {
        RUNNER_REL_PATH,
        DIAGNOSTIC_REL_PATH,
        PASS_EVIDENCE_REL_PATH,
        BLOCKED_EVIDENCE_REL_PATH,
    }
)


# =============================================================================
# Existing Authorities
# =============================================================================

mt5 = importlib.import_module(
    "MetaTrader5"
)

_acq = importlib.import_module(
    "02_AI.Adapters.mt5_read_only_forward_acquisition_adapter"
)

_pipeline = importlib.import_module(
    "02_AI.Features.portable_feature_pipeline"
)

_contract = importlib.import_module(
    "02_AI.Features.portable_feature_contract"
)

_observer = importlib.import_module(
    "02_AI.Models.frozen_c04_shadow_observer"
)


MT5ReadOnlyCapabilityFacade = (
    _acq.MT5ReadOnlyCapabilityFacade
)

MT5ReadOnlyForwardAcquisitionAdapter = (
    _acq.MT5ReadOnlyForwardAcquisitionAdapter
)

verify_forward_acquisition_authority = (
    _acq.verify_forward_acquisition_authority
)

compute_canonical_snapshot_id = (
    _acq.compute_canonical_snapshot_id
)

TIME_BASIS_UNIX_UTC: str = str(
    _acq.TIME_BASIS_UNIX_UTC
)

TIME_BASIS_NY_CLOSE_SERVER: str = str(
    _acq.TIME_BASIS_NY_CLOSE_SERVER
)

ACQUISITION_SCHEMA_VERSION: str = str(
    _acq.ACQUISITION_SCHEMA_VERSION
)

ACQUISITION_AUTHORITY_ID: str = str(
    _acq.ACQUISITION_AUTHORITY_ID
)

DEFAULT_MAX_TICK_AGE_SECONDS: int = int(
    _acq.DEFAULT_MAX_TICK_AGE_SECONDS
)

DEFAULT_MAX_FUTURE_TICK_SKEW_SECONDS: int = int(
    _acq.DEFAULT_MAX_FUTURE_TICK_SKEW_SECONDS
)


PortableFeaturePipeline = (
    _pipeline.PortableFeaturePipeline
)

FrozenC04ShadowObserver = (
    _observer.FrozenC04ShadowObserver
)

FrozenC04ObservationLedger = (
    _observer.FrozenC04ObservationLedger
)

DuplicateHandling = (
    _observer.DuplicateHandling
)

SourceProvenance = (
    _observer.SourceProvenance
)

OUTCOME_HORIZON_CONTRACT_STATUS: str = str(
    _observer.OUTCOME_HORIZON_CONTRACT_STATUS
)


EXPECTED_FEATURE_COUNT: int = int(
    _contract.EXPECTED_FEATURE_COUNT
)

EXPECTED_FEATURE_COLUMNS_SHA256: str = str(
    _contract.EXPECTED_FEATURE_COLUMNS_SHA256
)

FROZEN_MODEL_SHA256: str = str(
    _contract.FROZEN_MODEL_SHA256
)

SUPPORTED_SYMBOLS: tuple[str, ...] = tuple(
    str(value)
    for value
    in _contract.SUPPORTED_SYMBOLS
)


# =============================================================================
# Error
# =============================================================================

class Gate15BBBlockedError(RuntimeError):
    """Fail-closed Gate 15B-B blocker."""


def require(
    condition: bool,
    reason: str,
) -> None:
    if not condition:
        raise Gate15BBBlockedError(
            reason
        )


# =============================================================================
# Generic Utilities
# =============================================================================

def utc_timestamp(
    value: Any,
) -> pd.Timestamp:
    raw = pd.Timestamp(
        value
    )

    if raw is pd.NaT:
        raise Gate15BBBlockedError(
            "INVALID_UTC_TIMESTAMP_NAT"
        )

    timestamp = cast(
        pd.Timestamp,
        raw,
    )

    if timestamp.tzinfo is None:
        localized = timestamp.tz_localize(
            "UTC"
        )

        if localized is pd.NaT:
            raise Gate15BBBlockedError(
                "UTC_TIMESTAMP_LOCALIZATION_FAILED"
            )

        return cast(
            pd.Timestamp,
            localized,
        )

    converted = timestamp.tz_convert(
        "UTC"
    )

    if converted is pd.NaT:
        raise Gate15BBBlockedError(
            "UTC_TIMESTAMP_CONVERSION_FAILED"
        )

    return cast(
        pd.Timestamp,
        converted,
    )


def utc_iso(
    value: Any,
) -> str:
    timestamp = utc_timestamp(
        value
    )

    output = timestamp.isoformat()

    if output.endswith(
        "+00:00"
    ):
        output = (
            output[:-6]
            + "Z"
        )

    return output


def now_utc_iso() -> str:
    return utc_iso(
        pd.Timestamp.now(
            tz="UTC"
        )
    )


def sanitize_error_text(
    exc: BaseException,
) -> str:
    output = str(
        exc
    ).replace(
        str(REPO_ROOT),
        "<REPO_ROOT>",
    )

    return " ".join(
        output.split()
    )[:1500]


def normalize_git_path(
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


def git_process(
    *args: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "git",
            *args,
        ],
        cwd=REPO_ROOT,
        check=check,
        capture_output=True,
        text=True,
    )


def git_output(
    *args: str,
) -> str:
    # Preserve Git porcelain leading spaces.
    return git_process(
        *args
    ).stdout.rstrip(
        "\r\n"
    )


def working_tree_clean() -> bool:
    return (
        git_output(
            "status",
            "--porcelain",
            "--untracked-files=all",
        )
        == ""
    )


def file_sha256(
    path: Path,
) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def write_json_atomic_enough_for_evidence(
    path: Path,
    document: Mapping[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_path = path.with_suffix(
        path.suffix
        + ".tmp"
    )

    temp_path.write_text(
        json.dumps(
            document,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )

    temp_path.replace(
        path
    )


# =============================================================================
# Git Authority
# =============================================================================

def _parse_untracked_paths(
    status_porcelain: str,
) -> set[str]:
    paths: set[str] = set()

    for raw_line in (
        status_porcelain.splitlines()
    ):
        line = raw_line.rstrip()

        if line.startswith(
            "?? "
        ):
            paths.add(
                normalize_git_path(
                    line[3:]
                )
            )

    return paths


def verify_gate_15b_a_evidence() -> dict[str, Any]:
    require(
        GATE_15B_A_EVIDENCE_PATH.is_file(),
        "GATE_15B_A_V2_1_EVIDENCE_MISSING",
    )

    evidence = json.loads(
        GATE_15B_A_EVIDENCE_PATH.read_text(
            encoding="utf-8"
        )
    )

    require(
        evidence.get(
            "status"
        )
        == "PASS",
        "GATE_15B_A_V2_1_EVIDENCE_NOT_PASS",
    )

    require(
        evidence.get(
            "gate_version"
        )
        == "2.1.0",
        "GATE_15B_A_GATE_VERSION_NOT_2_1_0",
    )

    authority = evidence.get(
        "authority",
        {},
    )

    require(
        isinstance(
            authority,
            Mapping,
        ),
        "GATE_15B_A_AUTHORITY_DOCUMENT_INVALID",
    )

    require(
        authority.get(
            "schema_version"
        )
        == "2.1.0",
        "GATE_15B_A_SCHEMA_VERSION_NOT_2_1_0",
    )

    require(
        authority.get(
            "acquisition_authority_id"
        )
        == "MT5ReadOnlyForwardAcquisitionAdapter:2.1.0",
        "GATE_15B_A_AUTHORITY_ID_MISMATCH",
    )

    require(
        authority.get(
            "fixed_broker_offset_used"
        )
        is False,
        "GATE_15B_A_FIXED_BROKER_OFFSET_MUST_BE_FALSE",
    )

    require(
        authority.get(
            "historical_dst_normalization"
        )
        == "PER_ROW",
        "GATE_15B_A_HISTORICAL_DST_POLICY_MISMATCH",
    )

    inherited = evidence.get(
        "inherited_frozen_baseline",
        {},
    )

    require(
        isinstance(
            inherited,
            Mapping,
        ),
        "GATE_15B_A_INHERITED_BASELINE_INVALID",
    )

    require(
        inherited.get(
            "status"
        )
        == "PASS",
        "GATE_15B_A_INHERITED_41_OF_41_NOT_PASS",
    )

    require(
        int(
            inherited.get(
                "previous_verified_count",
                -1,
            )
        )
        == 41,
        "GATE_15B_A_INHERITED_VERIFIED_COUNT_NOT_41",
    )

    require(
        int(
            inherited.get(
                "previous_total_count",
                -1,
            )
        )
        == 41,
        "GATE_15B_A_INHERITED_TOTAL_COUNT_NOT_41",
    )

    for key in (
        "git_authority",
        "static_safety_audit",
        "sklearn_runtime_authority",
        "targeted_pytest",
        "unix_utc_policy_verification",
        "ny_close_server_policy_verification",
        "synthetic_pipeline_verification",
    ):
        section = evidence.get(
            key,
            {},
        )

        require(
            isinstance(
                section,
                Mapping,
            ),
            f"GATE_15B_A_SECTION_INVALID:{key}",
        )

        require(
            section.get(
                "status"
            )
            == "PASS",
            f"GATE_15B_A_SECTION_NOT_PASS:{key}",
        )

    sklearn_authority = evidence[
        "sklearn_runtime_authority"
    ]

    require(
        sklearn_authority.get(
            "expected_version"
        )
        == EXPECTED_SKLEARN_VERSION,
        "GATE_15B_A_SKLEARN_EXPECTED_VERSION_MISMATCH",
    )

    require(
        sklearn_authority.get(
            "actual_version"
        )
        == EXPECTED_SKLEARN_VERSION,
        "GATE_15B_A_SKLEARN_ACTUAL_VERSION_MISMATCH",
    )

    frozen_contracts = evidence.get(
        "frozen_contracts",
        {},
    )

    require(
        isinstance(
            frozen_contracts,
            Mapping,
        ),
        "GATE_15B_A_FROZEN_CONTRACTS_INVALID",
    )

    require(
        int(
            frozen_contracts.get(
                "feature_count",
                -1,
            )
        )
        == EXPECTED_FEATURE_COUNT,
        "GATE_15B_A_FEATURE_COUNT_AUTHORITY_MISMATCH",
    )

    require(
        frozen_contracts.get(
            "feature_columns_sha256"
        )
        == EXPECTED_FEATURE_COLUMNS_SHA256,
        "GATE_15B_A_FEATURE_SHA_AUTHORITY_MISMATCH",
    )

    require(
        frozen_contracts.get(
            "model_sha256"
        )
        == FROZEN_MODEL_SHA256,
        "GATE_15B_A_MODEL_SHA_AUTHORITY_MISMATCH",
    )

    artifact_hashes = evidence.get(
        "candidate_artifact_hashes",
        {},
    )

    require(
        isinstance(
            artifact_hashes,
            Mapping,
        ),
        "GATE_15B_A_ARTIFACT_HASH_AUTHORITY_INVALID",
    )

    expected_paths = (
        GATE_15B_A_ADAPTER_REL_PATH,
        GATE_15B_A_TEST_REL_PATH,
        GATE_15B_A_RUNNER_REL_PATH,
    )

    verified_hashes: dict[
        str,
        str,
    ] = {}

    for relative_path in expected_paths:
        expected_hash = artifact_hashes.get(
            relative_path
        )

        require(
            isinstance(
                expected_hash,
                str,
            )
            and len(
                expected_hash
            )
            == 64,
            (
                "GATE_15B_A_ARTIFACT_HASH_MISSING:"
                f"{relative_path}"
            ),
        )

        actual_hash = file_sha256(
            REPO_ROOT
            / relative_path
        )

        require(
            actual_hash
            == expected_hash,
            (
                "GATE_15B_A_ARTIFACT_HASH_MISMATCH:"
                f"{relative_path}:"
                f"{actual_hash}!="
                f"{expected_hash}"
            ),
        )

        verified_hashes[
            relative_path
        ] = actual_hash

    return {
        "status": "PASS",
        "gate_version": "2.1.0",
        "authority_commit": (
            GATE_15B_A_AUTHORITY_COMMIT
        ),
        "schema_version": (
            authority[
                "schema_version"
            ]
        ),
        "acquisition_authority_id": (
            authority[
                "acquisition_authority_id"
            ]
        ),
        "historical_dst_normalization": (
            authority[
                "historical_dst_normalization"
            ]
        ),
        "inherited_41_of_41_status": (
            inherited[
                "status"
            ]
        ),
        "verified_artifact_hashes": (
            verified_hashes
        ),
    }


def verify_repository_authority() -> dict[str, Any]:
    fetch = git_process(
        "fetch",
        "origin",
        check=False,
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
        == "main",
        f"UNEXPECTED_BRANCH:{branch}",
    )

    require(
        head
        == origin_main,
        (
            "HEAD_ORIGIN_MAIN_DIVERGENCE:"
            f"head={head};"
            f"origin_main={origin_main}"
        ),
    )

    ancestor = git_process(
        "merge-base",
        "--is-ancestor",
        GATE_15B_A_AUTHORITY_COMMIT,
        head,
        check=False,
    )

    require(
        ancestor.returncode
        == 0,
        "GATE_15B_A_V2_1_AUTHORITY_COMMIT_NOT_ANCESTOR",
    )

    tracked_unstaged = {
        normalize_git_path(
            path
        )
        for path
        in git_output(
            "diff",
            "--name-only",
        ).splitlines()
        if path.strip()
    }

    tracked_staged = {
        normalize_git_path(
            path
        )
        for path
        in git_output(
            "diff",
            "--cached",
            "--name-only",
        ).splitlines()
        if path.strip()
    }

    require(
        not tracked_unstaged,
        (
            "TRACKED_UNSTAGED_CHANGES_PRESENT:"
            f"{sorted(tracked_unstaged)}"
        ),
    )

    require(
        not tracked_staged,
        (
            "STAGED_CHANGES_PRESENT:"
            f"{sorted(tracked_staged)}"
        ),
    )

    changed_since_authority = {
        normalize_git_path(
            path
        )
        for path
        in git_output(
            "diff",
            "--name-only",
            (
                f"{GATE_15B_A_AUTHORITY_COMMIT}"
                f"..{head}"
            ),
        ).splitlines()
        if path.strip()
    }

    unexpected_committed = (
        changed_since_authority
        - set(
            ALLOWED_POST_AUTHORITY_TRACKED_PATHS
        )
    )

    require(
        not unexpected_committed,
        (
            "UNAUTHORIZED_COMMITTED_CHANGE_AFTER_GATE_15B_A_V2_1:"
            f"{sorted(unexpected_committed)}"
        ),
    )

    status_porcelain = git_output(
        "status",
        "--porcelain",
        "--untracked-files=all",
    )

    untracked_paths = (
        _parse_untracked_paths(
            status_porcelain
        )
    )

    unexpected_untracked = (
        untracked_paths
        - set(
            ALLOWED_UNTRACKED_PATHS
        )
    )

    require(
        not unexpected_untracked,
        (
            "UNEXPECTED_UNTRACKED_PATHS:"
            f"{sorted(unexpected_untracked)}"
        ),
    )

    gate_15b_a = (
        verify_gate_15b_a_evidence()
    )

    return {
        "status": "PASS",
        "branch": branch,
        "execution_head": head,
        "origin_main": origin_main,
        "head_equals_origin_main": True,
        "gate_15b_a_authority_commit": (
            GATE_15B_A_AUTHORITY_COMMIT
        ),
        "gate_15b_a_authority_is_ancestor": True,
        "changed_since_gate_15b_a_authority": sorted(
            changed_since_authority
        ),
        "allowed_post_authority_tracked_paths_only": True,
        "tracked_unstaged_change_count": 0,
        "tracked_staged_change_count": 0,
        "allowed_untracked_paths_present": sorted(
            untracked_paths
        ),
        "unexpected_untracked_path_count": 0,
        "gate_15b_a_v2_1": (
            gate_15b_a
        ),
    }


# =============================================================================
# Static Safety
# =============================================================================

def static_safety_audit() -> dict[str, Any]:
    files = [
        REPO_ROOT
        / RUNNER_REL_PATH,
        REPO_ROOT
        / GATE_15B_A_ADAPTER_REL_PATH,
        REPO_ROOT
        / "02_AI"
        / "Features"
        / "portable_feature_pipeline.py",
        REPO_ROOT
        / "02_AI"
        / "Models"
        / "frozen_c04_inference_adapter.py",
        REPO_ROOT
        / "02_AI"
        / "Models"
        / "frozen_c04_shadow_observer.py",
    ]

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
        "history_deals_get",
        "PositionOpen",
        "PositionClose",
        "order_modify",
        "order_close",
    }

    forbidden_dependencies = {
        "RiskEngine",
        "trade_ready",
        "broker_aware_risk_engine",
        "account_protection_guard",
    }

    findings: list[
        dict[str, str]
    ] = []

    for path in files:
        require(
            path.is_file(),
            (
                "STATIC_SAFETY_FILE_MISSING:"
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
                    for token in (
                        forbidden_dependencies
                    ):
                        if token in alias.name:
                            findings.append(
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

                for token in (
                    forbidden_dependencies
                ):
                    if token in module:
                        findings.append(
                            {
                                "file": path.name,
                                "type": (
                                    "import_from"
                                ),
                                "symbol": module,
                            }
                        )

                for alias in node.names:
                    if (
                        alias.name
                        in forbidden_dependencies
                    ):
                        findings.append(
                            {
                                "file": path.name,
                                "type": (
                                    "import_symbol"
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
                    if (
                        function.id
                        in forbidden_calls
                    ):
                        findings.append(
                            {
                                "file": path.name,
                                "type": "call",
                                "symbol": (
                                    function.id
                                ),
                            }
                        )

                elif isinstance(
                    function,
                    ast.Attribute,
                ):
                    if (
                        function.attr
                        in forbidden_calls
                    ):
                        findings.append(
                            {
                                "file": path.name,
                                "type": "call",
                                "symbol": (
                                    function.attr
                                ),
                            }
                        )

    require(
        not findings,
        (
            "STATIC_SAFETY_AUDIT_FAILED:"
            f"{findings}"
        ),
    )

    facade_forbidden = set(
        MT5ReadOnlyCapabilityFacade
        .FORBIDDEN_MUTATING_METHODS
    )

    core_mt5_writes = {
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

    require(
        core_mt5_writes.issubset(
            facade_forbidden
        ),
        (
            "READ_ONLY_FACADE_"
            "FORBIDDEN_METHOD_SET_INCOMPLETE"
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
            for path
            in files
        ],
        "audited_file_count": len(
            files
        ),
        "forbidden_write_call_count": 0,
        "forbidden_execution_dependency_count": 0,
        "facade_core_mutating_methods_blocked": True,
        "violations": [],
    }


# =============================================================================
# Runtime Compatibility
# =============================================================================

def verify_runtime_authority() -> dict[str, Any]:
    actual_sklearn = str(
        sklearn.__version__
    )

    require(
        actual_sklearn
        == EXPECTED_SKLEARN_VERSION,
        (
            "SKLEARN_RUNTIME_VERSION_MISMATCH:"
            f"expected={EXPECTED_SKLEARN_VERSION};"
            f"actual={actual_sklearn}"
        ),
    )

    require(
        ACQUISITION_SCHEMA_VERSION
        == "2.1.0",
        (
            "ACQUISITION_SCHEMA_VERSION_MISMATCH:"
            f"{ACQUISITION_SCHEMA_VERSION}"
        ),
    )

    require(
        ACQUISITION_AUTHORITY_ID
        == (
            "MT5ReadOnlyForwardAcquisitionAdapter:"
            "2.1.0"
        ),
        (
            "ACQUISITION_AUTHORITY_ID_MISMATCH:"
            f"{ACQUISITION_AUTHORITY_ID}"
        ),
    )

    return {
        "status": "PASS",
        "sklearn_version": (
            actual_sklearn
        ),
        "acquisition_schema_version": (
            ACQUISITION_SCHEMA_VERSION
        ),
        "acquisition_authority_id": (
            ACQUISITION_AUTHORITY_ID
        ),
    }


# =============================================================================
# Timestamp Representation Normalization
# =============================================================================

def normalize_market_timestamp_resolution(
    market_data: Mapping[
        str,
        pd.DataFrame,
    ],
) -> tuple[
    dict[str, pd.DataFrame],
    dict[str, str],
    dict[str, str],
]:
    normalized: dict[
        str,
        pd.DataFrame,
    ] = {}

    dtypes_before: dict[
        str,
        str,
    ] = {}

    dtypes_after: dict[
        str,
        str,
    ] = {}

    for (
        timeframe,
        source_frame,
    ) in market_data.items():
        require(
            isinstance(
                source_frame,
                pd.DataFrame,
            ),
            (
                "MARKET_DATA_FRAME_INVALID:"
                f"{timeframe}"
            ),
        )

        require(
            "time"
            in source_frame.columns,
            (
                "MARKET_DATA_TIME_COLUMN_MISSING:"
                f"{timeframe}"
            ),
        )

        frame = source_frame.copy(
            deep=True
        )

        dtypes_before[
            str(timeframe)
        ] = str(
            frame[
                "time"
            ].dtype
        )

        normalized_time = (
            pd.to_datetime(
                frame[
                    "time"
                ],
                utc=True,
                errors="raise",
            )
        )

        frame[
            "time"
        ] = normalized_time.astype(
            "datetime64[ns, UTC]"
        )

        require(
            not bool(
                frame[
                    "time"
                ].isna().any()
            ),
            (
                "TIMESTAMP_NORMALIZATION_"
                "PRODUCED_NAT:"
                f"{timeframe}"
            ),
        )

        dtypes_after[
            str(timeframe)
        ] = str(
            frame[
                "time"
            ].dtype
        )

        require(
            dtypes_after[
                str(timeframe)
            ]
            == "datetime64[ns, UTC]",
            (
                "TIMESTAMP_NORMALIZATION_"
                "DID_NOT_PRODUCE_NS_UTC:"
                f"{timeframe}:"
                f"{dtypes_after[str(timeframe)]}"
            ),
        )

        normalized[
            str(timeframe)
        ] = frame

    return (
        normalized,
        dtypes_before,
        dtypes_after,
    )


# =============================================================================
# Ledger
# =============================================================================

def true_forward_count(
    ledger: Any,
) -> int:
    return sum(
        1
        for record
        in ledger.read_all()
        if (
            record.source_provenance
            == (
                SourceProvenance
                .TRUE_FORWARD_OBSERVATION
                .value
            )
        )
    )


def safe_ledger_state() -> dict[str, Any]:
    try:
        ledger = (
            FrozenC04ObservationLedger(
                ledger_path=LEDGER_PATH,
                duplicate_handling=(
                    DuplicateHandling
                    .IDEMPOTENT_IGNORE
                ),
            )
        )

        ledger.validate_integrity()

        return {
            "available": True,
            "total_count": (
                ledger.count()
            ),
            "true_forward_count": (
                true_forward_count(
                    ledger
                )
            ),
            "integrity_verified": True,
            "error": None,
        }

    except Exception as exc:
        return {
            "available": False,
            "total_count": -1,
            "true_forward_count": -1,
            "integrity_verified": False,
            "error": (
                sanitize_error_text(
                    exc
                )
            ),
        }


# =============================================================================
# Market / Freshness Verification
# =============================================================================

def verify_bid_ask(
    read_only_api: Any,
    broker_symbol: str,
) -> dict[str, Any]:
    """
    Bid/ask validity only.

    IMPORTANT:
    Raw tick.time is NOT compared with local epoch here.
    Timestamp/freshness semantics belong to Gate 15B-A v2.1 acquisition.
    """

    require(
        bool(
            str(
                broker_symbol
            ).strip()
        ),
        "RESOLVED_BROKER_SYMBOL_EMPTY",
    )

    symbol_info = (
        read_only_api
        .symbol_info(
            broker_symbol
        )
    )

    require(
        symbol_info
        is not None,
        (
            "RESOLVED_SYMBOL_INFO_UNAVAILABLE:"
            f"{broker_symbol}"
        ),
    )

    tick = (
        read_only_api
        .symbol_info_tick(
            broker_symbol
        )
    )

    require(
        tick
        is not None,
        "GOLD_TICK_UNAVAILABLE",
    )

    bid_raw = getattr(
        tick,
        "bid",
        None,
    )

    ask_raw = getattr(
        tick,
        "ask",
        None,
    )

    if bid_raw is None:
        raise Gate15BBBlockedError(
            "GOLD_TICK_BID_MISSING"
        )

    if ask_raw is None:
        raise Gate15BBBlockedError(
            "GOLD_TICK_ASK_MISSING"
        )

    bid = float(
        bid_raw
    )

    ask = float(
        ask_raw
    )

    require(
        bid > 0.0,
        "GOLD_TICK_BID_INVALID",
    )

    require(
        ask > 0.0,
        "GOLD_TICK_ASK_INVALID",
    )

    require(
        ask >= bid,
        "GOLD_TICK_ASK_BELOW_BID",
    )

    return {
        "status": "PASS",
        "valid_bid_ask": True,
        "bid": bid,
        "ask": ask,
        "raw_tick_time_not_used_for_freshness": True,
    }


def verify_attested_freshness(
    attestation: Any,
) -> dict[str, Any]:
    """
    Freshness is taken exclusively from Gate 15B-A v2.1 normalized
    time-basis authority.

    The acquisition adapter already fails closed if normalized tick age:
      > 180 seconds
      < -5 seconds
    or timestamp basis is ambiguous.
    """

    policy = str(
        attestation.time_basis_policy
    )

    require(
        policy
        in {
            TIME_BASIS_UNIX_UTC,
            TIME_BASIS_NY_CLOSE_SERVER,
        },
        (
            "UNSUPPORTED_ATTESTED_TIME_BASIS:"
            f"{policy}"
        ),
    )

    reference_tick_utc = (
        attestation
        .time_basis_reference_tick_utc
    )

    require(
        isinstance(
            reference_tick_utc,
            str,
        )
        and bool(
            reference_tick_utc
        ),
        (
            "ATTESTED_NORMALIZED_REFERENCE_"
            "TICK_UTC_MISSING"
        ),
    )

    age_raw = (
        attestation
        .time_basis_reference_tick_age_seconds
    )

    require(
        age_raw
        is not None,
        "ATTESTED_TICK_AGE_MISSING",
    )

    age_seconds = float(
        age_raw
    )

    require(
        age_seconds
        <= float(
            DEFAULT_MAX_TICK_AGE_SECONDS
        ),
        (
            "ATTESTED_NORMALIZED_TICK_STALE:"
            f"age={age_seconds};"
            f"limit={DEFAULT_MAX_TICK_AGE_SECONDS}"
        ),
    )

    require(
        age_seconds
        >= -float(
            DEFAULT_MAX_FUTURE_TICK_SKEW_SECONDS
        ),
        (
            "ATTESTED_NORMALIZED_TICK_FUTURE:"
            f"age={age_seconds};"
            f"future_limit="
            f"{DEFAULT_MAX_FUTURE_TICK_SKEW_SECONDS}"
        ),
    )

    decision_time = utc_timestamp(
        attestation.decision_time_utc
    )

    normalized_tick = utc_timestamp(
        reference_tick_utc
    )

    require(
        decision_time
        <= normalized_tick,
        (
            "ATTESTED_DECISION_AFTER_"
            "NORMALIZED_REFERENCE_TICK:"
            f"decision={utc_iso(decision_time)};"
            f"tick={utc_iso(normalized_tick)}"
        ),
    )

    current_utc = pd.Timestamp.now(
        tz="UTC"
    )

    require(
        decision_time
        <= (
            current_utc
            + pd.Timedelta(
                seconds=(
                    DEFAULT_MAX_FUTURE_TICK_SKEW_SECONDS
                )
            )
        ),
        (
            "ATTESTED_DECISION_TIME_IS_FUTURE:"
            f"decision={utc_iso(decision_time)};"
            f"now={utc_iso(current_utc)}"
        ),
    )

    return {
        "status": "PASS",
        "authority": (
            "GATE_15B_A_V2_1_"
            "NORMALIZED_TIME_BASIS_ATTESTATION"
        ),
        "time_basis_policy": policy,
        "reference_tick_raw": (
            attestation
            .time_basis_reference_tick_raw
        ),
        "reference_tick_utc": (
            reference_tick_utc
        ),
        "reference_offset_seconds": (
            attestation
            .time_basis_reference_offset_seconds
        ),
        "tick_age_seconds": (
            age_seconds
        ),
        "max_tick_age_seconds": (
            DEFAULT_MAX_TICK_AGE_SECONDS
        ),
        "max_future_tick_skew_seconds": (
            DEFAULT_MAX_FUTURE_TICK_SKEW_SECONDS
        ),
        "decision_time_not_after_normalized_tick": (
            True
        ),
        "decision_time_not_future": (
            True
        ),
    }


# =============================================================================
# Runtime State / BLOCKED Evidence
# =============================================================================

def initial_run_state() -> dict[str, Any]:
    return {
        "repository_authority": None,
        "static_safety": None,
        "runtime_authority": None,
        "total_count_before": None,
        "true_forward_count_before": None,
        "total_count_after": None,
        "true_forward_count_after": None,
        "new_true_forward_observations_added": None,
        "mt5_initialized": False,
        "genuine_mt5_acquisition": False,
        "resolved_broker_symbol": None,
        "time_basis_policy": None,
        "normalized_reference_tick_utc": None,
        "decision_time_utc": None,
        "source_snapshot_id": None,
        "verified_forward_authority": False,
        "gate13_status": "NOT_RUN",
        "gate14_status": "NOT_RUN",
        "gate15a_status": "NOT_RUN",
        "ledger_append_performed": False,
        "ledger_idempotent_duplicate": False,
    }


def write_blocked_evidence(
    exc: BaseException,
    state: Mapping[str, Any],
) -> dict[str, Any]:
    ledger_now = (
        safe_ledger_state()
    )

    try:
        head = git_output(
            "rev-parse",
            "HEAD",
        )

        origin_main = git_output(
            "rev-parse",
            "origin/main",
        )

        head_equals_origin = (
            head
            == origin_main
        )

    except Exception:
        head = None
        origin_main = None
        head_equals_origin = False

    before = state.get(
        "true_forward_count_before"
    )

    after = ledger_now.get(
        "true_forward_count"
    )

    delta: int | None = None

    if (
        isinstance(
            before,
            int,
        )
        and isinstance(
            after,
            int,
        )
        and before >= 0
        and after >= 0
    ):
        delta = (
            after
            - before
        )

    blocked: dict[
        str,
        Any,
    ] = {
        "gate": (
            "Gate 15B-B — First Genuine "
            "Read-Only Forward Observation"
        ),
        "gate_id": GATE_ID,
        "schema_version": (
            SCHEMA_VERSION
        ),
        "generated_at_utc": (
            now_utc_iso()
        ),
        "status": "BLOCKED",
        "reason": {
            "error_type": (
                type(
                    exc
                ).__name__
            ),
            "error_text": (
                sanitize_error_text(
                    exc
                )
            ),
        },
        "git": {
            "gate_15b_a_authority_commit": (
                GATE_15B_A_AUTHORITY_COMMIT
            ),
            "execution_head": head,
            "origin_main": origin_main,
            "head_equals_origin_main": (
                head_equals_origin
            ),
        },
        "progress_before_block": {
            "mt5_initialized": bool(
                state.get(
                    "mt5_initialized",
                    False,
                )
            ),
            "genuine_mt5_acquisition": bool(
                state.get(
                    "genuine_mt5_acquisition",
                    False,
                )
            ),
            "resolved_broker_symbol": (
                state.get(
                    "resolved_broker_symbol"
                )
            ),
            "time_basis_policy": (
                state.get(
                    "time_basis_policy"
                )
            ),
            "normalized_reference_tick_utc": (
                state.get(
                    "normalized_reference_tick_utc"
                )
            ),
            "decision_time_utc": (
                state.get(
                    "decision_time_utc"
                )
            ),
            "source_snapshot_id": (
                state.get(
                    "source_snapshot_id"
                )
            ),
            "verified_forward_authority": bool(
                state.get(
                    "verified_forward_authority",
                    False,
                )
            ),
            "gate13_status": (
                state.get(
                    "gate13_status",
                    "NOT_RUN",
                )
            ),
            "gate14_status": (
                state.get(
                    "gate14_status",
                    "NOT_RUN",
                )
            ),
            "gate15a_status": (
                state.get(
                    "gate15a_status",
                    "NOT_RUN",
                )
            ),
            "ledger_append_performed": bool(
                state.get(
                    "ledger_append_performed",
                    False,
                )
            ),
            "ledger_idempotent_duplicate": bool(
                state.get(
                    "ledger_idempotent_duplicate",
                    False,
                )
            ),
        },
        "ledger": {
            "true_forward_count_before": (
                before
            ),
            "true_forward_count_after": (
                after
            ),
            "new_true_forward_observations_added": (
                delta
            ),
            "current_integrity_verified": (
                ledger_now.get(
                    "integrity_verified",
                    False,
                )
            ),
        },
        "forward_performance_evaluated": False,
        "outcome_horizon_contract_status": (
            OUTCOME_HORIZON_CONTRACT_STATUS
        ),
        "live_authorized": False,
        "execution_authorized": False,
        "validation_partition_accessed": False,
        "test_partition_accessed": False,
        "broker_write_calls": 0,
        "risk_engine_dependencies": 0,
        "trade_ready_dependencies": 0,
        "execution_dependencies": 0,
    }

    try:
        write_json_atomic_enough_for_evidence(
            BLOCKED_EVIDENCE_PATH,
            blocked,
        )

    except Exception:
        pass

    return blocked


# =============================================================================
# Main Gate
# =============================================================================

def run_gate(
    state: dict[str, Any],
) -> dict[str, Any]:

    # -------------------------------------------------------------------------
    # 1. Repository / frozen authority
    # -------------------------------------------------------------------------

    repository = (
        verify_repository_authority()
    )

    state[
        "repository_authority"
    ] = repository

    # -------------------------------------------------------------------------
    # 2. Static safety
    # -------------------------------------------------------------------------

    safety = (
        static_safety_audit()
    )

    state[
        "static_safety"
    ] = safety

    # -------------------------------------------------------------------------
    # 3. Runtime/model compatibility
    # -------------------------------------------------------------------------

    runtime_authority = (
        verify_runtime_authority()
    )

    state[
        "runtime_authority"
    ] = runtime_authority

    # -------------------------------------------------------------------------
    # 4. Existing append-only ledger
    # -------------------------------------------------------------------------

    ledger = (
        FrozenC04ObservationLedger(
            ledger_path=(
                LEDGER_PATH
            ),
            duplicate_handling=(
                DuplicateHandling
                .IDEMPOTENT_IGNORE
            ),
        )
    )

    require(
        ledger.validate_integrity(),
        (
            "PRE_ACQUISITION_LEDGER_"
            "INTEGRITY_FAILED"
        ),
    )

    total_count_before = (
        ledger.count()
    )

    true_count_before = (
        true_forward_count(
            ledger
        )
    )

    state[
        "total_count_before"
    ] = total_count_before

    state[
        "true_forward_count_before"
    ] = true_count_before

    initialized = False

    try:

        # ---------------------------------------------------------------------
        # 5. Raw MT5 lifecycle only
        # ---------------------------------------------------------------------

        initialized = bool(
            mt5.initialize()
        )

        state[
            "mt5_initialized"
        ] = initialized

        require(
            initialized,
            "MT5_INITIALIZE_FAILED",
        )

        # ---------------------------------------------------------------------
        # 6. Immediate read-only capability boundary
        # ---------------------------------------------------------------------

        read_only_api = (
            MT5ReadOnlyCapabilityFacade(
                mt5
            )
        )

        # ---------------------------------------------------------------------
        # 7. Gate 15B-A v2.1 genuine acquisition authority
        # ---------------------------------------------------------------------

        acquisition = (
            MT5ReadOnlyForwardAcquisitionAdapter(
                read_only_api,
                is_synthetic=False,
                include_native_d1=False,
                # AUTO is the accepted fail-closed policy:
                # exactly one timestamp basis must be proven.
                timestamp_basis="AUTO",
            )
        )

        broker_symbol = (
            acquisition
            .resolve_broker_symbol()
        )

        require(
            broker_symbol
            in set(
                SUPPORTED_SYMBOLS
            ),
            (
                "GATE_15B_A_RESOLVED_"
                "UNSUPPORTED_SYMBOL:"
                f"{broker_symbol}"
            ),
        )

        state[
            "resolved_broker_symbol"
        ] = broker_symbol

        # Bid/ask only. No raw timestamp freshness inference here.
        bid_ask = (
            verify_bid_ask(
                read_only_api,
                broker_symbol,
            )
        )

        snapshot = (
            acquisition.acquire_snapshot(
                enforce_forward_boundaries=True
            )
        )

        require(
            snapshot.is_synthetic
            is False,
            "SNAPSHOT_MUST_BE_GENUINE",
        )

        require(
            snapshot.broker_symbol
            == broker_symbol,
            (
                "BROKER_SYMBOL_CHANGED:"
                f"resolved={broker_symbol};"
                f"acquisition="
                f"{snapshot.broker_symbol}"
            ),
        )

        require(
            snapshot.authority
            is not None,
            (
                "VERIFIED_FORWARD_"
                "AUTHORITY_MISSING"
            ),
        )

        require(
            snapshot.authority
            .is_valid_authority(),
            (
                "VERIFIED_FORWARD_"
                "AUTHORITY_INVALID"
            ),
        )

        require(
            snapshot.attestation
            .verify_integrity(),
            (
                "ACQUISITION_ATTESTATION_"
                "INTEGRITY_FAILED"
            ),
        )

        verified_attestation = (
            verify_forward_acquisition_authority(
                snapshot.authority,
                expected_decision_time_utc=(
                    snapshot.decision_time_utc
                ),
                expected_source_snapshot_id=(
                    snapshot.source_snapshot_id
                ),
                expected_canonical_instrument=(
                    snapshot.canonical_instrument
                ),
                expected_feature_columns_sha256=(
                    EXPECTED_FEATURE_COLUMNS_SHA256
                ),
                expected_model_sha256=(
                    FROZEN_MODEL_SHA256
                ),
            )
        )

        require(
            verified_attestation.schema_version
            == "2.1.0",
            (
                "VERIFIED_ATTESTATION_"
                "SCHEMA_NOT_2_1_0"
            ),
        )

        require(
            verified_attestation
            .acquisition_authority
            == (
                "MT5ReadOnlyForwardAcquisitionAdapter:"
                "2.1.0"
            ),
            (
                "VERIFIED_ATTESTATION_"
                "AUTHORITY_ID_MISMATCH"
            ),
        )

        freshness = (
            verify_attested_freshness(
                verified_attestation
            )
        )

        state[
            "genuine_mt5_acquisition"
        ] = True

        state[
            "verified_forward_authority"
        ] = True

        state[
            "time_basis_policy"
        ] = (
            verified_attestation
            .time_basis_policy
        )

        state[
            "normalized_reference_tick_utc"
        ] = (
            verified_attestation
            .time_basis_reference_tick_utc
        )

        state[
            "decision_time_utc"
        ] = (
            snapshot.decision_time_utc
        )

        state[
            "source_snapshot_id"
        ] = (
            snapshot.source_snapshot_id
        )

        # ---------------------------------------------------------------------
        # 8. Representation-only pandas normalization
        # ---------------------------------------------------------------------

        (
            normalized_market_data,
            timestamp_dtypes_before,
            timestamp_dtypes_after,
        ) = (
            normalize_market_timestamp_resolution(
                snapshot.market_data
            )
        )

        normalized_snapshot_id = (
            compute_canonical_snapshot_id(
                normalized_market_data
            )
        )

        require(
            normalized_snapshot_id
            == snapshot.source_snapshot_id,
            (
                "TIMESTAMP_RESOLUTION_"
                "NORMALIZATION_CHANGED_"
                "SOURCE_SNAPSHOT_ID:"
                f"{normalized_snapshot_id}!="
                f"{snapshot.source_snapshot_id}"
            ),
        )

        # ---------------------------------------------------------------------
        # 9. Gate 13 — frozen exact 331 features
        # ---------------------------------------------------------------------

        feature_result = (
            PortableFeaturePipeline()
            .generate(
                normalized_market_data,
                symbol=(
                    snapshot
                    .canonical_instrument
                ),
            )
        )

        require(
            feature_result.feature_count
            == EXPECTED_FEATURE_COUNT,
            "GATE_13_FEATURE_COUNT_MISMATCH",
        )

        require(
            feature_result
            .feature_columns_sha256
            == EXPECTED_FEATURE_COLUMNS_SHA256,
            "GATE_13_FEATURE_SHA_MISMATCH",
        )

        require(
            feature_result.row_count
            > 0,
            "GATE_13_NO_VALID_FEATURE_ROWS",
        )

        latest_feature_time = (
            utc_iso(
                feature_result
                .decision_times
                .iloc[-1]
            )
        )

        require(
            latest_feature_time
            == snapshot.decision_time_utc,
            (
                "LATEST_CAUSAL_FEATURE_ROW_"
                "DOES_NOT_MATCH_ATTESTED_"
                "DECISION_TIME:"
                f"{latest_feature_time}!="
                f"{snapshot.decision_time_utc}"
            ),
        )

        # Recheck on normalized true UTC, never broker raw time.
        decision_ts = utc_timestamp(
            snapshot.decision_time_utc
        )

        machine_now = pd.Timestamp.now(
            tz="UTC"
        )

        require(
            decision_ts
            <= (
                machine_now
                + pd.Timedelta(
                    seconds=(
                        DEFAULT_MAX_FUTURE_TICK_SKEW_SECONDS
                    )
                )
            ),
            (
                "ATTESTED_DECISION_TIME_IS_FUTURE:"
                f"decision={utc_iso(decision_ts)};"
                f"now={utc_iso(machine_now)}"
            ),
        )

        normalized_tick_ts = (
            utc_timestamp(
                verified_attestation
                .time_basis_reference_tick_utc
            )
        )

        require(
            decision_ts
            <= normalized_tick_ts,
            (
                "DECISION_TIME_AFTER_"
                "NORMALIZED_REFERENCE_TICK"
            ),
        )

        state[
            "gate13_status"
        ] = "PASS"

        # ---------------------------------------------------------------------
        # 10. Gate 14 + Gate 15A
        # ---------------------------------------------------------------------

        observer = (
            FrozenC04ShadowObserver(
                canonical_instrument=(
                    snapshot
                    .canonical_instrument
                ),
                broker_symbol=(
                    snapshot
                    .broker_symbol
                ),
            )
        )

        observation = (
            observer.observe_single(
                feature_row=(
                    feature_result
                    .features
                    .iloc[-1]
                ),
                decision_time_utc=(
                    snapshot
                    .decision_time_utc
                ),
                source_snapshot_id=(
                    snapshot
                    .source_snapshot_id
                ),
                source_provenance=(
                    SourceProvenance
                    .TRUE_FORWARD_OBSERVATION
                ),
                acquisition_authority=(
                    snapshot.authority
                ),
            )
        )

        require(
            observation.source_provenance
            == (
                SourceProvenance
                .TRUE_FORWARD_OBSERVATION
                .value
            ),
            (
                "OBSERVATION_PROVENANCE_"
                "NOT_TRUE_FORWARD"
            ),
        )

        require(
            observation
            .is_true_forward_eligible
            is True,
            (
                "TRUE_FORWARD_"
                "ELIGIBILITY_FAILED"
            ),
        )

        require(
            observation.live_authorized
            is False,
            (
                "LIVE_AUTHORIZED_"
                "MUST_REMAIN_FALSE"
            ),
        )

        require(
            observation
            .execution_authorized
            is False,
            (
                "EXECUTION_AUTHORIZED_"
                "MUST_REMAIN_FALSE"
            ),
        )

        require(
            observation.model_sha256
            == FROZEN_MODEL_SHA256,
            "GATE_14_MODEL_SHA_MISMATCH",
        )

        require(
            observation
            .feature_columns_sha256
            == (
                EXPECTED_FEATURE_COLUMNS_SHA256
            ),
            (
                "OBSERVATION_FEATURE_"
                "SHA_MISMATCH"
            ),
        )

        require(
            observation.decision_time_utc
            == snapshot.decision_time_utc,
            (
                "OBSERVATION_DECISION_"
                "TIME_MISMATCH"
            ),
        )

        require(
            observation.source_snapshot_id
            == snapshot.source_snapshot_id,
            (
                "OBSERVATION_SOURCE_"
                "SNAPSHOT_MISMATCH"
            ),
        )

        state[
            "gate14_status"
        ] = "PASS"

        state[
            "gate15a_status"
        ] = "PASS"

        # ---------------------------------------------------------------------
        # 11. Append one latest genuine observation / idempotent retry
        # ---------------------------------------------------------------------

        append_result = (
            ledger.append(
                observation
            )
        )

        state[
            "ledger_append_performed"
        ] = bool(
            append_result.appended
        )

        state[
            "ledger_idempotent_duplicate"
        ] = bool(
            append_result.is_duplicate
        )

        require(
            ledger.validate_integrity(),
            (
                "POST_APPEND_LEDGER_"
                "INTEGRITY_FAILED"
            ),
        )

        total_count_after = (
            ledger.count()
        )

        true_count_after = (
            true_forward_count(
                ledger
            )
        )

        new_true_forward = (
            true_count_after
            - true_count_before
        )

        state[
            "total_count_after"
        ] = total_count_after

        state[
            "true_forward_count_after"
        ] = true_count_after

        state[
            "new_true_forward_observations_added"
        ] = new_true_forward

        require(
            new_true_forward
            in {
                0,
                1,
            },
            (
                "UNEXPECTED_TRUE_FORWARD_"
                "COUNT_DELTA:"
                f"{new_true_forward}"
            ),
        )

        require(
            append_result.appended
            or append_result.is_duplicate,
            (
                "LEDGER_APPEND_RESULT_"
                "NEITHER_APPEND_NOR_DUPLICATE"
            ),
        )

        if append_result.appended:
            require(
                new_true_forward
                == 1,
                (
                    "APPEND_DID_NOT_INCREASE_"
                    "TRUE_FORWARD_COUNT"
                ),
            )

        if append_result.is_duplicate:
            require(
                new_true_forward
                == 0,
                (
                    "IDEMPOTENT_DUPLICATE_CHANGED_"
                    "TRUE_FORWARD_COUNT"
                ),
            )

        # ---------------------------------------------------------------------
        # 12. PASS evidence
        # ---------------------------------------------------------------------

        evidence: dict[
            str,
            Any,
        ] = {
            "gate": (
                "Gate 15B-B — First Genuine "
                "Read-Only Forward Observation"
            ),
            "gate_id": GATE_ID,
            "schema_version": (
                SCHEMA_VERSION
            ),
            "generated_at_utc": (
                now_utc_iso()
            ),
            "status": "PASS",
            "git": {
                "gate_15b_a_authority_commit": (
                    GATE_15B_A_AUTHORITY_COMMIT
                ),
                "execution_head": (
                    repository[
                        "execution_head"
                    ]
                ),
                "origin_main": (
                    repository[
                        "origin_main"
                    ]
                ),
                "head_equals_origin_main": True,
                "gate_15b_a_authority_is_ancestor": True,
                "allowed_post_authority_tracked_paths_only": True,
            },
            "repository_authority": (
                repository
            ),
            "runtime_authority": (
                runtime_authority
            ),
            "canonical_instrument": (
                snapshot
                .canonical_instrument
            ),
            "resolved_broker_symbol": (
                snapshot
                .broker_symbol
            ),
            "symbol_resolution_authority": (
                "GATE_15B_A_V2_1_"
                "EXACT_SUPPORTED_SYMBOL"
            ),
            "acquisition_authority": (
                verified_attestation
                .acquisition_authority
            ),
            "acquisition_schema_version": (
                verified_attestation
                .schema_version
            ),
            "acquisition_time_utc": (
                verified_attestation
                .acquisition_time_utc
            ),
            "decision_time_utc": (
                snapshot
                .decision_time_utc
            ),
            "source_snapshot_id": (
                snapshot
                .source_snapshot_id
            ),
            "logical_observation_id": (
                observation
                .logical_observation_id
            ),
            "semantic_record_fingerprint": (
                observation
                .semantic_record_fingerprint
            ),
            "feature_columns_sha256": (
                EXPECTED_FEATURE_COLUMNS_SHA256
            ),
            "model_sha256": (
                FROZEN_MODEL_SHA256
            ),
            "capability_manifest": list(
                verified_attestation
                .capability_manifest
            ),
            "closed_bar_enforced": True,
            "forming_bar_start_pos_zero_used": False,
            "bid_ask_validation": (
                bid_ask
            ),
            "market_freshness": (
                freshness
            ),
            "time_basis": {
                "policy": (
                    verified_attestation
                    .time_basis_policy
                ),
                "reference_tick_raw": (
                    verified_attestation
                    .time_basis_reference_tick_raw
                ),
                "reference_tick_utc": (
                    verified_attestation
                    .time_basis_reference_tick_utc
                ),
                "reference_offset_seconds": (
                    verified_attestation
                    .time_basis_reference_offset_seconds
                ),
                "reference_tick_age_seconds": (
                    verified_attestation
                    .time_basis_reference_tick_age_seconds
                ),
                "historical_normalization": (
                    "GATE_15B_A_V2_1_PER_ROW"
                ),
                "manual_fixed_offset_used_by_gate_15b_b": False,
            },
            "timestamp_resolution_normalization": {
                "status": "PASS",
                "policy": (
                    "PANDAS_STORAGE_"
                    "RESOLUTION_ONLY_UTC_NANOSECONDS"
                ),
                "dtypes_before": (
                    timestamp_dtypes_before
                ),
                "dtypes_after": (
                    timestamp_dtypes_after
                ),
                "source_snapshot_id_before": (
                    snapshot
                    .source_snapshot_id
                ),
                "source_snapshot_id_after": (
                    normalized_snapshot_id
                ),
                "source_snapshot_identity_preserved": True,
            },
            "gate13": {
                "status": "PASS",
                "feature_count": (
                    feature_result
                    .feature_count
                ),
                "feature_columns_sha256": (
                    feature_result
                    .feature_columns_sha256
                ),
                "row_count": (
                    feature_result
                    .row_count
                ),
                "latest_feature_decision_time_utc": (
                    latest_feature_time
                ),
                "d1_source": (
                    feature_result
                    .d1_source
                ),
            },
            "gate14": {
                "status": "PASS",
                "model_sha256": (
                    observation
                    .model_sha256
                ),
                "inference_status": (
                    observation
                    .inference_status
                ),
            },
            "gate15a": {
                "status": "PASS",
                "observation_status": (
                    observation
                    .observation_status
                ),
                "source_provenance": (
                    observation
                    .source_provenance
                ),
                "is_true_forward_eligible": (
                    observation
                    .is_true_forward_eligible
                ),
            },
            "verified_forward_authority": True,
            "genuine_mt5_acquisition": True,
            "is_synthetic": False,
            "historical_replay": False,
            "ledger": {
                "total_count_before": (
                    total_count_before
                ),
                "total_count_after": (
                    total_count_after
                ),
                "true_forward_count_before": (
                    true_count_before
                ),
                "true_forward_count_after": (
                    true_count_after
                ),
                "new_true_forward_observations_added": (
                    new_true_forward
                ),
                "append_performed": (
                    append_result.appended
                ),
                "idempotent_duplicate": (
                    append_result.is_duplicate
                ),
                "integrity_verified": True,
                "runtime_ledger_committable": False,
            },
            "outcome_horizon_contract_status": (
                OUTCOME_HORIZON_CONTRACT_STATUS
            ),
            "forward_performance_evaluated": False,
            "live_authorized": False,
            "execution_authorized": False,
            "validation_partition_accessed": False,
            "test_partition_accessed": False,
            "broker_write_calls": 0,
            "risk_engine_dependencies": 0,
            "trade_ready_dependencies": 0,
            "execution_dependencies": 0,
            "static_safety": (
                safety
            ),
            "gate_15b_a_v2_1_authority": (
                repository[
                    "gate_15b_a_v2_1"
                ]
            ),
        }

        write_json_atomic_enough_for_evidence(
            PASS_EVIDENCE_PATH,
            evidence,
        )

        return evidence

    finally:
        if initialized:
            try:
                mt5.shutdown()

            except Exception:
                pass


# =============================================================================
# Entrypoint
# =============================================================================

def main() -> int:
    state = initial_run_state()

    try:
        result = run_gate(
            state
        )

        ledger_data = result[
            "ledger"
        ]

        recorded = bool(
            ledger_data[
                "append_performed"
            ]
            or ledger_data[
                "idempotent_duplicate"
            ]
        )

        print()
        print(
            "=" * 79
        )
        print(
            "PULSEVIPER XAU AI — GATE 15B-B"
        )
        print(
            "=" * 79
        )
        print(
            "STATUS: PASS"
        )
        print(
            "GENUINE_MT5_ACQUISITION: true"
        )
        print(
            "Resolved Broker Symbol:",
            result[
                "resolved_broker_symbol"
            ],
        )
        print(
            "Time Basis Policy:",
            result[
                "time_basis"
            ][
                "policy"
            ],
        )
        print(
            "Normalized Tick UTC:",
            result[
                "time_basis"
            ][
                "reference_tick_utc"
            ],
        )
        print(
            "Decision Time UTC:",
            result[
                "decision_time_utc"
            ],
        )
        print(
            "Tick Age Seconds:",
            result[
                "market_freshness"
            ][
                "tick_age_seconds"
            ],
        )
        print(
            "TRUE_FORWARD count before:",
            ledger_data[
                "true_forward_count_before"
            ],
        )
        print(
            "TRUE_FORWARD count after:",
            ledger_data[
                "true_forward_count_after"
            ],
        )
        print(
            "New TRUE_FORWARD observations:",
            ledger_data[
                "new_true_forward_observations_added"
            ],
        )
        print(
            "Idempotent duplicate:",
            ledger_data[
                "idempotent_duplicate"
            ],
        )
        print(
            "=" * 79
        )
        print()

        print(
            "GATE_15B_B_STATUS=PASS"
        )

        print(
            "GENUINE_MT5_ACQUISITION=true"
        )

        print(
            "TRUE_FORWARD_OBSERVATION_RECORDED="
            + (
                "true"
                if recorded
                else "false"
            )
        )

        print(
            "TRUE_FORWARD_COUNT_BEFORE="
            + str(
                ledger_data[
                    "true_forward_count_before"
                ]
            )
        )

        print(
            "TRUE_FORWARD_COUNT_AFTER="
            + str(
                ledger_data[
                    "true_forward_count_after"
                ]
            )
        )

        print(
            "NEW_TRUE_FORWARD_OBSERVATIONS_ADDED="
            + str(
                ledger_data[
                    "new_true_forward_observations_added"
                ]
            )
        )

        print(
            "TIME_BASIS_POLICY="
            + str(
                result[
                    "time_basis"
                ][
                    "policy"
                ]
            )
        )

        print(
            "NORMALIZED_REFERENCE_TICK_UTC="
            + str(
                result[
                    "time_basis"
                ][
                    "reference_tick_utc"
                ]
            )
        )

        print(
            "FORWARD_PERFORMANCE_EVALUATED=false"
        )

        print(
            "OUTCOME_HORIZON_CONTRACT_STATUS="
            + OUTCOME_HORIZON_CONTRACT_STATUS
        )

        print(
            "LIVE_AUTHORIZED=false"
        )

        print(
            "EXECUTION_AUTHORIZED=false"
        )

        print(
            "HEAD_EQUALS_ORIGIN_MAIN=true"
        )

        print(
            "WORKING_TREE_CLEAN="
            + (
                "true"
                if working_tree_clean()
                else "false"
            )
        )

        return 0

    except Exception as exc:
        blocked = (
            write_blocked_evidence(
                exc,
                state,
            )
        )

        ledger_data = blocked[
            "ledger"
        ]

        git_data = blocked[
            "git"
        ]

        progress = blocked[
            "progress_before_block"
        ]

        before = ledger_data.get(
            "true_forward_count_before"
        )

        after = ledger_data.get(
            "true_forward_count_after"
        )

        delta = ledger_data.get(
            "new_true_forward_observations_added"
        )

        recorded = bool(
            (
                isinstance(
                    before,
                    int,
                )
                and isinstance(
                    after,
                    int,
                )
                and before >= 0
                and after >= 0
                and after > before
            )
            or bool(
                progress.get(
                    "ledger_idempotent_duplicate",
                    False,
                )
            )
        )

        try:
            clean = working_tree_clean()

        except Exception:
            clean = False

        print()
        print(
            "=" * 79
        )
        print(
            "PULSEVIPER XAU AI — GATE 15B-B"
        )
        print(
            "=" * 79
        )
        print(
            "STATUS: BLOCKED"
        )
        print(
            "Error Type:",
            blocked[
                "reason"
            ][
                "error_type"
            ],
        )
        print(
            "Reason:",
            blocked[
                "reason"
            ][
                "error_text"
            ],
        )
        print(
            "No trading action was authorized."
        )
        print(
            "No performance evaluation was performed."
        )
        print(
            "=" * 79
        )
        print()

        print(
            "GATE_15B_B_STATUS=BLOCKED"
        )

        print(
            "GENUINE_MT5_ACQUISITION="
            + (
                "true"
                if progress.get(
                    "genuine_mt5_acquisition"
                )
                else "false"
            )
        )

        print(
            "TRUE_FORWARD_OBSERVATION_RECORDED="
            + (
                "true"
                if recorded
                else "false"
            )
        )

        print(
            "TRUE_FORWARD_COUNT_BEFORE="
            + str(
                before
                if before is not None
                else -1
            )
        )

        print(
            "TRUE_FORWARD_COUNT_AFTER="
            + str(
                after
                if after is not None
                else -1
            )
        )

        print(
            "NEW_TRUE_FORWARD_OBSERVATIONS_ADDED="
            + str(
                delta
                if delta is not None
                else 0
            )
        )

        print(
            "TIME_BASIS_POLICY="
            + str(
                progress.get(
                    "time_basis_policy"
                )
            )
        )

        print(
            "NORMALIZED_REFERENCE_TICK_UTC="
            + str(
                progress.get(
                    "normalized_reference_tick_utc"
                )
            )
        )

        print(
            "FORWARD_PERFORMANCE_EVALUATED=false"
        )

        print(
            "OUTCOME_HORIZON_CONTRACT_STATUS="
            + OUTCOME_HORIZON_CONTRACT_STATUS
        )

        print(
            "LIVE_AUTHORIZED=false"
        )

        print(
            "EXECUTION_AUTHORIZED=false"
        )

        print(
            "HEAD_EQUALS_ORIGIN_MAIN="
            + (
                "true"
                if git_data.get(
                    "head_equals_origin_main"
                )
                else "false"
            )
        )

        print(
            "WORKING_TREE_CLEAN="
            + (
                "true"
                if clean
                else "false"
            )
        )

        return 2


if __name__ == "__main__":
    raise SystemExit(
        main()
    )