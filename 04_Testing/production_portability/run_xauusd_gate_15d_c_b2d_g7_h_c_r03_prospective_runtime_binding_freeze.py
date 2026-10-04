from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

import numpy as np


REPO_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

if str(
    REPO_ROOT
) not in sys.path:

    sys.path.insert(
        0,
        str(
            REPO_ROOT
        ),
    )


GATE_ID = (
    "GATE_15D_C_B2D_G7_H_C_"
    "R03_PROSPECTIVE_RUNTIME_BINDING_FREEZE"
)

BASE_AUTHORITY_COMMIT = (
    "22f1ca6d0da30131ec5c9f0ce44ac46d03b82da4"
)

EXPECTED_ARTIFACT_SHA256 = (
    "b5da550921ef227b847207cfbfe5774e86f083f1d3354069a9624a5029ea2a03"
)

EXPECTED_MANIFEST_SHA256 = (
    "a1507666518e3289b0678525c0808fc91b45d54105ef1fb59f3c22fe5d52baf6"
)

EXPECTED_PROSPECTIVE_CONTRACT_FINGERPRINT = (
    "e70d8e26c8f4734c456022689d47de406fe3f8daf1827d01b7f0f0d7fe752b9e"
)


RUNTIME_REL = (
    "02_AI/Models/"
    "frozen_r03_prospective_runtime.py"
)

RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_h_c_"
    "r03_prospective_runtime_binding_freeze.py"
)

TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g7_h_c_"
    "r03_prospective_runtime_binding_freeze.py"
)

EVIDENCE_REL = (
    "04_Testing/evidence/research/"
    "portable_331/remediation/"
    "xauusd_gate_15d_c_b2d_g7_h_c_"
    "r03_prospective_runtime_binding_freeze.json"
)

EVIDENCE_PATH = (
    REPO_ROOT
    /
    EVIDENCE_REL
)


PROTECTED_RUNTIME_PATHS = (
    (
        "01_Data/Shadow/"
        "xauusd_frozen_c04_shadow_observations.jsonl"
    ),
    (
        "01_Data/Shadow/"
        "xauusd_frozen_c04_forward_outcome_anchors.jsonl"
    ),
    (
        "01_Data/Shadow/"
        "xauusd_frozen_c04_forward_outcomes.jsonl"
    ),
)


ALLOWED_LOCAL_PATHS = {
    RUNTIME_REL,
    RUNNER_REL,
    TEST_REL,
    EVIDENCE_REL,
}


_runtime: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_r03_prospective_runtime"
)

_contract: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_r03_prospective_forward_validation_contract"
)


