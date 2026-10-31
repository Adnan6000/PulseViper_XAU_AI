from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

import pandas as pd


REPO_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(REPO_ROOT),
    )


GATE_ID = (
    "GATE_15D_C_B2D_G7_H_E_B_R2_"
    "FIRST_GENUINE_R03_CAPTURE_RECOVERY"
)

FREEZE_BASE_AUTHORITY_COMMIT = (
    "d138717f1cb1d80584479289f71e95b0c5b9fe6f"
)

ORIGINAL_BLOCKED_EVIDENCE_REL = (
    "04_Testing/evidence/research/"
    "portable_331/remediation/"
    "xauusd_gate_15d_c_b2d_g7_h_e_b_"
    "first_genuine_r03_capture_blocked.json"
)

FREEZE_EVIDENCE_REL = (
    "04_Testing/evidence/research/"
    "portable_331/remediation/"
    "xauusd_gate_15d_c_b2d_g7_h_e_b_r2_"
    "first_genuine_r03_capture_recovery_runner_freeze.json"
)

PASS_EVIDENCE_REL = (
    "04_Testing/evidence/research/"
    "portable_331/remediation/"
    "xauusd_gate_15d_c_b2d_g7_h_e_b_r2_"
    "first_genuine_r03_capture_recovery.json"
)

BLOCKED_EVIDENCE_REL = (
    "04_Testing/evidence/research/"
    "portable_331/remediation/"
    "xauusd_gate_15d_c_b2d_g7_h_e_b_r2_"
    "first_genuine_r03_capture_recovery_blocked.json"
)

RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_h_e_b_r2_"
    "first_genuine_r03_capture_recovery.py"
)

FREEZE_RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_h_e_b_r2_"
    "first_genuine_r03_capture_recovery_freeze.py"
)

TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g7_h_e_b_r2_"
    "first_genuine_r03_capture_recovery_freeze.py"
)

ORIGINAL_BLOCKED_EVIDENCE_PATH = (
    REPO_ROOT
    /
    ORIGINAL_BLOCKED_EVIDENCE_REL
)

FREEZE_EVIDENCE_PATH = (
    REPO_ROOT
    /
    FREEZE_EVIDENCE_REL
)

PASS_EVIDENCE_PATH = (
    REPO_ROOT
    /
    PASS_EVIDENCE_REL
)

BLOCKED_EVIDENCE_PATH = (
    REPO_ROOT
    /
    BLOCKED_EVIDENCE_REL
)


_controller: Any = importlib.import_module(
    "02_AI.Models."
    "r03_prospective_collection_controller"
)

_runtime: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_r03_prospective_runtime"
)

_acquisition: Any = importlib.import_module(
    "02_AI.Adapters."
    "mt5_read_only_forward_acquisition_adapter"
)

_pipeline: Any = importlib.import_module(
    "02_AI.Features."
    "portable_feature_pipeline"
)

_legacy_capture: Any = importlib.import_module(
    "04_Testing.production_portability."
    "run_xauusd_gate_15d_c_b2d_g1_"
    "genuine_anchored_forward_capture"
)

mt5: Any = importlib.import_module(
    "MetaTrader5"
)


OBSERVATION_LEDGER_REL = str(
    _controller
    .OBSERVATION_LEDGER_RELATIVE_PATH
)

ANCHOR_LEDGER_REL = str(
    _controller
    .ANCHOR_LEDGER_RELATIVE_PATH
)

OUTCOME_LEDGER_REL = str(
    _controller
    .OUTCOME_LEDGER_RELATIVE_PATH
)


PERFORMANCE_EVALUATION_AUTHORIZED = False
PNL_EVALUATION_AUTHORIZED = False
LIVE_AUTHORIZED = False
EXECUTION_AUTHORIZED = False


class G7HEBR2BlockedError(
    RuntimeError
):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise G7HEBR2BlockedError(
            reason
        )


