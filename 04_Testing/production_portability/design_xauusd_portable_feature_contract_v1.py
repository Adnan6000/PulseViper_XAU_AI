from __future__ import annotations

import hashlib
import importlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping


ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


ANALYSIS_VERSION = (
    "XAUUSD_PORTABLE_FEATURE_CONTRACT_DESIGN_V1"
)

PORTABLE_FEATURE_CONTRACT_VERSION = (
    "XAUUSD_MTF_PORTABLE_FEATURE_V1"
)


ADJUDICATOR_MODULE = (
    "04_Testing."
    "adjudicate_xauusd_current_broker_full_333_portability"
)


adjudicator: Any = importlib.import_module(
    ADJUDICATOR_MODULE
)


FINAL_ADJUDICATION_JSON = (
    ROOT_DIR
    /
    "04_Testing/evidence/production_portability/xauusd_current_broker_full_333_evidence_adjudication.json"
)

FEATURE_ACTION_JSON = (
    ROOT_DIR
    /
    "04_Testing/evidence/production_portability/xauusd_broker_sensitive_feature_actions.json"
)

REPLACEMENT_AUDIT_JSON = (
    ROOT_DIR
    /
    "04_Testing/evidence/production_portability/xauusd_portable_broker_sensitive_replacements.json"
)


EXPECTED_FINAL_ADJUDICATION_VERSION = (
    "XAUUSD_CURRENT_BROKER_FULL_333_EVIDENCE_ADJUDICATION_V1"
)

EXPECTED_FEATURE_ACTION_VERSION = (
    "XAUUSD_BROKER_SENSITIVE_FEATURE_ACTIONS_V1"
)

EXPECTED_REPLACEMENT_AUDIT_VERSION = (
    "XAUUSD_PORTABLE_BROKER_SENSITIVE_REPLACEMENT_AUDIT_V1"
)


EXPECTED_FINAL_CLASSIFICATION = (
    "XAUUSD_330_NON_BROKER_SENSITIVE_FEATURES_"
    "TRAIN_PORTABILITY_CONFIRMED"
)

EXPECTED_FEATURE_ACTION_STATUS = (
    "BROKER_SENSITIVE_FEATURE_ACTION_POLICY_CONFIRMED"
)

EXPECTED_REPLACEMENT_STATUS = (
    "NO_PORTABLE_MODEL_SPREAD_CANDIDATE_IDENTIFIED"
)


PARENT_FEATURE_CONTRACT = (
    "XAUUSD_MTF_TRAINING_V3"
)

PARENT_FEATURE_COUNT = 333

PORTABLE_FEATURE_COUNT = 331


DROPPED_MODEL_FEATURES = (
    "m5_spread_points",
    "m5_tick_volume_log1p",
)

RETAINED_RELATIVE_VOLUME_FEATURE = (
    "m5_tick_volume_ratio20"
)


EXPECTED_PORTABLE_TICK_VOLUME_CANDIDATES = {
    "tick_volume_ratio100",
    "tick_volume_ratio288",
    "tick_volume_zscore100",
    "tick_volume_zscore288",
}


RUNTIME_COST_METRICS_OUTSIDE_MODEL = (
    "spread_price",
    "spread_points",
    "spread_ticks",
    "spread_atr",
    "spread_bps",
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
    document: Mapping[
        str,
        Any,
    ],
    key: str,
) -> Mapping[
    str,
    Any,
]:

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


def _string_list(
    document: Mapping[
        str,
        Any,
    ],
    key: str,
) -> list[str]:

    value = document.get(
        key
    )

    if not isinstance(
        value,
        list,
    ):
        raise RuntimeError(
            (
                "EXPECTED_LIST_MISSING:"
                f"{key}"
            )
        )

    return [
        str(
            item
        )
        for item
        in value
    ]


