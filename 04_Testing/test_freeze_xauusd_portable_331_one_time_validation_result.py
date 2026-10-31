from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).with_name(
    "freeze_xauusd_portable_331_one_time_validation_result.py"
)

spec = importlib.util.spec_from_file_location(
    "xauusd_validation_result_freeze_test_target",
    MODULE_PATH,
)

assert spec is not None
assert spec.loader is not None

freeze = importlib.util.module_from_spec(
    spec
)

sys.modules[
    spec.name
] = freeze

spec.loader.exec_module(
    freeze
)


def _payloads():
    preflight = freeze._read_json_auto(
        freeze.PREFLIGHT_PATH
    )

    result = freeze._read_json_auto(
        freeze.RESULT_PATH
    )

    ledger = freeze._read_json_auto(
        freeze.LEDGER_PATH
    )

    return (
        preflight,
        result,
        ledger,
    )


def test_real_consumed_validation_result_freezes_cleanly():
    report = (
        freeze.build_validation_result_freeze()
    )

    assert (
        report[
            "valid"
        ]
        is True
    )

    assert (
        report[
            "decision"
        ][
            "validation_result_frozen"
        ]
        is True
    )

    assert (
        report[
            "decision"
        ][
            "validation_accepted"
        ]
        is True
    )

    assert (
        report[
            "decision"
        ][
            "validation_rerun_authorized"
        ]
        is False
    )

    assert (
        report[
            "decision"
        ][
            "test_runner_implementation_authorized_next"
        ]
        is True
    )

    assert (
        report[
            "decision"
        ][
            "test_execution_authorized"
        ]
        is False
    )


def test_freeze_is_deterministic():
    first = (
        freeze.build_validation_result_freeze()
    )

    second = (
        freeze.build_validation_result_freeze()
    )

    assert (
        first
        == second
    )


def test_result_record_metric_tamper_fails_closed():
    (
        _,
        result,
        _,
    ) = _payloads()

    tampered = copy.deepcopy(
        result
    )

    tampered[
        "result_record"
    ][
        "validation_metrics"
    ][
        "balanced_accuracy_3class"
    ] += 0.01

    with pytest.raises(
        freeze.ValidationResultFreezeError
    ):
        freeze._validate_result(
            tampered
        )


def test_result_decision_tamper_fails_closed():
    (
        _,
        result,
        _,
    ) = _payloads()

    tampered = copy.deepcopy(
        result
    )

    tampered[
        "decision"
    ][
        "validation_rerun_authorized"
    ] = True

    with pytest.raises(
        freeze.ValidationResultFreezeError
    ):
        freeze._validate_result(
            tampered
        )


def test_ledger_second_read_attempt_tamper_fails_closed():
    (
        _,
        result,
        ledger,
    ) = _payloads()

    tampered = copy.deepcopy(
        ledger
    )

    tampered[
        "validation_read_attempt_count"
    ] = 2

    with pytest.raises(
        freeze.ValidationResultFreezeError
    ):
        freeze._validate_ledger(
            tampered,
            result,
        )


def test_preflight_fingerprint_tamper_fails_closed():
    (
        preflight,
        _,
        _,
    ) = _payloads()

    tampered = copy.deepcopy(
        preflight
    )

    tampered[
        "preflight_fingerprint"
    ][
        "sha256"
    ] = (
        "0"
        * 64
    )

    with pytest.raises(
        freeze.ValidationResultFreezeError
    ):
        freeze._validate_preflight(
            tampered
        )