from __future__ import annotations

import hashlib
import json
import sys

from collections.abc import Mapping
from pathlib import Path
from typing import Any


ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_331_TRAIN_MODEL_CANDIDATE_REGISTRY_DESIGN_V1"
)

CANDIDATE_REGISTRY_VERSION = (
    "XAUUSD_PORTABLE_331_TRAIN_MODEL_CANDIDATE_REGISTRY_V1"
)


RESEARCH_PROTOCOL_JSON = (
    ROOT_DIR
    /
    "xauusd_portable_331_train_model_research_protocol_design.json"
)


EXPECTED_RESEARCH_PROTOCOL_ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_331_TRAIN_MODEL_RESEARCH_PROTOCOL_DESIGN_V1"
)

EXPECTED_RESEARCH_PROTOCOL_VERSION = (
    "XAUUSD_PORTABLE_331_TRAIN_MODEL_RESEARCH_PROTOCOL_V1"
)

EXPECTED_RESEARCH_PROTOCOL_FINGERPRINT_SHA256 = (
    "69e51e1b249b9da68cbf6f6778a8ae10f9f33f7082a07e5073a1ba731fa1640d"
)

EXPECTED_RESEARCH_PROTOCOL_STATUS = (
    "XAUUSD_PORTABLE_331_TRAIN_MODEL_RESEARCH_PROTOCOL_DESIGN_CONFIRMED"
)


EXPECTED_DATASET_ID = (
    "portable_cff75b0686383a3ab6f8352b"
)

EXPECTED_DATASET_SHA256 = (
    "cff75b0686383a3ab6f8352bfcdcd55308b99b7a4c6edbf7d2e7215f6f33dd07"
)

EXPECTED_MANIFEST_SHA256 = (
    "1b8e3599b227c9cbbc6b12f8ab0e275ca4deb4a65839fb626ca90720d59512dc"
)


EXPECTED_TRAIN_INPUT_FINGERPRINT_SHA256 = (
    "9ffb72759499cfc202e88cfdbd61b42cee5b5c7cbb7db5870470453caa5ed2c5"
)

EXPECTED_TRAIN_TARGET_FINGERPRINT_SHA256 = (
    "bc063a790e70cdbc931b2170ccfef883634b40ee7336a529a32bda0eaf0babe3"
)


EXPECTED_TRAIN_ROWS = 69966
EXPECTED_FEATURE_COUNT = 331
EXPECTED_FOLD_COUNT = 4
EXPECTED_PURGE_ROWS = 12

RANDOM_SEED = 271828


CLASS_ORDER = (
    -1,
    0,
    1,
)

CLASS_NAMES = (
    "SHORT",
    "NO_TRADE",
    "LONG",
)


def _require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise RuntimeError(
            reason
        )


def _mapping(
    document: Mapping[str, Any],
    key: str,
) -> Mapping[str, Any]:

    value = document.get(
        key
    )

    if not isinstance(
        value,
        Mapping,
    ):
        raise RuntimeError(
            (
                "EXPECTED_MAPPING_MISSING:"
                f"{key}"
            )
        )

    return value


def _required_int(
    mapping: Mapping[str, Any],
    key: str,
) -> int:

    if key not in mapping:
        raise RuntimeError(
            (
                "REQUIRED_INTEGER_MISSING:"
                f"{key}"
            )
        )

    value = mapping[
        key
    ]

    if value is None:
        raise RuntimeError(
            (
                "REQUIRED_INTEGER_NONE:"
                f"{key}"
            )
        )

    if isinstance(
        value,
        bool,
    ):
        raise RuntimeError(
            (
                "REQUIRED_INTEGER_BOOLEAN:"
                f"{key}"
            )
        )

    try:

        result = int(
            value
        )

    except (
        TypeError,
        ValueError,
    ) as exc:

        raise RuntimeError(
            (
                "REQUIRED_INTEGER_INVALID:"
                f"{key}:"
                f"{value}"
            )
        ) from exc

    return result


def _canonical_json_sha256(
    value: Any,
) -> str:

    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(
            ",",
            ":",
        ),
        ensure_ascii=True,
        allow_nan=False,
    ).encode(
        "utf-8"
    )

    return hashlib.sha256(
        payload
    ).hexdigest()