def sha256_file(
    path: Path,
) -> str:

    require(
        path.is_file(),
        f"FILE_MISSING:{path}",
    )

    digest = hashlib.sha256()

    with path.open(
        "rb"
    ) as handle:

        while True:

            chunk = handle.read(
                1024 * 1024
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
        process.returncode == 0,
        (
            "GIT_COMMAND_FAILED:"
            +
            " ".join(
                args
            )
        ),
    )

    return process.stdout.rstrip(
        "\r\n"
    )


def status_paths() -> set[str]:

    raw = git_output(
        "status",
        "--porcelain",
        "--untracked-files=all",
    )

    output: set[str] = set()

    for line in raw.splitlines():

        if len(line) < 4:
            continue

        value = (
            line[3:]
            .strip()
            .replace(
                "\\",
                "/",
            )
        )

        if " -> " in value:
            value = value.split(
                " -> ",
                1,
            )[1]

        output.add(
            value
        )

    return output


def now_utc_iso() -> str:

    value = (
        pd.Timestamp.now(
            tz="UTC"
        )
        .isoformat()
    )

    if value.endswith(
        "+00:00"
    ):
        value = (
            value[:-6]
            +
            "Z"
        )

    return value


def write_create_only_json(
    path: Path,
    document: Mapping[
        str,
        Any,
    ],
) -> None:

    require(
        not path.exists(),
        (
            "EVIDENCE_ALREADY_EXISTS:"
            f"{path}"
        ),
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "x",
        encoding="utf-8",
    ) as handle:

        handle.write(
            json.dumps(
                dict(
                    document
                ),
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
            )
            +
            "\n"
        )


def verify_recovery_freeze_authority() -> dict[
    str,
    Any,
]:

    require(
        FREEZE_EVIDENCE_PATH.is_file(),
        "RECOVERY_FREEZE_EVIDENCE_MISSING",
    )

    raw = json.loads(
        FREEZE_EVIDENCE_PATH.read_text(
            encoding="utf-8"
        )
    )

    require(
        isinstance(
            raw,
            dict,
        ),
        "RECOVERY_FREEZE_EVIDENCE_INVALID",
    )

    require(
        raw.get(
            "status"
        )
        ==
        "PASS",
        "RECOVERY_FREEZE_NOT_PASS",
    )

    require(
        raw.get(
            "base_authority_commit"
        )
        ==
        FREEZE_BASE_AUTHORITY_COMMIT,
        "RECOVERY_FREEZE_BASE_MISMATCH",
    )

    original_blocked_sha = raw.get(
        "original_blocked_evidence_sha256"
    )

    require(
        isinstance(
            original_blocked_sha,
            str,
        )
        and
        len(
            original_blocked_sha
        )
        ==
        64,
        "ORIGINAL_BLOCKED_EVIDENCE_SHA_INVALID",
    )

    require(
        sha256_file(
            ORIGINAL_BLOCKED_EVIDENCE_PATH
        )
        ==
        original_blocked_sha,
        "ORIGINAL_BLOCKED_EVIDENCE_CHANGED",
    )

    hashes = raw.get(
        "candidate_artifact_hashes"
    )

    require(
        isinstance(
            hashes,
            dict,
        ),
        "RECOVERY_FREEZE_HASHES_MISSING",
    )

    expected_paths = {
        RUNNER_REL,
        FREEZE_RUNNER_REL,
        TEST_REL,
    }

    require(
        set(
            hashes.keys()
        )
        ==
        expected_paths,
        "RECOVERY_FREEZE_PATH_SET_MISMATCH",
    )

    for relative in sorted(
        expected_paths
    ):

        expected = hashes.get(
            relative
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
                "RECOVERY_ARTIFACT_HASH_INVALID:"
                f"{relative}"
            ),
        )

        require(
            sha256_file(
                REPO_ROOT
                /
                relative
            )
            ==
            expected,
            (
                "RECOVERY_ARTIFACT_CHANGED:"
                f"{relative}"
            ),
        )

    return raw


