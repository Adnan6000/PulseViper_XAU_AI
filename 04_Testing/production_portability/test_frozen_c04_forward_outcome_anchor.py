from __future__ import annotations

import dataclasses
import importlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest


pytestmark = pytest.mark.offline


anchor_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_anchor"
)

acquisition_mod: Any = importlib.import_module(
    "02_AI.Adapters.mt5_read_only_forward_acquisition_adapter"
)


DECISION_TIME: str = (
    "2026-09-28T12:00:00Z"
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

    m5 = _m5_frame()

    # Canonical snapshot hashing does not require every timeframe for the
    # unit test. Genuine acquisition integration will supply all frozen
    # acquisition timeframes.
    return {
        "M5": m5,
    }


def _observation(
    market_data: dict[str, pd.DataFrame],
) -> dict[str, Any]:

    snapshot_id = (
        acquisition_mod
        .compute_canonical_snapshot_id(
            market_data
        )
    )

    return {
        "logical_observation_id": (
            "a"
            *
            64
        ),

        "semantic_record_fingerprint": (
            "b"
            *
            64
        ),

        "source_snapshot_id": (
            snapshot_id
        ),

        "decision_time_utc": (
            DECISION_TIME
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

        "acquisition_authority": (
            "MT5ReadOnlyForwardAcquisitionAdapter:2.1.0"
        ),

        "live_authorized": False,

        "execution_authorized": False,
    }


def _anchor() -> Any:

    market_data = _market_data()

    return anchor_mod.capture_anchor(
        observation=(
            _observation(
                market_data
            )
        ),
        market_data=(
            market_data
        ),
    )


def test_01_authorities_pass() -> None:

    assert (
        anchor_mod.verify_authorities()
        is True
    )


def test_02_anchor_versions() -> None:

    assert (
        anchor_mod.ANCHOR_VERSION
        ==
        "FROZEN_C04_FORWARD_OUTCOME_ANCHOR_V1"
    )

    assert (
        anchor_mod.ANCHOR_LEDGER_VERSION
        ==
        "FROZEN_C04_FORWARD_OUTCOME_ANCHOR_LEDGER_V1"
    )


def test_03_anchor_capture() -> None:

    anchor = _anchor()

    assert (
        anchor.decision_time_utc
        ==
        "2026-09-28T12:00:00Z"
    )

    assert (
        anchor.decision_bar_open_time_utc
        ==
        "2026-09-28T11:55:00Z"
    )

    assert (
        anchor.decision_m5_close
        >
        0.0
    )

    assert (
        anchor.decision_m5_atr14
        >
        0.0
    )


def test_04_same_snapshot_identity_required() -> None:

    market_data = _market_data()

    observation = _observation(
        market_data
    )

    tampered = {
        "M5": (
            market_data[
                "M5"
            ].copy()
        )
    }

    tampered[
        "M5"
    ].loc[
        tampered[
            "M5"
        ].index[
            -1
        ],
        "close",
    ] += 0.5

    with pytest.raises(
        anchor_mod.InvalidAnchorError,
        match="SOURCE_SNAPSHOT_ID_MISMATCH",
    ):

        anchor_mod.capture_anchor(
            observation=observation,
            market_data=tampered,
        )


def test_05_snapshot_must_end_at_decision_bar() -> None:

    market_data = _market_data()

    observation = _observation(
        market_data
    )

    shifted = {
        "M5": (
            market_data[
                "M5"
            ].iloc[
                :-1
            ]
            .copy()
        )
    }

    observation[
        "source_snapshot_id"
    ] = (
        acquisition_mod
        .compute_canonical_snapshot_id(
            shifted
        )
    )

    with pytest.raises(
        anchor_mod.InvalidAnchorError,
        match="SNAPSHOT_NOT_TERMINATED_AT_DECISION_BAR",
    ):

        anchor_mod.capture_anchor(
            observation=observation,
            market_data=shifted,
        )


def test_06_future_m5_row_rejected() -> None:

    market_data = _market_data()

    m5 = market_data[
        "M5"
    ].copy()

    latest = (
        m5.iloc[
            -1
        ]
        .copy()
    )

    latest[
        "time"
    ] = (
        pd.Timestamp(
            latest[
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
            m5,
            pd.DataFrame(
                [
                    latest
                ]
            ),
        ],
        ignore_index=True,
    )

    future_market = {
        "M5": extended,
    }

    observation = _observation(
        future_market
    )

    with pytest.raises(
        anchor_mod.InvalidAnchorError,
        match=(
            "SNAPSHOT_NOT_TERMINATED_AT_DECISION_BAR"
        ),
    ):

        anchor_mod.capture_anchor(
            observation=observation,
            market_data=future_market,
        )


def test_07_pre_contract_observation_rejected() -> None:

    market_data = _market_data()

    observation = _observation(
        market_data
    )

    observation[
        "decision_time_utc"
    ] = (
        "2026-09-28T10:15:00Z"
    )

    with pytest.raises(
        anchor_mod.InvalidAnchorError,
        match="OBSERVATION_NOT_PROSPECTIVELY_ELIGIBLE",
    ):

        anchor_mod.capture_anchor(
            observation=observation,
            market_data=market_data,
        )


def test_08_wrong_feature_authority_rejected() -> None:

    market_data = _market_data()

    observation = _observation(
        market_data
    )

    observation[
        "feature_columns_sha256"
    ] = (
        "c"
        *
        64
    )

    with pytest.raises(
        anchor_mod.InvalidAnchorError,
        match="FEATURE_COLUMNS_AUTHORITY_MISMATCH",
    ):

        anchor_mod.capture_anchor(
            observation=observation,
            market_data=market_data,
        )


def test_09_wrong_model_authority_rejected() -> None:

    market_data = _market_data()

    observation = _observation(
        market_data
    )

    observation[
        "model_sha256"
    ] = (
        "c"
        *
        64
    )

    with pytest.raises(
        anchor_mod.InvalidAnchorError,
        match="MODEL_AUTHORITY_MISMATCH",
    ):

        anchor_mod.capture_anchor(
            observation=observation,
            market_data=market_data,
        )


def test_10_roundtrip_validation() -> None:

    anchor = _anchor()

    validated = (
        anchor_mod.validate_anchor_document(
            anchor.to_dict()
        )
    )

    assert (
        validated.semantic_fingerprint()
        ==
        anchor.semantic_fingerprint()
    )


def test_11_tampered_anchor_fingerprint_rejected() -> None:

    document = (
        _anchor()
        .to_dict()
    )

    document[
        "anchor_semantic_fingerprint"
    ] = (
        "c"
        *
        64
    )

    with pytest.raises(
        anchor_mod.InvalidAnchorError,
        match="ANCHOR_SEMANTIC_FINGERPRINT_MISMATCH",
    ):

        anchor_mod.validate_anchor_document(
            document
        )


def test_12_anchor_ledger_append(
    tmp_path: Path,
) -> None:

    ledger = (
        anchor_mod
        .FrozenC04ForwardOutcomeAnchorLedger(
            tmp_path
            /
            "anchors.jsonl"
        )
    )

    result = ledger.append(
        _anchor()
    )

    assert (
        result.appended
        is True
    )

    assert (
        ledger.count()
        ==
        1
    )

    assert (
        ledger.validate_integrity()
        is True
    )


def test_13_idempotent_duplicate() -> None:

    pass


def test_14_idempotent_duplicate(
    tmp_path: Path,
) -> None:

    ledger = (
        anchor_mod
        .FrozenC04ForwardOutcomeAnchorLedger(
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

    first = ledger.append(
        _anchor()
    )

    second = ledger.append(
        _anchor()
    )

    assert (
        first.appended
        is True
    )

    assert (
        second.appended
        is False
    )

    assert (
        second.is_duplicate
        is True
    )


def test_15_duplicate_fail_closed(
    tmp_path: Path,
) -> None:

    ledger = (
        anchor_mod
        .FrozenC04ForwardOutcomeAnchorLedger(
            tmp_path
            /
            "anchors.jsonl"
        )
    )

    ledger.append(
        _anchor()
    )

    with pytest.raises(
        anchor_mod.DuplicateAnchorError
    ):

        ledger.append(
            _anchor()
        )


def test_16_conflicting_anchor_fails_closed(
    tmp_path: Path,
) -> None:

    ledger = (
        anchor_mod
        .FrozenC04ForwardOutcomeAnchorLedger(
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

    original = _anchor()

    ledger.append(
        original
    )

    conflicting = dataclasses.replace(
        original,
        decision_m5_close=(
            original.decision_m5_close
            +
            1.0
        ),
    )

    with pytest.raises(
        anchor_mod.ConflictingAnchorError
    ):

        ledger.append(
            conflicting
        )


def test_17_corrupted_json_fails_closed(
    tmp_path: Path,
) -> None:

    path = (
        tmp_path
        /
        "anchors.jsonl"
    )

    path.write_text(
        "{not-json\n",
        encoding="utf-8",
    )

    with pytest.raises(
        anchor_mod.CorruptedAnchorLedgerError
    ):

        anchor_mod.FrozenC04ForwardOutcomeAnchorLedger(
            path
        )


def test_18_no_performance_or_execution_authority() -> None:

    assert (
        anchor_mod.FORMAL_MATURATION_REQUIRES_ANCHOR
        is True
    )

    assert (
        anchor_mod.PERFORMANCE_EVALUATION_AUTHORIZED
        is False
    )

    assert (
        anchor_mod.PNL_EVALUATION_AUTHORIZED
        is False
    )

    assert (
        anchor_mod.LIVE_AUTHORIZED
        is False
    )

    assert (
        anchor_mod.EXECUTION_AUTHORIZED
        is False
    )