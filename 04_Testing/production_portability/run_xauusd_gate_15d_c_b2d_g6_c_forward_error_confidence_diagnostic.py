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
    "GATE_15D_C_B2D_G6_C_FORWARD_ERROR_CONFIDENCE_DIAGNOSTIC"
)

SCHEMA_VERSION = "1.0.0"

BASE_AUTHORITY_COMMIT = (
    "ddc028899f382a2ea24520ea1ed0347d06906c00"
)

EXPECTED_SAMPLE_COUNT = 30

EXPECTED_CONTRACT_FINGERPRINT = (
    "32d8af41e2e1d128df664c8fc81bcf52a6a2b341f491a05d65179f740460875c"
)

HIGH_CONFIDENCE_ERROR_THRESHOLD = 0.50


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

CONTRACT_REL = (
    "02_AI/Models/"
    "frozen_c04_forward_performance_evaluation_contract.py"
)

G6C_RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g6_c_forward_error_confidence_diagnostic.py"
)

G6C_TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g6_c_forward_error_confidence_diagnostic.py"
)

EVIDENCE_REL = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g6_c_forward_error_confidence_diagnostic_evidence.json"
)

EVIDENCE_PATH = (
    REPO_ROOT
    / EVIDENCE_REL
)


ALLOWED_LOCAL_PATHS = {
    G6C_RUNNER_REL,
    G6C_TEST_REL,
    EVIDENCE_REL,
}


