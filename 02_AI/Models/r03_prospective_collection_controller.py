from __future__ import annotations

import dataclasses
import importlib
import json
from pathlib import Path
import sys
from typing import Any, Callable, Mapping, cast

import pandas as pd


REPO_ROOT: Path = (
    Path(__file__)
    .resolve()
    .parents[2]
)

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(REPO_ROOT),
    )


_runtime: Any = importlib.import_module(
    "02_AI.Models.frozen_r03_prospective_runtime"
)

_maturer: Any = importlib.import_module(
    "02_AI.Models.frozen_r03_prospective_outcome_maturer"
)

_contract: Any = importlib.import_module(
    "02_AI.Models.frozen_r03_prospective_forward_validation_contract"
)


CONTROLLER_VERSION: str = (
    "R03_PROSPECTIVE_COLLECTION_CONTROLLER_V1"
)

COLLECTION_POLICY: str = (
    "SINGLE_PENDING_NON_OVERLAPPING_PROSPECTIVE_SAMPLE"
)

SINGLE_COLLECTOR_PROCESS_REQUIRED: bool = True

MAX_PENDING_OBSERVATIONS: int = 1

MINIMUM_MATURED_OUTCOMES: int = int(
    _contract.MINIMUM_MATURED_OUTCOMES
)

MINIMUM_DISTINCT_OBSERVATION_UTC_DATES: int = int(
    _contract.MINIMUM_DISTINCT_OBSERVATION_UTC_DATES
)

OBSERVATION_LEDGER_RELATIVE_PATH: str = str(
    _runtime.OBSERVATION_LEDGER_RELATIVE_PATH
)

ANCHOR_LEDGER_RELATIVE_PATH: str = str(
    _runtime.ANCHOR_LEDGER_RELATIVE_PATH
)

OUTCOME_LEDGER_RELATIVE_PATH: str = str(
    _runtime.OUTCOME_LEDGER_RELATIVE_PATH
)

ACTION_CAPTURE_NEW_OBSERVATION: str = (
    "CAPTURE_NEW_OBSERVATION"
)

ACTION_CHECK_PENDING_MATURITY: str = (
    "CHECK_PENDING_MATURITY"
)

ACTION_REVIEW_ORPHAN_ANCHOR: str = (
    "REVIEW_ORPHAN_ANCHOR"
)

ACTION_COLLECTION_TARGET_REACHED: str = (
    "COLLECTION_TARGET_REACHED"
)

PERFORMANCE_EVALUATION_AUTHORIZED: bool = False

PNL_EVALUATION_AUTHORIZED: bool = False

LIVE_AUTHORIZED: bool = False

EXECUTION_AUTHORIZED: bool = False


class R03CollectionControllerError(
    RuntimeError
):
    pass


class R03LedgerStateError(
    R03CollectionControllerError
):
    pass


@dataclasses.dataclass(
    frozen=True
)
class R03CollectionState:

    observation_count: int

    anchor_count: int

    matured_outcome_count: int

    pending_count: int

    orphan_anchor_count: int

    distinct_matured_observation_utc_dates: int

    pending_logical_observation_id: str | None

    next_action: str

    collection_target_reached: bool

    performance_evaluated: bool = False

    pnl_evaluated: bool = False

    live_authorized: bool = False

    execution_authorized: bool = False

    def to_dict(
        self,
    ) -> dict[str, Any]:

        return {
            "observation_count": (
                self.observation_count
            ),
            "anchor_count": (
                self.anchor_count
            ),
            "matured_outcome_count": (
                self.matured_outcome_count
            ),
            "pending_count": (
                self.pending_count
            ),
            "orphan_anchor_count": (
                self.orphan_anchor_count
            ),
            "distinct_matured_observation_utc_dates": (
                self.distinct_matured_observation_utc_dates
            ),
            "minimum_matured_outcomes": (
                MINIMUM_MATURED_OUTCOMES
            ),
            "minimum_distinct_observation_utc_dates": (
                MINIMUM_DISTINCT_OBSERVATION_UTC_DATES
            ),
            "pending_logical_observation_id": (
                self.pending_logical_observation_id
            ),
            "next_action": (
                self.next_action
            ),
            "collection_target_reached": (
                self.collection_target_reached
            ),
            "performance_evaluated": False,
            "pnl_evaluated": False,
            "live_authorized": False,
            "execution_authorized": False,
        }


