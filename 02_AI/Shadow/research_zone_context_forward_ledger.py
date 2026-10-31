"""
===============================================================================
Module      : research_zone_context_forward_ledger.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Forward-Only Validation Ledger for Institutional Zone Hypotheses
===============================================================================

Forward boundary
----------------
FIRST RUN
    latest closed candle
        ↓
    establish anchor
        ↓
    capture ZERO historical opportunities

LATER RUNS
    causal research frame including anchor history
        ↓
    form candidate episodes causally
        ↓
    only episode STARTS with signal_time > previous anchor
        ↓
    freeze zone context + Z1-Z6 hypotheses at signal time
        ↓
    evaluate future 5 / 10 / 20 bars

Episode identity
----------------
A candidate continues the previous episode when:

- direction unchanged
- LEI entry family unchanged
- liquidity interpretation unchanged
- reference source unchanged
- confirmation type unchanged
- candidate-to-candidate gap <= max_gap_minutes

This mirrors the existing research candidate episode definition without using
future outcome information.

Pre-registered hypotheses
-------------------------
Z1  aligned zone ACCEPTED                  expected positive evidence
Z2  aligned zone FRESH                     expected negative evidence
Z3  price INSIDE aligned zone              expected negative evidence
Z4  SHORT + aligned zone OVERLAP           expected positive evidence
Z5  SHORT + INSIDE aligned zone            expected strong negative evidence
Z6  BOTH aligned/opposing context close    tentative positive evidence

These are observations only.

They are NOT:
- hard blockers
- trade authorization
- RWEI changes
- LEI changes
- trade_ready changes
- order logic

Safety
------
- research only
- no orders
- no position modification
- no risk sizing
- no hindsight cslabel_* / izlabel_*
- causal signal-time zone metadata only
- paper entry = signal candle close
- outcomes start from NEXT candle
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(
    __file__
).resolve().parents[
    2
]


DEFAULT_FORWARD_ZONE_CONTEXT_LEDGER_PATH = (
    PROJECT_ROOT
    /
    "01_Data"
    /
    "Processed"
    /
    "pulseviper_forward_zone_context_ledger.csv"
)


class ResearchZoneContextForwardLedger:
    VERSION = "1.0"

    MODE = "FORWARD_ONLY_ZONE_CONTEXT_VALIDATION"

    POLICY = "PRE_REGISTERED_ZONE_HYPOTHESES_V1"

    DEFAULT_EPISODE_GAP_MINUTES = 3

    HORIZONS = (
        5,
        10,
        20,
    )

    HYPOTHESES = (
        (
            "Z1",
            "ALIGNED_ACCEPTED",
        ),
        (
            "Z2",
            "ALIGNED_FRESH",
        ),
        (
            "Z3",
            "ALIGNED_INSIDE",
        ),
        (
            "Z4",
            "SHORT_ALIGNED_OVERLAP",
        ),
        (
            "Z5",
            "SHORT_ALIGNED_INSIDE",
        ),
        (
            "Z6",
            "BOTH_CLOSE",
        ),
    )

    REQUIRED_CAPTURE_COLUMNS = {
        "time",
        "close",

        "lei_candidate_flag",
        "lei_direction",
        "lei_entry_family",
        "lei_reference_source",
        "lei_confirmation_type",

        "liqintel_event_interpretation",

        "izctx_active_bullish_count",
        "izctx_active_bearish_count",

        "izctx_bullish_event_id",
        "izctx_bullish_state",
        "izctx_bullish_distance_atr",
        "izctx_bullish_inside_flag",
        "izctx_bullish_overlap_flag",

        "izctx_bearish_event_id",
        "izctx_bearish_state",
        "izctx_bearish_distance_atr",
        "izctx_bearish_inside_flag",
        "izctx_bearish_overlap_flag",

        "izctx_live_safe",
        "izctx_version",
        "izctx_mode",

        "research_live_safe",
        "research_trade_ready_unchanged",
    }

    LEDGER_COLUMNS = (
        "event_id",

        "signal_time",

        "requested_symbol",
        "resolved_symbol",
        "timeframe",

        "direction",
        "paper_direction",

        "entry_close",

        "lei_entry_family",
        "liqintel_event_interpretation",
        "lei_reference_source",
        "lei_confirmation_type",

        "confidence_score",
        "regime_state",

        "aligned_zone_event_id",
        "aligned_zone_state",
        "aligned_distance_atr",
        "aligned_location",
        "aligned_active_count",

        "opposing_zone_event_id",
        "opposing_zone_state",
        "opposing_distance_atr",
        "opposing_location",
        "opposing_active_count",

        "zone_relation",

        "z1_aligned_accepted",
        "z2_aligned_fresh",
        "z3_aligned_inside",
        "z4_short_aligned_overlap",
        "z5_short_aligned_inside",
        "z6_both_close",

        "hypothesis_tags",

        "zone_context_version",
        "zone_context_mode",

        "zone_forward_policy",
        "zone_forward_version",
        "zone_forward_mode",

        "episode_gap_minutes",

        "bars_available",
        "status",
        "last_evaluated_time",

        "close_5",
        "net_5",

        "close_10",
        "net_10",

        "close_20",
        "net_20",

        "mfe_20",
        "mae_20",

        "positive_20",
    )

    # =========================================================================
    # Init
    # =========================================================================

    def __init__(
        self,
        path: str | Path | None = None,
    ) -> None:

        self.path = Path(
            path
            if path is not None
            else DEFAULT_FORWARD_ZONE_CONTEXT_LEDGER_PATH
        )

        self.anchor_path = self.path.with_suffix(
            self.path.suffix
            +
            ".anchor.json"
        )

    # =========================================================================
    # Helpers
    # =========================================================================

    @staticmethod
    def _number(
        value: Any,
    ) -> float:

        try:
            number = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            return np.nan

        if not np.isfinite(
            number
        ):
            return np.nan

        return number

    @staticmethod
    def _text(
        value: Any,
        default: str = "UNKNOWN",
    ) -> str:

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
            pass

        text = str(
            value
        ).strip()

        return (
            text
            if text
            else default
        )

    @staticmethod
    def _timestamp(
        value: Any,
    ) -> pd.Timestamp | None:

        timestamp = pd.to_datetime(
            value,
            errors="coerce",
            utc=True,
        )

        if pd.isna(
            timestamp
        ):
            return None

        return (
            pd.Timestamp(
                timestamp
            )
            .tz_convert(
                None
            )
        )

    @classmethod
    def _empty_frame(
        cls,
    ) -> pd.DataFrame:

        return pd.DataFrame(
            columns=list(
                cls.LEDGER_COLUMNS
            )
        )

    @classmethod
    def _normalize(
        cls,
        frame: pd.DataFrame,
    ) -> pd.DataFrame:

        result = frame.copy().reindex(
            columns=list(
                cls.LEDGER_COLUMNS
            )
        )

        for column in (
            "signal_time",
            "last_evaluated_time",
        ):

            result[
                column
            ] = pd.to_datetime(
                result[
                    column
                ],
                errors="coerce",
            )

        return result.reset_index(
            drop=True
        )

    @staticmethod
    def _distance_band_location(
        event_id: Any,
        inside_flag: Any,
        overlap_flag: Any,
        distance_atr: Any,
    ) -> str:

        event = (
            ResearchZoneContextForwardLedger
            ._text(
                event_id,
                "NONE",
            )
            .upper()
        )

        if event == "NONE":
            return "NO_ZONE"

        inside = (
            ResearchZoneContextForwardLedger
            ._number(
                inside_flag
            )
        )

        overlap = (
            ResearchZoneContextForwardLedger
            ._number(
                overlap_flag
            )
        )

        distance = (
            ResearchZoneContextForwardLedger
            ._number(
                distance_atr
            )
        )

        if (
            np.isfinite(
                inside
            )
            and
            inside >= 1.0
        ):
            return "INSIDE"

        if (
            np.isfinite(
                overlap
            )
            and
            overlap >= 1.0
        ):
            return "OVERLAP"

        if not np.isfinite(
            distance
        ):
            return "UNKNOWN"

        if distance <= 0.10:
            return "VERY_NEAR"

        if distance <= 0.25:
            return "NEAR"

        if distance <= 0.50:
            return "MODERATE"

        return "FAR"

    @staticmethod
    def _zone_relation(
        aligned_location: str,
        opposing_location: str,
    ) -> str:

        close_locations = {
            "INSIDE",
            "OVERLAP",
            "VERY_NEAR",
            "NEAR",
        }

        aligned_close = (
            aligned_location
            in close_locations
        )

        opposing_close = (
            opposing_location
            in close_locations
        )

        if (
            aligned_close
            and
            opposing_close
        ):
            return "BOTH_CLOSE"

        if aligned_close:
            return "ALIGNED_CLOSE"

        if opposing_close:
            return "OPPOSING_CLOSE"

        if (
            aligned_location == "NO_ZONE"
            and
            opposing_location == "NO_ZONE"
        ):
            return "NO_ZONE_CONTEXT"

        return "DISTANT_OR_MIXED"

    # =========================================================================
    # Event / episode identity
    # =========================================================================

    @classmethod
    def _episode_key(
        cls,
        row: pd.Series,
    ) -> tuple[
        str,
        str,
        str,
        str,
        str,
    ]:

        return (
            cls._text(
                row.get(
                    "lei_direction"
                ),
                "NONE",
            ).upper(),

            cls._text(
                row.get(
                    "lei_entry_family"
                ),
                "NONE",
            ).upper(),

            cls._text(
                row.get(
                    "liqintel_event_interpretation"
                ),
                "NONE",
            ).upper(),

            cls._text(
                row.get(
                    "lei_reference_source"
                ),
                "NONE",
            ).upper(),

            cls._text(
                row.get(
                    "lei_confirmation_type"
                ),
                "NONE",
            ).upper(),
        )

    @staticmethod
    def _event_id(
        symbol: str,
        timeframe: str,
        signal_time: pd.Timestamp,
        episode_key: tuple[
            str,
            str,
            str,
            str,
            str,
        ],
        policy: str,
    ) -> str:

        identity = "|".join(
            (
                symbol.upper(),
                timeframe.upper(),

                signal_time.strftime(
                    "%Y-%m-%dT%H:%M:%S"
                ),

                *episode_key,

                policy,
            )
        )

        return hashlib.sha1(
            identity.encode(
                "utf-8"
            )
        ).hexdigest()[
            :20
        ]

    # =========================================================================
    # Safety
    # =========================================================================

    @classmethod
    def _validate_capture_input(
        cls,
        frame: pd.DataFrame,
    ) -> None:

        if not isinstance(
            frame,
            pd.DataFrame,
        ):
            raise TypeError(
                "Forward zone input must be a pandas DataFrame"
            )

        if not frame.columns.is_unique:
            raise ValueError(
                "Forward zone input contains duplicate columns"
            )

        missing = (
            cls.REQUIRED_CAPTURE_COLUMNS
            -
            set(
                frame.columns
            )
        )

        if missing:
            raise ValueError(
                "Missing forward zone columns: "
                +
                ", ".join(
                    sorted(
                        missing
                    )
                )
            )

        hindsight = [
            column
            for column in frame.columns
            if (
                isinstance(
                    column,
                    str,
                )
                and
                column.startswith(
                    (
                        "cslabel_",
                        "izlabel_",
                    )
                )
            )
        ]

        if hindsight:
            raise ValueError(
                "Hindsight cslabel_* / izlabel_* columns "
                "are forbidden"
            )

        research_safe = (
            pd.to_numeric(
                frame[
                    "research_live_safe"
                ],
                errors="coerce",
            )
            .fillna(
                0
            )
            .eq(
                1
            )
        )

        zone_safe = (
            pd.to_numeric(
                frame[
                    "izctx_live_safe"
                ],
                errors="coerce",
            )
            .fillna(
                0
            )
            .eq(
                1
            )
        )

        unchanged = (
            pd.to_numeric(
                frame[
                    "research_trade_ready_unchanged"
                ],
                errors="coerce",
            )
            .fillna(
                0
            )
            .eq(
                1
            )
        )

        if not bool(
            research_safe.all()
        ):
            raise ValueError(
                "Forward zone ledger requires "
                "research_live_safe == 1"
            )

        if not bool(
            zone_safe.all()
        ):
            raise ValueError(
                "Forward zone ledger requires "
                "izctx_live_safe == 1"
            )

        if not bool(
            unchanged.all()
        ):
            raise ValueError(
                "Forward zone ledger requires "
                "research_trade_ready_unchanged == 1"
            )

    # =========================================================================
    # Anchor
    # =========================================================================

    def load_anchor(
        self,
    ) -> pd.Timestamp | None:

        if not self.anchor_path.exists():
            return None

        payload = json.loads(
            self.anchor_path.read_text(
                encoding="utf-8"
            )
        )

        return self._timestamp(
            payload.get(
                "anchor_time"
            )
        )

    def save_anchor(
        self,
        anchor_time: Any,
    ) -> pd.Timestamp:

        timestamp = self._timestamp(
            anchor_time
        )

        if timestamp is None:
            raise ValueError(
                "Invalid forward zone anchor time"
            )

        self.anchor_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = {
            "anchor_time": (
                timestamp.isoformat()
            ),

            "zone_forward_policy": (
                self.POLICY
            ),

            "zone_forward_version": (
                self.VERSION
            ),

            "zone_forward_mode": (
                self.MODE
            ),
        }

        temporary = self.anchor_path.with_suffix(
            self.anchor_path.suffix
            +
            ".tmp"
        )

        temporary.write_text(
            json.dumps(
                payload,
                indent=2,
            ),
            encoding="utf-8",
        )

        temporary.replace(
            self.anchor_path
        )

        return timestamp

    @classmethod
    def latest_market_time(
        cls,
        frame: pd.DataFrame,
    ) -> pd.Timestamp:

        if (
            not isinstance(
                frame,
                pd.DataFrame,
            )
            or
            "time" not in frame.columns
            or
            frame.empty
        ):
            raise ValueError(
                "Cannot determine latest market time"
            )

        times = pd.to_datetime(
            frame[
                "time"
            ],
            errors="coerce",
            utc=True,
        )

        latest = times.max()

        if pd.isna(
            latest
        ):
            raise ValueError(
                "No valid market timestamp"
            )

        return (
            pd.Timestamp(
                latest
            )
            .tz_convert(
                None
            )
        )

    # =========================================================================
    # Persistence
    # =========================================================================

    def load(
        self,
    ) -> pd.DataFrame:

        if not self.path.exists():
            return self._empty_frame()

        frame = pd.read_csv(
            self.path
        )

        return (
            self._normalize(
                frame
            )
            .drop_duplicates(
                "event_id",
                keep="last",
            )
            .sort_values(
                "signal_time"
            )
            .reset_index(
                drop=True
            )
        )

    def save(
        self,
        frame: pd.DataFrame,
    ) -> None:

        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        result = (
            self._normalize(
                frame
            )
            .drop_duplicates(
                "event_id",
                keep="last",
            )
            .sort_values(
                "signal_time"
            )
            .reset_index(
                drop=True
            )
        )

        temporary = self.path.with_suffix(
            self.path.suffix
            +
            ".tmp"
        )

        result.to_csv(
            temporary,
            index=False,
        )

        temporary.replace(
            self.path
        )

    # =========================================================================
    # Direction-relative zone snapshot
    # =========================================================================

    @classmethod
    def _zone_snapshot(
        cls,
        row: pd.Series,
        direction: str,
    ) -> dict[
        str,
        Any,
    ]:

        if direction == "LONG":
            aligned = "bullish"
            opposing = "bearish"

        elif direction == "SHORT":
            aligned = "bearish"
            opposing = "bullish"

        else:
            raise ValueError(
                f"Unsupported direction: {direction}"
            )

        aligned_event = cls._text(
            row.get(
                f"izctx_{aligned}_event_id"
            ),
            "NONE",
        ).upper()

        aligned_state = cls._text(
            row.get(
                f"izctx_{aligned}_state"
            ),
            "NONE",
        ).upper()

        aligned_distance = cls._number(
            row.get(
                f"izctx_{aligned}_distance_atr"
            )
        )

        aligned_inside = cls._number(
            row.get(
                f"izctx_{aligned}_inside_flag"
            )
        )

        aligned_overlap = cls._number(
            row.get(
                f"izctx_{aligned}_overlap_flag"
            )
        )

        aligned_location = (
            cls._distance_band_location(
                event_id=aligned_event,
                inside_flag=aligned_inside,
                overlap_flag=aligned_overlap,
                distance_atr=aligned_distance,
            )
        )

        opposing_event = cls._text(
            row.get(
                f"izctx_{opposing}_event_id"
            ),
            "NONE",
        ).upper()

        opposing_state = cls._text(
            row.get(
                f"izctx_{opposing}_state"
            ),
            "NONE",
        ).upper()

        opposing_distance = cls._number(
            row.get(
                f"izctx_{opposing}_distance_atr"
            )
        )

        opposing_inside = cls._number(
            row.get(
                f"izctx_{opposing}_inside_flag"
            )
        )

        opposing_overlap = cls._number(
            row.get(
                f"izctx_{opposing}_overlap_flag"
            )
        )

        opposing_location = (
            cls._distance_band_location(
                event_id=opposing_event,
                inside_flag=opposing_inside,
                overlap_flag=opposing_overlap,
                distance_atr=opposing_distance,
            )
        )

        aligned_count = cls._number(
            row.get(
                f"izctx_active_{aligned}_count"
            )
        )

        opposing_count = cls._number(
            row.get(
                f"izctx_active_{opposing}_count"
            )
        )

        relation = cls._zone_relation(
            aligned_location,
            opposing_location,
        )

        return {
            "aligned_zone_event_id": (
                aligned_event
            ),

            "aligned_zone_state": (
                aligned_state
            ),

            "aligned_distance_atr": (
                aligned_distance
            ),

            "aligned_location": (
                aligned_location
            ),

            "aligned_active_count": (
                aligned_count
            ),

            "opposing_zone_event_id": (
                opposing_event
            ),

            "opposing_zone_state": (
                opposing_state
            ),

            "opposing_distance_atr": (
                opposing_distance
            ),

            "opposing_location": (
                opposing_location
            ),

            "opposing_active_count": (
                opposing_count
            ),

            "zone_relation": (
                relation
            ),
        }

    # =========================================================================
    # Frozen hypothesis snapshot
    # =========================================================================

    @classmethod
    def _hypothesis_snapshot(
        cls,
        direction: str,
        zone: dict[
            str,
            Any,
        ],
    ) -> dict[
        str,
        Any,
    ]:

        aligned_state = cls._text(
            zone.get(
                "aligned_zone_state"
            ),
            "NONE",
        ).upper()

        aligned_location = cls._text(
            zone.get(
                "aligned_location"
            ),
            "NO_ZONE",
        ).upper()

        relation = cls._text(
            zone.get(
                "zone_relation"
            ),
            "NO_ZONE_CONTEXT",
        ).upper()

        z1 = int(
            aligned_state
            ==
            "ACCEPTED"
        )

        z2 = int(
            aligned_state
            ==
            "FRESH"
        )

        z3 = int(
            aligned_location
            ==
            "INSIDE"
        )

        z4 = int(
            direction
            ==
            "SHORT"
            and
            aligned_location
            ==
            "OVERLAP"
        )

        z5 = int(
            direction
            ==
            "SHORT"
            and
            aligned_location
            ==
            "INSIDE"
        )

        z6 = int(
            relation
            ==
            "BOTH_CLOSE"
        )

        flags = {
            "Z1": z1,
            "Z2": z2,
            "Z3": z3,
            "Z4": z4,
            "Z5": z5,
            "Z6": z6,
        }

        tags = [
            code
            for code, active
            in flags.items()
            if active == 1
        ]

        return {
            "z1_aligned_accepted": z1,

            "z2_aligned_fresh": z2,

            "z3_aligned_inside": z3,

            "z4_short_aligned_overlap": z4,

            "z5_short_aligned_inside": z5,

            "z6_both_close": z6,

            "hypothesis_tags": (
                "|".join(
                    tags
                )
                if tags
                else
                "NONE"
            ),
        }

    # =========================================================================
    # Forward-only causal episode capture
    # =========================================================================

    def capture_after_anchor(
        self,
        frame: pd.DataFrame,
        anchor_time: Any,
        requested_symbol: str,
        resolved_symbol: str,
        timeframe: str = "M1",
        max_gap_minutes: int = DEFAULT_EPISODE_GAP_MINUTES,
    ) -> pd.DataFrame:

        self._validate_capture_input(
            frame
        )

        if max_gap_minutes < 1:
            raise ValueError(
                "max_gap_minutes must be >= 1"
            )

        anchor = self._timestamp(
            anchor_time
        )

        if anchor is None:
            raise ValueError(
                "Forward zone capture requires a valid anchor"
            )

        working = frame.copy(
            deep=True
        )

        working[
            "_zf_time"
        ] = (
            pd.to_datetime(
                working[
                    "time"
                ],
                errors="coerce",
                utc=True,
            )
            .dt
            .tz_convert(
                None
            )
        )

        valid_times = working[
            "_zf_time"
        ].dropna()

        if valid_times.empty:
            return self._empty_frame()

        # We need some market/candidate history at or before the anchor so the
        # first post-anchor candidate cannot silently be misclassified as a new
        # episode when it is actually a continuation.
        if valid_times.min() > anchor:
            raise ValueError(
                "Forward zone capture frame must include "
                "history at or before the anchor"
            )

        candidate_mask = (
            pd.to_numeric(
                working[
                    "lei_candidate_flag"
                ],
                errors="coerce",
            )
            .fillna(
                0
            )
            .eq(
                1
            )
        )

        candidates = (
            working.loc[
                candidate_mask
                &
                working[
                    "_zf_time"
                ].notna()
            ]
            .copy()
            .sort_values(
                "_zf_time"
            )
            .reset_index(
                drop=True
            )
        )

        if candidates.empty:
            return self._empty_frame()

        rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        previous_key: tuple[
            str,
            str,
            str,
            str,
            str,
        ] | None = None

        previous_time: pd.Timestamp | None = None

        for _, row in candidates.iterrows():

            signal_time = self._timestamp(
                row.get(
                    "_zf_time"
                )
            )

            if signal_time is None:
                continue

            key = self._episode_key(
                row
            )

            direction = key[
                0
            ]

            if direction not in {
                "LONG",
                "SHORT",
            }:
                previous_key = key
                previous_time = signal_time
                continue

            if previous_time is None:

                new_episode = True

            else:

                gap_minutes = (
                    (
                        signal_time
                        -
                        previous_time
                    )
                    .total_seconds()
                    /
                    60.0
                )

                new_episode = (
                    key
                    !=
                    previous_key
                    or
                    gap_minutes
                    >
                    float(
                        max_gap_minutes
                    )
                )

            # Episode construction itself uses all causal candidate history.
            # Forward boundary is applied only AFTER episode-start detection.
            capture_this_episode = (
                new_episode
                and
                signal_time
                >
                anchor
            )

            if capture_this_episode:

                zone = self._zone_snapshot(
                    row,
                    direction,
                )

                hypotheses = (
                    self._hypothesis_snapshot(
                        direction,
                        zone,
                    )
                )

                record: dict[
                    str,
                    Any,
                ] = {
                    column: np.nan
                    for column
                    in self.LEDGER_COLUMNS
                }

                record.update(
                    {
                        "event_id": self._event_id(
                            symbol=resolved_symbol,
                            timeframe=timeframe,
                            signal_time=signal_time,
                            episode_key=key,
                            policy=self.POLICY,
                        ),

                        "signal_time": (
                            signal_time
                        ),

                        "requested_symbol": (
                            requested_symbol
                        ),

                        "resolved_symbol": (
                            resolved_symbol
                        ),

                        "timeframe": (
                            timeframe
                        ),

                        "direction": (
                            direction
                        ),

                        "paper_direction": (
                            "BULLISH"
                            if direction == "LONG"
                            else
                            "BEARISH"
                        ),

                        "entry_close": self._number(
                            row.get(
                                "close"
                            )
                        ),

                        "lei_entry_family": (
                            key[
                                1
                            ]
                        ),

                        "liqintel_event_interpretation": (
                            key[
                                2
                            ]
                        ),

                        "lei_reference_source": (
                            key[
                                3
                            ]
                        ),

                        "lei_confirmation_type": (
                            key[
                                4
                            ]
                        ),

                        "confidence_score": self._number(
                            row.get(
                                "confidence_score"
                            )
                        ),

                        "regime_state": self._text(
                            row.get(
                                "regime_state"
                            ),
                            "UNKNOWN",
                        ),

                        **zone,

                        **hypotheses,

                        "zone_context_version": self._text(
                            row.get(
                                "izctx_version"
                            ),
                            "UNKNOWN",
                        ),

                        "zone_context_mode": self._text(
                            row.get(
                                "izctx_mode"
                            ),
                            "UNKNOWN",
                        ),

                        "zone_forward_policy": (
                            self.POLICY
                        ),

                        "zone_forward_version": (
                            self.VERSION
                        ),

                        "zone_forward_mode": (
                            self.MODE
                        ),

                        "episode_gap_minutes": int(
                            max_gap_minutes
                        ),

                        "bars_available": 0,

                        "status": "OPEN",
                    }
                )

                rows.append(
                    record
                )

            previous_key = key
            previous_time = signal_time

        if not rows:
            return self._empty_frame()

        return self._normalize(
            pd.DataFrame(
                rows
            )
        )

    # =========================================================================
    # Merge
    # =========================================================================

    def merge(
        self,
        existing: pd.DataFrame,
        incoming: pd.DataFrame,
    ) -> tuple[
        pd.DataFrame,
        int,
    ]:

        current = self._normalize(
            existing
        )

        new = self._normalize(
            incoming
        )

        if new.empty:
            return (
                current,
                0,
            )

        known = set(
            current[
                "event_id"
            ]
            .dropna()
            .astype(
                str
            )
        )

        new = new.loc[
            ~new[
                "event_id"
            ]
            .astype(
                str
            )
            .isin(
                known
            )
        ].copy()

        if new.empty:
            return (
                current,
                0,
            )

        combined = (
            new
            if current.empty
            else
            pd.concat(
                [
                    current,
                    new,
                ],
                ignore_index=True,
            )
        )

        combined = (
            combined
            .drop_duplicates(
                "event_id",
                keep="last",
            )
            .sort_values(
                "signal_time"
            )
            .reset_index(
                drop=True
            )
        )

        return (
            self._normalize(
                combined
            ),
            len(
                new
            ),
        )

    # =========================================================================
    # Outcome helpers
    # =========================================================================

    @staticmethod
    def _favorable(
        direction: str,
        entry: float,
        future: pd.DataFrame,
    ) -> np.ndarray:

        if direction == "BULLISH":

            return (
                pd.to_numeric(
                    future[
                        "high"
                    ],
                    errors="coerce",
                )
                .to_numpy(
                    dtype=float
                )
                -
                entry
            )

        return (
            entry
            -
            pd.to_numeric(
                future[
                    "low"
                ],
                errors="coerce",
            )
            .to_numpy(
                dtype=float
            )
        )

    @staticmethod
    def _adverse(
        direction: str,
        entry: float,
        future: pd.DataFrame,
    ) -> np.ndarray:

        if direction == "BULLISH":

            return (
                entry
                -
                pd.to_numeric(
                    future[
                        "low"
                    ],
                    errors="coerce",
                )
                .to_numpy(
                    dtype=float
                )
            )

        return (
            pd.to_numeric(
                future[
                    "high"
                ],
                errors="coerce",
            )
            .to_numpy(
                dtype=float
            )
            -
            entry
        )

    # =========================================================================
    # Future-only evaluation
    # =========================================================================

    def evaluate(
        self,
        ledger: pd.DataFrame,
        market: pd.DataFrame,
    ) -> pd.DataFrame:

        required = {
            "time",
            "high",
            "low",
            "close",
        }

        missing = (
            required
            -
            set(
                market.columns
            )
        )

        if missing:
            raise ValueError(
                "Missing forward outcome columns: "
                +
                ", ".join(
                    sorted(
                        missing
                    )
                )
            )

        result = self._normalize(
            ledger
        )

        if result.empty:
            return result

        data = market.copy(
            deep=True
        )

        data[
            "time"
        ] = (
            pd.to_datetime(
                data[
                    "time"
                ],
                errors="coerce",
                utc=True,
            )
            .dt
            .tz_convert(
                None
            )
        )

        data = (
            data
            .dropna(
                subset=[
                    "time",
                    "high",
                    "low",
                    "close",
                ]
            )
            .drop_duplicates(
                "time",
                keep="last",
            )
            .sort_values(
                "time"
            )
            .reset_index(
                drop=True
            )
        )

        if data.empty:
            return result

        positions = {
            pd.Timestamp(
                timestamp
            ): position
            for position, timestamp
            in enumerate(
                data[
                    "time"
                ].tolist()
            )
        }

        latest_time = data[
            "time"
        ].iloc[
            -1
        ]

        for ledger_index in range(
            len(
                result
            )
        ):

            signal_time = self._timestamp(
                result.at[
                    ledger_index,
                    "signal_time",
                ]
            )

            if (
                signal_time is None
                or
                signal_time not in positions
            ):
                continue

            position = positions[
                signal_time
            ]

            entry = self._number(
                result.at[
                    ledger_index,
                    "entry_close",
                ]
            )

            if not np.isfinite(
                entry
            ):
                continue

            direction = self._text(
                result.at[
                    ledger_index,
                    "paper_direction",
                ]
            ).upper()

            if direction not in {
                "BULLISH",
                "BEARISH",
            }:
                continue

            available = max(
                0,
                len(
                    data
                )
                -
                position
                -
                1,
            )

            result.at[
                ledger_index,
                "bars_available",
            ] = min(
                available,
                20,
            )

            result.at[
                ledger_index,
                "last_evaluated_time",
            ] = latest_time

            result.at[
                ledger_index,
                "status",
            ] = (
                "MATURED_20"
                if available >= 20
                else
                "PARTIAL_10"
                if available >= 10
                else
                "PARTIAL_5"
                if available >= 5
                else
                "OPEN"
            )

            sign = (
                1.0
                if direction == "BULLISH"
                else
                -1.0
            )

            for horizon in self.HORIZONS:

                if available < horizon:
                    continue

                future_close = self._number(
                    data.iloc[
                        position
                        +
                        horizon
                    ][
                        "close"
                    ]
                )

                result.at[
                    ledger_index,
                    f"close_{horizon}",
                ] = future_close

                result.at[
                    ledger_index,
                    f"net_{horizon}",
                ] = (
                    sign
                    *
                    (
                        future_close
                        -
                        entry
                    )
                )

            if available >= 20:

                future20 = data.iloc[
                    position + 1
                    :
                    position + 21
                ]

                favorable = self._favorable(
                    direction,
                    entry,
                    future20,
                )

                adverse = self._adverse(
                    direction,
                    entry,
                    future20,
                )

                finite_favorable = favorable[
                    np.isfinite(
                        favorable
                    )
                ]

                finite_adverse = adverse[
                    np.isfinite(
                        adverse
                    )
                ]

                if finite_favorable.size:

                    result.at[
                        ledger_index,
                        "mfe_20",
                    ] = max(
                        0.0,
                        float(
                            np.max(
                                finite_favorable
                            )
                        ),
                    )

                if finite_adverse.size:

                    result.at[
                        ledger_index,
                        "mae_20",
                    ] = max(
                        0.0,
                        float(
                            np.max(
                                finite_adverse
                            )
                        ),
                    )

                net20 = self._number(
                    result.at[
                        ledger_index,
                        "net_20",
                    ]
                )

                if np.isfinite(
                    net20
                ):

                    result.at[
                        ledger_index,
                        "positive_20",
                    ] = int(
                        net20 > 0.0
                    )

        return self._normalize(
            result
        )

    # =========================================================================
    # Dashboards
    # =========================================================================

    @staticmethod
    def _median(
        frame: pd.DataFrame,
        column: str,
    ) -> float:

        values = pd.to_numeric(
            frame[
                column
            ],
            errors="coerce",
        ).dropna()

        if values.empty:
            return np.nan

        return round(
            float(
                values.median()
            ),
            3,
        )

    @staticmethod
    def _positive_pct(
        frame: pd.DataFrame,
    ) -> float:

        values = pd.to_numeric(
            frame[
                "positive_20"
            ],
            errors="coerce",
        ).dropna()

        if values.empty:
            return np.nan

        return round(
            float(
                values.mean()
                *
                100.0
            ),
            3,
        )

    @classmethod
    def hypothesis_dashboard(
        cls,
        ledger: pd.DataFrame,
    ) -> pd.DataFrame:

        matured = ledger.loc[
            ledger[
                "status"
            ]
            .astype(
                str
            )
            .eq(
                "MATURED_20"
            )
        ].copy()

        mapping = (
            (
                "Z1",
                "ALIGNED_ACCEPTED",
                "z1_aligned_accepted",
            ),
            (
                "Z2",
                "ALIGNED_FRESH",
                "z2_aligned_fresh",
            ),
            (
                "Z3",
                "ALIGNED_INSIDE",
                "z3_aligned_inside",
            ),
            (
                "Z4",
                "SHORT_ALIGNED_OVERLAP",
                "z4_short_aligned_overlap",
            ),
            (
                "Z5",
                "SHORT_ALIGNED_INSIDE",
                "z5_short_aligned_inside",
            ),
            (
                "Z6",
                "BOTH_CLOSE",
                "z6_both_close",
            ),
        )

        rows: list[
            dict[
                str,
                Any,
            ]
        ] = []

        for (
            code,
            name,
            column,
        ) in mapping:

            active = (
                pd.to_numeric(
                    matured[
                        column
                    ],
                    errors="coerce",
                )
                .fillna(
                    0
                )
                .eq(
                    1
                )
            )

            frame = matured.loc[
                active
            ]

            rows.append(
                {
                    "hypothesis": (
                        code
                    ),

                    "name": (
                        name
                    ),

                    "n": len(
                        frame
                    ),

                    "net5_med": cls._median(
                        frame,
                        "net_5",
                    ),

                    "net10_med": cls._median(
                        frame,
                        "net_10",
                    ),

                    "net20_med": cls._median(
                        frame,
                        "net_20",
                    ),

                    "positive20_pct": (
                        cls._positive_pct(
                            frame
                        )
                    ),

                    "mfe20_med": cls._median(
                        frame,
                        "mfe_20",
                    ),

                    "mae20_med": cls._median(
                        frame,
                        "mae_20",
                    ),
                }
            )

        return pd.DataFrame(
            rows
        )


research_zone_context_forward_ledger = (
    ResearchZoneContextForwardLedger()
)