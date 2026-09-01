from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).with_name(
    "run_xauusd_portable_331_one_time_validation.py"
)

spec = importlib.util.spec_from_file_location(
    "xauusd_one_time_validation_runner_test_target",
    MODULE_PATH,
)

assert spec is not None
assert spec.loader is not None

runner = importlib.util.module_from_spec(
    spec
)

sys.modules[
    spec.name
] = runner

spec.loader.exec_module(
    runner
)


def test_real_dry_preflight_is_valid_and_non_consuming(
    tmp_path: Path,
):
    ledger_path = (
        tmp_path
        / "xauusd_portable_331_one_time_validation_access_ledger.json"
    )

    result_path = (
        tmp_path
        / "xauusd_portable_331_one_time_validation_result.json"
    )

    report = runner.build_preflight(
        ledger_path=ledger_path,
        result_path=result_path,
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
            "dry_preflight_completed"
        ]
        is True
    )

    assert (
        report[
            "decision"
        ][
            "real_validation_executed"
        ]
        is False
    )

    assert (
        report[
            "decision"
        ][
            "real_validation_execution_authorized_next"
        ]
        is True
    )

    assert (
        report[
            "decision"
        ][
            "test_access_authorized"
        ]
        is False
    )

    assert (
        ledger_path.exists()
        is False
    )


def test_dry_preflight_is_deterministic(
    tmp_path: Path,
):
    ledger_path = (
        tmp_path
        / "xauusd_portable_331_one_time_validation_access_ledger.json"
    )

    result_path = (
        tmp_path
        / "xauusd_portable_331_one_time_validation_result.json"
    )

    first = runner.build_preflight(
        ledger_path=ledger_path,
        result_path=result_path,
    )

    second = runner.build_preflight(
        ledger_path=ledger_path,
        result_path=result_path,
    )

    assert (
        first[
            "preflight_record"
        ]
        == second[
            "preflight_record"
        ]
    )

    assert (
        first[
            "preflight_fingerprint"
        ]
        == second[
            "preflight_fingerprint"
        ]
    )


def test_preflight_fingerprint_matches_record(
    tmp_path: Path,
):
    report = runner.build_preflight(
        ledger_path=(
            tmp_path
            / "ledger.json"
        ),
        result_path=(
            tmp_path
            / "result.json"
        ),
    )

    assert (
        runner._canonical_sha256(
            report[
                "preflight_record"
            ]
        )
        == report[
            "preflight_fingerprint"
        ][
            "sha256"
        ]
    )


def test_tampered_stored_preflight_fails_closed(
    tmp_path: Path,
):
    ledger_path = (
        tmp_path
        / "ledger.json"
    )

    result_path = (
        tmp_path
        / "result.json"
    )

    preflight_path = (
        tmp_path
        / "preflight.json"
    )

    report = runner.build_preflight(
        ledger_path=ledger_path,
        result_path=result_path,
    )

    original_fingerprint = (
        report[
            "preflight_fingerprint"
        ][
            "sha256"
        ]
    )

    tampered = copy.deepcopy(
        report
    )

    tampered[
        "preflight_record"
    ][
        "threshold_search_allowed"
    ] = True

    preflight_path.write_text(
        json.dumps(
            tampered,
            indent=2,
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        runner.OneTimeValidationRunnerError
    ):
        runner.validate_stored_preflight(
            preflight_path=preflight_path,
            expected_fingerprint=(
                original_fingerprint
            ),
            ledger_path=ledger_path,
            result_path=result_path,
        )


def test_consumed_ledger_blocks_new_preflight_execution(
    tmp_path: Path,
):
    core = runner._load_module(
        runner.CORE_PATH,
        "xauusd_runner_test_core_for_consumed_ledger",
    )

    ledger_path = (
        tmp_path
        / "ledger.json"
    )

    ledger = core.ValidationAccessLedger(
        path=ledger_path,
        protocol_fingerprint_sha256=(
            runner.EXPECTED_PROTOCOL_FINGERPRINT
        ),
        model_artifact_sha256=(
            runner.EXPECTED_MODEL_ARTIFACT_SHA256
        ),
    )

    ledger.reserve_before_read()
    ledger.mark_read_initiated()

    report = runner.build_preflight(
        ledger_path=ledger_path,
        result_path=(
            tmp_path
            / "result.json"
        ),
    )

    assert (
        report[
            "decision"
        ][
            "real_validation_execution_authorized_next"
        ]
        is False
    )

    assert (
        report[
            "preflight_record"
        ][
            "holdout_consumed_before_execution"
        ]
        is True
    )


def test_pre_read_failure_ledger_is_recoverable(
    tmp_path: Path,
):
    core = runner._load_module(
        runner.CORE_PATH,
        "xauusd_runner_test_core_for_recoverable_ledger",
    )

    ledger_path = (
        tmp_path
        / "ledger.json"
    )

    ledger = core.ValidationAccessLedger(
        path=ledger_path,
        protocol_fingerprint_sha256=(
            runner.EXPECTED_PROTOCOL_FINGERPRINT
        ),
        model_artifact_sha256=(
            runner.EXPECTED_MODEL_ARTIFACT_SHA256
        ),
    )

    ledger.reserve_before_read()
    ledger.mark_failure(
        RuntimeError(
            "synthetic pre-read failure"
        )
    )

    report = runner.build_preflight(
        ledger_path=ledger_path,
        result_path=(
            tmp_path
            / "result.json"
        ),
    )

    assert (
        report[
            "decision"
        ][
            "real_validation_execution_authorized_next"
        ]
        is True
    )

    assert (
        report[
            "preflight_record"
        ][
            "ledger_state"
        ]
        == "PRE_READ_TECHNICAL_FAILURE_RECOVERABLE"
    )