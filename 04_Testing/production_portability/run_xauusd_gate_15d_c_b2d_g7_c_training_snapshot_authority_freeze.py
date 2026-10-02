from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

import pandas as pd


REPO_ROOT = Path(__file__).resolve().parents[2]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(REPO_ROOT),
    )


GATE_ID = (
    "GATE_15D_C_B2D_G7_C_TRAINING_SNAPSHOT_AUTHORITY_FREEZE"
)

SCHEMA_VERSION = "1.0.0"

BASE_AUTHORITY_COMMIT = (
    "5ab1fdbe822e0e1f723f2a6a5f75da3544233f09"
)

EXPECTED_G7B_FINGERPRINT = (
    "5e1d643c9a65d5709593bf7e3163895cc087ffb18eb0330ae0e80886d4fae0f3"
)


CANONICAL_ROOT = (
    REPO_ROOT
    / "01_Data"
    / "Canonical"
)

CONTRACT_REL = (
    "02_AI/Models/"
    "frozen_c04_remediation_training_snapshot_authority.py"
)

G7B_CONTRACT_REL = (
    "02_AI/Models/"
    "frozen_c04_remediation_data_authority_contract.py"
)

G7B_EVIDENCE_REL = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g7_b_remediation_data_authority_freeze_evidence.json"
)

SOURCE_READINESS_EVIDENCE_REL = (
    "04_Testing/evidence/research/portable_331/train/"
    "xauusd_portable_331_train_input_readiness.json"
)

SOURCE_C04_FIT_EVIDENCE_REL = (
    "04_Testing/evidence/research/portable_331/train/"
    "xauusd_portable_331_c04_full_train_model_fit.json"
)

OBSERVATION_LEDGER_REL = (
    "01_Data/Shadow/"
    "xauusd_frozen_c04_shadow_observations.jsonl"
)

ANCHOR_LEDGER_REL = (
    "01_Data/Shadow/"
    "xauusd_frozen_c04_forward_outcome_anchors.jsonl"
)

OUTCOME_LEDGER_REL = (
    "01_Data/Shadow/"
    "xauusd_frozen_c04_forward_outcomes.jsonl"
)

G7C_RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_c_training_snapshot_authority_freeze.py"
)

G7C_TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g7_c_training_snapshot_authority_freeze.py"
)

EVIDENCE_REL = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g7_c_training_snapshot_authority_freeze_evidence.json"
)

EVIDENCE_PATH = (
    REPO_ROOT
    / EVIDENCE_REL
)


ALLOWED_LOCAL_PATHS = {
    CONTRACT_REL,
    G7C_RUNNER_REL,
    G7C_TEST_REL,
    EVIDENCE_REL,
}


HASH_BOUND_DEPENDENCIES = (
    CONTRACT_REL,
    G7B_CONTRACT_REL,
    G7B_EVIDENCE_REL,
    SOURCE_READINESS_EVIDENCE_REL,
    SOURCE_C04_FIT_EVIDENCE_REL,
    G7C_RUNNER_REL,
    G7C_TEST_REL,
)


_contract: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_remediation_training_snapshot_authority"
)

_g7b: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_remediation_data_authority_contract"
)


class G7CFreezeError(RuntimeError):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise G7CFreezeError(
            reason
        )


def require_mapping(
    value: Any,
    reason: str,
) -> Mapping[str, Any]:

    if not isinstance(
        value,
        Mapping,
    ):
        raise G7CFreezeError(
            reason
        )

    return value


def require_list(
    value: Any,
    reason: str,
) -> list[Any]:

    if not isinstance(
        value,
        list,
    ):
        raise G7CFreezeError(
            reason
        )

    return value


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

            block = handle.read(
                1024
                *
                1024
            )

            if not block:
                break

            digest.update(
                block
            )

    return digest.hexdigest()


