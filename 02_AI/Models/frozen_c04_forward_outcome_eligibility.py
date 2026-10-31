"""
===============================================================================
Module      : frozen_c04_forward_outcome_eligibility.py
Project     : PulseViper XAU AI
Purpose     : Gate 15D-A — Prospective Forward Outcome Eligibility Authority
===============================================================================

This module establishes the prospective eligibility boundary for formal
forward-outcome maturation.

It does NOT:
- acquire market data
- access MT5
- calculate an outcome
- calculate accuracy / win rate / PnL / drawdown
- mutate the observation ledger
- authorize execution or live trading
===============================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
import importlib
from typing import Any, Mapping, cast

import pandas as pd


_outcome = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_contract"
)

_features = importlib.import_module(
    "02_AI.Features.portable_feature_contract"
)


ELIGIBILITY_VERSION: str = (
    "FROZEN_C04_FORWARD_OUTCOME_ELIGIBILITY_V1"
)

GATE_15C_EVIDENCE_AUTHORITY_COMMIT: str = (
    "59f5b6815f0c8d0a51725aa5123812595566b530"
)

GATE_15C_ACTIVATION_UTC: str = (
    "2026-09-28T11:16:59Z"
)

EXPECTED_OUTCOME_CONTRACT_FINGERPRINT_SHA256: str = (
    "01fe52a2f068fcc8fb2fc5b89dd7e19dc974fc2d967cfb791e75c3415804ce87"
)

EXPECTED_FEATURE_COLUMNS_SHA256: str = str(
    _features.EXPECTED_FEATURE_COLUMNS_SHA256
)

EXPECTED_MODEL_SHA256: str = str(
    _features.FROZEN_MODEL_SHA256
)

EXPECTED_CANONICAL_INSTRUMENT: str = "XAUUSD"

EXPECTED_SOURCE_PROVENANCE: str = (
    "TRUE_FORWARD_OBSERVATION"
)

PRE_CONTRACT_POLICY: str = (
    "RETAIN_FOR_PIPELINE_AUDIT_EXCLUDE_FROM_FORMAL_FORWARD_PERFORMANCE"
)

PERFORMANCE_EVALUATION_AUTHORIZED: bool = False
OUTCOME_MATURATION_AUTHORIZED: bool = False
MT5_ACCESS_AUTHORIZED: bool = False
LIVE_AUTHORIZED: bool = False
EXECUTION_AUTHORIZED: bool = False


class ForwardOutcomeEligibilityError(
    RuntimeError
):
    pass


@dataclass(frozen=True)
class ForwardOutcomeEligibilityDecision:
    logical_observation_id: str
    decision_time_utc: str

    eligible_for_formal_maturation: bool
    eligibility_reason: str

    activation_utc: str = (
        GATE_15C_ACTIVATION_UTC
    )

    activation_authority_commit: str = (
        GATE_15C_EVIDENCE_AUTHORITY_COMMIT
    )

    outcome_contract_fingerprint_sha256: str = (
        EXPECTED_OUTCOME_CONTRACT_FINGERPRINT_SHA256
    )

    performance_evaluation_authorized: bool = False
    live_authorized: bool = False
    execution_authorized: bool = False

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "logical_observation_id": (
                self.logical_observation_id
            ),
            "decision_time_utc": (
                self.decision_time_utc
            ),
            "eligible_for_formal_maturation": (
                self.eligible_for_formal_maturation
            ),
            "eligibility_reason": (
                self.eligibility_reason
            ),
            "activation_utc": (
                self.activation_utc
            ),
            "activation_authority_commit": (
                self.activation_authority_commit
            ),
            "outcome_contract_fingerprint_sha256": (
                self.outcome_contract_fingerprint_sha256
            ),
            "performance_evaluation_authorized": (
                self.performance_evaluation_authorized
            ),
            "live_authorized": (
                self.live_authorized
            ),
            "execution_authorized": (
                self.execution_authorized
            ),
        }


def _utc_timestamp(
    value: Any,
) -> pd.Timestamp:

    try:
        timestamp = pd.Timestamp(
            value
        )

    except Exception as exc:
        raise ForwardOutcomeEligibilityError(
            "INVALID_DECISION_TIME"
        ) from exc

    if timestamp is pd.NaT:
        raise ForwardOutcomeEligibilityError(
            "INVALID_DECISION_TIME"
        )

    timestamp = cast(
        pd.Timestamp,
        timestamp,
    )

    if timestamp.tzinfo is None:
        raise ForwardOutcomeEligibilityError(
            "DECISION_TIME_MUST_BE_TIMEZONE_AWARE"
        )

    converted = timestamp.tz_convert(
        "UTC"
    )

    if converted is pd.NaT:
        raise ForwardOutcomeEligibilityError(
            "INVALID_DECISION_TIME_AFTER_UTC_CONVERSION"
        )

    return cast(
        pd.Timestamp,
        converted,
    )


def _require_string(
    document: Mapping[str, Any],
    key: str,
) -> str:

    value = document.get(
        key
    )

    if not isinstance(
        value,
        str,
    ):
        raise ForwardOutcomeEligibilityError(
            f"REQUIRED_STRING_MISSING:{key}"
        )

    value = value.strip()

    if not value:
        raise ForwardOutcomeEligibilityError(
            f"REQUIRED_STRING_EMPTY:{key}"
        )

    return value


def verify_authorities() -> bool:

    if (
        _outcome.compute_contract_fingerprint()
        !=
        EXPECTED_OUTCOME_CONTRACT_FINGERPRINT_SHA256
    ):
        raise ForwardOutcomeEligibilityError(
            "OUTCOME_CONTRACT_FINGERPRINT_MISMATCH"
        )

    if (
        EXPECTED_FEATURE_COLUMNS_SHA256
        !=
        "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
    ):
        raise ForwardOutcomeEligibilityError(
            "FEATURE_AUTHORITY_MISMATCH"
        )

    if (
        EXPECTED_MODEL_SHA256
        !=
        "48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769"
    ):
        raise ForwardOutcomeEligibilityError(
            "MODEL_AUTHORITY_MISMATCH"
        )

    return True


def assess_observation(
    observation: Mapping[str, Any],
) -> ForwardOutcomeEligibilityDecision:

    verify_authorities()

    logical_id = _require_string(
        observation,
        "logical_observation_id",
    )

    decision_time = _require_string(
        observation,
        "decision_time_utc",
    )

    canonical_instrument = _require_string(
        observation,
        "canonical_instrument",
    )

    source_provenance = _require_string(
        observation,
        "source_provenance",
    )

    feature_sha = _require_string(
        observation,
        "feature_columns_sha256",
    )

    model_sha = _require_string(
        observation,
        "model_sha256",
    )

    if (
        canonical_instrument
        !=
        EXPECTED_CANONICAL_INSTRUMENT
    ):
        raise ForwardOutcomeEligibilityError(
            "CANONICAL_INSTRUMENT_MISMATCH"
        )

    if (
        source_provenance
        !=
        EXPECTED_SOURCE_PROVENANCE
    ):
        raise ForwardOutcomeEligibilityError(
            "NON_TRUE_FORWARD_OBSERVATION"
        )

    if (
        observation.get(
            "is_true_forward_eligible"
        )
        is not True
    ):
        raise ForwardOutcomeEligibilityError(
            "OBSERVATION_NOT_TRUE_FORWARD_ELIGIBLE"
        )

    if (
        feature_sha
        !=
        EXPECTED_FEATURE_COLUMNS_SHA256
    ):
        raise ForwardOutcomeEligibilityError(
            "FEATURE_COLUMNS_SHA256_MISMATCH"
        )

    if (
        model_sha
        !=
        EXPECTED_MODEL_SHA256
    ):
        raise ForwardOutcomeEligibilityError(
            "MODEL_SHA256_MISMATCH"
        )

    if (
        observation.get(
            "live_authorized"
        )
        is not False
    ):
        raise ForwardOutcomeEligibilityError(
            "OBSERVATION_LIVE_AUTHORIZATION_VIOLATION"
        )

    if (
        observation.get(
            "execution_authorized"
        )
        is not False
    ):
        raise ForwardOutcomeEligibilityError(
            "OBSERVATION_EXECUTION_AUTHORIZATION_VIOLATION"
        )

    decision_ts = _utc_timestamp(
        decision_time
    )

    activation_ts = _utc_timestamp(
        GATE_15C_ACTIVATION_UTC
    )

    if (
        decision_ts
        <=
        activation_ts
    ):
        return (
            ForwardOutcomeEligibilityDecision(
                logical_observation_id=(
                    logical_id
                ),
                decision_time_utc=(
                    decision_time
                ),
                eligible_for_formal_maturation=False,
                eligibility_reason=(
                    "PRE_CONTRACT_OBSERVATION"
                ),
            )
        )

    return (
        ForwardOutcomeEligibilityDecision(
            logical_observation_id=(
                logical_id
            ),
            decision_time_utc=(
                decision_time
            ),
            eligible_for_formal_maturation=True,
            eligibility_reason=(
                "POST_CONTRACT_PROSPECTIVE_OBSERVATION"
            ),
        )
    )


def assert_performance_evaluation_blocked() -> None:

    if PERFORMANCE_EVALUATION_AUTHORIZED:
        raise ForwardOutcomeEligibilityError(
            "PERFORMANCE_EVALUATION_UNEXPECTEDLY_AUTHORIZED"
        )

    raise ForwardOutcomeEligibilityError(
        "FORWARD_PERFORMANCE_EVALUATION_NOT_AUTHORIZED_IN_GATE_15D_A"
    )