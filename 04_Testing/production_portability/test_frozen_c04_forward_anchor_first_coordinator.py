from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest


pytestmark = pytest.mark.offline


coordinator_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_anchor_first_coordinator"
)

atomic_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_runtime_atomic_ledgers"
)

anchor_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_anchor"
)

observer_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_shadow_observer"
)

acquisition_mod: Any = importlib.import_module(
    "02_AI.Adapters.mt5_read_only_forward_acquisition_adapter"
)


DECISION_TIME: str = "2026-09-28T12:00:00Z"

ACQUISITION_AUTHORITY: str = (
    "MT5ReadOnlyForwardAcquisitionAdapter:2.1.0"
)


def _m5_frame() -> pd.DataFrame:

    decision_time = pd.Timestamp(
        DECISION_TIME
    )

    decision_open = (
        decision_time
        -
        pd.Timedelta(
            minutes=5
        )
    )

    start = (
        decision_open
        -
        pd.Timedelta(
            minutes=(
                249
                *
                5
            )
        )
    )

    times = pd.date_range(
        start=start,
        periods=250,
        freq="5min",
        tz="UTC",
    )

    close = (
        2000.0
        +
        np.arange(
            250,
            dtype=float,
        )
        *
        0.01
    )

    return pd.DataFrame(
        {
            "time": times,
            "open": close,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "tick_volume": 100,
        }
    )


def _market_data() -> dict[str, pd.DataFrame]:

    return {
        "M5": _m5_frame(),
    }


def _observation(
    market_data: dict[str, pd.DataFrame],
    *,
    decision_time: str = DECISION_TIME,
) -> Any:

    snapshot_id = (
        acquisition_mod
        .compute_canonical_snapshot_id(
            market_data
        )
    )

    logical_id = (
        observer_mod
        .compute_logical_observation_id(
            schema_version=(
                observer_mod
                .OBSERVER_SCHEMA_VERSION
            ),

            canonical_instrument=(
                "XAUUSD"
            ),

            decision_time_utc=(
                decision_time
            ),

            feature_columns_sha256=(
                observer_mod
                .EXPECTED_FEATURE_COLUMNS_SHA256
            ),

            model_sha256=(
                observer_mod
                .FROZEN_MODEL_SHA256
            ),
        )
    )

    probability_short = 0.10
    probability_no_trade = 0.20
    probability_long = 0.70

    predicted_class = 1
    winning_probability = 0.70

    semantic_fp = (
        observer_mod
        .compute_semantic_record_fingerprint(
            logical_observation_id=(
                logical_id
            ),

            source_snapshot_id=(
                snapshot_id
            ),

            source_provenance=(
                "TRUE_FORWARD_OBSERVATION"
            ),

            probability_short=(
                probability_short
            ),

            probability_no_trade=(
                probability_no_trade
            ),

            probability_long=(
                probability_long
            ),

            predicted_class=(
                predicted_class
            ),

            winning_probability=(
                winning_probability
            ),

            feature_count=(
                observer_mod
                .EXPECTED_FEATURE_COUNT
            ),

            feature_columns_sha256=(
                observer_mod
                .EXPECTED_FEATURE_COLUMNS_SHA256
            ),

            model_sha256=(
                observer_mod
                .FROZEN_MODEL_SHA256
            ),
        )
    )

    return (
        observer_mod
        .FrozenC04ObservationRecord(
            logical_observation_id=(
                logical_id
            ),

            semantic_record_fingerprint=(
                semantic_fp
            ),

            observed_at_utc=(
                "2026-09-28T12:00:30Z"
            ),

            decision_time_utc=(
                decision_time
            ),

            canonical_instrument=(
                "XAUUSD"
            ),

            broker_symbol=(
                "XAUUSDm"
            ),

            feature_count=(
                observer_mod
                .EXPECTED_FEATURE_COUNT
            ),

            feature_columns_sha256=(
                observer_mod
                .EXPECTED_FEATURE_COLUMNS_SHA256
            ),

            model_sha256=(
                observer_mod
                .FROZEN_MODEL_SHA256
            ),

            model_class=(
                observer_mod
                .EXPECTED_MODEL_CLASS_NAME
            ),

            class_order=(
                observer_mod
                .FROZEN_MODEL_CLASSES
            ),

            probability_short=(
                probability_short
            ),

            probability_no_trade=(
                probability_no_trade
            ),

            probability_long=(
                probability_long
            ),

            predicted_class=(
                predicted_class
            ),

            predicted_label=(
                "LONG"
            ),

            winning_probability=(
                winning_probability
            ),

            source_snapshot_id=(
                snapshot_id
            ),

            source_provenance=(
                "TRUE_FORWARD_OBSERVATION"
            ),

            feature_generation_status=(
                "VALIDATED_GATE_13"
            ),

            inference_status=(
                "SUCCESS_GATE_14"
            ),

            observation_status=(
                "RECORDED"
            ),

            is_true_forward_eligible=True,

            live_authorized=False,

            execution_authorized=False,
        )
    )


