from __future__ import annotations

import dataclasses
import importlib
from typing import Any, cast

import numpy as np
import pandas as pd
import pytest


pytestmark = pytest.mark.offline


module: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_maturer"
)

anchor_mod: Any = importlib.import_module(
    "02_AI.Models.frozen_c04_forward_outcome_anchor"
)


DECISION_TIME: str = (
    "2026-09-28T12:00:00Z"
)

DECISION_BAR_OPEN: str = (
    "2026-09-28T11:55:00Z"
)

FEATURE_SHA: str = (
    "65637cc25cf36b52cbfb3eaed9df51fdb66a0ad8c5bd618a25733454935f6cd2"
)

MODEL_SHA: str = (
    "48a1d70de37b4dfa5f37d5788bbb070a73710a64260243db436f6ffd00893769"
)

SOURCE_SNAPSHOT_ID: str = (
    "c"
    *
    64
)

OBSERVATION_FINGERPRINT: str = (
    "b"
    *
    64
)

LOGICAL_OBSERVATION_ID: str = (
    "a"
    *
    64
)

ANCHOR_ENTRY_CLOSE: float = (
    2000.0
)

ANCHOR_ATR14: float = (
    2.0
)


def _observation() -> dict[str, Any]:

    return {
        "logical_observation_id": (
            LOGICAL_OBSERVATION_ID
        ),

        "semantic_record_fingerprint": (
            OBSERVATION_FINGERPRINT
        ),

        "source_snapshot_id": (
            SOURCE_SNAPSHOT_ID
        ),

        "decision_time_utc": (
            DECISION_TIME
        ),

        "canonical_instrument": (
            "XAUUSD"
        ),

        "source_provenance": (
            "TRUE_FORWARD_OBSERVATION"
        ),

        "is_true_forward_eligible": True,

        "feature_columns_sha256": (
            FEATURE_SHA
        ),

        "model_sha256": (
            MODEL_SHA
        ),

        "live_authorized": False,

        "execution_authorized": False,
    }


def _anchor() -> Any:

    return (
        anchor_mod
        .FrozenC04ForwardOutcomeAnchor(
            logical_observation_id=(
                LOGICAL_OBSERVATION_ID
            ),

            semantic_observation_fingerprint=(
                OBSERVATION_FINGERPRINT
            ),

            source_snapshot_id=(
                SOURCE_SNAPSHOT_ID
            ),

            canonical_instrument=(
                "XAUUSD"
            ),

            decision_time_utc=(
                DECISION_TIME
            ),

            decision_bar_open_time_utc=(
                DECISION_BAR_OPEN
            ),

            decision_m5_close=(
                ANCHOR_ENTRY_CLOSE
            ),

            decision_m5_atr14=(
                ANCHOR_ATR14
            ),

            feature_columns_sha256=(
                FEATURE_SHA
            ),

            model_sha256=(
                MODEL_SHA
            ),

            acquisition_authority=(
                "MT5ReadOnlyForwardAcquisitionAdapter:2.1.0"
            ),

            source_provenance=(
                "TRUE_FORWARD_OBSERVATION"
            ),
        )
    )


