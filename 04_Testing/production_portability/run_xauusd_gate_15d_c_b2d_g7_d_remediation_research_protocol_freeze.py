from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(REPO_ROOT),
    )


GATE_ID = (
    "GATE_15D_C_B2D_G7_D_REMEDIATION_RESEARCH_PROTOCOL_FREEZE"
)

SCHEMA_VERSION = "1.0.0"

BASE_AUTHORITY_COMMIT = (
    "03dfb354bdb99a8a334aa6408b9edfd4d21bc096"
)

EXPECTED_G7C_FINGERPRINT = (
    "11302c424f05aab2fbd640d644b30d3df0b013d3b9e1b559b29e325ee2f99b50"
)

EXPECTED_HISTORICAL_REGISTRY_FINGERPRINT = (
    "b8088bb34ce8940f7de5946fbb9b0fd20f40d7cc93a76b76fd7975591f00066c"
)

EXPECTED_HISTORICAL_RESEARCH_PROTOCOL_FINGERPRINT = (
    "69e51e1b249b9da68cbf6f6778a8ae10f9f33f7082a07e5073a1ba731fa1640d"
)


CONTRACT_REL = (
    "02_AI/Models/"
    "frozen_c04_remediation_research_protocol_contract.py"
)

G7C_CONTRACT_REL = (
    "02_AI/Models/"
    "frozen_c04_remediation_training_snapshot_authority.py"
)

G7C_EVIDENCE_REL = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g7_c_training_snapshot_authority_freeze_evidence.json"
)

HISTORICAL_REGISTRY_REL = (
    "xauusd_portable_331_train_model_candidate_registry_design.json"
)

HISTORICAL_RESEARCH_PROTOCOL_REL = (
    "04_Testing/evidence/research/portable_331/train/"
    "xauusd_portable_331_train_model_research_protocol_design.json"
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

RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_d_remediation_research_protocol_freeze.py"
)

TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g7_d_remediation_research_protocol_freeze.py"
)

EVIDENCE_REL = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g7_d_remediation_research_protocol_freeze_evidence.json"
)

EVIDENCE_PATH = (
    REPO_ROOT
    / EVIDENCE_REL
)


ALLOWED_LOCAL_PATHS = {
    CONTRACT_REL,
    RUNNER_REL,
    TEST_REL,
    EVIDENCE_REL,
}


HASH_BOUND_DEPENDENCIES = (
    CONTRACT_REL,
    G7C_CONTRACT_REL,
    G7C_EVIDENCE_REL,
    HISTORICAL_REGISTRY_REL,
    HISTORICAL_RESEARCH_PROTOCOL_REL,
    RUNNER_REL,
    TEST_REL,
)


_contract: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_remediation_research_protocol_contract"
)

_g7c: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_remediation_training_snapshot_authority"
)