def _ledgers(
    tmp_path: Path,
) -> tuple[Any, Any]:

    anchor_ledger = (
        atomic_mod
        .AtomicFrozenC04ForwardOutcomeAnchorLedger(
            tmp_path
            /
            "anchors.jsonl",

            duplicate_handling=(
                anchor_mod
                .AnchorDuplicateHandling
                .IDEMPOTENT_IGNORE
            ),
        )
    )

    observation_ledger = (
        atomic_mod
        .AtomicFrozenC04ObservationLedger(
            tmp_path
            /
            "observations.jsonl",

            duplicate_handling=(
                observer_mod
                .DuplicateHandling
                .IDEMPOTENT_IGNORE
            ),
        )
    )

    return (
        anchor_ledger,
        observation_ledger,
    )


class RecordingAnchorLedger(
    atomic_mod.AtomicFrozenC04ForwardOutcomeAnchorLedger
):

    def __init__(
        self,
        path: Path,
        events: list[str],
    ) -> None:

        super().__init__(
            path,
            duplicate_handling=(
                anchor_mod
                .AnchorDuplicateHandling
                .IDEMPOTENT_IGNORE
            ),
        )

        self._events = (
            events
        )

    def append(
        self,
        anchor: Any,
    ) -> Any:

        self._events.append(
            "ANCHOR_APPEND"
        )

        return super().append(
            anchor
        )


class RecordingObservationLedger(
    atomic_mod.AtomicFrozenC04ObservationLedger
):

    def __init__(
        self,
        path: Path,
        events: list[str],
    ) -> None:

        super().__init__(
            path,
            duplicate_handling=(
                observer_mod
                .DuplicateHandling
                .IDEMPOTENT_IGNORE
            ),
        )

        self._events = (
            events
        )

    def append(
        self,
        observation: Any,
    ) -> Any:

        self._events.append(
            "OBSERVATION_APPEND"
        )

        return super().append(
            observation
        )


class FailingObservationLedger(
    atomic_mod.AtomicFrozenC04ObservationLedger
):

    def append(
        self,
        observation: Any,
    ) -> Any:

        raise RuntimeError(
            "INTENTIONAL_OBSERVATION_APPEND_FAILURE"
        )


class FailingAnchorLedger(
    atomic_mod.AtomicFrozenC04ForwardOutcomeAnchorLedger
):

    def append(
        self,
        anchor: Any,
    ) -> Any:

        raise RuntimeError(
            "INTENTIONAL_ANCHOR_APPEND_FAILURE"
        )


def test_01_authorities_pass() -> None:

    assert (
        coordinator_mod.verify_authorities()
        is True
    )


def test_02_coordinator_versions_and_policies() -> None:

    assert (
        coordinator_mod.COORDINATOR_VERSION
        ==
        "FROZEN_C04_FORWARD_ANCHOR_FIRST_COORDINATOR_V1"
    )

    assert (
        coordinator_mod.PERSISTENCE_ORDER
        ==
        "ANCHOR_FIRST_THEN_OBSERVATION"
    )

    assert (
        coordinator_mod.ORPHAN_ANCHOR_POLICY
        ==
        "PRESERVE_IMMUTABLE_ANCHOR_IF_OBSERVATION_APPEND_FAILS"
    )


