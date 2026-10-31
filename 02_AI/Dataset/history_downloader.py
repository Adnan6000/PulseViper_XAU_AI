"""
===============================================================================
Module      : history_downloader.py
Project     : PulseViper XAU AI
Version     : 2.0
Purpose     : Broker-Aware Multi-Timeframe Historical Data Downloader
===============================================================================

Responsibilities
----------------
- fetch historical XAU / Gold data through the canonical MT5DataFetcher
- preserve the actual broker-resolved symbol in exported dataset names
- export deterministic multi-timeframe datasets
- expose download metadata for future dataset lineage

This module does NOT:
- generate trading signals
- generate labels
- train models
- make execution decisions
"""

from __future__ import annotations

import importlib
import sys

from datetime import datetime
from pathlib import Path
from typing import Any

import MetaTrader5 as mt5
import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


fetcher_module: Any = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
)

fetcher: Any = fetcher_module.fetcher


RAW_DIR = (
    ROOT_DIR
    / "01_Data"
    / "Raw"
)


class HistoryDownloader:
    """
    Broker-aware historical data downloader.

    The requested symbol is treated as a preference.
    Exported datasets use the actual MT5-resolved broker symbol.
    """

    TIMEFRAMES: dict[str, int] = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
    }

    def __init__(
        self,
        output_directory: Path | None = None,
    ) -> None:

        self.output_directory = (
            output_directory
            if output_directory is not None
            else RAW_DIR
        )

        self.last_exports: list[
            dict[str, Any]
        ] = []

    @staticmethod
    def _safe_filename_symbol(
        symbol: str,
    ) -> str:

        cleaned = "".join(
            character
            for character in symbol
            if (
                character.isalnum()
                or character
                in (
                    "-",
                    "_",
                    ".",
                )
            )
        )

        return (
            cleaned
            if cleaned
            else "UNKNOWN"
        )

    def download_timeframe(
        self,
        symbol: str,
        timeframe_name: str,
        timeframe: int,
        bars: int,
    ) -> dict[str, Any]:

        if bars <= 0:
            raise ValueError(
                "bars must be greater than zero"
            )

        dataframe: pd.DataFrame = fetcher.fetch(
            symbol=symbol,
            timeframe=timeframe,
            bars=bars,
        )

        if dataframe.empty:
            raise RuntimeError(
                (
                    "No historical bars returned for "
                    f"{timeframe_name}"
                )
            )

        resolved_symbol = str(
            getattr(
                fetcher,
                "last_resolved_symbol",
                "",
            )
            or symbol
        )

        safe_symbol = self._safe_filename_symbol(
            resolved_symbol
        )

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        date_stamp = datetime.utcnow().strftime(
            "%Y%m%d"
        )

        filename = (
            f"{safe_symbol}_"
            f"{timeframe_name}_"
            f"{date_stamp}.csv"
        )

        path = (
            self.output_directory
            / filename
        )

        dataframe.to_csv(
            path,
            index=False,
        )

        start_time: Any = None
        end_time: Any = None

        if (
            "time"
            in dataframe.columns
            and
            not dataframe.empty
        ):

            start_time = dataframe[
                "time"
            ].iloc[
                0
            ]

            end_time = dataframe[
                "time"
            ].iloc[
                -1
            ]

        return {
            "requested_symbol": (
                symbol
            ),

            "resolved_symbol": (
                resolved_symbol
            ),

            "timeframe": (
                timeframe_name
            ),

            "bars": int(
                len(
                    dataframe
                )
            ),

            "start_time": (
                start_time
            ),

            "end_time": (
                end_time
            ),

            "path": (
                path
            ),
        }

    def download(
        self,
        symbol: str = "XAUUSDm",
        bars: int = 100000,
    ) -> list[Path]:

        if bars <= 0:
            raise ValueError(
                "bars must be greater than zero"
            )

        self.last_exports = []

        exported_paths: list[
            Path
        ] = []

        for (
            timeframe_name,
            timeframe_value,
        ) in self.TIMEFRAMES.items():

            print(
                f"Downloading {timeframe_name}..."
            )

            metadata = self.download_timeframe(
                symbol=symbol,
                timeframe_name=timeframe_name,
                timeframe=timeframe_value,
                bars=bars,
            )

            self.last_exports.append(
                metadata
            )

            path = metadata[
                "path"
            ]

            exported_paths.append(
                path
            )

            print(
                (
                    f"{timeframe_name}: "
                    f"{metadata['bars']} bars | "
                    f"broker={metadata['resolved_symbol']} | "
                    f"{path}"
                )
            )

        return exported_paths


downloader = HistoryDownloader()