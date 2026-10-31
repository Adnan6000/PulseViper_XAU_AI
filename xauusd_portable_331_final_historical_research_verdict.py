from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ANALYSIS_VERSION = "XAUUSD_PORTABLE_331_FINAL_HISTORICAL_RESEARCH_VERDICT_V1"

VALIDATION_RESULT_FILE = "xauusd_portable_331_one_time_validation_result.json"
VALIDATION_FREEZE_FILE = "xauusd_portable_331_one_time_validation_result_freeze.json"
TEST_RESULT_FILE = "xauusd_portable_331_one_time_test_recovery_result.json"
OUTPUT_FILE = "xauusd_portable_331_final_historical_research_verdict.json"

EXPECTED = {
    "winner_candidate_id": "C04_FLAT_EXTRA_TREES_CONSTRAINED",
    "model_artifact_sha256": "48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769",
    "feature_columns_sha256": "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2",
    "validation_protocol_fingerprint_sha256": "ce78180a5f2472c36c74cea2c447307641aa3d5fedfb7a01d9b65260b5a6fcea",
    "validation_result_fingerprint_sha256": "ea8b482e60f854f58e27f3be387b7bb82f0c16a6cf1a99555b12643aeeca5fa1",
    "validation_freeze_fingerprint_sha256": "521a97b41a86231b049cc65aebfd85ffc7c83ae7141134d6ae1158d112b1468c",
    "test_protocol_fingerprint_sha256": "f8acc2665e9e5bbd3c3ad4bdf34d4a1ff9bfb8b715acf24f6669530eaa5aab3e",
    "test_core_result_fingerprint_sha256": "3f029e5a1fb17cd5cf2344bef589f1dba85ca93bff322d469fa819a109c7727d",
    "test_wrapper_result_fingerprint_sha256": "b616845398dba270ed9425da8809d8d91b6ae9def99ec269a71fcc059f389713",
    "original_test_failure_sha256": "84557a8399d89f81cd1db15b7489fcc60805b1b61fd9bfbae2a850ceb4066110",
    "recovery_preflight_fingerprint_sha256": "cc9316f5483fd3cd92344d6600b6848657e73cadde02905d92b30591c2386d6f",
}