def _decode_text_bytes(
    raw: bytes,
    *,
    source_name: str,
) -> str:

    if raw.startswith(
        b"\xef\xbb\xbf"
    ):

        try:

            return raw.decode(
                "utf-8-sig"
            )

        except UnicodeDecodeError as exc:

            raise RuntimeError(
                (
                    "UTF8_BOM_TEXT_DECODE_FAILED:"
                    f"{source_name}"
                )
            ) from exc

    if (
        raw.startswith(
            b"\xff\xfe"
        )
        or
        raw.startswith(
            b"\xfe\xff"
        )
    ):

        try:

            return raw.decode(
                "utf-16"
            )

        except UnicodeDecodeError as exc:

            raise RuntimeError(
                (
                    "UTF16_TEXT_DECODE_FAILED:"
                    f"{source_name}"
                )
            ) from exc

    try:

        return raw.decode(
            "utf-8"
        )

    except UnicodeDecodeError as exc:

        raise RuntimeError(
            (
                "TEXT_ENCODING_NOT_SUPPORTED:"
                f"{source_name}"
            )
        ) from exc


def _read_text_auto(
    path: Path,
) -> str:

    _require(
        path.is_file(),
        (
            "TEXT_FILE_NOT_FOUND:"
            f"{path.name}"
        ),
    )

    try:

        raw = path.read_bytes()

    except OSError as exc:

        raise RuntimeError(
            (
                "TEXT_FILE_READ_FAILED:"
                f"{path.name}"
            )
        ) from exc

    return _decode_text_bytes(
        raw,
        source_name=(
            path.name
        ),
    )


def _load_json_object(
    path: Path,
) -> dict[str, Any]:

    text = (
        _read_text_auto(
            path
        )
    )

    try:

        document_raw: Any = json.loads(
            text
        )

    except json.JSONDecodeError as exc:

        raise RuntimeError(
            (
                "JSON_PARSE_FAILED:"
                f"{path.name}:"
                f"line={exc.lineno}:"
                f"column={exc.colno}"
            )
        ) from exc

    if not isinstance(
        document_raw,
        dict,
    ):
        raise RuntimeError(
            (
                "JSON_ROOT_NOT_OBJECT:"
                f"{path.name}"
            )
        )

    return document_raw