def require(
    condition: bool,
    reason: str,
) -> None:

    if not condition:

        raise R03CollectionControllerError(
            reason
        )


def utc_timestamp(
    value: Any,
) -> pd.Timestamp:

    try:

        parsed = pd.Timestamp(
            value
        )

    except Exception as exc:

        raise R03LedgerStateError(
            "INVALID_TIMESTAMP"
        ) from exc

    if parsed is pd.NaT:

        raise R03LedgerStateError(
            "INVALID_TIMESTAMP_NAT"
        )

    timestamp = cast(
        pd.Timestamp,
        parsed,
    )

    if timestamp.tzinfo is None:

        raise R03LedgerStateError(
            "TIMESTAMP_MUST_BE_TIMEZONE_AWARE"
        )

    converted = timestamp.tz_convert(
        "UTC"
    )

    if converted is pd.NaT:

        raise R03LedgerStateError(
            "TIMESTAMP_UTC_CONVERSION_FAILED"
        )

    return cast(
        pd.Timestamp,
        converted,
    )


def _read_jsonl_records(
    *,
    path: Path,
    validator: Callable[
        [
            Mapping[
                str,
                Any,
            ]
        ],
        Any,
    ],
    fingerprint_field: str,
) -> dict[
    str,
    Any,
]:

    if not path.exists():

        return {}

    if not path.is_file():

        raise R03LedgerStateError(
            f"LEDGER_PATH_NOT_FILE:{path}"
        )

    records: dict[
        str,
        Any,
    ] = {}

    fingerprints: dict[
        str,
        str,
    ] = {}

    with path.open(
        "r",
        encoding="utf-8",
    ) as handle:

        for (
            line_number,
            raw_line,
        ) in enumerate(
            handle,
            start=1,
        ):

            line = raw_line.strip()

            if not line:
                continue

            try:

                value = json.loads(
                    line
                )

            except Exception as exc:

                raise R03LedgerStateError(
                    (
                        "LEDGER_JSON_CORRUPTION:"
                        f"{path}:"
                        f"{line_number}"
                    )
                ) from exc

            if not isinstance(
                value,
                dict,
            ):

                raise R03LedgerStateError(
                    (
                        "LEDGER_RECORD_NOT_OBJECT:"
                        f"{path}:"
                        f"{line_number}"
                    )
                )

            mapping_value = cast(
                Mapping[
                    str,
                    Any,
                ],
                value,
            )

            try:

                record = validator(
                    mapping_value
                )

            except Exception as exc:

                raise R03LedgerStateError(
                    (
                        "LEDGER_RECORD_VALIDATION_FAILED:"
                        f"{path}:"
                        f"{line_number}:"
                        f"{type(exc).__name__}:"
                        f"{exc}"
                    )
                ) from exc

            logical_id = str(
                getattr(
                    record,
                    "logical_observation_id",
                )
            )

            fingerprint_raw = value.get(
                fingerprint_field
            )

            if not isinstance(
                fingerprint_raw,
                str,
            ):

                raise R03LedgerStateError(
                    (
                        "LEDGER_FINGERPRINT_MISSING:"
                        f"{path}:"
                        f"{line_number}"
                    )
                )

            fingerprint = (
                fingerprint_raw
                .strip()
                .lower()
            )

            if logical_id in records:

                if (
                    fingerprints[
                        logical_id
                    ]
                    !=
                    fingerprint
                ):

                    raise R03LedgerStateError(
                        (
                            "LEDGER_DUPLICATE_CONFLICT:"
                            f"{logical_id}"
                        )
                    )

                continue

            records[
                logical_id
            ] = record

            fingerprints[
                logical_id
            ] = fingerprint

    return records