def _load_evidence(
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:

    final_document = (
        adjudicator
        ._load_json(
            FINAL_ADJUDICATION_JSON
        )
    )

    action_document = (
        adjudicator
        ._load_json(
            FEATURE_ACTION_JSON
        )
    )

    replacement_document = (
        adjudicator
        ._load_json(
            REPLACEMENT_AUDIT_JSON
        )
    )

    return (
        final_document,
        action_document,
        replacement_document,
    )


def _validate_document(
    document: Mapping[
        str,
        Any,
    ],
    *,
    expected_version: str,
    evidence_name: str,
) -> None:

    _require(
        bool(
            document.get(
                "valid",
                False,
            )
        ),
        (
            "EVIDENCE_NOT_VALID:"
            f"{evidence_name}"
        ),
    )

    observed_version = str(
        document.get(
            "analysis_version",
            "",
        )
    )

    _require(
        observed_version
        ==
        expected_version,
        (
            "EVIDENCE_VERSION_MISMATCH:"
            f"{evidence_name}:"
            f"{observed_version}:"
            f"{expected_version}"
        ),
    )


def _validate_final_adjudication(
    document: Mapping[
        str,
        Any,
    ],
) -> None:

    classification = (
        _mapping(
            document,
            "classification",
        )
    )

    observed = str(
        classification.get(
            "classification",
            "",
        )
    )

    _require(
        observed
        ==
        EXPECTED_FINAL_CLASSIFICATION,
        (
            "FINAL_CLASSIFICATION_MISMATCH:"
            f"{observed}"
        ),
    )

    _require(
        bool(
            classification.get(
                "non_broker_sensitive_330_portable",
                False,
            )
        ),
        "NON_BROKER_SENSITIVE_330_NOT_PORTABLE",
    )

    _require(
        not bool(
            classification.get(
                "full_333_portable_as_is",
                True,
            )
        ),
        "FULL_333_UNEXPECTEDLY_PORTABLE_AS_IS",
    )

    _require(
        bool(
            classification.get(
                "broker_sensitive_normalization_required",
                False,
            )
        ),
        "BROKER_SENSITIVE_NORMALIZATION_NOT_REQUIRED",
    )

    _require(
        not bool(
            classification.get(
                "test_evaluation_authorized",
                True,
            )
        ),
        "TEST_UNEXPECTEDLY_AUTHORIZED",
    )

    _require(
        not bool(
            classification.get(
                "broker_specific_retraining_authorized",
                True,
            )
        ),
        "RETRAINING_UNEXPECTEDLY_AUTHORIZED",
    )


def _validate_feature_actions(
    document: Mapping[
        str,
        Any,
    ],
) -> None:

    decision = (
        _mapping(
            document,
            "decision",
        )
    )

    status = str(
        decision.get(
            "status",
            "",
        )
    )

    _require(
        status
        ==
        EXPECTED_FEATURE_ACTION_STATUS,
        (
            "FEATURE_ACTION_STATUS_MISMATCH:"
            f"{status}"
        ),
    )

    _require(
        bool(
            decision.get(
                "unchanged_331_feature_base_confirmed",
                False,
            )
        ),
        "UNCHANGED_331_BASE_NOT_CONFIRMED",
    )

    observed_count = int(
        decision.get(
            "unchanged_portable_feature_count",
            0,
        )
    )

    _require(
        observed_count
        ==
        PORTABLE_FEATURE_COUNT,
        (
            "UNCHANGED_PORTABLE_COUNT_MISMATCH:"
            f"{observed_count}:"
            f"{PORTABLE_FEATURE_COUNT}"
        ),
    )

    keep_features = (
        _string_list(
            decision,
            "keep_as_is_features",
        )
    )

    _require(
        keep_features
        ==
        [
            RETAINED_RELATIVE_VOLUME_FEATURE
        ],
        (
            "KEEP_AS_IS_FEATURE_POLICY_MISMATCH:"
            f"{keep_features}"
        ),
    )

    removal_features = set(
        _string_list(
            decision,
            "replacement_or_removal_features",
        )
    )

    _require(
        removal_features
        ==
        set(
            DROPPED_MODEL_FEATURES
        ),
        (
            "REMOVAL_FEATURE_POLICY_MISMATCH:"
            f"{sorted(removal_features)}"
        ),
    )

    _require(
        not bool(
            decision.get(
                "model_retraining_authorized",
                True,
            )
        ),
        "ACTION_GATE_RETRAINING_UNEXPECTEDLY_AUTHORIZED",
    )

    _require(
        not bool(
            decision.get(
                "test_evaluation_authorized",
                True,
            )
        ),
        "ACTION_GATE_TEST_UNEXPECTEDLY_AUTHORIZED",
    )

    _require(
        not bool(
            decision.get(
                "target_contract_change_authorized",
                True,
            )
        ),
        "ACTION_GATE_TARGET_CHANGE_UNEXPECTEDLY_AUTHORIZED",
    )


def _validate_replacement_audit(
    document: Mapping[
        str,
        Any,
    ],
) -> None:

    decision = (
        _mapping(
            document,
            "decision",
        )
    )

    status = str(
        decision.get(
            "status",
            "",
        )
    )

    _require(
        status
        ==
        EXPECTED_REPLACEMENT_STATUS,
        (
            "REPLACEMENT_STATUS_MISMATCH:"
            f"{status}"
        ),
    )

    portable_spread_candidates = (
        _string_list(
            decision,
            "portable_spread_candidates",
        )
    )

    _require(
        not portable_spread_candidates,
        (
            "PORTABLE_SPREAD_CANDIDATE_UNEXPECTED:"
            f"{portable_spread_candidates}"
        ),
    )

    selected_spread = (
        decision.get(
            "selected_spread_candidate_for_contract_design"
        )
    )

    _require(
        selected_spread
        is None,
        (
            "SELECTED_SPREAD_CANDIDATE_UNEXPECTED:"
            f"{selected_spread}"
        ),
    )

    retained_relative_volume = str(
        decision.get(
            "retained_existing_relative_volume_feature",
            "",
        )
    )

    _require(
        retained_relative_volume
        ==
        RETAINED_RELATIVE_VOLUME_FEATURE,
        (
            "RETAINED_RELATIVE_VOLUME_MISMATCH:"
            f"{retained_relative_volume}"
        ),
    )

    portable_tick_candidates = set(
        _string_list(
            decision,
            "portable_tick_volume_candidates",
        )
    )

    _require(
        portable_tick_candidates
        ==
        EXPECTED_PORTABLE_TICK_VOLUME_CANDIDATES,
        (
            "PORTABLE_TICK_CANDIDATE_SET_MISMATCH:"
            f"{sorted(portable_tick_candidates)}"
        ),
    )

    absolute_action = str(
        decision.get(
            "absolute_tick_volume_default_action",
            "",
        )
    )

    _require(
        absolute_action
        ==
        "DROP_WITHOUT_REPLACEMENT_FOR_FIRST_PORTABLE_CONTRACT",
        (
            "ABSOLUTE_TICK_VOLUME_DEFAULT_ACTION_MISMATCH:"
            f"{absolute_action}"
        ),
    )

    observed_base = int(
        decision.get(
            "unchanged_portable_feature_base",
            0,
        )
    )

    _require(
        observed_base
        ==
        PORTABLE_FEATURE_COUNT,
        (
            "REPLACEMENT_AUDIT_BASE_COUNT_MISMATCH:"
            f"{observed_base}:"
            f"{PORTABLE_FEATURE_COUNT}"
        ),
    )

    _require(
        not bool(
            decision.get(
                "new_feature_contract_implementation_authorized",
                True,
            )
        ),
        "REPLACEMENT_GATE_IMPLEMENTATION_UNEXPECTEDLY_AUTHORIZED",
    )

    _require(
        not bool(
            decision.get(
                "model_retraining_authorized",
                True,
            )
        ),
        "REPLACEMENT_GATE_RETRAINING_UNEXPECTEDLY_AUTHORIZED",
    )

    _require(
        not bool(
            decision.get(
                "test_evaluation_authorized",
                True,
            )
        ),
        "REPLACEMENT_GATE_TEST_UNEXPECTEDLY_AUTHORIZED",
    )

    _require(
        not bool(
            decision.get(
                "target_contract_change_authorized",
                True,
            )
        ),
        "REPLACEMENT_GATE_TARGET_CHANGE_UNEXPECTEDLY_AUTHORIZED",
    )


def _training_identity(
    final_document: Mapping[
        str,
        Any,
    ],
) -> Mapping[
    str,
    Any,
]:

    evidence_identity = (
        _mapping(
            final_document,
            "evidence_identity",
        )
    )

    training_identity = (
        _mapping(
            evidence_identity,
            "training_identity",
        )
    )

    return training_identity


def _canonical_json_sha256(
    document: Mapping[
        str,
        Any,
    ],
) -> str:

    payload = json.dumps(
        document,
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


def _contract_core(
    training_identity: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:

    return {
        "contract_version": (
            PORTABLE_FEATURE_CONTRACT_VERSION
        ),
        "contract_status": (
            "DESIGN_ONLY_NOT_IMPLEMENTED"
        ),
        "asset": (
            "XAUUSD"
        ),
        "parent_contract": (
            PARENT_FEATURE_CONTRACT
        ),
        "parent_feature_count": (
            PARENT_FEATURE_COUNT
        ),
        "portable_model_feature_count": (
            PORTABLE_FEATURE_COUNT
        ),
        "feature_transformation": {
            "operation": (
                "PARENT_FEATURE_SET_MINUS_EXPLICIT_DROPS"
            ),
            "dropped_features": list(
                DROPPED_MODEL_FEATURES
            ),
            "added_features": [],
            "retained_existing_broker_sensitive_feature": (
                RETAINED_RELATIVE_VOLUME_FEATURE
            ),
        },
        "spread_policy": {
            "model_feature_policy": (
                "NO_SPREAD_FEATURE_IN_FIRST_PORTABLE_MODEL_CONTRACT"
            ),
            "raw_spread_points_in_model": (
                False
            ),
            "normalized_spread_candidate_in_model": (
                False
            ),
            "reason": (
                "NO_PREDECLARED_SPREAD_CANDIDATE_PASSED_"
                "TRAIN_ONLY_CROSS_BROKER_PORTABILITY"
            ),
            "runtime_cost_metrics_outside_model": list(
                RUNTIME_COST_METRICS_OUTSIDE_MODEL
            ),
            "runtime_cost_metric_role": (
                "EXECUTION_DIAGNOSTIC_RISK_AND_TRADE_READY_GATING_ONLY"
            ),
        },
        "tick_volume_policy": {
            "absolute_tick_volume_log1p_in_model": (
                False
            ),
            "retained_relative_feature": (
                RETAINED_RELATIVE_VOLUME_FEATURE
            ),
            "additional_relative_volume_features_added": [],
            "portable_but_not_selected_candidates": sorted(
                EXPECTED_PORTABLE_TICK_VOLUME_CANDIDATES
            ),
            "reason_additional_candidates_not_selected": (
                "PORTABILITY_ALONE_DOES_NOT_JUSTIFY_REDUNDANT_"
                "FEATURE_ADDITION_WITHOUT_LABEL_OR_MODEL_EVIDENCE"
            ),
        },
        "time_semantics": {
            "source_broker_time": (
                "MUST_BE_CANONICALIZED_BEFORE_FEATURE_GENERATION"
            ),
            "feature_availability": (
                "CAUSAL_ONLY_AT_DECISION_TIME"
            ),
        },
        "d1_semantics": {
            "source": (
                "RECONSTRUCT_FROM_CANONICAL_H1"
            ),
            "session_boundary_utc": (
                "00:00"
            ),
            "minimum_h1_bars_per_retained_d1_session": (
                1
            ),
            "available_lag_minutes": (
                1440
            ),
            "native_broker_d1_required": (
                False
            ),
        },
        "target_contract": {
            "changed": (
                False
            ),
            "target_semantics": (
                "UNCHANGED_FROM_FROZEN_RESEARCH_TARGET"
            ),
        },
        "training_lineage": {
            "source_dataset_id": str(
                training_identity.get(
                    "dataset_id",
                    "",
                )
            ),
            "source_dataset_sha256": str(
                training_identity.get(
                    "dataset_sha256",
                    "",
                )
            ),
            "source_training_manifest_sha256": str(
                training_identity.get(
                    "training_manifest_sha256",
                    "",
                )
            ),
            "source_training_contract": str(
                training_identity.get(
                    "training_contract",
                    "",
                )
            ),
            "source_train_rows": int(
                training_identity.get(
                    "train_rows",
                    0,
                )
            ),
        },
        "authorization": {
            "design_frozen": (
                True
            ),
            "research_pipeline_implementation_authorized": (
                False
            ),
            "dataset_rebuild_authorized": (
                False
            ),
            "model_retraining_authorized": (
                False
            ),
            "validation_evaluation_authorized": (
                False
            ),
            "test_evaluation_authorized": (
                False
            ),
            "live_authorized": (
                False
            ),
        },
    }


def _decision(
    *,
    contract_core: Mapping[
        str,
        Any,
    ],
    fingerprint: str,
) -> dict[str, Any]:

    feature_transformation = (
        _mapping(
            contract_core,
            "feature_transformation",
        )
    )

    dropped = (
        _string_list(
            feature_transformation,
            "dropped_features",
        )
    )

    added = (
        _string_list(
            feature_transformation,
            "added_features",
        )
    )

    expected_count = (
        PARENT_FEATURE_COUNT
        -
        len(
            dropped
        )
        +
        len(
            added
        )
    )

    _require(
        expected_count
        ==
        PORTABLE_FEATURE_COUNT,
        (
            "PORTABLE_CONTRACT_FEATURE_COUNT_ARITHMETIC_FAILED:"
            f"{expected_count}:"
            f"{PORTABLE_FEATURE_COUNT}"
        ),
    )

    return {
        "status": (
            "XAUUSD_PORTABLE_331_FEATURE_CONTRACT_DESIGN_CONFIRMED"
        ),
        "reason": (
            "PORTABILITY_EVIDENCE_SUPPORTS_RETAINING_331_PARENT_"
            "FEATURES_WHILE_DROPPING_RAW_SPREAD_POINTS_AND_"
            "ABSOLUTE_TICK_VOLUME_LEVEL_WITH_NO_NEW_MODEL_FEATURES"
        ),
        "contract_version": (
            PORTABLE_FEATURE_CONTRACT_VERSION
        ),
        "contract_fingerprint_sha256": (
            fingerprint
        ),
        "parent_feature_count": (
            PARENT_FEATURE_COUNT
        ),
        "dropped_feature_count": int(
            len(
                dropped
            )
        ),
        "added_feature_count": int(
            len(
                added
            )
        ),
        "portable_model_feature_count": (
            expected_count
        ),
        "research_pipeline_implementation_authorized_next": (
            True
        ),
        "dataset_rebuild_authorized": (
            False
        ),
        "model_retraining_authorized": (
            False
        ),
        "validation_evaluation_authorized": (
            False
        ),
        "test_evaluation_authorized": (
            False
        ),
        "target_contract_change_authorized": (
            False
        ),
        "live_authorized": (
            False
        ),
        "next_action": (
            "IMPLEMENT_XAUUSD_MTF_PORTABLE_FEATURE_V1_IN_"
            "RESEARCH_DATASET_PIPELINE_WITHOUT_RETRAINING"
        ),
    }


def run_design(
) -> dict[str, Any]:

    (
        final_document,
        action_document,
        replacement_document,
    ) = (
        _load_evidence()
    )

    _validate_document(
        final_document,
        expected_version=(
            EXPECTED_FINAL_ADJUDICATION_VERSION
        ),
        evidence_name=(
            "FINAL_333_ADJUDICATION"
        ),
    )

    _validate_document(
        action_document,
        expected_version=(
            EXPECTED_FEATURE_ACTION_VERSION
        ),
        evidence_name=(
            "BROKER_SENSITIVE_FEATURE_ACTIONS"
        ),
    )

    _validate_document(
        replacement_document,
        expected_version=(
            EXPECTED_REPLACEMENT_AUDIT_VERSION
        ),
        evidence_name=(
            "BROKER_SENSITIVE_REPLACEMENT_AUDIT"
        ),
    )

    _validate_final_adjudication(
        final_document
    )

    _validate_feature_actions(
        action_document
    )

    _validate_replacement_audit(
        replacement_document
    )

    training_identity = (
        _training_identity(
            final_document
        )
    )

    contract_core = (
        _contract_core(
            training_identity
        )
    )

    fingerprint = (
        _canonical_json_sha256(
            contract_core
        )
    )

    decision = (
        _decision(
            contract_core=(
                contract_core
            ),
            fingerprint=(
                fingerprint
            ),
        )
    )

    return {
        "valid": True,
        "reason": (
            "OK_XAUUSD_PORTABLE_FEATURE_CONTRACT_DESIGN"
        ),
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "research_scope": (
            "DESIGN_ONLY_FREEZE_OF_FIRST_CROSS_BROKER_"
            "PORTABLE_XAUUSD_MODEL_FEATURE_CONTRACT"
        ),
        "evidence": {
            "final_333_adjudication_version": (
                EXPECTED_FINAL_ADJUDICATION_VERSION
            ),
            "broker_sensitive_action_version": (
                EXPECTED_FEATURE_ACTION_VERSION
            ),
            "replacement_audit_version": (
                EXPECTED_REPLACEMENT_AUDIT_VERSION
            ),
            "all_prerequisites_validated": (
                True
            ),
        },
        "contract": (
            contract_core
        ),
        "contract_fingerprint": {
            "version": (
                "XAUUSD_PORTABLE_FEATURE_CONTRACT_FINGERPRINT_V1"
            ),
            "sha256": (
                fingerprint
            ),
            "canonicalization": (
                "JSON_SORT_KEYS_COMPACT_UTF8_SHA256"
            ),
        },
        "decision": (
            decision
        ),
        "scientific_policy": {
            "train_evidence_used": (
                True
            ),
            "new_market_data_loaded": (
                False
            ),
            "mt5_used": (
                False
            ),
            "labels_used": (
                False
            ),
            "target_columns_loaded": (
                False
            ),
            "validation_loaded": (
                False
            ),
            "validation_evaluated": (
                False
            ),
            "test_loaded": (
                False
            ),
            "test_evaluated": (
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
            "feature_pipeline_modified": (
                False
            ),
            "dataset_rebuilt": (
                False
            ),
            "frozen_v3_contract_mutated": (
                False
            ),
            "target_contract_changed": (
                False
            ),
            "execution_integration_modified": (
                False
            ),
            "risk_engine_modified": (
                False
            ),
            "sizing_modified": (
                False
            ),
            "orders_sent": (
                False
            ),
            "positions_modified": (
                False
            ),
            "live_authorized": (
                False
            ),
            "account_login_emitted": (
                False
            ),
            "account_holder_name_emitted": (
                False
            ),
            "account_scope_identifier_emitted": (
                False
            ),
            "filesystem_paths_emitted": (
                False
            ),
        },
        "next_decision_contract": {
            "if_design_confirmed": (
                "IMPLEMENT_PORTABLE_FEATURE_V1_IN_RESEARCH_"
                "DATASET_PIPELINE_WITHOUT_MODEL_RETRAINING"
            ),
            "expected_model_feature_count": (
                PORTABLE_FEATURE_COUNT
            ),
            "expected_dropped_features": list(
                DROPPED_MODEL_FEATURES
            ),
            "expected_added_features": [],
            "retained_existing_relative_volume_feature": (
                RETAINED_RELATIVE_VOLUME_FEATURE
            ),
            "spread_model_feature_expected": (
                False
            ),
            "runtime_broker_cost_metrics_preserved": (
                True
            ),
            "target_contract_change_required": (
                False
            ),
            "test_holdout_remains_untouched": (
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
                        "XAUUSD_PORTABLE_FEATURE_CONTRACT_DESIGN_FAILED"
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
                    "mt5_used": (
                        False
                    ),
                    "validation_loaded": (
                        False
                    ),
                    "test_loaded": (
                        False
                    ),
                    "test_evaluated": (
                        False
                    ),
                    "model_loaded": (
                        False
                    ),
                    "model_trained": (
                        False
                    ),
                    "feature_pipeline_modified": (
                        False
                    ),
                    "target_contract_changed": (
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