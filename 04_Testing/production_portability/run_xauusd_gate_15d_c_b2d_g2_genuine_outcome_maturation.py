from __future__ import annotations

import argparse
import hashlib
import importlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Mapping


REPO_ROOT: Path = Path(__file__).resolve().parents[2]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


GATE_ID: str = (
    "GATE_15D_C_B2D_G2_GENUINE_OUTCOME_MATURATION"
)

SCHEMA_VERSION: str = "1.0.0"

BASE_AUTHORITY_COMMIT: str = (
    "a1b692acd6b71b8fa32e59cb78f2da313388977f"
)

CANONICAL_INSTRUMENT: str = "XAUUSD"

RUNNER_REL_PATH: str = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g2_genuine_outcome_maturation.py"
)

TEST_REL_PATH: str = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g2_genuine_outcome_maturation.py"
)

PASS_EVIDENCE_REL_PATH: str = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g2_genuine_outcome_maturation_evidence.json"
)

BLOCKED_EVIDENCE_REL_PATH: str = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g2_genuine_outcome_maturation_blocked.json"
)

PASS_EVIDENCE_PATH = REPO_ROOT / PASS_EVIDENCE_REL_PATH
BLOCKED_EVIDENCE_PATH = REPO_ROOT / BLOCKED_EVIDENCE_REL_PATH

OBSERVATION_LEDGER_PATH = (
    REPO_ROOT
    / "01_Data/Shadow/"
      "xauusd_frozen_c04_shadow_observations.jsonl"
)

ANCHOR_LEDGER_PATH = (
    REPO_ROOT
    / "01_Data/Shadow/"
      "xauusd_frozen_c04_forward_outcome_anchors.jsonl"
)

OUTCOME_LEDGER_PATH = (
    REPO_ROOT
    / "01_Data/Shadow/"
      "xauusd_frozen_c04_forward_outcomes.jsonl"
)


_observer: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_shadow_observer"
)

_anchor: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_anchor"
)

_maturer: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_maturer"
)

_outcome_ledger: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_ledger"
)

_acq: Any = importlib.import_module(
    "02_AI.Adapters.mt5_read_only_forward_acquisition_adapter"
)

mt5: Any = importlib.import_module(
    "MetaTrader5"
)


ObservationLedger: Any = (
    _observer.FrozenC04ObservationLedger
)

AnchorLedger: Any = (
    _anchor.FrozenC04ForwardOutcomeAnchorLedger
)

OutcomeLedger: Any = (
    _outcome_ledger.FrozenC04ForwardOutcomeLedger
)

OutcomeDuplicateHandling: Any = (
    _outcome_ledger.OutcomeDuplicateHandling
)

MT5ReadOnlyCapabilityFacade: Any = (
    _acq.MT5ReadOnlyCapabilityFacade
)

MT5ReadOnlyForwardAcquisitionAdapter: Any = (
    _acq.MT5ReadOnlyForwardAcquisitionAdapter
)


PERFORMANCE_EVALUATION_AUTHORIZED: bool = False
PNL_EVALUATION_AUTHORIZED: bool = False
LIVE_AUTHORIZED: bool = False
EXECUTION_AUTHORIZED: bool = False

RAW_MT5_CALLS: tuple[str, ...] = (
    "initialize",
    "shutdown",
)

_SHA256_RE = re.compile(
    r"^[a-f0-9]{64}$"
)


