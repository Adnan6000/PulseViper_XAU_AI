from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).with_name(
    "design_xauusd_portable_331_one_time_validation_protocol.py"
)

spec = importlib.util.spec_from_file_location(
    "xauusd_one_time_validation_protocol_design_test_target",
    MODULE_PATH,
)

assert spec is not None
assert spec.loader is not None

design = importlib.util.module_from_spec(
    spec
)

sys.modules[
    spec.name
] = design

spec.loader.exec_module(
    design
)


def test_real_protocol_design_is_valid_and_deterministic():
    first = design.build_protocol()
    second = design.build_protocol()

    assert first == second

    assert (
        first[
            "valid"
        ]
        is True
    )

    assert (
        first[
            "decision"
        ][
            "validation_protocol_frozen"
        ]
        is True
    )

    assert (
        first[
            "decision"
        ][
            "validation_values_loaded"
        ]
        is False
    )

    assert (
        first[
            "decision"
        ][
            "test_access_authorized"
        ]
        is False
    )


def test_acceptance_gate_is_derived_from_frozen_c04_train_results():
    report = design.build_protocol()

    gate = (
        report[
            "contract"
        ][
            "acceptance_gate"
        ]
    )

    assert (
        gate[
            "minimum_directional_macro_f1_short_long"
        ]
        == pytest.approx(
            0.25365034089349603
        )
    )

    assert (
        gate[
            "minimum_balanced_accuracy_3class"
        ]
        == pytest.approx(
            0.34040386328178984
        )
    )

    assert (
        gate[
            "minimum_macro_f1_3class"
        ]
        == pytest.approx(
            0.24533114425757888
        )
    )


def test_original_trade_coverage_bounds_are_preserved():
    report = design.build_protocol()

    gate = (
        report[
            "contract"
        ][
            "acceptance_gate"
        ]
    )

    assert (
        gate[
            "minimum_predicted_trade_coverage"
        ]
        == pytest.approx(
            0.05
        )
    )

    assert (
        gate[
            "maximum_predicted_trade_coverage"
        ]
        == pytest.approx(
            0.95
        )
    )

    assert (
        gate[
            "short_recall_must_be_positive"
        ]
        is True
    )

    assert (
        gate[
            "long_recall_must_be_positive"
        ]
        is True
    )


def test_probability_metrics_are_report_only_not_post_hoc_gate():
    report = design.build_protocol()

    gate = (
        report[
            "contract"
        ][
            "acceptance_gate"
        ]
    )

    policy = (
        report[
            "contract"
        ][
            "prediction_policy"
        ]
    )

    assert (
        gate[
            "log_loss_3class_is_hard_gate"
        ]
        is False
    )

    assert (
        gate[
            "multiclass_brier_is_hard_gate"
        ]
        is False
    )

    assert (
        policy[
            "probability_calibration_allowed"
        ]
        is False
    )

    assert (
        policy[
            "threshold_search_allowed"
        ]
        is False
    )


def test_model_verification_tamper_fails_closed():
    payload = (
        design._read_json_auto(
            design.MODEL_VERIFICATION_PATH
        )
    )

    tampered = copy.deepcopy(
        payload
    )

    tampered[
        "artifact_validation"
    ][
        "model_artifact_sha256"
    ] = (
        "0"
        * 64
    )

    with pytest.raises(
        design.ValidationProtocolDesignError
    ):
        design._validate_model_verification(
            tampered
        )


def test_walk_forward_fingerprint_tamper_fails_closed():
    payload = (
        design._read_json_auto(
            design.WALK_FORWARD_PATH
        )
    )

    tampered = copy.deepcopy(
        payload
    )

    tampered[
        "evaluation_fingerprint"
    ][
        "sha256"
    ] = (
        "0"
        * 64
    )

    with pytest.raises(
        design.ValidationProtocolDesignError
    ):
        design._validate_walk_forward(
            tampered
        )