def _base_frame(
    *,
    future_high_offset: float = 0.5,
    future_low_offset: float = 0.5,
    historical_decision_close: float | None = None,
) -> pd.DataFrame:

    decision_open = (
        pd.Timestamp(
            DECISION_BAR_OPEN
        )
    )

    start = (
        decision_open
        -
        pd.Timedelta(
            minutes=(
                20
                *
                5
            )
        )
    )

    times = pd.date_range(
        start=start,
        periods=33,
        freq="5min",
        tz="UTC",
    )

    base = (
        ANCHOR_ENTRY_CLOSE
    )

    frame = pd.DataFrame(
        {
            "time": times,

            "open": np.full(
                len(
                    times
                ),
                base,
                dtype=float,
            ),

            "high": np.full(
                len(
                    times
                ),
                base
                +
                1.0,
                dtype=float,
            ),

            "low": np.full(
                len(
                    times
                ),
                base
                -
                1.0,
                dtype=float,
            ),

            "close": np.full(
                len(
                    times
                ),
                base,
                dtype=float,
            ),

            "tick_volume": np.full(
                len(
                    times
                ),
                100,
                dtype=int,
            ),
        }
    )

    positions = np.flatnonzero(
        (
            frame[
                "time"
            ]
            ==
            decision_open
        ).to_numpy(
            dtype=bool
        )
    )

    assert (
        len(
            positions
        )
        ==
        1
    )

    decision_index = int(
        positions[
            0
        ]
    )

    if (
        historical_decision_close
        is not None
    ):

        altered = float(
            historical_decision_close
        )

        frame.loc[
            decision_index,
            "open",
        ] = (
            altered
        )

        frame.loc[
            decision_index,
            "close",
        ] = (
            altered
        )

        frame.loc[
            decision_index,
            "high",
        ] = (
            altered
            +
            1.0
        )

        frame.loc[
            decision_index,
            "low",
        ] = (
            altered
            -
            1.0
        )

    future_indexes = frame.index[
        decision_index
        +
        1:
        decision_index
        +
        13
    ]

    assert (
        len(
            future_indexes
        )
        ==
        12
    )

    frame.loc[
        future_indexes,
        "open",
    ] = (
        ANCHOR_ENTRY_CLOSE
    )

    frame.loc[
        future_indexes,
        "close",
    ] = (
        ANCHOR_ENTRY_CLOSE
    )

    frame.loc[
        future_indexes,
        "high",
    ] = (
        ANCHOR_ENTRY_CLOSE
        +
        future_high_offset
    )

    frame.loc[
        future_indexes,
        "low",
    ] = (
        ANCHOR_ENTRY_CLOSE
        -
        future_low_offset
    )

    return cast(
        pd.DataFrame,
        frame,
    )


def _mature(
    frame: pd.DataFrame,
    *,
    observation: dict[str, Any] | None = None,
    anchor: Any | None = None,
) -> Any:

    return module.mature_observation(
        observation=(
            observation
            if observation is not None
            else
            _observation()
        ),

        anchor=(
            anchor
            if anchor is not None
            else
            _anchor()
        ),

        completed_m5_bars=(
            frame
        ),
    )


def test_01_authorities_pass() -> None:

    assert (
        module.verify_authorities()
        is True
    )


def test_02_version_is_v2() -> None:

    assert (
        module.MATURATION_VERSION
        ==
        "FROZEN_C04_FORWARD_OUTCOME_MATURER_V2"
    )

    assert (
        module.SUPERSEDES_MATURATION_VERSION
        ==
        "FROZEN_C04_FORWARD_OUTCOME_MATURER_V1_1"
    )


def test_03_anchor_is_mandatory() -> None:

    with pytest.raises(
        module.InvalidProspectiveAnchorError,
        match="PROSPECTIVE_ANCHOR_REQUIRED",
    ):

        module.mature_observation(
            observation=(
                _observation()
            ),

            anchor=None,

            completed_m5_bars=(
                _base_frame()
            ),
        )


def test_04_reference_policy_is_anchor_only() -> None:

    assert (
        module.FORMAL_MATURATION_REQUIRES_ANCHOR
        is True
    )

    assert (
        module.ANCHOR_REQUIREMENT
        ==
        "VALIDATED_PROSPECTIVE_ANCHOR_REQUIRED"
    )

    assert (
        module.ENTRY_REFERENCE
        ==
        "PROSPECTIVE_ANCHOR_DECISION_M5_CLOSE"
    )

    assert (
        module.ATR_REFERENCE
        ==
        "PROSPECTIVE_ANCHOR_DECISION_M5_ATR14"
    )

    assert (
        module.REFERENCE_RECONSTRUCTION_POLICY
        ==
        "POST_HOC_ENTRY_AND_ATR_RECONSTRUCTION_FORBIDDEN"
    )


def test_05_long_outcome_uses_anchor() -> None:

    outcome = (
        _mature(
            _base_frame(
                future_high_offset=3.0,
                future_low_offset=1.0,
            )
        )
    )

    assert (
        outcome.outcome_class
        ==
        1
    )

    assert (
        outcome.outcome_label
        ==
        "LONG"
    )

    assert (
        outcome.entry_close
        ==
        pytest.approx(
            ANCHOR_ENTRY_CLOSE
        )
    )

    assert (
        outcome.decision_atr14
        ==
        pytest.approx(
            ANCHOR_ATR14
        )
    )

    assert (
        outcome.up_excursion_atr
        ==
        pytest.approx(
            1.5
        )
    )

    assert (
        outcome.down_excursion_atr
        ==
        pytest.approx(
            0.5
        )
    )


