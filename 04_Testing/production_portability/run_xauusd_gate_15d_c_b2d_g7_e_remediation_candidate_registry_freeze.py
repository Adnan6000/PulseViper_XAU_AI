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
    "GATE_15D_C_B2D_G7_E_REMEDIATION_CANDIDATE_REGISTRY_FREEZE"
)

SCHEMA_VERSION = "1.0.0"

REPOSITORY_BASE_COMMIT = (
    "63b2ea84a74c7a4a5e3ad355b6e0c2ec4e702893"
)

SCIENTIFIC_PARENT_AUTHORITY_COMMIT = (
    "86271e347939c18a45c03629efdfeab1035da75a"
)

EXPECTED_G7D_FINGERPRINT = (
    "c6270f03fed45ba749d40ea4c556b95e683ad934575c9dc958664bef83f86638"
)

EXPECTED_HISTORICAL_C04_CONFIG_FINGERPRINT = (
    "f1b11c6f91561f2eba1bd56195e2239e9598b1906c88f11ada67eac6cdeb09e3"
)


CONTRACT_REL = (
    "02_AI/Models/"
    "frozen_c04_remediation_candidate_registry.py"
)

G7D_CONTRACT_REL = (
    "02_AI/Models/"
    "frozen_c04_remediation_research_protocol_contract.py"
)

G7D_EVIDENCE_REL = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g7_d_remediation_research_protocol_freeze_evidence.json"
)

HISTORICAL_REGISTRY_REL = (
    "xauusd_portable_331_train_model_candidate_registry_design.json"
)

RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_e_remediation_candidate_registry_freeze.py"
)

TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g7_e_remediation_candidate_registry_freeze.py"
)

EVIDENCE_REL = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g7_e_remediation_candidate_registry_freeze_evidence.json"
)

EVIDENCE_PATH = (
    REPO_ROOT
    / EVIDENCE_REL
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


ALLOWED_BRIDGE_PATHS = {
    "README.md",
    "05_Documentation/Architecture.md",
    "05_Documentation/Development_Roadmap.md",
}


ALLOWED_LOCAL_PATHS = {
    CONTRACT_REL,
    RUNNER_REL,
    TEST_REL,
    EVIDENCE_REL,
}


HASH_BOUND_DEPENDENCIES = (
    CONTRACT_REL,
    G7D_CONTRACT_REL,
    G7D_EVIDENCE_REL,
    HISTORICAL_REGISTRY_REL,
    RUNNER_REL,
    TEST_REL,
)


_registry: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_remediation_candidate_registry"
)

_g7d: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_remediation_research_protocol_contract"
)


