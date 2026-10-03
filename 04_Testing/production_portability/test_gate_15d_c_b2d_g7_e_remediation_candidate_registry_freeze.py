from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path
from typing import Any


RUNNER_PATH = (
    Path(__file__).resolve().parent
    / "run_xauusd_gate_15d_c_b2d_g7_e_remediation_candidate_registry_freeze.py"
)


spec = importlib.util.spec_from_file_location(
    "g7e",
    RUNNER_PATH,
)

assert spec is not None
assert spec.loader is not None

g7e: Any = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(
    g7e
)


registry: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_remediation_candidate_registry"
)


def test_01_repository_base() -> None:

    assert (
        registry.REPOSITORY_BASE_COMMIT
        ==
        "63b2ea84a74c7a4a5e3ad355b6e0c2ec4e702893"
    )


def test_02_scientific_parent_is_g7d() -> None:

    assert (
        registry.SCIENTIFIC_PARENT_AUTHORITY_COMMIT
        ==
        "86271e347939c18a45c03629efdfeab1035da75a"
    )


def test_03_g7d_fingerprint_bound() -> None:

    assert (
        registry.G7D_CONTRACT_FINGERPRINT_SHA256
        ==
        "c6270f03fed45ba749d40ea4c556b95e683ad934575c9dc958664bef83f86638"
    )


def test_04_data_authority_frozen() -> None:

    assert (
        registry.DATASET_ID
        ==
        "portable_cff75b0686383a3ab6f8352b"
    )

    assert registry.FEATURE_COUNT == 331


def test_05_feature_hash_frozen() -> None:

    assert (
        registry.FEATURE_COLUMNS_SHA256
        ==
        "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
    )


def test_06_target_unchanged() -> None:

    assert (
        registry.TARGET_CONTRACT
        ==
        "CLEAN_DIRECTIONAL_EXCURSION_V2"
    )

    assert registry.TARGET_CHANGE_ALLOWED is False


def test_07_registry_candidate_count_within_bound() -> None:

    count = len(
        registry.CANDIDATES
    )

    assert count == 6

    assert (
        registry.MIN_ALLOWED_CANDIDATES
        <=
        count
        <=
        registry.MAX_ALLOWED_CANDIDATES
    )


def test_08_registry_is_finite() -> None:

    assert registry.REGISTRY_FINITE is True

    assert (
        registry.REGISTRY_FROZEN_BEFORE_FIRST_FIT
        is True
    )


def test_09_registry_immutable_after_fit() -> None:

    assert (
        registry.REGISTRY_CHANGE_AFTER_FIRST_FIT_ALLOWED
        is False
    )

    assert (
        registry.RESULTS_DRIVEN_CANDIDATE_ADDITION_ALLOWED
        is False
    )

    assert (
        registry.RESULTS_DRIVEN_HYPERPARAMETER_CHANGE_ALLOWED
        is False
    )


def test_10_no_automated_unbounded_search() -> None:

    assert (
        registry.UNBOUNDED_GRID_SEARCH_ALLOWED
        is False
    )

    assert (
        registry.BAYESIAN_OPTIMIZATION_ALLOWED
        is False
    )

    assert registry.AUTOML_ALLOWED is False

    assert (
        registry.UNBOUNDED_RANDOM_SEARCH_ALLOWED
        is False
    )


def test_11_no_feature_subset_search() -> None:

    assert (
        registry.ALL_CANDIDATES_USE_EXACT_331_FEATURES
        is True
    )

    assert (
        registry.FEATURE_SUBSET_SEARCH_ALLOWED
        is False
    )


def test_12_candidate_ids_unique() -> None:

    ids = [
        candidate[
            "candidate_id"
        ]
        for candidate
        in registry.CANDIDATES
    ]

    assert len(
        ids
    ) == len(
        set(
            ids
        )
    )


def test_13_c04_control_first() -> None:

    candidate = registry.CANDIDATES[
        0
    ]

    assert (
        candidate[
            "candidate_id"
        ]
        ==
        "R00_CONTROL_C04_EXACT"
    )

    assert (
        candidate[
            "role"
        ]
        ==
        "HISTORICAL_CONTROL"
    )


def test_14_c04_exact_estimator_config() -> None:

    candidate = registry.CANDIDATES[
        0
    ]

    estimator = candidate[
        "estimator"
    ]

    assert (
        estimator[
            "implementation"
        ]
        ==
        "sklearn.ensemble.ExtraTreesClassifier"
    )

    assert estimator[
        "bootstrap"
    ] is False

    assert estimator[
        "class_weight"
    ] == "balanced"

    assert estimator[
        "max_depth"
    ] == 10

    assert estimator[
        "max_features"
    ] == 0.35

    assert estimator[
        "min_samples_leaf"
    ] == 25

    assert estimator[
        "n_estimators"
    ] == 500

    assert estimator[
        "n_jobs"
    ] == -1

    assert estimator[
        "random_state"
    ] == 271828


