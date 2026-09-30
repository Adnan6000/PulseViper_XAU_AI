from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[2]

GATE_ID = "GATE_15D_C_B2D_G2_FREEZE"
SCHEMA_VERSION = "1.0.0"

BASE_AUTHORITY_COMMIT = (
    "a1b692acd6b71b8fa32e59cb78f2da313388977f"
)

RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g2_genuine_outcome_maturation.py"
)

TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g2_genuine_outcome_maturation.py"
)

FREEZE_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g2_freeze.py"
)

EVIDENCE_REL = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g2_freeze_evidence.json"
)

EVIDENCE_PATH = REPO_ROOT / EVIDENCE_REL

HASH_BOUND_DEPENDENCIES = (
    "02_AI/Adapters/mt5_read_only_forward_acquisition_adapter.py",
    "02_AI/Adapters/xauusd_broker_adapter.py",
    "02_AI/Models/frozen_c04_shadow_observer.py",
    "02_AI/Models/frozen_c04_forward_outcome_anchor.py",
    "02_AI/Models/frozen_c04_forward_outcome_contract.py",
    "02_AI/Models/frozen_c04_forward_outcome_eligibility.py",
    "02_AI/Models/frozen_c04_forward_outcome_maturer.py",
    "02_AI/Models/frozen_c04_forward_outcome_ledger.py",
    RUNNER_REL,
    TEST_REL,
    FREEZE_REL,
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

ALLOWED_LOCAL_PATHS = {
    RUNNER_REL,
    TEST_REL,
    FREEZE_REL,
    EVIDENCE_REL,
}


class G2FreezeError(RuntimeError):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise G2FreezeError(reason)


def git_process(
    *args: str,
) -> subprocess.CompletedProcess[str]:

    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def git_output(
    *args: str,
) -> str:

    result = git_process(*args)

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


def normalize_path(
    value: str,
) -> str:

    return value.strip().replace(
        "\\",
        "/",
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

        item = line[3:].strip()

        if " -> " in item:
            item = item.split(
                " -> ",
                1,
            )[1]

        if (
            item.startswith('"')
            and
            item.endswith('"')
        ):
            item = item[1:-1]

        paths.add(
            normalize_path(item)
        )

    return paths


def sha256_file(
    path: Path,
) -> str:

    digest = hashlib.sha256()

    with path.open("rb") as handle:

        while True:
            chunk = handle.read(
                1024 * 1024
            )

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest()


def optional_sha256(
    path: Path,
) -> str | None:

    if not path.is_file():
        return None

    return sha256_file(path)


def write_json(
    path: Path,
    document: Mapping[str, Any],
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
            dict(document),
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )

    temp.replace(path)


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

    origin_main = git_output(
        "rev-parse",
        "origin/main",
    )

    require(
        branch == "main",
        f"UNEXPECTED_BRANCH:{branch}",
    )

    require(
        head == origin_main,
        (
            "HEAD_ORIGIN_MAIN_DIVERGENCE:"
            f"{head}!={origin_main}"
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

    local = status_paths()

    unexpected = (
        local
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
        "origin_main": origin_main,
        "allowed_local_paths": sorted(local),
    }


def static_safety_audit() -> dict[str, Any]:

    runner_path = (
        REPO_ROOT / RUNNER_REL
    )

    source = runner_path.read_text(
        encoding="utf-8"
    )

    forbidden = (
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
    )

    present = [
        name
        for name in forbidden
        if name in source
    ]

    require(
        not present,
        (
            "FORBIDDEN_EXECUTION_CAPABILITY_PRESENT:"
            f"{present}"
        ),
    )

    require(
        "mt5.initialize()" in source,
        "MT5_INITIALIZE_NOT_EXPLICIT",
    )

    require(
        "mt5.shutdown()" in source,
        "MT5_SHUTDOWN_NOT_EXPLICIT",
    )

    require(
        "MT5ReadOnlyCapabilityFacade"
        in source,
        "READ_ONLY_FACADE_MISSING",
    )

    require(
        "mature_observation"
        in source,
        "MATURATION_CALL_MISSING",
    )

    require(
        "if append_outcome:"
        in source,
        "EXPLICIT_APPEND_GATE_MISSING",
    )

    require(
        "IDEMPOTENT_IGNORE"
        in source,
        "IDEMPOTENT_OUTCOME_POLICY_MISSING",
    )

    return {
        "status": "PASS",
        "raw_mt5_calls": [
            "initialize",
            "shutdown",
        ],
        "execution_capabilities_present": [],
        "read_only_capability_facade": True,
        "append_requires_explicit_flag": True,
        "performance_evaluation_authorized": False,
        "live_authorized": False,
        "execution_authorized": False,
    }


def run_validation() -> dict[str, Any]:

    compile_process = subprocess.run(
        [
            str(REPO_ROOT / ".venv/Scripts/python.exe"),
            "-m",
            "py_compile",
            str(REPO_ROOT / RUNNER_REL),
            str(REPO_ROOT / TEST_REL),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    require(
        compile_process.returncode == 0,
        (
            "PY_COMPILE_FAILED:"
            + compile_process.stderr[-2000:]
        ),
    )

    pyright_process = subprocess.run(
        [
            str(REPO_ROOT / ".venv/Scripts/python.exe"),
            "-m",
            "pyright",
            RUNNER_REL,
            TEST_REL,
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    require(
        pyright_process.returncode == 0,
        (
            "PYRIGHT_FAILED:"
            + pyright_process.stdout[-2500:]
            + pyright_process.stderr[-2500:]
        ),
    )

    pytest_process = subprocess.run(
        [
            str(REPO_ROOT / ".venv/Scripts/python.exe"),
            "-m",
            "pytest",
            TEST_REL,
            "-q",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    require(
        pytest_process.returncode == 0,
        (
            "PYTEST_FAILED:"
            + pytest_process.stdout[-2500:]
            + pytest_process.stderr[-2500:]
        ),
    )

    return {
        "status": "PASS",
        "py_compile": True,
        "pyright_stdout": (
            pyright_process.stdout.strip()
        ),
        "pytest_stdout": (
            pytest_process.stdout.strip()
        ),
    }


def dependency_hashes() -> dict[str, str]:

    result: dict[str, str] = {}

    for relative in HASH_BOUND_DEPENDENCIES:

        path = REPO_ROOT / relative

        require(
            path.is_file(),
            (
                "HASH_BOUND_FILE_MISSING:"
                f"{relative}"
            ),
        )

        result[relative] = (
            sha256_file(path)
        )

    return result


def run_gate() -> dict[str, Any]:

    observation_before = optional_sha256(
        REPO_ROOT
        / OBSERVATION_LEDGER_REL
    )

    anchor_before = optional_sha256(
        REPO_ROOT
        / ANCHOR_LEDGER_REL
    )

    outcome_before = optional_sha256(
        REPO_ROOT
        / OUTCOME_LEDGER_REL
    )

    repository = verify_repository()

    safety = static_safety_audit()

    validation = run_validation()

    hashes = dependency_hashes()

    observation_after = optional_sha256(
        REPO_ROOT
        / OBSERVATION_LEDGER_REL
    )

    anchor_after = optional_sha256(
        REPO_ROOT
        / ANCHOR_LEDGER_REL
    )

    outcome_after = optional_sha256(
        REPO_ROOT
        / OUTCOME_LEDGER_REL
    )

    require(
        observation_before
        ==
        observation_after,
        "OBSERVATION_LEDGER_CHANGED",
    )

    require(
        anchor_before
        ==
        anchor_after,
        "ANCHOR_LEDGER_CHANGED",
    )

    require(
        outcome_before
        ==
        outcome_after,
        "OUTCOME_LEDGER_CHANGED",
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
        "static_safety": safety,
        "validation": validation,
        "hash_bound_dependencies": (
            hashes
        ),
        "genuine_runner_executed": False,
        "mt5_initialized": False,
        "market_data_acquired": False,
        "observation_ledger_unchanged": True,
        "anchor_ledger_unchanged": True,
        "outcome_ledger_unchanged": True,
        "outcome_appended": False,
        "forward_performance_evaluated": False,
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
            "GATE_15D_C_B2D_G2_FREEZE_STATUS=BLOCKED"
        )
        print(
            "ERROR_TYPE="
            + type(exc).__name__
        )
        print(
            "ERROR="
            + str(exc)
        )
        print(
            "GENUINE_RUNNER_EXECUTED=false"
        )
        print(
            "LIVE_AUTHORIZED=false"
        )
        print(
            "EXECUTION_AUTHORIZED=false"
        )

        return 2

    print(
        "GATE_15D_C_B2D_G2_FREEZE_STATUS=PASS"
    )

    print(
        "BASE_AUTHORITY_COMMIT="
        + evidence[
            "base_authority_commit"
        ]
    )

    print(
        "HASH_BOUND_FILE_COUNT="
        + str(
            len(
                evidence[
                    "hash_bound_dependencies"
                ]
            )
        )
    )

    print(
        "GENUINE_RUNNER_EXECUTED=false"
    )
    print(
        "MT5_INITIALIZED=false"
    )
    print(
        "MARKET_DATA_ACQUIRED=false"
    )
    print(
        "OBSERVATION_LEDGER_UNCHANGED=true"
    )
    print(
        "ANCHOR_LEDGER_UNCHANGED=true"
    )
    print(
        "OUTCOME_LEDGER_UNCHANGED=true"
    )
    print(
        "OUTCOME_APPENDED=false"
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

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