def canonical_sha256(
    path: Path,
) -> str:

    require(
        path.is_file(),
        f"FILE_MISSING:{path}",
    )

    data = (
        path.read_bytes()
        .replace(
            b"\r\n",
            b"\n",
        )
        .replace(
            b"\r",
            b"\n",
        )
    )

    return hashlib.sha256(
        data
    ).hexdigest()


def feature_columns_sha256(
    feature_columns: list[str],
) -> str:

    payload = json.dumps(
        feature_columns,
        separators=(
            ",",
            ":",
        ),
        ensure_ascii=False,
        allow_nan=False,
    ).encode(
        "utf-8"
    )

    return hashlib.sha256(
        payload
    ).hexdigest()


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

    result = git_process(
        *args
    )

    require(
        result.returncode == 0,
        (
            "GIT_COMMAND_FAILED:"
            + " ".join(args)
            + ":"
            + result.stderr.strip()
        ),
    )

    return result.stdout.rstrip(
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

        if len(line) < 4:
            continue

        value = line[
            3:
        ].strip()

        if " -> " in value:

            value = value.split(
                " -> ",
                1,
            )[
                1
            ]

        if (
            value.startswith('"')
            and
            value.endswith('"')
        ):
            value = value[
                1:-1
            ]

        paths.add(
            value.replace(
                "\\",
                "/",
            )
        )

    return paths


def load_json(
    path: Path,
) -> dict[str, Any]:

    require(
        path.is_file(),
        f"JSON_FILE_MISSING:{path}",
    )

    payload = path.read_bytes()

    if payload.startswith(
        (
            b"\xff\xfe",
            b"\xfe\xff",
        )
    ):

        text = payload.decode(
            "utf-16"
        )

    else:

        text = payload.decode(
            "utf-8-sig"
        )

    value = json.loads(
        text
    )

    if not isinstance(
        value,
        dict,
    ):
        raise G7CFreezeError(
            f"JSON_ROOT_NOT_OBJECT:{path}"
        )

    return value


def write_json(
    path: Path,
    value: Mapping[str, Any],
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
            dict(
                value
            ),
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


def verify_repository() -> dict[str, Any]:

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
        f"UNEXPECTED_BRANCH:{branch}",
    )

    require(
        head == origin,
        (
            "HEAD_ORIGIN_MAIN_DIVERGENCE:"
            f"{head}!={origin}"
        ),
    )

    require(
        head == BASE_AUTHORITY_COMMIT,
        (
            "UNEXPECTED_BASE_HEAD:"
            f"{head}:expected="
            f"{BASE_AUTHORITY_COMMIT}"
        ),
    )

    unexpected = (
        status_paths()
        -
        ALLOWED_LOCAL_PATHS
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
        "branch": branch,
        "head": head,
        "origin_main": origin,
    }


def verify_upstream_authority() -> dict[str, Any]:

    evidence = load_json(
        REPO_ROOT
        /
        G7B_EVIDENCE_REL
    )

    require(
        evidence.get(
            "status"
        )
        ==
        "PASS",
        "G7B_STATUS_NOT_PASS",
    )

    contract_block = require_mapping(
        evidence.get(
            "data_authority_contract"
        ),
        "G7B_CONTRACT_BLOCK_MISSING",
    )

    require(
        contract_block.get(
            "contract_fingerprint_sha256"
        )
        ==
        EXPECTED_G7B_FINGERPRINT,
        "G7B_EVIDENCE_FINGERPRINT_MISMATCH",
    )

    require(
        _g7b.contract_fingerprint_sha256()
        ==
        EXPECTED_G7B_FINGERPRINT,
        "CURRENT_G7B_FINGERPRINT_MISMATCH",
    )

    return {
        "status": "PASS",
        "contract_fingerprint_sha256": (
            EXPECTED_G7B_FINGERPRINT
        ),
    }


def verify_research_lineage() -> dict[str, Any]:

    readiness = load_json(
        REPO_ROOT
        /
        SOURCE_READINESS_EVIDENCE_REL
    )

    fit = load_json(
        REPO_ROOT
        /
        SOURCE_C04_FIT_EVIDENCE_REL
    )

    portable = require_mapping(
        readiness.get(
            "portable_artifact"
        ),
        "PORTABLE_ARTIFACT_EVIDENCE_MISSING",
    )

    source = require_mapping(
        readiness.get(
            "source_artifact"
        ),
        "SOURCE_ARTIFACT_EVIDENCE_MISSING",
    )

    split_validation = require_mapping(
        readiness.get(
            "split_validation"
        ),
        "SPLIT_VALIDATION_MISSING",
    )

    portable_split = require_mapping(
        split_validation.get(
            "portable"
        ),
        "PORTABLE_SPLIT_VALIDATION_MISSING",
    )

    split_rows = require_mapping(
        portable_split.get(
            "split_rows"
        ),
        "PORTABLE_SPLIT_ROWS_MISSING",
    )

    require(
        portable.get(
            "dataset_id"
        )
        ==
        _contract.DATASET_ID,
        "PORTABLE_DATASET_ID_MISMATCH",
    )

    require(
        portable.get(
            "dataset_sha256"
        )
        ==
        _contract.DATASET_SHA256,
        "PORTABLE_DATASET_HASH_MISMATCH",
    )

    require(
        portable.get(
            "manifest_sha256"
        )
        ==
        _contract.MANIFEST_SHA256,
        "PORTABLE_MANIFEST_HASH_MISMATCH",
    )

    require(
        portable.get(
            "feature_columns_sha256"
        )
        ==
        _contract.FEATURE_COLUMNS_SHA256,
        "PORTABLE_FEATURE_HASH_MISMATCH",
    )

    require(
        int(
            portable.get(
                "feature_count",
                -1,
            )
        )
        ==
        _contract.FEATURE_COUNT,
        "PORTABLE_FEATURE_COUNT_MISMATCH",
    )

    require(
        portable.get(
            "training_contract_version"
        )
        ==
        _contract.TRAINING_CONTRACT_VERSION,
        "PORTABLE_TRAINING_CONTRACT_MISMATCH",
    )

    require(
        source.get(
            "dataset_id"
        )
        ==
        _contract.SOURCE_DATASET_ID,
        "SOURCE_DATASET_ID_MISMATCH",
    )

    require(
        source.get(
            "dataset_sha256"
        )
        ==
        _contract.SOURCE_DATASET_SHA256,
        "SOURCE_DATASET_HASH_MISMATCH",
    )

    require(
        source.get(
            "manifest_sha256"
        )
        ==
        _contract.SOURCE_MANIFEST_SHA256,
        "SOURCE_MANIFEST_HASH_MISMATCH",
    )

    require(
        source.get(
            "training_contract_version"
        )
        ==
        _contract.SOURCE_TRAINING_CONTRACT_VERSION,
        "SOURCE_TRAINING_CONTRACT_MISMATCH",
    )

    require(
        int(
            portable_split.get(
                "total_rows",
                -1,
            )
        )
        ==
        _contract.TOTAL_ROWS,
        "PORTABLE_TOTAL_ROWS_MISMATCH",
    )

    observed_split_rows = {
        str(
            key
        ): int(
            value
        )
        for (
            key,
            value,
        )
        in split_rows.items()
    }

    require(
        observed_split_rows
        ==
        _contract.EXPECTED_SPLIT_COUNTS,
        "PORTABLE_SPLIT_COUNTS_MISMATCH",
    )

    require(
        portable_split.get(
            "train_is_contiguous_prefix"
        )
        is True,
        "PORTABLE_TRAIN_PREFIX_NOT_CONFIRMED",
    )

    model_record = require_mapping(
        fit.get(
            "model_record"
        ),
        "C04_MODEL_RECORD_MISSING",
    )

    require(
        model_record.get(
            "dataset_id"
        )
        ==
        _contract.DATASET_ID,
        "C04_DATASET_ID_AUTHORITY_MISMATCH",
    )

    require(
        model_record.get(
            "dataset_sha256"
        )
        ==
        _contract.DATASET_SHA256,
        "C04_DATASET_AUTHORITY_MISMATCH",
    )

    require(
        model_record.get(
            "manifest_sha256"
        )
        ==
        _contract.MANIFEST_SHA256,
        "C04_MANIFEST_AUTHORITY_MISMATCH",
    )

    require(
        model_record.get(
            "feature_columns_sha256"
        )
        ==
        _contract.FEATURE_COLUMNS_SHA256,
        "C04_FEATURE_AUTHORITY_MISMATCH",
    )

    require(
        int(
            model_record.get(
                "feature_count",
                -1,
            )
        )
        ==
        _contract.FEATURE_COUNT,
        "C04_FEATURE_COUNT_AUTHORITY_MISMATCH",
    )

    require(
        int(
            model_record.get(
                "train_rows",
                -1,
            )
        )
        ==
        _contract.TRAIN_ROWS,
        "C04_TRAIN_ROWS_AUTHORITY_MISMATCH",
    )

    return {
        "status": "PASS",
        "dataset_id": (
            _contract.DATASET_ID
        ),
        "dataset_sha256": (
            _contract.DATASET_SHA256
        ),
        "manifest_sha256": (
            _contract.MANIFEST_SHA256
        ),
        "feature_columns_sha256": (
            _contract.FEATURE_COLUMNS_SHA256
        ),
        "feature_count": (
            _contract.FEATURE_COUNT
        ),
        "total_rows": (
            _contract.TOTAL_ROWS
        ),
        "split_counts": dict(
            _contract.EXPECTED_SPLIT_COUNTS
        ),
    }


def discover_manifest() -> Path:

    require(
        CANONICAL_ROOT.is_dir(),
        (
            "CANONICAL_ROOT_MISSING:"
            f"{CANONICAL_ROOT}"
        ),
    )

    matches: list[Path] = []

    for path in CANONICAL_ROOT.rglob(
        "*.manifest.json"
    ):

        if not path.is_file():
            continue

        if (
            sha256_file(
                path
            )
            ==
            _contract.MANIFEST_SHA256
        ):

            matches.append(
                path
            )

    require(
        len(
            matches
        )
        ==
        1,
        (
            "EXPECTED_EXACTLY_ONE_AUTHORIZED_MANIFEST:"
            f"found={len(matches)}"
        ),
    )

    return matches[
        0
    ]


def verify_local_snapshot() -> dict[str, Any]:

    manifest_path = discover_manifest()

    manifest = load_json(
        manifest_path
    )

    require(
        manifest.get(
            "dataset_id"
        )
        ==
        _contract.DATASET_ID,
        "LOCAL_DATASET_ID_MISMATCH",
    )

    require(
        manifest.get(
            "training_contract_version"
        )
        ==
        _contract.TRAINING_CONTRACT_VERSION,
        "LOCAL_TRAINING_CONTRACT_MISMATCH",
    )

    require(
        int(
            manifest.get(
                "row_count",
                -1,
            )
        )
        ==
        _contract.TOTAL_ROWS,
        "LOCAL_ROW_COUNT_MANIFEST_MISMATCH",
    )

    require(
        int(
            manifest.get(
                "feature_count",
                -1,
            )
        )
        ==
        _contract.FEATURE_COUNT,
        "LOCAL_FEATURE_COUNT_MISMATCH",
    )

    feature_columns_raw = require_list(
        manifest.get(
            "feature_columns"
        ),
        "LOCAL_FEATURE_COLUMNS_MISSING",
    )

    feature_columns: list[str] = [
        str(
            value
        )
        for value
        in feature_columns_raw
    ]

    require(
        len(
            feature_columns
        )
        ==
        _contract.FEATURE_COUNT,
        "LOCAL_FEATURE_COLUMNS_COUNT_MISMATCH",
    )

    require(
        len(
            set(
                feature_columns
            )
        )
        ==
        len(
            feature_columns
        ),
        "LOCAL_FEATURE_COLUMNS_NOT_UNIQUE",
    )

    derived_feature_hash = (
        feature_columns_sha256(
            feature_columns
        )
    )

    require(
        derived_feature_hash
        ==
        _contract.FEATURE_COLUMNS_SHA256,
        (
            "LOCAL_FEATURE_COLUMNS_HASH_MISMATCH:"
            f"{derived_feature_hash}"
        ),
    )

    filename = str(
        manifest.get(
            "dataset_filename",
            "",
        )
    ).strip()

    require(
        bool(
            filename
        ),
        "LOCAL_DATASET_FILENAME_MISSING",
    )

    dataset_path = (
        manifest_path.parent
        /
        filename
    )

    require(
        dataset_path.is_file(),
        "LOCAL_DATASET_FILE_MISSING",
    )

    require(
        sha256_file(
            dataset_path
        )
        ==
        _contract.DATASET_SHA256,
        "LOCAL_DATASET_SHA256_MISMATCH",
    )

    frame = pd.read_csv(
        dataset_path,
        usecols=[
            "decision_time",
            "dataset_split",
        ],
    )

    require(
        len(
            frame
        )
        ==
        _contract.TOTAL_ROWS,
        "LOCAL_DATASET_ROW_COUNT_MISMATCH",
    )

    split_counts = {
        str(
            key
        ): int(
            value
        )
        for (
            key,
            value,
        )
        in frame[
            "dataset_split"
        ]
        .value_counts()
        .to_dict()
        .items()
    }

    require(
        split_counts
        ==
        _contract.EXPECTED_SPLIT_COUNTS,
        (
            "LOCAL_SPLIT_COUNTS_MISMATCH:"
            f"{split_counts}"
        ),
    )

    decision_time = pd.to_datetime(
        frame[
            "decision_time"
        ],
        utc=True,
        errors="raise",
    )

    require(
        not bool(
            decision_time
            .duplicated()
            .any()
        ),
        "DUPLICATE_DECISION_TIME",
    )

    require(
        bool(
            decision_time
            .is_monotonic_increasing
        ),
        "DECISION_TIME_NOT_MONOTONIC",
    )

    cutoff = pd.Timestamp(
        _contract.RESEARCH_DATA_CUTOFF_UTC
    )

    maximum = decision_time.max()

    minimum = decision_time.min()

    require(
        pd.notna(
            maximum
        ),
        "MAXIMUM_DECISION_TIME_MISSING",
    )

    require(
        pd.notna(
            minimum
        ),
        "MINIMUM_DECISION_TIME_MISSING",
    )

    require(
        maximum
        <=
        cutoff,
        (
            "DATA_EXTENDS_PAST_RESEARCH_CUTOFF:"
            f"{maximum.isoformat()}"
        ),
    )

    split_values: list[str] = (
        frame[
            "dataset_split"
        ]
        .astype(
            str
        )
        .tolist()
    )

    first_non_train = next(
        (
            index
            for (
                index,
                value,
            )
            in enumerate(
                split_values
            )
            if value
            !=
            "TRAIN"
        ),
        len(
            split_values
        ),
    )

    require(
        all(
            value
            ==
            "TRAIN"
            for value
            in split_values[
                :first_non_train
            ]
        ),
        "TRAIN_PREFIX_INVALID",
    )

    require(
        all(
            value
            !=
            "TRAIN"
            for value
            in split_values[
                first_non_train:
            ]
        ),
        "TRAIN_NOT_CONTIGUOUS_PREFIX",
    )

    return {
        "status": "PASS",
        "dataset_id": (
            _contract.DATASET_ID
        ),
        "dataset_sha256": (
            _contract.DATASET_SHA256
        ),
        "manifest_sha256": (
            _contract.MANIFEST_SHA256
        ),
        "feature_columns_sha256": (
            derived_feature_hash
        ),
        "feature_count": (
            len(
                feature_columns
            )
        ),
        "row_count": (
            len(
                frame
            )
        ),
        "split_counts": (
            split_counts
        ),
        "minimum_decision_time_utc": (
            minimum.isoformat()
        ),
        "maximum_decision_time_utc": (
            maximum.isoformat()
        ),
        "research_data_cutoff_utc": (
            _contract.RESEARCH_DATA_CUTOFF_UTC
        ),
        "train_is_contiguous_prefix": True,
        "dataset_path_emitted": False,
        "manifest_path_emitted": False,
    }


def verify_contract() -> dict[str, Any]:

    require(
        _contract.CONTRACT_ID
        ==
        "FROZEN_C04_REMEDIATION_TRAINING_SNAPSHOT_AUTHORITY_V1",
        "CONTRACT_ID_MISMATCH",
    )

    require(
        _contract.BASE_AUTHORITY_COMMIT
        ==
        BASE_AUTHORITY_COMMIT,
        "CONTRACT_BASE_AUTHORITY_MISMATCH",
    )

    require(
        _contract.G7B_CONTRACT_FINGERPRINT_SHA256
        ==
        EXPECTED_G7B_FINGERPRINT,
        "CONTRACT_G7B_LINKAGE_MISMATCH",
    )

    require(
        _contract.TRAIN_MAY_BE_USED_FOR_FITTING
        is True,
        "TRAIN_FIT_AUTHORITY_MISSING",
    )

    require(
        _contract.VALIDATION_MAY_BE_USED_FOR_RESEARCH_SELECTION
        is True,
        "VALIDATION_RESEARCH_AUTHORITY_MISSING",
    )

    require(
        _contract.TEST_MAY_BE_USED_BEFORE_CANDIDATE_FREEZE
        is False,
        "PREMATURE_TEST_ACCESS_ALLOWED",
    )

    require(
        _contract.TEST_MAY_SELECT_MODEL
        is False,
        "TEST_MODEL_SELECTION_ALLOWED",
    )

    require(
        _contract.TEST_MAY_SELECT_FEATURES
        is False,
        "TEST_FEATURE_SELECTION_ALLOWED",
    )

    require(
        _contract.TEST_MAY_SELECT_HYPERPARAMETERS
        is False,
        "TEST_HYPERPARAMETER_SELECTION_ALLOWED",
    )

    require(
        _contract.TEST_MAY_SELECT_THRESHOLDS
        is False,
        "TEST_THRESHOLD_SELECTION_ALLOWED",
    )

    require(
        _contract.TEST_MAY_SELECT_CALIBRATION
        is False,
        "TEST_CALIBRATION_SELECTION_ALLOWED",
    )

    require(
        _contract.FORWARD_30_MAY_BE_USED_FOR_TRAINING
        is False,
        "FORWARD_TRAINING_ALLOWED",
    )

    require(
        _contract.FORWARD_30_MAY_BE_USED_FOR_SELECTION
        is False,
        "FORWARD_SELECTION_ALLOWED",
    )

    forbidden = (
        _contract.THIS_GATE_READS_MODEL_FEATURE_VALUES,
        _contract.THIS_GATE_READS_TARGET_VALUES,
        _contract.THIS_GATE_TRAINS_MODEL,
        _contract.THIS_GATE_FITS_PREPROCESSOR,
        _contract.THIS_GATE_SELECTS_MODEL,
        _contract.THIS_GATE_SELECTS_FEATURES,
        _contract.THIS_GATE_TUNES_HYPERPARAMETERS,
        _contract.THIS_GATE_TUNES_THRESHOLDS,
        _contract.THIS_GATE_CALIBRATES_PROBABILITIES,
        _contract.THIS_GATE_EVALUATES_VALIDATION,
        _contract.THIS_GATE_EVALUATES_TEST,
        _contract.THIS_GATE_WRITES_RUNTIME_LEDGERS,
        _contract.THIS_GATE_ACQUIRES_MARKET_DATA,
        _contract.THIS_GATE_EVALUATES_PNL,
        _contract.LIVE_AUTHORIZED,
        _contract.EXECUTION_AUTHORIZED,
    )

    require(
        not any(
            forbidden
        ),
        "G7C_FORBIDDEN_ACTION_ENABLED",
    )

    require(
        _contract.THIS_GATE_DISCOVERS_LOCAL_ARTIFACT
        is True,
        "LOCAL_ARTIFACT_DISCOVERY_NOT_ENABLED",
    )

    require(
        _contract.THIS_GATE_VERIFIES_DATASET_HASH
        is True,
        "DATASET_HASH_VERIFICATION_NOT_ENABLED",
    )

    require(
        _contract.THIS_GATE_VERIFIES_MANIFEST_HASH
        is True,
        "MANIFEST_HASH_VERIFICATION_NOT_ENABLED",
    )

    fingerprint = (
        _contract
        .contract_fingerprint_sha256()
    )

    require(
        fingerprint
        ==
        _contract.CONTRACT_FINGERPRINT_SHA256,
        "CONTRACT_FINGERPRINT_MISMATCH",
    )

    return {
        "status": "PASS",
        "contract_id": (
            _contract.CONTRACT_ID
        ),
        "contract_fingerprint_sha256": (
            fingerprint
        ),
    }


def runtime_hashes() -> dict[str, str]:

    return {
        "observation": sha256_file(
            REPO_ROOT
            /
            OBSERVATION_LEDGER_REL
        ),
        "anchor": sha256_file(
            REPO_ROOT
            /
            ANCHOR_LEDGER_REL
        ),
        "outcome": sha256_file(
            REPO_ROOT
            /
            OUTCOME_LEDGER_REL
        ),
    }


def dependency_hashes() -> dict[str, str]:

    result: dict[str, str] = {}

    for relative in (
        HASH_BOUND_DEPENDENCIES
    ):

        path = (
            REPO_ROOT
            /
            relative
        )

        require(
            path.is_file(),
            (
                "HASH_BOUND_FILE_MISSING:"
                f"{relative}"
            ),
        )

        result[
            relative
        ] = canonical_sha256(
            path
        )

    return result


def run_gate() -> dict[str, Any]:

    before = runtime_hashes()

    repository = (
        verify_repository()
    )

    upstream = (
        verify_upstream_authority()
    )

    lineage = (
        verify_research_lineage()
    )

    contract = (
        verify_contract()
    )

    snapshot = (
        verify_local_snapshot()
    )

    after = runtime_hashes()

    require(
        before
        ==
        after,
        "RUNTIME_LEDGER_CHANGED_DURING_G7C_FREEZE",
    )

    evidence = {
        "gate_id": GATE_ID,
        "schema_version": SCHEMA_VERSION,
        "status": "PASS",
        "base_authority_commit": (
            BASE_AUTHORITY_COMMIT
        ),
        "repository_authority": (
            repository
        ),
        "g7b_authority": (
            upstream
        ),
        "research_lineage": (
            lineage
        ),
        "snapshot_contract": (
            contract
        ),
        "authorized_training_snapshot": (
            snapshot
        ),
        "runtime_ledger_raw_sha256": (
            after
        ),
        "hashing_semantics": (
            "GIT_TEXT_CANONICAL_LF_SHA256"
        ),
        "feature_columns_hashing_semantics": (
            "JSON_COMPACT_UTF8_SHA256_ORDER_PRESERVED"
        ),
        "hash_bound_dependencies": (
            dependency_hashes()
        ),
        "hash_bound_file_count": (
            len(
                HASH_BOUND_DEPENDENCIES
            )
        ),
        "dataset_discovered": True,
        "dataset_hash_verified": True,
        "manifest_hash_verified": True,
        "feature_columns_hash_verified": True,
        "feature_values_loaded": False,
        "target_values_loaded": False,
        "retraining_performed": False,
        "refitting_performed": False,
        "model_reselection_performed": False,
        "feature_reselection_performed": False,
        "hyperparameter_tuning_performed": False,
        "threshold_tuning_performed": False,
        "calibration_performed": False,
        "validation_evaluated": False,
        "test_evaluated": False,
        "pnl_evaluated": False,
        "market_data_acquired": False,
        "ledger_write_performed": False,
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

    except Exception as exc:

        print(
            "GATE_15D_C_B2D_G7_C_FREEZE_STATUS=BLOCKED"
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
            "RETRAINING_PERFORMED=false"
        )

        print(
            "TEST_EVALUATED=false"
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

    snapshot = require_mapping(
        evidence.get(
            "authorized_training_snapshot"
        ),
        "EVIDENCE_SNAPSHOT_BLOCK_MISSING",
    )

    contract = require_mapping(
        evidence.get(
            "snapshot_contract"
        ),
        "EVIDENCE_CONTRACT_BLOCK_MISSING",
    )

    split_counts = require_mapping(
        snapshot.get(
            "split_counts"
        ),
        "EVIDENCE_SPLIT_COUNTS_MISSING",
    )

    print(
        "GATE_15D_C_B2D_G7_C_FREEZE_STATUS=PASS"
    )

    print(
        "BASE_AUTHORITY_COMMIT="
        +
        BASE_AUTHORITY_COMMIT
    )

    print(
        "CONTRACT_ID="
        +
        str(
            contract[
                "contract_id"
            ]
        )
    )

    print(
        "CONTRACT_FINGERPRINT_SHA256="
        +
        str(
            contract[
                "contract_fingerprint_sha256"
            ]
        )
    )

    print(
        "DATASET_ID="
        +
        str(
            snapshot[
                "dataset_id"
            ]
        )
    )

    print(
        "DATASET_SHA256="
        +
        str(
            snapshot[
                "dataset_sha256"
            ]
        )
    )

    print(
        "MANIFEST_SHA256="
        +
        str(
            snapshot[
                "manifest_sha256"
            ]
        )
    )

    print(
        "FEATURE_COLUMNS_SHA256="
        +
        str(
            snapshot[
                "feature_columns_sha256"
            ]
        )
    )

    print(
        "FEATURE_COUNT="
        +
        str(
            snapshot[
                "feature_count"
            ]
        )
    )

    print(
        "TOTAL_ROWS="
        +
        str(
            snapshot[
                "row_count"
            ]
        )
    )

    print(
        "TRAIN_ROWS="
        +
        str(
            split_counts[
                "TRAIN"
            ]
        )
    )

    print(
        "VALIDATION_ROWS="
        +
        str(
            split_counts[
                "VALIDATION"
            ]
        )
    )

    print(
        "TEST_ROWS="
        +
        str(
            split_counts[
                "TEST"
            ]
        )
    )

    print(
        "MAXIMUM_DECISION_TIME_UTC="
        +
        str(
            snapshot[
                "maximum_decision_time_utc"
            ]
        )
    )

    print(
        "DATASET_DISCOVERED=true"
    )

    print(
        "DATASET_HASH_VERIFIED=true"
    )

    print(
        "MANIFEST_HASH_VERIFIED=true"
    )

    print(
        "FEATURE_COLUMNS_HASH_VERIFIED=true"
    )

    print(
        "FEATURE_VALUES_LOADED=false"
    )

    print(
        "TARGET_VALUES_LOADED=false"
    )

    print(
        "RETRAINING_PERFORMED=false"
    )

    print(
        "TEST_EVALUATED=false"
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