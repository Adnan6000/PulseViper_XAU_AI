from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping


ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


ANALYSIS_VERSION = (
    "XAUUSD_BROKER_SENSITIVE_FEATURE_ACTIONS_V1"
)

FULL_AUDIT_VERSION = (
    "XAUUSD_CURRENT_BROKER_FULL_MTF_PORTABILITY_V2"
)

FINAL_ADJUDICATION_VERSION = (
    "XAUUSD_CURRENT_BROKER_FULL_333_EVIDENCE_ADJUDICATION_V1"
)


ADJUDICATOR_MODULE = (
    "04_Testing."
    "adjudicate_xauusd_current_broker_full_333_portability"
)


adjudicator: Any = importlib.import_module(
    ADJUDICATOR_MODULE
)


FULL_AUDIT_JSON = (
    ROOT_DIR
    /
    "04_Testing/evidence/production_portability/xauusd_current_broker_full_mtf_portability.json"
)

FINAL_ADJUDICATION_JSON = (
    ROOT_DIR
    /
    "04_Testing/evidence/production_portability/xauusd_current_broker_full_333_evidence_adjudication.json"
)


BROKER_SENSITIVE_FEATURES = (
    "m5_spread_points",
    "m5_tick_volume_log1p",
    "m5_tick_volume_ratio20",
)


EXPECTED_FINAL_CLASSIFICATION = (
    "XAUUSD_330_NON_BROKER_SENSITIVE_FEATURES_"
    "TRAIN_PORTABILITY_CONFIRMED"
)


MINIMUM_FINITE_PAIR_FRACTION = 0.90

MINIMUM_PAIRED_CORRELATION = 0.80

PSI_MATERIAL = 0.25

STANDARDIZED_MEAN_SHIFT_MATERIAL = 0.50


EXPECTED_ACTIONS = {
    "m5_spread_points": (
        "REPLACE_WITH_BROKER_INVARIANT_SPREAD_FEATURE"
    ),
    "m5_tick_volume_log1p": (
        "REMOVE_OR_REPLACE_ABSOLUTE_TICK_VOLUME_LEVEL"
    ),
    "m5_tick_volume_ratio20": (
        "KEEP_AS_IS"
    ),
}


UNCHANGED_PORTABLE_BASE_BEFORE_TRIO = 330

EXPECTED_KEEP_AS_IS_FROM_TRIO = 1

EXPECTED_REPLACEMENT_REQUIRED_FROM_TRIO = 2

EXPECTED_UNCHANGED_PORTABLE_BASE_AFTER_TRIO = 331


def _require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:
        raise RuntimeError(
            reason
        )


def _safe_float(
    value: Any,
) -> float | None:

    try:
        result = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):
        return None

    if result != result:
        return None

    if result in (
        float("inf"),
        float("-inf"),
    ):
        return None

    return result


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


def _load_evidence(
) -> tuple[
    dict[str, Any],
    dict[str, Any],
]:

    full_document = (
        adjudicator
        ._load_json(
            FULL_AUDIT_JSON
        )
    )

    final_document = (
        adjudicator
        ._load_json(
            FINAL_ADJUDICATION_JSON
        )
    )

    _require(
        bool(
            full_document.get(
                "valid",
                False,
            )
        ),
        "FULL_AUDIT_EVIDENCE_INVALID",
    )

    _require(
        bool(
            final_document.get(
                "valid",
                False,
            )
        ),
        "FINAL_ADJUDICATION_EVIDENCE_INVALID",
    )

    _require(
        str(
            full_document.get(
                "analysis_version",
                "",
            )
        )
        ==
        FULL_AUDIT_VERSION,
        (
            "FULL_AUDIT_VERSION_MISMATCH:"
            f"{full_document.get('analysis_version')}"
        ),
    )

    _require(
        str(
            final_document.get(
                "analysis_version",
                "",
            )
        )
        ==
        FINAL_ADJUDICATION_VERSION,
        (
            "FINAL_ADJUDICATION_VERSION_MISMATCH:"
            f"{final_document.get('analysis_version')}"
        ),
    )

    return (
        full_document,
        final_document,
    )