def _validate_research_protocol(
) -> Mapping[str, Any]:

    document = (
        _load_json_object(
            RESEARCH_PROTOCOL_JSON
        )
    )

    _require(
        bool(
            document.get(
                "valid",
                False,
            )
        ),
        "RESEARCH_PROTOCOL_INVALID",
    )

    _require(
        str(
            document.get(
                "analysis_version",
                "",
            )
        )
        ==
        EXPECTED_RESEARCH_PROTOCOL_ANALYSIS_VERSION,
        "RESEARCH_PROTOCOL_ANALYSIS_VERSION_MISMATCH",
    )

    fingerprint = (
        _mapping(
            document,
            "contract_fingerprint",
        )
    )

    _require(
        str(
            fingerprint.get(
                "sha256",
                "",
            )
        )
        ==
        EXPECTED_RESEARCH_PROTOCOL_FINGERPRINT_SHA256,
        "RESEARCH_PROTOCOL_FINGERPRINT_MISMATCH",
    )

    decision = (
        _mapping(
            document,
            "decision",
        )
    )

    _require(
        str(
            decision.get(
                "status",
                "",
            )
        )
        ==
        EXPECTED_RESEARCH_PROTOCOL_STATUS,
        "RESEARCH_PROTOCOL_STATUS_MISMATCH",
    )

    _require(
        str(
            decision.get(
                "research_protocol_version",
                "",
            )
        )
        ==
        EXPECTED_RESEARCH_PROTOCOL_VERSION,
        "RESEARCH_PROTOCOL_VERSION_MISMATCH",
    )

    _require(
        str(
            decision.get(
                "research_protocol_fingerprint_sha256",
                "",
            )
        )
        ==
        EXPECTED_RESEARCH_PROTOCOL_FINGERPRINT_SHA256,
        "DECISION_RESEARCH_PROTOCOL_FINGERPRINT_MISMATCH",
    )

    _require(
        _required_int(
            decision,
            "train_rows",
        )
        ==
        EXPECTED_TRAIN_ROWS,
        "TRAIN_ROW_COUNT_MISMATCH",
    )

    _require(
        _required_int(
            decision,
            "feature_count",
        )
        ==
        EXPECTED_FEATURE_COUNT,
        "FEATURE_COUNT_MISMATCH",
    )

    _require(
        _required_int(
            decision,
            "walk_forward_fold_count",
        )
        ==
        EXPECTED_FOLD_COUNT,
        "WALK_FORWARD_FOLD_COUNT_MISMATCH",
    )

    _require(
        _required_int(
            decision,
            "purge_rows",
        )
        ==
        EXPECTED_PURGE_ROWS,
        "PURGE_ROW_COUNT_MISMATCH",
    )

    _require(
        bool(
            decision.get(
                "candidate_registry_design_authorized_next",
                False,
            )
        ),
        "CANDIDATE_REGISTRY_DESIGN_NOT_AUTHORIZED",
    )

    _require(
        not bool(
            decision.get(
                "candidate_training_authorized",
                True,
            )
        ),
        "CANDIDATE_TRAINING_ALREADY_AUTHORIZED",
    )

    _require(
        not bool(
            decision.get(
                "validation_access_authorized",
                True,
            )
        ),
        "VALIDATION_ACCESS_ALREADY_AUTHORIZED",
    )

    _require(
        not bool(
            decision.get(
                "test_access_authorized",
                True,
            )
        ),
        "TEST_ACCESS_ALREADY_AUTHORIZED",
    )

    _require(
        str(
            decision.get(
                "next_action",
                "",
            )
        )
        ==
        (
            "DESIGN_FIXED_FINITE_TRAIN_ONLY_MODEL_CANDIDATE_"
            "REGISTRY_BEFORE_ANY_MODEL_FIT"
        ),
        "RESEARCH_PROTOCOL_NEXT_ACTION_MISMATCH",
    )

    contract = (
        _mapping(
            document,
            "contract",
        )
    )

    artifact = (
        _mapping(
            contract,
            "artifact_identity",
        )
    )

    _require(
        str(
            artifact.get(
                "dataset_id",
                "",
            )
        )
        ==
        EXPECTED_DATASET_ID,
        "DATASET_ID_MISMATCH",
    )

    _require(
        str(
            artifact.get(
                "dataset_sha256",
                "",
            )
        )
        ==
        EXPECTED_DATASET_SHA256,
        "DATASET_SHA256_MISMATCH",
    )

    _require(
        str(
            artifact.get(
                "manifest_sha256",
                "",
            )
        )
        ==
        EXPECTED_MANIFEST_SHA256,
        "MANIFEST_SHA256_MISMATCH",
    )

    frozen_train = (
        _mapping(
            contract,
            "frozen_train_data",
        )
    )

    _require(
        str(
            frozen_train.get(
                "train_input_fingerprint_sha256",
                "",
            )
        )
        ==
        EXPECTED_TRAIN_INPUT_FINGERPRINT_SHA256,
        "TRAIN_INPUT_FINGERPRINT_MISMATCH",
    )

    _require(
        str(
            frozen_train.get(
                "train_target_fingerprint_sha256",
                "",
            )
        )
        ==
        EXPECTED_TRAIN_TARGET_FINGERPRINT_SHA256,
        "TRAIN_TARGET_FINGERPRINT_MISMATCH",
    )

    holdout = (
        _mapping(
            contract,
            "holdout_boundary",
        )
    )

    _require(
        not bool(
            holdout.get(
                "validation_feature_access_authorized",
                True,
            )
        ),
        "VALIDATION_FEATURE_ACCESS_NOT_BLOCKED",
    )

    _require(
        not bool(
            holdout.get(
                "validation_target_access_authorized",
                True,
            )
        ),
        "VALIDATION_TARGET_ACCESS_NOT_BLOCKED",
    )

    _require(
        not bool(
            holdout.get(
                "test_feature_access_authorized",
                True,
            )
        ),
        "TEST_FEATURE_ACCESS_NOT_BLOCKED",
    )

    _require(
        not bool(
            holdout.get(
                "test_target_access_authorized",
                True,
            )
        ),
        "TEST_TARGET_ACCESS_NOT_BLOCKED",
    )

    return document