def test_03_valid_same_snapshot_pair_persists(
    tmp_path: Path,
) -> None:

    market_data = (
        _market_data()
    )

    observation = (
        _observation(
            market_data
        )
    )

    (
        anchor_ledger,
        observation_ledger,
    ) = _ledgers(
        tmp_path
    )

    coordinator = (
        coordinator_mod
        .FrozenC04ForwardAnchorFirstCoordinator(
            anchor_ledger=(
                anchor_ledger
            ),

            observation_ledger=(
                observation_ledger
            ),
        )
    )

    result = coordinator.persist(
        observation=(
            observation
        ),

        market_data=(
            market_data
        ),

        acquisition_authority=(
            ACQUISITION_AUTHORITY
        ),
    )

    assert (
        result.anchor_appended
        is True
    )

    assert (
        result.observation_appended
        is True
    )

    assert (
        result.anchor_idempotent_duplicate
        is False
    )

    assert (
        result.observation_idempotent_duplicate
        is False
    )

    assert (
        result.orphan_anchor
        is False
    )

    assert (
        anchor_ledger.count()
        ==
        1
    )

    assert (
        observation_ledger.count()
        ==
        1
    )


def test_04_anchor_is_persisted_before_observation(
    tmp_path: Path,
) -> None:

    events: list[str] = []

    market_data = (
        _market_data()
    )

    observation = (
        _observation(
            market_data
        )
    )

    anchor_ledger = (
        RecordingAnchorLedger(
            tmp_path
            /
            "anchors.jsonl",
            events,
        )
    )

    observation_ledger = (
        RecordingObservationLedger(
            tmp_path
            /
            "observations.jsonl",
            events,
        )
    )

    coordinator = (
        coordinator_mod
        .FrozenC04ForwardAnchorFirstCoordinator(
            anchor_ledger=(
                anchor_ledger
            ),

            observation_ledger=(
                observation_ledger
            ),
        )
    )

    coordinator.persist(
        observation=(
            observation
        ),

        market_data=(
            market_data
        ),

        acquisition_authority=(
            ACQUISITION_AUTHORITY
        ),
    )

    assert events == [
        "ANCHOR_APPEND",
        "OBSERVATION_APPEND",
    ]


def test_05_source_snapshot_mismatch_fails_before_persistence(
    tmp_path: Path,
) -> None:

    market_data = (
        _market_data()
    )

    observation = (
        _observation(
            market_data
        )
    )

    tampered_market = {
        "M5": (
            market_data[
                "M5"
            ].copy()
        )
    }

    tampered_market[
        "M5"
    ].loc[
        tampered_market[
            "M5"
        ].index[
            -1
        ],
        "close",
    ] += 0.5

    (
        anchor_ledger,
        observation_ledger,
    ) = _ledgers(
        tmp_path
    )

    coordinator = (
        coordinator_mod
        .FrozenC04ForwardAnchorFirstCoordinator(
            anchor_ledger=(
                anchor_ledger
            ),

            observation_ledger=(
                observation_ledger
            ),
        )
    )

    with pytest.raises(
        anchor_mod.InvalidAnchorError,
        match="SOURCE_SNAPSHOT_ID_MISMATCH",
    ):

        coordinator.persist(
            observation=(
                observation
            ),

            market_data=(
                tampered_market
            ),

            acquisition_authority=(
                ACQUISITION_AUTHORITY
            ),
        )

    assert (
        anchor_ledger.count()
        ==
        0
    )

    assert (
        observation_ledger.count()
        ==
        0
    )


def test_06_future_m5_row_rejected_before_persistence(
    tmp_path: Path,
) -> None:

    market_data = (
        _market_data()
    )

    extended = (
        market_data[
            "M5"
        ].copy()
    )

    future_row = (
        extended.iloc[
            -1
        ].copy()
    )

    future_row[
        "time"
    ] = (
        pd.Timestamp(
            future_row[
                "time"
            ]
        )
        +
        pd.Timedelta(
            minutes=5
        )
    )

    extended = pd.concat(
        [
            extended,
            pd.DataFrame(
                [
                    future_row
                ]
            ),
        ],
        ignore_index=True,
    )

    future_market = {
        "M5": extended,
    }

    observation = (
        _observation(
            future_market
        )
    )

    (
        anchor_ledger,
        observation_ledger,
    ) = _ledgers(
        tmp_path
    )

    coordinator = (
        coordinator_mod
        .FrozenC04ForwardAnchorFirstCoordinator(
            anchor_ledger=(
                anchor_ledger
            ),

            observation_ledger=(
                observation_ledger
            ),
        )
    )

    with pytest.raises(
        anchor_mod.InvalidAnchorError,
        match="SNAPSHOT_NOT_TERMINATED_AT_DECISION_BAR",
    ):

        coordinator.persist(
            observation=(
                observation
            ),

            market_data=(
                future_market
            ),

            acquisition_authority=(
                ACQUISITION_AUTHORITY
            ),
        )

    assert (
        anchor_ledger.count()
        ==
        0
    )

    assert (
        observation_ledger.count()
        ==
        0
    )