def test_15_all_candidates_exact_331_scope() -> None:

    for candidate in registry.CANDIDATES:

        assert (
            candidate[
                "feature_scope"
            ]
            ==
            "EXACT_331_FROZEN_FEATURES"
        )


def test_16_all_class_orders_frozen() -> None:

    for candidate in registry.CANDIDATES:

        assert (
            candidate[
                "probability_class_order"
            ]
            ==
            [-1, 0, 1]
        )


def test_17_no_candidate_calibration() -> None:

    for candidate in registry.CANDIDATES:

        assert (
            candidate[
                "probability_calibration"
            ][
                "enabled"
            ]
            is False
        )


def test_18_no_candidate_threshold_tuning() -> None:

    for candidate in registry.CANDIDATES:

        assert (
            candidate[
                "threshold_policy"
            ][
                "tuning_enabled"
            ]
            is False
        )


def test_19_remediation_candidates_have_hypotheses() -> None:

    for candidate in registry.CANDIDATES[
        1:
    ]:

        assert (
            candidate[
                "role"
            ]
            ==
            "REMEDIATION_CANDIDATE"
        )

        assert bool(
            candidate[
                "hypothesis"
            ]
        )


def test_20_remediation_candidates_bind_failure_modes() -> None:

    allowed = set(
        registry.BROAD_FAILURE_MODES
    )

    for candidate in registry.CANDIDATES[
        1:
    ]:

        modes = candidate[
            "addresses_failure_modes"
        ]

        assert modes

        assert set(
            modes
        ).issubset(
            allowed
        )


def test_21_forward_30_is_not_development_data() -> None:

    assert (
        registry.FORWARD_30_DEVELOPMENT_USE_ALLOWED
        is False
    )

    assert (
        registry.SAMPLE_SPECIFIC_FORWARD_TUNING_ALLOWED
        is False
    )


def test_22_test_sealed() -> None:

    assert (
        registry.TEST_ACCESS_ALLOWED_IN_G7E
        is False
    )

    assert (
        registry.TEST_ACCESS_ALLOWED_DURING_REMEDIATION_SELECTION
        is False
    )


def test_23_selection_policy_predeclared() -> None:

    assert (
        len(
            registry.SELECTION_POLICY
        )
        ==
        6
    )

    assert (
        registry.SELECTION_POLICY[
            0
        ][
            "metric"
        ]
        ==
        "macro_f1"
    )


def test_24_selection_not_single_metric_only() -> None:

    assert (
        registry.SINGLE_METRIC_ONLY_SELECTION_ALLOWED
        is False
    )


def test_25_current_gate_loads_no_values() -> None:

    assert (
        registry.THIS_GATE_LOADS_TRAIN_VALUES
        is False
    )

    assert (
        registry.THIS_GATE_LOADS_VALIDATION_VALUES
        is False
    )

    assert (
        registry.THIS_GATE_LOADS_TEST_VALUES
        is False
    )


def test_26_current_gate_does_not_train() -> None:

    assert (
        registry.THIS_GATE_TRAINS_MODELS
        is False
    )

    assert (
        registry.THIS_GATE_FITS_PREPROCESSORS
        is False
    )

    assert (
        registry.THIS_GATE_EVALUATES_CANDIDATES
        is False
    )


def test_27_current_gate_selects_no_winner() -> None:

    assert (
        registry.THIS_GATE_SELECTS_WINNER
        is False
    )


def test_28_no_live_execution() -> None:

    assert registry.LIVE_AUTHORIZED is False

    assert (
        registry.EXECUTION_AUTHORIZED
        is False
    )


def test_29_candidate_fingerprints_complete() -> None:

    fingerprints = (
        registry.candidate_fingerprints()
    )

    assert len(
        fingerprints
    ) == len(
        registry.CANDIDATES
    )

    assert all(
        len(value) == 64
        for value
        in fingerprints.values()
    )


def test_30_registry_fingerprint_consistent() -> None:

    assert (
        registry.registry_fingerprint_sha256()
        ==
        registry.REGISTRY_FINGERPRINT_SHA256
    )


def test_31_runner_no_mt5_execution_surface() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert "MetaTrader5" not in text
    assert "order_send(" not in text
    assert "order_check(" not in text
    assert "positions_get(" not in text


def test_32_runtime_ledgers_protected() -> None:

    text = RUNNER_PATH.read_text(
        encoding="utf-8"
    )

    assert (
        "RUNTIME_LEDGER_CHANGED_DURING_G7E_FREEZE"
        in text
    )


def test_33_docs_only_bridge_enforced() -> None:

    assert (
        g7e.ALLOWED_BRIDGE_PATHS
        ==
        {
            "README.md",
            "05_Documentation/Architecture.md",
            "05_Documentation/Development_Roadmap.md",
        }
    )