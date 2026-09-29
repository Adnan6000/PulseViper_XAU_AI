"""
===============================================================================
Module      : run_xauusd_gate_15d_c_b2d_g1_genuine_anchored_forward_capture.py
Project     : PulseViper XAU AI
Purpose     : Gate 15D-C-B2D-G1 — Genuine Anchored Forward Capture
===============================================================================

ONE controlled genuine read-only prospective capture.

Frozen order:

    published-authority verification
        ->
    MT5 initialize
        ->
    read-only capability facade
        ->
    genuine Gate 15B-A v2.1 snapshot
        ->
    acquisition-authority verification
        ->
    representation-only timestamp normalization
        ->
    Gate 13 frozen 331 features
        ->
    Gate 14 frozen C04 observation
        ->
    Gate 15D-A prospective eligibility
        ->
    SAME-SNAPSHOT prospective anchor
        ->
    atomic anchor append FIRST
        ->
    anchor integrity
        ->
    atomic observation append SECOND
        ->
    observation integrity
        ->
    evidence
        ->
    MT5 shutdown
        ->
    STOP

This gate does NOT authorize:
- outcome maturation
- future outcome access
- performance evaluation
- PnL
- accuracy / win rate
- returns / drawdown
- RiskEngine
- trade_ready
- broker-aware risk
- account protection
- order APIs
- live trading
- execution

If anchor persistence succeeds and observation persistence later fails, the
anchor is preserved as immutable orphan prospective audit history.
===============================================================================
"""

from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, cast

import pandas as pd


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
# Gate
# =============================================================================

GATE_ID: str = (
    "GATE_15D_C_B2D_G1_GENUINE_ANCHORED_FORWARD_CAPTURE"
)

SCHEMA_VERSION: str = "1.0.0"

B2D_AUTHORITY_COMMIT: str = (
    "03c7a5e74b57b3f670521e29d0b55086027ca4da"
)

B2D_EVIDENCE_REL_PATH: str = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_anchor_first_integration_evidence.json"
)

RUNNER_REL_PATH: str = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g1_genuine_anchored_forward_capture.py"
)

PASS_EVIDENCE_REL_PATH: str = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g1_genuine_anchored_forward_capture_evidence.json"
)

BLOCKED_EVIDENCE_REL_PATH: str = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g1_genuine_anchored_forward_capture_blocked.json"
)

B2D_EVIDENCE_PATH: Path = (
    REPO_ROOT
    /
    B2D_EVIDENCE_REL_PATH
)

PASS_EVIDENCE_PATH: Path = (
    REPO_ROOT
    /
    PASS_EVIDENCE_REL_PATH
)

BLOCKED_EVIDENCE_PATH: Path = (
    REPO_ROOT
    /
    BLOCKED_EVIDENCE_REL_PATH
)


# =============================================================================
# Runtime Ledgers
# =============================================================================

OBSERVATION_LEDGER_PATH: Path = (
    REPO_ROOT
    /
    "01_Data/Shadow/"
    "xauusd_frozen_c04_shadow_observations.jsonl"
)

ANCHOR_LEDGER_PATH: Path = (
    REPO_ROOT
    /
    "01_Data/Shadow/"
    "xauusd_frozen_c04_forward_outcome_anchors.jsonl"
)

OUTCOME_LEDGER_PATH: Path = (
    REPO_ROOT
    /
    "01_Data/Shadow/"
    "xauusd_frozen_c04_forward_outcomes.jsonl"
)


# =============================================================================
# Published Authorities
# =============================================================================

_legacy: Any = importlib.import_module(
    "04_Testing.production_portability."
    "run_xauusd_gate_15b_b_genuine_forward_observation"
)

_acq: Any = importlib.import_module(
    "02_AI.Adapters.mt5_read_only_forward_acquisition_adapter"
)

_pipeline: Any = importlib.import_module(
    "02_AI.Features.portable_feature_pipeline"
)

_contract: Any = importlib.import_module(
    "02_AI.Features.portable_feature_contract"
)

_observer: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_shadow_observer"
)

_eligibility: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_eligibility"
)

_anchor: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_anchor"
)

_atomic: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_runtime_atomic_ledgers"
)

_coordinator: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_anchor_first_coordinator"
)

_maturer: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_maturer"
)

_outcome_ledger: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_ledger"
)

mt5: Any = importlib.import_module(
    "MetaTrader5"
)


MT5ReadOnlyCapabilityFacade: Any = (
    _acq.MT5ReadOnlyCapabilityFacade
)

MT5ReadOnlyForwardAcquisitionAdapter: Any = (
    _acq.MT5ReadOnlyForwardAcquisitionAdapter
)

verify_forward_acquisition_authority: Any = (
    _acq.verify_forward_acquisition_authority
)