class Gate15DCB2DG2BlockedError(
    RuntimeError
):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise Gate15DCB2DG2BlockedError(
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
            chunk = handle.read(
                1024 * 1024
            )

            if not chunk:
                break

            digest.update(
                chunk
            )

    return digest.hexdigest()


def optional_sha256(
    path: Path,
) -> str | None:

    if not path.is_file():
        return None

    return sha256_file(
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

    process = git_process(
        *args
    )

    require(
        process.returncode == 0,
        (
            "GIT_COMMAND_FAILED:"
            + " ".join(args)
            + ":"
            + process.stderr.strip()
        ),
    )

    return process.stdout.rstrip(
        "\r\n"
    )


def normalize_git_path(
    value: str,
) -> str:

    return (
        value.strip()
        .replace(
            "\\",
            "/",
        )
    )


def status_paths() -> set[str]:

    output = git_output(
        "status",
        "--porcelain",
        "--untracked-files=all",
    )

    result: set[str] = set()

    for line in output.splitlines():

        if len(line) < 4:
            continue

        path = line[3:].strip()

        if " -> " in path:
            path = path.split(
                " -> ",
                1,
            )[1]

        if (
            path.startswith('"')
            and
            path.endswith('"')
        ):
            path = path[1:-1]

        result.add(
            normalize_git_path(
                path
            )
        )

    return result


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

    ancestor = git_process(
        "merge-base",
        "--is-ancestor",
        BASE_AUTHORITY_COMMIT,
        head,
    )

    require(
        ancestor.returncode == 0,
        (
            "BASE_AUTHORITY_NOT_ANCESTOR:"
            f"{BASE_AUTHORITY_COMMIT}"
        ),
    )

    allowed_local = {
        PASS_EVIDENCE_REL_PATH,
        BLOCKED_EVIDENCE_REL_PATH,
    }

    unexpected = (
        status_paths()
        -
        allowed_local
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
        "base_authority_commit": (
            BASE_AUTHORITY_COMMIT
        ),
    }


def verify_runtime_authorities() -> None:

    require(
        bool(
            _anchor.verify_authorities()
        ),
        "ANCHOR_AUTHORITY_INVALID",
    )

    require(
        bool(
            _maturer.verify_authorities()
        ),
        "MATURER_AUTHORITY_INVALID",
    )

    require(
        bool(
            _outcome_ledger.verify_authorities()
        ),
        "OUTCOME_LEDGER_AUTHORITY_INVALID",
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
        _maturer.EXPECTED_HORIZON_BARS
        ==
        12,
        "HORIZON_AUTHORITY_MISMATCH",
    )

    require(
        not PERFORMANCE_EVALUATION_AUTHORIZED,
        "PERFORMANCE_AUTHORIZATION_VIOLATION",
    )

    require(
        not PNL_EVALUATION_AUTHORIZED,
        "PNL_AUTHORIZATION_VIOLATION",
    )

    require(
        not LIVE_AUTHORIZED,
        "LIVE_AUTHORIZATION_VIOLATION",
    )

    require(
        not EXECUTION_AUTHORIZED,
        "EXECUTION_AUTHORIZATION_VIOLATION",
    )


def write_json(
    path: Path,
    document: Mapping[str, Any],
) -> None:

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary.write_text(
        json.dumps(
            dict(document),
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary.replace(
        path
    )


def find_unique_record(
    records: list[Any],
    observation_id: str,
    record_name: str,
) -> Any:

    matches = [
        record
        for record in records
        if (
            record.logical_observation_id
            ==
            observation_id
        )
    ]

    require(
        len(matches) == 1,
        (
            f"EXPECTED_ONE_{record_name}:"
            f"{len(matches)}"
        ),
    )

    return matches[0]


def run_gate(
    *,
    observation_id: str,
    append_outcome: bool,
) -> dict[str, Any]:

    observation_id = (
        observation_id.strip().lower()
    )

    require(
        bool(
            _SHA256_RE.fullmatch(
                observation_id
            )
        ),
        "INVALID_LOGICAL_OBSERVATION_ID",
    )

    repository_authority = (
        verify_repository_authority()
    )

    verify_runtime_authorities()

    observation_hash_before = (
        optional_sha256(
            OBSERVATION_LEDGER_PATH
        )
    )

    anchor_hash_before = (
        optional_sha256(
            ANCHOR_LEDGER_PATH
        )
    )

    outcome_hash_before = (
        optional_sha256(
            OUTCOME_LEDGER_PATH
        )
    )

    observation_ledger = ObservationLedger(
        OBSERVATION_LEDGER_PATH
    )

    anchor_ledger = AnchorLedger(
        ANCHOR_LEDGER_PATH
    )

    require(
        observation_ledger.validate_integrity(),
        "OBSERVATION_LEDGER_INTEGRITY_FAILED",
    )

    require(
        anchor_ledger.validate_integrity(),
        "ANCHOR_LEDGER_INTEGRITY_FAILED",
    )

    observation = find_unique_record(
        observation_ledger.read_all(),
        observation_id,
        "OBSERVATION",
    )

    anchor = find_unique_record(
        anchor_ledger.read_all(),
        observation_id,
        "ANCHOR",
    )

    initialized = bool(
        mt5.initialize()
    )

    require(
        initialized,
        "MT5_INITIALIZE_FAILED",
    )

    try:

        facade = (
            MT5ReadOnlyCapabilityFacade(
                mt5
            )
        )

        acquisition = (
            MT5ReadOnlyForwardAcquisitionAdapter(
                facade,
                is_synthetic=False,
                include_native_d1=False,
                timestamp_basis="AUTO",
            )
        )

        broker_symbol = (
            acquisition.resolve_broker_symbol()
        )

        require(
            broker_symbol
            ==
            observation.broker_symbol,
            (
                "BROKER_SYMBOL_MISMATCH:"
                f"{broker_symbol}!="
                f"{observation.broker_symbol}"
            ),
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
            snapshot.canonical_instrument
            ==
            CANONICAL_INSTRUMENT,
            (
                "CANONICAL_INSTRUMENT_MISMATCH:"
                f"{snapshot.canonical_instrument}"
            ),
        )

        require(
            snapshot.broker_symbol
            ==
            broker_symbol,
            "BROKER_SYMBOL_CHANGED_DURING_ACQUISITION",
        )

        outcome = (
            _maturer.mature_observation(
                observation=(
                    observation.to_dict()
                ),
                anchor=anchor,
                completed_m5_bars=(
                    snapshot.market_data[
                        "M5"
                    ].copy()
                ),
            )
        )

    finally:
        mt5.shutdown()

    append_result: Any | None = None
    outcome_count_before: int | None = None
    outcome_count_after: int | None = None

    if append_outcome:

        outcome_ledger = OutcomeLedger(
            OUTCOME_LEDGER_PATH,
            duplicate_handling=(
                OutcomeDuplicateHandling
                .IDEMPOTENT_IGNORE
            ),
        )

        require(
            outcome_ledger.validate_integrity(),
            "OUTCOME_LEDGER_INTEGRITY_FAILED_BEFORE_APPEND",
        )

        outcome_count_before = (
            outcome_ledger.count()
        )

        append_result = (
            outcome_ledger.append(
                outcome
            )
        )

        require(
            outcome_ledger.validate_integrity(),
            "OUTCOME_LEDGER_INTEGRITY_FAILED_AFTER_APPEND",
        )

        outcome_count_after = (
            outcome_ledger.count()
        )

        require(
            outcome_count_before
            is not None,
            "OUTCOME_COUNT_BEFORE_MISSING",
        )

        require(
            outcome_count_after
            is not None,
            "OUTCOME_COUNT_AFTER_MISSING",
        )

        assert (
            outcome_count_before
            is not None
        )

        assert (
            outcome_count_after
            is not None
        )

        outcome_count_delta = (
            outcome_count_after
            -
            outcome_count_before
        )

        require(
            outcome_count_delta
            in {
                0,
                1,
            },
            "OUTCOME_COUNT_DELTA_INVALID",
        )

    observation_hash_after = (
        optional_sha256(
            OBSERVATION_LEDGER_PATH
        )
    )

    anchor_hash_after = (
        optional_sha256(
            ANCHOR_LEDGER_PATH
        )
    )

    outcome_hash_after = (
        optional_sha256(
            OUTCOME_LEDGER_PATH
        )
    )

    require(
        observation_hash_before
        ==
        observation_hash_after,
        "OBSERVATION_LEDGER_CHANGED",
    )

    require(
        anchor_hash_before
        ==
        anchor_hash_after,
        "ANCHOR_LEDGER_CHANGED",
    )

    if not append_outcome:

        require(
            outcome_hash_before
            ==
            outcome_hash_after,
            "OUTCOME_LEDGER_CHANGED_DURING_DRY_RUN",
        )

    evidence: dict[str, Any] = {
        "gate_id": GATE_ID,
        "schema_version": SCHEMA_VERSION,
        "status": "PASS",
        "mode": (
            "APPEND_OUTCOME"
            if append_outcome
            else
            "DRY_RUN"
        ),
        "repository_authority": (
            repository_authority
        ),
        "logical_observation_id": (
            outcome.logical_observation_id
        ),
        "decision_time_utc": (
            outcome.decision_time_utc
        ),
        "broker_symbol": (
            observation.broker_symbol
        ),
        "canonical_instrument": (
            CANONICAL_INSTRUMENT
        ),
        "maturation_version": (
            outcome.maturation_version
        ),
        "horizon_bars": (
            outcome.horizon_bars
        ),
        "first_future_bar_time_utc": (
            outcome.first_future_bar_time_utc
        ),
        "last_future_bar_time_utc": (
            outcome.last_future_bar_time_utc
        ),
        "outcome_class": (
            outcome.outcome_class
        ),
        "outcome_label": (
            outcome.outcome_label
        ),
        "up_excursion_atr": (
            outcome.up_excursion_atr
        ),
        "down_excursion_atr": (
            outcome.down_excursion_atr
        ),
        "semantic_outcome_fingerprint": (
            outcome.semantic_fingerprint()
        ),
        "outcome_append_requested": (
            append_outcome
        ),
        "outcome_appended": (
            bool(
                append_result.appended
            )
            if append_result is not None
            else
            False
        ),
        "outcome_idempotent_duplicate": (
            bool(
                append_result.is_duplicate
            )
            if append_result is not None
            else
            False
        ),
        "outcome_count_before": (
            outcome_count_before
        ),
        "outcome_count_after": (
            outcome_count_after
        ),
        "observation_ledger_unchanged": True,
        "anchor_ledger_unchanged": True,
        "outcome_ledger_changed": (
            outcome_hash_before
            !=
            outcome_hash_after
        ),
        "forward_performance_evaluated": False,
        "pnl_evaluated": False,
        "live_authorized": False,
        "execution_authorized": False,
        "raw_mt5_calls": list(
            RAW_MT5_CALLS
        ),
    }

    write_json(
        PASS_EVIDENCE_PATH,
        evidence,
    )

    return evidence


def write_blocked_evidence(
    *,
    observation_id: str,
    append_outcome: bool,
    exc: BaseException,
) -> None:

    document = {
        "gate_id": GATE_ID,
        "schema_version": SCHEMA_VERSION,
        "status": "BLOCKED",
        "logical_observation_id": (
            observation_id
        ),
        "append_outcome_requested": (
            append_outcome
        ),
        "error_type": (
            type(exc).__name__
        ),
        "error": (
            str(exc)[:2000]
        ),
        "forward_performance_evaluated": False,
        "pnl_evaluated": False,
        "live_authorized": False,
        "execution_authorized": False,
    }

    write_json(
        BLOCKED_EVIDENCE_PATH,
        document,
    )


def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--observation-id",
        required=True,
    )

    parser.add_argument(
        "--append-outcome",
        action="store_true",
        default=False,
    )

    return parser.parse_args()


def main() -> int:

    args = parse_args()

    observation_id = str(
        args.observation_id
    )

    append_outcome = bool(
        args.append_outcome
    )

    try:

        evidence = run_gate(
            observation_id=(
                observation_id
            ),
            append_outcome=(
                append_outcome
            ),
        )

    except Exception as exc:

        write_blocked_evidence(
            observation_id=(
                observation_id
            ),
            append_outcome=(
                append_outcome
            ),
            exc=exc,
        )

        print(
            "GATE_15D_C_B2D_G2_STATUS=BLOCKED"
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
            "FORWARD_PERFORMANCE_EVALUATED=false"
        )
        print(
            "LIVE_AUTHORIZED=false"
        )
        print(
            "EXECUTION_AUTHORIZED=false"
        )

        return 2

    print(
        "GATE_15D_C_B2D_G2_STATUS=PASS"
    )

    print(
        "MODE="
        + str(
            evidence["mode"]
        )
    )

    print(
        "LOGICAL_OBSERVATION_ID="
        + str(
            evidence[
                "logical_observation_id"
            ]
        )
    )

    print(
        "OUTCOME_CLASS="
        + str(
            evidence[
                "outcome_class"
            ]
        )
    )

    print(
        "OUTCOME_LABEL="
        + str(
            evidence[
                "outcome_label"
            ]
        )
    )

    print(
        "HORIZON_BARS="
        + str(
            evidence[
                "horizon_bars"
            ]
        )
    )

    print(
        "OUTCOME_APPENDED="
        + str(
            evidence[
                "outcome_appended"
            ]
        ).lower()
    )

    print(
        "OUTCOME_IDEMPOTENT_DUPLICATE="
        + str(
            evidence[
                "outcome_idempotent_duplicate"
            ]
        ).lower()
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
    raise SystemExit(
        main()
    )