def test_07_pre_contract_observation_fails_before_anchor_append(
    tmp_path: Path,
) -> None:

    market_data = (
        _market_data()
    )

    observation = (
        _observation(
            market_data,
            decision_time=(
                "2026-09-28T10:15:00Z"
            ),
        )
    )

    (
        anchor_ledger,
        observation_ledger,
    ) = _ledgers(
        tmp_path
    )

    coordinator = (
        coordinator_mod
        .FrozenC04ForwardAnchorFirstCoordinator(
            anchor_ledger=(
                anchor_ledger
            ),

            observation_ledger=(
                observation_ledger
            ),
        )
    )

    with pytest.raises(
        coordinator_mod.ObservationNotProspectivelyEligibleError,
        match="PRE_CONTRACT_OBSERVATION",
    ):

        coordinator.persist(
            observation=(
                observation
            ),

            market_data=(
                market_data
            ),

            acquisition_authority=(
                ACQUISITION_AUTHORITY
            ),
        )

    assert (
        anchor_ledger.count()
        ==
        0
    )

    assert (
        observation_ledger.count()
        ==
        0
    )


def test_08_anchor_append_failure_prevents_observation_append(
    tmp_path: Path,
) -> None:

    market_data = (
        _market_data()
    )

    observation = (
        _observation(
            market_data
        )
    )

    anchor_ledger = (
        FailingAnchorLedger(
            tmp_path
            /
            "anchors.jsonl",

            duplicate_handling=(
                anchor_mod
                .AnchorDuplicateHandling
                .IDEMPOTENT_IGNORE
            ),
        )
    )

    observation_ledger = (
        atomic_mod
        .AtomicFrozenC04ObservationLedger(
            tmp_path
            /
            "observations.jsonl",

            duplicate_handling=(
                observer_mod
                .DuplicateHandling
                .IDEMPOTENT_IGNORE
            ),
        )
    )

    coordinator = (
        coordinator_mod
        .FrozenC04ForwardAnchorFirstCoordinator(
            anchor_ledger=(
                anchor_ledger
            ),

            observation_ledger=(
                observation_ledger
            ),
        )
    )

    with pytest.raises(
        coordinator_mod.AnchorPersistenceError,
        match="ANCHOR_PERSISTENCE_FAILED",
    ):

        coordinator.persist(
            observation=(
                observation
            ),

            market_data=(
                market_data
            ),

            acquisition_authority=(
                ACQUISITION_AUTHORITY
            ),
        )

    assert (
        observation_ledger.count()
        ==
        0
    )


def test_09_observation_failure_preserves_orphan_anchor(
    tmp_path: Path,
) -> None:

    market_data = (
        _market_data()
    )

    observation = (
        _observation(
            market_data
        )
    )

    anchor_path = (
        tmp_path
        /
        "anchors.jsonl"
    )

    anchor_ledger = (
        atomic_mod
        .AtomicFrozenC04ForwardOutcomeAnchorLedger(
            anchor_path,

            duplicate_handling=(
                anchor_mod
                .AnchorDuplicateHandling
                .IDEMPOTENT_IGNORE
            ),
        )
    )

    observation_ledger = (
        FailingObservationLedger(
            tmp_path
            /
            "observations.jsonl",

            duplicate_handling=(
                observer_mod
                .DuplicateHandling
                .IDEMPOTENT_IGNORE
            ),
        )
    )

    coordinator = (
        coordinator_mod
        .FrozenC04ForwardAnchorFirstCoordinator(
            anchor_ledger=(
                anchor_ledger
            ),

            observation_ledger=(
                observation_ledger
            ),
        )
    )

    with pytest.raises(
        coordinator_mod.ObservationPersistenceAfterAnchorError
    ) as exc_info:

        coordinator.persist(
            observation=(
                observation
            ),

            market_data=(
                market_data
            ),

            acquisition_authority=(
                ACQUISITION_AUTHORITY
            ),
        )

    error = (
        exc_info.value
    )

    assert (
        error.orphan_anchor_preserved
        is True
    )

    assert (
        error.logical_observation_id
        ==
        observation.logical_observation_id
    )

    assert (
        anchor_ledger.validate_integrity()
        is True
    )

    assert (
        anchor_ledger.count()
        ==
        1
    )

    assert (
        anchor_path.is_file()
        is True
    )

    persisted = (
        anchor_ledger.read_all()
    )

    assert (
        len(
            persisted
        )
        ==
        1
    )

    assert (
        persisted[
            0
        ].logical_observation_id
        ==
        observation.logical_observation_id
    )


