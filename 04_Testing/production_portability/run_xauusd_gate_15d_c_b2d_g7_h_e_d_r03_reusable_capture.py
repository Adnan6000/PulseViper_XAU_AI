from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

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
    "GATE_15D_C_B2D_G7_H_E_D_"
    "R03_REUSABLE_CAPTURE"
)

FREEZE_BASE_AUTHORITY_COMMIT = (
    "80c05a1270081cafd136cac40309f27302796d15"
)

FREEZE_EVIDENCE_REL = (
    "04_Testing/evidence/research/"
    "portable_331/remediation/"
    "xauusd_gate_15d_c_b2d_g7_h_e_d_"
    "r03_reusable_capture_runner_freeze.json"
)

RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_h_e_d_"
    "r03_reusable_capture.py"
)

FREEZE_RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_h_e_d_"
    "r03_reusable_capture_freeze.py"
)

TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g7_h_e_d_"
    "r03_reusable_capture_freeze.py"
)

FREEZE_EVIDENCE_PATH = (
    REPO_ROOT
    /
    FREEZE_EVIDENCE_REL
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


class G7HEDCaptureError(
    RuntimeError
):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise G7HEDCaptureError(
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


def verify_freeze_authority() -> dict[
    str,
    Any,
]:

    require(
        FREEZE_EVIDENCE_PATH.is_file(),
        "CAPTURE_FREEZE_EVIDENCE_MISSING",
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
        "CAPTURE_FREEZE_EVIDENCE_INVALID",
    )

    require(
        raw.get(
            "status"
        )
        ==
        "PASS",
        "CAPTURE_FREEZE_NOT_PASS",
    )

    require(
        raw.get(
            "base_authority_commit"
        )
        ==
        FREEZE_BASE_AUTHORITY_COMMIT,
        "CAPTURE_FREEZE_BASE_MISMATCH",
    )

    hashes = raw.get(
        "candidate_artifact_hashes"
    )

    require(
        isinstance(
            hashes,
            dict,
        ),
        "CAPTURE_FREEZE_HASHES_MISSING",
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
        "CAPTURE_FREEZE_PATH_SET_MISMATCH",
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
                "CAPTURE_ARTIFACT_HASH_INVALID:"
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
                "CAPTURE_ARTIFACT_CHANGED:"
                f"{relative}"
            ),
        )

    return raw


def verify_repository() -> dict[
    str,
    str,
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
        "CAPTURE_BASE_NOT_ANCESTOR",
    )

    allowed = {
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

    _ = verify_freeze_authority()

    return {
        "branch": branch,
        "head": head,
        "origin_main": origin,
    }


def run_gate() -> dict[
    str,
    Any,
]:

    repository = verify_repository()

    before = (
        _controller.inspect_state(
            repo_root=REPO_ROOT
        )
    )

    require(
        before.next_action
        ==
        _controller.ACTION_CAPTURE_NEW_OBSERVATION,
        (
            "NEW_CAPTURE_NOT_AUTHORIZED:"
            f"{before.next_action}"
        ),
    )

    require(
        before.pending_count == 0,
        (
            "CAPTURE_REQUIRES_ZERO_PENDING:"
            f"{before.pending_count}"
        ),
    )

    require(
        before.orphan_anchor_count == 0,
        (
            "CAPTURE_REQUIRES_ZERO_ORPHAN_ANCHORS:"
            f"{before.orphan_anchor_count}"
        ),
    )

    require(
        before.collection_target_reached
        is False,
        "COLLECTION_TARGET_ALREADY_REACHED",
    )

    observation_count_before = (
        before.observation_count
    )

    anchor_count_before = (
        before.anchor_count
    )

    outcome_count_before = (
        before.matured_outcome_count
    )

    distinct_dates_before = (
        before
        .distinct_matured_observation_utc_dates
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
            acquisition
            .acquire_snapshot(
                enforce_forward_boundaries=True
            )
        )

        require(
            snapshot.is_synthetic
            is False,
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

        require(
            result.get(
                "action"
            )
            ==
            "CAPTURED_NEW_OBSERVATION",
            "UNEXPECTED_CAPTURE_ACTION",
        )

        after = (
            _controller.inspect_state(
                repo_root=REPO_ROOT
            )
        )

        require(
            after.observation_count
            ==
            (
                observation_count_before
                +
                1
            ),
            "POST_CAPTURE_OBSERVATION_COUNT_NOT_INCREMENTED",
        )

        require(
            after.anchor_count
            ==
            (
                anchor_count_before
                +
                1
            ),
            "POST_CAPTURE_ANCHOR_COUNT_NOT_INCREMENTED",
        )

        require(
            after.matured_outcome_count
            ==
            outcome_count_before,
            "OUTCOME_COUNT_CHANGED_DURING_CAPTURE",
        )

        require(
            after.distinct_matured_observation_utc_dates
            ==
            distinct_dates_before,
            "MATURED_DATE_COUNT_CHANGED_DURING_CAPTURE",
        )

        require(
            after.pending_count == 1,
            "POST_CAPTURE_PENDING_COUNT_NOT_ONE",
        )

        require(
            after.pending_logical_observation_id
            ==
            result.get(
                "logical_observation_id"
            ),
            "POST_CAPTURE_PENDING_ID_MISMATCH",
        )

        require(
            after.orphan_anchor_count == 0,
            "POST_CAPTURE_ORPHAN_ANCHOR_CREATED",
        )

        require(
            after.next_action
            ==
            _controller.ACTION_CHECK_PENDING_MATURITY,
            "POST_CAPTURE_NEXT_ACTION_MISMATCH",
        )

        return {
            "status": "CAPTURED",
            "repository": repository,
            "broker_symbol": broker_symbol,
            "canonical_instrument": (
                snapshot.canonical_instrument
            ),
            "decision_time_utc": (
                result.get(
                    "decision_time_utc"
                )
            ),
            "source_snapshot_id": (
                snapshot.source_snapshot_id
            ),
            "logical_observation_id": (
                result.get(
                    "logical_observation_id"
                )
            ),
            "predicted_class": (
                result.get(
                    "predicted_class"
                )
            ),
            "predicted_label": (
                result.get(
                    "predicted_label"
                )
            ),
            "probability_short": (
                result.get(
                    "probability_short"
                )
            ),
            "probability_no_trade": (
                result.get(
                    "probability_no_trade"
                )
            ),
            "probability_long": (
                result.get(
                    "probability_long"
                )
            ),
            "bid_ask_check": bid_ask,
            "timestamp_dtypes_before": (
                timestamp_dtypes_before
            ),
            "timestamp_dtypes_after": (
                timestamp_dtypes_after
            ),
            "anchor_appended": (
                result.get(
                    "anchor_appended"
                )
            ),
            "observation_appended": (
                result.get(
                    "observation_appended"
                )
            ),
            "state_before": (
                before.to_dict()
            ),
            "state_after": (
                after.to_dict()
            ),
            "performance_evaluated": False,
            "pnl_evaluated": False,
            "live_authorized": False,
            "execution_authorized": False,
        }

    finally:

        if initialized:

            try:
                mt5.shutdown()
            except Exception:
                pass


def main() -> int:

    try:

        result = run_gate()

    except Exception as exc:

        print(
            "GATE_15D_C_B2D_G7_H_E_D_STATUS=BLOCKED"
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
        "GATE_15D_C_B2D_G7_H_E_D_STATUS=CAPTURED"
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
                "predicted_class"
            ]
        )
    )

    print(
        "PREDICTED_LABEL="
        +
        str(
            result[
                "predicted_label"
            ]
        )
    )

    print(
        "PROBABILITY_SHORT="
        +
        str(
            result[
                "probability_short"
            ]
        )
    )

    print(
        "PROBABILITY_NO_TRADE="
        +
        str(
            result[
                "probability_no_trade"
            ]
        )
    )

    print(
        "PROBABILITY_LONG="
        +
        str(
            result[
                "probability_long"
            ]
        )
    )

    print(
        "ANCHOR_FIRST_THEN_OBSERVATION=true"
    )

    print(
        "ANCHOR_APPENDED="
        +
        str(
            result[
                "anchor_appended"
            ]
        ).lower()
    )

    print(
        "OBSERVATION_APPENDED="
        +
        str(
            result[
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