def load_json(base_dir: Path, filename: str) -> dict[str, Any]:
    path = base_dir / filename
    if not path.is_file():
        raise RuntimeError(f"required evidence file missing: {filename}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"required evidence is not a JSON object: {filename}")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(f"evidence integrity check failed: {message}")


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def all_true(mapping: dict[str, Any]) -> bool:
    return bool(mapping) and all(value is True for value in mapping.values())


def build_verdict(base_dir: Path) -> dict[str, Any]:
    validation = load_json(base_dir, VALIDATION_RESULT_FILE)
    validation_freeze = load_json(base_dir, VALIDATION_FREEZE_FILE)
    test = load_json(base_dir, TEST_RESULT_FILE)

    validation_core = validation["core_result"]
    validation_record = validation["result_record"]
    validation_decision = validation["decision"]
    validation_policy = validation["scientific_policy"]

    freeze_record = validation_freeze["freeze_record"]
    freeze_decision = validation_freeze["decision"]
    freeze_policy = validation_freeze["scientific_policy"]

    test_record = test["result_record"]
    test_core = test_record["core_result"]
    test_ledger = test_record["ledger_final"]
    test_decision = test["decision"]
    test_policy = test["scientific_policy"]

    require(validation.get("valid") is True, "validation result valid != true")
    require(validation_freeze.get("valid") is True, "validation freeze valid != true")
    require(test.get("valid") is True, "test result valid != true")
    require(test_core.get("valid") is True, "test core valid != true")
    require(test_ledger.get("valid") is True, "test ledger valid != true")

    require(
        validation["research_scope"]
        == "FIRST_AND_ONLY_REAL_UNTOUCHED_PORTABLE_VALIDATION_EVALUATION_OF_VERIFIED_FROZEN_C04",
        "validation research scope mismatch",
    )
    require(
        test["research_scope"]
        == "RECOVERED_FIRST_AND_ONLY_REAL_PORTABLE_TEST_EVALUATION_AFTER_PRE_READ_TECHNICAL_FAILURE",
        "test research scope mismatch",
    )

    require(
        validation["result_fingerprint"]["sha256"]
        == EXPECTED["validation_result_fingerprint_sha256"],
        "validation result fingerprint mismatch",
    )
    require(
        validation_freeze["freeze_fingerprint"]["sha256"]
        == EXPECTED["validation_freeze_fingerprint_sha256"],
        "validation freeze fingerprint mismatch",
    )
    require(
        test["result_fingerprint"]["sha256"]
        == EXPECTED["test_wrapper_result_fingerprint_sha256"],
        "test wrapper fingerprint mismatch",
    )
    require(
        test_core["result_fingerprint"]
        == EXPECTED["test_core_result_fingerprint_sha256"],
        "test core fingerprint mismatch",
    )
    require(
        test_ledger["result_fingerprint"]
        == EXPECTED["test_core_result_fingerprint_sha256"],
        "test ledger/core fingerprint mismatch",
    )

    require(
        validation_record["validation_protocol_fingerprint_sha256"]
        == EXPECTED["validation_protocol_fingerprint_sha256"],
        "validation protocol fingerprint mismatch",
    )
    require(
        freeze_record["validation_result_fingerprint_sha256"]
        == EXPECTED["validation_result_fingerprint_sha256"],
        "validation freeze/result binding mismatch",
    )
    require(
        test_record["validation_result_fingerprint_sha256"]
        == EXPECTED["validation_result_fingerprint_sha256"],
        "test/validation-result binding mismatch",
    )
    require(
        test_record["validation_freeze_fingerprint_sha256"]
        == EXPECTED["validation_freeze_fingerprint_sha256"],
        "test/validation-freeze binding mismatch",
    )
    require(
        test_record["test_protocol_fingerprint_sha256"]
        == EXPECTED["test_protocol_fingerprint_sha256"],
        "test protocol fingerprint mismatch",
    )
    require(
        test_record["original_failed_result_sha256"]
        == EXPECTED["original_test_failure_sha256"],
        "original pre-read failure fingerprint mismatch",
    )
    require(
        test_record["recovery_preflight_fingerprint_sha256"]
        == EXPECTED["recovery_preflight_fingerprint_sha256"],
        "recovery preflight fingerprint mismatch",
    )

    for label, value in (
        ("validation winner", validation_record["winner_candidate_id"]),
        ("validation freeze winner", freeze_record["winner_candidate_id"]),
        ("test winner", test_record["winner_candidate_id"]),
    ):
        require(value == EXPECTED["winner_candidate_id"], f"{label} mismatch")

    for label, value in (
        ("validation model", validation_record["model_artifact_sha256"]),
        ("validation freeze model", freeze_record["model_artifact_sha256"]),
        ("test model", test_record["model_artifact_sha256"]),
        ("test core model", test_core["bindings"]["model_artifact_sha256"]),
        ("test ledger model", test_ledger["model_artifact_sha256"]),
    ):
        require(value == EXPECTED["model_artifact_sha256"], f"{label} SHA mismatch")

    for label, value in (
        ("validation features", validation_record["feature_columns_sha256"]),
        ("validation freeze features", freeze_record["feature_columns_sha256"]),
        ("test features", test_record["feature_columns_sha256"]),
        ("test core features", test_core["bindings"]["feature_columns_sha256"]),
        ("test ledger features", test_ledger["feature_columns_sha256"]),
    ):
        require(value == EXPECTED["feature_columns_sha256"], f"{label} SHA mismatch")

    require(
        test_core["bindings"]["probability_class_order"] == [-1, 0, 1],
        "probability class order mismatch",
    )
    require(test_core["bindings"]["feature_count"] == 331, "test feature count != 331")
    require(
        validation_record["validation_feature_count"] == 331,
        "validation feature count != 331",
    )

    require(
        validation_decision["status"] == "ONE_TIME_VALIDATION_ACCEPTED",
        "validation status mismatch",
    )
    require(
        validation_decision["validation_accepted"] is True,
        "validation not accepted",
    )
    require(
        validation_decision["validation_consumed"] is True,
        "validation not consumed",
    )
    require(
        validation_decision["validation_rerun_authorized"] is False,
        "validation rerun authorized",
    )
    require(
        validation_core["ledger"]["validation_read_attempt_count"] == 1,
        "validation read count != 1",
    )
    require(
        validation_core["ledger"]["validation_metrics_computed"] is True,
        "validation metrics not computed",
    )
    require(
        all_true(validation_record["validation_gate_result"]["hard_checks"]),
        "validation hard checks not all true",
    )
    require(
        validation_record["source_evidence"]["read_policy"][
            "test_feature_values_loaded"
        ]
        is False
        and validation_record["source_evidence"]["read_policy"][
            "test_target_values_loaded"
        ]
        is False,
        "test values accessed during validation",
    )

    require(
        freeze_decision["status"]
        == "ONE_TIME_VALIDATION_RESULT_FROZEN_ACCEPTED",
        "validation freeze status mismatch",
    )
    require(
        freeze_decision["validation_result_frozen"] is True,
        "validation result not frozen",
    )
    require(
        freeze_policy["dataset_rows_loaded_in_this_gate"] is False,
        "dataset rows loaded during validation freeze",
    )

    require(
        test_decision["status"] == "ONE_TIME_TEST_ACCEPTED",
        "test status mismatch",
    )
    require(test_decision["test_accepted"] is True, "test not accepted")
    require(test_decision["test_consumed"] is True, "test not consumed")
    require(
        test_decision["test_rerun_authorized"] is False,
        "test rerun authorized",
    )
    require(
        test_ledger["status"] == "TEST_COMPLETE_ACCEPTED",
        "test ledger status mismatch",
    )
    require(
        test_ledger["test_read_attempt_count"] == 1,
        "test read count != 1",
    )
    require(
        test_ledger["test_values_loaded"] is True,
        "test values not loaded",
    )
    require(
        test_ledger["test_metrics_computed"] is True,
        "test metrics not computed",
    )
    require(
        test_ledger["holdout_consumed_for_rerun_policy"] is True,
        "test holdout not marked consumed",
    )
    require(
        test_ledger["validation_values_reread"] is False,
        "validation reread during test",
    )
    require(
        all_true(test_core["hard_checks"]),
        "test hard checks not all true",
    )

    test_read_policy = test_record["source_evidence"]["read_policy"]
    require(
        test_read_policy["parser_reads_final_test_block_only"] is True,
        "test parser policy mismatch",
    )
    require(
        test_read_policy["train_feature_values_loaded"] is False,
        "train features loaded during test",
    )
    require(
        test_read_policy["train_target_values_loaded"] is False,
        "train targets loaded during test",
    )
    require(
        test_read_policy["validation_feature_values_loaded"] is False,
        "validation features loaded during test",
    )
    require(
        test_read_policy["validation_target_values_loaded"] is False,
        "validation targets loaded during test",
    )

    core_policy = test_core["scientific_policy"]
    no_post_holdout_change = all(
        (
            core_policy["candidate_change_performed"] is False,
            core_policy["feature_change_performed"] is False,
            core_policy["target_change_performed"] is False,
            core_policy["model_refit_performed"] is False,
            core_policy["probability_calibration_performed"] is False,
            core_policy["threshold_change_performed"] is False,
            test_core["decision"][
                "current_frozen_lineage_may_be_tuned_from_test"
            ]
            is False,
        )
    )
    require(
        no_post_holdout_change,
        "post-holdout model/policy change detected",
    )

    for label, policy in (
        ("validation", validation_policy),
        ("validation freeze", freeze_policy),
        ("test", test_policy),
    ):
        require(
            policy["live_authorized"] is False,
            f"live authorized by {label}",
        )
        require(
            policy["shadow_authorized"] is False,
            f"shadow authorized by {label}",
        )

    require(
        test_policy["risk_engine_modified"] is False,
        "risk engine modified",
    )
    require(
        test_policy["execution_integration_modified"] is False,
        "execution integration modified",
    )
    require(
        test_policy["orders_sent"] is False,
        "orders sent",
    )
    require(
        test_policy["portable_validation_reread_performed"] is False,
        "validation reread performed",
    )

    verdict_record: dict[str, Any] = {
        "analysis_version": ANALYSIS_VERSION,
        "research_scope": (
            "FINAL_HISTORICAL_OUT_OF_SAMPLE_VERDICT_FOR_"
            "FROZEN_PORTABLE_XAUUSD_C04_LINEAGE"
        ),
        "lineage": {
            "winner_candidate_id": EXPECTED["winner_candidate_id"],
            "model_artifact_sha256": EXPECTED["model_artifact_sha256"],
            "feature_columns_sha256": EXPECTED["feature_columns_sha256"],
            "feature_count": 331,
            "probability_class_order": [-1, 0, 1],
        },
        "evidence_bindings": {
            "validation_result": {
                "file": VALIDATION_RESULT_FILE,
                "protocol_fingerprint_sha256": EXPECTED[
                    "validation_protocol_fingerprint_sha256"
                ],
                "result_fingerprint_sha256": EXPECTED[
                    "validation_result_fingerprint_sha256"
                ],
            },
            "validation_freeze": {
                "file": VALIDATION_FREEZE_FILE,
                "freeze_fingerprint_sha256": EXPECTED[
                    "validation_freeze_fingerprint_sha256"
                ],
            },
            "test_result": {
                "file": TEST_RESULT_FILE,
                "protocol_fingerprint_sha256": EXPECTED[
                    "test_protocol_fingerprint_sha256"
                ],
                "core_result_fingerprint_sha256": EXPECTED[
                    "test_core_result_fingerprint_sha256"
                ],
                "wrapper_result_fingerprint_sha256": EXPECTED[
                    "test_wrapper_result_fingerprint_sha256"
                ],
                "original_pre_read_failure_sha256": EXPECTED[
                    "original_test_failure_sha256"
                ],
                "recovery_preflight_fingerprint_sha256": EXPECTED[
                    "recovery_preflight_fingerprint_sha256"
                ],
            },
        },
        "validation": {
            "status": validation_decision["status"],
            "accepted": True,
            "consumed": True,
            "read_attempt_count": validation_core["ledger"][
                "validation_read_attempt_count"
            ],
            "rerun_authorized": False,
            "row_count": validation_record["validation_row_count"],
            "metrics": validation_record["validation_metrics"],
            "hard_checks": validation_record[
                "validation_gate_result"
            ]["hard_checks"],
        },
        "test": {
            "status": test_decision["status"],
            "ledger_status": test_ledger["status"],
            "accepted": True,
            "consumed": True,
            "read_attempt_count": test_ledger["test_read_attempt_count"],
            "rerun_authorized": False,
            "validation_values_reread": test_ledger[
                "validation_values_reread"
            ],
            "row_count": test_core["test_row_count"],
            "metrics": test_core["metrics"],
            "hard_checks": test_core["hard_checks"],
        },
        "historical_research_verdict": {
            "frozen_c04_passed_one_time_untouched_validation": True,
            "frozen_c04_passed_first_and_only_untouched_historical_test": True,
            "test_accessed_exactly_once": True,
            "test_permanently_consumed": True,
            "post_holdout_tuning_refit_calibration_candidate_feature_target_changes_performed": False,
            "validation_reread_during_test": False,
            "historical_out_of_sample_acceptance_under_predefined_train_only_thresholds": True,
            "live_trading_authorized": False,
            "shadow_deployment_automatically_authorized": False,
            "next_major_engineering_phase": (
                "PRODUCTION_PORTABILITY_AND_SHADOW_INFRASTRUCTURE"
            ),
        },
        "scientific_policy": {
            "candidate_change_performed_after_holdout": False,
            "feature_change_performed_after_holdout": False,
            "target_change_performed_after_holdout": False,
            "model_refit_performed_after_holdout": False,
            "probability_calibration_performed_after_holdout": False,
            "threshold_change_performed_after_holdout": False,
            "validation_reread_during_test": False,
            "test_rerun_authorized": False,
            "validation_rerun_authorized": False,
            "live_authorized": False,
            "shadow_authorized": False,
            "risk_engine_modified": False,
            "execution_integration_modified": False,
            "orders_sent": False,
        },
        "decision": {
            "status": "FINAL_HISTORICAL_RESEARCH_ACCEPTED",
            "historical_research_accepted": True,
            "live_authorized": False,
            "shadow_authorized": False,
            "test_consumed": True,
            "test_rerun_authorized": False,
            "validation_consumed": True,
            "validation_rerun_authorized": False,
            "current_frozen_lineage_may_be_tuned_from_holdouts": False,
            "next_action": (
                "BEGIN_PRODUCTION_PORTABILITY_AND_SHADOW_"
                "INFRASTRUCTURE_WITHOUT_MODEL_RETRAINING"
            ),
        },
    }

    return {
        "analysis_version": ANALYSIS_VERSION,
        "verdict_record": verdict_record,
        "verdict_fingerprint": {
            "canonicalization": "JSON_SORT_KEYS_COMPACT_UTF8_SHA256",
            "sha256": canonical_sha256(verdict_record),
        },
        "valid": True,
    }


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    artifact = build_verdict(base_dir)

    output_path = base_dir / OUTPUT_FILE
    output_path.write_text(
        json.dumps(
            artifact,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    verdict = artifact["verdict_record"]

    print(f"status={verdict['decision']['status']}")
    print(
        f"validation_accepted="
        f"{verdict['validation']['accepted']}"
    )
    print(
        f"test_accepted="
        f"{verdict['test']['accepted']}"
    )
    print(
        f"test_read_attempt_count="
        f"{verdict['test']['read_attempt_count']}"
    )
    print(
        f"test_permanently_consumed="
        f"{verdict['historical_research_verdict']['test_permanently_consumed']}"
    )
    print(
        f"validation_reread_during_test="
        f"{verdict['test']['validation_values_reread']}"
    )
    print(
        f"live_authorized="
        f"{verdict['decision']['live_authorized']}"
    )
    print(
        f"shadow_authorized="
        f"{verdict['decision']['shadow_authorized']}"
    )
    print(
        f"verdict_fingerprint="
        f"{artifact['verdict_fingerprint']['sha256']}"
    )
    print(f"wrote={OUTPUT_FILE}")


if __name__ == "__main__":
    main()