class G7EFreezeError(RuntimeError):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise G7EFreezeError(
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
        raise G7EFreezeError(
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
        raise G7EFreezeError(
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

    payload = (
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
        payload
    ).hexdigest()


def canonical_json_sha256(
    value: Any,
) -> str:

    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")

    return hashlib.sha256(
        payload
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
        raise G7EFreezeError(
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


def verify_repository_authority() -> dict[str, Any]:

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
        head
        ==
        REPOSITORY_BASE_COMMIT,
        (
            "UNEXPECTED_REPOSITORY_BASE:"
            f"{head}:expected="
            f"{REPOSITORY_BASE_COMMIT}"
        ),
    )

    ancestry = git_process(
        "merge-base",
        "--is-ancestor",
        SCIENTIFIC_PARENT_AUTHORITY_COMMIT,
        head,
    )

    require(
        ancestry.returncode == 0,
        "G7D_SCIENTIFIC_PARENT_NOT_ANCESTOR",
    )

    changed_since_parent = {
        line.strip().replace(
            "\\",
            "/",
        )
        for line in git_output(
            "diff",
            "--name-only",
            (
                SCIENTIFIC_PARENT_AUTHORITY_COMMIT
                + ".."
                + head
            ),
        ).splitlines()
        if line.strip()
    }

    require(
        changed_since_parent
        <=
        ALLOWED_BRIDGE_PATHS,
        (
            "NON_DOCUMENTATION_BRIDGE_CHANGE_DETECTED:"
            f"{sorted(changed_since_parent)}"
        ),
    )

    unexpected_local = (
        status_paths()
        -
        ALLOWED_LOCAL_PATHS
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
        "origin_main": origin,
        "scientific_parent_authority_commit": (
            SCIENTIFIC_PARENT_AUTHORITY_COMMIT
        ),
        "bridge_paths": sorted(
            changed_since_parent
        ),
        "bridge_docs_only": True,
    }


def verify_g7d_authority() -> dict[str, Any]:

    evidence = load_json(
        REPO_ROOT
        / G7D_EVIDENCE_REL
    )

    require(
        evidence.get(
            "status"
        )
        ==
        "PASS",
        "G7D_STATUS_NOT_PASS",
    )

    block = require_mapping(
        evidence.get(
            "remediation_research_contract"
        ),
        "G7D_CONTRACT_BLOCK_MISSING",
    )

    require(
        block.get(
            "contract_fingerprint_sha256"
        )
        ==
        EXPECTED_G7D_FINGERPRINT,
        "G7D_EVIDENCE_FINGERPRINT_MISMATCH",
    )

    require(
        _g7d.contract_fingerprint_sha256()
        ==
        EXPECTED_G7D_FINGERPRINT,
        "CURRENT_G7D_FINGERPRINT_MISMATCH",
    )

    require(
        _registry.G7D_CONTRACT_FINGERPRINT_SHA256
        ==
        EXPECTED_G7D_FINGERPRINT,
        "REGISTRY_G7D_LINKAGE_MISMATCH",
    )

    return {
        "status": "PASS",
        "contract_fingerprint_sha256": (
            EXPECTED_G7D_FINGERPRINT
        ),
    }


def verify_historical_c04_control() -> dict[str, Any]:

    document = load_json(
        REPO_ROOT
        / HISTORICAL_REGISTRY_REL
    )

    contract = require_mapping(
        document.get(
            "contract"
        ),
        "HISTORICAL_REGISTRY_CONTRACT_MISSING",
    )

    candidates = require_list(
        contract.get(
            "candidates"
        ),
        "HISTORICAL_CANDIDATES_MISSING",
    )

    historical_c04: Mapping[str, Any] | None = None

    for raw in candidates:

        candidate = require_mapping(
            raw,
            "INVALID_HISTORICAL_CANDIDATE",
        )

        if (
            candidate.get(
                "candidate_id"
            )
            ==
            _registry.HISTORICAL_C04_CANDIDATE_ID
        ):
            historical_c04 = candidate
            break

    require(
        historical_c04 is not None,
        "HISTORICAL_C04_NOT_FOUND",
    )

    if historical_c04 is None:
        raise G7EFreezeError(
            "HISTORICAL_C04_NOT_FOUND"
        )

    observed_fingerprint = (
        canonical_json_sha256(
            dict(
                historical_c04
            )
        )
    )

    require(
        observed_fingerprint
        ==
        EXPECTED_HISTORICAL_C04_CONFIG_FINGERPRINT,
        (
            "HISTORICAL_C04_CONFIG_FINGERPRINT_MISMATCH:"
            f"{observed_fingerprint}"
        ),
    )

    control = require_mapping(
        _registry.CANDIDATES[
            0
        ],
        "G7E_CONTROL_CANDIDATE_MISSING",
    )

    control_core = {
        "architecture": control.get(
            "architecture"
        ),
        "candidate_id": (
            _registry.HISTORICAL_C04_CANDIDATE_ID
        ),
        "estimator": control.get(
            "estimator"
        ),
        "family": control.get(
            "family"
        ),
        "preprocessing": control.get(
            "preprocessing"
        ),
        "probability_class_order": (
            control.get(
                "probability_class_order"
            )
        ),
    }

    historical_core = {
        "architecture": historical_c04.get(
            "architecture"
        ),
        "candidate_id": historical_c04.get(
            "candidate_id"
        ),
        "estimator": historical_c04.get(
            "estimator"
        ),
        "family": historical_c04.get(
            "family"
        ),
        "preprocessing": historical_c04.get(
            "preprocessing"
        ),
        "probability_class_order": (
            historical_c04.get(
                "probability_class_order"
            )
        ),
    }

    require(
        control_core
        ==
        historical_core,
        "G7E_C04_CONTROL_NOT_EXACT_HISTORICAL_CONFIG",
    )

    return {
        "status": "PASS",
        "historical_c04_config_fingerprint_sha256": (
            observed_fingerprint
        ),
        "control_exact_match": True,
    }


def verify_registry_structure() -> dict[str, Any]:

    candidates = list(
        _registry.CANDIDATES
    )

    require(
        len(candidates)
        ==
        _registry.CANDIDATE_COUNT,
        "REGISTRY_CANDIDATE_COUNT_MISMATCH",
    )

    require(
        (
            _registry.MIN_ALLOWED_CANDIDATES
            <=
            len(candidates)
            <=
            _registry.MAX_ALLOWED_CANDIDATES
        ),
        "REGISTRY_CANDIDATE_COUNT_OUT_OF_BOUNDS",
    )

    ids: list[str] = []

    for candidate in candidates:

        candidate_id = str(
            candidate.get(
                "candidate_id",
                "",
            )
        ).strip()

        require(
            bool(candidate_id),
            "EMPTY_CANDIDATE_ID",
        )

        ids.append(
            candidate_id
        )

        require(
            candidate.get(
                "feature_scope"
            )
            ==
            "EXACT_331_FROZEN_FEATURES",
            (
                "NON_FROZEN_FEATURE_SCOPE:"
                f"{candidate_id}"
            ),
        )

        require(
            candidate.get(
                "probability_class_order"
            )
            ==
            [-1, 0, 1],
            (
                "INVALID_CLASS_ORDER:"
                f"{candidate_id}"
            ),
        )

        calibration = require_mapping(
            candidate.get(
                "probability_calibration"
            ),
            (
                "CALIBRATION_BLOCK_MISSING:"
                f"{candidate_id}"
            ),
        )

        require(
            calibration.get(
                "enabled"
            )
            is False,
            (
                "CALIBRATION_ENABLED_IN_G7E:"
                f"{candidate_id}"
            ),
        )

        thresholds = require_mapping(
            candidate.get(
                "threshold_policy"
            ),
            (
                "THRESHOLD_BLOCK_MISSING:"
                f"{candidate_id}"
            ),
        )

        require(
            thresholds.get(
                "tuning_enabled"
            )
            is False,
            (
                "THRESHOLD_TUNING_ENABLED:"
                f"{candidate_id}"
            ),
        )

    require(
        len(set(ids))
        ==
        len(ids),
        "DUPLICATE_CANDIDATE_IDS",
    )

    require(
        ids[
            0
        ]
        ==
        "R00_CONTROL_C04_EXACT",
        "C04_CONTROL_NOT_FIRST",
    )

    remediation_candidates = [
        candidate
        for candidate
        in candidates
        if candidate.get(
            "role"
        )
        ==
        "REMEDIATION_CANDIDATE"
    ]

    require(
        len(
            remediation_candidates
        )
        ==
        len(candidates)
        - 1,
        "INVALID_REMEDIATION_ROLE_COUNTS",
    )

    for candidate in remediation_candidates:

        failure_modes = require_list(
            candidate.get(
                "addresses_failure_modes"
            ),
            (
                "FAILURE_MODE_LIST_MISSING:"
                + str(
                    candidate.get(
                        "candidate_id"
                    )
                )
            ),
        )

        require(
            bool(
                failure_modes
            ),
            (
                "REMEDIATION_HYPOTHESIS_HAS_NO_FAILURE_MODE:"
                + str(
                    candidate.get(
                        "candidate_id"
                    )
                )
            ),
        )

        for mode in failure_modes:

            require(
                mode
                in
                _registry.BROAD_FAILURE_MODES,
                (
                    "UNKNOWN_FAILURE_MODE:"
                    f"{mode}"
                ),
            )

    fingerprints = (
        _registry.candidate_fingerprints()
    )

    require(
        set(
            fingerprints.keys()
        )
        ==
        set(ids),
        "CANDIDATE_FINGERPRINT_SET_MISMATCH",
    )

    require(
        all(
            len(value) == 64
            for value
            in fingerprints.values()
        ),
        "INVALID_CANDIDATE_FINGERPRINT",
    )

    registry_fingerprint = (
        _registry.registry_fingerprint_sha256()
    )

    require(
        registry_fingerprint
        ==
        _registry.REGISTRY_FINGERPRINT_SHA256,
        "REGISTRY_FINGERPRINT_MISMATCH",
    )

    return {
        "status": "PASS",
        "candidate_count": len(
            candidates
        ),
        "candidate_ids": ids,
        "candidate_fingerprints": (
            fingerprints
        ),
        "registry_fingerprint_sha256": (
            registry_fingerprint
        ),
    }


def verify_scientific_policy() -> dict[str, Any]:

    require(
        _registry.REGISTRY_FINITE
        is True,
        "REGISTRY_NOT_FINITE",
    )

    require(
        _registry.REGISTRY_FROZEN_BEFORE_FIRST_FIT
        is True,
        "REGISTRY_NOT_FROZEN_BEFORE_FIRST_FIT",
    )

    require(
        _registry.REGISTRY_CHANGE_AFTER_FIRST_FIT_ALLOWED
        is False,
        "POST_FIT_REGISTRY_CHANGE_ALLOWED",
    )

    require(
        _registry.RESULTS_DRIVEN_CANDIDATE_ADDITION_ALLOWED
        is False,
        "RESULTS_DRIVEN_CANDIDATE_ADDITION_ALLOWED",
    )

    require(
        _registry.RESULTS_DRIVEN_HYPERPARAMETER_CHANGE_ALLOWED
        is False,
        "RESULTS_DRIVEN_HYPERPARAMETER_CHANGE_ALLOWED",
    )

    require(
        _registry.UNBOUNDED_GRID_SEARCH_ALLOWED
        is False,
        "UNBOUNDED_GRID_SEARCH_ALLOWED",
    )

    require(
        _registry.BAYESIAN_OPTIMIZATION_ALLOWED
        is False,
        "BAYESIAN_OPTIMIZATION_ALLOWED",
    )

    require(
        _registry.AUTOML_ALLOWED
        is False,
        "AUTOML_ALLOWED",
    )

    require(
        _registry.UNBOUNDED_RANDOM_SEARCH_ALLOWED
        is False,
        "UNBOUNDED_RANDOM_SEARCH_ALLOWED",
    )

    require(
        _registry.FEATURE_SUBSET_SEARCH_ALLOWED
        is False,
        "FEATURE_SUBSET_SEARCH_ALLOWED",
    )

    require(
        _registry.FORWARD_30_DEVELOPMENT_USE_ALLOWED
        is False,
        "FORWARD_30_DEVELOPMENT_USE_ALLOWED",
    )

    require(
        _registry.TEST_ACCESS_ALLOWED_DURING_REMEDIATION_SELECTION
        is False,
        "TEST_ACCESS_DURING_SELECTION_ALLOWED",
    )

    forbidden = (
        _registry.THIS_GATE_LOADS_TRAIN_VALUES,
        _registry.THIS_GATE_LOADS_VALIDATION_VALUES,
        _registry.THIS_GATE_LOADS_TEST_VALUES,
        _registry.THIS_GATE_TRAINS_MODELS,
        _registry.THIS_GATE_FITS_PREPROCESSORS,
        _registry.THIS_GATE_EVALUATES_CANDIDATES,
        _registry.THIS_GATE_SELECTS_WINNER,
        _registry.THIS_GATE_CALIBRATES_PROBABILITIES,
        _registry.THIS_GATE_TUNES_THRESHOLDS,
        _registry.THIS_GATE_EVALUATES_PNL,
        _registry.THIS_GATE_ACQUIRES_MARKET_DATA,
        _registry.THIS_GATE_WRITES_RUNTIME_LEDGERS,
        _registry.LIVE_AUTHORIZED,
        _registry.EXECUTION_AUTHORIZED,
    )

    require(
        not any(
            forbidden
        ),
        "G7E_FORBIDDEN_ACTION_ENABLED",
    )

    return {
        "status": "PASS",
        "registry_frozen_before_fit": True,
        "test_sealed": True,
        "forward_30_development_use": False,
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

    repository = (
        verify_repository_authority()
    )

    g7d = (
        verify_g7d_authority()
    )

    historical_control = (
        verify_historical_c04_control()
    )

    registry = (
        verify_registry_structure()
    )

    scientific_policy = (
        verify_scientific_policy()
    )

    after = runtime_hashes()

    require(
        before
        ==
        after,
        "RUNTIME_LEDGER_CHANGED_DURING_G7E_FREEZE",
    )

    evidence = {
        "gate_id": GATE_ID,
        "schema_version": SCHEMA_VERSION,
        "status": "PASS",
        "repository_base_commit": (
            REPOSITORY_BASE_COMMIT
        ),
        "scientific_parent_authority_commit": (
            SCIENTIFIC_PARENT_AUTHORITY_COMMIT
        ),
        "repository_authority": repository,
        "g7d_authority": g7d,
        "historical_c04_control": (
            historical_control
        ),
        "remediation_candidate_registry": (
            registry
        ),
        "scientific_policy": (
            scientific_policy
        ),
        "runtime_ledger_raw_sha256": after,
        "hash_bound_dependencies": (
            dependency_hashes()
        ),
        "train_values_loaded": False,
        "validation_values_loaded": False,
        "test_values_loaded": False,
        "model_training_performed": False,
        "candidate_evaluation_performed": False,
        "winner_selected": False,
        "probability_calibration_performed": False,
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
            "GATE_15D_C_B2D_G7_E_FREEZE_STATUS=BLOCKED"
        )

        print(
            "ERROR_TYPE="
            + type(
                exc
            ).__name__
        )

        print(
            "ERROR="
            + str(
                exc
            )
        )

        print(
            "MODEL_TRAINING_PERFORMED=false"
        )

        print(
            "CANDIDATE_EVALUATION_PERFORMED=false"
        )

        print(
            "TEST_VALUES_LOADED=false"
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

    registry = require_mapping(
        evidence.get(
            "remediation_candidate_registry"
        ),
        "EVIDENCE_REGISTRY_BLOCK_MISSING",
    )

    print(
        "GATE_15D_C_B2D_G7_E_FREEZE_STATUS=PASS"
    )

    print(
        "REPOSITORY_BASE_COMMIT="
        + REPOSITORY_BASE_COMMIT
    )

    print(
        "SCIENTIFIC_PARENT_AUTHORITY_COMMIT="
        + SCIENTIFIC_PARENT_AUTHORITY_COMMIT
    )

    print(
        "G7D_CONTRACT_FINGERPRINT_SHA256="
        + EXPECTED_G7D_FINGERPRINT
    )

    print(
        "REGISTRY_VERSION="
        + _registry.REGISTRY_VERSION
    )

    print(
        "REGISTRY_FINGERPRINT_SHA256="
        + str(
            registry[
                "registry_fingerprint_sha256"
            ]
        )
    )

    print(
        "CANDIDATE_COUNT="
        + str(
            registry[
                "candidate_count"
            ]
        )
    )

    print(
        "C04_CONTROL_EXACT=true"
    )

    print(
        "REGISTRY_FROZEN_BEFORE_FIRST_FIT=true"
    )

    print(
        "TRAIN_VALUES_LOADED=false"
    )

    print(
        "VALIDATION_VALUES_LOADED=false"
    )

    print(
        "TEST_VALUES_LOADED=false"
    )

    print(
        "MODEL_TRAINING_PERFORMED=false"
    )

    print(
        "CANDIDATE_EVALUATION_PERFORMED=false"
    )

    print(
        "WINNER_SELECTED=false"
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