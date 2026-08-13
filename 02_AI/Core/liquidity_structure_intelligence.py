"""
===============================================================================
Module      : liquidity_structure_intelligence.py
Project     : PulseViper XAU AI
Version     : 1.2
Purpose     : Causal Liquidity Clustering / Trap / Breakout Intelligence
===============================================================================

Research-only metadata layer.

This module consumes causal market-context and liquidity-lifecycle outputs.

It does NOT:
- open trades
- modify trade_ready
- modify Confidence
- modify SetupState
- modify BOS
- modify risk
- use future candles

Main responsibilities
---------------------
1. Group nearby contextual liquidity into clusters.
2. Separate EXTERNAL vs INTERNAL liquidity.
3. Detect MIXED confluence clusters.
4. Interpret causal lifecycle events:
   - liquidity sweep traps
   - breakout attempts
   - accepted breakouts
   - failed breakouts / reclaims
5. Preserve range location context for later entry research.

Important
---------
A cluster is NOT automatically a strong trading level.

Cluster count and composition are telemetry only.
Actual usefulness must be validated from outcomes.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class LiquidityStructureIntelligence:
    VERSION = "1.2"

    MODE = "CAUSAL_RESEARCH_METADATA_ONLY"

    HIGH_SOURCES = (
        (
            "PDH",
            "ctx_pdh",
            "EXTERNAL",
        ),
        (
            "PWH",
            "ctx_pwh",
            "EXTERNAL",
        ),
        (
            "PREV_ASIA_HIGH",
            "ctx_prev_asia_high",
            "EXTERNAL",
        ),
        (
            "PREV_LONDON_HIGH",
            "ctx_prev_london_high",
            "EXTERNAL",
        ),
        (
            "PREV_NEW_YORK_HIGH",
            "ctx_prev_new_york_high",
            "EXTERNAL",
        ),
        (
            "MICRO_HIGH",
            "ctx_nearest_micro_high",
            "INTERNAL",
        ),
        (
            "INTERNAL_HIGH",
            "ctx_nearest_internal_high",
            "INTERNAL",
        ),
        (
            "MAJOR_HIGH",
            "ctx_nearest_major_high",
            "EXTERNAL",
        ),
    )

    LOW_SOURCES = (
        (
            "PDL",
            "ctx_pdl",
            "EXTERNAL",
        ),
        (
            "PWL",
            "ctx_pwl",
            "EXTERNAL",
        ),
        (
            "PREV_ASIA_LOW",
            "ctx_prev_asia_low",
            "EXTERNAL",
        ),
        (
            "PREV_LONDON_LOW",
            "ctx_prev_london_low",
            "EXTERNAL",
        ),
        (
            "PREV_NEW_YORK_LOW",
            "ctx_prev_new_york_low",
            "EXTERNAL",
        ),
        (
            "MICRO_LOW",
            "ctx_nearest_micro_low",
            "INTERNAL",
        ),
        (
            "INTERNAL_LOW",
            "ctx_nearest_internal_low",
            "INTERNAL",
        ),
        (
            "MAJOR_LOW",
            "ctx_nearest_major_low",
            "EXTERNAL",
        ),
    )

    def __init__(
        self,
        cluster_tolerance_atr: float = 0.10,
    ) -> None:

        if (
            cluster_tolerance_atr
            <
            0.0
        ):
            raise ValueError(
                "cluster_tolerance_atr cannot be negative"
            )

        self.cluster_tolerance_atr = float(
            cluster_tolerance_atr
        )

    # =========================================================================
    # Validation / conversion
    # =========================================================================

    @staticmethod
    def _validate(
        df: pd.DataFrame,
    ) -> None:

        if not isinstance(
            df,
            pd.DataFrame,
        ):
            raise TypeError(
                "LiquidityStructureIntelligence input "
                "must be a pandas DataFrame"
            )

        required = {
            "close",
        }

        missing = (
            required
            -
            set(
                df.columns
            )
        )

        if missing:
            raise ValueError(
                "Missing required columns: "
                +
                ", ".join(
                    sorted(
                        missing
                    )
                )
            )

    @staticmethod
    def _safe_float(
        value: Any,
    ) -> float:
        """
        Type-safe scalar conversion.

        Avoids pandas Scalar -> float Pylance errors.
        """

        if (
            value is None
            or
            isinstance(
                value,
                complex,
            )
        ):
            return float(
                "nan"
            )

        try:

            if bool(
                pd.isna(
                    value
                )
            ):
                return float(
                    "nan"
                )

        except (
            TypeError,
            ValueError,
        ):
            return float(
                "nan"
            )

        try:

            number = float(
                value
            )

        except (
            TypeError,
            ValueError,
            OverflowError,
        ):
            return float(
                "nan"
            )

        if not np.isfinite(
            number
        ):
            return float(
                "nan"
            )

        return number

    # =========================================================================
    # Lifecycle interpretation
    # =========================================================================

    @staticmethod
    def _event_interpretation(
        event: str,
        side: str,
    ) -> tuple[
        str,
        str,
    ]:

        event = (
            event
            .upper()
            .strip()
        )

        side = (
            side
            .upper()
            .strip()
        )

        # ---------------------------------------------------------------------
        # Liquidity sweep / raid
        # ---------------------------------------------------------------------

        if event == "SWEPT":

            if side == "HIGH":
                return (
                    "BUY_SIDE_SWEEP_TRAP",
                    "BEARISH",
                )

            if side == "LOW":
                return (
                    "SELL_SIDE_SWEEP_TRAP",
                    "BULLISH",
                )

        # ---------------------------------------------------------------------
        # First close beyond liquidity
        # ---------------------------------------------------------------------

        if event == "BROKEN":

            if side == "HIGH":
                return (
                    "UPSIDE_BREAKOUT_ATTEMPT",
                    "BULLISH",
                )

            if side == "LOW":
                return (
                    "DOWNSIDE_BREAKOUT_ATTEMPT",
                    "BEARISH",
                )

        # ---------------------------------------------------------------------
        # Multiple closes beyond liquidity
        # ---------------------------------------------------------------------

        if event == "ACCEPTED_BEYOND":

            if side == "HIGH":
                return (
                    "UPSIDE_BREAKOUT_ACCEPTED",
                    "BULLISH",
                )

            if side == "LOW":
                return (
                    "DOWNSIDE_BREAKOUT_ACCEPTED",
                    "BEARISH",
                )

        # ---------------------------------------------------------------------
        # Breakout lost / level reclaimed
        # ---------------------------------------------------------------------

        if event == "RECLAIMED":

            if side == "HIGH":
                return (
                    "FAILED_UPSIDE_BREAKOUT",
                    "BEARISH",
                )

            if side == "LOW":
                return (
                    "FAILED_DOWNSIDE_BREAKOUT",
                    "BULLISH",
                )

        if event == "TESTED":
            return (
                "LIQUIDITY_TEST",
                "NEUTRAL",
            )

        return (
            "NONE",
            "NEUTRAL",
        )

    # =========================================================================
    # Level collection
    # =========================================================================

    def _collect_levels(
        self,
        df: pd.DataFrame,
        index: int,
        sources: tuple[
            tuple[
                str,
                str,
                str,
            ],
            ...,
        ],
    ) -> list[
        tuple[
            str,
            float,
            str,
        ]
    ]:

        levels: list[
            tuple[
                str,
                float,
                str,
            ]
        ] = []

        for (
            label,
            column,
            classification,
        ) in sources:

            if column not in df.columns:
                continue

            price = self._safe_float(
                df[
                    column
                ].iat[
                    index
                ]
            )

            if not np.isfinite(
                price
            ):
                continue

            levels.append(
                (
                    label,
                    price,
                    classification,
                )
            )

        return levels

    # =========================================================================
    # Cluster selection
    # =========================================================================

    def _nearest_cluster(
        self,
        levels: list[
            tuple[
                str,
                float,
                str,
            ]
        ],
        current_price: float,
        atr: float,
        side: str,
    ) -> tuple[
        float,
        str,
        int,
        int,
        int,
        str,
        float,
    ]:

        if (
            not levels
            or
            not np.isfinite(
                current_price
            )
        ):
            return (
                np.nan,
                "NONE",
                0,
                0,
                0,
                "NONE",
                np.nan,
            )

        if side == "ABOVE":

            eligible = [
                item
                for item in levels
                if (
                    item[
                        1
                    ]
                    >=
                    current_price
                )
            ]

            eligible.sort(
                key=lambda item: (
                    item[
                        1
                    ]
                    -
                    current_price,
                    item[
                        1
                    ],
                    item[
                        0
                    ],
                )
            )

        else:

            eligible = [
                item
                for item in levels
                if (
                    item[
                        1
                    ]
                    <=
                    current_price
                )
            ]

            eligible.sort(
                key=lambda item: (
                    current_price
                    -
                    item[
                        1
                    ],
                    -
                    item[
                        1
                    ],
                    item[
                        0
                    ],
                )
            )

        if not eligible:

            return (
                np.nan,
                "NONE",
                0,
                0,
                0,
                "NONE",
                np.nan,
            )

        anchor = float(
            eligible[
                0
            ][
                1
            ]
        )

        if (
            np.isfinite(
                atr
            )
            and
            atr > 0.0
        ):

            tolerance = (
                atr
                *
                self.cluster_tolerance_atr
            )

        else:

            tolerance = 0.0

        cluster = [
            item

            for item
            in eligible

            if (
                abs(
                    item[
                        1
                    ]
                    -
                    anchor
                )
                <=
                (
                    tolerance
                    +
                    1e-12
                )
            )
        ]

        prices = [
            item[
                1
            ]
            for item in cluster
        ]

        cluster_price = float(
            np.mean(
                prices
            )
        )

        labels = "|".join(
            sorted(
                item[
                    0
                ]
                for item in cluster
            )
        )

        external_count = sum(
            1
            for item in cluster
            if (
                item[
                    2
                ]
                ==
                "EXTERNAL"
            )
        )

        internal_count = sum(
            1
            for item in cluster
            if (
                item[
                    2
                ]
                ==
                "INTERNAL"
            )
        )

        if (
            external_count > 0
            and
            internal_count > 0
        ):

            cluster_type = (
                "MIXED"
            )

        elif external_count > 0:

            cluster_type = (
                "EXTERNAL"
            )

        else:

            cluster_type = (
                "INTERNAL"
            )

        if side == "ABOVE":

            distance = (
                cluster_price
                -
                current_price
            )

        else:

            distance = (
                current_price
                -
                cluster_price
            )

        return (
            cluster_price,
            labels,
            len(
                cluster
            ),
            external_count,
            internal_count,
            cluster_type,
            float(
                distance
            ),
        )

    # =========================================================================
    # Generate
    # =========================================================================

    def generate(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        self._validate(
            data
        )

        df = (
            data
            .copy()
            .reset_index(
                drop=True
            )
        )

        row_count = len(
            df
        )

        close = (
            pd.to_numeric(
                df[
                    "close"
                ],
                errors="coerce",
            )
            .to_numpy(
                dtype=float
            )
        )

        if "atr" in df.columns:

            atr = (
                pd.to_numeric(
                    df[
                        "atr"
                    ],
                    errors="coerce",
                )
                .to_numpy(
                    dtype=float
                )
            )

        else:

            atr = np.full(
                row_count,
                np.nan,
                dtype=float,
            )

        # ---------------------------------------------------------------------
        # Cluster outputs
        # ---------------------------------------------------------------------

        above_price = np.full(
            row_count,
            np.nan,
            dtype=float,
        )

        below_price = np.full(
            row_count,
            np.nan,
            dtype=float,
        )

        above_sources = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        below_sources = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        above_count = np.zeros(
            row_count,
            dtype=np.int64,
        )

        below_count = np.zeros(
            row_count,
            dtype=np.int64,
        )

        above_external = np.zeros(
            row_count,
            dtype=np.int64,
        )

        below_external = np.zeros(
            row_count,
            dtype=np.int64,
        )

        above_internal = np.zeros(
            row_count,
            dtype=np.int64,
        )

        below_internal = np.zeros(
            row_count,
            dtype=np.int64,
        )

        above_type = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        below_type = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        above_distance = np.full(
            row_count,
            np.nan,
            dtype=float,
        )

        below_distance = np.full(
            row_count,
            np.nan,
            dtype=float,
        )

        # ---------------------------------------------------------------------
        # Event interpretation outputs
        # ---------------------------------------------------------------------

        interpretation = np.full(
            row_count,
            "NONE",
            dtype=object,
        )

        event_bias = np.full(
            row_count,
            "NEUTRAL",
            dtype=object,
        )

        trap_flag = np.zeros(
            row_count,
            dtype=np.int8,
        )

        breakout_attempt_flag = np.zeros(
            row_count,
            dtype=np.int8,
        )

        breakout_accepted_flag = np.zeros(
            row_count,
            dtype=np.int8,
        )

        failed_breakout_flag = np.zeros(
            row_count,
            dtype=np.int8,
        )

        # =====================================================================
        # Chronological row evaluation
        # =====================================================================

        for i in range(
            row_count
        ):

            high_levels = self._collect_levels(
                df=df,
                index=i,
                sources=self.HIGH_SOURCES,
            )

            low_levels = self._collect_levels(
                df=df,
                index=i,
                sources=self.LOW_SOURCES,
            )

            (
                above_price[
                    i
                ],
                above_sources[
                    i
                ],
                above_count[
                    i
                ],
                above_external[
                    i
                ],
                above_internal[
                    i
                ],
                above_type[
                    i
                ],
                above_distance[
                    i
                ],
            ) = self._nearest_cluster(
                levels=high_levels,
                current_price=close[
                    i
                ],
                atr=atr[
                    i
                ],
                side="ABOVE",
            )

            (
                below_price[
                    i
                ],
                below_sources[
                    i
                ],
                below_count[
                    i
                ],
                below_external[
                    i
                ],
                below_internal[
                    i
                ],
                below_type[
                    i
                ],
                below_distance[
                    i
                ],
            ) = self._nearest_cluster(
                levels=low_levels,
                current_price=close[
                    i
                ],
                atr=atr[
                    i
                ],
                side="BELOW",
            )

            # -----------------------------------------------------------------
            # Lifecycle event interpretation
            # -----------------------------------------------------------------

            if "liq_event_type" in df.columns:

                event = str(
                    df[
                        "liq_event_type"
                    ].iat[
                        i
                    ]
                )

            else:

                event = (
                    "NONE"
                )

            if "liq_event_side" in df.columns:

                side = str(
                    df[
                        "liq_event_side"
                    ].iat[
                        i
                    ]
                )

            else:

                side = (
                    "NONE"
                )

            (
                interpreted,
                bias,
            ) = self._event_interpretation(
                event=event,
                side=side,
            )

            interpretation[
                i
            ] = interpreted

            event_bias[
                i
            ] = bias

            trap_flag[
                i
            ] = int(
                interpreted
                in {
                    "BUY_SIDE_SWEEP_TRAP",
                    "SELL_SIDE_SWEEP_TRAP",
                }
            )

            breakout_attempt_flag[
                i
            ] = int(
                interpreted
                in {
                    "UPSIDE_BREAKOUT_ATTEMPT",
                    "DOWNSIDE_BREAKOUT_ATTEMPT",
                }
            )

            breakout_accepted_flag[
                i
            ] = int(
                interpreted
                in {
                    "UPSIDE_BREAKOUT_ACCEPTED",
                    "DOWNSIDE_BREAKOUT_ACCEPTED",
                }
            )

            failed_breakout_flag[
                i
            ] = int(
                interpreted
                in {
                    "FAILED_UPSIDE_BREAKOUT",
                    "FAILED_DOWNSIDE_BREAKOUT",
                }
            )

        # =====================================================================
        # Assign outputs
        # =====================================================================

        result = df.copy()

        # ---------------------------------------------------------------------
        # Above cluster
        # ---------------------------------------------------------------------

        result[
            "liqintel_above_cluster_price"
        ] = above_price

        result[
            "liqintel_above_cluster_sources"
        ] = above_sources

        result[
            "liqintel_above_cluster_count"
        ] = above_count

        result[
            "liqintel_above_external_count"
        ] = above_external

        result[
            "liqintel_above_internal_count"
        ] = above_internal

        result[
            "liqintel_above_cluster_type"
        ] = above_type

        result[
            "liqintel_above_distance"
        ] = above_distance

        # ---------------------------------------------------------------------
        # Below cluster
        # ---------------------------------------------------------------------

        result[
            "liqintel_below_cluster_price"
        ] = below_price

        result[
            "liqintel_below_cluster_sources"
        ] = below_sources

        result[
            "liqintel_below_cluster_count"
        ] = below_count

        result[
            "liqintel_below_external_count"
        ] = below_external

        result[
            "liqintel_below_internal_count"
        ] = below_internal

        result[
            "liqintel_below_cluster_type"
        ] = below_type

        result[
            "liqintel_below_distance"
        ] = below_distance

        # ---------------------------------------------------------------------
        # ATR-normalized distance
        # ---------------------------------------------------------------------

        safe_atr = np.where(
            (
                np.isfinite(
                    atr
                )
                &
                (
                    atr
                    >
                    0.0
                )
            ),
            atr,
            np.nan,
        )

        result[
            "liqintel_above_distance_atr"
        ] = (
            above_distance
            /
            safe_atr
        )

        result[
            "liqintel_below_distance_atr"
        ] = (
            below_distance
            /
            safe_atr
        )

        # ---------------------------------------------------------------------
        # Event meaning
        # ---------------------------------------------------------------------

        result[
            "liqintel_event_interpretation"
        ] = interpretation

        result[
            "liqintel_event_bias"
        ] = event_bias

        result[
            "liqintel_trap_flag"
        ] = trap_flag

        result[
            "liqintel_breakout_attempt_flag"
        ] = breakout_attempt_flag

        result[
            "liqintel_breakout_accepted_flag"
        ] = breakout_accepted_flag

        result[
            "liqintel_failed_breakout_flag"
        ] = failed_breakout_flag

        # ---------------------------------------------------------------------
        # Range context
        # ---------------------------------------------------------------------

        if "ctx_range_zone" in df.columns:

            result[
                "liqintel_range_location"
            ] = (
                df[
                    "ctx_range_zone"
                ]
                .astype(
                    str
                )
            )

        else:

            result[
                "liqintel_range_location"
            ] = (
                "UNKNOWN"
            )

        # ---------------------------------------------------------------------
        # Metadata
        # ---------------------------------------------------------------------

        result[
            "liqintel_version"
        ] = self.VERSION

        result[
            "liqintel_mode"
        ] = self.MODE

        return result


liquidity_structure_intelligence = (
    LiquidityStructureIntelligence()
)