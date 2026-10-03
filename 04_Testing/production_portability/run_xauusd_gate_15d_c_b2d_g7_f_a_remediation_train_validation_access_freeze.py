from __future__ import annotations

import hashlib
import importlib
import inspect
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
    "GATE_15D_C_B2D_G7_F_A_REMEDIATION_TRAIN_VALIDATION_ACCESS_FREEZE"
)

BASE_AUTHORITY_COMMIT = (
    "b650eff40e191b154c3055caadd9159e0eb0812a"
)

EXPECTED_G7E_REGISTRY_FINGERPRINT = (
    "4556eb982086da0ea19ab910a30b5ab58788c7e5b7488ef8e3453e46289c0deb"
)

CONTRACT_REL = (
    "02_AI/Models/"
    "frozen_c04_remediation_train_validation_access_contract.py"
)

LOADER_REL = (
    "02_AI/Dataset/"
    "portable_331_remediation_train_validation_loader.py"
)

RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_f_a_remediation_train_validation_access_freeze.py"
)

TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g7_f_a_remediation_train_validation_access_freeze.py"
)

EVIDENCE_REL = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g7_f_a_remediation_train_validation_access_freeze_evidence.json"
)

EVIDENCE_PATH = REPO_ROOT / EVIDENCE_REL

OBSERVATION_LEDGER_REL = (
    "01_Data/Shadow/xauusd_frozen_c04_shadow_observations.jsonl"
)

ANCHOR_LEDGER_REL = (
    "01_Data/Shadow/xauusd_frozen_c04_forward_outcome_anchors.jsonl"
)

OUTCOME_LEDGER_REL = (
    "01_Data/Shadow/xauusd_frozen_c04_forward_outcomes.jsonl"
)

HISTORICAL_VALIDATION_LEDGER_REL = (
    "xauusd_portable_331_one_time_validation_access_ledger.json"
)

ALLOWED_LOCAL_PATHS = {
    CONTRACT_REL,
    LOADER_REL,
    RUNNER_REL,
    TEST_REL,
    EVIDENCE_REL,
}


_contract: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_remediation_train_validation_access_contract"
)

_registry: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_remediation_candidate_registry"
)

_loader_module: Any = importlib.import_module(
    "02_AI.Dataset.portable_331_remediation_train_validation_loader"
)


class G7FAFreezeError(RuntimeError):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise G7FAFreezeError(reason)


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

            digest.update(block)

    return digest.hexdigest()


def git_output(
    *args: str,
) -> str:

    result = subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
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

        value = line[3:].strip()

        if " -> " in value:
            value = value.split(
                " -> ",
                1,
            )[1]

        paths.add(
            value.replace(
                "\\",
                "/",
            )
        )

    return paths


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

    temp.replace(path)