def verify_repository() -> dict[
    str,
    Any,
]:

    fetch = git_process(
        "fetch",
        "origin",
    )

    require(
        fetch.returncode == 0,
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

    origin = git_output(
        "rev-parse",
        "origin/main",
    )

    require(
        branch == "main",
        (
            "UNEXPECTED_BRANCH:"
            f"{branch}"
        ),
    )

    require(
        head == origin,
        (
            "HEAD_ORIGIN_MAIN_DIVERGENCE:"
            f"{head}!="
            f"{origin}"
        ),
    )

    ancestor = git_process(
        "merge-base",
        "--is-ancestor",
        FREEZE_BASE_AUTHORITY_COMMIT,
        head,
    )

    require(
        ancestor.returncode == 0,
        "RECOVERY_BASE_NOT_ANCESTOR",
    )

    allowed = {
        PASS_EVIDENCE_REL,
        BLOCKED_EVIDENCE_REL,
        OBSERVATION_LEDGER_REL,
        ANCHOR_LEDGER_REL,
        OUTCOME_LEDGER_REL,
    }

    unexpected = (
        status_paths()
        -
        allowed
    )

    require(
        not unexpected,
        (
            "UNEXPECTED_LOCAL_PATHS:"
            f"{sorted(unexpected)}"
        ),
    )

    freeze = (
        verify_recovery_freeze_authority()
    )

    return {
        "branch": branch,
        "execution_head": head,
        "origin_main": origin,
        "recovery_freeze_authority": (
            freeze
        ),
    }


def verify_original_failure() -> dict[
    str,
    Any,
]:

    require(
        ORIGINAL_BLOCKED_EVIDENCE_PATH.is_file(),
        "ORIGINAL_BLOCKED_EVIDENCE_MISSING",
    )

    raw = json.loads(
        ORIGINAL_BLOCKED_EVIDENCE_PATH
        .read_text(
            encoding="utf-8"
        )
    )

    require(
        isinstance(
            raw,
            dict,
        ),
        "ORIGINAL_BLOCKED_EVIDENCE_INVALID",
    )

    require(
        raw.get(
            "status"
        )
        ==
        "BLOCKED",
        "ORIGINAL_ATTEMPT_NOT_BLOCKED",
    )

    require(
        raw.get(
            "error_type"
        )
        ==
        "TimestampBasisResolutionError",
        "ORIGINAL_BLOCK_REASON_CHANGED",
    )

    error = raw.get(
        "error"
    )

    require(
        isinstance(
            error,
            str,
        )
        and
        "TIMESTAMP_BASIS_NOT_UNIQUELY_PROVEN"
        in
        error,
        "ORIGINAL_TIMESTAMP_BASIS_FAILURE_NOT_FOUND",
    )

    return {
        "sha256": (
            sha256_file(
                ORIGINAL_BLOCKED_EVIDENCE_PATH
            )
        ),
        "error_type": (
            raw.get(
                "error_type"
            )
        ),
        "error": error,
    }


def run_gate() -> dict[
    str,
    Any,
]:

    repository = verify_repository()

    original_failure = (
        verify_original_failure()
    )

    require(
        not PASS_EVIDENCE_PATH.exists(),
        "RECOVERY_PASS_EVIDENCE_ALREADY_EXISTS",
    )

    require(
        not BLOCKED_EVIDENCE_PATH.exists(),
        "RECOVERY_BLOCKED_EVIDENCE_ALREADY_EXISTS",
    )

    before = (
        _controller.inspect_state(
            repo_root=REPO_ROOT
        )
    )

    require(
        before.observation_count == 0,
        "RECOVERY_REQUIRES_ZERO_R03_OBSERVATIONS",
    )

    require(
        before.anchor_count == 0,
        "RECOVERY_REQUIRES_ZERO_R03_ANCHORS",
    )

    require(
        before.matured_outcome_count == 0,
        "RECOVERY_REQUIRES_ZERO_R03_OUTCOMES",
    )

    require(
        before.next_action
        ==
        _controller.ACTION_CAPTURE_NEW_OBSERVATION,
        (
            "RECOVERY_CAPTURE_NOT_AUTHORIZED:"
            f"{before.next_action}"
        ),
    )

    initialized = False

    try:

        initialized = bool(
            mt5.initialize()
        )

        require(
            initialized,
            "MT5_INITIALIZE_FAILED",
        )

        read_only_api = (
            _acquisition
            .MT5ReadOnlyCapabilityFacade(
                mt5
            )
        )

        acquisition = (
            _acquisition
            .MT5ReadOnlyForwardAcquisitionAdapter(
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
            bool(
                str(
                    broker_symbol
                ).strip()
            ),
            "BROKER_SYMBOL_EMPTY",
        )

        bid_ask = (
            _legacy_capture
            .verify_bid_ask(
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
            snapshot.is_synthetic is False,
            "SNAPSHOT_NOT_GENUINE",
        )

        require(
            snapshot.canonical_instrument
            ==
            "XAUUSD",
            "CANONICAL_INSTRUMENT_MISMATCH",
        )

        require(
            snapshot.broker_symbol
            ==
            broker_symbol,
            "BROKER_SYMBOL_CHANGED_DURING_CAPTURE",
        )

        require(
            snapshot.authority
            is not None,
            "SNAPSHOT_AUTHORITY_MISSING",
        )

        (
            normalized_market_data,
            timestamp_dtypes_before,
            timestamp_dtypes_after,
        ) = (
            _legacy_capture
            .normalize_market_timestamp_resolution(
                snapshot.market_data
            )
        )

        normalized_snapshot_id = (
            _acquisition
            .compute_canonical_snapshot_id(
                normalized_market_data
            )
        )

        require(
            normalized_snapshot_id
            ==
            snapshot.source_snapshot_id,
            "TIMESTAMP_NORMALIZATION_CHANGED_SNAPSHOT_ID",
        )

        feature_result = (
            _pipeline
            .PortableFeaturePipeline()
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
            _runtime.FEATURE_COUNT,
            "FEATURE_COUNT_MISMATCH",
        )

        require(
            feature_result.feature_columns_sha256
            ==
            _runtime.FEATURE_COLUMNS_SHA256,
            "FEATURE_COLUMNS_HASH_MISMATCH",
        )

        require(
            feature_result.row_count > 0,
            "FEATURE_RESULT_EMPTY",
        )

        result = (
            _controller
            .capture_new_observation_from_snapshot(
                snapshot=snapshot,
                feature_result=feature_result,
                repo_root=REPO_ROOT,
            )
        )

        after = (
            _controller.inspect_state(
                repo_root=REPO_ROOT
            )
        )

        require(
            after.observation_count == 1,
            "POST_RECOVERY_OBSERVATION_COUNT_NOT_ONE",
        )

        require(
            after.anchor_count == 1,
            "POST_RECOVERY_ANCHOR_COUNT_NOT_ONE",
        )

        require(
            after.pending_count == 1,
            "POST_RECOVERY_PENDING_COUNT_NOT_ONE",
        )

        require(
            after.matured_outcome_count == 0,
            "OUTCOME_MATURED_DURING_RECOVERY_CAPTURE",
        )

        require(
            after.next_action
            ==
            _controller.ACTION_CHECK_PENDING_MATURITY,
            "POST_RECOVERY_NEXT_ACTION_MISMATCH",
        )

        evidence = {
            "gate_id": GATE_ID,
            "status": "PASS",
            "generated_at_utc": (
                now_utc_iso()
            ),
            "repository": repository,
            "original_blocked_attempt_preserved": True,
            "original_blocked_attempt": (
                original_failure
            ),
            "genuine_mt5_acquisition": True,
            "broker_symbol": broker_symbol,
            "canonical_instrument": (
                snapshot.canonical_instrument
            ),
            "decision_time_utc": (
                result[
                    "decision_time_utc"
                ]
            ),
            "source_snapshot_id": (
                snapshot.source_snapshot_id
            ),
            "logical_observation_id": (
                result[
                    "logical_observation_id"
                ]
            ),
            "prediction": {
                "class": (
                    result[
                        "predicted_class"
                    ]
                ),
                "label": (
                    result[
                        "predicted_label"
                    ]
                ),
                "probability_short": (
                    result[
                        "probability_short"
                    ]
                ),
                "probability_no_trade": (
                    result[
                        "probability_no_trade"
                    ]
                ),
                "probability_long": (
                    result[
                        "probability_long"
                    ]
                ),
            },
            "bid_ask_check": bid_ask,
            "timestamp_dtypes_before": (
                timestamp_dtypes_before
            ),
            "timestamp_dtypes_after": (
                timestamp_dtypes_after
            ),
            "persistence": {
                "order": (
                    "ANCHOR_FIRST_THEN_OBSERVATION"
                ),
                "anchor_appended": (
                    result[
                        "anchor_appended"
                    ]
                ),
                "observation_appended": (
                    result[
                        "observation_appended"
                    ]
                ),
            },
            "state_before": (
                before.to_dict()
            ),
            "state_after": (
                after.to_dict()
            ),
            "outcome_matured": False,
            "performance_evaluated": False,
            "pnl_evaluated": False,
            "live_authorized": False,
            "execution_authorized": False,
        }

        write_create_only_json(
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


def write_blocked(
    exc: BaseException,
) -> None:

    try:

        state = (
            _controller
            .inspect_state(
                repo_root=REPO_ROOT
            )
            .to_dict()
        )

    except Exception:
        state = None

    document = {
        "gate_id": GATE_ID,
        "status": "BLOCKED",
        "generated_at_utc": (
            now_utc_iso()
        ),
        "original_blocked_attempt_preserved": True,
        "error_type": (
            type(
                exc
            ).__name__
        ),
        "error": (
            " ".join(
                str(
                    exc
                ).split()
            )[:2000]
        ),
        "r03_collection_state": state,
        "performance_evaluated": False,
        "pnl_evaluated": False,
        "live_authorized": False,
        "execution_authorized": False,
    }

    try:
        write_create_only_json(
            BLOCKED_EVIDENCE_PATH,
            document,
        )
    except Exception:
        pass


def main() -> int:

    try:

        result = run_gate()

    except Exception as exc:

        write_blocked(
            exc
        )

        print(
            "GATE_15D_C_B2D_G7_H_E_B_R2_STATUS=BLOCKED"
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
            "PERFORMANCE_EVALUATED=false"
        )

        print(
            "PNL_EVALUATED=false"
        )

        print(
            "LIVE_AUTHORIZED=false"
        )

        print(
            "EXECUTION_AUTHORIZED=false"
        )

        return 2

    print(
        "GATE_15D_C_B2D_G7_H_E_B_R2_STATUS=PASS"
    )

    print(
        "ORIGINAL_BLOCKED_ATTEMPT_PRESERVED=true"
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
        "PREDICTED_CLASS="
        +
        str(
            result[
                "prediction"
            ][
                "class"
            ]
        )
    )

    print(
        "PREDICTED_LABEL="
        +
        str(
            result[
                "prediction"
            ][
                "label"
            ]
        )
    )

    print(
        "ANCHOR_APPENDED="
        +
        str(
            result[
                "persistence"
            ][
                "anchor_appended"
            ]
        ).lower()
    )

    print(
        "OBSERVATION_APPENDED="
        +
        str(
            result[
                "persistence"
            ][
                "observation_appended"
            ]
        ).lower()
    )

    print(
        "PENDING_OUTCOMES=1"
    )

    print(
        "OUTCOME_MATURED=false"
    )

    print(
        "PERFORMANCE_EVALUATED=false"
    )

    print(
        "PNL_EVALUATED=false"
    )

    print(
        "LIVE_AUTHORIZED=false"
    )

    print(
        "EXECUTION_AUTHORIZED=false"
    )

    return 0


if __name__ == "__main__":

    raise SystemExit(
        main()
    )