def test_06_short_outcome() -> None:

    outcome = (
        _mature(
            _base_frame(
                future_high_offset=1.0,
                future_low_offset=3.0,
            )
        )
    )

    assert (
        outcome.outcome_class
        ==
        -1
    )

    assert (
        outcome.outcome_label
        ==
        "SHORT"
    )


def test_07_no_trade_when_neither_clean_direction() -> None:

    outcome = (
        _mature(
            _base_frame(
                future_high_offset=1.0,
                future_low_offset=1.0,
            )
        )
    )

    assert (
        outcome.outcome_class
        ==
        0
    )

    assert (
        outcome.outcome_label
        ==
        "NO_TRADE"
    )


def test_08_no_trade_when_both_sides_large() -> None:

    outcome = (
        _mature(
            _base_frame(
                future_high_offset=3.0,
                future_low_offset=3.0,
            )
        )
    )

    assert (
        outcome.outcome_class
        ==
        0
    )


def test_09_historical_decision_close_cannot_replace_anchor() -> None:

    frame: pd.DataFrame = (
        _base_frame(
            future_high_offset=3.0,
            future_low_offset=1.0,
            historical_decision_close=2100.0,
        )
    )

    outcome = (
        _mature(
            frame
        )
    )

    assert (
        outcome.entry_close
        ==
        pytest.approx(
            ANCHOR_ENTRY_CLOSE
        )
    )

    assert (
        outcome.entry_close
        !=
        pytest.approx(
            2100.0
        )
    )

    assert (
        outcome.decision_atr14
        ==
        pytest.approx(
            ANCHOR_ATR14
        )
    )


def test_10_anchor_fingerprint_preserved() -> None:

    anchor = (
        _anchor()
    )

    outcome = (
        _mature(
            _base_frame(),
            anchor=anchor,
        )
    )

    assert (
        outcome.source_anchor_fingerprint
        ==
        anchor.semantic_fingerprint()
    )

    assert (
        outcome.source_anchor_version
        ==
        anchor_mod.ANCHOR_VERSION
    )


def test_11_observation_fingerprint_preserved() -> None:

    outcome = (
        _mature(
            _base_frame()
        )
    )

    assert (
        outcome.source_observation_fingerprint
        ==
        OBSERVATION_FINGERPRINT
    )


def test_12_decision_times_come_from_anchor() -> None:

    outcome = (
        _mature(
            _base_frame()
        )
    )

    assert (
        outcome.decision_time_utc
        ==
        DECISION_TIME
    )

    assert (
        outcome.decision_bar_open_time_utc
        ==
        DECISION_BAR_OPEN
    )


def test_13_first_and_last_future_rows() -> None:

    outcome = (
        _mature(
            _base_frame()
        )
    )

    assert (
        outcome.first_future_bar_time_utc
        ==
        "2026-09-28T12:00:00Z"
    )

    assert (
        outcome.last_future_bar_time_utc
        ==
        "2026-09-28T12:55:00Z"
    )


def test_14_exact_12_future_rows_required() -> None:

    base_frame: pd.DataFrame = (
        _base_frame()
    )

    frame = cast(
        pd.DataFrame,
        base_frame.iloc[
            :-1
        ].copy(),
    )

    with pytest.raises(
        module.InsufficientFutureBarsError,
        match="INSUFFICIENT_COMPLETED_FUTURE_M5_BARS",
    ):

        _mature(
            frame
        )


def test_15_decision_row_required_for_row_horizon() -> None:

    base_frame: pd.DataFrame = (
        _base_frame()
    )

    decision_open = pd.Timestamp(
        DECISION_BAR_OPEN
    )

    filtered = base_frame.loc[
        base_frame[
            "time"
        ]
        !=
        decision_open,
        :,
    ]

    frame = cast(
        pd.DataFrame,
        filtered.copy(),
    )

    with pytest.raises(
        module.ForwardOutcomeMaturationError,
        match="DECISION_M5_BAR_NOT_UNIQUE",
    ):

        _mature(
            frame
        )


