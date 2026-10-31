"""
===============================================================================
Module      : frozen_c04_forward_anchor_first_coordinator.py
Project     : PulseViper XAU AI
Purpose     : Gate 15D-C-B2D — Anchor-First Forward Persistence Coordinator
===============================================================================

Coordinates persistence of a formally eligible TRUE_FORWARD observation and
its prospective outcome anchor.

This module performs NO market acquisition and NO inference.

It accepts:
- an already-created frozen observation
- the SAME acquisition market-data snapshot used for that observation
- hardened append-only anchor / observation ledgers

Frozen transaction order:

    validate prospective eligibility
        ->
    capture anchor from SAME acquisition snapshot
        ->
    append anchor FIRST
        ->
    validate anchor ledger integrity
        ->
    append observation SECOND
        ->
    validate observation ledger integrity

Failure policy:

If anchor append succeeds but observation append fails:
- anchor is NEVER deleted
- anchor is NEVER rewritten
- anchor ledger is NEVER truncated
- anchor becomes an ORPHAN_PROSPECTIVE_ANCHOR audit artifact
- no formal scoring is authorized until the exact linked observation exists

This coordinator does NOT:
- initialize MT5
- fetch market data
- access future outcome rows
- mature outcomes
- calculate performance
- calculate PnL
- authorize live trading
- authorize execution
===============================================================================
"""

from __future__ import annotations

import dataclasses
import importlib
from typing import Any, Mapping

import pandas as pd


_anchor_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_anchor"
)

_eligibility_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_eligibility"
)

_atomic_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_runtime_atomic_ledgers"
)

_observer_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_shadow_observer"
)


# =============================================================================
# Authority
# =============================================================================

COORDINATOR_VERSION: str = (
    "FROZEN_C04_FORWARD_ANCHOR_FIRST_COORDINATOR_V1"
)

PERSISTENCE_ORDER: str = (
    "ANCHOR_FIRST_THEN_OBSERVATION"
)

ORPHAN_ANCHOR_POLICY: str = (
    "PRESERVE_IMMUTABLE_ANCHOR_IF_OBSERVATION_APPEND_FAILS"
)

EXPECTED_ANCHOR_VERSION: str = (
    "FROZEN_C04_FORWARD_OUTCOME_ANCHOR_V1"
)

EXPECTED_ATOMIC_LEDGER_AUTHORITY: str = (
    "FROZEN_C04_FORWARD_RUNTIME_ATOMIC_LEDGERS_V1"
)

EXPECTED_SOURCE_PROVENANCE: str = (
    "TRUE_FORWARD_OBSERVATION"
)

OUTCOME_MATURATION_AUTHORIZED: bool = False
PERFORMANCE_EVALUATION_AUTHORIZED: bool = False
PNL_EVALUATION_AUTHORIZED: bool = False
LIVE_AUTHORIZED: bool = False
EXECUTION_AUTHORIZED: bool = False


# =============================================================================
# Errors
# =============================================================================

class AnchorFirstCoordinatorError(
    RuntimeError
):
    pass


class ObservationNotProspectivelyEligibleError(
    AnchorFirstCoordinatorError
):
    pass


class AnchorPersistenceError(
    AnchorFirstCoordinatorError
):
    pass


class ObservationPersistenceAfterAnchorError(
    AnchorFirstCoordinatorError
):
    """
    Raised only after the anchor has already been successfully persisted.

    The successful anchor MUST remain in the anchor ledger.
    """

    def __init__(
        self,
        message: str,
        *,
        logical_observation_id: str,
        anchor_semantic_fingerprint: str,
    ) -> None:

        super().__init__(
            message
        )

        self.logical_observation_id = (
            logical_observation_id
        )

        self.anchor_semantic_fingerprint = (
            anchor_semantic_fingerprint
        )

        self.orphan_anchor_preserved = True


# =============================================================================
# Result
# =============================================================================

