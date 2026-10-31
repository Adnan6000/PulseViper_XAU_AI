from __future__ import annotations

import datetime as dt
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
    "GATE_15D_C_B2D_G6_B_BASELINE_FORWARD_PERFORMANCE_EVALUATION"
)

SCHEMA_VERSION = "1.0.0"

BASE_AUTHORITY_COMMIT = (
    "b6c19f6a9fa652efcd1af566996dc77a32e1c279"
)

EXPECTED_CONTRACT_FINGERPRINT = (
    "32d8af41e2e1d128df664c8fc81bcf52a6a2b341f491a05d65179f740460875c"
)

EXPECTED_BASELINE_SAMPLE_COUNT = 30


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

CONTRACT_REL = (
    "02_AI/Models/"
    "frozen_c04_forward_performance_evaluation_contract.py"
)

G6B_RUNNER_REL = (
    "04_Testing/production_portability/"
    "run_xauusd_gate_15d_c_b2d_g6_b_baseline_forward_performance_evaluation.py"
)

G6B_TEST_REL = (
    "04_Testing/production_portability/"
    "test_gate_15d_c_b2d_g6_b_baseline_forward_performance_evaluation.py"
)

EVIDENCE_REL = (
    "04_Testing/evidence/forward_shadow/"
    "xauusd_gate_15d_c_b2d_g6_b_baseline_forward_performance_evaluation_evidence.json"
)

EVIDENCE_PATH = (
    REPO_ROOT
    / EVIDENCE_REL
)


ALLOWED_LOCAL_PATHS = {
    G6B_RUNNER_REL,
    G6B_TEST_REL,
    EVIDENCE_REL,
}


