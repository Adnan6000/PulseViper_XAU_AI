from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping


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


BASE_AUTHORITY_COMMIT = (
    "c45008d4f2e18a28b758d9563d8b1298077c1ca7"
)

GATE_ID = (
    "GATE_15D_C_B2D_G7_H_D_"
    "R03_OUTCOME_MATURATION_BINDING_FREEZE"
)

MODULE_REL = (
    "02_AI/Models/"
    "frozen_r03_prospective_outcome_maturer.py"
)

RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g7_h_d_"
    "r03_outcome_maturation_binding_freeze.py"
)

TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g7_h_d_"
    "r03_outcome_maturation_binding_freeze.py"
)

EVIDENCE_REL = (
    "04_Testing/evidence/research/"
    "portable_331/remediation/"
    "xauusd_gate_15d_c_b2d_g7_h_d_"
    "r03_outcome_maturation_binding_freeze.json"
)

EVIDENCE_PATH = (
    REPO_ROOT
    /
    EVIDENCE_REL
)


ALLOWED_LOCAL_PATHS = {
    MODULE_REL,
    RUNNER_REL,
    TEST_REL,
    EVIDENCE_REL,
}


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
    (
        "01_Data/Shadow/"
        "xauusd_r03_prospective_observations.jsonl"
    ),
    (
        "01_Data/Shadow/"
        "xauusd_r03_prospective_forward_outcome_anchors.jsonl"
    ),
    (
        "01_Data/Shadow/"
        "xauusd_r03_prospective_forward_outcomes.jsonl"
    ),
)


_maturer: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_r03_prospective_outcome_maturer"
)

_runtime: Any = importlib.import_module(
    "02_AI.Models."
    "frozen_r03_prospective_runtime"
)


class G7HDError(RuntimeError):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise G7HDError(
            reason
        )


def sha256_file(
    path: Path,
) -> str:

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


def protected_states() -> dict[
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


def verify_repository() -> None:

    git_output(
        "fetch",
        "origin",
    )

    require(
        git_output(
            "branch",
            "--show-current",
        )
        ==
        "main",
        "UNEXPECTED_BRANCH",
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
        head
        ==
        origin,
        "HEAD_ORIGIN_DIVERGENCE",
    )

    require(
        head
        ==
        BASE_AUTHORITY_COMMIT,
        "BASE_AUTHORITY_MISMATCH",
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

    before = protected_states()

    verify_repository()

    require(
        _maturer.verify_authorities()
        is True,
        "MATURATION_AUTHORITIES_INVALID",
    )

    require(
        _maturer.OUTCOME_LEDGER_RELATIVE_PATH
        ==
        _runtime.OUTCOME_LEDGER_RELATIVE_PATH,
        "R03_OUTCOME_LEDGER_PATH_MISMATCH",
    )

    require(
        _maturer.label_outcome(
            up_excursion_atr=1.25,
            down_excursion_atr=0.50,
        )
        ==
        (
            1,
            "LONG",
        ),
        "LONG_RULE_SMOKE_FAILED",
    )

    require(
        _maturer.label_outcome(
            up_excursion_atr=0.50,
            down_excursion_atr=1.25,
        )
        ==
        (
            -1,
            "SHORT",
        ),
        "SHORT_RULE_SMOKE_FAILED",
    )

    require(
        _maturer.label_outcome(
            up_excursion_atr=0.50,
            down_excursion_atr=0.50,
        )
        ==
        (
            0,
            "NO_TRADE",
        ),
        "NO_TRADE_RULE_SMOKE_FAILED",
    )

    after = protected_states()

    require(
        before
        ==
        after,
        "RUNTIME_LEDGER_CHANGED_DURING_FREEZE",
    )

    evidence = {
        "gate_id": GATE_ID,
        "status": "PASS",
        "base_authority_commit": (
            BASE_AUTHORITY_COMMIT
        ),
        "maturation_version": (
            _maturer.MATURATION_VERSION
        ),
        "outcome_schema_version": (
            _maturer.OUTCOME_SCHEMA_VERSION
        ),
        "artifact_sha256": (
            _maturer.EXPECTED_ARTIFACT_SHA256
        ),
        "outcome_contract_fingerprint_sha256": (
            _maturer.EXPECTED_CONTRACT_FINGERPRINT_SHA256
        ),
        "prospective_contract_fingerprint_sha256": (
            _maturer.EXPECTED_PROSPECTIVE_CONTRACT_FINGERPRINT_SHA256
        ),
        "horizon_bars": 12,
        "horizon_minutes": 60,
        "profit_atr": 1.25,
        "max_adverse_atr": 0.75,
        "entry_reference": (
            _maturer.ENTRY_REFERENCE
        ),
        "atr_reference": (
            _maturer.ATR_REFERENCE
        ),
        "outcome_ledger": (
            _maturer.OUTCOME_LEDGER_RELATIVE_PATH
        ),
        "real_market_data_loaded": False,
        "runtime_ledgers_written": False,
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
            "GATE_15D_C_B2D_G7_H_D_FREEZE_STATUS=BLOCKED"
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
            "REAL_MARKET_DATA_LOADED=false"
        )

        print(
            "RUNTIME_LEDGERS_WRITTEN=false"
        )

        print(
            "LIVE_AUTHORIZED=false"
        )

        print(
            "EXECUTION_AUTHORIZED=false"
        )

        return 2

    print(
        "GATE_15D_C_B2D_G7_H_D_FREEZE_STATUS=PASS"
    )

    print(
        "BASE_AUTHORITY_COMMIT="
        +
        BASE_AUTHORITY_COMMIT
    )

    print(
        "MATURATION_VERSION="
        +
        _maturer.MATURATION_VERSION
    )

    print(
        "HORIZON_BARS=12"
    )

    print(
        "HORIZON_MINUTES=60"
    )

    print(
        "PROFIT_ATR=1.25"
    )

    print(
        "MAX_ADVERSE_ATR=0.75"
    )

    print(
        "OUTCOME_LEDGER="
        +
        _maturer.OUTCOME_LEDGER_RELATIVE_PATH
    )

    print(
        "REAL_MARKET_DATA_LOADED=false"
    )

    print(
        "RUNTIME_LEDGERS_WRITTEN=false"
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