@dataclasses.dataclass(
    frozen=True
)
class AnchorFirstPersistenceResult:

    logical_observation_id: str

    anchor_semantic_fingerprint: str

    observation_semantic_fingerprint: str

    source_snapshot_id: str

    anchor_appended: bool

    anchor_idempotent_duplicate: bool

    observation_appended: bool

    observation_idempotent_duplicate: bool

    anchor_integrity_verified: bool

    observation_integrity_verified: bool

    persistence_order: str = (
        PERSISTENCE_ORDER
    )

    orphan_anchor: bool = False

    outcome_maturation_authorized: bool = False

    performance_evaluation_authorized: bool = False

    live_authorized: bool = False

    execution_authorized: bool = False


# =============================================================================
# Authority Verification
# =============================================================================

def verify_authorities() -> bool:

    if (
        _anchor_mod.ANCHOR_VERSION
        !=
        EXPECTED_ANCHOR_VERSION
    ):
        raise AnchorFirstCoordinatorError(
            "ANCHOR_VERSION_AUTHORITY_MISMATCH"
        )

    if (
        _atomic_mod.ATOMIC_LEDGER_AUTHORITY_VERSION
        !=
        EXPECTED_ATOMIC_LEDGER_AUTHORITY
    ):
        raise AnchorFirstCoordinatorError(
            "ATOMIC_LEDGER_AUTHORITY_MISMATCH"
        )

    if (
        _anchor_mod.FORMAL_MATURATION_REQUIRES_ANCHOR
        is not True
    ):
        raise AnchorFirstCoordinatorError(
            "FORMAL_MATURATION_ANCHOR_REQUIREMENT_NOT_ESTABLISHED"
        )

    if (
        OUTCOME_MATURATION_AUTHORIZED
        or
        PERFORMANCE_EVALUATION_AUTHORIZED
        or
        PNL_EVALUATION_AUTHORIZED
        or
        LIVE_AUTHORIZED
        or
        EXECUTION_AUTHORIZED
    ):
        raise AnchorFirstCoordinatorError(
            "COORDINATOR_AUTHORIZATION_BOUNDARY_VIOLATION"
        )

    return True


# =============================================================================
# Observation Document
# =============================================================================

def _observation_document(
    observation: Any,
    *,
    acquisition_authority: str,
) -> dict[str, Any]:

    if not isinstance(
        observation,
        _observer_mod.FrozenC04ObservationRecord,
    ):
        raise AnchorFirstCoordinatorError(
            "OBSERVATION_RECORD_TYPE_INVALID"
        )

    document = (
        observation.to_dict()
    )

    document[
        "acquisition_authority"
    ] = (
        acquisition_authority
    )

    return document


# =============================================================================
# Linkage Verification
# =============================================================================

def _verify_anchor_observation_linkage(
    *,
    observation: Any,
    anchor: Any,
) -> None:

    if (
        anchor.logical_observation_id
        !=
        observation.logical_observation_id
    ):
        raise AnchorFirstCoordinatorError(
            "ANCHOR_OBSERVATION_LOGICAL_ID_MISMATCH"
        )

    if (
        anchor.semantic_observation_fingerprint
        !=
        observation.semantic_record_fingerprint
    ):
        raise AnchorFirstCoordinatorError(
            "ANCHOR_OBSERVATION_SEMANTIC_FINGERPRINT_MISMATCH"
        )

    if (
        anchor.source_snapshot_id
        !=
        observation.source_snapshot_id
    ):
        raise AnchorFirstCoordinatorError(
            "ANCHOR_OBSERVATION_SOURCE_SNAPSHOT_MISMATCH"
        )

    if (
        anchor.canonical_instrument
        !=
        observation.canonical_instrument
    ):
        raise AnchorFirstCoordinatorError(
            "ANCHOR_OBSERVATION_INSTRUMENT_MISMATCH"
        )

    if (
        anchor.decision_time_utc
        !=
        observation.decision_time_utc
    ):
        raise AnchorFirstCoordinatorError(
            "ANCHOR_OBSERVATION_DECISION_TIME_MISMATCH"
        )

    if (
        anchor.feature_columns_sha256
        !=
        observation.feature_columns_sha256
    ):
        raise AnchorFirstCoordinatorError(
            "ANCHOR_OBSERVATION_FEATURE_HASH_MISMATCH"
        )

    if (
        anchor.model_sha256
        !=
        observation.model_sha256
    ):
        raise AnchorFirstCoordinatorError(
            "ANCHOR_OBSERVATION_MODEL_HASH_MISMATCH"
        )

    if (
        anchor.source_provenance
        !=
        EXPECTED_SOURCE_PROVENANCE
    ):
        raise AnchorFirstCoordinatorError(
            "ANCHOR_SOURCE_PROVENANCE_INVALID"
        )

    if (
        observation.source_provenance
        !=
        EXPECTED_SOURCE_PROVENANCE
    ):
        raise AnchorFirstCoordinatorError(
            "OBSERVATION_SOURCE_PROVENANCE_INVALID"
        )


