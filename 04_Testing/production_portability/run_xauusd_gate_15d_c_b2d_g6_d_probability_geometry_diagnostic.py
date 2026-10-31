from __future__ import annotations

import hashlib
import importlib
import json
import math
from pathlib import Path
import statistics
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
    "GATE_15D_C_B2D_G6_D_PROBABILITY_GEOMETRY_ARGMAX_BIAS_DIAGNOSTIC"
)

SCHEMA_VERSION = "1.0.0"

BASE_AUTHORITY_COMMIT = (
    "78d1b094700a7635c75851492d33340b64894351"
)

EXPECTED_SAMPLE_COUNT = 30

EXPECTED_CONTRACT_FINGERPRINT = (
    "32d8af41e2e1d128df664c8fc81bcf52a6a2b341f491a05d65179f740460875c"
)

UNIFORM_PROBABILITY = (
    1.0
    /
    3.0
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

CONTRACT_REL = (
    "02_AI/Models/"
    "frozen_c04_forward_performance_evaluation_contract.py"
)

G6D_RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g6_d_probability_geometry_diagnostic.py"
)

G6D_TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g6_d_probability_geometry_diagnostic.py"
)

EVIDENCE_REL = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g6_d_probability_geometry_diagnostic_evidence.json"
)

EVIDENCE_PATH = (
    REPO_ROOT
    / EVIDENCE_REL
)


ALLOWED_LOCAL_PATHS = {
    G6D_RUNNER_REL,
    G6D_TEST_REL,
    EVIDENCE_REL,
}