def _candidate_registry(
) -> list[dict[str, Any]]:

    return [
        {
            "candidate_id": (
                "C01_FLAT_LOGREG_BALANCED_C005"
            ),
            "architecture": (
                "FLAT_3CLASS"
            ),
            "family": (
                "LOGISTIC_REGRESSION"
            ),
            "probability_class_order": list(
                CLASS_ORDER
            ),
            "preprocessing": {
                "standard_scaler": (
                    True
                ),
                "scaler_fit_scope": (
                    "FOLD_TRAIN_ONLY"
                ),
            },
            "estimator": {
                "implementation": (
                    "sklearn.linear_model.LogisticRegression"
                ),
                "C": (
                    0.05
                ),
                "class_weight": (
                    "balanced"
                ),
                "solver": (
                    "lbfgs"
                ),
                "max_iter": (
                    2000
                ),
                "tol": (
                    0.0001
                ),
            },
        },
        {
            "candidate_id": (
                "C02_FLAT_LOGREG_BALANCED_C020"
            ),
            "architecture": (
                "FLAT_3CLASS"
            ),
            "family": (
                "LOGISTIC_REGRESSION"
            ),
            "probability_class_order": list(
                CLASS_ORDER
            ),
            "preprocessing": {
                "standard_scaler": (
                    True
                ),
                "scaler_fit_scope": (
                    "FOLD_TRAIN_ONLY"
                ),
            },
            "estimator": {
                "implementation": (
                    "sklearn.linear_model.LogisticRegression"
                ),
                "C": (
                    0.20
                ),
                "class_weight": (
                    "balanced"
                ),
                "solver": (
                    "lbfgs"
                ),
                "max_iter": (
                    2000
                ),
                "tol": (
                    0.0001
                ),
            },
        },
        {
            "candidate_id": (
                "C03_FLAT_HGB_SHALLOW"
            ),
            "architecture": (
                "FLAT_3CLASS"
            ),
            "family": (
                "HIST_GRADIENT_BOOSTING"
            ),
            "probability_class_order": list(
                CLASS_ORDER
            ),
            "preprocessing": {
                "standard_scaler": (
                    False
                ),
            },
            "estimator": {
                "implementation": (
                    "sklearn.ensemble.HistGradientBoostingClassifier"
                ),
                "loss": (
                    "log_loss"
                ),
                "learning_rate": (
                    0.03
                ),
                "max_iter": (
                    220
                ),
                "max_leaf_nodes": (
                    7
                ),
                "min_samples_leaf": (
                    80
                ),
                "l2_regularization": (
                    1.0
                ),
                "early_stopping": (
                    False
                ),
                "random_state": (
                    RANDOM_SEED
                ),
            },
            "fold_local_class_balance": (
                "INVERSE_FREQUENCY_SAMPLE_WEIGHT"
            ),
        },
        {
            "candidate_id": (
                "C04_FLAT_EXTRA_TREES_CONSTRAINED"
            ),
            "architecture": (
                "FLAT_3CLASS"
            ),
            "family": (
                "EXTRA_TREES"
            ),
            "probability_class_order": list(
                CLASS_ORDER
            ),
            "preprocessing": {
                "standard_scaler": (
                    False
                ),
            },
            "estimator": {
                "implementation": (
                    "sklearn.ensemble.ExtraTreesClassifier"
                ),
                "n_estimators": (
                    500
                ),
                "max_depth": (
                    10
                ),
                "min_samples_leaf": (
                    25
                ),
                "max_features": (
                    0.35
                ),
                "class_weight": (
                    "balanced"
                ),
                "bootstrap": (
                    False
                ),
                "random_state": (
                    RANDOM_SEED
                ),
                "n_jobs": (
                    -1
                ),
            },
        },
        {
            "candidate_id": (
                "C05_HIER_LOGREG_REGULARIZED"
            ),
            "architecture": (
                "HIERARCHICAL_TRADEABILITY_DIRECTION"
            ),
            "family": (
                "LOGISTIC_REGRESSION_HIERARCHICAL"
            ),
            "probability_class_order": list(
                CLASS_ORDER
            ),
            "stage_a": {
                "target": (
                    "target_tradeable"
                ),
                "preprocessing": {
                    "standard_scaler": (
                        True
                    ),
                    "scaler_fit_scope": (
                        "FOLD_TRAIN_ONLY"
                    ),
                },
                "estimator": {
                    "implementation": (
                        "sklearn.linear_model.LogisticRegression"
                    ),
                    "C": (
                        0.10
                    ),
                    "class_weight": (
                        "balanced"
                    ),
                    "solver": (
                        "lbfgs"
                    ),
                    "max_iter": (
                        2000
                    ),
                    "tol": (
                        0.0001
                    ),
                },
            },
            "stage_b": {
                "fit_scope": (
                    "TRUE_TRADEABLE_FOLD_TRAIN_ROWS_ONLY"
                ),
                "target": (
                    "SHORT_VS_LONG_FROM_TARGET_CLASS"
                ),
                "preprocessing": {
                    "standard_scaler": (
                        True
                    ),
                    "scaler_fit_scope": (
                        "STAGE_B_FOLD_TRAIN_ONLY"
                    ),
                },
                "estimator": {
                    "implementation": (
                        "sklearn.linear_model.LogisticRegression"
                    ),
                    "C": (
                        0.05
                    ),
                    "class_weight": (
                        "balanced"
                    ),
                    "solver": (
                        "lbfgs"
                    ),
                    "max_iter": (
                        2000
                    ),
                    "tol": (
                        0.0001
                    ),
                },
            },
            "probability_combination": {
                "SHORT": (
                    "P_TRADEABLE * P_SHORT_GIVEN_TRADEABLE"
                ),
                "NO_TRADE": (
                    "1 - P_TRADEABLE"
                ),
                "LONG": (
                    "P_TRADEABLE * P_LONG_GIVEN_TRADEABLE"
                ),
            },
        },
        {
            "candidate_id": (
                "C06_HIER_HGB_LOGREG_CONSTRAINED"
            ),
            "architecture": (
                "HIERARCHICAL_TRADEABILITY_DIRECTION"
            ),
            "family": (
                "HGB_STAGE_A_LOGREG_STAGE_B"
            ),
            "probability_class_order": list(
                CLASS_ORDER
            ),
            "stage_a": {
                "target": (
                    "target_tradeable"
                ),
                "preprocessing": {
                    "standard_scaler": (
                        False
                    ),
                },
                "estimator": {
                    "implementation": (
                        "sklearn.ensemble.HistGradientBoostingClassifier"
                    ),
                    "loss": (
                        "log_loss"
                    ),
                    "learning_rate": (
                        0.03
                    ),
                    "max_iter": (
                        180
                    ),
                    "max_leaf_nodes": (
                        7
                    ),
                    "min_samples_leaf": (
                        100
                    ),
                    "l2_regularization": (
                        2.0
                    ),
                    "early_stopping": (
                        False
                    ),
                    "random_state": (
                        RANDOM_SEED
                    ),
                },
                "fold_local_class_balance": (
                    "INVERSE_FREQUENCY_SAMPLE_WEIGHT"
                ),
            },
            "stage_b": {
                "fit_scope": (
                    "TRUE_TRADEABLE_FOLD_TRAIN_ROWS_ONLY"
                ),
                "target": (
                    "SHORT_VS_LONG_FROM_TARGET_CLASS"
                ),
                "preprocessing": {
                    "standard_scaler": (
                        True
                    ),
                    "scaler_fit_scope": (
                        "STAGE_B_FOLD_TRAIN_ONLY"
                    ),
                },
                "estimator": {
                    "implementation": (
                        "sklearn.linear_model.LogisticRegression"
                    ),
                    "C": (
                        0.05
                    ),
                    "class_weight": (
                        "balanced"
                    ),
                    "solver": (
                        "lbfgs"
                    ),
                    "max_iter": (
                        2000
                    ),
                    "tol": (
                        0.0001
                    ),
                },
            },
            "probability_combination": {
                "SHORT": (
                    "P_TRADEABLE * P_SHORT_GIVEN_TRADEABLE"
                ),
                "NO_TRADE": (
                    "1 - P_TRADEABLE"
                ),
                "LONG": (
                    "P_TRADEABLE * P_LONG_GIVEN_TRADEABLE"
                ),
            },
        },
    ]


