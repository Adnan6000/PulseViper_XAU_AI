from __future__ import annotations

import importlib
from typing import Any

import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_eligibility"
)


def _observation(
    decision_time: str,
) -> dict[str, Any]:

    return {
        "logical_observation_id": (
            "a" * 64
        ),
        "decision_time_utc": (
            decision_time
        ),
        "canonical_instrument": "XAUUSD",
        "source_provenance": (
            "TRUE_FORWARD_OBSERVATION"
        ),
        "is_true_forward_eligible": True,
        "feature_columns_sha256": (
            "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
        ),
        "model_sha256": (
            "48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769"
        ),
        "live_authorized": False,
        "execution_authorized": False,
    }


def test_01_authorities_pass() -> None:
    assert module.verify_authorities() is True


def test_02_activation_authority_is_frozen() -> None:
    assert (
        module.GATE_15C_EVIDENCE_AUTHORITY_COMMIT
        ==
        "59f5b6815f0c8d0a51725aa5123812595566b530"
    )

    assert (
        module.GATE_15C_ACTIVATION_UTC
        ==
        "2026-09-28T11:16:59Z"
    )


def test_03_first_existing_observation_is_pre_contract() -> None:

    decision = module.assess_observation(
        _observation(
            "2026-09-28T10:15:00Z"
        )
    )

    assert (
        decision.eligible_for_formal_maturation
        is False
    )

    assert (
        decision.eligibility_reason
        ==
        "PRE_CONTRACT_OBSERVATION"
    )


def test_04_exact_activation_time_is_ineligible() -> None:

    decision = module.assess_observation(
        _observation(
            "2026-09-28T11:16:59Z"
        )
    )

    assert (
        decision.eligible_for_formal_maturation
        is False
    )


def test_05_post_activation_observation_is_eligible() -> None:

    decision = module.assess_observation(
        _observation(
            "2026-09-28T11:20:00Z"
        )
    )

    assert (
        decision.eligible_for_formal_maturation
        is True
    )

    assert (
        decision.eligibility_reason
        ==
        "POST_CONTRACT_PROSPECTIVE_OBSERVATION"
    )


def test_06_non_true_forward_is_rejected() -> None:

    observation = _observation(
        "2026-09-28T11:20:00Z"
    )

    observation[
        "source_provenance"
    ] = "SYNTHETIC_ENGINEERING"

    with pytest.raises(
        module.ForwardOutcomeEligibilityError,
        match="NON_TRUE_FORWARD_OBSERVATION",
    ):
        module.assess_observation(
            observation
        )


def test_07_feature_authority_mismatch_rejected() -> None:

    observation = _observation(
        "2026-09-28T11:20:00Z"
    )

    observation[
        "feature_columns_sha256"
    ] = "b" * 64

    with pytest.raises(
        module.ForwardOutcomeEligibilityError,
        match="FEATURE_COLUMNS_SHA256_MISMATCH",
    ):
        module.assess_observation(
            observation
        )


def test_08_model_authority_mismatch_rejected() -> None:

    observation = _observation(
        "2026-09-28T11:20:00Z"
    )

    observation[
        "model_sha256"
    ] = "c" * 64

    with pytest.raises(
        module.ForwardOutcomeEligibilityError,
        match="MODEL_SHA256_MISMATCH",
    ):
        module.assess_observation(
            observation
        )


def test_09_live_authorization_rejected() -> None:

    observation = _observation(
        "2026-09-28T11:20:00Z"
    )

    observation[
        "live_authorized"
    ] = True

    with pytest.raises(
        module.ForwardOutcomeEligibilityError,
        match="OBSERVATION_LIVE_AUTHORIZATION_VIOLATION",
    ):
        module.assess_observation(
            observation
        )


def test_10_execution_authorization_rejected() -> None:

    observation = _observation(
        "2026-09-28T11:20:00Z"
    )

    observation[
        "execution_authorized"
    ] = True

    with pytest.raises(
        module.ForwardOutcomeEligibilityError,
        match="OBSERVATION_EXECUTION_AUTHORIZATION_VIOLATION",
    ):
        module.assess_observation(
            observation
        )


def test_11_naive_timestamp_rejected() -> None:

    with pytest.raises(
        module.ForwardOutcomeEligibilityError,
        match="DECISION_TIME_MUST_BE_TIMEZONE_AWARE",
    ):
        module.assess_observation(
            _observation(
                "2026-09-28 11:20:00"
            )
        )


def test_12_performance_remains_blocked() -> None:

    assert (
        module.PERFORMANCE_EVALUATION_AUTHORIZED
        is False
    )

    assert (
        module.OUTCOME_MATURATION_AUTHORIZED
        is False
    )

    assert (
        module.MT5_ACCESS_AUTHORIZED
        is False
    )

    assert module.LIVE_AUTHORIZED is False
    assert module.EXECUTION_AUTHORIZED is False

    with pytest.raises(
        module.ForwardOutcomeEligibilityError,
        match="FORWARD_PERFORMANCE_EVALUATION_NOT_AUTHORIZED",
    ):
        module.assert_performance_evaluation_blocked()