def test_16_market_gap_does_not_change_row_horizon() -> None:

    frame: pd.DataFrame = (
        _base_frame(
            future_high_offset=3.0,
            future_low_offset=1.0,
        )
    )

    decision_time = pd.Timestamp(
        DECISION_TIME
    )

    mask = cast(
        pd.Series,
        (
            frame[
                "time"
            ]
            >
            (
                decision_time
                +
                pd.Timedelta(
                    minutes=10
                )
            )
        ),
    )

    shifted_times = cast(
        pd.Series,
        frame.loc[
            mask,
            "time",
        ],
    )

    shifted_times = (
        shifted_times
        +
        pd.Timedelta(
            hours=48
        )
    )

    frame.loc[
        mask,
        "time",
    ] = (
        shifted_times
    )

    typed_frame = cast(
        pd.DataFrame,
        frame,
    )

    outcome = (
        _mature(
            typed_frame
        )
    )

    assert (
        outcome.horizon_bars
        ==
        12
    )

    assert (
        outcome.outcome_class
        ==
        1
    )


def test_17_wrong_anchor_logical_id_rejected() -> None:

    anchor = dataclasses.replace(
        _anchor(),
        logical_observation_id=(
            "d"
            *
            64
        ),
    )

    with pytest.raises(
        module.InvalidProspectiveAnchorError,
        match="ANCHOR_LOGICAL_OBSERVATION_ID_MISMATCH",
    ):

        _mature(
            _base_frame(),
            anchor=anchor,
        )


def test_18_wrong_anchor_observation_fingerprint_rejected() -> None:

    anchor = dataclasses.replace(
        _anchor(),
        semantic_observation_fingerprint=(
            "d"
            *
            64
        ),
    )

    with pytest.raises(
        module.InvalidProspectiveAnchorError,
        match="ANCHOR_OBSERVATION_FINGERPRINT_MISMATCH",
    ):

        _mature(
            _base_frame(),
            anchor=anchor,
        )


def test_19_wrong_anchor_snapshot_id_rejected() -> None:

    anchor = dataclasses.replace(
        _anchor(),
        source_snapshot_id=(
            "d"
            *
            64
        ),
    )

    with pytest.raises(
        module.InvalidProspectiveAnchorError,
        match="ANCHOR_SOURCE_SNAPSHOT_ID_MISMATCH",
    ):

        _mature(
            _base_frame(),
            anchor=anchor,
        )


def test_20_wrong_anchor_decision_time_rejected() -> None:

    anchor = dataclasses.replace(
        _anchor(),
        decision_time_utc=(
            "2026-09-28T12:05:00Z"
        ),
        decision_bar_open_time_utc=(
            "2026-09-28T12:00:00Z"
        ),
    )

    with pytest.raises(
        module.InvalidProspectiveAnchorError,
        match="ANCHOR_DECISION_TIME_MISMATCH",
    ):

        _mature(
            _base_frame(),
            anchor=anchor,
        )


def test_21_invalid_anchor_fingerprint_fails_closed() -> None:

    document = (
        _anchor()
        .to_dict()
    )

    document[
        "anchor_semantic_fingerprint"
    ] = (
        "d"
        *
        64
    )

    with pytest.raises(
        module.InvalidProspectiveAnchorError,
        match="INVALID_PROSPECTIVE_ANCHOR",
    ):

        _mature(
            _base_frame(),
            anchor=document,
        )


def test_22_pre_contract_observation_rejected() -> None:

    observation = (
        _observation()
    )

    observation[
        "decision_time_utc"
    ] = (
        "2026-09-28T10:15:00Z"
    )

    with pytest.raises(
        module.ForwardOutcomeMaturationError,
        match="OBSERVATION_NOT_PROSPECTIVELY_ELIGIBLE",
    ):

        module.mature_observation(
            observation=(
                observation
            ),

            anchor=(
                _anchor()
            ),

            completed_m5_bars=(
                _base_frame()
            ),
        )


def test_23_semantic_fingerprint_deterministic() -> None:

    frame: pd.DataFrame = (
        _base_frame(
            future_high_offset=3.0,
            future_low_offset=1.0,
        )
    )

    first = (
        _mature(
            frame
        )
    )

    second_frame = cast(
        pd.DataFrame,
        frame.copy(),
    )

    second = (
        _mature(
            second_frame
        )
    )

    assert (
        first.semantic_fingerprint()
        ==
        second.semantic_fingerprint()
    )


def test_24_no_performance_or_execution_authority() -> None:

    assert (
        module.OUTCOME_MATURATION_AUTHORIZED
        is True
    )

    assert (
        module.PERFORMANCE_EVALUATION_AUTHORIZED
        is False
    )

    assert (
        module.PNL_EVALUATION_AUTHORIZED
        is False
    )

    assert (
        module.LIVE_AUTHORIZED
        is False
    )

    assert (
        module.EXECUTION_AUTHORIZED
        is False
    )