compute_canonical_snapshot_id: Any = (
    _acq.compute_canonical_snapshot_id
)

PortableFeaturePipeline: Any = (
    _pipeline.PortableFeaturePipeline
)

FrozenC04ShadowObserver: Any = (
    _observer.FrozenC04ShadowObserver
)

SourceProvenance: Any = (
    _observer.SourceProvenance
)

AtomicAnchorLedger: Any = (
    _atomic.AtomicFrozenC04ForwardOutcomeAnchorLedger
)

AtomicObservationLedger: Any = (
    _atomic.AtomicFrozenC04ObservationLedger
)

AnchorFirstCoordinator: Any = (
    _coordinator.FrozenC04ForwardAnchorFirstCoordinator
)

AnchorDuplicateHandling: Any = (
    _anchor.AnchorDuplicateHandling
)

ObservationDuplicateHandling: Any = (
    _observer.DuplicateHandling
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
    for value in _contract.SUPPORTED_SYMBOLS
)

ACQUISITION_AUTHORITY_ID: str = str(
    _acq.ACQUISITION_AUTHORITY_ID
)


# =============================================================================
# Authorization Boundaries
# =============================================================================

OUTCOME_MATURATION_AUTHORIZED: bool = False
PERFORMANCE_EVALUATION_AUTHORIZED: bool = False
PNL_EVALUATION_AUTHORIZED: bool = False
LIVE_AUTHORIZED: bool = False
EXECUTION_AUTHORIZED: bool = False


# =============================================================================
# Error
# =============================================================================

class Gate15DCB2DG1BlockedError(
    RuntimeError
):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:

        raise Gate15DCB2DG1BlockedError(
            reason
        )


# =============================================================================
# Time Helpers
# =============================================================================

def utc_timestamp(
    value: Any,
) -> pd.Timestamp:

    parsed = pd.Timestamp(
        value
    )

    if parsed is pd.NaT:

        raise Gate15DCB2DG1BlockedError(
            "INVALID_TIMESTAMP_NAT"
        )

    timestamp = cast(
        pd.Timestamp,
        parsed,
    )

    if timestamp.tzinfo is None:

        localized = timestamp.tz_localize(
            "UTC"
        )

        if localized is pd.NaT:

            raise Gate15DCB2DG1BlockedError(
                "TIMESTAMP_LOCALIZATION_FAILED"
            )

        return cast(
            pd.Timestamp,
            localized,
        )

    converted = timestamp.tz_convert(
        "UTC"
    )

    if converted is pd.NaT:

        raise Gate15DCB2DG1BlockedError(
            "TIMESTAMP_UTC_CONVERSION_FAILED"
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
            output[
                :-6
            ]
            +
            "Z"
        )

    return output


def now_utc_iso() -> str:

    return utc_iso(
        pd.Timestamp.now(
            tz="UTC"
        )
    )


# =============================================================================
# Git / Files
# =============================================================================

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