def test_10_exact_retry_is_idempotent(
    tmp_path: Path,
) -> None:

    market_data = (
        _market_data()
    )

    observation = (
        _observation(
            market_data
        )
    )

    (
        anchor_ledger,
        observation_ledger,
    ) = _ledgers(
        tmp_path
    )

    coordinator = (
        coordinator_mod
        .FrozenC04ForwardAnchorFirstCoordinator(
            anchor_ledger=(
                anchor_ledger
            ),

            observation_ledger=(
                observation_ledger
            ),
        )
    )

    first = coordinator.persist(
        observation=(
            observation
        ),

        market_data=(
            market_data
        ),

        acquisition_authority=(
            ACQUISITION_AUTHORITY
        ),
    )

    second = coordinator.persist(
        observation=(
            observation
        ),

        market_data=(
            market_data
        ),

        acquisition_authority=(
            ACQUISITION_AUTHORITY
        ),
    )

    assert (
        first.anchor_appended
        is True
    )

    assert (
        first.observation_appended
        is True
    )

    assert (
        second.anchor_appended
        is False
    )

    assert (
        second.anchor_idempotent_duplicate
        is True
    )

    assert (
        second.observation_appended
        is False
    )

    assert (
        second.observation_idempotent_duplicate
        is True
    )

    assert (
        anchor_ledger.count()
        ==
        1
    )

    assert (
        observation_ledger.count()
        ==
        1
    )


def test_11_non_atomic_anchor_ledger_rejected(
    tmp_path: Path,
) -> None:

    legacy_anchor_ledger = (
        anchor_mod
        .FrozenC04ForwardOutcomeAnchorLedger(
            tmp_path
            /
            "legacy_anchors.jsonl"
        )
    )

    observation_ledger = (
        atomic_mod
        .AtomicFrozenC04ObservationLedger(
            tmp_path
            /
            "observations.jsonl"
        )
    )

    with pytest.raises(
        coordinator_mod.AnchorFirstCoordinatorError,
        match="ATOMIC_ANCHOR_LEDGER_REQUIRED",
    ):

        coordinator_mod.FrozenC04ForwardAnchorFirstCoordinator(
            anchor_ledger=(
                legacy_anchor_ledger
            ),

            observation_ledger=(
                observation_ledger
            ),
        )


def test_12_non_atomic_observation_ledger_rejected(
    tmp_path: Path,
) -> None:

    anchor_ledger = (
        atomic_mod
        .AtomicFrozenC04ForwardOutcomeAnchorLedger(
            tmp_path
            /
            "anchors.jsonl"
        )
    )

    legacy_observation_ledger = (
        observer_mod
        .FrozenC04ObservationLedger(
            tmp_path
            /
            "legacy_observations.jsonl"
        )
    )

    with pytest.raises(
        coordinator_mod.AnchorFirstCoordinatorError,
        match="ATOMIC_OBSERVATION_LEDGER_REQUIRED",
    ):

        coordinator_mod.FrozenC04ForwardAnchorFirstCoordinator(
            anchor_ledger=(
                anchor_ledger
            ),

            observation_ledger=(
                legacy_observation_ledger
            ),
        )


def test_13_no_maturation_or_performance_authority() -> None:

    assert (
        coordinator_mod.OUTCOME_MATURATION_AUTHORIZED
        is False
    )

    assert (
        coordinator_mod.PERFORMANCE_EVALUATION_AUTHORIZED
        is False
    )

    assert (
        coordinator_mod.PNL_EVALUATION_AUTHORIZED
        is False
    )


def test_14_live_and_execution_remain_blocked() -> None:

    assert (
        coordinator_mod.LIVE_AUTHORIZED
        is False
    )

    assert (
        coordinator_mod.EXECUTION_AUTHORIZED
        is False
    )