HASH_BOUND_DEPENDENCIES = (
    CONTRACT_REL,
    G5_EVIDENCE_REL,
    G6A_EVIDENCE_REL,
    "02_AI/Models/frozen_c04_shadow_observer.py",
    "02_AI/Models/frozen_c04_forward_outcome_ledger.py",
    G6B_RUNNER_REL,
    G6B_TEST_REL,
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


class G6BEvaluationError(RuntimeError):
    pass


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise G6BEvaluationError(
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

        if (
            value.startswith('"')
            and value.endswith('"')
        ):
            value = value[1:-1]

        paths.add(
            value.replace(
                "\\",
                "/",
            )
        )

    return paths


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
        raise G6BEvaluationError(
            f"JSON_ROOT_NOT_OBJECT:{relative}"
        )

    return value


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


def verify_protocol_authority() -> dict[str, Any]:

    g6a = load_json(
        G6A_EVIDENCE_REL
    )

    require(
        g6a.get(
            "status"
        )
        ==
        "PASS",
        "G6A_STATUS_NOT_PASS",
    )

    evaluation_contract = g6a.get(
        "evaluation_contract"
    )

    if not isinstance(
        evaluation_contract,
        dict,
    ):
        raise G6BEvaluationError(
            "G6A_CONTRACT_EVIDENCE_MISSING"
        )

    frozen_fp = str(
        evaluation_contract.get(
            "contract_fingerprint_sha256",
            "",
        )
    )

    require(
        frozen_fp
        ==
        EXPECTED_CONTRACT_FINGERPRINT,
        (
            "G6A_CONTRACT_FINGERPRINT_MISMATCH:"
            f"{frozen_fp}"
        ),
    )

    current_fp = (
        _contract.contract_fingerprint_sha256()
    )

    require(
        current_fp
        ==
        EXPECTED_CONTRACT_FINGERPRINT,
        (
            "CURRENT_CONTRACT_FINGERPRINT_MISMATCH:"
            f"{current_fp}"
        ),
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
        "contract_id": (
            _contract.CONTRACT_ID
        ),
        "contract_fingerprint_sha256": (
            current_fp
        ),
        "evaluation_cadence": (
            _contract.EVALUATION_CADENCE
        ),
    }


def verify_exact_g5_ledgers() -> dict[str, Any]:

    g5 = load_json(
        G5_EVIDENCE_REL
    )

    require(
        g5.get(
            "status"
        )
        ==
        "PASS",
        "G5_STATUS_NOT_PASS",
    )

    expected = g5.get(
        "runtime_ledger_raw_sha256"
    )

    if not isinstance(
        expected,
        dict,
    ):
        raise G6BEvaluationError(
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
        "runtime_ledger_raw_sha256": (
            actual
        ),
        "exact_g5_baseline": True,
    }


def safe_divide(
    numerator: float,
    denominator: float,
) -> float:

    if denominator == 0.0:
        return float(
            _contract.ZERO_DIVISION_POLICY
        )

    return (
        numerator
        /
        denominator
    )


def week_start_utc(
    timestamp_text: str,
) -> str:

    parsed = dt.datetime.fromisoformat(
        timestamp_text.replace(
            "Z",
            "+00:00",
        )
    )

    require(
        parsed.tzinfo is not None,
        "DECISION_TIME_NOT_TIMEZONE_AWARE",
    )

    utc = parsed.astimezone(
        dt.timezone.utc
    )

    start = (
        utc
        -
        dt.timedelta(
            days=utc.weekday(),
            hours=utc.hour,
            minutes=utc.minute,
            seconds=utc.second,
            microseconds=utc.microsecond,
        )
    )

    return (
        start.isoformat()
        .replace(
            "+00:00",
            "Z",
        )
    )


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


def load_baseline_rows() -> list[dict[str, Any]]:

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

    observation_by_id = {
        record.logical_observation_id: record
        for record in observation_records
    }

    require(
        len(outcome_records)
        ==
        EXPECTED_BASELINE_SAMPLE_COUNT,
        (
            "OUTCOME_COUNT_MISMATCH:"
            f"{len(outcome_records)}"
        ),
    )

    rows: list[
        dict[str, Any]
    ] = []

    seen_ids: set[str] = set()

    for outcome in outcome_records:

        logical_id = (
            outcome.logical_observation_id
        )

        require(
            logical_id
            not in seen_ids,
            (
                "DUPLICATE_OUTCOME_LOGICAL_ID:"
                f"{logical_id}"
            ),
        )

        seen_ids.add(
            logical_id
        )

        require(
            logical_id
            in observation_by_id,
            (
                "OUTCOME_OBSERVATION_MISSING:"
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
                "OUTCOME_LINKED_TO_INELIGIBLE_OBSERVATION:"
                f"{logical_id}"
            ),
        )

        require(
            tuple(
                observation.class_order
            )
            ==
            tuple(
                _contract.CLASS_ORDER
            ),
            (
                "OBSERVATION_CLASS_ORDER_MISMATCH:"
                f"{logical_id}"
            ),
        )

        require(
            outcome.source_observation_fingerprint
            ==
            observation.semantic_record_fingerprint,
            (
                "OUTCOME_SOURCE_OBSERVATION_FINGERPRINT_MISMATCH:"
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

        probabilities = (
            float(
                observation.probability_short
            ),
            float(
                observation.probability_no_trade
            ),
            float(
                observation.probability_long
            ),
        )

        for value in probabilities:

            require(
                math.isfinite(
                    value
                ),
                (
                    "NON_FINITE_PROBABILITY:"
                    f"{logical_id}"
                ),
            )

            require(
                0.0
                <=
                value
                <=
                1.0,
                (
                    "PROBABILITY_OUT_OF_RANGE:"
                    f"{logical_id}:{value}"
                ),
            )

        probability_sum = sum(
            probabilities
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
                f"{logical_id}:{probability_sum}"
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
            in
            _contract.CLASS_ORDER,
            (
                "INVALID_PREDICTED_CLASS:"
                f"{logical_id}:{predicted_class}"
            ),
        )

        require(
            outcome_class
            in
            _contract.CLASS_ORDER,
            (
                "INVALID_OUTCOME_CLASS:"
                f"{logical_id}:{outcome_class}"
            ),
        )

        rows.append(
            {
                "logical_observation_id": (
                    logical_id
                ),
                "decision_time_utc": (
                    observation.decision_time_utc
                ),
                "predicted_class": (
                    predicted_class
                ),
                "outcome_class": (
                    outcome_class
                ),
                "probabilities": (
                    probabilities
                ),
            }
        )

    require(
        len(rows)
        ==
        EXPECTED_BASELINE_SAMPLE_COUNT,
        (
            "BASELINE_ROW_COUNT_MISMATCH:"
            f"{len(rows)}"
        ),
    )

    rows.sort(
        key=lambda row: (
            row[
                "decision_time_utc"
            ]
        )
    )

    return rows


def evaluate_rows(
    rows: list[
        dict[str, Any]
    ],
) -> dict[str, Any]:

    require(
        bool(rows),
        "EMPTY_EVALUATION_COHORT",
    )

    classes = list(
        _contract.CLASS_ORDER
    )

    labels = {
        int(k): str(v)
        for k, v
        in _contract.CLASS_LABELS.items()
    }

    confusion: dict[
        int,
        dict[int, int],
    ] = {
        true_class: {
            predicted_class: 0
            for predicted_class
            in classes
        }
        for true_class
        in classes
    }

    prediction_counts = {
        value: 0
        for value in classes
    }

    outcome_counts = {
        value: 0
        for value in classes
    }

    correct = 0
    brier_total = 0.0
    log_loss_total = 0.0

    epsilon = float(
        _contract.LOG_LOSS_EPSILON
    )

    class_to_index = {
        value: index
        for index, value
        in enumerate(
            classes
        )
    }

    for row in rows:

        predicted = int(
            row[
                "predicted_class"
            ]
        )

        actual = int(
            row[
                "outcome_class"
            ]
        )

        probabilities = [
            float(value)
            for value
            in row[
                "probabilities"
            ]
        ]

        confusion[
            actual
        ][
            predicted
        ] += 1

        prediction_counts[
            predicted
        ] += 1

        outcome_counts[
            actual
        ] += 1

        if predicted == actual:
            correct += 1

        true_index = (
            class_to_index[
                actual
            ]
        )

        sample_brier = 0.0

        for index, probability in enumerate(
            probabilities
        ):

            target = (
                1.0
                if index == true_index
                else 0.0
            )

            sample_brier += (
                probability
                -
                target
            ) ** 2

        brier_total += (
            sample_brier
        )

        clipped = [
            min(
                max(
                    probability,
                    epsilon,
                ),
                1.0
                -
                epsilon,
            )
            for probability
            in probabilities
        ]

        clipped_sum = sum(
            clipped
        )

        require(
            clipped_sum > 0.0,
            "CLIPPED_PROBABILITY_SUM_NON_POSITIVE",
        )

        normalized = [
            value
            /
            clipped_sum
            for value
            in clipped
        ]

        true_probability = (
            normalized[
                true_index
            ]
        )

        log_loss_total += (
            -math.log(
                true_probability
            )
        )

    sample_count = len(
        rows
    )

    per_class: dict[
        str,
        dict[str, Any],
    ] = {}

    recalls: list[float] = []
    f1_values: list[float] = []

    for class_value in classes:

        tp = float(
            confusion[
                class_value
            ][
                class_value
            ]
        )

        fp = float(
            sum(
                confusion[
                    true_value
                ][
                    class_value
                ]
                for true_value
                in classes
                if true_value
                !=
                class_value
            )
        )

        fn = float(
            sum(
                confusion[
                    class_value
                ][
                    predicted_value
                ]
                for predicted_value
                in classes
                if predicted_value
                !=
                class_value
            )
        )

        precision = safe_divide(
            tp,
            tp + fp,
        )

        recall = safe_divide(
            tp,
            tp + fn,
        )

        f1 = safe_divide(
            2.0
            *
            precision
            *
            recall,
            precision
            +
            recall,
        )

        recalls.append(
            recall
        )

        f1_values.append(
            f1
        )

        label = labels[
            class_value
        ]

        per_class[
            label
        ] = {
            "class": class_value,
            "tp": int(
                tp
            ),
            "fp": int(
                fp
            ),
            "fn": int(
                fn
            ),
            "precision": (
                precision
            ),
            "recall": (
                recall
            ),
            "f1": (
                f1
            ),
        }

    confusion_named = {
        labels[
            true_value
        ]: {
            labels[
                predicted_value
            ]: confusion[
                true_value
            ][
                predicted_value
            ]
            for predicted_value
            in classes
        }
        for true_value
        in classes
    }

    prediction_distribution = {
        labels[value]: {
            "count": (
                prediction_counts[
                    value
                ]
            ),
            "proportion": (
                prediction_counts[
                    value
                ]
                /
                sample_count
            ),
        }
        for value
        in classes
    }

    outcome_distribution = {
        labels[value]: {
            "count": (
                outcome_counts[
                    value
                ]
            ),
            "proportion": (
                outcome_counts[
                    value
                ]
                /
                sample_count
            ),
        }
        for value
        in classes
    }

    return {
        "sample_count": (
            sample_count
        ),
        "coverage_period": {
            "first_decision_time_utc": (
                rows[0][
                    "decision_time_utc"
                ]
            ),
            "last_decision_time_utc": (
                rows[-1][
                    "decision_time_utc"
                ]
            ),
        },
        "exact_class_accuracy": (
            correct
            /
            sample_count
        ),
        "confusion_matrix": (
            confusion_named
        ),
        "per_class": (
            per_class
        ),
        "macro_f1": (
            sum(
                f1_values
            )
            /
            len(
                f1_values
            )
        ),
        "balanced_accuracy": (
            sum(
                recalls
            )
            /
            len(
                recalls
            )
        ),
        "prediction_distribution": (
            prediction_distribution
        ),
        "outcome_distribution": (
            outcome_distribution
        ),
        "multiclass_brier_score": (
            brier_total
            /
            sample_count
        ),
        "multiclass_log_loss": (
            log_loss_total
            /
            sample_count
        ),
    }


def evaluate_weekly_cohorts(
    rows: list[
        dict[str, Any]
    ],
) -> list[dict[str, Any]]:

    groups: dict[
        str,
        list[dict[str, Any]],
    ] = {}

    for row in rows:

        week = week_start_utc(
            str(
                row[
                    "decision_time_utc"
                ]
            )
        )

        groups.setdefault(
            week,
            [],
        ).append(
            row
        )

    result: list[
        dict[str, Any]
    ] = []

    for week in sorted(
        groups
    ):

        cohort_rows = groups[
            week
        ]

        result.append(
            {
                "week_start_utc": (
                    week
                ),
                "metrics": (
                    evaluate_rows(
                        cohort_rows
                    )
                ),
            }
        )

    return result


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

    protocol = (
        verify_protocol_authority()
    )

    baseline = (
        verify_exact_g5_ledgers()
    )

    rows = (
        load_baseline_rows()
    )

    cumulative_metrics = (
        evaluate_rows(
            rows
        )
    )

    weekly_cohorts = (
        evaluate_weekly_cohorts(
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
        "RUNTIME_LEDGER_CHANGED_DURING_EVALUATION",
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
        "protocol_authority": (
            protocol
        ),
        "baseline_authority": (
            baseline
        ),
        "evaluation_scope": (
            "EXACT_G5_FROZEN_30_MATURED_FORWARD_OUTCOMES"
        ),
        "cumulative_metrics": (
            cumulative_metrics
        ),
        "weekly_cohorts": (
            weekly_cohorts
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
        "performance_calculated": True,
        "performance_interpreted_for_promotion": False,
        "pass_fail_threshold_defined": False,
        "production_promotion_decision_authorized": False,
        "pnl_evaluated": False,
        "retraining_performed": False,
        "refitting_performed": False,
        "calibration_performed": False,
        "model_reselection_performed": False,
        "threshold_tuning_performed": False,
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
            "GATE_15D_C_B2D_G6_B_STATUS=BLOCKED"
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
            "PNL_EVALUATED=false"
        )
        print(
            "LIVE_AUTHORIZED=false"
        )
        print(
            "EXECUTION_AUTHORIZED=false"
        )

        return 2

    metrics = evidence[
        "cumulative_metrics"
    ]

    print(
        "GATE_15D_C_B2D_G6_B_STATUS=PASS"
    )
    print(
        "BASE_AUTHORITY_COMMIT="
        + evidence[
            "base_authority_commit"
        ]
    )
    print(
        "EVALUATION_SCOPE=EXACT_G5_FROZEN_30_MATURED_FORWARD_OUTCOMES"
    )
    print(
        "SAMPLE_COUNT="
        + str(
            metrics[
                "sample_count"
            ]
        )
    )
    print(
        "EXACT_CLASS_ACCURACY="
        + format(
            float(
                metrics[
                    "exact_class_accuracy"
                ]
            ),
            ".12f",
        )
    )
    print(
        "MACRO_F1="
        + format(
            float(
                metrics[
                    "macro_f1"
                ]
            ),
            ".12f",
        )
    )
    print(
        "BALANCED_ACCURACY="
        + format(
            float(
                metrics[
                    "balanced_accuracy"
                ]
            ),
            ".12f",
        )
    )
    print(
        "MULTICLASS_BRIER_SCORE="
        + format(
            float(
                metrics[
                    "multiclass_brier_score"
                ]
            ),
            ".12f",
        )
    )
    print(
        "MULTICLASS_LOG_LOSS="
        + format(
            float(
                metrics[
                    "multiclass_log_loss"
                ]
            ),
            ".12f",
        )
    )
    print(
        "WEEKLY_COHORT_COUNT="
        + str(
            len(
                evidence[
                    "weekly_cohorts"
                ]
            )
        )
    )
    print(
        "PERFORMANCE_CALCULATED=true"
    )
    print(
        "PERFORMANCE_INTERPRETED_FOR_PROMOTION=false"
    )
    print(
        "PASS_FAIL_THRESHOLD_DEFINED=false"
    )
    print(
        "PNL_EVALUATED=false"
    )
    print(
        "RETRAINING_PERFORMED=false"
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