"""
===============================================================================
Module      : fvg_mitigation_engine.py
Project     : PulseViper XAU AI
Version     : 1.2
Author      : Muhammad Adnan
Purpose     : Causal FVG Mitigation, Rejection & Event Identity Engine
===============================================================================

Responsibilities
----------------
- maintain FVG lifecycle chronologically
- detect rejection
- detect full mitigation
- preserve exact FVG ID and direction for every lifecycle event
- expose all same-candle interactions for Temporal Setup Engine
- preserve legacy mitigation/rejection output columns

Important
---------
A candle may interact with more than one active FVG.

Therefore this engine exposes:

    fvg_interaction_events

as a list of dictionaries containing ALL events on that candle.

Scalar columns such as:

    fvg_interaction_id
    fvg_interaction_direction
    fvg_interaction_type

represent the strongest primary interaction only.
"""

from __future__ import annotations

from typing import Any

import pandas as pd


class FVGMitigationEngine:

    def __init__(
        self,
        full_mitigation: float = 1.0,
        rejection_threshold: float = 0.25,
    ) -> None:

        if not (
            0.0
            <= rejection_threshold
            <= 1.0
        ):
            raise ValueError(
                "rejection_threshold must be between 0 and 1"
            )

        if full_mitigation <= 0.0:
            raise ValueError(
                "full_mitigation must be greater than zero"
            )

        self.full_mitigation = float(
            full_mitigation
        )

        self.rejection_threshold = float(
            rejection_threshold
        )

    # =========================================================================
    # Helpers
    # =========================================================================

    @staticmethod
    def _to_float(
        value: Any,
        default: float = 0.0,
    ) -> float:

        if value is None:
            return default

        try:

            if pd.isna(
                value
            ):
                return default

        except (
            TypeError,
            ValueError,
        ):
            return default

        try:

            return float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            return default

    # =========================================================================
    # Validation
    # =========================================================================

    @staticmethod
    def _validate_input(
        df: pd.DataFrame,
    ) -> None:

        required = {
            "high",
            "low",
            "close",
            "fvg_id",
            "bullish_fvg",
            "bearish_fvg",
            "fvg_high",
            "fvg_low",
        }

        missing = (
            required
            - set(
                df.columns
            )
        )

        if missing:

            raise ValueError(
                "Missing required FVG columns: "
                + ", ".join(
                    sorted(
                        missing
                    )
                )
            )

    # =========================================================================
    # Primary Event Selection
    # =========================================================================

    @staticmethod
    def _select_primary_event(
        events: list[
            dict[str, Any]
        ],
    ) -> dict[str, Any] | None:

        if not events:
            return None

        priority = {
            "MITIGATION": 1,
            "REJECTION": 2,
        }

        return max(
            events,
            key=lambda event: (
                float(
                    event[
                        "fill_percent"
                    ]
                ),
                priority.get(
                    str(
                        event[
                            "event_type"
                        ]
                    ),
                    0,
                ),
            ),
        )

    # =========================================================================
    # Main
    # =========================================================================

    def generate(
        self,
        data: pd.DataFrame,
    ) -> pd.DataFrame:

        df = data.copy()

        self._validate_input(
            df
        )

        row_count = len(
            df
        )

        # ---------------------------------------------------------------------
        # Legacy lifecycle outputs
        # ---------------------------------------------------------------------

        df["fvg_mitigated"] = 0

        df["fvg_active"] = 0

        df["fvg_fill_percent"] = 0.0

        df["fvg_mitigation_index"] = -1

        df[
            "fvg_mitigation_price"
        ] = float(
            "nan"
        )

        df["fvg_rejection"] = 0

        df[
            "fvg_rejection_strength"
        ] = 0.0

        # ---------------------------------------------------------------------
        # Explicit rejection identity
        # ---------------------------------------------------------------------

        df["fvg_rejection_id"] = 0

        df[
            "fvg_rejection_direction"
        ] = "NONE"

        # ---------------------------------------------------------------------
        # Explicit mitigation identity
        # ---------------------------------------------------------------------

        df["fvg_mitigation_id"] = 0

        df[
            "fvg_mitigation_direction"
        ] = "NONE"

        # ---------------------------------------------------------------------
        # Unified primary interaction
        # ---------------------------------------------------------------------

        df["fvg_interaction"] = 0

        df["fvg_interaction_id"] = 0

        df[
            "fvg_interaction_direction"
        ] = "NONE"

        df[
            "fvg_interaction_type"
        ] = "NONE"

        df[
            "fvg_interaction_fill_percent"
        ] = 0.0

        df[
            "fvg_interaction_count"
        ] = 0

        # ---------------------------------------------------------------------
        # IMPORTANT
        #
        # Do NOT assign list[dict] through df.at[].
        #
        # Pandas/Pylance types df.at assignments as scalar values.
        # Keep object events in a Python buffer and assign the complete
        # object Series after chronological processing.
        # ---------------------------------------------------------------------

        interaction_events_buffer: list[
            list[
                dict[str, Any]
            ]
        ] = [
            []
            for _ in range(
                row_count
            )
        ]

        # ---------------------------------------------------------------------
        # Active causal FVG registry
        # ---------------------------------------------------------------------

        active_fvgs: dict[
            int,
            dict[str, Any],
        ] = {}

        # =========================================================================
        # Chronological Replay
        # =========================================================================

        for i in range(
            row_count
        ):

            row = df.iloc[i]

            row_events: list[
                dict[str, Any]
            ] = []

            # =====================================================================
            # STEP 1
            # Register new FVG created on current candle.
            # =====================================================================

            raw_fvg_id = (
                self._to_float(
                    row["fvg_id"],
                    default=0.0,
                )
            )

            if raw_fvg_id > 0.0:

                current_fvg_id = int(
                    raw_fvg_id
                )

                bullish = (
                    self._to_float(
                        row[
                            "bullish_fvg"
                        ]
                    )
                )

                bearish = (
                    self._to_float(
                        row[
                            "bearish_fvg"
                        ]
                    )
                )

                direction = "NONE"

                if bullish == 1.0:

                    direction = (
                        "BULLISH"
                    )

                elif bearish == 1.0:

                    direction = (
                        "BEARISH"
                    )

                zone_high = (
                    self._to_float(
                        row[
                            "fvg_high"
                        ]
                    )
                )

                zone_low = (
                    self._to_float(
                        row[
                            "fvg_low"
                        ]
                    )
                )

                if (
                    direction
                    != "NONE"
                    and zone_high
                    > zone_low
                ):

                    active_fvgs[
                        current_fvg_id
                    ] = {
                        "fvg_id": (
                            current_fvg_id
                        ),
                        "direction": (
                            direction
                        ),
                        "high": (
                            zone_high
                        ),
                        "low": (
                            zone_low
                        ),
                        "origin_index": (
                            i
                        ),
                    }

            # =====================================================================
            # STEP 2
            # Evaluate previously existing FVGs.
            # =====================================================================

            if active_fvgs:

                candle_high = (
                    self._to_float(
                        row[
                            "high"
                        ]
                    )
                )

                candle_low = (
                    self._to_float(
                        row[
                            "low"
                        ]
                    )
                )

                candle_close = (
                    self._to_float(
                        row[
                            "close"
                        ]
                    )
                )

                for (
                    current_id,
                    zone,
                ) in list(
                    active_fvgs.items()
                ):

                    origin_index = int(
                        zone[
                            "origin_index"
                        ]
                    )

                    # -------------------------------------------------------------
                    # Causality:
                    # never interact on creation candle.
                    # -------------------------------------------------------------

                    if i <= origin_index:
                        continue

                    direction = str(
                        zone[
                            "direction"
                        ]
                    )

                    zone_high = float(
                        zone[
                            "high"
                        ]
                    )

                    zone_low = float(
                        zone[
                            "low"
                        ]
                    )

                    zone_size = (
                        zone_high
                        - zone_low
                    )

                    if zone_size <= 0.0:

                        del active_fvgs[
                            current_id
                        ]

                        continue

                    # =============================================================
                    # BULLISH FVG
                    # =============================================================

                    if (
                        direction
                        == "BULLISH"
                    ):

                        if (
                            candle_low
                            > zone_high
                        ):
                            continue

                        penetration = (
                            zone_high
                            - candle_low
                        )

                        fill_ratio = (
                            penetration
                            / zone_size
                        )

                        fill_ratio = max(
                            0.0,
                            min(
                                1.0,
                                fill_ratio,
                            ),
                        )

                        fill_percent = (
                            fill_ratio
                            * 100.0
                        )

                        rejection = (
                            candle_close
                            > zone_high
                            and
                            fill_ratio
                            >= self.rejection_threshold
                        )

                        fully_mitigated = (
                            fill_ratio
                            >= self.full_mitigation
                            or
                            candle_low
                            <= zone_low
                        )

                        current_row_fill = (
                            self._to_float(
                                df.at[
                                    df.index[i],
                                    "fvg_fill_percent",
                                ]
                            )
                        )

                        if (
                            fill_percent
                            > current_row_fill
                        ):

                            df.at[
                                df.index[i],
                                "fvg_fill_percent",
                            ] = round(
                                fill_percent,
                                2,
                            )

                        # ---------------------------------------------------------
                        # Rejection
                        # ---------------------------------------------------------

                        if rejection:

                            rejection_event: dict[
                                str,
                                Any,
                            ] = {
                                "fvg_id": (
                                    int(
                                        current_id
                                    )
                                ),
                                "direction": (
                                    "BULLISH"
                                ),
                                "event_type": (
                                    "REJECTION"
                                ),
                                "fill_percent": (
                                    round(
                                        fill_percent,
                                        2,
                                    )
                                ),
                                "index": (
                                    i
                                ),
                            }

                            row_events.append(
                                rejection_event
                            )

                            df.at[
                                df.index[i],
                                "fvg_rejection",
                            ] = 1

                            existing_strength = (
                                self._to_float(
                                    df.at[
                                        df.index[i],
                                        "fvg_rejection_strength",
                                    ]
                                )
                            )

                            if (
                                fill_percent
                                >= existing_strength
                            ):

                                df.at[
                                    df.index[i],
                                    "fvg_rejection_strength",
                                ] = round(
                                    fill_percent,
                                    2,
                                )

                                df.at[
                                    df.index[i],
                                    "fvg_rejection_id",
                                ] = int(
                                    current_id
                                )

                                df.at[
                                    df.index[i],
                                    "fvg_rejection_direction",
                                ] = (
                                    "BULLISH"
                                )

                        # ---------------------------------------------------------
                        # Full mitigation
                        # ---------------------------------------------------------

                        if fully_mitigated:

                            mitigation_event: dict[
                                str,
                                Any,
                            ] = {
                                "fvg_id": (
                                    int(
                                        current_id
                                    )
                                ),
                                "direction": (
                                    "BULLISH"
                                ),
                                "event_type": (
                                    "MITIGATION"
                                ),
                                "fill_percent": (
                                    round(
                                        fill_percent,
                                        2,
                                    )
                                ),
                                "index": (
                                    i
                                ),
                            }

                            row_events.append(
                                mitigation_event
                            )

                            df.at[
                                df.index[i],
                                "fvg_mitigated",
                            ] = 1

                            df.at[
                                df.index[i],
                                "fvg_active",
                            ] = 0

                            df.at[
                                df.index[i],
                                "fvg_mitigation_index",
                            ] = i

                            df.at[
                                df.index[i],
                                "fvg_mitigation_price",
                            ] = (
                                candle_low
                            )

                            df.at[
                                df.index[i],
                                "fvg_mitigation_id",
                            ] = int(
                                current_id
                            )

                            df.at[
                                df.index[i],
                                "fvg_mitigation_direction",
                            ] = (
                                "BULLISH"
                            )

                            del active_fvgs[
                                current_id
                            ]

                            continue

                        df.at[
                            df.index[i],
                            "fvg_active",
                        ] = 1

                    # =============================================================
                    # BEARISH FVG
                    # =============================================================

                    elif (
                        direction
                        == "BEARISH"
                    ):

                        if (
                            candle_high
                            < zone_low
                        ):
                            continue

                        penetration = (
                            candle_high
                            - zone_low
                        )

                        fill_ratio = (
                            penetration
                            / zone_size
                        )

                        fill_ratio = max(
                            0.0,
                            min(
                                1.0,
                                fill_ratio,
                            ),
                        )

                        fill_percent = (
                            fill_ratio
                            * 100.0
                        )

                        rejection = (
                            candle_close
                            < zone_low
                            and
                            fill_ratio
                            >= self.rejection_threshold
                        )

                        fully_mitigated = (
                            fill_ratio
                            >= self.full_mitigation
                            or
                            candle_high
                            >= zone_high
                        )

                        current_row_fill = (
                            self._to_float(
                                df.at[
                                    df.index[i],
                                    "fvg_fill_percent",
                                ]
                            )
                        )

                        if (
                            fill_percent
                            > current_row_fill
                        ):

                            df.at[
                                df.index[i],
                                "fvg_fill_percent",
                            ] = round(
                                fill_percent,
                                2,
                            )

                        # ---------------------------------------------------------
                        # Rejection
                        # ---------------------------------------------------------

                        if rejection:

                            rejection_event = {
                                "fvg_id": (
                                    int(
                                        current_id
                                    )
                                ),
                                "direction": (
                                    "BEARISH"
                                ),
                                "event_type": (
                                    "REJECTION"
                                ),
                                "fill_percent": (
                                    round(
                                        fill_percent,
                                        2,
                                    )
                                ),
                                "index": (
                                    i
                                ),
                            }

                            row_events.append(
                                rejection_event
                            )

                            df.at[
                                df.index[i],
                                "fvg_rejection",
                            ] = 1

                            existing_strength = (
                                self._to_float(
                                    df.at[
                                        df.index[i],
                                        "fvg_rejection_strength",
                                    ]
                                )
                            )

                            if (
                                fill_percent
                                >= existing_strength
                            ):

                                df.at[
                                    df.index[i],
                                    "fvg_rejection_strength",
                                ] = round(
                                    fill_percent,
                                    2,
                                )

                                df.at[
                                    df.index[i],
                                    "fvg_rejection_id",
                                ] = int(
                                    current_id
                                )

                                df.at[
                                    df.index[i],
                                    "fvg_rejection_direction",
                                ] = (
                                    "BEARISH"
                                )

                        # ---------------------------------------------------------
                        # Full mitigation
                        # ---------------------------------------------------------

                        if fully_mitigated:

                            mitigation_event = {
                                "fvg_id": (
                                    int(
                                        current_id
                                    )
                                ),
                                "direction": (
                                    "BEARISH"
                                ),
                                "event_type": (
                                    "MITIGATION"
                                ),
                                "fill_percent": (
                                    round(
                                        fill_percent,
                                        2,
                                    )
                                ),
                                "index": (
                                    i
                                ),
                            }

                            row_events.append(
                                mitigation_event
                            )

                            df.at[
                                df.index[i],
                                "fvg_mitigated",
                            ] = 1

                            df.at[
                                df.index[i],
                                "fvg_active",
                            ] = 0

                            df.at[
                                df.index[i],
                                "fvg_mitigation_index",
                            ] = i

                            df.at[
                                df.index[i],
                                "fvg_mitigation_price",
                            ] = (
                                candle_high
                            )

                            df.at[
                                df.index[i],
                                "fvg_mitigation_id",
                            ] = int(
                                current_id
                            )

                            df.at[
                                df.index[i],
                                "fvg_mitigation_direction",
                            ] = (
                                "BEARISH"
                            )

                            del active_fvgs[
                                current_id
                            ]

                            continue

                        df.at[
                            df.index[i],
                            "fvg_active",
                        ] = 1

            # =====================================================================
            # STEP 3
            # Store complete interaction contract in Python buffer.
            # =====================================================================

            interaction_events_buffer[
                i
            ] = row_events

            df.at[
                df.index[i],
                "fvg_interaction_count",
            ] = len(
                row_events
            )

            primary_event = (
                self._select_primary_event(
                    row_events
                )
            )

            if (
                primary_event
                is not None
            ):

                df.at[
                    df.index[i],
                    "fvg_interaction",
                ] = 1

                df.at[
                    df.index[i],
                    "fvg_interaction_id",
                ] = int(
                    primary_event[
                        "fvg_id"
                    ]
                )

                df.at[
                    df.index[i],
                    "fvg_interaction_direction",
                ] = str(
                    primary_event[
                        "direction"
                    ]
                )

                df.at[
                    df.index[i],
                    "fvg_interaction_type",
                ] = str(
                    primary_event[
                        "event_type"
                    ]
                )

                df.at[
                    df.index[i],
                    "fvg_interaction_fill_percent",
                ] = float(
                    primary_event[
                        "fill_percent"
                    ]
                )

        # =========================================================================
        # Object Event Column
        #
        # Assign complete object Series at once.
        # This avoids Pylance/Pandas scalar assignment errors.
        # =========================================================================

        df[
            "fvg_interaction_events"
        ] = pd.Series(
            interaction_events_buffer,
            index=df.index,
            dtype="object",
        )

        return df


fvg_mitigation_engine = (
    FVGMitigationEngine()
)