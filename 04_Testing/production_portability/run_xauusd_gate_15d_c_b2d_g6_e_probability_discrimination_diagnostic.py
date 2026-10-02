from __future__ import annotations

import hashlib
import importlib
import json
import math
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
    "GATE_15D_C_B2D_G6_E_FORWARD_PROBABILITY_DISCRIMINATION_DIAGNOSTIC"
)

SCHEMA_VERSION = "1.0.0"

BASE_AUTHORITY_COMMIT = (
    "e1639f68cb686aafd949b6e402d576e4a0885257"
)

EXPECTED_SAMPLE_COUNT = 30

EXPECTED_CONTRACT_FINGERPRINT = (
    "32d8af41e2e1d128df664c8fc81bcf52a6a2b341f491a05d65179f740460875c"
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


G5_EVIDENCE_REL = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g5_30_sample_completion_freeze_evidence.json"
)

G6A_EVIDENCE_REL = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g6_a_forward_evaluation_protocol_freeze_evidence.json"
)

G6B_EVIDENCE_REL = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g6_b_baseline_forward_performance_evaluation_evidence.json"
)

G6C_EVIDENCE_REL = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g6_c_forward_error_confidence_diagnostic_evidence.json"
)

G6D_EVIDENCE_REL = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g6_d_probability_geometry_diagnostic_evidence.json"
)

CONTRACT_REL = (
    "02_AI/Models/"
    "frozen_c04_forward_performance_evaluation_contract.py"
)

G6E_RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g6_e_probability_discrimination_diagnostic.py"
)

G6E_TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g6_e_probability_discrimination_diagnostic.py"
)

EVIDENCE_REL = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g6_e_probability_discrimination_diagnostic_evidence.json"
)

EVIDENCE_PATH = (
    REPO_ROOT
    / EVIDENCE_REL
)


ALLOWED_LOCAL_PATHS = {
    G6E_RUNNER_REL,
    G6E_TEST_REL,
    EVIDENCE_REL,
}


HASH_BOUND_DEPENDENCIES = (
    CONTRACT_REL,
    G5_EVIDENCE_REL,
    G6A_EVIDENCE_REL,
    G6B_EVIDENCE_REL,
    G6C_EVIDENCE_REL,
    G6D_EVIDENCE_REL,
    "02_AI/Models/frozen_c04_shadow_observer.py",
    "02_AI/Models/frozen_c04_forward_outcome_ledger.py",
    G6E_RUNNER_REL,
    G6E_TEST_REL,
)


_contract: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_performance_evaluation_contract"
)

_observer: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_shadow_observer"
)

_outcome_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_ledger"
)


ObservationLedger: Any = (
    _observer.FrozenC04ObservationLedger
)

OutcomeLedger: Any = (
    _outcome_mod.FrozenC04ForwardOutcomeLedger
)


