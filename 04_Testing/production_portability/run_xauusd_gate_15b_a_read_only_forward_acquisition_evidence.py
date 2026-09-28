"""
===============================================================================
Module      : run_xauusd_gate_15b_a_read_only_forward_acquisition_evidence.py
Project     : PulseViper XAU AI
Purpose     : Gate 15B-A v2.1 Authority-Regeneration Evidence Runner
===============================================================================

OFFLINE / SYNTHETIC authority-regeneration runner.

This runner:
- does NOT initialize MT5
- does NOT append to the TRUE_FORWARD ledger
- does NOT authorize live trading or execution
- does NOT evaluate forward performance
- does NOT inspect outcomes
- does NOT retrain/refit/calibrate/tune/reselect the frozen model

It proves:
- accepted Gate 15B-A baseline ancestry is preserved
- committed changes since the accepted baseline remain allowlisted
- current local Gate 15B-A candidate changes are explicit and allowlisted
- production read-only acquisition code contains no forbidden broker-write calls
- the facade blocks the full required mutating/order API set
- targeted Gate 15B-A tests pass
- scikit-learn runtime matches frozen model serialization version
- UNIX_UTC policy remains valid
- NY-close server-wall-clock policy is DST-aware per historical row
- Gate 13 exact 331-feature contract is preserved
- synthetic data cannot escalate to TRUE_FORWARD provenance
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
from typing import Any, cast

import pandas as pd
import sklearn


REPO_ROOT: Path = Path(__file__).resolve().parents[2]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(REPO_ROOT),
    )


# =============================================================================
# Authorities
# =============================================================================

_acq_mod = importlib.import_module(
    "02_AI.Adapters.mt5_read_only_forward_acquisition_adapter"
)

_pipeline_mod = importlib.import_module(
    "02_AI.Features.portable_feature_pipeline"
)

_observer_mod = importlib.import_module(
    "02_AI.Models.frozen_c04_shadow_observer"
)

_test_mod = importlib.import_module(
    "04_Testing.production_portability.test_mt5_read_only_forward_acquisition_adapter"
)


MT5ReadOnlyCapabilityFacade = (
    _acq_mod.MT5ReadOnlyCapabilityFacade
)

MT5ReadOnlyForwardAcquisitionAdapter = (
    _acq_mod.MT5ReadOnlyForwardAcquisitionAdapter
)

TIME_BASIS_UNIX_UTC: str = str(
    _acq_mod.TIME_BASIS_UNIX_UTC
)

TIME_BASIS_NY_CLOSE_SERVER: str = str(
    _acq_mod.TIME_BASIS_NY_CLOSE_SERVER
)

ACQUISITION_SCHEMA_VERSION: str = str(
    _acq_mod.ACQUISITION_SCHEMA_VERSION
)

ACQUISITION_AUTHORITY_ID: str = str(
    _acq_mod.ACQUISITION_AUTHORITY_ID
)

EXPECTED_FEATURE_COLUMNS_SHA256: str = str(
    _acq_mod.EXPECTED_FEATURE_COLUMNS_SHA256
)

FROZEN_MODEL_SHA256: str = str(
    _acq_mod.FROZEN_MODEL_SHA256
)

normalize_ny_close_server_epoch: Any = (
    _acq_mod.normalize_ny_close_server_epoch
)

PortableFeaturePipeline = (
    _pipeline_mod.PortableFeaturePipeline
)

SourceProvenance = (
    _observer_mod.SourceProvenance
)

FrozenC04ShadowObserver = (
    _observer_mod.FrozenC04ShadowObserver
)

TrueForwardAcquisitionNotAuthorizedError = (
    _observer_mod.TrueForwardAcquisitionNotAuthorizedError
)

MockMT5Session = (
    _test_mod.MockMT5Session
)

_epoch = (
    _test_mod._epoch
)


# =============================================================================
# Frozen / Accepted Authorities
# =============================================================================

ACCEPTED_GATE_15B_A_BASELINE: str = (
    "58b12b8d6e5cdb69acb3e9c4cd5c19cd744d30c5"
)

EXPECTED_SKLEARN_VERSION: str = "1.9.0"

EVIDENCE_OUTPUT_PATH: Path = (
    REPO_ROOT
    / "04_Testing"
    / "evidence"
    / "forward_shadow"
    / "xauusd_gate_15b_a_read_only_forward_acquisition_evidence.json"
)


ALLOWED_COMMITTED_PATHS_SINCE_BASELINE: frozenset[str] = frozenset(
    {
        ".github/ISSUE_TEMPLATE/bug_report.md",
        ".github/ISSUE_TEMPLATE/feature_request.md",
        ".github/pull_request_template.md",
        "CODE_OF_CONDUCT.md",
        "CONTRIBUTING.md",
        "README.md",
        "SECURITY.md",

        # Formally reopened Gate 15B-A v2.1 authority paths.
        "02_AI/Adapters/mt5_read_only_forward_acquisition_adapter.py",
        "04_Testing/production_portability/test_mt5_read_only_forward_acquisition_adapter.py",
        "04_Testing/production_portability/run_xauusd_gate_15b_a_read_only_forward_acquisition_evidence.py",
    }
)


REOPENED_GATE_PATHS: frozenset[str] = frozenset(
    {
        "02_AI/Adapters/mt5_read_only_forward_acquisition_adapter.py",
        "04_Testing/production_portability/test_mt5_read_only_forward_acquisition_adapter.py",
        "04_Testing/production_portability/run_xauusd_gate_15b_a_read_only_forward_acquisition_evidence.py",
        "04_Testing/evidence/forward_shadow/xauusd_gate_15b_a_read_only_forward_acquisition_evidence.json",
    }
)


ALLOWED_EXISTING_GATE_15B_B_WORK_PRODUCTS: frozenset[str] = frozenset(
    {
        "04_Testing/evidence/forward_shadow/xauusd_gate_15b_b_first_genuine_forward_observation_blocked.json",
        "04_Testing/production_portability/diagnose_xauusd_icmarkets_server_time_history.py",
        "04_Testing/production_portability/run_xauusd_gate_15b_b_genuine_forward_observation.py",
    }
)


FORBIDDEN_EXECUTION_DEPENDENCIES: frozenset[str] = frozenset(
    {
        "RiskEngine",
        "broker_aware_risk_engine",
        "account_protection_guard",
        "trade_ready",
    }
)


FORBIDDEN_BROKER_CALLS: frozenset[str] = frozenset(
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
        "history_deals_get",
    }
)


# =============================================================================
# Git Utilities
# =============================================================================

def _git(
    *args: str,
) -> str:
    result = subprocess.run(
        [
            "git",
            *args,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "GIT_COMMAND_FAILED:"
            + " ".join(args)
            + ":"
            + result.stderr.strip()
        )

    return result.stdout.rstrip("\r\n")


def _git_status_paths() -> list[str]:
    output = _git(
        "status",
        "--porcelain",
    )

    paths: list[str] = []

    for line in output.splitlines():
        if len(line) < 4:
            continue

        path = line[3:].strip()

        if " -> " in path:
            path = path.split(
                " -> ",
                1,
            )[1]

        if (
            path.startswith('"')
            and path.endswith('"')
        ):
            path = path[1:-1]

        paths.append(
            path.replace("\\", "/")
        )

    return paths


def verify_git_authority() -> dict[str, Any]:
    head = _git(
        "rev-parse",
        "HEAD",
    )

    origin_main = _git(
        "rev-parse",
        "origin/main",
    )

    ancestor_process = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            ACCEPTED_GATE_15B_A_BASELINE,
            "HEAD",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    baseline_is_ancestor = bool(
        ancestor_process.returncode == 0
    )

    committed_output = _git(
        "diff",
        "--name-only",
        f"{ACCEPTED_GATE_15B_A_BASELINE}..HEAD",
    )

    committed_paths = {
        line.strip().replace("\\", "/")
        for line in committed_output.splitlines()
        if line.strip()
    }

    unexpected_committed_paths = sorted(
        committed_paths
        - set(
            ALLOWED_COMMITTED_PATHS_SINCE_BASELINE
        )
    )

    local_paths = set(
        _git_status_paths()
    )

    allowed_local_paths = set(
        REOPENED_GATE_PATHS
    ) | set(
        ALLOWED_EXISTING_GATE_15B_B_WORK_PRODUCTS
    )

    unexpected_local_paths = sorted(
        local_paths
        - allowed_local_paths
    )

    head_equals_origin_main = bool(
        head == origin_main
    )

    passed = bool(
        head_equals_origin_main
        and baseline_is_ancestor
        and not unexpected_committed_paths
        and not unexpected_local_paths
    )

    return {
        "status": (
            "PASS"
            if passed
            else "FAIL"
        ),
        "head": head,
        "origin_main": origin_main,
        "head_equals_origin_main": (
            head_equals_origin_main
        ),
        "accepted_baseline": (
            ACCEPTED_GATE_15B_A_BASELINE
        ),
        "accepted_baseline_is_ancestor": (
            baseline_is_ancestor
        ),
        "committed_paths_since_baseline": sorted(
            committed_paths
        ),
        "unexpected_committed_paths": (
            unexpected_committed_paths
        ),
        "local_worktree_paths": sorted(
            local_paths
        ),
        "allowed_local_worktree_paths": sorted(
            allowed_local_paths
        ),
        "unexpected_local_paths": (
            unexpected_local_paths
        ),
    }


# =============================================================================
# Inherited Baseline Authority
# =============================================================================

def verify_inherited_baseline_authority() -> dict[str, Any]:
    return {
        "status": "PASS",
        "verification_mode": (
            "INHERITED_ACCEPTED_AUTHORITY"
        ),
        "accepted_baseline_commit": (
            ACCEPTED_GATE_15B_A_BASELINE
        ),
        "previous_verified_count": 41,
        "previous_total_count": 41,
        "fresh_41_file_rehash_performed": False,
        "reopened_gate_paths": sorted(
            REOPENED_GATE_PATHS
        ),
        "note": (
            "Previous 41/41 integrity authority is inherited. "
            "Reopened Gate 15B-A files are validated separately."
        ),
    }


# =============================================================================
# Static Safety
# =============================================================================

def _audit_production_python_file(
    path: Path,
) -> list[dict[str, str]]:
    source = path.read_text(
        encoding="utf-8"
    )

    tree = ast.parse(
        source
    )

    violations: list[
        dict[str, str]
    ] = []

    relative_path = str(
        path.relative_to(
            REPO_ROOT
        )
    ).replace(
        "\\",
        "/",
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
                    in FORBIDDEN_EXECUTION_DEPENDENCIES
                ):
                    violations.append(
                        {
                            "file": relative_path,
                            "type": "forbidden_import",
                            "symbol": alias.name,
                        }
                    )

        elif isinstance(
            node,
            ast.ImportFrom,
        ):
            if (
                node.module
                in FORBIDDEN_EXECUTION_DEPENDENCIES
            ):
                violations.append(
                    {
                        "file": relative_path,
                        "type": "forbidden_import_from",
                        "symbol": str(
                            node.module
                        ),
                    }
                )

            for alias in node.names:
                if (
                    alias.name
                    in FORBIDDEN_EXECUTION_DEPENDENCIES
                ):
                    violations.append(
                        {
                            "file": relative_path,
                            "type": "forbidden_import_alias",
                            "symbol": alias.name,
                        }
                    )

        elif isinstance(
            node,
            ast.Call,
        ):
            function = node.func

            call_name: str | None = None

            if isinstance(
                function,
                ast.Attribute,
            ):
                call_name = (
                    function.attr
                )

            elif isinstance(
                function,
                ast.Name,
            ):
                call_name = (
                    function.id
                )

            if (
                call_name is not None
                and call_name
                in FORBIDDEN_BROKER_CALLS
            ):
                violations.append(
                    {
                        "file": relative_path,
                        "type": "forbidden_broker_call",
                        "symbol": call_name,
                    }
                )

    return violations


def perform_static_safety_audit() -> dict[str, Any]:
    """
    Audit production-reachable Gate 15B-A code.

    Important:
    The unit test file is intentionally excluded from broker-call violation
    scanning because it deliberately calls facade.order_send(),
    facade.positions_get(), etc. to prove they raise PermissionError.
    Those negative tests are safety evidence, not production violations.
    """

    audited_paths = [
        (
            REPO_ROOT
            / "02_AI"
            / "Adapters"
            / "mt5_read_only_forward_acquisition_adapter.py"
        ),
        (
            REPO_ROOT
            / "04_Testing"
            / "production_portability"
            / "run_xauusd_gate_15b_a_read_only_forward_acquisition_evidence.py"
        ),
    ]

    violations: list[
        dict[str, str]
    ] = []

    for path in audited_paths:
        violations.extend(
            _audit_production_python_file(
                path
            )
        )

    facade_forbidden_methods = set(
        MT5ReadOnlyCapabilityFacade.FORBIDDEN_MUTATING_METHODS
    )

    facade_required_coverage = bool(
        set(
            FORBIDDEN_BROKER_CALLS
        )
        <= facade_forbidden_methods
    )

    passed = bool(
        not violations
        and facade_required_coverage
    )

    return {
        "status": (
            "PASS"
            if passed
            else "FAIL"
        ),
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
        "test_negative_calls_excluded_from_production_violation_scan": (
            True
        ),
        "violation_count": len(
            violations
        ),
        "violations": violations,
        "facade_required_mutating_methods_blocked": (
            facade_required_coverage
        ),
        "required_forbidden_broker_methods": sorted(
            FORBIDDEN_BROKER_CALLS
        ),
    }


# =============================================================================
# Runtime Environment Authority
# =============================================================================

def verify_sklearn_runtime() -> dict[str, Any]:
    actual_version = str(
        sklearn.__version__
    )

    passed = bool(
        actual_version
        == EXPECTED_SKLEARN_VERSION
    )

    return {
        "status": (
            "PASS"
            if passed
            else "FAIL"
        ),
        "expected_version": (
            EXPECTED_SKLEARN_VERSION
        ),
        "actual_version": (
            actual_version
        ),
        "frozen_model_runtime_compatible": (
            passed
        ),
        "model_unpickle_allowed": (
            passed
        ),
    }


# =============================================================================
# Targeted Tests
# =============================================================================

def run_targeted_pytest() -> dict[str, Any]:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "04_Testing/production_portability/"
            "test_mt5_read_only_forward_acquisition_adapter.py",
            "-q",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    return {
        "status": (
            "PASS"
            if result.returncode == 0
            else "FAIL"
        ),
        "return_code": (
            result.returncode
        ),
        "stdout": (
            result.stdout.strip()
        ),
        "stderr": (
            result.stderr.strip()
        ),
    }


# =============================================================================
# Timestamp Policies
# =============================================================================

def verify_unix_utc_policy() -> dict[str, Any]:
    base_epoch = int(
        _epoch(
            "2026-09-20T12:00:00Z"
        )
    )

    session = MockMT5Session(
        base_epoch=base_epoch,
        raw_tick_epoch=base_epoch,
        server_wall_clock=False,
    )

    adapter = MT5ReadOnlyForwardAcquisitionAdapter(
        session,
        is_synthetic=False,
        timestamp_basis=(
            TIME_BASIS_UNIX_UTC
        ),
        now_provider=(
            lambda: float(
                base_epoch
            )
        ),
    )

    snapshot = (
        adapter.acquire_snapshot()
    )

    authority_valid = bool(
        snapshot.authority is not None
        and snapshot.authority.is_valid_authority()
    )

    passed = bool(
        snapshot.attestation.time_basis_policy
        == TIME_BASIS_UNIX_UTC
        and authority_valid
    )

    return {
        "status": (
            "PASS"
            if passed
            else "FAIL"
        ),
        "time_basis_policy": (
            snapshot.attestation.time_basis_policy
        ),
        "decision_time_utc": (
            snapshot.decision_time_utc
        ),
        "authority_valid": (
            authority_valid
        ),
    }


def verify_ny_close_policy() -> dict[str, Any]:
    base_epoch = int(
        _epoch(
            "2026-09-20T12:00:00Z"
        )
    )

    raw_server_tick = (
        base_epoch
        + 10800
    )

    session = MockMT5Session(
        base_epoch=base_epoch,
        raw_tick_epoch=(
            raw_server_tick
        ),
        server_wall_clock=True,
    )

    adapter = MT5ReadOnlyForwardAcquisitionAdapter(
        session,
        is_synthetic=False,
        timestamp_basis=(
            TIME_BASIS_NY_CLOSE_SERVER
        ),
        now_provider=(
            lambda: float(
                base_epoch
            )
        ),
    )

    snapshot = (
        adapter.acquire_snapshot()
    )

    pipeline = (
        PortableFeaturePipeline()
    )

    feature_result = (
        pipeline.generate(
            snapshot.market_data,
            symbol=(
                snapshot.canonical_instrument
            ),
        )
    )

    winter_true = int(
        _epoch(
            "2026-03-08T06:00:00Z"
        )
    )

    summer_true = int(
        _epoch(
            "2026-03-09T06:00:00Z"
        )
    )

    (
        winter_normalized,
        winter_offset,
    ) = normalize_ny_close_server_epoch(
        winter_true
        + 7200
    )

    (
        summer_normalized,
        summer_offset,
    ) = normalize_ny_close_server_epoch(
        summer_true
        + 10800
    )

    passed = bool(
        snapshot.attestation.time_basis_policy
        == TIME_BASIS_NY_CLOSE_SERVER
        and snapshot.attestation.time_basis_reference_offset_seconds
        == 10800
        and int(
            winter_normalized.timestamp()
        )
        == winter_true
        and int(
            summer_normalized.timestamp()
        )
        == summer_true
        and winter_offset
        == 7200
        and summer_offset
        == 10800
        and feature_result.feature_count
        == 331
        and feature_result.feature_columns_sha256
        == EXPECTED_FEATURE_COLUMNS_SHA256
    )

    return {
        "status": (
            "PASS"
            if passed
            else "FAIL"
        ),
        "time_basis_policy": (
            snapshot.attestation.time_basis_policy
        ),
        "reference_offset_seconds": (
            snapshot.attestation.time_basis_reference_offset_seconds
        ),
        "winter_offset_seconds": (
            winter_offset
        ),
        "summer_offset_seconds": (
            summer_offset
        ),
        "feature_count": (
            feature_result.feature_count
        ),
        "feature_columns_sha256": (
            feature_result.feature_columns_sha256
        ),
        "decision_time_utc": (
            snapshot.decision_time_utc
        ),
    }


# =============================================================================
# Synthetic Gate 13 -> Gate 14 -> Gate 15A Isolation Proof
# =============================================================================

def verify_synthetic_pipeline() -> dict[str, Any]:
    session = MockMT5Session(
        base_epoch=1789000000,
    )

    adapter = (
        MT5ReadOnlyForwardAcquisitionAdapter(
            session,
            is_synthetic=True,
        )
    )

    snapshot = (
        adapter.acquire_snapshot()
    )

    pipeline = (
        PortableFeaturePipeline()
    )

    feature_result = (
        pipeline.generate(
            snapshot.market_data,
            symbol=(
                snapshot.canonical_instrument
            ),
        )
    )

    observer = (
        FrozenC04ShadowObserver(
            canonical_instrument=(
                snapshot.canonical_instrument
            )
        )
    )

    latest_feature_row = (
        feature_result.features.iloc[-1]
    )

    raw_decision_ts = pd.Timestamp(
        feature_result.decision_times.iloc[-1]
    )

    if raw_decision_ts is pd.NaT:
        raise RuntimeError(
            "SYNTHETIC_DECISION_TIMESTAMP_IS_NAT"
        )

    decision_ts = cast(
        pd.Timestamp,
        raw_decision_ts,
    )

    if decision_ts.tzinfo is None:
        localized = (
            decision_ts.tz_localize(
                "UTC"
            )
        )

        if localized is pd.NaT:
            raise RuntimeError(
                "SYNTHETIC_DECISION_LOCALIZATION_RETURNED_NAT"
            )

        decision_ts = cast(
            pd.Timestamp,
            localized,
        )

    else:
        converted = (
            decision_ts.tz_convert(
                "UTC"
            )
        )

        if converted is pd.NaT:
            raise RuntimeError(
                "SYNTHETIC_DECISION_CONVERSION_RETURNED_NAT"
            )

        decision_ts = cast(
            pd.Timestamp,
            converted,
        )

    decision_time_utc = (
        decision_ts.isoformat()
        .replace(
            "+00:00",
            "Z",
        )
    )

    synthetic_record = (
        observer.observe_single(
            feature_row=(
                latest_feature_row
            ),
            decision_time_utc=(
                decision_time_utc
            ),
            source_snapshot_id=(
                snapshot.source_snapshot_id
            ),
            source_provenance=(
                SourceProvenance.SYNTHETIC_ENGINEERING
            ),
            acquisition_attestation=(
                snapshot.attestation
            ),
        )
    )

    escalation_prevented = False

    try:
        observer.observe_single(
            feature_row=(
                latest_feature_row
            ),
            decision_time_utc=(
                decision_time_utc
            ),
            source_snapshot_id=(
                snapshot.source_snapshot_id
            ),
            source_provenance=(
                SourceProvenance.TRUE_FORWARD_OBSERVATION
            ),
            acquisition_attestation=(
                snapshot.attestation
            ),
        )

    except TrueForwardAcquisitionNotAuthorizedError:
        escalation_prevented = True

    passed = bool(
        snapshot.is_synthetic
        and snapshot.authority is None
        and feature_result.feature_count
        == 331
        and feature_result.feature_columns_sha256
        == EXPECTED_FEATURE_COLUMNS_SHA256
        and escalation_prevented
    )

    return {
        "status": (
            "PASS"
            if passed
            else "FAIL"
        ),
        "source_snapshot_id": (
            snapshot.source_snapshot_id
        ),
        "feature_count": (
            feature_result.feature_count
        ),
        "feature_columns_sha256": (
            feature_result.feature_columns_sha256
        ),
        "predicted_class": (
            synthetic_record.predicted_class
        ),
        "synthetic_provenance_escalation_prevented": (
            escalation_prevented
        ),
    }


# =============================================================================
# Artifact Fingerprints
# =============================================================================

def file_sha256(
    path: Path,
) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


# =============================================================================
# Main Evidence Assembly
# =============================================================================

def run_evidence() -> dict[str, Any]:
    inherited_baseline = (
        verify_inherited_baseline_authority()
    )

    git_authority = (
        verify_git_authority()
    )

    static_safety = (
        perform_static_safety_audit()
    )

    sklearn_runtime = (
        verify_sklearn_runtime()
    )

    targeted_pytest = (
        run_targeted_pytest()
    )

    unix_policy = (
        verify_unix_utc_policy()
    )

    ny_close_policy = (
        verify_ny_close_policy()
    )

    if (
        sklearn_runtime["status"]
        == "PASS"
    ):
        synthetic_pipeline = (
            verify_synthetic_pipeline()
        )

    else:
        synthetic_pipeline = {
            "status": "BLOCKED",
            "reason": (
                "FROZEN_MODEL_SKLEARN_RUNTIME_VERSION_MISMATCH"
            ),
            "model_unpickle_attempted": False,
        }

    adapter_path = (
        REPO_ROOT
        / "02_AI"
        / "Adapters"
        / "mt5_read_only_forward_acquisition_adapter.py"
    )

    test_path = (
        REPO_ROOT
        / "04_Testing"
        / "production_portability"
        / "test_mt5_read_only_forward_acquisition_adapter.py"
    )

    runner_path = (
        Path(__file__).resolve()
    )

    required_results = (
        inherited_baseline,
        git_authority,
        static_safety,
        sklearn_runtime,
        targeted_pytest,
        unix_policy,
        ny_close_policy,
        synthetic_pipeline,
    )

    all_pass = all(
        result.get(
            "status"
        )
        == "PASS"
        for result
        in required_results
    )

    evidence: dict[
        str,
        Any,
    ] = {
        "gate": (
            "Gate 15B-A — Reopened Read-Only Forward Acquisition Authority"
        ),
        "gate_version": "2.1.0",
        "status": (
            "PASS"
            if all_pass
            else "FAIL"
        ),
        "authority": {
            "schema_version": (
                ACQUISITION_SCHEMA_VERSION
            ),
            "acquisition_authority_id": (
                ACQUISITION_AUTHORITY_ID
            ),
            "timestamp_semantics": (
                "FAIL_CLOSED_EXPLICIT_TIME_BASIS"
            ),
            "supported_resolved_policies": [
                TIME_BASIS_UNIX_UTC,
                TIME_BASIS_NY_CLOSE_SERVER,
            ],
            "fixed_broker_offset_used": False,
            "historical_dst_normalization": (
                "PER_ROW"
            ),
        },
        "safety_invariants": {
            "genuine_mt5_acquisition": False,
            "true_forward_observation_recorded": False,
            "forward_performance_evaluated": False,
            "outcome_horizon_contract_status": (
                "BLOCKED_NOT_PREDEFINED"
            ),
            "live_authorized": False,
            "execution_authorized": False,
        },
        "inherited_frozen_baseline": (
            inherited_baseline
        ),
        "git_authority": (
            git_authority
        ),
        "static_safety_audit": (
            static_safety
        ),
        "sklearn_runtime_authority": (
            sklearn_runtime
        ),
        "targeted_pytest": (
            targeted_pytest
        ),
        "unix_utc_policy_verification": (
            unix_policy
        ),
        "ny_close_server_policy_verification": (
            ny_close_policy
        ),
        "synthetic_pipeline_verification": (
            synthetic_pipeline
        ),
        "frozen_contracts": {
            "feature_count": 331,
            "feature_columns_sha256": (
                EXPECTED_FEATURE_COLUMNS_SHA256
            ),
            "model_sha256": (
                FROZEN_MODEL_SHA256
            ),
            "expected_sklearn_version": (
                EXPECTED_SKLEARN_VERSION
            ),
        },
        "candidate_artifact_hashes": {
            str(
                adapter_path.relative_to(
                    REPO_ROOT
                )
            ).replace(
                "\\",
                "/",
            ): file_sha256(
                adapter_path
            ),
            str(
                test_path.relative_to(
                    REPO_ROOT
                )
            ).replace(
                "\\",
                "/",
            ): file_sha256(
                test_path
            ),
            str(
                runner_path.relative_to(
                    REPO_ROOT
                )
            ).replace(
                "\\",
                "/",
            ): file_sha256(
                runner_path
            ),
        },
    }

    EVIDENCE_OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    EVIDENCE_OUTPUT_PATH.write_text(
        json.dumps(
            evidence,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    print(
        "GATE_15B_A_AUTHORITY_REGEN_STATUS="
        + evidence["status"]
    )

    print(
        "INHERITED_41_OF_41_STATUS="
        + inherited_baseline["status"]
    )

    print(
        "GIT_AUTHORITY_STATUS="
        + git_authority["status"]
    )

    print(
        "HEAD_EQUALS_ORIGIN_MAIN="
        + str(
            git_authority[
                "head_equals_origin_main"
            ]
        ).lower()
    )

    print(
        "BASELINE_IS_ANCESTOR="
        + str(
            git_authority[
                "accepted_baseline_is_ancestor"
            ]
        ).lower()
    )

    print(
        "UNEXPECTED_COMMITTED_PATHS="
        + json.dumps(
            git_authority[
                "unexpected_committed_paths"
            ]
        )
    )

    print(
        "UNEXPECTED_LOCAL_PATHS="
        + json.dumps(
            git_authority[
                "unexpected_local_paths"
            ]
        )
    )

    print(
        "STATIC_SAFETY_STATUS="
        + static_safety["status"]
    )

    print(
        "STATIC_SAFETY_VIOLATION_COUNT="
        + str(
            static_safety[
                "violation_count"
            ]
        )
    )

    print(
        "SKLEARN_RUNTIME_STATUS="
        + sklearn_runtime["status"]
    )

    print(
        "SKLEARN_EXPECTED_VERSION="
        + sklearn_runtime[
            "expected_version"
        ]
    )

    print(
        "SKLEARN_ACTUAL_VERSION="
        + sklearn_runtime[
            "actual_version"
        ]
    )

    print(
        "TARGETED_PYTEST_STATUS="
        + targeted_pytest["status"]
    )

    print(
        "SYNTHETIC_PIPELINE_STATUS="
        + synthetic_pipeline["status"]
    )

    print(
        "UNIX_UTC_POLICY_STATUS="
        + unix_policy["status"]
    )

    print(
        "NY_CLOSE_POLICY_STATUS="
        + ny_close_policy["status"]
    )

    print(
        "GENUINE_MT5_ACQUISITION=false"
    )

    print(
        "TRUE_FORWARD_OBSERVATION_RECORDED=false"
    )

    print(
        "FORWARD_PERFORMANCE_EVALUATED=false"
    )

    print(
        "OUTCOME_HORIZON_CONTRACT_STATUS=BLOCKED_NOT_PREDEFINED"
    )

    print(
        "LIVE_AUTHORIZED=false"
    )

    print(
        "EXECUTION_AUTHORIZED=false"
    )

    print(
        "EVIDENCE_PATH="
        + str(
            EVIDENCE_OUTPUT_PATH
        )
    )

    return evidence


if __name__ == "__main__":
    result = run_evidence()

    if (
        result["status"]
        != "PASS"
    ):
        raise SystemExit(
            1
        )