def read_observations(
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[
    str,
    Any,
]:

    return _read_jsonl_records(
        path=(
            repo_root
            /
            OBSERVATION_LEDGER_RELATIVE_PATH
        ),
        validator=(
            _runtime.validate_observation_document
        ),
        fingerprint_field=(
            "semantic_record_fingerprint"
        ),
    )


def read_anchors(
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[
    str,
    Any,
]:

    return _read_jsonl_records(
        path=(
            repo_root
            /
            ANCHOR_LEDGER_RELATIVE_PATH
        ),
        validator=(
            _runtime.validate_anchor_document
        ),
        fingerprint_field=(
            "anchor_semantic_fingerprint"
        ),
    )


def read_outcomes(
    *,
    repo_root: Path = REPO_ROOT,
) -> dict[
    str,
    Any,
]:

    return _read_jsonl_records(
        path=(
            repo_root
            /
            OUTCOME_LEDGER_RELATIVE_PATH
        ),
        validator=(
            _maturer.validate_outcome_document
        ),
        fingerprint_field=(
            "semantic_outcome_fingerprint"
        ),
    )


def derive_state_from_records(
    *,
    observations: Mapping[
        str,
        Any,
    ],
    anchors: Mapping[
        str,
        Any,
    ],
    outcomes: Mapping[
        str,
        Any,
    ],
) -> R03CollectionState:

    observation_ids = set(
        observations.keys()
    )

    anchor_ids = set(
        anchors.keys()
    )

    outcome_ids = set(
        outcomes.keys()
    )

    observation_without_anchor = (
        observation_ids
        -
        anchor_ids
    )

    if observation_without_anchor:

        raise R03LedgerStateError(
            (
                "OBSERVATION_WITHOUT_PROSPECTIVE_ANCHOR:"
                f"{sorted(observation_without_anchor)}"
            )
        )

    outcome_without_observation = (
        outcome_ids
        -
        observation_ids
    )

    if outcome_without_observation:

        raise R03LedgerStateError(
            (
                "OUTCOME_WITHOUT_OBSERVATION:"
                f"{sorted(outcome_without_observation)}"
            )
        )

    outcome_without_anchor = (
        outcome_ids
        -
        anchor_ids
    )

    if outcome_without_anchor:

        raise R03LedgerStateError(
            (
                "OUTCOME_WITHOUT_ANCHOR:"
                f"{sorted(outcome_without_anchor)}"
            )
        )

    orphan_anchor_ids = (
        anchor_ids
        -
        observation_ids
    )

    pending_ids = (
        observation_ids
        -
        outcome_ids
    )

    if (
        len(
            pending_ids
        )
        >
        MAX_PENDING_OBSERVATIONS
    ):

        raise R03LedgerStateError(
            (
                "MULTIPLE_PENDING_OBSERVATIONS_FORBIDDEN:"
                f"{sorted(pending_ids)}"
            )
        )

    matured_dates: set[
        str
    ] = set()

    for logical_id in sorted(
        outcome_ids
    ):

        observation = observations[
            logical_id
        ]

        decision_time = utc_timestamp(
            getattr(
                observation,
                "decision_time_utc",
            )
        )

        matured_dates.add(
            decision_time
            .date()
            .isoformat()
        )

    matured_count = len(
        outcome_ids
    )

    distinct_dates = len(
        matured_dates
    )

    target_reached = bool(
        matured_count
        >=
        MINIMUM_MATURED_OUTCOMES
        and
        distinct_dates
        >=
        MINIMUM_DISTINCT_OBSERVATION_UTC_DATES
    )

    pending_id: str | None = None

    if pending_ids:

        pending_id = next(
            iter(
                pending_ids
            )
        )

    if orphan_anchor_ids:

        next_action = (
            ACTION_REVIEW_ORPHAN_ANCHOR
        )

    elif target_reached:

        next_action = (
            ACTION_COLLECTION_TARGET_REACHED
        )

    elif pending_id is not None:

        next_action = (
            ACTION_CHECK_PENDING_MATURITY
        )

    else:

        next_action = (
            ACTION_CAPTURE_NEW_OBSERVATION
        )

    return R03CollectionState(
        observation_count=(
            len(
                observation_ids
            )
        ),
        anchor_count=(
            len(
                anchor_ids
            )
        ),
        matured_outcome_count=(
            matured_count
        ),
        pending_count=(
            len(
                pending_ids
            )
        ),
        orphan_anchor_count=(
            len(
                orphan_anchor_ids
            )
        ),
        distinct_matured_observation_utc_dates=(
            distinct_dates
        ),
        pending_logical_observation_id=(
            pending_id
        ),
        next_action=(
            next_action
        ),
        collection_target_reached=(
            target_reached
        ),
        performance_evaluated=False,
        pnl_evaluated=False,
        live_authorized=False,
        execution_authorized=False,
    )


def inspect_state(
    *,
    repo_root: Path = REPO_ROOT,
) -> R03CollectionState:

    observations = read_observations(
        repo_root=repo_root
    )

    anchors = read_anchors(
        repo_root=repo_root
    )

    outcomes = read_outcomes(
        repo_root=repo_root
    )

    return derive_state_from_records(
        observations=observations,
        anchors=anchors,
        outcomes=outcomes,
    )


def capture_new_observation_from_snapshot(
    *,
    snapshot: Any,
    feature_result: Any,
    repo_root: Path = REPO_ROOT,
    observed_at_utc: str | None = None,
) -> dict[
    str,
    Any,
]:

    before = inspect_state(
        repo_root=repo_root
    )

    if (
        before.next_action
        !=
        ACTION_CAPTURE_NEW_OBSERVATION
    ):

        raise R03CollectionControllerError(
            (
                "NEW_CAPTURE_NOT_AUTHORIZED:"
                f"{before.next_action}"
            )
        )

    binder = (
        _runtime
        .R03ProspectiveRuntimeBinder(
            inference_adapter=(
                _runtime
                .R03FrozenArtifactInferenceAdapter(
                    repo_root=repo_root
                )
            )
        )
    )

    observation = (
        binder.create_observation(
            snapshot=snapshot,
            feature_result=feature_result,
            observed_at_utc=(
                observed_at_utc
            ),
        )
    )

    anchor = binder.create_anchor(
        observation=observation,
        market_data=(
            snapshot.market_data
        ),
    )

    observation_ledger = (
        _runtime
        .R03ProspectiveObservationLedger(
            repo_root
            /
            OBSERVATION_LEDGER_RELATIVE_PATH
        )
    )

    anchor_ledger = (
        _runtime
        .R03ProspectiveAnchorLedger(
            repo_root
            /
            ANCHOR_LEDGER_RELATIVE_PATH
        )
    )

    persistence = (
        binder.persist_anchor_first(
            observation=observation,
            anchor=anchor,
            observation_ledger=(
                observation_ledger
            ),
            anchor_ledger=(
                anchor_ledger
            ),
        )
    )

    after = inspect_state(
        repo_root=repo_root
    )

    require(
        after.pending_count
        ==
        1,
        "POST_CAPTURE_PENDING_COUNT_NOT_ONE",
    )

    require(
        after.pending_logical_observation_id
        ==
        observation.logical_observation_id,
        "POST_CAPTURE_PENDING_ID_MISMATCH",
    )

    return {
        "action": (
            "CAPTURED_NEW_OBSERVATION"
        ),
        "logical_observation_id": (
            observation.logical_observation_id
        ),
        "decision_time_utc": (
            observation.decision_time_utc
        ),
        "predicted_class": (
            observation.predicted_class
        ),
        "predicted_label": (
            observation.predicted_label
        ),
        "probability_short": (
            observation.probability_short
        ),
        "probability_no_trade": (
            observation.probability_no_trade
        ),
        "probability_long": (
            observation.probability_long
        ),
        "anchor_appended": (
            bool(
                persistence[
                    "anchor_appended"
                ]
            )
        ),
        "observation_appended": (
            bool(
                persistence[
                    "observation_appended"
                ]
            )
        ),
        "state_after": (
            after.to_dict()
        ),
        "performance_evaluated": False,
        "pnl_evaluated": False,
        "live_authorized": False,
        "execution_authorized": False,
    }


def mature_pending_from_snapshot(
    *,
    snapshot: Any,
    repo_root: Path = REPO_ROOT,
) -> dict[
    str,
    Any,
]:

    before = inspect_state(
        repo_root=repo_root
    )

    if (
        before.next_action
        !=
        ACTION_CHECK_PENDING_MATURITY
    ):

        raise R03CollectionControllerError(
            (
                "PENDING_MATURATION_NOT_AUTHORIZED:"
                f"{before.next_action}"
            )
        )

    pending_id = (
        before.pending_logical_observation_id
    )

    if pending_id is None:

        raise R03CollectionControllerError(
            "PENDING_ID_MISSING"
        )

    observations = read_observations(
        repo_root=repo_root
    )

    anchors = read_anchors(
        repo_root=repo_root
    )

    observation = observations.get(
        pending_id
    )

    anchor = anchors.get(
        pending_id
    )

    if observation is None:

        raise R03CollectionControllerError(
            "PENDING_OBSERVATION_RECORD_MISSING"
        )

    if anchor is None:

        raise R03CollectionControllerError(
            "PENDING_ANCHOR_RECORD_MISSING"
        )

    binder = (
        _runtime
        .R03ProspectiveRuntimeBinder(
            inference_adapter=(
                _runtime
                .R03FrozenArtifactInferenceAdapter(
                    repo_root=repo_root
                )
            )
        )
    )

    _ = (
        binder
        .verify_genuine_snapshot_authority(
            snapshot
        )
    )

    market_data = getattr(
        snapshot,
        "market_data",
        None,
    )

    if not isinstance(
        market_data,
        Mapping,
    ):

        raise R03CollectionControllerError(
            "MATURATION_SNAPSHOT_MARKET_DATA_INVALID"
        )

    m5 = market_data.get(
        "M5"
    )

    if not isinstance(
        m5,
        pd.DataFrame,
    ):

        raise R03CollectionControllerError(
            "MATURATION_SNAPSHOT_M5_INVALID"
        )

    try:

        outcome = (
            _maturer
            .mature_observation(
                observation=observation,
                anchor=anchor,
                completed_m5_bars=m5,
            )
        )

    except _maturer.InsufficientFutureBarsError as exc:

        return {
            "action": (
                "WAIT_FOR_MORE_COMPLETED_M5_BARS"
            ),
            "logical_observation_id": (
                pending_id
            ),
            "reason": str(
                exc
            ),
            "state_after": (
                before.to_dict()
            ),
            "performance_evaluated": False,
            "pnl_evaluated": False,
            "live_authorized": False,
            "execution_authorized": False,
        }

    outcome_ledger = (
        _maturer
        .R03ProspectiveOutcomeLedger(
            repo_root
            /
            OUTCOME_LEDGER_RELATIVE_PATH
        )
    )

    append_result = (
        outcome_ledger.append(
            outcome
        )
    )

    require(
        outcome_ledger.validate_integrity()
        is True,
        "OUTCOME_LEDGER_INTEGRITY_FAILED",
    )

    after = inspect_state(
        repo_root=repo_root
    )

    require(
        after.pending_count
        ==
        0,
        "POST_MATURATION_PENDING_COUNT_NOT_ZERO",
    )

    return {
        "action": (
            "MATURED_PENDING_OUTCOME"
        ),
        "logical_observation_id": (
            pending_id
        ),
        "outcome_class": (
            outcome.outcome_class
        ),
        "outcome_label": (
            outcome.outcome_label
        ),
        "up_excursion_atr": (
            outcome.up_excursion_atr
        ),
        "down_excursion_atr": (
            outcome.down_excursion_atr
        ),
        "outcome_appended": (
            append_result.appended
        ),
        "outcome_idempotent_duplicate": (
            append_result.is_duplicate
        ),
        "state_after": (
            after.to_dict()
        ),
        "performance_evaluated": False,
        "pnl_evaluated": False,
        "live_authorized": False,
        "execution_authorized": False,
    }


def next_action(
    *,
    repo_root: Path = REPO_ROOT,
) -> str:

    return inspect_state(
        repo_root=repo_root
    ).next_action