def _validate_candidate_registry(
    candidates: list[dict[str, Any]],
) -> None:

    _require(
        len(
            candidates
        )
        ==
        6,
        (
            "CANDIDATE_COUNT_MISMATCH:"
            f"{len(candidates)}"
        ),
    )

    candidate_ids: list[str] = []

    for candidate in (
        candidates
    ):

        candidate_id_raw = (
            candidate.get(
                "candidate_id"
            )
        )

        if not isinstance(
            candidate_id_raw,
            str,
        ):
            raise RuntimeError(
                "CANDIDATE_ID_NOT_STRING"
            )

        candidate_id = (
            candidate_id_raw.strip()
        )

        _require(
            bool(
                candidate_id
            ),
            "CANDIDATE_ID_EMPTY",
        )

        candidate_ids.append(
            candidate_id
        )

        architecture_raw = (
            candidate.get(
                "architecture"
            )
        )

        if not isinstance(
            architecture_raw,
            str,
        ):
            raise RuntimeError(
                (
                    "CANDIDATE_ARCHITECTURE_NOT_STRING:"
                    f"{candidate_id}"
                )
            )

        architecture = (
            architecture_raw.strip()
        )

        _require(
            architecture
            in
            {
                "FLAT_3CLASS",
                "HIERARCHICAL_TRADEABILITY_DIRECTION",
            },
            (
                "CANDIDATE_ARCHITECTURE_INVALID:"
                f"{candidate_id}:"
                f"{architecture}"
            ),
        )

        class_order_raw = (
            candidate.get(
                "probability_class_order"
            )
        )

        if not isinstance(
            class_order_raw,
            list,
        ):
            raise RuntimeError(
                (
                    "CANDIDATE_CLASS_ORDER_NOT_LIST:"
                    f"{candidate_id}"
                )
            )

        class_order: list[int] = []

        for value in (
            class_order_raw
        ):

            if isinstance(
                value,
                bool,
            ):
                raise RuntimeError(
                    (
                        "CANDIDATE_CLASS_ORDER_BOOLEAN:"
                        f"{candidate_id}"
                    )
                )

            try:

                normalized = int(
                    value
                )

            except (
                TypeError,
                ValueError,
            ) as exc:

                raise RuntimeError(
                    (
                        "CANDIDATE_CLASS_ORDER_INVALID:"
                        f"{candidate_id}"
                    )
                ) from exc

            class_order.append(
                normalized
            )

        _require(
            tuple(
                class_order
            )
            ==
            CLASS_ORDER,
            (
                "CANDIDATE_CLASS_ORDER_MISMATCH:"
                f"{candidate_id}:"
                f"{class_order}"
            ),
        )

    _require(
        len(
            candidate_ids
        )
        ==
        len(
            set(
                candidate_ids
            )
        ),
        "CANDIDATE_IDS_NOT_UNIQUE",
    )