# =============================================================================
# Coordinator
# =============================================================================

class FrozenC04ForwardAnchorFirstCoordinator:

    def __init__(
        self,
        *,
        anchor_ledger: Any,
        observation_ledger: Any,
    ) -> None:

        verify_authorities()

        if not isinstance(
            anchor_ledger,
            _atomic_mod.AtomicFrozenC04ForwardOutcomeAnchorLedger,
        ):
            raise AnchorFirstCoordinatorError(
                "ATOMIC_ANCHOR_LEDGER_REQUIRED"
            )

        if not isinstance(
            observation_ledger,
            _atomic_mod.AtomicFrozenC04ObservationLedger,
        ):
            raise AnchorFirstCoordinatorError(
                "ATOMIC_OBSERVATION_LEDGER_REQUIRED"
            )

        self._anchor_ledger = (
            anchor_ledger
        )

        self._observation_ledger = (
            observation_ledger
        )

    @property
    def anchor_ledger(
        self,
    ) -> Any:

        return self._anchor_ledger

    @property
    def observation_ledger(
        self,
    ) -> Any:

        return self._observation_ledger

    def persist(
        self,
        *,
        observation: Any,
        market_data: Mapping[
            str,
            pd.DataFrame,
        ],
        acquisition_authority: str,
    ) -> AnchorFirstPersistenceResult:

        verify_authorities()

        observation_document = (
            _observation_document(
                observation,
                acquisition_authority=(
                    acquisition_authority
                ),
            )
        )

        # ---------------------------------------------------------------------
        # 1. Prospective eligibility BEFORE any persistence.
        # ---------------------------------------------------------------------

        eligibility = (
            _eligibility_mod.assess_observation(
                observation_document
            )
        )

        if (
            eligibility
            .eligible_for_formal_maturation
            is not True
        ):
            raise ObservationNotProspectivelyEligibleError(
                (
                    "OBSERVATION_NOT_PROSPECTIVELY_ELIGIBLE:"
                    f"{eligibility.eligibility_reason}"
                )
            )

        if (
            eligibility.eligibility_reason
            !=
            "POST_CONTRACT_PROSPECTIVE_OBSERVATION"
        ):
            raise ObservationNotProspectivelyEligibleError(
                (
                    "UNEXPECTED_PROSPECTIVE_ELIGIBILITY_REASON:"
                    f"{eligibility.eligibility_reason}"
                )
            )

        # ---------------------------------------------------------------------
        # 2. Capture anchor from SAME acquisition snapshot.
        #
        # capture_anchor() itself proves:
        # - source snapshot canonical fingerprint
        # - exact decision M5 candle
        # - no future M5 rows
        # - correct feature/model/instrument/provenance authorities
        # - correct decision close / ATR14
        # ---------------------------------------------------------------------

        anchor = (
            _anchor_mod.capture_anchor(
                observation=(
                    observation_document
                ),
                market_data=(
                    market_data
                ),
            )
        )

        _verify_anchor_observation_linkage(
            observation=(
                observation
            ),
            anchor=(
                anchor
            ),
        )

        # ---------------------------------------------------------------------
        # 3. ANCHOR FIRST.
        # ---------------------------------------------------------------------

        try:

            anchor_result = (
                self._anchor_ledger.append(
                    anchor
                )
            )

        except Exception as exc:

            raise AnchorPersistenceError(
                (
                    "ANCHOR_PERSISTENCE_FAILED:"
                    f"{type(exc).__name__}:"
                    f"{exc}"
                )
            ) from exc

        if not (
            anchor_result.appended
            or
            anchor_result.is_duplicate
        ):
            raise AnchorPersistenceError(
                "ANCHOR_APPEND_RESULT_INVALID"
            )

        if (
            self._anchor_ledger
            .validate_integrity()
            is not True
        ):
            raise AnchorPersistenceError(
                "ANCHOR_LEDGER_INTEGRITY_FAILED"
            )

        # ---------------------------------------------------------------------
        # 4. OBSERVATION SECOND.
        #
        # If this block fails, anchor remains immutable on disk.
        # There is deliberately NO rollback.
        # ---------------------------------------------------------------------

        try:

            observation_result = (
                self._observation_ledger
                .append(
                    observation
                )
            )

        except Exception as exc:

            raise ObservationPersistenceAfterAnchorError(
                (
                    "OBSERVATION_PERSISTENCE_FAILED_AFTER_ANCHOR:"
                    f"{type(exc).__name__}:"
                    f"{exc}"
                ),
                logical_observation_id=(
                    anchor.logical_observation_id
                ),
                anchor_semantic_fingerprint=(
                    anchor.semantic_fingerprint()
                ),
            ) from exc

        if not (
            observation_result.appended
            or
            observation_result.is_duplicate
        ):
            raise ObservationPersistenceAfterAnchorError(
                "OBSERVATION_APPEND_RESULT_INVALID_AFTER_ANCHOR",
                logical_observation_id=(
                    anchor.logical_observation_id
                ),
                anchor_semantic_fingerprint=(
                    anchor.semantic_fingerprint()
                ),
            )

        try:

            observation_integrity = (
                self._observation_ledger
                .validate_integrity()
            )

        except Exception as exc:

            raise ObservationPersistenceAfterAnchorError(
                (
                    "OBSERVATION_LEDGER_INTEGRITY_FAILED_AFTER_ANCHOR:"
                    f"{type(exc).__name__}:"
                    f"{exc}"
                ),
                logical_observation_id=(
                    anchor.logical_observation_id
                ),
                anchor_semantic_fingerprint=(
                    anchor.semantic_fingerprint()
                ),
            ) from exc

        if (
            observation_integrity
            is not True
        ):
            raise ObservationPersistenceAfterAnchorError(
                "OBSERVATION_LEDGER_INTEGRITY_FALSE_AFTER_ANCHOR",
                logical_observation_id=(
                    anchor.logical_observation_id
                ),
                anchor_semantic_fingerprint=(
                    anchor.semantic_fingerprint()
                ),
            )

        # ---------------------------------------------------------------------
        # 5. Completed anchor-first persistence only.
        #
        # NO maturation.
        # NO performance.
        # ---------------------------------------------------------------------

        return AnchorFirstPersistenceResult(
            logical_observation_id=(
                observation.logical_observation_id
            ),

            anchor_semantic_fingerprint=(
                anchor.semantic_fingerprint()
            ),

            observation_semantic_fingerprint=(
                observation.semantic_record_fingerprint
            ),

            source_snapshot_id=(
                observation.source_snapshot_id
            ),

            anchor_appended=(
                bool(
                    anchor_result.appended
                )
            ),

            anchor_idempotent_duplicate=(
                bool(
                    anchor_result.is_duplicate
                )
            ),

            observation_appended=(
                bool(
                    observation_result.appended
                )
            ),

            observation_idempotent_duplicate=(
                bool(
                    observation_result.is_duplicate
                )
            ),

            anchor_integrity_verified=True,

            observation_integrity_verified=True,

            orphan_anchor=False,

            outcome_maturation_authorized=False,

            performance_evaluation_authorized=False,

            live_authorized=False,

            execution_authorized=False,
        )