class G6EDiagnosticError(RuntimeError):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise G6EDiagnosticError(
            reason
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

        value = line[3:].strip()

        if " -> " in value:
            value = value.split(
                " -> ",
                1,
            )[1]

        if (
            value.startswith('"')
            and value.endswith('"')
        ):
            value = value[1:-1]

        result.add(
            value.replace(
                "\\",
                "/",
            )
        )

    return result


def raw_sha256(
    path: Path,
) -> str:

    require(
        path.is_file(),
        f"FILE_MISSING:{path}",
    )

    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest()


def canonical_sha256(
    path: Path,
) -> str:

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


def load_json(
    relative: str,
) -> dict[str, Any]:

    path = (
        REPO_ROOT
        / relative
    )

    require(
        path.is_file(),
        f"JSON_FILE_MISSING:{relative}",
    )

    value = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(
        value,
        dict,
    ):
        raise G6EDiagnosticError(
            f"JSON_ROOT_NOT_OBJECT:{relative}"
        )

    return value


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

    dirty = status_paths()

    unexpected = (
        dirty
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
        "allowed_local_paths": sorted(
            dirty
        ),
    }


def verify_authorities() -> dict[str, Any]:

    evidence_files = (
        G5_EVIDENCE_REL,
        G6A_EVIDENCE_REL,
        G6B_EVIDENCE_REL,
        G6C_EVIDENCE_REL,
        G6D_EVIDENCE_REL,
    )

    loaded: list[
        dict[str, Any]
    ] = []

    for relative in evidence_files:

        value = load_json(
            relative
        )

        require(
            value.get(
                "status"
            )
            ==
            "PASS",
            (
                "UPSTREAM_STATUS_NOT_PASS:"
                f"{relative}"
            ),
        )

        loaded.append(
            value
        )

    g6d = loaded[-1]

    diagnostic = g6d.get(
        "diagnostic"
    )

    if not isinstance(
        diagnostic,
        dict,
    ):
        raise G6EDiagnosticError(
            "G6D_DIAGNOSTIC_MISSING"
        )

    require(
        int(
            diagnostic.get(
                "sample_count",
                -1,
            )
        )
        ==
        EXPECTED_SAMPLE_COUNT,
        "G6D_SAMPLE_COUNT_MISMATCH",
    )

    current_fp = (
        _contract.contract_fingerprint_sha256()
    )

    require(
        current_fp
        ==
        EXPECTED_CONTRACT_FINGERPRINT,
        "CURRENT_CONTRACT_FINGERPRINT_MISMATCH",
    )

    require(
        _contract.RETRAINING_ALLOWED
        is False,
        "RETRAINING_ALLOWED",
    )

    require(
        _contract.REFITTING_ALLOWED
        is False,
        "REFITTING_ALLOWED",
    )

    require(
        _contract.MODEL_RESELECTION_ALLOWED
        is False,
        "MODEL_RESELECTION_ALLOWED",
    )

    require(
        _contract.THRESHOLD_TUNING_ALLOWED
        is False,
        "THRESHOLD_TUNING_ALLOWED",
    )

    require(
        _contract.PROBABILITY_CALIBRATION_ALLOWED
        is False,
        "CALIBRATION_ALLOWED",
    )

    require(
        _contract.PNL_EVALUATION_AUTHORIZED
        is False,
        "PNL_EVALUATION_AUTHORIZED",
    )

    require(
        _contract.LIVE_AUTHORIZED
        is False,
        "LIVE_AUTHORIZED",
    )

    require(
        _contract.EXECUTION_AUTHORIZED
        is False,
        "EXECUTION_AUTHORIZED",
    )

    return {
        "status": "PASS",
        "contract_fingerprint_sha256": (
            current_fp
        ),
        "upstream_gate_count": (
            len(
                evidence_files
            )
        ),
    }


def verify_exact_g5_ledgers() -> dict[str, Any]:

    g5 = load_json(
        G5_EVIDENCE_REL
    )

    expected = g5.get(
        "runtime_ledger_raw_sha256"
    )

    if not isinstance(
        expected,
        dict,
    ):
        raise G6EDiagnosticError(
            "G5_LEDGER_HASHES_MISSING"
        )

    actual = {
        "observation": raw_sha256(
            REPO_ROOT
            / OBSERVATION_LEDGER_REL
        ),
        "anchor": raw_sha256(
            REPO_ROOT
            / ANCHOR_LEDGER_REL
        ),
        "outcome": raw_sha256(
            REPO_ROOT
            / OUTCOME_LEDGER_REL
        ),
    }

    require(
        actual
        ==
        expected,
        (
            "RUNTIME_LEDGER_NOT_EXACT_G5_BASELINE:"
            f"actual={actual}:"
            f"expected={expected}"
        ),
    )

    return {
        "status": "PASS",
        "exact_g5_baseline": True,
        "runtime_ledger_raw_sha256": (
            actual
        ),
    }


def verify_observation_fingerprint(
    record: Any,
) -> None:

    recomputed = (
        _observer.compute_semantic_record_fingerprint(
            logical_observation_id=(
                record.logical_observation_id
            ),
            source_snapshot_id=(
                record.source_snapshot_id
            ),
            source_provenance=(
                record.source_provenance
            ),
            probability_short=(
                record.probability_short
            ),
            probability_no_trade=(
                record.probability_no_trade
            ),
            probability_long=(
                record.probability_long
            ),
            predicted_class=(
                record.predicted_class
            ),
            winning_probability=(
                record.winning_probability
            ),
            feature_count=(
                record.feature_count
            ),
            feature_columns_sha256=(
                record.feature_columns_sha256
            ),
            model_sha256=(
                record.model_sha256
            ),
        )
    )

    require(
        recomputed
        ==
        record.semantic_record_fingerprint,
        (
            "OBSERVATION_SEMANTIC_FINGERPRINT_MISMATCH:"
            f"{record.logical_observation_id}"
        ),
    )


def load_rows() -> list[dict[str, Any]]:

    observations = ObservationLedger(
        REPO_ROOT
        / OBSERVATION_LEDGER_REL
    )

    outcomes = OutcomeLedger(
        REPO_ROOT
        / OUTCOME_LEDGER_REL
    )

    require(
        observations.validate_integrity(),
        "OBSERVATION_LEDGER_INTEGRITY_FAILED",
    )

    require(
        outcomes.validate_integrity(),
        "OUTCOME_LEDGER_INTEGRITY_FAILED",
    )

    observation_records = (
        observations.read_all()
    )

    outcome_records = (
        outcomes.read_all()
    )

    require(
        len(
            outcome_records
        )
        ==
        EXPECTED_SAMPLE_COUNT,
        (
            "OUTCOME_COUNT_MISMATCH:"
            f"{len(outcome_records)}"
        ),
    )

    observation_by_id = {
        record.logical_observation_id: record
        for record
        in observation_records
    }

    rows: list[
        dict[str, Any]
    ] = []

    seen: set[str] = set()

    for outcome in outcome_records:

        logical_id = str(
            outcome.logical_observation_id
        )

        require(
            logical_id
            not in seen,
            (
                "DUPLICATE_OUTCOME_LOGICAL_ID:"
                f"{logical_id}"
            ),
        )

        seen.add(
            logical_id
        )

        require(
            logical_id
            in observation_by_id,
            (
                "OBSERVATION_MISSING_FOR_OUTCOME:"
                f"{logical_id}"
            ),
        )

        observation = (
            observation_by_id[
                logical_id
            ]
        )

        verify_observation_fingerprint(
            observation
        )

        require(
            observation.semantic_record_fingerprint
            ==
            outcome.source_observation_fingerprint,
            (
                "OUTCOME_OBSERVATION_FINGERPRINT_MISMATCH:"
                f"{logical_id}"
            ),
        )

        require(
            observation.decision_time_utc
            ==
            outcome.decision_time_utc,
            (
                "DECISION_TIME_LINKAGE_MISMATCH:"
                f"{logical_id}"
            ),
        )

        probabilities = {
            -1: float(
                observation.probability_short
            ),
            0: float(
                observation.probability_no_trade
            ),
            1: float(
                observation.probability_long
            ),
        }

        for probability in probabilities.values():

            require(
                math.isfinite(
                    probability
                ),
                (
                    "NON_FINITE_PROBABILITY:"
                    f"{logical_id}"
                ),
            )

            require(
                0.0
                <=
                probability
                <=
                1.0,
                (
                    "PROBABILITY_OUT_OF_RANGE:"
                    f"{logical_id}"
                ),
            )

        require(
            abs(
                sum(
                    probabilities.values()
                )
                -
                1.0
            )
            <=
            float(
                _contract.PROBABILITY_SUM_TOLERANCE
            ),
            (
                "PROBABILITY_SUM_MISMATCH:"
                f"{logical_id}"
            ),
        )

        ranked = sorted(
            probabilities.items(),
            key=lambda item: (
                item[1],
                item[0],
            ),
            reverse=True,
        )

        rank_by_class = {
            int(
                class_value
            ): rank
            for rank, (
                class_value,
                _,
            )
            in enumerate(
                ranked,
                start=1,
            )
        }

        outcome_class = int(
            outcome.outcome_class
        )

        rows.append(
            {
                "logical_observation_id": (
                    logical_id
                ),
                "decision_time_utc": (
                    str(
                        outcome.decision_time_utc
                    )
                ),
                "outcome_class": (
                    outcome_class
                ),
                "probability_short": (
                    probabilities[-1]
                ),
                "probability_no_trade": (
                    probabilities[0]
                ),
                "probability_long": (
                    probabilities[1]
                ),
                "true_class_probability": (
                    probabilities[
                        outcome_class
                    ]
                ),
                "true_class_rank": (
                    rank_by_class[
                        outcome_class
                    ]
                ),
            }
        )

    require(
        len(rows)
        ==
        EXPECTED_SAMPLE_COUNT,
        (
            "ROW_COUNT_MISMATCH:"
            f"{len(rows)}"
        ),
    )

    rows.sort(
        key=lambda row: (
            str(
                row[
                    "decision_time_utc"
                ]
            )
        )
    )

    return rows


def mean(
    values: list[float],
) -> float:

    if not values:
        return 0.0

    return (
        sum(values)
        /
        len(values)
    )


def class_probability(
    row: Mapping[str, Any],
    class_value: int,
) -> float:

    if class_value == -1:
        return float(
            row[
                "probability_short"
            ]
        )

    if class_value == 0:
        return float(
            row[
                "probability_no_trade"
            ]
        )

    if class_value == 1:
        return float(
            row[
                "probability_long"
            ]
        )

    raise G6EDiagnosticError(
        f"UNKNOWN_CLASS:{class_value}"
    )


def pairwise_auc(
    positive_scores: list[float],
    negative_scores: list[float],
) -> float:

    require(
        bool(
            positive_scores
        ),
        "AUC_POSITIVE_SET_EMPTY",
    )

    require(
        bool(
            negative_scores
        ),
        "AUC_NEGATIVE_SET_EMPTY",
    )

    wins = 0.0
    comparisons = 0

    for positive in positive_scores:

        for negative in negative_scores:

            comparisons += 1

            if positive > negative:
                wins += 1.0

            elif positive == negative:
                wins += 0.5

    require(
        comparisons > 0,
        "AUC_NO_COMPARISONS",
    )

    return (
        wins
        /
        comparisons
    )


def summarize_class(
    rows: list[
        dict[str, Any]
    ],
    class_value: int,
) -> dict[str, Any]:

    positive_rows = [
        row
        for row in rows
        if int(
            row[
                "outcome_class"
            ]
        )
        ==
        class_value
    ]

    negative_rows = [
        row
        for row in rows
        if int(
            row[
                "outcome_class"
            ]
        )
        !=
        class_value
    ]

    positive_scores = [
        class_probability(
            row,
            class_value,
        )
        for row
        in positive_rows
    ]

    negative_scores = [
        class_probability(
            row,
            class_value,
        )
        for row
        in negative_rows
    ]

    ranks = [
        int(
            row[
                "true_class_rank"
            ]
        )
        for row
        in positive_rows
    ]

    return {
        "class": class_value,
        "label": str(
            _contract.CLASS_LABELS[
                class_value
            ]
        ),
        "positive_count": (
            len(
                positive_rows
            )
        ),
        "negative_count": (
            len(
                negative_rows
            )
        ),
        "mean_probability_when_true": (
            mean(
                positive_scores
            )
        ),
        "mean_probability_when_not_true": (
            mean(
                negative_scores
            )
        ),
        "mean_probability_separation": (
            mean(
                positive_scores
            )
            -
            mean(
                negative_scores
            )
        ),
        "pairwise_auc": (
            pairwise_auc(
                positive_scores,
                negative_scores,
            )
        ),
        "true_class_rank_1_count": (
            sum(
                1
                for rank
                in ranks
                if rank == 1
            )
        ),
        "true_class_rank_2_count": (
            sum(
                1
                for rank
                in ranks
                if rank == 2
            )
        ),
        "true_class_rank_3_count": (
            sum(
                1
                for rank
                in ranks
                if rank == 3
            )
        ),
        "mean_true_class_rank": (
            mean(
                [
                    float(
                        rank
                    )
                    for rank
                    in ranks
                ]
            )
        ),
    }


def diagnostic_summary(
    rows: list[
        dict[str, Any]
    ],
) -> dict[str, Any]:

    require(
        len(rows)
        ==
        EXPECTED_SAMPLE_COUNT,
        "UNEXPECTED_DIAGNOSTIC_SAMPLE_COUNT",
    )

    per_class: dict[
        str,
        Any,
    ] = {}

    auc_values: list[float] = []
    separations: list[float] = []

    for class_value in (
        _contract.CLASS_ORDER
    ):

        summary = summarize_class(
            rows,
            int(
                class_value
            ),
        )

        label = str(
            summary[
                "label"
            ]
        )

        per_class[
            label
        ] = summary

        auc_values.append(
            float(
                summary[
                    "pairwise_auc"
                ]
            )
        )

        separations.append(
            float(
                summary[
                    "mean_probability_separation"
                ]
            )
        )

    true_probabilities = [
        float(
            row[
                "true_class_probability"
            ]
        )
        for row
        in rows
    ]

    true_ranks = [
        int(
            row[
                "true_class_rank"
            ]
        )
        for row
        in rows
    ]

    return {
        "sample_count": (
            len(rows)
        ),
        "per_class": (
            per_class
        ),
        "macro_pairwise_auc": (
            mean(
                auc_values
            )
        ),
        "macro_mean_probability_separation": (
            mean(
                separations
            )
        ),
        "mean_true_class_probability": (
            mean(
                true_probabilities
            )
        ),
        "true_class_rank_1_count": (
            sum(
                1
                for rank
                in true_ranks
                if rank == 1
            )
        ),
        "true_class_rank_2_count": (
            sum(
                1
                for rank
                in true_ranks
                if rank == 2
            )
        ),
        "true_class_rank_3_count": (
            sum(
                1
                for rank
                in true_ranks
                if rank == 3
            )
        ),
        "mean_true_class_rank": (
            mean(
                [
                    float(
                        rank
                    )
                    for rank
                    in true_ranks
                ]
            )
        ),
    }


def dependency_hashes() -> dict[str, str]:

    result: dict[str, str] = {}

    for relative in (
        HASH_BOUND_DEPENDENCIES
    ):

        path = (
            REPO_ROOT
            / relative
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

    before = {
        "observation": raw_sha256(
            REPO_ROOT
            / OBSERVATION_LEDGER_REL
        ),
        "anchor": raw_sha256(
            REPO_ROOT
            / ANCHOR_LEDGER_REL
        ),
        "outcome": raw_sha256(
            REPO_ROOT
            / OUTCOME_LEDGER_REL
        ),
    }

    repository = (
        verify_repository()
    )

    authorities = (
        verify_authorities()
    )

    baseline = (
        verify_exact_g5_ledgers()
    )

    rows = (
        load_rows()
    )

    diagnostic = (
        diagnostic_summary(
            rows
        )
    )

    after = {
        "observation": raw_sha256(
            REPO_ROOT
            / OBSERVATION_LEDGER_REL
        ),
        "anchor": raw_sha256(
            REPO_ROOT
            / ANCHOR_LEDGER_REL
        ),
        "outcome": raw_sha256(
            REPO_ROOT
            / OUTCOME_LEDGER_REL
        ),
    }

    require(
        before
        ==
        after,
        "RUNTIME_LEDGER_CHANGED_DURING_DIAGNOSTIC",
    )

    hashes = (
        dependency_hashes()
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
        "authority_verification": (
            authorities
        ),
        "baseline_authority": (
            baseline
        ),
        "diagnostic_scope": (
            "EXACT_G5_FROZEN_30_MATURED_FORWARD_OUTCOMES"
        ),
        "diagnostic_only": True,
        "diagnostic": (
            diagnostic
        ),
        "runtime_ledger_raw_sha256": (
            after
        ),
        "hashing_semantics": (
            "GIT_TEXT_CANONICAL_LF_SHA256"
        ),
        "hash_bound_dependencies": (
            hashes
        ),
        "hash_bound_file_count": (
            len(
                hashes
            )
        ),
        "performance_recalculated": False,
        "performance_interpreted_for_promotion": False,
        "pass_fail_threshold_defined": False,
        "probability_calibration_performed": False,
        "retraining_performed": False,
        "refitting_performed": False,
        "model_reselection_performed": False,
        "threshold_tuning_performed": False,
        "feature_reselection_performed": False,
        "pnl_evaluated": False,
        "ledger_write_performed": False,
        "market_data_acquired": False,
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
            "GATE_15D_C_B2D_G6_E_STATUS=BLOCKED"
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
            "CALIBRATION_PERFORMED=false"
        )

        print(
            "RETRAINING_PERFORMED=false"
        )

        print(
            "THRESHOLD_TUNING_PERFORMED=false"
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

    diagnostic = evidence[
        "diagnostic"
    ]

    per_class = diagnostic[
        "per_class"
    ]

    print(
        "GATE_15D_C_B2D_G6_E_STATUS=PASS"
    )

    print(
        "BASE_AUTHORITY_COMMIT="
        + evidence[
            "base_authority_commit"
        ]
    )

    print(
        "SAMPLE_COUNT="
        + str(
            diagnostic[
                "sample_count"
            ]
        )
    )

    for label in (
        "SHORT",
        "NO_TRADE",
        "LONG",
    ):

        summary = per_class[
            label
        ]

        print(
            f"{label}_MEAN_PROB_WHEN_TRUE="
            + format(
                float(
                    summary[
                        "mean_probability_when_true"
                    ]
                ),
                ".12f",
            )
        )

        print(
            f"{label}_MEAN_PROB_WHEN_NOT_TRUE="
            + format(
                float(
                    summary[
                        "mean_probability_when_not_true"
                    ]
                ),
                ".12f",
            )
        )

        print(
            f"{label}_PAIRWISE_AUC="
            + format(
                float(
                    summary[
                        "pairwise_auc"
                    ]
                ),
                ".12f",
            )
        )

        print(
            f"{label}_TRUE_RANK1_COUNT="
            + str(
                summary[
                    "true_class_rank_1_count"
                ]
            )
        )

    print(
        "MACRO_PAIRWISE_AUC="
        + format(
            float(
                diagnostic[
                    "macro_pairwise_auc"
                ]
            ),
            ".12f",
        )
    )

    print(
        "MACRO_MEAN_PROBABILITY_SEPARATION="
        + format(
            float(
                diagnostic[
                    "macro_mean_probability_separation"
                ]
            ),
            ".12f",
        )
    )

    print(
        "MEAN_TRUE_CLASS_PROBABILITY="
        + format(
            float(
                diagnostic[
                    "mean_true_class_probability"
                ]
            ),
            ".12f",
        )
    )

    print(
        "MEAN_TRUE_CLASS_RANK="
        + format(
            float(
                diagnostic[
                    "mean_true_class_rank"
                ]
            ),
            ".12f",
        )
    )

    print(
        "DIAGNOSTIC_ONLY=true"
    )

    print(
        "PERFORMANCE_RECALCULATED=false"
    )

    print(
        "CALIBRATION_PERFORMED=false"
    )

    print(
        "RETRAINING_PERFORMED=false"
    )

    print(
        "MODEL_RESELECTION_PERFORMED=false"
    )

    print(
        "THRESHOLD_TUNING_PERFORMED=false"
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