def _validate_final_prerequisite(
    final_document: Mapping[
        str,
        Any,
    ],
) -> None:

    classification = (
        _mapping(
            final_document,
            "classification",
        )
    )

    observed_classification = str(
        classification.get(
            "classification",
            "",
        )
    )

    _require(
        observed_classification
        ==
        EXPECTED_FINAL_CLASSIFICATION,
        (
            "FINAL_PORTABILITY_CLASSIFICATION_MISMATCH:"
            f"{observed_classification}"
        ),
    )

    _require(
        bool(
            classification.get(
                "non_broker_sensitive_330_portable",
                False,
            )
        ),
        "NON_BROKER_SENSITIVE_330_NOT_CONFIRMED",
    )

    _require(
        not bool(
            classification.get(
                "broker_sensitive_group_portable_as_is",
                True,
            )
        ),
        "BROKER_SENSITIVE_GROUP_UNEXPECTEDLY_PORTABLE_AS_IS",
    )

    _require(
        bool(
            classification.get(
                "broker_sensitive_normalization_required",
                False,
            )
        ),
        "BROKER_SENSITIVE_NORMALIZATION_NOT_REQUIRED_BY_PREREQUISITE",
    )

    _require(
        bool(
            classification.get(
                "portable_feature_contract_design_authorized",
                False,
            )
        ),
        "PORTABLE_FEATURE_CONTRACT_DESIGN_NOT_AUTHORIZED",
    )

    _require(
        not bool(
            classification.get(
                "test_evaluation_authorized",
                True,
            )
        ),
        "TEST_EVALUATION_UNEXPECTEDLY_AUTHORIZED",
    )

    _require(
        not bool(
            classification.get(
                "broker_specific_retraining_authorized",
                True,
            )
        ),
        "BROKER_SPECIFIC_RETRAINING_UNEXPECTEDLY_AUTHORIZED",
    )


def _feature_comparison_map(
    full_document: Mapping[
        str,
        Any,
    ],
) -> dict[
    str,
    Mapping[
        str,
        Any,
    ],
]:

    raw_comparisons = (
        full_document.get(
            "feature_comparisons"
        )
    )

    if not isinstance(
        raw_comparisons,
        list,
    ):
        raise RuntimeError(
            "FEATURE_COMPARISONS_LIST_MISSING"
        )

    result: dict[
        str,
        Mapping[
            str,
            Any,
        ],
    ] = {}

    for item in raw_comparisons:

        if not isinstance(
            item,
            Mapping,
        ):
            continue

        feature = str(
            item.get(
                "feature",
                "",
            )
        ).strip()

        if not feature:
            continue

        _require(
            feature
            not in
            result,
            (
                "DUPLICATE_FEATURE_COMPARISON:"
                f"{feature}"
            ),
        )

        result[
            feature
        ] = item

    for feature in (
        BROKER_SENSITIVE_FEATURES
    ):

        _require(
            feature
            in
            result,
            (
                "BROKER_SENSITIVE_FEATURE_COMPARISON_MISSING:"
                f"{feature}"
            ),
        )

    return result