class G7DFreezeError(RuntimeError):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise G7DFreezeError(
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
        raise G7DFreezeError(
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
        raise G7DFreezeError(
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

    with path.open("rb") as handle:

        while True:

            block = handle.read(
                1024 * 1024
            )

            if not block:
                break

            digest.update(
                block
            )

    return digest.hexdigest()


def canonical_text_sha256(
    path: Path,
) -> str:

    require(
        path.is_file(),
        f"FILE_MISSING:{path}",
    )

    data = (
        path.read_bytes()
        .replace(b"\r\n", b"\n")
        .replace(b"\r", b"\n")
    )

    return hashlib.sha256(
        data
    ).hexdigest()


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
        raise G7DFreezeError(
            f"JSON_ROOT_NOT_OBJECT:{path}"
        )

    return value


def canonical_mapping_sha256(
    value: Mapping[str, Any],
) -> str:

    payload = json.dumps(
        dict(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")

    return hashlib.sha256(
        payload
    ).hexdigest()


def write_json(
    path: Path,
    value: Mapping[str, Any],
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp = path.with_suffix(
        path.suffix + ".tmp"
    )

    temp.write_text(
        json.dumps(
            dict(value),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )

    temp.replace(
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
            )[1]

        if (
            value.startswith('"')
            and value.endswith('"')
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


def verify_g7c_authority() -> dict[str, Any]:

    evidence = load_json(
        REPO_ROOT
        / G7C_EVIDENCE_REL
    )

    require(
        evidence.get("status")
        ==
        "PASS",
        "G7C_STATUS_NOT_PASS",
    )

    contract_block = require_mapping(
        evidence.get(
            "snapshot_contract"
        ),
        "G7C_CONTRACT_BLOCK_MISSING",
    )

    require(
        contract_block.get(
            "contract_fingerprint_sha256"
        )
        ==
        EXPECTED_G7C_FINGERPRINT,
        "G7C_EVIDENCE_FINGERPRINT_MISMATCH",
    )

    require(
        _g7c.contract_fingerprint_sha256()
        ==
        EXPECTED_G7C_FINGERPRINT,
        "CURRENT_G7C_FINGERPRINT_MISMATCH",
    )

    snapshot = require_mapping(
        evidence.get(
            "authorized_training_snapshot"
        ),
        "G7C_SNAPSHOT_BLOCK_MISSING",
    )

    require(
        snapshot.get("dataset_id")
        ==
        _contract.DATASET_ID,
        "G7C_DATASET_ID_MISMATCH",
    )

    require(
        snapshot.get("dataset_sha256")
        ==
        _contract.DATASET_SHA256,
        "G7C_DATASET_SHA256_MISMATCH",
    )

    require(
        snapshot.get("manifest_sha256")
        ==
        _contract.MANIFEST_SHA256,
        "G7C_MANIFEST_SHA256_MISMATCH",
    )

    require(
        snapshot.get(
            "feature_columns_sha256"
        )
        ==
        _contract.FEATURE_COLUMNS_SHA256,
        "G7C_FEATURE_SHA256_MISMATCH",
    )

    return {
        "status": "PASS",
        "g7c_contract_fingerprint_sha256": (
            EXPECTED_G7C_FINGERPRINT
        ),
        "dataset_id": _contract.DATASET_ID,
    }


def verify_historical_registry() -> dict[str, Any]:

    document = load_json(
        REPO_ROOT
        / HISTORICAL_REGISTRY_REL
    )

    contract_block = require_mapping(
        document.get(
            "contract"
        ),
        "HISTORICAL_REGISTRY_CONTRACT_MISSING",
    )

    registry_fingerprint = require_mapping(
        document.get(
            "registry_fingerprint"
        ),
        "HISTORICAL_REGISTRY_FINGERPRINT_BLOCK_MISSING",
    )

    decision = require_mapping(
        document.get(
            "decision"
        ),
        "HISTORICAL_REGISTRY_DECISION_MISSING",
    )

    candidates = require_list(
        contract_block.get(
            "candidates"
        ),
        "HISTORICAL_REGISTRY_CANDIDATES_MISSING",
    )

    candidate_ids: list[str] = []

    for raw_candidate in candidates:

        candidate = require_mapping(
            raw_candidate,
            "INVALID_HISTORICAL_CANDIDATE",
        )

        candidate_id = str(
            candidate.get(
                "candidate_id",
                "",
            )
        ).strip()

        require(
            bool(candidate_id),
            "HISTORICAL_CANDIDATE_ID_MISSING",
        )

        candidate_ids.append(
            candidate_id
        )

    require(
        tuple(candidate_ids)
        ==
        _contract.HISTORICAL_CANDIDATE_IDS,
        (
            "HISTORICAL_CANDIDATE_IDS_MISMATCH:"
            f"{candidate_ids}"
        ),
    )

    require(
        registry_fingerprint.get(
            "sha256"
        )
        ==
        EXPECTED_HISTORICAL_REGISTRY_FINGERPRINT,
        "HISTORICAL_REGISTRY_FINGERPRINT_MISMATCH",
    )

    require(
        decision.get(
            "candidate_registry_fingerprint_sha256"
        )
        ==
        EXPECTED_HISTORICAL_REGISTRY_FINGERPRINT,
        "HISTORICAL_REGISTRY_DECISION_FINGERPRINT_MISMATCH",
    )

    require(
        int(
            decision.get(
                "candidate_count",
                -1,
            )
        )
        ==
        6,
        "HISTORICAL_REGISTRY_CANDIDATE_COUNT_MISMATCH",
    )

    require(
        contract_block.get(
            "contract_status"
        )
        ==
        "DESIGN_ONLY_NO_MODEL_FIT",
        "HISTORICAL_REGISTRY_DESIGN_STATUS_MISMATCH",
    )

    return {
        "status": "PASS",
        "registry_version": (
            _contract.HISTORICAL_CANDIDATE_REGISTRY_VERSION
        ),
        "registry_fingerprint_sha256": (
            EXPECTED_HISTORICAL_REGISTRY_FINGERPRINT
        ),
        "candidate_count": len(
            candidate_ids
        ),
        "candidate_ids": candidate_ids,
    }


def verify_historical_research_protocol() -> dict[str, Any]:

    document = load_json(
        REPO_ROOT
        / HISTORICAL_RESEARCH_PROTOCOL_REL
    )

    fingerprint_block = require_mapping(
        document.get(
            "contract_fingerprint"
        ),
        "HISTORICAL_RESEARCH_PROTOCOL_FINGERPRINT_MISSING",
    )

    decision = require_mapping(
        document.get(
            "decision"
        ),
        "HISTORICAL_RESEARCH_PROTOCOL_DECISION_MISSING",
    )

    require(
        fingerprint_block.get(
            "sha256"
        )
        ==
        EXPECTED_HISTORICAL_RESEARCH_PROTOCOL_FINGERPRINT,
        "HISTORICAL_RESEARCH_PROTOCOL_FINGERPRINT_MISMATCH",
    )

    require(
        decision.get(
            "research_protocol_fingerprint_sha256"
        )
        ==
        EXPECTED_HISTORICAL_RESEARCH_PROTOCOL_FINGERPRINT,
        "HISTORICAL_PROTOCOL_DECISION_FINGERPRINT_MISMATCH",
    )

    require(
        int(
            decision.get(
                "feature_count",
                -1,
            )
        )
        ==
        _contract.FEATURE_COUNT,
        "HISTORICAL_PROTOCOL_FEATURE_COUNT_MISMATCH",
    )

    return {
        "status": "PASS",
        "research_protocol_fingerprint_sha256": (
            EXPECTED_HISTORICAL_RESEARCH_PROTOCOL_FINGERPRINT
        ),
    }


def verify_contract() -> dict[str, Any]:

    require(
        _contract.BASE_AUTHORITY_COMMIT
        ==
        BASE_AUTHORITY_COMMIT,
        "CONTRACT_BASE_AUTHORITY_MISMATCH",
    )

    require(
        _contract.G7C_CONTRACT_FINGERPRINT_SHA256
        ==
        EXPECTED_G7C_FINGERPRINT,
        "CONTRACT_G7C_LINKAGE_MISMATCH",
    )

    require(
        _contract.NEW_REMEDIATION_REGISTRY_REQUIRED
        is True,
        "NEW_REGISTRY_NOT_REQUIRED",
    )

    require(
        _contract.NEW_REMEDIATION_REGISTRY_GATE
        ==
        "G7-E",
        "UNEXPECTED_NEW_REGISTRY_GATE",
    )

    require(
        _contract.NEW_REMEDIATION_REGISTRY_MUST_BE_FINITE
        is True,
        "NEW_REGISTRY_NOT_FINITE",
    )

    require(
        _contract.NEW_REMEDIATION_REGISTRY_MUST_BE_FROZEN_BEFORE_FIRST_FIT
        is True,
        "REGISTRY_FREEZE_BEFORE_FIT_NOT_REQUIRED",
    )

    require(
        _contract.NEW_REMEDIATION_REGISTRY_MIN_CANDIDATES
        >=
        1,
        "INVALID_MINIMUM_CANDIDATE_COUNT",
    )

    require(
        _contract.NEW_REMEDIATION_REGISTRY_MAX_CANDIDATES
        >=
        _contract.NEW_REMEDIATION_REGISTRY_MIN_CANDIDATES,
        "INVALID_MAXIMUM_CANDIDATE_COUNT",
    )

    require(
        _contract.NEW_REMEDIATION_REGISTRY_MUST_INCLUDE_C04_CONTROL
        is True,
        "C04_CONTROL_NOT_REQUIRED",
    )

    require(
        _contract.HISTORICAL_REGISTRY_AUTOMATICALLY_REUSED_AS_REMEDIATION_REGISTRY
        is False,
        "OLD_REGISTRY_AUTOMATIC_REUSE_ALLOWED",
    )

    require(
        _contract.FORWARD_30_MAY_BE_USED_FOR_TRAINING
        is False,
        "FORWARD_30_TRAINING_ALLOWED",
    )

    require(
        _contract.FORWARD_30_MAY_BE_USED_FOR_MODEL_SELECTION
        is False,
        "FORWARD_30_MODEL_SELECTION_ALLOWED",
    )

    require(
        _contract.TEST_MAY_BE_USED_FOR_REMEDIATION_RESEARCH
        is False,
        "TEST_RESEARCH_ACCESS_ALLOWED",
    )

    require(
        _contract.TEST_MAY_BE_USED_BEFORE_FINAL_CANDIDATE_FREEZE
        is False,
        "PREMATURE_TEST_ACCESS_ALLOWED",
    )

    require(
        _contract.UNBOUNDED_GRID_SEARCH_ALLOWED
        is False,
        "UNBOUNDED_GRID_SEARCH_ALLOWED",
    )

    require(
        _contract.BAYESIAN_OPTIMIZATION_ALLOWED
        is False,
        "BAYESIAN_OPTIMIZATION_ALLOWED",
    )

    require(
        _contract.AUTOML_SEARCH_ALLOWED
        is False,
        "AUTOML_SEARCH_ALLOWED",
    )

    require(
        _contract.NEW_PROSPECTIVE_FORWARD_VALIDATION_REQUIRED
        is True,
        "PROSPECTIVE_VALIDATION_NOT_REQUIRED",
    )

    require(
        _contract.FORWARD_EVALUATION_CADENCE
        ==
        "WEEKLY",
        "FORWARD_CADENCE_NOT_WEEKLY",
    )

    require(
        _contract.FORWARD_MINIMUM_NEW_WEEKLY_SAMPLE_COUNT
        ==
        0,
        "FIXED_WEEKLY_MINIMUM_PRESENT",
    )

    require(
        _contract.FIXED_COUNT_FORWARD_WAIT_REQUIRED
        is False,
        "FIXED_COUNT_FORWARD_WAIT_ENABLED",
    )

    current_gate_forbidden = (
        _contract.THIS_GATE_LOADS_TRAIN_FEATURE_VALUES,
        _contract.THIS_GATE_LOADS_TRAIN_TARGET_VALUES,
        _contract.THIS_GATE_LOADS_VALIDATION_FEATURE_VALUES,
        _contract.THIS_GATE_LOADS_VALIDATION_TARGET_VALUES,
        _contract.THIS_GATE_LOADS_TEST_FEATURE_VALUES,
        _contract.THIS_GATE_LOADS_TEST_TARGET_VALUES,
        _contract.THIS_GATE_TRAINS_MODEL,
        _contract.THIS_GATE_FITS_PREPROCESSOR,
        _contract.THIS_GATE_SELECTS_MODEL,
        _contract.THIS_GATE_SELECTS_FEATURES,
        _contract.THIS_GATE_TUNES_HYPERPARAMETERS,
        _contract.THIS_GATE_CALIBRATES_PROBABILITIES,
        _contract.THIS_GATE_TUNES_THRESHOLDS,
        _contract.THIS_GATE_WRITES_MODEL_ARTIFACTS,
        _contract.THIS_GATE_ACQUIRES_MARKET_DATA,
        _contract.THIS_GATE_WRITES_RUNTIME_LEDGERS,
        _contract.THIS_GATE_EVALUATES_PNL,
        _contract.LIVE_AUTHORIZED,
        _contract.EXECUTION_AUTHORIZED,
    )

    require(
        not any(
            current_gate_forbidden
        ),
        "G7D_FORBIDDEN_CURRENT_GATE_ACTION_ENABLED",
    )

    fingerprint = (
        _contract.contract_fingerprint_sha256()
    )

    require(
        fingerprint
        ==
        _contract.CONTRACT_FINGERPRINT_SHA256,
        "CONTRACT_FINGERPRINT_MISMATCH",
    )

    return {
        "status": "PASS",
        "contract_id": _contract.CONTRACT_ID,
        "contract_fingerprint_sha256": fingerprint,
        "next_gate": "G7-E",
    }


def runtime_hashes() -> dict[str, str]:

    return {
        "observation": sha256_file(
            REPO_ROOT
            / OBSERVATION_LEDGER_REL
        ),
        "anchor": sha256_file(
            REPO_ROOT
            / ANCHOR_LEDGER_REL
        ),
        "outcome": sha256_file(
            REPO_ROOT
            / OUTCOME_LEDGER_REL
        ),
    }


def dependency_hashes() -> dict[str, str]:

    return {
        relative: canonical_text_sha256(
            REPO_ROOT
            / relative
        )
        for relative
        in HASH_BOUND_DEPENDENCIES
    }


def run_gate() -> dict[str, Any]:

    before = runtime_hashes()

    repository = verify_repository()

    g7c = verify_g7c_authority()

    historical_registry = (
        verify_historical_registry()
    )

    historical_protocol = (
        verify_historical_research_protocol()
    )

    contract = verify_contract()

    after = runtime_hashes()

    require(
        before
        ==
        after,
        "RUNTIME_LEDGER_CHANGED_DURING_G7D_FREEZE",
    )

    evidence = {
        "gate_id": GATE_ID,
        "schema_version": SCHEMA_VERSION,
        "status": "PASS",
        "base_authority_commit": BASE_AUTHORITY_COMMIT,
        "repository_authority": repository,
        "g7c_authority": g7c,
        "historical_registry_lineage": (
            historical_registry
        ),
        "historical_research_protocol_lineage": (
            historical_protocol
        ),
        "remediation_research_contract": contract,
        "runtime_ledger_raw_sha256": after,
        "hash_bound_dependencies": (
            dependency_hashes()
        ),
        "historical_registry_reused_as_new_registry": False,
        "new_registry_required_next": True,
        "new_registry_gate": "G7-E",
        "train_feature_values_loaded": False,
        "train_target_values_loaded": False,
        "validation_feature_values_loaded": False,
        "validation_target_values_loaded": False,
        "test_feature_values_loaded": False,
        "test_target_values_loaded": False,
        "retraining_performed": False,
        "model_reselection_performed": False,
        "feature_reselection_performed": False,
        "hyperparameter_tuning_performed": False,
        "calibration_performed": False,
        "threshold_tuning_performed": False,
        "pnl_evaluated": False,
        "market_data_acquired": False,
        "runtime_ledger_write_performed": False,
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
            "GATE_15D_C_B2D_G7_D_FREEZE_STATUS=BLOCKED"
        )

        print(
            "ERROR_TYPE="
            + type(exc).__name__
        )

        print(
            "ERROR="
            + str(exc)
        )

        print("RETRAINING_PERFORMED=false")
        print("TEST_VALUES_LOADED=false")
        print("PNL_EVALUATED=false")
        print("LIVE_AUTHORIZED=false")
        print("EXECUTION_AUTHORIZED=false")

        return 2

    contract = require_mapping(
        evidence.get(
            "remediation_research_contract"
        ),
        "EVIDENCE_CONTRACT_BLOCK_MISSING",
    )

    registry = require_mapping(
        evidence.get(
            "historical_registry_lineage"
        ),
        "EVIDENCE_REGISTRY_BLOCK_MISSING",
    )

    print(
        "GATE_15D_C_B2D_G7_D_FREEZE_STATUS=PASS"
    )

    print(
        "BASE_AUTHORITY_COMMIT="
        + BASE_AUTHORITY_COMMIT
    )

    print(
        "CONTRACT_ID="
        + str(
            contract[
                "contract_id"
            ]
        )
    )

    print(
        "CONTRACT_FINGERPRINT_SHA256="
        + str(
            contract[
                "contract_fingerprint_sha256"
            ]
        )
    )

    print(
        "HISTORICAL_REGISTRY_FINGERPRINT_SHA256="
        + str(
            registry[
                "registry_fingerprint_sha256"
            ]
        )
    )

    print(
        "HISTORICAL_CANDIDATE_COUNT="
        + str(
            registry[
                "candidate_count"
            ]
        )
    )

    print(
        "NEW_REMEDIATION_REGISTRY_REQUIRED=true"
    )

    print(
        "NEW_REMEDIATION_REGISTRY_GATE=G7-E"
    )

    print(
        "HISTORICAL_REGISTRY_REUSED_AS_NEW_REGISTRY=false"
    )

    print(
        "TRAIN_FEATURE_VALUES_LOADED=false"
    )

    print(
        "VALIDATION_FEATURE_VALUES_LOADED=false"
    )

    print(
        "TEST_VALUES_LOADED=false"
    )

    print(
        "RETRAINING_PERFORMED=false"
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