def _build_contract(
    *,
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:

    return {
        "contract_version": (
            CANDIDATE_REGISTRY_VERSION
        ),
        "contract_status": (
            "DESIGN_ONLY_NO_MODEL_FIT"
        ),
        "asset": (
            "XAUUSD"
        ),
        "parent_research_protocol": {
            "version": (
                EXPECTED_RESEARCH_PROTOCOL_VERSION
            ),
            "fingerprint_sha256": (
                EXPECTED_RESEARCH_PROTOCOL_FINGERPRINT_SHA256
            ),
        },
        "frozen_train_identity": {
            "dataset_id": (
                EXPECTED_DATASET_ID
            ),
            "dataset_sha256": (
                EXPECTED_DATASET_SHA256
            ),
            "manifest_sha256": (
                EXPECTED_MANIFEST_SHA256
            ),
            "train_input_fingerprint_sha256": (
                EXPECTED_TRAIN_INPUT_FINGERPRINT_SHA256
            ),
            "train_target_fingerprint_sha256": (
                EXPECTED_TRAIN_TARGET_FINGERPRINT_SHA256
            ),
            "row_count": (
                EXPECTED_TRAIN_ROWS
            ),
            "feature_count": (
                EXPECTED_FEATURE_COUNT
            ),
        },
        "candidate_registry_policy": {
            "candidate_count": (
                len(
                    candidates
                )
            ),
            "finite_registry": (
                True
            ),
            "registry_frozen_before_first_model_fit": (
                True
            ),
            "registry_change_after_first_fit_allowed": (
                False
            ),
            "results_driven_candidate_addition_allowed": (
                False
            ),
            "results_driven_hyperparameter_change_allowed": (
                False
            ),
            "feature_subset_search_allowed": (
                False
            ),
            "all_candidates_use_exact_331_features": (
                True
            ),
            "random_seed": (
                RANDOM_SEED
            ),
        },
        "candidates": (
            candidates
        ),
        "diagnostic_baseline": {
            "selectable_as_winner": (
                False
            ),
            "implementation": (
                "sklearn.dummy.DummyClassifier"
            ),
            "strategy": (
                "prior"
            ),
            "purpose": (
                "NO_SKILL_REFERENCE_ONLY"
            ),
        },
        "prediction_policy": {
            "class_order": list(
                CLASS_ORDER
            ),
            "class_names": list(
                CLASS_NAMES
            ),
            "flat_prediction_rule": (
                "ARGMAX_3CLASS_PROBABILITY"
            ),
            "hierarchical_prediction_rule": (
                "ARGMAX_COMBINED_3CLASS_PROBABILITY"
            ),
            "probability_calibration_allowed": (
                False
            ),
            "decision_threshold_tuning_allowed": (
                False
            ),
            "trade_threshold_tuning_allowed": (
                False
            ),
            "post_hoc_class_bias_allowed": (
                False
            ),
        },
        "fold_training_policy": {
            "walk_forward_fold_count": (
                EXPECTED_FOLD_COUNT
            ),
            "purge_rows": (
                EXPECTED_PURGE_ROWS
            ),
            "chronological_only": (
                True
            ),
            "shuffle_allowed": (
                False
            ),
            "scaler_fit_scope": (
                "FOLD_TRAIN_ONLY"
            ),
            "model_fit_scope": (
                "FOLD_TRAIN_ONLY"
            ),
            "fold_validation_scope": (
                "TRAIN_INTERNAL_WALK_FORWARD_ONLY"
            ),
            "portable_validation_access_allowed": (
                False
            ),
            "portable_test_access_allowed": (
                False
            ),
            "candidate_fit_failure_policy": (
                "FAIL_CANDIDATE_CLOSED"
            ),
            "missing_required_class_policy": (
                "FAIL_CANDIDATE_CLOSED"
            ),
        },
        "eligibility_gate": {
            "all_four_folds_required": (
                True
            ),
            "all_reported_metrics_must_be_finite": (
                True
            ),
            "short_recall_must_be_positive_every_fold": (
                True
            ),
            "long_recall_must_be_positive_every_fold": (
                True
            ),
            "directional_macro_f1_must_be_positive_every_fold": (
                True
            ),
            "minimum_predicted_trade_coverage_each_fold": (
                0.05
            ),
            "maximum_predicted_trade_coverage_each_fold": (
                0.95
            ),
            "if_all_candidates_fail": (
                "NO_WINNER"
            ),
            "eligibility_rules_may_not_be_relaxed_after_results": (
                True
            ),
        },
        "selection_policy": {
            "source": (
                "PARENT_RESEARCH_PROTOCOL"
            ),
            "ranking": [
                {
                    "priority": 1,
                    "metric": (
                        "worst_fold_directional_macro_f1_short_long"
                    ),
                    "direction": (
                        "MAXIMIZE"
                    ),
                },
                {
                    "priority": 2,
                    "metric": (
                        "mean_directional_macro_f1_short_long"
                    ),
                    "direction": (
                        "MAXIMIZE"
                    ),
                },
                {
                    "priority": 3,
                    "metric": (
                        "worst_fold_balanced_accuracy_3class"
                    ),
                    "direction": (
                        "MAXIMIZE"
                    ),
                },
                {
                    "priority": 4,
                    "metric": (
                        "mean_macro_f1_3class"
                    ),
                    "direction": (
                        "MAXIMIZE"
                    ),
                },
                {
                    "priority": 5,
                    "metric": (
                        "std_directional_macro_f1_short_long"
                    ),
                    "direction": (
                        "MINIMIZE"
                    ),
                },
                {
                    "priority": 6,
                    "metric": (
                        "mean_log_loss_3class"
                    ),
                    "direction": (
                        "MINIMIZE"
                    ),
                },
            ],
            "tie_breaking": (
                "LEXICOGRAPHIC_DECLARED_PRIORITY_ORDER"
            ),
            "single_best_fold_selection_allowed": (
                False
            ),
            "pooled_only_selection_allowed": (
                False
            ),
        },
        "anti_overfit_policy": {
            "candidate_count_bounded": (
                True
            ),
            "hyperparameter_grid_search_allowed": (
                False
            ),
            "bayesian_optimization_allowed": (
                False
            ),
            "validation_split_peeking_allowed": (
                False
            ),
            "test_peeking_allowed": (
                False
            ),
            "feature_selection_during_candidate_search_allowed": (
                False
            ),
            "threshold_search_during_candidate_search_allowed": (
                False
            ),
            "candidate_addition_after_results_allowed": (
                False
            ),
        },
        "current_gate_boundary": {
            "model_fit_performed": (
                False
            ),
            "scaler_fit_performed": (
                False
            ),
            "train_values_loaded": (
                False
            ),
            "validation_values_loaded": (
                False
            ),
            "test_values_loaded": (
                False
            ),
            "model_artifacts_written": (
                False
            ),
            "live_authorized": (
                False
            ),
        },
    }


def run_design(
) -> dict[str, Any]:

    _validate_research_protocol()

    candidates = (
        _candidate_registry()
    )

    _validate_candidate_registry(
        candidates
    )

    contract = (
        _build_contract(
            candidates=(
                candidates
            )
        )
    )

    registry_fingerprint = (
        _canonical_json_sha256(
            contract
        )
    )

    candidate_ids = [
        str(
            candidate[
                "candidate_id"
            ]
        )
        for candidate
        in candidates
    ]

    return {
        "valid": True,
        "reason": (
            "OK_XAUUSD_PORTABLE_331_TRAIN_MODEL_CANDIDATE_REGISTRY_DESIGN"
        ),
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "research_scope": (
            "DESIGN_ONLY_FIXED_FINITE_MODEL_CANDIDATE_REGISTRY_"
            "BEFORE_ANY_TRAIN_ONLY_WALK_FORWARD_MODEL_FIT"
        ),
        "contract": (
            contract
        ),
        "registry_fingerprint": {
            "version": (
                "XAUUSD_PORTABLE_331_TRAIN_MODEL_CANDIDATE_"
                "REGISTRY_FINGERPRINT_V1"
            ),
            "canonicalization": (
                "JSON_SORT_KEYS_COMPACT_UTF8_SHA256"
            ),
            "sha256": (
                registry_fingerprint
            ),
        },
        "decision": {
            "status": (
                "XAUUSD_PORTABLE_331_TRAIN_MODEL_CANDIDATE_REGISTRY_DESIGN_CONFIRMED"
            ),
            "reason": (
                "A_FIXED_FINITE_SIX_CANDIDATE_REGISTRY_IS_FROZEN_"
                "BEFORE_ANY_MODEL_FIT_WITH_FLAT_LINEAR_NONLINEAR_"
                "AND_CONSTRAINED_HIERARCHICAL_ARCHITECTURES"
            ),
            "candidate_registry_version": (
                CANDIDATE_REGISTRY_VERSION
            ),
            "candidate_registry_fingerprint_sha256": (
                registry_fingerprint
            ),
            "candidate_count": (
                len(
                    candidates
                )
            ),
            "candidate_ids": (
                candidate_ids
            ),
            "candidate_training_implementation_authorized_next": (
                True
            ),
            "candidate_real_fit_authorized_next": (
                False
            ),
            "final_model_fit_authorized": (
                False
            ),
            "validation_access_authorized": (
                False
            ),
            "test_access_authorized": (
                False
            ),
            "live_authorized": (
                False
            ),
            "next_action": (
                "IMPLEMENT_TRAIN_ONLY_WALK_FORWARD_CANDIDATE_"
                "EVALUATOR_WITH_SYNTHETIC_TESTS_BEFORE_REAL_FIT"
            ),
        },
        "scientific_policy": {
            "research_protocol_evidence_loaded": (
                True
            ),
            "portable_dataset_rows_loaded": (
                False
            ),
            "train_feature_values_loaded": (
                False
            ),
            "train_target_values_loaded": (
                False
            ),
            "validation_feature_values_loaded": (
                False
            ),
            "validation_target_values_loaded": (
                False
            ),
            "test_feature_values_loaded": (
                False
            ),
            "test_target_values_loaded": (
                False
            ),
            "target_distribution_computed": (
                False
            ),
            "metrics_computed": (
                False
            ),
            "scaler_fit": (
                False
            ),
            "model_loaded": (
                False
            ),
            "model_trained": (
                False
            ),
            "model_artifacts_written": (
                False
            ),
            "dataset_written": (
                False
            ),
            "manifest_written": (
                False
            ),
            "feature_contract_changed": (
                False
            ),
            "target_contract_changed": (
                False
            ),
            "mt5_used": (
                False
            ),
            "orders_sent": (
                False
            ),
            "positions_modified": (
                False
            ),
            "risk_engine_modified": (
                False
            ),
            "sizing_modified": (
                False
            ),
            "execution_integration_modified": (
                False
            ),
            "live_authorized": (
                False
            ),
            "filesystem_paths_emitted": (
                False
            ),
        },
        "next_decision_contract": {
            "if_design_confirmed": (
                "IMPLEMENT_TRAIN_ONLY_WALK_FORWARD_CANDIDATE_"
                "EVALUATOR_WITH_SYNTHETIC_TESTS_BEFORE_REAL_FIT"
            ),
            "registry_must_not_change_after_first_candidate_fit": (
                True
            ),
            "candidate_training_implementation_authorized": (
                True
            ),
            "real_candidate_fit_not_authorized_until_evaluator_tests_pass": (
                True
            ),
            "final_model_fit_not_authorized": (
                True
            ),
            "portable_validation_access_remains_blocked": (
                True
            ),
            "portable_test_access_remains_blocked": (
                True
            ),
            "live_authorization_not_changed": (
                True
            ),
        },
    }


def main() -> int:

    try:

        result = (
            run_design()
        )

    except Exception as exc:

        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "XAUUSD_PORTABLE_331_TRAIN_MODEL_"
                        "CANDIDATE_REGISTRY_DESIGN_FAILED"
                    ),
                    "analysis_version": (
                        ANALYSIS_VERSION
                    ),
                    "error_type": (
                        type(
                            exc
                        ).__name__
                    ),
                    "error": (
                        str(
                            exc
                        )
                    ),
                    "train_feature_values_loaded": (
                        False
                    ),
                    "train_target_values_loaded": (
                        False
                    ),
                    "validation_feature_values_loaded": (
                        False
                    ),
                    "validation_target_values_loaded": (
                        False
                    ),
                    "test_feature_values_loaded": (
                        False
                    ),
                    "test_target_values_loaded": (
                        False
                    ),
                    "model_loaded": (
                        False
                    ),
                    "model_trained": (
                        False
                    ),
                    "scaler_fit": (
                        False
                    ),
                    "dataset_written": (
                        False
                    ),
                    "mt5_used": (
                        False
                    ),
                    "orders_sent": (
                        False
                    ),
                    "live_authorized": (
                        False
                    ),
                },
                indent=2,
                sort_keys=True,
                allow_nan=False,
            )
        )

        return 2

    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
    )

    return 0


if __name__ == "__main__":

    raise SystemExit(
        main()
    )