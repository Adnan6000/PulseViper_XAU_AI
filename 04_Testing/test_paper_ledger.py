"""
Offline deterministic tests for PulseViper shadow paper ledger.
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
    direction: str,
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
    direction: str,
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


def test_bullish_outcomes_are_direction_adjusted(
    tmp_path: Path,
) -> None:

    store = PaperLedger(
        tmp_path
        /
        "ledger.csv"
    )

    enriched = _enriched(
        "BULLISH"
    )

    signals = store.capture_signals(
        enriched,
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

    assert int(
        row[
            "target_5_hit"
        ]
    ) == 1

    assert int(
        row[
            "target_5_bars"
        ]
    ) == 5


def test_bearish_outcomes_are_direction_adjusted(
    tmp_path: Path,
) -> None:

    store = PaperLedger(
        tmp_path
        /
        "ledger.csv"
    )

    enriched = _enriched(
        "BEARISH"
    )

    signals = store.capture_signals(
        enriched,
        "XAUUSDm",
        "XAUUSDc",
    )

    (
        ledger,
        _,
    ) = store.merge_new_signals(
        store._empty_frame(),
        signals,
        "BOOTSTRAP_BACKFILL",
    )

    evaluated = store.evaluate(
        ledger,
        _market(
            "BEARISH"
        ),
    )

    row = evaluated.iloc[
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

    assert float(
        row[
            "mae_5"
        ]
    ) == pytest.approx(
        0.0
    )

    assert int(
        row[
            "target_5_hit"
        ]
    ) == 1


def test_event_identity_is_stable_when_setup_id_changes(
    tmp_path: Path,
) -> None:

    store = PaperLedger(
        tmp_path
        /
        "ledger.csv"
    )

    enriched = _enriched(
        "BULLISH"
    )

    first = store.capture_signals(
        enriched,
        "XAUUSDm",
        "XAUUSDc",
    )

    (
        ledger,
        added,
    ) = store.merge_new_signals(
        store._empty_frame(),
        first,
        "BOOTSTRAP_BACKFILL",
    )

    assert added == 1

    enriched.loc[
        2,
        "setup_id",
    ] = 9999

    second = store.capture_signals(
        enriched,
        "XAUUSDm",
        "XAUUSDc",
    )

    (
        ledger,
        added_again,
    ) = store.merge_new_signals(
        ledger,
        second,
        "LIVE_SHADOW",
    )

    assert added_again == 0

    assert len(
        ledger
    ) == 1


def test_save_load_round_trip(
    tmp_path: Path,
) -> None:

    path = (
        tmp_path
        /
        "ledger.csv"
    )

    store = PaperLedger(
        path
    )

    signals = store.capture_signals(
        _enriched(
            "BULLISH"
        ),
        "XAUUSDm",
        "XAUUSDc",
    )

    (
        ledger,
        _,
    ) = store.merge_new_signals(
        store._empty_frame(),
        signals,
        "BOOTSTRAP_BACKFILL",
    )

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

    assert path.exists()

    assert len(
        loaded
    ) == 1

    assert (
        loaded.iloc[
            0
        ][
            "event_id"
        ]
        ==
        evaluated.iloc[
            0
        ][
            "event_id"
        ]
    )

    assert (
        loaded.iloc[
            0
        ][
            "status"
        ]
        ==
        "MATURED_20"
    )