class G7HCError(RuntimeError):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:

        raise G7HCError(
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

            block = handle.read(
                1024 * 1024
            )

            if not block:
                break

            digest.update(
                block
            )

    return digest.hexdigest()


def optional_hash(
    path: Path,
) -> str | None:

    if not path.exists():

        return None

    return sha256_file(
        path
    )


def protected_hashes() -> dict[
    str,
    str | None,
]:

    return {
        relative: optional_hash(
            REPO_ROOT
            /
            relative
        )
        for relative
        in PROTECTED_RUNTIME_PATHS
    }


def git_output(
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

    require(
        result.returncode
        ==
        0,
        (
            "GIT_COMMAND_FAILED:"
            +
            " ".join(
                args
            )
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

        if len(
            line
        ) < 4:

            continue

        value = line[
            3:
        ].strip()

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


def verify_repository() -> dict[str, Any]:

    git_output(
        "fetch",
        "origin",
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
        branch
        ==
        "main",
        "UNEXPECTED_BRANCH",
    )

    require(
        head
        ==
        origin,
        "HEAD_ORIGIN_MAIN_DIVERGENCE",
    )

    require(
        head
        ==
        BASE_AUTHORITY_COMMIT,
        (
            "UNEXPECTED_BASE_AUTHORITY:"
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
        "branch": branch,
        "head": head,
        "origin_main": origin,
    }


def verify_authorities() -> dict[str, Any]:

    require(
        _runtime.ARTIFACT_SHA256
        ==
        EXPECTED_ARTIFACT_SHA256,
        "RUNTIME_ARTIFACT_HASH_CONSTANT_MISMATCH",
    )

    require(
        _runtime.MANIFEST_SHA256
        ==
        EXPECTED_MANIFEST_SHA256,
        "RUNTIME_MANIFEST_HASH_CONSTANT_MISMATCH",
    )

    require(
        _runtime.PROSPECTIVE_CONTRACT_FINGERPRINT_SHA256
        ==
        EXPECTED_PROSPECTIVE_CONTRACT_FINGERPRINT,
        "RUNTIME_PROSPECTIVE_CONTRACT_MISMATCH",
    )

    require(
        _contract.CONTRACT_FINGERPRINT_SHA256
        ==
        EXPECTED_PROSPECTIVE_CONTRACT_FINGERPRINT,
        "PUBLISHED_PROSPECTIVE_CONTRACT_MISMATCH",
    )

    actual_artifact = sha256_file(
        REPO_ROOT
        /
        _runtime.ARTIFACT_RELATIVE_PATH
    )

    actual_manifest = sha256_file(
        REPO_ROOT
        /
        _runtime.MANIFEST_RELATIVE_PATH
    )

    require(
        actual_artifact
        ==
        EXPECTED_ARTIFACT_SHA256,
        "PUBLISHED_ARTIFACT_HASH_MISMATCH",
    )

    require(
        actual_manifest
        ==
        EXPECTED_MANIFEST_SHA256,
        "PUBLISHED_MANIFEST_HASH_MISMATCH",
    )

    require(
        _runtime.OBSERVATION_LEDGER_RELATIVE_PATH
        ==
        _contract.OBSERVATION_LEDGER_RELATIVE_PATH,
        "OBSERVATION_LEDGER_PATH_MISMATCH",
    )

    require(
        _runtime.ANCHOR_LEDGER_RELATIVE_PATH
        ==
        _contract.ANCHOR_LEDGER_RELATIVE_PATH,
        "ANCHOR_LEDGER_PATH_MISMATCH",
    )

    require(
        _runtime.OUTCOME_LEDGER_RELATIVE_PATH
        ==
        _contract.OUTCOME_LEDGER_RELATIVE_PATH,
        "OUTCOME_LEDGER_PATH_MISMATCH",
    )

    return {
        "status": "PASS",
        "artifact_sha256": (
            actual_artifact
        ),
        "manifest_sha256": (
            actual_manifest
        ),
        "prospective_contract_fingerprint_sha256": (
            _contract.CONTRACT_FINGERPRINT_SHA256
        ),
    }


def verify_inference_binding() -> dict[str, Any]:

    adapter = (
        _runtime
        .R03FrozenArtifactInferenceAdapter()
    )

    feature_columns = (
        adapter.feature_columns
    )

    require(
        len(
            feature_columns
        )
        ==
        331,
        "ARTIFACT_FEATURE_COUNT_MISMATCH",
    )

    matrix = np.zeros(
        (
            331,
        ),
        dtype=np.float64,
    )

    result = adapter.infer_single(
        matrix
    )

    probabilities = (
        result.probability_short,
        result.probability_no_trade,
        result.probability_long,
    )

    require(
        all(
            np.isfinite(
                value
            )
            for value
            in probabilities
        ),
        "SMOKE_PROBABILITY_NON_FINITE",
    )

    require(
        bool(
            np.isclose(
                sum(
                    probabilities
                ),
                1.0,
                rtol=1e-9,
                atol=1e-9,
            )
        ),
        "SMOKE_PROBABILITY_SUM_MISMATCH",
    )

    require(
        result.predicted_class
        in
        {
            -1,
            0,
            1,
        },
        "SMOKE_PREDICTED_CLASS_INVALID",
    )

    return {
        "status": "PASS",
        "feature_count": 331,
        "predicted_class": (
            result.predicted_class
        ),
        "probability_sum": float(
            sum(
                probabilities
            )
        ),
    }


def verify_gate_boundaries() -> dict[str, Any]:

    require(
        _runtime.LIVE_AUTHORIZED
        is False,
        "LIVE_AUTHORIZED",
    )

    require(
        _runtime.EXECUTION_AUTHORIZED
        is False,
        "EXECUTION_AUTHORIZED",
    )

    require(
        _runtime.PERFORMANCE_EVALUATION_AUTHORIZED
        is False,
        "PERFORMANCE_EVALUATION_AUTHORIZED",
    )

    require(
        _runtime.PNL_EVALUATION_AUTHORIZED
        is False,
        "PNL_EVALUATION_AUTHORIZED",
    )

    for relative in (
        _runtime.OBSERVATION_LEDGER_RELATIVE_PATH,
        _runtime.ANCHOR_LEDGER_RELATIVE_PATH,
        _runtime.OUTCOME_LEDGER_RELATIVE_PATH,
    ):

        require(
            not (
                REPO_ROOT
                /
                relative
            ).exists(),
            (
                "G7HC_MUST_NOT_CREATE_RUNTIME_LEDGER:"
                f"{relative}"
            ),
        )

    return {
        "status": "PASS",
        "market_data_loaded": False,
        "prospective_ledgers_created": False,
        "prospective_ledgers_written": False,
        "performance_evaluated": False,
        "pnl_evaluated": False,
        "live_authorized": False,
        "execution_authorized": False,
    }


def write_evidence(
    document: Mapping[str, Any],
) -> None:

    require(
        not EVIDENCE_PATH.exists(),
        "EVIDENCE_ALREADY_EXISTS",
    )

    EVIDENCE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with EVIDENCE_PATH.open(
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


def run_gate() -> dict[str, Any]:

    protected_before = (
        protected_hashes()
    )

    repository = (
        verify_repository()
    )

    authorities = (
        verify_authorities()
    )

    inference_binding = (
        verify_inference_binding()
    )

    boundaries = (
        verify_gate_boundaries()
    )

    protected_after = (
        protected_hashes()
    )

    require(
        protected_before
        ==
        protected_after,
        "OLD_C04_RUNTIME_LEDGER_CHANGED",
    )

    evidence = {
        "gate_id": GATE_ID,
        "status": "PASS",
        "base_authority_commit": (
            BASE_AUTHORITY_COMMIT
        ),
        "repository": repository,
        "authorities": authorities,
        "inference_binding": (
            inference_binding
        ),
        "boundaries": boundaries,
        "old_c04_runtime_ledger_sha256": (
            protected_after
        ),
        "r03_runtime_version": (
            _runtime.RUNTIME_VERSION
        ),
        "observation_schema_version": (
            _runtime.OBSERVATION_SCHEMA_VERSION
        ),
        "anchor_schema_version": (
            _runtime.ANCHOR_SCHEMA_VERSION
        ),
        "persistence_order": (
            "ANCHOR_FIRST_THEN_OBSERVATION"
        ),
        "acquisition_authority_role": (
            "GENUINE_READ_ONLY_MT5_PROVENANCE_ONLY"
        ),
        "r03_model_authority_role": (
            "EXACT_FROZEN_ARTIFACT_SHA256"
        ),
        "market_data_loaded": False,
        "prospective_ledgers_created": False,
        "prospective_ledgers_written": False,
        "performance_evaluated": False,
        "pnl_evaluated": False,
        "live_authorized": False,
        "execution_authorized": False,
    }

    write_evidence(
        evidence
    )

    return evidence


def main() -> int:

    try:

        evidence = run_gate()

    except Exception as exc:

        print(
            "GATE_15D_C_B2D_G7_H_C_FREEZE_STATUS=BLOCKED"
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
            "MARKET_DATA_LOADED=false"
        )

        print(
            "PROSPECTIVE_LEDGERS_WRITTEN=false"
        )

        print(
            "LIVE_AUTHORIZED=false"
        )

        print(
            "EXECUTION_AUTHORIZED=false"
        )

        return 2

    print(
        "GATE_15D_C_B2D_G7_H_C_FREEZE_STATUS=PASS"
    )

    print(
        "BASE_AUTHORITY_COMMIT="
        +
        BASE_AUTHORITY_COMMIT
    )

    print(
        "R03_ARTIFACT_SHA256="
        +
        EXPECTED_ARTIFACT_SHA256
    )

    print(
        "R03_MANIFEST_SHA256="
        +
        EXPECTED_MANIFEST_SHA256
    )

    print(
        "R03_RUNTIME_VERSION="
        +
        _runtime.RUNTIME_VERSION
    )

    print(
        "OBSERVATION_LEDGER="
        +
        _runtime.OBSERVATION_LEDGER_RELATIVE_PATH
    )

    print(
        "ANCHOR_LEDGER="
        +
        _runtime.ANCHOR_LEDGER_RELATIVE_PATH
    )

    print(
        "OUTCOME_LEDGER_RESERVED="
        +
        _runtime.OUTCOME_LEDGER_RELATIVE_PATH
    )

    print(
        "PERSISTENCE_ORDER=ANCHOR_FIRST_THEN_OBSERVATION"
    )

    print(
        "MARKET_DATA_LOADED=false"
    )

    print(
        "PROSPECTIVE_LEDGERS_CREATED=false"
    )

    print(
        "PROSPECTIVE_LEDGERS_WRITTEN=false"
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

    _ = evidence

    return 0


if __name__ == "__main__":

    raise SystemExit(
        main()
    )