def _individual_portability_checks(
    comparison: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:

    finite_pair_fraction = (
        _safe_float(
            comparison.get(
                "finite_pair_fraction"
            )
        )
    )

    paired_correlation = (
        _safe_float(
            comparison.get(
                "paired_correlation"
            )
        )
    )

    psi = (
        _safe_float(
            comparison.get(
                "psi"
            )
        )
    )

    standardized_mean_shift = (
        _safe_float(
            comparison.get(
                "standardized_mean_shift"
            )
        )
    )

    material_distribution_shift = bool(
        comparison.get(
            "material_distribution_shift",
            False,
        )
    )

    coverage_ok = bool(
        finite_pair_fraction
        is not None
        and
        finite_pair_fraction
        >=
        MINIMUM_FINITE_PAIR_FRACTION
    )

    correlation_ok = bool(
        paired_correlation
        is not None
        and
        paired_correlation
        >=
        MINIMUM_PAIRED_CORRELATION
    )

    psi_ok = bool(
        psi is None
        or
        psi
        <
        PSI_MATERIAL
    )

    standardized_shift_ok = bool(
        standardized_mean_shift
        is None
        or
        abs(
            standardized_mean_shift
        )
        <
        STANDARDIZED_MEAN_SHIFT_MATERIAL
    )

    distribution_ok = bool(
        not material_distribution_shift
        and
        psi_ok
        and
        standardized_shift_ok
    )

    portable_as_is = bool(
        coverage_ok
        and
        correlation_ok
        and
        distribution_ok
    )

    return {
        "finite_pair_fraction": (
            finite_pair_fraction
        ),
        "paired_correlation": (
            paired_correlation
        ),
        "psi": (
            psi
        ),
        "standardized_mean_shift": (
            standardized_mean_shift
        ),
        "material_distribution_shift": (
            material_distribution_shift
        ),
        "coverage_ok": (
            coverage_ok
        ),
        "correlation_ok": (
            correlation_ok
        ),
        "psi_ok": (
            psi_ok
        ),
        "standardized_mean_shift_ok": (
            standardized_shift_ok
        ),
        "distribution_ok": (
            distribution_ok
        ),
        "portable_as_is": (
            portable_as_is
        ),
    }


def _action_for_feature(
    *,
    feature: str,
    checks: Mapping[
        str,
        Any,
    ],
) -> str:

    portable_as_is = bool(
        checks.get(
            "portable_as_is",
            False,
        )
    )

    if portable_as_is:

        return (
            "KEEP_AS_IS"
        )

    if (
        feature
        ==
        "m5_spread_points"
    ):

        return (
            "REPLACE_WITH_BROKER_INVARIANT_SPREAD_FEATURE"
        )

    if (
        feature
        ==
        "m5_tick_volume_log1p"
    ):

        return (
            "REMOVE_OR_REPLACE_ABSOLUTE_TICK_VOLUME_LEVEL"
        )

    return (
        "REQUIRES_ADDITIONAL_PORTABILITY_RESEARCH"
    )


def _feature_document(
    *,
    feature: str,
    comparison: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:

    checks = (
        _individual_portability_checks(
            comparison
        )
    )

    action = (
        _action_for_feature(
            feature=(
                feature
            ),
            checks=(
                checks
            ),
        )
    )

    expected_action = (
        EXPECTED_ACTIONS[
            feature
        ]
    )

    return {
        "feature": (
            feature
        ),
        "checks": (
            checks
        ),
        "action": (
            action
        ),
        "expected_action": (
            expected_action
        ),
        "action_matches_expected": bool(
            action
            ==
            expected_action
        ),
    }


def _decision(
    feature_documents: Mapping[
        str,
        Mapping[
            str,
            Any,
        ],
    ],
) -> dict[str, Any]:

    keep_features = [
        feature
        for (
            feature,
            document,
        )
        in feature_documents.items()
        if (
            document.get(
                "action"
            )
            ==
            "KEEP_AS_IS"
        )
    ]

    replacement_features = [
        feature
        for (
            feature,
            document,
        )
        in feature_documents.items()
        if (
            document.get(
                "action"
            )
            !=
            "KEEP_AS_IS"
        )
    ]

    unexpected_actions = [
        feature
        for (
            feature,
            document,
        )
        in feature_documents.items()
        if not bool(
            document.get(
                "action_matches_expected",
                False,
            )
        )
    ]

    all_expected = bool(
        not unexpected_actions
        and
        len(
            keep_features
        )
        ==
        EXPECTED_KEEP_AS_IS_FROM_TRIO
        and
        len(
            replacement_features
        )
        ==
        EXPECTED_REPLACEMENT_REQUIRED_FROM_TRIO
        and
        keep_features
        ==
        [
            "m5_tick_volume_ratio20"
        ]
    )

    if all_expected:

        status = (
            "BROKER_SENSITIVE_FEATURE_ACTION_POLICY_CONFIRMED"
        )

        reason = (
            "RELATIVE_TICK_VOLUME_RATIO_MEETS_INDIVIDUAL_"
            "PORTABILITY_THRESHOLDS_WHILE_RAW_SPREAD_POINTS_"
            "AND_ABSOLUTE_TICK_VOLUME_LEVEL_REQUIRE_REDESIGN"
        )

        next_action = (
            "AUDIT_PORTABLE_SPREAD_AND_TICK_VOLUME_"
            "REPLACEMENT_CANDIDATES_ON_TRAIN_ONLY"
        )

    else:

        status = (
            "BROKER_SENSITIVE_FEATURE_ACTION_POLICY_UNRESOLVED"
        )

        reason = (
            "INDIVIDUAL_BROKER_SENSITIVE_FEATURE_EVIDENCE_"
            "DOES_NOT_MATCH_THE_PREDECLARED_ACTION_POLICY"
        )

        next_action = (
            "REVIEW_ONLY_UNEXPECTED_BROKER_SENSITIVE_FEATURE_ACTIONS"
        )

    unchanged_portable_feature_count = (
        UNCHANGED_PORTABLE_BASE_BEFORE_TRIO
        +
        len(
            keep_features
        )
    )

    return {
        "status": (
            status
        ),
        "reason": (
            reason
        ),
        "keep_as_is_features": (
            keep_features
        ),
        "replacement_or_removal_features": (
            replacement_features
        ),
        "unexpected_action_features": (
            unexpected_actions
        ),
        "unchanged_portable_feature_count": (
            unchanged_portable_feature_count
        ),
        "expected_unchanged_portable_feature_count": (
            EXPECTED_UNCHANGED_PORTABLE_BASE_AFTER_TRIO
        ),
        "unchanged_331_feature_base_confirmed": bool(
            all_expected
            and
            unchanged_portable_feature_count
            ==
            EXPECTED_UNCHANGED_PORTABLE_BASE_AFTER_TRIO
        ),
        "portable_spread_replacement_research_authorized": bool(
            all_expected
        ),
        "portable_tick_volume_replacement_research_authorized": bool(
            all_expected
        ),
        "new_feature_contract_implementation_authorized": (
            False
        ),
        "model_retraining_authorized": (
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
            next_action
        ),
    }


def run_adjudication(
) -> dict[str, Any]:

    (
        full_document,
        final_document,
    ) = (
        _load_evidence()
    )

    _validate_final_prerequisite(
        final_document
    )

    comparison_map = (
        _feature_comparison_map(
            full_document
        )
    )

    feature_documents: dict[
        str,
        dict[str, Any],
    ] = {}

    for feature in (
        BROKER_SENSITIVE_FEATURES
    ):

        feature_documents[
            feature
        ] = (
            _feature_document(
                feature=(
                    feature
                ),
                comparison=(
                    comparison_map[
                        feature
                    ]
                ),
            )
        )

    decision = (
        _decision(
            feature_documents
        )
    )

    return {
        "valid": True,
        "reason": (
            "OK_XAUUSD_BROKER_SENSITIVE_FEATURE_ACTION_ADJUDICATION"
        ),
        "analysis_version": (
            ANALYSIS_VERSION
        ),
        "research_scope": (
            "TRAIN_ONLY_INDIVIDUAL_ACTION_POLICY_FOR_"
            "THREE_BROKER_SENSITIVE_XAUUSD_FEATURES"
        ),
        "prerequisite": {
            "full_audit_version": (
                FULL_AUDIT_VERSION
            ),
            "final_adjudication_version": (
                FINAL_ADJUDICATION_VERSION
            ),
            "final_classification": (
                EXPECTED_FINAL_CLASSIFICATION
            ),
            "non_broker_sensitive_portable_count": (
                UNCHANGED_PORTABLE_BASE_BEFORE_TRIO
            ),
        },
        "thresholds": {
            "minimum_finite_pair_fraction": (
                MINIMUM_FINITE_PAIR_FRACTION
            ),
            "minimum_paired_correlation": (
                MINIMUM_PAIRED_CORRELATION
            ),
            "psi_material": (
                PSI_MATERIAL
            ),
            "standardized_mean_shift_material": (
                STANDARDIZED_MEAN_SHIFT_MATERIAL
            ),
        },
        "feature_actions": (
            feature_documents
        ),
        "decision": (
            decision
        ),
        "candidate_research_direction": {
            "spread_feature": {
                "source_feature": (
                    "m5_spread_points"
                ),
                "action": (
                    "REPLACE"
                ),
                "candidate_families_to_test": [
                    "spread_ticks",
                    "spread_atr",
                    "spread_bps",
                ],
                "candidate_selected": (
                    False
                ),
            },
            "absolute_tick_volume_feature": {
                "source_feature": (
                    "m5_tick_volume_log1p"
                ),
                "action": (
                    "REMOVE_OR_REPLACE"
                ),
                "candidate_families_to_test": [
                    "tick_volume_zscore",
                    "tick_volume_longer_horizon_ratio",
                    "drop_without_replacement",
                ],
                "candidate_selected": (
                    False
                ),
            },
            "relative_tick_volume_feature": {
                "source_feature": (
                    "m5_tick_volume_ratio20"
                ),
                "action": (
                    "KEEP_AS_IS_IF_POLICY_CONFIRMED"
                ),
            },
        },
        "scientific_policy": {
            "existing_train_evidence_only": (
                True
            ),
            "new_market_data_loaded": (
                False
            ),
            "mt5_used": (
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
            "labels_used": (
                False
            ),
            "target_columns_loaded": (
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
            "frozen_v3_contract_mutated": (
                False
            ),
            "target_contract_changed": (
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
            "broker_specific_retraining_authorized": (
                False
            ),
            "model_retraining_authorized": (
                False
            ),
            "test_evaluation_authorized": (
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
            "if_action_policy_confirmed": (
                "AUDIT_PORTABLE_SPREAD_AND_TICK_VOLUME_"
                "REPLACEMENT_CANDIDATES_ON_TRAIN_ONLY"
            ),
            "if_action_policy_unresolved": (
                "REVIEW_ONLY_UNEXPECTED_BROKER_SENSITIVE_FEATURE_ACTIONS"
            ),
            "candidate_contract_not_created_yet": (
                True
            ),
            "candidate_replacements_not_selected_yet": (
                True
            ),
            "frozen_v3_contract_not_mutated": (
                True
            ),
            "target_contract_not_changed": (
                True
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
            run_adjudication()
        )

    except Exception as exc:

        print(
            json.dumps(
                {
                    "valid": False,
                    "reason": (
                        "XAUUSD_BROKER_SENSITIVE_"
                        "FEATURE_ACTION_ADJUDICATION_FAILED"
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
                    "orders_sent": (
                        False
                    ),
                    "positions_modified": (
                        False
                    ),
                    "risk_engine_modified": (
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