HASH_BOUND_DEPENDENCIES = (
    CONTRACT_REL,
    G5_EVIDENCE_REL,
    G6A_EVIDENCE_REL,
    G6B_EVIDENCE_REL,
    G6C_EVIDENCE_REL,
    "02_AI/Models/frozen_c04_shadow_observer.py",
    "02_AI/Models/frozen_c04_forward_outcome_ledger.py",
    G6D_RUNNER_REL,
    G6D_TEST_REL,
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


class G6DDiagnosticError(RuntimeError):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise G6DDiagnosticError(
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
        raise G6DDiagnosticError(
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

    g5 = load_json(
        G5_EVIDENCE_REL
    )

    g6a = load_json(
        G6A_EVIDENCE_REL
    )

    g6b = load_json(
        G6B_EVIDENCE_REL
    )

    g6c = load_json(
        G6C_EVIDENCE_REL
    )

    require(
        g5.get(
            "status"
        )
        ==
        "PASS",
        "G5_STATUS_NOT_PASS",
    )

    require(
        g6a.get(
            "status"
        )
        ==
        "PASS",
        "G6A_STATUS_NOT_PASS",
    )

    require(
        g6b.get(
            "status"
        )
        ==
        "PASS",
        "G6B_STATUS_NOT_PASS",
    )

    require(
        g6c.get(
            "status"
        )
        ==
        "PASS",
        "G6C_STATUS_NOT_PASS",
    )

    diagnostic = g6c.get(
        "diagnostic"
    )

    if not isinstance(
        diagnostic,
        dict,
    ):
        raise G6DDiagnosticError(
            "G6C_DIAGNOSTIC_MISSING"
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
        "G6C_SAMPLE_COUNT_MISMATCH",
    )

    require(
        int(
            diagnostic.get(
                "missed_short_count",
                -1,
            )
        )
        ==
        8,
        "G6C_MISSED_SHORT_COUNT_MISMATCH",
    )

    require(
        int(
            diagnostic.get(
                "false_long_count",
                -1,
            )
        )
        ==
        16,
        "G6C_FALSE_LONG_COUNT_MISMATCH",
    )

    require(
        int(
            diagnostic.get(
                "missed_no_trade_count",
                -1,
            )
        )
        ==
        10,
        "G6C_MISSED_NO_TRADE_COUNT_MISMATCH",
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
        "g5_status": "PASS",
        "g6a_status": "PASS",
        "g6b_status": "PASS",
        "g6c_status": "PASS",
        "contract_fingerprint_sha256": (
            current_fp
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
        raise G6DDiagnosticError(
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
            f"actual={actual}:expected={expected}"
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
            logical_id not in seen,
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
            bool(
                observation.is_true_forward_eligible
            ),
            (
                "OBSERVATION_NOT_FORWARD_ELIGIBLE:"
                f"{logical_id}"
            ),
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

        probability_sum = sum(
            probabilities.values()
        )

        require(
            abs(
                probability_sum
                -
                1.0
            )
            <=
            float(
                _contract.PROBABILITY_SUM_TOLERANCE
            ),
            (
                "PROBABILITY_SUM_MISMATCH:"
                f"{logical_id}:"
                f"{probability_sum}"
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

        predicted_class = int(
            observation.predicted_class
        )

        outcome_class = int(
            outcome.outcome_class
        )

        require(
            int(
                ranked[0][0]
            )
            ==
            predicted_class,
            (
                "ARGMAX_PREDICTION_MISMATCH:"
                f"{logical_id}"
            ),
        )

        entropy = 0.0

        for probability in probabilities.values():

            if probability > 0.0:

                entropy -= (
                    probability
                    *
                    math.log(
                        probability
                    )
                )

        max_entropy = math.log(
            3.0
        )

        normalized_entropy = (
            entropy
            /
            max_entropy
        )

        l1_uniform_distance = sum(
            abs(
                probability
                -
                UNIFORM_PROBABILITY
            )
            for probability
            in probabilities.values()
        )

        l2_uniform_distance = math.sqrt(
            sum(
                (
                    probability
                    -
                    UNIFORM_PROBABILITY
                )
                ** 2
                for probability
                in probabilities.values()
            )
        )

        winner_probability = float(
            ranked[0][1]
        )

        runner_up_probability = float(
            ranked[1][1]
        )

        margin = (
            winner_probability
            -
            runner_up_probability
        )

        rows.append(
            {
                "logical_observation_id": (
                    logical_id
                ),
                "decision_time_utc": (
                    str(
                        observation.decision_time_utc
                    )
                ),
                "predicted_class": (
                    predicted_class
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
                "rank_1_class": int(
                    ranked[0][0]
                ),
                "rank_2_class": int(
                    ranked[1][0]
                ),
                "rank_3_class": int(
                    ranked[2][0]
                ),
                "winner_probability": (
                    winner_probability
                ),
                "runner_up_probability": (
                    runner_up_probability
                ),
                "confidence_margin": (
                    margin
                ),
                "entropy": (
                    entropy
                ),
                "normalized_entropy": (
                    normalized_entropy
                ),
                "l1_uniform_distance": (
                    l1_uniform_distance
                ),
                "l2_uniform_distance": (
                    l2_uniform_distance
                ),
                "correct": (
                    predicted_class
                    ==
                    outcome_class
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


def median(
    values: list[float],
) -> float:

    if not values:
        return 0.0

    return float(
        statistics.median(
            values
        )
    )


def minimum(
    values: list[float],
) -> float:

    if not values:
        return 0.0

    return min(
        values
    )


def maximum(
    values: list[float],
) -> float:

    if not values:
        return 0.0

    return max(
        values
    )


def class_label(
    value: int,
) -> str:

    return str(
        _contract.CLASS_LABELS[
            value
        ]
    )


def summarize_probability_vector(
    rows: list[
        dict[str, Any]
    ],
) -> dict[str, Any]:

    probability_short = [
        float(
            row[
                "probability_short"
            ]
        )
        for row in rows
    ]

    probability_no_trade = [
        float(
            row[
                "probability_no_trade"
            ]
        )
        for row in rows
    ]

    probability_long = [
        float(
            row[
                "probability_long"
            ]
        )
        for row in rows
    ]

    return {
        "SHORT": {
            "mean": mean(
                probability_short
            ),
            "median": median(
                probability_short
            ),
            "min": minimum(
                probability_short
            ),
            "max": maximum(
                probability_short
            ),
        },
        "NO_TRADE": {
            "mean": mean(
                probability_no_trade
            ),
            "median": median(
                probability_no_trade
            ),
            "min": minimum(
                probability_no_trade
            ),
            "max": maximum(
                probability_no_trade
            ),
        },
        "LONG": {
            "mean": mean(
                probability_long
            ),
            "median": median(
                probability_long
            ),
            "min": minimum(
                probability_long
            ),
            "max": maximum(
                probability_long
            ),
        },
    }


def summarize_by_outcome(
    rows: list[
        dict[str, Any]
    ],
) -> dict[str, Any]:

    result: dict[
        str,
        Any,
    ] = {}

    for outcome_class in (
        _contract.CLASS_ORDER
    ):

        class_rows = [
            row
            for row in rows
            if int(
                row[
                    "outcome_class"
                ]
            )
            ==
            int(
                outcome_class
            )
        ]

        result[
            class_label(
                int(
                    outcome_class
                )
            )
        ] = {
            "sample_count": (
                len(
                    class_rows
                )
            ),
            "mean_probabilities": {
                "SHORT": mean(
                    [
                        float(
                            row[
                                "probability_short"
                            ]
                        )
                        for row
                        in class_rows
                    ]
                ),
                "NO_TRADE": mean(
                    [
                        float(
                            row[
                                "probability_no_trade"
                            ]
                        )
                        for row
                        in class_rows
                    ]
                ),
                "LONG": mean(
                    [
                        float(
                            row[
                                "probability_long"
                            ]
                        )
                        for row
                        in class_rows
                    ]
                ),
            },
            "mean_winner_probability": mean(
                [
                    float(
                        row[
                            "winner_probability"
                        ]
                    )
                    for row
                    in class_rows
                ]
            ),
            "mean_confidence_margin": mean(
                [
                    float(
                        row[
                            "confidence_margin"
                        ]
                    )
                    for row
                    in class_rows
                ]
            ),
            "mean_normalized_entropy": mean(
                [
                    float(
                        row[
                            "normalized_entropy"
                        ]
                    )
                    for row
                    in class_rows
                ]
            ),
        }

    return result


def summarize_by_prediction(
    rows: list[
        dict[str, Any]
    ],
) -> dict[str, Any]:

    result: dict[
        str,
        Any,
    ] = {}

    for predicted_class in (
        _contract.CLASS_ORDER
    ):

        class_rows = [
            row
            for row in rows
            if int(
                row[
                    "predicted_class"
                ]
            )
            ==
            int(
                predicted_class
            )
        ]

        result[
            class_label(
                int(
                    predicted_class
                )
            )
        ] = {
            "sample_count": (
                len(
                    class_rows
                )
            ),
            "mean_winner_probability": mean(
                [
                    float(
                        row[
                            "winner_probability"
                        ]
                    )
                    for row
                    in class_rows
                ]
            ),
            "mean_confidence_margin": mean(
                [
                    float(
                        row[
                            "confidence_margin"
                        ]
                    )
                    for row
                    in class_rows
                ]
            ),
            "mean_normalized_entropy": mean(
                [
                    float(
                        row[
                            "normalized_entropy"
                        ]
                    )
                    for row
                    in class_rows
                ]
            ),
            "mean_l1_uniform_distance": mean(
                [
                    float(
                        row[
                            "l1_uniform_distance"
                        ]
                    )
                    for row
                    in class_rows
                ]
            ),
        }

    return result


def rank_frequency(
    rows: list[
        dict[str, Any]
    ],
) -> dict[str, Any]:

    result: dict[
        str,
        dict[
            str,
            int,
        ],
    ] = {
        "rank_1": {
            "SHORT": 0,
            "NO_TRADE": 0,
            "LONG": 0,
        },
        "rank_2": {
            "SHORT": 0,
            "NO_TRADE": 0,
            "LONG": 0,
        },
        "rank_3": {
            "SHORT": 0,
            "NO_TRADE": 0,
            "LONG": 0,
        },
    }

    rank_fields = (
        (
            "rank_1",
            "rank_1_class",
        ),
        (
            "rank_2",
            "rank_2_class",
        ),
        (
            "rank_3",
            "rank_3_class",
        ),
    )

    for row in rows:

        for (
            output_key,
            field_name,
        ) in rank_fields:

            value = int(
                row[
                    field_name
                ]
            )

            result[
                output_key
            ][
                class_label(
                    value
                )
            ] += 1

    return result


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

    margins = [
        float(
            row[
                "confidence_margin"
            ]
        )
        for row in rows
    ]

    winners = [
        float(
            row[
                "winner_probability"
            ]
        )
        for row in rows
    ]

    normalized_entropies = [
        float(
            row[
                "normalized_entropy"
            ]
        )
        for row in rows
    ]

    l1_distances = [
        float(
            row[
                "l1_uniform_distance"
            ]
        )
        for row in rows
    ]

    l2_distances = [
        float(
            row[
                "l2_uniform_distance"
            ]
        )
        for row in rows
    ]

    correct_rows = [
        row
        for row in rows
        if bool(
            row[
                "correct"
            ]
        )
    ]

    incorrect_rows = [
        row
        for row in rows
        if not bool(
            row[
                "correct"
            ]
        )
    ]

    most_uniform = sorted(
        rows,
        key=lambda row: (
            float(
                row[
                    "l2_uniform_distance"
                ]
            )
        ),
    )

    largest_margin = sorted(
        rows,
        key=lambda row: (
            float(
                row[
                    "confidence_margin"
                ]
            )
        ),
        reverse=True,
    )

    smallest_margin = sorted(
        rows,
        key=lambda row: (
            float(
                row[
                    "confidence_margin"
                ]
            )
        ),
    )

    return {
        "sample_count": (
            len(rows)
        ),
        "uniform_reference_probability": (
            UNIFORM_PROBABILITY
        ),
        "overall_probability_summary": (
            summarize_probability_vector(
                rows
            )
        ),
        "rank_frequency": (
            rank_frequency(
                rows
            )
        ),
        "by_true_outcome": (
            summarize_by_outcome(
                rows
            )
        ),
        "by_predicted_class": (
            summarize_by_prediction(
                rows
            )
        ),
        "winner_probability": {
            "mean": mean(
                winners
            ),
            "median": median(
                winners
            ),
            "min": minimum(
                winners
            ),
            "max": maximum(
                winners
            ),
        },
        "confidence_margin": {
            "mean": mean(
                margins
            ),
            "median": median(
                margins
            ),
            "min": minimum(
                margins
            ),
            "max": maximum(
                margins
            ),
        },
        "normalized_entropy": {
            "mean": mean(
                normalized_entropies
            ),
            "median": median(
                normalized_entropies
            ),
            "min": minimum(
                normalized_entropies
            ),
            "max": maximum(
                normalized_entropies
            ),
        },
        "uniform_distance": {
            "mean_l1": mean(
                l1_distances
            ),
            "median_l1": median(
                l1_distances
            ),
            "mean_l2": mean(
                l2_distances
            ),
            "median_l2": median(
                l2_distances
            ),
        },
        "correct_vs_incorrect": {
            "correct_count": (
                len(
                    correct_rows
                )
            ),
            "incorrect_count": (
                len(
                    incorrect_rows
                )
            ),
            "mean_entropy_correct": mean(
                [
                    float(
                        row[
                            "normalized_entropy"
                        ]
                    )
                    for row
                    in correct_rows
                ]
            ),
            "mean_entropy_incorrect": mean(
                [
                    float(
                        row[
                            "normalized_entropy"
                        ]
                    )
                    for row
                    in incorrect_rows
                ]
            ),
            "mean_uniform_distance_correct": mean(
                [
                    float(
                        row[
                            "l2_uniform_distance"
                        ]
                    )
                    for row
                    in correct_rows
                ]
            ),
            "mean_uniform_distance_incorrect": mean(
                [
                    float(
                        row[
                            "l2_uniform_distance"
                        ]
                    )
                    for row
                    in incorrect_rows
                ]
            ),
        },
        "most_uniform_probability_rows": (
            most_uniform[
                :5
            ]
        ),
        "largest_margin_rows": (
            largest_margin[
                :5
            ]
        ),
        "smallest_margin_rows": (
            smallest_margin[
                :5
            ]
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
            "GATE_15D_C_B2D_G6_D_STATUS=BLOCKED"
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

    probabilities = diagnostic[
        "overall_probability_summary"
    ]

    ranks = diagnostic[
        "rank_frequency"
    ]

    print(
        "GATE_15D_C_B2D_G6_D_STATUS=PASS"
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

    print(
        "MEAN_PROBABILITY_SHORT="
        + format(
            float(
                probabilities[
                    "SHORT"
                ][
                    "mean"
                ]
            ),
            ".12f",
        )
    )

    print(
        "MEAN_PROBABILITY_NO_TRADE="
        + format(
            float(
                probabilities[
                    "NO_TRADE"
                ][
                    "mean"
                ]
            ),
            ".12f",
        )
    )

    print(
        "MEAN_PROBABILITY_LONG="
        + format(
            float(
                probabilities[
                    "LONG"
                ][
                    "mean"
                ]
            ),
            ".12f",
        )
    )

    print(
        "MEAN_WINNER_PROBABILITY="
        + format(
            float(
                diagnostic[
                    "winner_probability"
                ][
                    "mean"
                ]
            ),
            ".12f",
        )
    )

    print(
        "MEAN_CONFIDENCE_MARGIN="
        + format(
            float(
                diagnostic[
                    "confidence_margin"
                ][
                    "mean"
                ]
            ),
            ".12f",
        )
    )

    print(
        "MEAN_NORMALIZED_ENTROPY="
        + format(
            float(
                diagnostic[
                    "normalized_entropy"
                ][
                    "mean"
                ]
            ),
            ".12f",
        )
    )

    print(
        "MEAN_L2_DISTANCE_FROM_UNIFORM="
        + format(
            float(
                diagnostic[
                    "uniform_distance"
                ][
                    "mean_l2"
                ]
            ),
            ".12f",
        )
    )

    print(
        "RANK1_SHORT_COUNT="
        + str(
            ranks[
                "rank_1"
            ][
                "SHORT"
            ]
        )
    )

    print(
        "RANK1_NO_TRADE_COUNT="
        + str(
            ranks[
                "rank_1"
            ][
                "NO_TRADE"
            ]
        )
    )

    print(
        "RANK1_LONG_COUNT="
        + str(
            ranks[
                "rank_1"
            ][
                "LONG"
            ]
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