def working_tree_clean() -> bool:

    return (
        git_output(
            "status",
            "--porcelain",
            "--untracked-files=all",
        )
        ==
        ""
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


def sanitize_error_text(
    exc: BaseException,
) -> str:

    output = str(
        exc
    )

    output = output.replace(
        str(
            REPO_ROOT
        ),
        "<REPO_ROOT>",
    )

    return " ".join(
        output.split()
    )[
        :2000
    ]


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
# Runtime Ledger File State
# =============================================================================

def ledger_file_state(
    path: Path,
) -> dict[str, Any]:

    if not path.exists():

        return {
            "exists": False,
            "size_bytes": 0,
            "sha256": None,
        }

    require(
        path.is_file(),
        (
            "LEDGER_PATH_NOT_FILE:"
            f"{path}"
        ),
    )

    return {
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


def runtime_file_states() -> dict[str, Any]:

    return {
        "observation": (
            ledger_file_state(
                OBSERVATION_LEDGER_PATH
            )
        ),

        "anchor": (
            ledger_file_state(
                ANCHOR_LEDGER_PATH
            )
        ),

        "outcome": (
            ledger_file_state(
                OUTCOME_LEDGER_PATH
            )
        ),
    }


def true_forward_count(
    ledger: Any,
) -> int:

    return sum(
        1
        for record in ledger.read_all()
        if (
            record.source_provenance
            ==
            SourceProvenance
            .TRUE_FORWARD_OBSERVATION
            .value
        )
    )


# =============================================================================
# Published B2D Authority
# =============================================================================

def verify_b2d_authority() -> dict[str, Any]:

    require(
        B2D_EVIDENCE_PATH.is_file(),
        "B2D_EVIDENCE_MISSING",
    )

    document = json.loads(
        B2D_EVIDENCE_PATH.read_text(
            encoding="utf-8"
        )
    )

    require(
        isinstance(
            document,
            dict,
        ),
        "B2D_EVIDENCE_ROOT_INVALID",
    )

    require(
        document.get(
            "status"
        )
        ==
        "PASS",
        "B2D_EVIDENCE_NOT_PASS",
    )

    require(
        document.get(
            "gate_id"
        )
        ==
        (
            "GATE_15D_C_B2D_"
            "ANCHOR_FIRST_FORWARD_PERSISTENCE_INTEGRATION"
        ),
        "B2D_GATE_ID_MISMATCH",
    )

    hashes = document.get(
        "candidate_artifact_hashes"
    )

    require(
        isinstance(
            hashes,
            dict,
        ),
        "B2D_CANDIDATE_HASHES_MISSING",
    )

    verified_hashes: dict[
        str,
        str,
    ] = {}

    for relative, expected in hashes.items():

        require(
            isinstance(
                relative,
                str,
            ),
            "B2D_ARTIFACT_PATH_INVALID",
        )

        require(
            isinstance(
                expected,
                str,
            )
            and
            len(
                expected
            )
            ==
            64,
            (
                "B2D_ARTIFACT_HASH_INVALID:"
                f"{relative}"
            ),
        )

        path = (
            REPO_ROOT
            /
            relative
        )

        require(
            path.is_file(),
            (
                "B2D_ARTIFACT_MISSING:"
                f"{relative}"
            ),
        )

        actual = sha256_file(
            path
        )

        require(
            actual
            ==
            expected,
            (
                "B2D_ARTIFACT_HASH_MISMATCH:"
                f"{relative}:"
                f"{actual}!="
                f"{expected}"
            ),
        )

        verified_hashes[
            relative
        ] = actual

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
        "ANCHOR_FIRST_ORDER_MISMATCH",
    )

    require(
        _coordinator.ORPHAN_ANCHOR_POLICY
        ==
        "PRESERVE_IMMUTABLE_ANCHOR_IF_OBSERVATION_APPEND_FAILS",
        "ORPHAN_ANCHOR_POLICY_MISMATCH",
    )

    return {
        "status": "PASS",

        "authority_commit": (
            B2D_AUTHORITY_COMMIT
        ),

        "verified_artifact_hashes": (
            verified_hashes
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
    }


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
        B2D_AUTHORITY_COMMIT,
        (
            "UNEXPECTED_G1_FREEZE_BASE:"
            f"{head}!="
            f"{B2D_AUTHORITY_COMMIT}"
        ),
    )

    ancestor = git_process(
        "merge-base",
        "--is-ancestor",
        B2D_AUTHORITY_COMMIT,
        head,
    )

    require(
        ancestor.returncode
        ==
        0,
        "B2D_AUTHORITY_NOT_ANCESTOR",
    )

    b2d = verify_b2d_authority()

    return {
        "status": "PASS",

        "branch": branch,

        "execution_head": head,

        "origin_main": origin_main,

        "head_equals_origin_main": True,

        "b2d_authority": b2d,
    }


# =============================================================================
# Runtime Authority
# =============================================================================

def verify_runtime_authorities() -> dict[str, Any]:

    require(
        bool(
            _atomic.verify_authorities()
        ),
        "ATOMIC_LEDGER_AUTHORITY_INVALID",
    )

    require(
        bool(
            _coordinator.verify_authorities()
        ),
        "COORDINATOR_AUTHORITY_INVALID",
    )

    require(
        bool(
            _anchor.verify_authorities()
        ),
        "ANCHOR_AUTHORITY_INVALID",
    )

    require(
        bool(
            _eligibility.verify_authorities()
        ),
        "ELIGIBILITY_AUTHORITY_INVALID",
    )

    require(
        ACQUISITION_AUTHORITY_ID
        ==
        "MT5ReadOnlyForwardAcquisitionAdapter:2.1.0",
        "ACQUISITION_AUTHORITY_ID_MISMATCH",
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
        OUTCOME_MATURATION_AUTHORIZED
        is False,
        "OUTCOME_MATURATION_AUTHORIZED_UNEXPECTEDLY",
    )

    require(
        PERFORMANCE_EVALUATION_AUTHORIZED
        is False,
        "PERFORMANCE_AUTHORIZED_UNEXPECTEDLY",
    )

    require(
        PNL_EVALUATION_AUTHORIZED
        is False,
        "PNL_AUTHORIZED_UNEXPECTEDLY",
    )

    require(
        LIVE_AUTHORIZED
        is False,
        "LIVE_AUTHORIZED_UNEXPECTEDLY",
    )

    require(
        EXECUTION_AUTHORIZED
        is False,
        "EXECUTION_AUTHORIZED_UNEXPECTEDLY",
    )

    return {
        "status": "PASS",

        "acquisition_authority": (
            ACQUISITION_AUTHORITY_ID
        ),

        "atomic_ledger_authority": (
            _atomic
            .ATOMIC_LEDGER_AUTHORITY_VERSION
        ),

        "coordinator_authority": (
            _coordinator
            .COORDINATOR_VERSION
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
# Static Safety
# =============================================================================

def static_safety_audit() -> dict[str, Any]:

    legacy = (
        _legacy.static_safety_audit()
    )

    require(
        legacy.get(
            "status"
        )
        ==
        "PASS",
        "PUBLISHED_READ_ONLY_STACK_STATIC_SAFETY_FAILED",
    )

    return {
        "status": "PASS",

        "published_read_only_stack": (
            legacy
        ),

        "broker_write_calls": 0,

        "risk_engine_dependencies": 0,

        "trade_ready_dependencies": 0,

        "outcome_maturation_calls": 0,

        "outcome_ledger_append_calls": 0,
    }


# =============================================================================
# Existing Verified Market Helpers
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

    return (
        _legacy
        .normalize_market_timestamp_resolution(
            market_data
        )
    )


def verify_bid_ask(
    read_only_api: Any,
    broker_symbol: str,
) -> dict[str, Any]:

    return (
        _legacy.verify_bid_ask(
            read_only_api,
            broker_symbol,
        )
    )


def verify_attested_freshness(
    attestation: Any,
) -> dict[str, Any]:

    return (
        _legacy.verify_attested_freshness(
            attestation
        )
    )


# =============================================================================
# State
# =============================================================================

def initial_state() -> dict[str, Any]:

    return {
        "mt5_initialized": False,

        "genuine_mt5_acquisition": False,

        "verified_forward_authority": False,

        "gate13_status": "NOT_RUN",

        "gate14_status": "NOT_RUN",

        "prospective_eligibility_status": "NOT_RUN",

        "anchor_append_performed": False,

        "anchor_idempotent_duplicate": False,

        "anchor_integrity_verified": False,

        "observation_append_performed": False,

        "observation_idempotent_duplicate": False,

        "observation_integrity_verified": False,

        "orphan_anchor_preserved": False,

        "decision_time_utc": None,

        "source_snapshot_id": None,

        "logical_observation_id": None,

        "anchor_semantic_fingerprint": None,
    }


# =============================================================================
# Blocked Evidence
# =============================================================================

def write_blocked_evidence(
    exc: BaseException,
    state: Mapping[str, Any],
) -> dict[str, Any]:

    try:

        head = git_output(
            "rev-parse",
            "HEAD",
        )

        origin_main = git_output(
            "rev-parse",
            "origin/main",
        )

    except Exception:

        head = None

        origin_main = None

    document: dict[
        str,
        Any,
    ] = {
        "gate": (
            "Gate 15D-C-B2D-G1 — "
            "Genuine Anchored Forward Capture"
        ),

        "gate_id": (
            GATE_ID
        ),

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
            "execution_head": (
                head
            ),

            "origin_main": (
                origin_main
            ),

            "head_equals_origin_main": (
                head is not None
                and
                head
                ==
                origin_main
            ),
        },

        "progress_before_block": (
            dict(
                state
            )
        ),

        "runtime_ledger_files": (
            runtime_file_states()
        ),

        "outcome_maturation_authorized": False,

        "forward_performance_evaluated": False,

        "pnl_evaluated": False,

        "live_authorized": False,

        "execution_authorized": False,
    }

    try:

        write_json(
            BLOCKED_EVIDENCE_PATH,
            document,
        )

    except Exception:

        pass

    return document


# =============================================================================
# Genuine Capture
# =============================================================================

def run_gate(
    state: dict[str, Any],
) -> dict[str, Any]:

    repository = (
        verify_repository_authority()
    )

    safety = (
        static_safety_audit()
    )

    runtime_authority = (
        verify_runtime_authorities()
    )

    anchor_ledger = (
        AtomicAnchorLedger(
            ANCHOR_LEDGER_PATH,

            duplicate_handling=(
                AnchorDuplicateHandling
                .IDEMPOTENT_IGNORE
            ),
        )
    )

    observation_ledger = (
        AtomicObservationLedger(
            OBSERVATION_LEDGER_PATH,

            duplicate_handling=(
                ObservationDuplicateHandling
                .IDEMPOTENT_IGNORE
            ),
        )
    )

    require(
        bool(
            anchor_ledger.validate_integrity()
        ),
        "PRE_CAPTURE_ANCHOR_LEDGER_INTEGRITY_FAILED",
    )

    require(
        bool(
            observation_ledger.validate_integrity()
        ),
        "PRE_CAPTURE_OBSERVATION_LEDGER_INTEGRITY_FAILED",
    )

    anchor_count_before = (
        anchor_ledger.count()
    )

    observation_count_before = (
        observation_ledger.count()
    )

    true_forward_before = (
        true_forward_count(
            observation_ledger
        )
    )

    runtime_before = (
        runtime_file_states()
    )

    outcome_before = (
        runtime_before[
            "outcome"
        ]
    )

    initialized = False

    try:

        # ---------------------------------------------------------------------
        # MT5 lifecycle
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

        read_only_api = (
            MT5ReadOnlyCapabilityFacade(
                mt5
            )
        )

        # ---------------------------------------------------------------------
        # Genuine read-only acquisition
        # ---------------------------------------------------------------------

        acquisition = (
            MT5ReadOnlyForwardAcquisitionAdapter(
                read_only_api,

                is_synthetic=False,

                include_native_d1=False,

                timestamp_basis="AUTO",
            )
        )

        broker_symbol = (
            acquisition
            .resolve_broker_symbol()
        )

        require(
            broker_symbol
            in
            set(
                SUPPORTED_SYMBOLS
            ),
            (
                "UNSUPPORTED_BROKER_SYMBOL:"
                f"{broker_symbol}"
            ),
        )

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
            snapshot.authority
            is not None,
            "VERIFIED_FORWARD_AUTHORITY_MISSING",
        )

        require(
            bool(
                snapshot.authority
                .is_valid_authority()
            ),
            "VERIFIED_FORWARD_AUTHORITY_INVALID",
        )

        verified_attestation = (
            verify_forward_acquisition_authority(
                snapshot.authority,

                expected_decision_time_utc=(
                    snapshot
                    .decision_time_utc
                ),

                expected_source_snapshot_id=(
                    snapshot
                    .source_snapshot_id
                ),

                expected_canonical_instrument=(
                    snapshot
                    .canonical_instrument
                ),

                expected_feature_columns_sha256=(
                    EXPECTED_FEATURE_COLUMNS_SHA256
                ),

                expected_model_sha256=(
                    FROZEN_MODEL_SHA256
                ),
            )
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
            "decision_time_utc"
        ] = (
            snapshot
            .decision_time_utc
        )

        state[
            "source_snapshot_id"
        ] = (
            snapshot
            .source_snapshot_id
        )

        # ---------------------------------------------------------------------
        # Representation normalization only
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
            ==
            snapshot.source_snapshot_id,
            (
                "TIMESTAMP_NORMALIZATION_CHANGED_SOURCE_SNAPSHOT_ID:"
                f"{normalized_snapshot_id}!="
                f"{snapshot.source_snapshot_id}"
            ),
        )

        # ---------------------------------------------------------------------
        # Gate 13
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
            ==
            EXPECTED_FEATURE_COUNT,
            "GATE13_FEATURE_COUNT_MISMATCH",
        )

        require(
            feature_result
            .feature_columns_sha256
            ==
            EXPECTED_FEATURE_COLUMNS_SHA256,
            "GATE13_FEATURE_HASH_MISMATCH",
        )

        require(
            feature_result.row_count
            >
            0,
            "GATE13_NO_VALID_FEATURE_ROWS",
        )

        latest_feature_time = (
            utc_iso(
                feature_result
                .decision_times
                .iloc[
                    -1
                ]
            )
        )

        require(
            latest_feature_time
            ==
            snapshot.decision_time_utc,
            (
                "GATE13_DECISION_TIME_MISMATCH:"
                f"{latest_feature_time}!="
                f"{snapshot.decision_time_utc}"
            ),
        )

        state[
            "gate13_status"
        ] = "PASS"

        # ---------------------------------------------------------------------
        # Gate 14 observation candidate
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
                    .iloc[
                        -1
                    ]
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
                    snapshot
                    .authority
                ),
            )
        )

        require(
            observation.source_snapshot_id
            ==
            snapshot.source_snapshot_id,
            "OBSERVATION_SOURCE_SNAPSHOT_MISMATCH",
        )

        require(
            observation.decision_time_utc
            ==
            snapshot.decision_time_utc,
            "OBSERVATION_DECISION_TIME_MISMATCH",
        )

        require(
            observation.feature_columns_sha256
            ==
            EXPECTED_FEATURE_COLUMNS_SHA256,
            "OBSERVATION_FEATURE_HASH_MISMATCH",
        )

        require(
            observation.model_sha256
            ==
            FROZEN_MODEL_SHA256,
            "OBSERVATION_MODEL_HASH_MISMATCH",
        )

        require(
            observation.live_authorized
            is False,
            "OBSERVATION_LIVE_AUTHORIZATION_VIOLATION",
        )

        require(
            observation.execution_authorized
            is False,
            "OBSERVATION_EXECUTION_AUTHORIZATION_VIOLATION",
        )

        state[
            "gate14_status"
        ] = "PASS"

        state[
            "logical_observation_id"
        ] = (
            observation
            .logical_observation_id
        )

        # ---------------------------------------------------------------------
        # Explicit Gate 15D-A prospective eligibility
        # ---------------------------------------------------------------------

        eligibility = (
            _eligibility
            .assess_observation(
                observation.to_dict()
            )
        )

        require(
            eligibility
            .eligible_for_formal_maturation
            is True,
            (
                "PROSPECTIVE_ELIGIBILITY_FAILED:"
                f"{eligibility.eligibility_reason}"
            ),
        )

        require(
            eligibility.eligibility_reason
            ==
            "POST_CONTRACT_PROSPECTIVE_OBSERVATION",
            (
                "UNEXPECTED_ELIGIBILITY_REASON:"
                f"{eligibility.eligibility_reason}"
            ),
        )

        state[
            "prospective_eligibility_status"
        ] = "PASS"

        # ---------------------------------------------------------------------
        # Published B2D anchor-first persistence
        # ---------------------------------------------------------------------

        coordinator = (
            AnchorFirstCoordinator(
                anchor_ledger=(
                    anchor_ledger
                ),

                observation_ledger=(
                    observation_ledger
                ),
            )
        )

        persistence = (
            coordinator.persist(
                observation=(
                    observation
                ),

                market_data=(
                    normalized_market_data
                ),

                acquisition_authority=(
                    verified_attestation
                    .acquisition_authority
                ),
            )
        )

        state[
            "anchor_append_performed"
        ] = bool(
            persistence
            .anchor_appended
        )

        state[
            "anchor_idempotent_duplicate"
        ] = bool(
            persistence
            .anchor_idempotent_duplicate
        )

        state[
            "anchor_integrity_verified"
        ] = bool(
            persistence
            .anchor_integrity_verified
        )

        state[
            "observation_append_performed"
        ] = bool(
            persistence
            .observation_appended
        )

        state[
            "observation_idempotent_duplicate"
        ] = bool(
            persistence
            .observation_idempotent_duplicate
        )

        state[
            "observation_integrity_verified"
        ] = bool(
            persistence
            .observation_integrity_verified
        )

        state[
            "anchor_semantic_fingerprint"
        ] = (
            persistence
            .anchor_semantic_fingerprint
        )

        # ---------------------------------------------------------------------
        # Post-persistence integrity
        # ---------------------------------------------------------------------

        require(
            bool(
                anchor_ledger
                .validate_integrity()
            ),
            "POST_CAPTURE_ANCHOR_LEDGER_INTEGRITY_FAILED",
        )

        require(
            bool(
                observation_ledger
                .validate_integrity()
            ),
            "POST_CAPTURE_OBSERVATION_LEDGER_INTEGRITY_FAILED",
        )

        anchor_count_after = (
            anchor_ledger.count()
        )

        observation_count_after = (
            observation_ledger.count()
        )

        true_forward_after = (
            true_forward_count(
                observation_ledger
            )
        )

        anchor_delta = (
            anchor_count_after
            -
            anchor_count_before
        )

        observation_delta = (
            observation_count_after
            -
            observation_count_before
        )

        true_forward_delta = (
            true_forward_after
            -
            true_forward_before
        )

        require(
            anchor_delta
            in {
                0,
                1,
            },
            (
                "UNEXPECTED_ANCHOR_DELTA:"
                f"{anchor_delta}"
            ),
        )

        require(
            observation_delta
            in {
                0,
                1,
            },
            (
                "UNEXPECTED_OBSERVATION_DELTA:"
                f"{observation_delta}"
            ),
        )

        require(
            true_forward_delta
            in {
                0,
                1,
            },
            (
                "UNEXPECTED_TRUE_FORWARD_DELTA:"
                f"{true_forward_delta}"
            ),
        )

        if persistence.anchor_appended:

            require(
                anchor_delta
                ==
                1,
                "ANCHOR_APPEND_COUNT_MISMATCH",
            )

        if persistence.anchor_idempotent_duplicate:

            require(
                anchor_delta
                ==
                0,
                "ANCHOR_DUPLICATE_CHANGED_COUNT",
            )

        if persistence.observation_appended:

            require(
                observation_delta
                ==
                1,
                "OBSERVATION_APPEND_COUNT_MISMATCH",
            )

            require(
                true_forward_delta
                ==
                1,
                "TRUE_FORWARD_APPEND_COUNT_MISMATCH",
            )

        if persistence.observation_idempotent_duplicate:

            require(
                observation_delta
                ==
                0,
                "OBSERVATION_DUPLICATE_CHANGED_COUNT",
            )

        # ---------------------------------------------------------------------
        # Outcome ledger MUST be unchanged
        # ---------------------------------------------------------------------

        runtime_after = (
            runtime_file_states()
        )

        require(
            runtime_after[
                "outcome"
            ]
            ==
            outcome_before,
            "OUTCOME_LEDGER_CHANGED_DURING_G1",
        )

        # ---------------------------------------------------------------------
        # Evidence
        # ---------------------------------------------------------------------

        evidence: dict[
            str,
            Any,
        ] = {
            "gate": (
                "Gate 15D-C-B2D-G1 — "
                "Genuine Anchored Forward Capture"
            ),

            "gate_id": (
                GATE_ID
            ),

            "schema_version": (
                SCHEMA_VERSION
            ),

            "generated_at_utc": (
                now_utc_iso()
            ),

            "status": "PASS",

            "repository_authority": (
                repository
            ),

            "static_safety": (
                safety
            ),

            "runtime_authority": (
                runtime_authority
            ),

            "genuine_mt5_acquisition": True,

            "canonical_instrument": (
                snapshot
                .canonical_instrument
            ),

            "resolved_broker_symbol": (
                snapshot
                .broker_symbol
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

            "semantic_observation_fingerprint": (
                observation
                .semantic_record_fingerprint
            ),

            "anchor_semantic_fingerprint": (
                persistence
                .anchor_semantic_fingerprint
            ),

            "feature_columns_sha256": (
                EXPECTED_FEATURE_COLUMNS_SHA256
            ),

            "model_sha256": (
                FROZEN_MODEL_SHA256
            ),

            "predicted_class": (
                observation
                .predicted_class
            ),

            "predicted_label": (
                observation
                .predicted_label
            ),

            "winning_probability": (
                observation
                .winning_probability
            ),

            "gate13_status": "PASS",

            "gate14_status": "PASS",

            "prospective_eligibility": {
                "status": "PASS",

                "eligible_for_formal_maturation": True,

                "eligibility_reason": (
                    eligibility
                    .eligibility_reason
                ),
            },

            "time_basis": {
                "policy": (
                    verified_attestation
                    .time_basis_policy
                ),

                "reference_tick_utc": (
                    verified_attestation
                    .time_basis_reference_tick_utc
                ),

                "reference_tick_age_seconds": (
                    verified_attestation
                    .time_basis_reference_tick_age_seconds
                ),
            },

            "market_freshness": (
                freshness
            ),

            "bid_ask_validation": (
                bid_ask
            ),

            "timestamp_resolution_normalization": {
                "status": "PASS",

                "dtypes_before": (
                    timestamp_dtypes_before
                ),

                "dtypes_after": (
                    timestamp_dtypes_after
                ),

                "source_snapshot_id_unchanged": True,
            },

            "persistence": {
                "order": (
                    persistence
                    .persistence_order
                ),

                "anchor_appended": (
                    persistence
                    .anchor_appended
                ),

                "anchor_idempotent_duplicate": (
                    persistence
                    .anchor_idempotent_duplicate
                ),

                "anchor_integrity_verified": (
                    persistence
                    .anchor_integrity_verified
                ),

                "observation_appended": (
                    persistence
                    .observation_appended
                ),

                "observation_idempotent_duplicate": (
                    persistence
                    .observation_idempotent_duplicate
                ),

                "observation_integrity_verified": (
                    persistence
                    .observation_integrity_verified
                ),

                "orphan_anchor": False,
            },

            "ledger_counts": {
                "anchor_before": (
                    anchor_count_before
                ),

                "anchor_after": (
                    anchor_count_after
                ),

                "anchor_delta": (
                    anchor_delta
                ),

                "observation_before": (
                    observation_count_before
                ),

                "observation_after": (
                    observation_count_after
                ),

                "observation_delta": (
                    observation_delta
                ),

                "true_forward_before": (
                    true_forward_before
                ),

                "true_forward_after": (
                    true_forward_after
                ),

                "true_forward_delta": (
                    true_forward_delta
                ),
            },

            "runtime_ledger_files_before": (
                runtime_before
            ),

            "runtime_ledger_files_after": (
                runtime_after
            ),

            "outcome_ledger_unchanged": True,

            "genuine_anchor_persisted_or_idempotently_present": (
                bool(
                    persistence
                    .anchor_appended
                    or
                    persistence
                    .anchor_idempotent_duplicate
                )
            ),

            "genuine_observation_persisted_or_idempotently_present": (
                bool(
                    persistence
                    .observation_appended
                    or
                    persistence
                    .observation_idempotent_duplicate
                )
            ),

            "genuine_forward_observation_matured": False,

            "genuine_outcome_appended": False,

            "outcome_maturation_authorized": False,

            "forward_performance_evaluated": False,

            "accuracy_evaluated": False,

            "win_rate_evaluated": False,

            "pnl_evaluated": False,

            "return_evaluated": False,

            "drawdown_evaluated": False,

            "live_authorized": False,

            "execution_authorized": False,

            "next_step": (
                "WAIT_FOR_EXACT_12_COMPLETED_FUTURE_M5_ROWS_"
                "THEN_USE_SEPARATELY_FROZEN_MATURATION_GATE"
            ),
        }

        write_json(
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

    state = initial_state()

    try:

        result = run_gate(
            state
        )

        persistence = result[
            "persistence"
        ]

        counts = result[
            "ledger_counts"
        ]

        print(
            "GATE_15D_C_B2D_G1_STATUS=PASS"
        )

        print(
            "GENUINE_MT5_ACQUISITION=true"
        )

        print(
            "DECISION_TIME_UTC="
            +
            str(
                result[
                    "decision_time_utc"
                ]
            )
        )

        print(
            "SOURCE_SNAPSHOT_ID="
            +
            str(
                result[
                    "source_snapshot_id"
                ]
            )
        )

        print(
            "LOGICAL_OBSERVATION_ID="
            +
            str(
                result[
                    "logical_observation_id"
                ]
            )
        )

        print(
            "ANCHOR_SEMANTIC_FINGERPRINT="
            +
            str(
                result[
                    "anchor_semantic_fingerprint"
                ]
            )
        )

        print(
            "PERSISTENCE_ORDER="
            +
            str(
                persistence[
                    "order"
                ]
            )
        )

        print(
            "ANCHOR_APPENDED="
            +
            (
                "true"
                if persistence[
                    "anchor_appended"
                ]
                else
                "false"
            )
        )

        print(
            "ANCHOR_IDEMPOTENT_DUPLICATE="
            +
            (
                "true"
                if persistence[
                    "anchor_idempotent_duplicate"
                ]
                else
                "false"
            )
        )

        print(
            "OBSERVATION_APPENDED="
            +
            (
                "true"
                if persistence[
                    "observation_appended"
                ]
                else
                "false"
            )
        )

        print(
            "OBSERVATION_IDEMPOTENT_DUPLICATE="
            +
            (
                "true"
                if persistence[
                    "observation_idempotent_duplicate"
                ]
                else
                "false"
            )
        )

        print(
            "ANCHOR_COUNT_DELTA="
            +
            str(
                counts[
                    "anchor_delta"
                ]
            )
        )

        print(
            "OBSERVATION_COUNT_DELTA="
            +
            str(
                counts[
                    "observation_delta"
                ]
            )
        )

        print(
            "TRUE_FORWARD_COUNT_DELTA="
            +
            str(
                counts[
                    "true_forward_delta"
                ]
            )
        )

        print(
            "OUTCOME_LEDGER_UNCHANGED=true"
        )

        print(
            "GENUINE_FORWARD_OBSERVATION_MATURED=false"
        )

        print(
            "GENUINE_OUTCOME_APPENDED=false"
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
                PASS_EVIDENCE_PATH
            )
        )

        return 0

    except Exception as exc:

        # Dynamic import modules are intentionally typed Any, therefore Pyright
        # cannot narrow `exc` using the dynamically imported exception class.
        # getattr() preserves the runtime contract without unsafe typing claims.

        coordinator_error_type = getattr(
            _coordinator,
            "ObservationPersistenceAfterAnchorError",
            None,
        )

        if (
            isinstance(
                coordinator_error_type,
                type,
            )
            and
            isinstance(
                exc,
                coordinator_error_type,
            )
        ):

            state[
                "orphan_anchor_preserved"
            ] = bool(
                getattr(
                    exc,
                    "orphan_anchor_preserved",
                    False,
                )
            )

            state[
                "logical_observation_id"
            ] = getattr(
                exc,
                "logical_observation_id",
                None,
            )

            state[
                "anchor_semantic_fingerprint"
            ] = getattr(
                exc,
                "anchor_semantic_fingerprint",
                None,
            )

        blocked = write_blocked_evidence(
            exc,
            state,
        )

        print(
            "GATE_15D_C_B2D_G1_STATUS=BLOCKED"
        )

        print(
            "ERROR_TYPE="
            +
            str(
                blocked[
                    "reason"
                ][
                    "error_type"
                ]
            )
        )

        print(
            "ERROR="
            +
            str(
                blocked[
                    "reason"
                ][
                    "error_text"
                ]
            )
        )

        print(
            "ORPHAN_ANCHOR_PRESERVED="
            +
            (
                "true"
                if state.get(
                    "orphan_anchor_preserved",
                    False,
                )
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

        return 2


if __name__ == "__main__":

    raise SystemExit(
        main()
    )