def verify_repository() -> dict[str, Any]:

    git_output(
        "fetch",
        "origin",
    )

    head = git_output(
        "rev-parse",
        "HEAD",
    )

    origin = git_output(
        "rev-parse",
        "origin/main",
    )

    branch = git_output(
        "branch",
        "--show-current",
    )

    require(
        branch == "main",
        "NOT_ON_MAIN",
    )

    require(
        head == origin,
        "HEAD_ORIGIN_DIVERGENCE",
    )

    require(
        head == BASE_AUTHORITY_COMMIT,
        (
            "UNEXPECTED_BASE:"
            f"{head}"
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
        "head": head,
        "origin_main": origin,
    }


def verify_authorities() -> dict[str, Any]:

    require(
        _registry.REGISTRY_FINGERPRINT_SHA256
        ==
        EXPECTED_G7E_REGISTRY_FINGERPRINT,
        "G7E_REGISTRY_FINGERPRINT_MISMATCH",
    )

    require(
        _contract.G7E_REGISTRY_FINGERPRINT_SHA256
        ==
        EXPECTED_G7E_REGISTRY_FINGERPRINT,
        "ACCESS_CONTRACT_G7E_LINKAGE_MISMATCH",
    )

    require(
        _contract.TEST_FEATURE_ACCESS_AUTHORIZED
        is False,
        "TEST_FEATURE_ACCESS_ENABLED",
    )

    require(
        _contract.TEST_TARGET_ACCESS_AUTHORIZED
        is False,
        "TEST_TARGET_ACCESS_ENABLED",
    )

    require(
        _contract.VALIDATION_FEATURE_ACCESS_AUTHORIZED
        is True,
        "VALIDATION_FEATURE_ACCESS_NOT_AUTHORIZED",
    )

    require(
        _contract.VALIDATION_TARGET_ACCESS_AUTHORIZED
        is True,
        "VALIDATION_TARGET_ACCESS_NOT_AUTHORIZED",
    )

    return {
        "status": "PASS",
        "g7e_registry_fingerprint_sha256": (
            EXPECTED_G7E_REGISTRY_FINGERPRINT
        ),
        "access_contract_fingerprint_sha256": (
            _contract.CONTRACT_FINGERPRINT_SHA256
        ),
    }


def verify_loader_source() -> dict[str, Any]:

    cls = (
        _loader_module
        .Portable331RemediationTrainValidationLoader
    )

    source = inspect.getsource(cls)

    require(
        "load_validation_supervised" in source,
        "VALIDATION_SUPERVISED_METHOD_MISSING",
    )

    require(
        "TEST_FEATURE_ACCESS_NOT_AUTHORIZED_FOR_REMEDIATION"
        in source,
        "TEST_FEATURE_BLOCK_MISSING",
    )

    require(
        "TEST_TARGET_ACCESS_NOT_AUTHORIZED_FOR_REMEDIATION"
        in source,
        "TEST_TARGET_BLOCK_MISSING",
    )

    require(
        "nrows=self.EXPECTED_VALIDATION_ROWS"
        in source,
        "VALIDATION_READ_BOUND_MISSING",
    )

    require(
        "skiprows=skiprows"
        in source,
        "VALIDATION_START_BOUND_MISSING",
    )

    require(
        "model.fit(" not in source,
        "MODEL_FIT_FOUND_IN_LOADER",
    )

    return {
        "status": "PASS",
        "loader_version": cls.VERSION,
        "test_values_hard_blocked": True,
        "validation_read_bounded": True,
    }


def runtime_hashes() -> dict[str, str]:

    return {
        "observation": sha256_file(
            REPO_ROOT / OBSERVATION_LEDGER_REL
        ),
        "anchor": sha256_file(
            REPO_ROOT / ANCHOR_LEDGER_REL
        ),
        "outcome": sha256_file(
            REPO_ROOT / OUTCOME_LEDGER_REL
        ),
        "historical_validation_ledger": sha256_file(
            REPO_ROOT
            /
            HISTORICAL_VALIDATION_LEDGER_REL
        ),
    }


def run_gate() -> dict[str, Any]:

    before = runtime_hashes()

    repository = verify_repository()

    authorities = verify_authorities()

    loader = verify_loader_source()

    after = runtime_hashes()

    require(
        before == after,
        "PROTECTED_LEDGER_CHANGED_DURING_G7FA",
    )

    evidence = {
        "gate_id": GATE_ID,
        "status": "PASS",
        "base_authority_commit": BASE_AUTHORITY_COMMIT,
        "repository": repository,
        "authorities": authorities,
        "loader": loader,
        "protected_ledger_sha256": after,
        "train_values_loaded": False,
        "validation_values_loaded": False,
        "test_values_loaded": False,
        "model_training_performed": False,
        "candidate_evaluation_performed": False,
        "winner_selected": False,
        "historical_validation_ledger_modified": False,
        "pnl_evaluated": False,
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
            "GATE_15D_C_B2D_G7_F_A_FREEZE_STATUS=BLOCKED"
        )

        print(
            "ERROR_TYPE="
            + type(exc).__name__
        )

        print(
            "ERROR="
            + str(exc)
        )

        print("TRAIN_VALUES_LOADED=false")
        print("VALIDATION_VALUES_LOADED=false")
        print("TEST_VALUES_LOADED=false")
        print("MODEL_TRAINING_PERFORMED=false")
        print("LIVE_AUTHORIZED=false")
        print("EXECUTION_AUTHORIZED=false")

        return 2

    print(
        "GATE_15D_C_B2D_G7_F_A_FREEZE_STATUS=PASS"
    )

    print(
        "BASE_AUTHORITY_COMMIT="
        + BASE_AUTHORITY_COMMIT
    )

    print(
        "ACCESS_CONTRACT_FINGERPRINT_SHA256="
        + _contract.CONTRACT_FINGERPRINT_SHA256
    )

    print(
        "G7E_REGISTRY_FINGERPRINT_SHA256="
        + EXPECTED_G7E_REGISTRY_FINGERPRINT
    )

    print(
        "VALIDATION_ACCESS_AUTHORIZED_FOR_REMEDIATION=true"
    )

    print(
        "TEST_VALUES_HARD_BLOCKED=true"
    )

    print(
        "HISTORICAL_VALIDATION_LEDGER_MODIFIED=false"
    )

    print("TRAIN_VALUES_LOADED=false")
    print("VALIDATION_VALUES_LOADED=false")
    print("TEST_VALUES_LOADED=false")
    print("MODEL_TRAINING_PERFORMED=false")
    print("CANDIDATE_EVALUATION_PERFORMED=false")
    print("WINNER_SELECTED=false")
    print("LIVE_AUTHORIZED=false")
    print("EXECUTION_AUTHORIZED=false")

    _ = evidence

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )