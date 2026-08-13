"""
Offline deterministic tests for PulseViper PaperLedger v1.1.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest


pytestmark = pytest.mark.offline


paper_module: Any = importlib.import_module(
    "02_AI.Shadow.paper_ledger"
)

PaperLedger: Any = (
    paper_module.PaperLedger
)


def _market(
    direction: str = "BULLISH",
) -> pd.DataFrame:

    times = pd.date_range(
        "2026-01-01",
        periods=30,
        freq="min",
    )

    if direction == "BULLISH":

        close = np.arange(
            100.0,
            130.0,
        )

    else:

        close = np.arange(
            130.0,
            100.0,
            -1.0,
        )

    return pd.DataFrame(
        {
            "time": times,
            "open": close,
            "high": close + 0.6,
            "low": close - 0.4,
            "close": close,
        }
    )


def _enriched(
    direction: str = "BULLISH",
) -> pd.DataFrame:

    frame = _market(
        direction
    )

    frame[
        "trade_ready"
    ] = 0

    frame.loc[
        2,
        "trade_ready",
    ] = 1

    frame.loc[
        2,
        "confidence_direction",
    ] = direction

    frame.loc[
        2,
        "setup_direction",
    ] = direction

    frame.loc[
        2,
        "setup_id",
    ] = 7

    frame.loc[
        2,
        "setup_state",
    ] = "READY"

    frame.loc[
        2,
        "confidence_score",
    ] = 80.0

    frame.loc[
        2,
        "confidence_confluence",
    ] = 6

    frame.loc[
        2,
        "atr",
    ] = 2.0

    frame.loc[
        2,
        "pipeline_version",
    ] = "1.0"

    frame.loc[
        2,
        "pipeline_mode",
    ] = "SCALPING_TEMPORAL"

    return frame


def _make_ledger(
    store: Any,
    frame: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    int,
]:

    signals = store.capture_signals(
        frame,
        "XAUUSDm",
        "XAUUSDc",
    )

    return store.merge_new_signals(
        store._empty_frame(),
        signals,
        "BOOTSTRAP_BACKFILL",
    )


def _custom_path() -> pd.DataFrame:

    times = pd.date_range(
        "2026-01-01",
        periods=22,
        freq="min",
    )

    frame = pd.DataFrame(
        {
            "time": times,
            "open": 100.0,
            "high": 100.2,
            "low": 99.8,
            "close": 100.0,
        }
    )

    frame[
        "trade_ready"
    ] = 0

    frame.loc[
        0,
        "trade_ready",
    ] = 1

    frame.loc[
        0,
        "confidence_direction",
    ] = "BULLISH"

    frame.loc[
        0,
        "setup_direction",
    ] = "BULLISH"

    frame.loc[
        0,
        "setup_id",
    ] = 1

    frame.loc[
        0,
        "setup_state",
    ] = "READY"

    frame.loc[
        0,
        "confidence_score",
    ] = 80

    frame.loc[
        0,
        "confidence_confluence",
    ] = 6

    frame.loc[
        0,
        "atr",
    ] = 1.0

    return frame


def test_bullish_outcomes_and_first_passage(
    tmp_path: Path,
) -> None:

    store = PaperLedger(
        tmp_path
        /
        "ledger.csv"
    )

    frame = _enriched(
        "BULLISH"
    )

    (
        ledger,
        added,
    ) = _make_ledger(
        store,
        frame,
    )

    evaluated = store.evaluate(
        ledger,
        _market(
            "BULLISH"
        ),
    )

    row = evaluated.iloc[
        0
    ]

    assert added == 1

    assert (
        row[
            "status"
        ]
        ==
        "MATURED_20"
    )

    assert float(
        row[
            "net_5"
        ]
    ) == pytest.approx(
        5.0
    )

    assert float(
        row[
            "mfe_5"
        ]
    ) == pytest.approx(
        5.6
    )

    assert float(
        row[
            "mae_5"
        ]
    ) == pytest.approx(
        0.0
    )

    assert (
        row[
            "fp_1_result"
        ]
        ==
        "PROFIT_FIRST"
    )

    assert int(
        row[
            "fp_1_bar"
        ]
    ) == 1

    assert (
        row[
            "be_after_1_status"
        ]
        ==
        "HELD_20"
    )

    assert float(
        row[
            "be_after_1_net_20"
        ]
    ) == pytest.approx(
        20.0
    )

    assert int(
        row[
            "bars_to_mfe_20"
        ]
    ) == 20

    assert float(
        row[
            "extension_after_5_20"
        ]
    ) == pytest.approx(
        15.6
    )


def test_bearish_direction_adjustment(
    tmp_path: Path,
) -> None:

    store = PaperLedger(
        tmp_path
        /
        "ledger.csv"
    )

    (
        ledger,
        _,
    ) = _make_ledger(
        store,
        _enriched(
            "BEARISH"
        ),
    )

    row = store.evaluate(
        ledger,
        _market(
            "BEARISH"
        ),
    ).iloc[
        0
    ]

    assert float(
        row[
            "net_5"
        ]
    ) == pytest.approx(
        5.0
    )

    assert float(
        row[
            "mfe_5"
        ]
    ) == pytest.approx(
        5.4
    )

    assert (
        row[
            "fp_2_result"
        ]
        ==
        "PROFIT_FIRST"
    )


def test_ambiguous_same_bar_is_not_guessed(
    tmp_path: Path,
) -> None:

    store = PaperLedger(
        tmp_path
        /
        "ledger.csv"
    )

    frame = _custom_path()

    frame.loc[
        1,
        [
            "high",
            "low",
            "close",
        ],
    ] = [
        101.2,
        98.8,
        100.1,
    ]

    (
        ledger,
        _,
    ) = _make_ledger(
        store,
        frame,
    )

    row = store.evaluate(
        ledger,
        frame,
    ).iloc[
        0
    ]

    assert (
        row[
            "fp_1_result"
        ]
        ==
        "AMBIGUOUS_SAME_BAR"
    )

    assert int(
        row[
            "fp_1_bar"
        ]
    ) == 1


def test_breakeven_stops_only_after_activation_candle(
    tmp_path: Path,
) -> None:

    store = PaperLedger(
        tmp_path
        /
        "ledger.csv"
    )

    frame = _custom_path()

    frame.loc[
        1,
        [
            "high",
            "low",
            "close",
        ],
    ] = [
        101.4,
        99.5,
        101.0,
    ]

    frame.loc[
        2,
        [
            "high",
            "low",
            "close",
        ],
    ] = [
        102.0,
        99.9,
        101.5,
    ]

    frame.loc[
        3:20,
        "high",
    ] = 105.0

    frame.loc[
        3:20,
        "low",
    ] = 101.0

    frame.loc[
        20,
        "close",
    ] = 104.0

    (
        ledger,
        _,
    ) = _make_ledger(
        store,
        frame,
    )

    row = store.evaluate(
        ledger,
        frame,
    ).iloc[
        0
    ]

    assert (
        row[
            "be_after_1_status"
        ]
        ==
        "STOPPED_BE"
    )

    assert int(
        row[
            "be_after_1_activation_bar"
        ]
    ) == 1

    assert int(
        row[
            "be_after_1_exit_bar"
        ]
    ) == 2

    assert float(
        row[
            "be_after_1_net_20"
        ]
    ) == pytest.approx(
        0.0
    )


def test_continuation_structure_and_regime_telemetry(
    tmp_path: Path,
) -> None:

    store = PaperLedger(
        tmp_path
        /
        "ledger.csv"
    )

    frame = _custom_path()

    frame.loc[
        1:20,
        "close",
    ] = np.linspace(
        100.5,
        106.0,
        20,
    )

    frame.loc[
        1:20,
        "high",
    ] = (
        frame.loc[
            1:20,
            "close",
        ]
        +
        0.5
    )

    frame.loc[
        1:20,
        "low",
    ] = (
        frame.loc[
            1:20,
            "close",
        ]
        -
        0.3
    )

    frame[
        "bos_direction"
    ] = "NONE"

    frame[
        "internal_bos"
    ] = 0

    frame[
        "major_bos"
    ] = 0

    frame.loc[
        2,
        "bos_direction",
    ] = "BULLISH"

    frame.loc[
        2,
        "internal_bos",
    ] = 1

    frame.loc[
        6,
        "bos_direction",
    ] = "BEARISH"

    frame.loc[
        8,
        "bos_direction",
    ] = "BULLISH"

    frame.loc[
        8,
        "major_bos",
    ] = 1

    frame[
        "swing_scale"
    ] = "NONE"

    frame.loc[
        4,
        "swing_scale",
    ] = "INTERNAL"

    frame.loc[
        9,
        "swing_scale",
    ] = "MAJOR"

    frame[
        "structure_bias"
    ] = "NEUTRAL"

    frame.loc[
        5:20,
        "structure_bias",
    ] = "BULLISH"

    frame[
        "regime_state"
    ] = "RANGE_NORMAL_VOL"

    frame.loc[
        10:20,
        "regime_state",
    ] = "BULLISH_HIGH_VOL"

    frame[
        "regime_trend"
    ] = "RANGE"

    frame.loc[
        10:20,
        "regime_trend",
    ] = "BULLISH"

    frame[
        "regime_volatility"
    ] = "NORMAL"

    frame.loc[
        10:20,
        "regime_volatility",
    ] = "HIGH"

    (
        ledger,
        _,
    ) = _make_ledger(
        store,
        frame,
    )

    row = store.evaluate(
        ledger,
        frame,
    ).iloc[
        0
    ]

    assert int(
        row[
            "directional_bos_count_20"
        ]
    ) == 2

    assert int(
        row[
            "opposing_bos_count_20"
        ]
    ) == 1

    assert int(
        row[
            "directional_internal_bos_count_20"
        ]
    ) == 1

    assert int(
        row[
            "directional_major_bos_count_20"
        ]
    ) == 1

    assert int(
        row[
            "internal_swing_count_20"
        ]
    ) == 1

    assert int(
        row[
            "major_swing_count_20"
        ]
    ) == 1

    assert int(
        row[
            "structure_aligned_5"
        ]
    ) == 1

    assert (
        row[
            "regime_state_10"
        ]
        ==
        "BULLISH_HIGH_VOL"
    )


def test_duplicate_identity_and_roundtrip(
    tmp_path: Path,
) -> None:

    store = PaperLedger(
        tmp_path
        /
        "ledger.csv"
    )

    frame = _enriched(
        "BULLISH"
    )

    signals = store.capture_signals(
        frame,
        "XAUUSDm",
        "XAUUSDc",
    )

    (
        ledger,
        added,
    ) = store.merge_new_signals(
        store._empty_frame(),
        signals,
        "BOOTSTRAP_BACKFILL",
    )

    frame.loc[
        2,
        "setup_id",
    ] = 999

    signals_again = store.capture_signals(
        frame,
        "XAUUSDm",
        "XAUUSDc",
    )

    (
        ledger,
        added_again,
    ) = store.merge_new_signals(
        ledger,
        signals_again,
        "LIVE_SHADOW",
    )

    assert added == 1

    assert added_again == 0

    assert len(
        ledger
    ) == 1

    evaluated = store.evaluate(
        ledger,
        _market(
            "BULLISH"
        ),
    )

    store.save(
        evaluated
    )

    loaded = store.load()

    assert len(
        loaded
    ) == 1

    assert (
        loaded.iloc[
            0
        ][
            "ledger_version"
        ]
        ==
        "1.1"
    )

    assert (
        "fp_1_result"
        in loaded.columns
    )

    assert (
        "be_after_1_status"
        in loaded.columns
    )