HASH_BOUND_DEPENDENCIES = (
    CONTRACT_REL,
    G5_EVIDENCE_REL,
    G6A_EVIDENCE_REL,
    G6B_EVIDENCE_REL,
    "02_AI/Models/frozen_c04_shadow_observer.py",
    "02_AI/Models/frozen_c04_forward_outcome_ledger.py",
    G6C_RUNNER_REL,
    G6C_TEST_REL,
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


class G6CDiagnosticError(RuntimeError):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise G6CDiagnosticError(
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
        raise G6CDiagnosticError(
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
        - ALLOWED_LOCAL_PATHS
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
        g6b.get(
            "performance_calculated"
        )
        is True,
        "G6B_PERFORMANCE_NOT_CALCULATED",
    )

    require(
        g6b.get(
            "performance_interpreted_for_promotion"
        )
        is False,
        "G6B_PROMOTION_INTERPRETATION_ALREADY_PERFORMED",
    )

    require(
        g6b.get(
            "pnl_evaluated"
        )
        is False,
        "G6B_PNL_ALREADY_EVALUATED",
    )

    metrics = g6b.get(
        "cumulative_metrics"
    )

    if not isinstance(
        metrics,
        dict,
    ):
        raise G6CDiagnosticError(
            "G6B_CUMULATIVE_METRICS_MISSING"
        )

    require(
        int(
            metrics.get(
                "sample_count",
                -1,
            )
        )
        ==
        EXPECTED_SAMPLE_COUNT,
        "G6B_SAMPLE_COUNT_MISMATCH",
    )

    protocol = g6b.get(
        "protocol_authority"
    )

    if not isinstance(
        protocol,
        dict,
    ):
        raise G6CDiagnosticError(
            "G6B_PROTOCOL_AUTHORITY_MISSING"
        )

    require(
        protocol.get(
            "contract_fingerprint_sha256"
        )
        ==
        EXPECTED_CONTRACT_FINGERPRINT,
        "G6B_CONTRACT_FINGERPRINT_MISMATCH",
    )

    current_contract_fp = (
        _contract.contract_fingerprint_sha256()
    )

    require(
        current_contract_fp
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
        _contract.PASS_FAIL_THRESHOLD_DEFINED
        is False,
        "PASS_FAIL_THRESHOLD_DEFINED",
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
        "contract_fingerprint_sha256": (
            current_contract_fp
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
        raise G6CDiagnosticError(
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
        "runtime_ledger_raw_sha256": actual,
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

    observation_ledger = ObservationLedger(
        REPO_ROOT
        / OBSERVATION_LEDGER_REL
    )

    outcome_ledger = OutcomeLedger(
        REPO_ROOT
        / OUTCOME_LEDGER_REL
    )

    require(
        observation_ledger.validate_integrity(),
        "OBSERVATION_LEDGER_INTEGRITY_FAILED",
    )

    require(
        outcome_ledger.validate_integrity(),
        "OUTCOME_LEDGER_INTEGRITY_FAILED",
    )

    observations = (
        observation_ledger.read_all()
    )

    outcomes = (
        outcome_ledger.read_all()
    )

    require(
        len(outcomes)
        ==
        EXPECTED_SAMPLE_COUNT,
        (
            "OUTCOME_COUNT_MISMATCH:"
            f"{len(outcomes)}"
        ),
    )

    observation_by_id = {
        record.logical_observation_id: record
        for record in observations
    }

    rows: list[
        dict[str, Any]
    ] = []

    seen: set[str] = set()

    class_order = tuple(
        _contract.CLASS_ORDER
    )

    for outcome in outcomes:

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

        require(
            tuple(
                observation.class_order
            )
            ==
            class_order,
            (
                "CLASS_ORDER_MISMATCH:"
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

        for probability in (
            probabilities.values()
        ):

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
                    f"{logical_id}:"
                    f"{probability}"
                ),
            )

        predicted_class = int(
            observation.predicted_class
        )

        outcome_class = int(
            outcome.outcome_class
        )

        require(
            predicted_class
            in class_order,
            (
                "INVALID_PREDICTED_CLASS:"
                f"{logical_id}"
            ),
        )

        require(
            outcome_class
            in class_order,
            (
                "INVALID_OUTCOME_CLASS:"
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

        winner_class = int(
            ranked[0][0]
        )

        winner_probability = float(
            ranked[0][1]
        )

        runner_up_class = int(
            ranked[1][0]
        )

        runner_up_probability = float(
            ranked[1][1]
        )

        require(
            winner_class
            ==
            predicted_class,
            (
                "ARGMAX_PREDICTION_MISMATCH:"
                f"{logical_id}:"
                f"{winner_class}!="
                f"{predicted_class}"
            ),
        )

        margin = (
            winner_probability
            -
            runner_up_probability
        )

        correct = (
            predicted_class
            ==
            outcome_class
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
                "predicted_label": (
                    str(
                        observation.predicted_label
                    )
                ),
                "outcome_class": (
                    outcome_class
                ),
                "outcome_label": (
                    str(
                        outcome.outcome_label
                    )
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
                "winner_probability": (
                    winner_probability
                ),
                "runner_up_class": (
                    runner_up_class
                ),
                "runner_up_probability": (
                    runner_up_probability
                ),
                "confidence_margin": (
                    margin
                ),
                "correct": (
                    correct
                ),
                "high_confidence_error": (
                    (not correct)
                    and
                    winner_probability
                    >=
                    HIGH_CONFIDENCE_ERROR_THRESHOLD
                ),
            }
        )

    require(
        len(rows)
        ==
        EXPECTED_SAMPLE_COUNT,
        (
            "DIAGNOSTIC_ROW_COUNT_MISMATCH:"
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

    labels = {
        int(key): str(value)
        for key, value
        in _contract.CLASS_LABELS.items()
    }

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

    high_confidence_errors = [
        row
        for row in incorrect_rows
        if bool(
            row[
                "high_confidence_error"
            ]
        )
    ]

    false_long = [
        row
        for row in rows
        if int(
            row[
                "predicted_class"
            ]
        )
        ==
        1
        and int(
            row[
                "outcome_class"
            ]
        )
        !=
        1
    ]

    missed_short = [
        row
        for row in rows
        if int(
            row[
                "outcome_class"
            ]
        )
        ==
        -1
        and int(
            row[
                "predicted_class"
            ]
        )
        !=
        -1
    ]

    missed_no_trade = [
        row
        for row in rows
        if int(
            row[
                "outcome_class"
            ]
        )
        ==
        0
        and int(
            row[
                "predicted_class"
            ]
        )
        !=
        0
    ]

    pair_counts: dict[
        str,
        int,
    ] = {}

    for row in rows:

        predicted = labels[
            int(
                row[
                    "predicted_class"
                ]
            )
        ]

        actual = labels[
            int(
                row[
                    "outcome_class"
                ]
            )
        ]

        key = (
            predicted
            +
            "->"
            +
            actual
        )

        pair_counts[
            key
        ] = (
            pair_counts.get(
                key,
                0,
            )
            +
            1
        )

    per_predicted_class: dict[
        str,
        dict[str, Any],
    ] = {}

    for class_value in (
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
                class_value
            )
        ]

        class_correct = [
            row
            for row in class_rows
            if bool(
                row[
                    "correct"
                ]
            )
        ]

        label = labels[
            int(
                class_value
            )
        ]

        per_predicted_class[
            label
        ] = {
            "prediction_count": (
                len(
                    class_rows
                )
            ),
            "correct_count": (
                len(
                    class_correct
                )
            ),
            "mean_winner_probability": (
                mean(
                    [
                        float(
                            row[
                                "winner_probability"
                            ]
                        )
                        for row
                        in class_rows
                    ]
                )
            ),
            "mean_confidence_margin": (
                mean(
                    [
                        float(
                            row[
                                "confidence_margin"
                            ]
                        )
                        for row
                        in class_rows
                    ]
                )
            ),
        }

    incorrect_details = sorted(
        incorrect_rows,
        key=lambda row: (
            float(
                row[
                    "winner_probability"
                ]
            ),
            float(
                row[
                    "confidence_margin"
                ]
            ),
        ),
        reverse=True,
    )

    high_confidence_details = sorted(
        high_confidence_errors,
        key=lambda row: (
            float(
                row[
                    "winner_probability"
                ]
            ),
            float(
                row[
                    "confidence_margin"
                ]
            ),
        ),
        reverse=True,
    )

    false_long_details = sorted(
        false_long,
        key=lambda row: (
            float(
                row[
                    "probability_long"
                ]
            ),
            float(
                row[
                    "confidence_margin"
                ]
            ),
        ),
        reverse=True,
    )

    missed_short_details = sorted(
        missed_short,
        key=lambda row: (
            float(
                row[
                    "probability_short"
                ]
            ),
        ),
    )

    missed_no_trade_details = sorted(
        missed_no_trade,
        key=lambda row: (
            float(
                row[
                    "probability_no_trade"
                ]
            ),
        ),
    )

    return {
        "sample_count": (
            len(rows)
        ),
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
        "correct_rate": (
            len(
                correct_rows
            )
            /
            len(rows)
        ),
        "mean_winner_probability_correct": (
            mean(
                [
                    float(
                        row[
                            "winner_probability"
                        ]
                    )
                    for row
                    in correct_rows
                ]
            )
        ),
        "mean_winner_probability_incorrect": (
            mean(
                [
                    float(
                        row[
                            "winner_probability"
                        ]
                    )
                    for row
                    in incorrect_rows
                ]
            )
        ),
        "mean_margin_correct": (
            mean(
                [
                    float(
                        row[
                            "confidence_margin"
                        ]
                    )
                    for row
                    in correct_rows
                ]
            )
        ),
        "mean_margin_incorrect": (
            mean(
                [
                    float(
                        row[
                            "confidence_margin"
                        ]
                    )
                    for row
                    in incorrect_rows
                ]
            )
        ),
        "high_confidence_error_threshold": (
            HIGH_CONFIDENCE_ERROR_THRESHOLD
        ),
        "high_confidence_error_count": (
            len(
                high_confidence_errors
            )
        ),
        "false_long_count": (
            len(
                false_long
            )
        ),
        "missed_short_count": (
            len(
                missed_short
            )
        ),
        "missed_no_trade_count": (
            len(
                missed_no_trade
            )
        ),
        "prediction_outcome_pair_counts": (
            pair_counts
        ),
        "per_predicted_class_confidence": (
            per_predicted_class
        ),
        "high_confidence_errors": (
            high_confidence_details
        ),
        "false_long_errors": (
            false_long_details
        ),
        "missed_short_errors": (
            missed_short_details
        ),
        "missed_no_trade_errors": (
            missed_no_trade_details
        ),
        "all_incorrect_predictions": (
            incorrect_details
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
            len(hashes)
        ),
        "performance_recalculated": False,
        "performance_interpreted_for_promotion": False,
        "pass_fail_threshold_defined": False,
        "high_confidence_error_threshold_is_trading_threshold": False,
        "retraining_performed": False,
        "refitting_performed": False,
        "calibration_performed": False,
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
            "GATE_15D_C_B2D_G6_C_STATUS=BLOCKED"
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
            "RETRAINING_PERFORMED=false"
        )
        print(
            "CALIBRATION_PERFORMED=false"
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

    print(
        "GATE_15D_C_B2D_G6_C_STATUS=PASS"
    )

    print(
        "BASE_AUTHORITY_COMMIT="
        + evidence[
            "base_authority_commit"
        ]
    )

    print(
        "DIAGNOSTIC_SCOPE=EXACT_G5_FROZEN_30_MATURED_FORWARD_OUTCOMES"
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
        "CORRECT_COUNT="
        + str(
            diagnostic[
                "correct_count"
            ]
        )
    )

    print(
        "INCORRECT_COUNT="
        + str(
            diagnostic[
                "incorrect_count"
            ]
        )
    )

    print(
        "MEAN_WINNER_PROBABILITY_CORRECT="
        + format(
            float(
                diagnostic[
                    "mean_winner_probability_correct"
                ]
            ),
            ".12f",
        )
    )

    print(
        "MEAN_WINNER_PROBABILITY_INCORRECT="
        + format(
            float(
                diagnostic[
                    "mean_winner_probability_incorrect"
                ]
            ),
            ".12f",
        )
    )

    print(
        "MEAN_MARGIN_CORRECT="
        + format(
            float(
                diagnostic[
                    "mean_margin_correct"
                ]
            ),
            ".12f",
        )
    )

    print(
        "MEAN_MARGIN_INCORRECT="
        + format(
            float(
                diagnostic[
                    "mean_margin_incorrect"
                ]
            ),
            ".12f",
        )
    )

    print(
        "HIGH_CONFIDENCE_ERROR_THRESHOLD="
        + format(
            HIGH_CONFIDENCE_ERROR_THRESHOLD,
            ".2f",
        )
    )

    print(
        "HIGH_CONFIDENCE_ERROR_COUNT="
        + str(
            diagnostic[
                "high_confidence_error_count"
            ]
        )
    )

    print(
        "FALSE_LONG_COUNT="
        + str(
            diagnostic[
                "false_long_count"
            ]
        )
    )

    print(
        "MISSED_SHORT_COUNT="
        + str(
            diagnostic[
                "missed_short_count"
            ]
        )
    )

    print(
        "MISSED_NO_TRADE_COUNT="
        + str(
            diagnostic[
                "missed_no_trade_count"
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
        "PERFORMANCE_INTERPRETED_FOR_PROMOTION=false"
    )
    print(
        "PASS_FAIL_THRESHOLD_DEFINED=false"
    )
    print(
        "RETRAINING_PERFORMED=false"
    )
    print(
        "REFITTING_PERFORMED=false"
    )
    print(
        "CALIBRATION_PERFORMED=false"
    )
    print(
        "MODEL_RESELECTION_PERFORMED=false"
    )
    print(
        "THRESHOLD_TUNING_PERFORMED=false"
    )
    print(
        "FEATURE_RESELECTION_PERFORMED=false"
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