"""
===============================================================================
Module      : setup_state_engine.py
Project     : PulseViper XAU AI
Version     : 1.1
Author      : Muhammad Adnan
Purpose     : Causal Temporal Scalping Setup State & Quality Telemetry Engine
===============================================================================

Temporal setup sequence
-----------------------
Liquidity sweep
    ↓
Directional displacement
    ↓
Directional BOS
    ↓
Directional FVG
    ↓
Rejection of an FVG attached to the setup
    ↓
READY

Important
---------
Evidence may occur on different candles.

v1.1 adds quality telemetry while preserving v1.0 readiness behavior.

Quality telemetry
-----------------
- displacement score
- impulse strength
- BOS ID
- BOS strength ATR
- BOS break distance ATR
- BOS scope/context
- rejection fill percentage
- FVG count
- causal event indices
- sweep-to-event timing
- sweep-to-ready duration

Engineering
-----------
- Pylance-safe heterogeneous snapshots.
- Output columns are created as one DataFrame block.
- Avoids DataFrame fragmentation from repeated column insertion.
- Preserves canonical setup_direction required by ConfidenceEngine v2.

This engine does NOT:
- open trades
- apply confidence thresholds
- use future candles
- decide which BOS scope is profitable
"""

from __future__ import annotations

from typing import Any

import pandas as pd


class SetupStateEngine:

    DIRECTIONS = (
        "BULLISH",
        "BEARISH",
    )

    BOS_SCOPE_RANK = {
        "NONE": 0,
        "MICRO": 1,
        "INTERNAL": 2,
        "MAJOR": 3,
    }

    # =========================================================================
    # Snapshot contract
    #
    # Every item below becomes:
    #
    # canonical:
    #     setup_<suffix>
    #
    # directional:
    #     bullish_setup_<suffix>
    #     bearish_setup_<suffix>
    # =========================================================================

    SNAPSHOT_SUFFIXES = (
        # ---------------------------------------------------------------------
        # Core identity / lifecycle
        # ---------------------------------------------------------------------
        "id",
        "direction",
        "state",
        "age_bars",
        "evidence_count",
        "ready",

        "start_index",
        "last_event_index",

        # ---------------------------------------------------------------------
        # Core evidence
        # ---------------------------------------------------------------------
        "has_sweep",
        "has_displacement",
        "has_bos",
        "has_fvg",
        "has_rejection",
        "has_mitigation",

        # ---------------------------------------------------------------------
        # Context
        # ---------------------------------------------------------------------
        "structure_alignment",

        # ---------------------------------------------------------------------
        # FVG identity
        # ---------------------------------------------------------------------
        "fvg_id",
        "rejection_fvg_id",

        # ---------------------------------------------------------------------
        # BOS compatibility
        # ---------------------------------------------------------------------
        "bos_scope",

        # ---------------------------------------------------------------------
        # Displacement telemetry
        # ---------------------------------------------------------------------
        "displacement_score",
        "impulse_strength",
        "displacement_index",

        # ---------------------------------------------------------------------
        # BOS telemetry
        # ---------------------------------------------------------------------
        "bos_id",
        "bos_strength_atr",
        "break_distance_atr",
        "bos_event_scope",
        "bos_context",
        "bos_index",

        # ---------------------------------------------------------------------
        # FVG telemetry
        # ---------------------------------------------------------------------
        "fvg_index",
        "fvg_count",

        # ---------------------------------------------------------------------
        # Rejection telemetry
        # ---------------------------------------------------------------------
        "rejection_index",
        "rejection_fill_percent",
        "rejection_strength_fvg_id",

        # ---------------------------------------------------------------------
        # Mitigation telemetry
        # ---------------------------------------------------------------------
        "mitigation_index",
        "mitigation_fill_percent",

        # ---------------------------------------------------------------------
        # Ready timing
        # ---------------------------------------------------------------------
        "ready_index",

        # ---------------------------------------------------------------------
        # Temporal distances
        # ---------------------------------------------------------------------
        "sweep_to_displacement_bars",
        "sweep_to_bos_bars",
        "sweep_to_fvg_bars",
        "sweep_to_rejection_bars",
        "sweep_to_ready_bars",

        "event_span_bars",
    )

    DIRECTIONAL_EVENT_SUFFIXES = (
        "started_event",
        "ready_event",
        "expired_event",
    )

    def __init__(
        self,
        max_setup_bars: int = 20,
    ) -> None:

        if max_setup_bars <= 0:

            raise ValueError(
                "max_setup_bars must be greater than zero"
            )

        self.max_setup_bars = int(
            max_setup_bars
        )

    # =========================================================================
    # Numeric helpers
    # =========================================================================

    @staticmethod
    def _to_float(
        value: Any,
        default: float = 0.0,
    ) -> float:

        if value is None:
            return default

        try:

            missing = pd.isna(
                value
            )

            if isinstance(
                missing,
                bool,
            ):

                if missing:
                    return default

        except (
            TypeError,
            ValueError,
        ):

            pass

        try:

            return float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):

            return default

    @classmethod
    def _flag(
        cls,
        row: pd.Series,
        column: str,
    ) -> bool:

        if column not in row.index:
            return False

        return (
            cls._to_float(
                row[
                    column
                ]
            )
            == 1.0
        )

    @staticmethod
    def _normalize_direction(
        value: Any,
    ) -> str:

        direction = str(
            value
        ).upper()

        if direction in (
            "BULLISH",
            "BEARISH",
        ):

            return direction

        return "NONE"

    @staticmethod
    def _clamp_percent(
        value: float,
    ) -> float:

        return max(
            0.0,
            min(
                100.0,
                float(
                    value
                ),
            ),
        )

    # =========================================================================
    # Validation
    # =========================================================================

    @staticmethod
    def _validate_input(
        df: pd.DataFrame,
    ) -> None:

        if (
            "close"
            not in df.columns
        ):

            raise ValueError(
                "Missing required setup column: close"
            )

    # =========================================================================
    # Setup creation
    # =========================================================================

    @staticmethod
    def _new_setup(
        setup_id: int,
        direction: str,
        index: int,
        timestamp: Any,
    ) -> dict[str, Any]:

        setup: dict[
            str,
            Any,
        ] = {
            # -----------------------------------------------------------------
            # Identity
            # -----------------------------------------------------------------
            "setup_id": setup_id,
            "direction": direction,

            # -----------------------------------------------------------------
            # Lifecycle
            # -----------------------------------------------------------------
            "start_index": index,
            "start_time": timestamp,

            "last_event_index": index,
            "last_event_time": timestamp,

            # -----------------------------------------------------------------
            # Required evidence
            # -----------------------------------------------------------------
            "sweep": 1,
            "displacement": 0,
            "bos": 0,
            "fvg": 0,
            "rejection": 0,

            # -----------------------------------------------------------------
            # Additional lifecycle context
            # -----------------------------------------------------------------
            "mitigation": 0,

            # -----------------------------------------------------------------
            # Displacement telemetry
            # -----------------------------------------------------------------
            "first_displacement_index": -1,

            "displacement_score": 0.0,
            "impulse_strength": 0.0,

            "displacement_quality_seen": False,

            # -----------------------------------------------------------------
            # BOS telemetry
            #
            # bos_scope:
            #     highest structural scope observed.
            #
            # bos_event_scope:
            #     scope belonging to quantitatively strongest BOS event.
            # -----------------------------------------------------------------
            "bos_scope": "NONE",

            "first_bos_index": -1,

            "bos_id": 0,

            "bos_strength_atr": 0.0,
            "break_distance_atr": 0.0,

            "bos_event_scope": "NONE",
            "bos_context": "NONE",

            "bos_quality_seen": False,

            # -----------------------------------------------------------------
            # FVG identity
            # -----------------------------------------------------------------
            "fvg_ids": set(),

            "latest_fvg_id": 0,

            "first_fvg_index": -1,

            # -----------------------------------------------------------------
            # Rejection
            # -----------------------------------------------------------------
            "rejection_fvg_id": 0,

            "first_rejection_index": -1,

            "rejection_fill_percent": 0.0,

            "rejection_strength_fvg_id": 0,

            "rejection_quality_seen": False,

            # -----------------------------------------------------------------
            # Mitigation
            # -----------------------------------------------------------------
            "mitigation_fvg_id": 0,

            "first_mitigation_index": -1,

            "mitigation_fill_percent": 0.0,

            # -----------------------------------------------------------------
            # READY
            # -----------------------------------------------------------------
            "ready": False,

            "ready_index": -1,
            "ready_time": None,
        }

        return setup

    # =========================================================================
    # Touch setup
    # =========================================================================

    @staticmethod
    def _touch(
        setup: dict[str, Any],
        index: int,
        timestamp: Any,
    ) -> None:

        setup[
            "last_event_index"
        ] = index

        setup[
            "last_event_time"
        ] = timestamp

    # =========================================================================
    # BOS scope
    # =========================================================================

    def _update_bos_scope(
        self,
        setup: dict[str, Any],
        new_scope: str,
    ) -> None:

        scope = str(
            new_scope
        ).upper()

        if (
            scope
            not in self.BOS_SCOPE_RANK
        ):

            scope = "MICRO"

        current_scope = str(
            setup.get(
                "bos_scope",
                "NONE",
            )
        ).upper()

        if (
            current_scope
            not in self.BOS_SCOPE_RANK
        ):

            current_scope = "NONE"

        if (
            self.BOS_SCOPE_RANK[
                scope
            ]
            >
            self.BOS_SCOPE_RANK[
                current_scope
            ]
        ):

            setup[
                "bos_scope"
            ] = scope

    # =========================================================================
    # Displacement telemetry
    # =========================================================================

    def _update_displacement_quality(
        self,
        setup: dict[str, Any],
        row: pd.Series,
    ) -> None:

        score = max(
            0.0,
            self._to_float(
                row.get(
                    "displacement_score",
                    row.get(
                        "fvg_displacement_score",
                        0.0,
                    ),
                )
            ),
        )

        impulse = max(
            0.0,
            self._to_float(
                row.get(
                    "impulse_strength",
                    0.0,
                )
            ),
        )

        candidate_rank = (
            score,
            impulse,
        )

        current_rank = (
            float(
                setup[
                    "displacement_score"
                ]
            ),
            float(
                setup[
                    "impulse_strength"
                ]
            ),
        )

        if (
            not bool(
                setup[
                    "displacement_quality_seen"
                ]
            )
            or
            candidate_rank
            > current_rank
        ):

            setup[
                "displacement_score"
            ] = score

            setup[
                "impulse_strength"
            ] = impulse

            setup[
                "displacement_quality_seen"
            ] = True

    # =========================================================================
    # BOS telemetry
    # =========================================================================

    def _update_bos_quality(
        self,
        setup: dict[str, Any],
        row: pd.Series,
        scope: str,
    ) -> None:

        strength_atr = max(
            0.0,
            self._to_float(
                row.get(
                    "bos_strength_atr",
                    0.0,
                )
            ),
        )

        break_distance_atr = max(
            0.0,
            self._to_float(
                row.get(
                    "break_distance_atr",
                    strength_atr,
                )
            ),
        )

        candidate_rank = (
            break_distance_atr,
            strength_atr,
        )

        current_rank = (
            float(
                setup[
                    "break_distance_atr"
                ]
            ),
            float(
                setup[
                    "bos_strength_atr"
                ]
            ),
        )

        if (
            not bool(
                setup[
                    "bos_quality_seen"
                ]
            )
            or
            candidate_rank
            > current_rank
        ):

            setup[
                "bos_id"
            ] = int(
                self._to_float(
                    row.get(
                        "bos_id",
                        0,
                    )
                )
            )

            setup[
                "bos_strength_atr"
            ] = strength_atr

            setup[
                "break_distance_atr"
            ] = break_distance_atr

            setup[
                "bos_event_scope"
            ] = scope

            setup[
                "bos_context"
            ] = str(
                row.get(
                    "bos_context",
                    "NONE",
                )
            ).upper()

            setup[
                "bos_quality_seen"
            ] = True

    # =========================================================================
    # Rejection telemetry
    # =========================================================================

    def _update_rejection_quality(
        self,
        setup: dict[str, Any],
        fvg_id: int,
        fill_percent: float,
    ) -> None:

        fill = (
            self._clamp_percent(
                fill_percent
            )
        )

        current_fill = float(
            setup[
                "rejection_fill_percent"
            ]
        )

        if (
            not bool(
                setup[
                    "rejection_quality_seen"
                ]
            )
            or
            fill
            > current_fill
        ):

            setup[
                "rejection_fill_percent"
            ] = fill

            setup[
                "rejection_strength_fvg_id"
            ] = fvg_id

            setup[
                "rejection_quality_seen"
            ] = True

    # =========================================================================
    # Evidence count
    # =========================================================================

    @staticmethod
    def _evidence_count(
        setup: dict[str, Any],
    ) -> int:

        return int(
            int(
                bool(
                    setup[
                        "sweep"
                    ]
                )
            )
            +
            int(
                bool(
                    setup[
                        "displacement"
                    ]
                )
            )
            +
            int(
                bool(
                    setup[
                        "bos"
                    ]
                )
            )
            +
            int(
                bool(
                    setup[
                        "fvg"
                    ]
                )
            )
            +
            int(
                bool(
                    setup[
                        "rejection"
                    ]
                )
            )
        )

    # =========================================================================
    # READY contract
    # =========================================================================

    @staticmethod
    def _is_ready(
        setup: dict[str, Any],
    ) -> bool:

        return bool(
            setup[
                "sweep"
            ]
            and
            setup[
                "displacement"
            ]
            and
            setup[
                "bos"
            ]
            and
            setup[
                "fvg"
            ]
            and
            setup[
                "rejection"
            ]
        )

    # =========================================================================
    # State
    # =========================================================================

    @staticmethod
    def _state(
        setup: dict[str, Any],
    ) -> str:

        if bool(
            setup[
                "ready"
            ]
        ):

            return "READY"

        if not bool(
            setup[
                "displacement"
            ]
        ):

            return "WAITING_IMPULSE"

        if not bool(
            setup[
                "fvg"
            ]
        ):

            return "WAITING_FVG"

        if not bool(
            setup[
                "bos"
            ]
        ):

            return "WAITING_STRUCTURE"

        if not bool(
            setup[
                "rejection"
            ]
        ):

            return "WAITING_RETRACE"

        return "DEVELOPING"

    # =========================================================================
    # Structure alignment
    # =========================================================================

    @staticmethod
    def _structure_alignment(
        direction: str,
        bias: str,
    ) -> int:

        normalized_direction = str(
            direction
        ).upper()

        normalized_bias = str(
            bias
        ).upper()

        if (
            normalized_direction
            not in (
                "BULLISH",
                "BEARISH",
            )
        ):

            return 0

        if (
            normalized_bias
            not in (
                "BULLISH",
                "BEARISH",
            )
        ):

            return 0

        if (
            normalized_direction
            == normalized_bias
        ):

            return 1

        return -1

    # =========================================================================
    # Primary setup selection
    # =========================================================================

    def _select_primary_setup(
        self,
        active: dict[
            str,
            dict[str, Any] | None,
        ],
    ) -> tuple[
        dict[str, Any] | None,
        bool,
    ]:

        bullish = active[
            "BULLISH"
        ]

        bearish = active[
            "BEARISH"
        ]

        if (
            bullish is None
            and
            bearish is None
        ):

            return None, False

        if bullish is None:

            return bearish, False

        if bearish is None:

            return bullish, False

        bullish_rank = (
            int(
                bool(
                    bullish[
                        "ready"
                    ]
                )
            ),

            self._evidence_count(
                bullish
            ),

            int(
                bullish[
                    "last_event_index"
                ]
            ),

            int(
                bullish[
                    "start_index"
                ]
            ),
        )

        bearish_rank = (
            int(
                bool(
                    bearish[
                        "ready"
                    ]
                )
            ),

            self._evidence_count(
                bearish
            ),

            int(
                bearish[
                    "last_event_index"
                ]
            ),

            int(
                bearish[
                    "start_index"
                ]
            ),
        )

        if (
            bullish_rank
            > bearish_rank
        ):

            return bullish, False

        if (
            bearish_rank
            > bullish_rank
        ):

            return bearish, False

        # ---------------------------------------------------------------------
        # Perfect tie.
        #
        # Do not invent directional preference.
        # ---------------------------------------------------------------------

        return None, True

    # =========================================================================
    # FVG interaction events
    # =========================================================================

    @staticmethod
    def _interaction_events(
        row: pd.Series,
    ) -> list[
        dict[str, Any]
    ]:

        if (
            "fvg_interaction_events"
            in row.index
        ):

            raw_events = row[
                "fvg_interaction_events"
            ]

            if isinstance(
                raw_events,
                list,
            ):

                return [
                    event
                    for event
                    in raw_events
                    if isinstance(
                        event,
                        dict,
                    )
                ]

        # ---------------------------------------------------------------------
        # Scalar fallback
        # ---------------------------------------------------------------------

        interaction = (
            SetupStateEngine
            ._to_float(
                row.get(
                    "fvg_interaction",
                    0,
                )
            )
        )

        if interaction != 1.0:

            return []

        fvg_id = int(
            SetupStateEngine
            ._to_float(
                row.get(
                    "fvg_interaction_id",
                    0,
                )
            )
        )

        if fvg_id <= 0:

            return []

        return [
            {
                "fvg_id": (
                    fvg_id
                ),

                "direction": str(
                    row.get(
                        "fvg_interaction_direction",
                        "NONE",
                    )
                ).upper(),

                "event_type": str(
                    row.get(
                        "fvg_interaction_type",
                        "NONE",
                    )
                ).upper(),

                "fill_percent": (
                    SetupStateEngine
                    ._to_float(
                        row.get(
                            "fvg_interaction_fill_percent",
                            0.0,
                        )
                    )
                ),
            }
        ]

    # =========================================================================
    # Timing
    # =========================================================================

    @staticmethod
    def _lag(
        event_index: int,
        start_index: int,
    ) -> int:

        if event_index < 0:

            return -1

        return max(
            0,
            event_index
            - start_index,
        )

    # =========================================================================
    # Empty snapshot
    # =========================================================================

    def _empty_snapshot(
        self,
    ) -> dict[str, Any]:

        # ---------------------------------------------------------------------
        # Explicit Any is required because snapshot values are heterogeneous.
        # ---------------------------------------------------------------------

        snapshot: dict[
            str,
            Any,
        ] = {
            suffix: 0
            for suffix
            in self.SNAPSHOT_SUFFIXES
        }

        snapshot[
            "direction"
        ] = "NONE"

        snapshot[
            "state"
        ] = "NONE"

        snapshot[
            "age_bars"
        ] = -1

        snapshot[
            "start_index"
        ] = -1

        snapshot[
            "last_event_index"
        ] = -1

        snapshot[
            "bos_scope"
        ] = "NONE"

        snapshot[
            "bos_event_scope"
        ] = "NONE"

        snapshot[
            "bos_context"
        ] = "NONE"

        snapshot[
            "displacement_index"
        ] = -1

        snapshot[
            "bos_index"
        ] = -1

        snapshot[
            "fvg_index"
        ] = -1

        snapshot[
            "rejection_index"
        ] = -1

        snapshot[
            "mitigation_index"
        ] = -1

        snapshot[
            "ready_index"
        ] = -1

        snapshot[
            "sweep_to_displacement_bars"
        ] = -1

        snapshot[
            "sweep_to_bos_bars"
        ] = -1

        snapshot[
            "sweep_to_fvg_bars"
        ] = -1

        snapshot[
            "sweep_to_rejection_bars"
        ] = -1

        snapshot[
            "sweep_to_ready_bars"
        ] = -1

        snapshot[
            "event_span_bars"
        ] = -1

        return snapshot

    # =========================================================================
    # Active setup snapshot
    # =========================================================================

    def _snapshot(
        self,
        setup: dict[str, Any] | None,
        direction: str,
        current_index: int,
        structure_bias: str,
    ) -> dict[str, Any]:

        if setup is None:

            return (
                self._empty_snapshot()
            )

        start_index = int(
            setup[
                "start_index"
            ]
        )

        displacement_index = int(
            setup[
                "first_displacement_index"
            ]
        )

        bos_index = int(
            setup[
                "first_bos_index"
            ]
        )

        fvg_index = int(
            setup[
                "first_fvg_index"
            ]
        )

        rejection_index = int(
            setup[
                "first_rejection_index"
            ]
        )

        mitigation_index = int(
            setup[
                "first_mitigation_index"
            ]
        )

        ready_index = int(
            setup[
                "ready_index"
            ]
        )

        fvg_ids = setup[
            "fvg_ids"
        ]

        fvg_count = (
            len(
                fvg_ids
            )
            if isinstance(
                fvg_ids,
                set,
            )
            else 0
        )

        snapshot: dict[
            str,
            Any,
        ] = {
            # -----------------------------------------------------------------
            # Identity
            # -----------------------------------------------------------------
            "id": int(
                setup[
                    "setup_id"
                ]
            ),

            "direction": str(
                setup[
                    "direction"
                ]
            ).upper(),

            # -----------------------------------------------------------------
            # Lifecycle
            # -----------------------------------------------------------------
            "state": (
                self._state(
                    setup
                )
            ),

            "age_bars": (
                current_index
                - start_index
            ),

            "evidence_count": (
                self._evidence_count(
                    setup
                )
            ),

            "ready": int(
                bool(
                    setup[
                        "ready"
                    ]
                )
            ),

            "start_index": (
                start_index
            ),

            "last_event_index": int(
                setup[
                    "last_event_index"
                ]
            ),

            # -----------------------------------------------------------------
            # Required evidence
            # -----------------------------------------------------------------
            "has_sweep": int(
                bool(
                    setup[
                        "sweep"
                    ]
                )
            ),

            "has_displacement": int(
                bool(
                    setup[
                        "displacement"
                    ]
                )
            ),

            "has_bos": int(
                bool(
                    setup[
                        "bos"
                    ]
                )
            ),

            "has_fvg": int(
                bool(
                    setup[
                        "fvg"
                    ]
                )
            ),

            "has_rejection": int(
                bool(
                    setup[
                        "rejection"
                    ]
                )
            ),

            "has_mitigation": int(
                bool(
                    setup[
                        "mitigation"
                    ]
                )
            ),

            # -----------------------------------------------------------------
            # Context
            # -----------------------------------------------------------------
            "structure_alignment": (
                self._structure_alignment(
                    direction=direction,
                    bias=structure_bias,
                )
            ),

            # -----------------------------------------------------------------
            # FVG identity
            # -----------------------------------------------------------------
            "fvg_id": int(
                setup[
                    "latest_fvg_id"
                ]
            ),

            "rejection_fvg_id": int(
                setup[
                    "rejection_fvg_id"
                ]
            ),

            # -----------------------------------------------------------------
            # BOS structural scope
            # -----------------------------------------------------------------
            "bos_scope": str(
                setup[
                    "bos_scope"
                ]
            ).upper(),

            # -----------------------------------------------------------------
            # Displacement telemetry
            # -----------------------------------------------------------------
            "displacement_score": round(
                float(
                    setup[
                        "displacement_score"
                    ]
                ),
                4,
            ),

            "impulse_strength": round(
                float(
                    setup[
                        "impulse_strength"
                    ]
                ),
                4,
            ),

            "displacement_index": (
                displacement_index
            ),

            # -----------------------------------------------------------------
            # BOS telemetry
            # -----------------------------------------------------------------
            "bos_id": int(
                setup[
                    "bos_id"
                ]
            ),

            "bos_strength_atr": round(
                float(
                    setup[
                        "bos_strength_atr"
                    ]
                ),
                6,
            ),

            "break_distance_atr": round(
                float(
                    setup[
                        "break_distance_atr"
                    ]
                ),
                6,
            ),

            "bos_event_scope": str(
                setup[
                    "bos_event_scope"
                ]
            ).upper(),

            "bos_context": str(
                setup[
                    "bos_context"
                ]
            ).upper(),

            "bos_index": (
                bos_index
            ),

            # -----------------------------------------------------------------
            # FVG telemetry
            # -----------------------------------------------------------------
            "fvg_index": (
                fvg_index
            ),

            "fvg_count": (
                fvg_count
            ),

            # -----------------------------------------------------------------
            # Rejection telemetry
            # -----------------------------------------------------------------
            "rejection_index": (
                rejection_index
            ),

            "rejection_fill_percent": round(
                float(
                    setup[
                        "rejection_fill_percent"
                    ]
                ),
                4,
            ),

            "rejection_strength_fvg_id": int(
                setup[
                    "rejection_strength_fvg_id"
                ]
            ),

            # -----------------------------------------------------------------
            # Mitigation telemetry
            # -----------------------------------------------------------------
            "mitigation_index": (
                mitigation_index
            ),

            "mitigation_fill_percent": round(
                float(
                    setup[
                        "mitigation_fill_percent"
                    ]
                ),
                4,
            ),

            # -----------------------------------------------------------------
            # READY
            # -----------------------------------------------------------------
            "ready_index": (
                ready_index
            ),

            # -----------------------------------------------------------------
            # Timing
            # -----------------------------------------------------------------
            "sweep_to_displacement_bars": (
                self._lag(
                    displacement_index,
                    start_index,
                )
            ),

            "sweep_to_bos_bars": (
                self._lag(
                    bos_index,
                    start_index,
                )
            ),

            "sweep_to_fvg_bars": (
                self._lag(
                    fvg_index,
                    start_index,
                )
            ),

            "sweep_to_rejection_bars": (
                self._lag(
                    rejection_index,
                    start_index,
                )
            ),

            "sweep_to_ready_bars": (
                self._lag(
                    ready_index,
                    start_index,
                )
            ),

            "event_span_bars": max(
                0,
                int(
                    setup[
                        "last_event_index"
                    ]
                )
                - start_index,
            ),
        }

        return snapshot

    # =========================================================================
    # Generate
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

        if (
            "time"
            in df.columns
        ):

            time_values = (
                df[
                    "time"
                ]
                .tolist()
            )

        else:

            time_values = list(
                df.index
            )

        # =====================================================================
        # Runtime setup state
        # =====================================================================

        active: dict[
            str,
            dict[str, Any] | None,
        ] = {
            "BULLISH": None,
            "BEARISH": None,
        }

        next_setup_id = 1

        # =====================================================================
        # Buffers
        # =====================================================================

        directional_suffixes = (
            self.SNAPSHOT_SUFFIXES
            +
            self.DIRECTIONAL_EVENT_SUFFIXES
        )

        directional_buffers: dict[
            str,
            dict[
                str,
                list[Any],
            ],
        ] = {}

        for direction in (
            self.DIRECTIONS
        ):

            directional_buffers[
                direction
            ] = {
                suffix: []
                for suffix
                in directional_suffixes
            }

        canonical_buffers: dict[
            str,
            list[Any],
        ] = {
            suffix: []
            for suffix
            in self.SNAPSHOT_SUFFIXES
        }

        setup_ready_event_buffer: list[int] = []
        setup_conflict_buffer: list[int] = []

        # =====================================================================
        # Chronological scan
        # =====================================================================

        for i in range(
            row_count
        ):

            row = df.iloc[
                i
            ]

            timestamp = (
                time_values[
                    i
                ]
            )

            started_event: dict[
                str,
                int,
            ] = {
                "BULLISH": 0,
                "BEARISH": 0,
            }

            ready_event: dict[
                str,
                int,
            ] = {
                "BULLISH": 0,
                "BEARISH": 0,
            }

            expired_event: dict[
                str,
                int,
            ] = {
                "BULLISH": 0,
                "BEARISH": 0,
            }

            # =================================================================
            # STEP 1
            # Expire stale setup.
            # =================================================================

            for direction in (
                self.DIRECTIONS
            ):

                setup = active[
                    direction
                ]

                if setup is None:
                    continue

                age = (
                    i
                    - int(
                        setup[
                            "start_index"
                        ]
                    )
                )

                if (
                    age
                    > self.max_setup_bars
                ):

                    active[
                        direction
                    ] = None

                    expired_event[
                        direction
                    ] = 1

            # =================================================================
            # STEP 2
            # Liquidity sweep starts new directional setup.
            # =================================================================

            bullish_sweep = (
                self._flag(
                    row,
                    "bullish_sweep",
                )
            )

            bearish_sweep = (
                self._flag(
                    row,
                    "bearish_sweep",
                )
            )

            # Compatibility aliases.
            if (
                not bullish_sweep
                and
                self._flag(
                    row,
                    "sell_side_sweep",
                )
            ):

                bullish_sweep = True

            if (
                not bearish_sweep
                and
                self._flag(
                    row,
                    "buy_side_sweep",
                )
            ):

                bearish_sweep = True

            if bullish_sweep:

                active[
                    "BULLISH"
                ] = self._new_setup(
                    setup_id=(
                        next_setup_id
                    ),
                    direction="BULLISH",
                    index=i,
                    timestamp=timestamp,
                )

                next_setup_id += 1

                started_event[
                    "BULLISH"
                ] = 1

            if bearish_sweep:

                active[
                    "BEARISH"
                ] = self._new_setup(
                    setup_id=(
                        next_setup_id
                    ),
                    direction="BEARISH",
                    index=i,
                    timestamp=timestamp,
                )

                next_setup_id += 1

                started_event[
                    "BEARISH"
                ] = 1

            # =================================================================
            # STEP 3
            # Directional displacement.
            # =================================================================

            displacement_direction = (
                "NONE"
            )

            institutional_move = int(
                self._to_float(
                    row.get(
                        "institutional_move",
                        0,
                    )
                )
            )

            if institutional_move > 0:

                displacement_direction = (
                    "BULLISH"
                )

            elif institutional_move < 0:

                displacement_direction = (
                    "BEARISH"
                )

            elif self._flag(
                row,
                "is_displacement",
            ):

                current_open = (
                    self._to_float(
                        row.get(
                            "open",
                            0.0,
                        )
                    )
                )

                current_close = (
                    self._to_float(
                        row.get(
                            "close",
                            0.0,
                        )
                    )
                )

                if (
                    current_close
                    > current_open
                ):

                    displacement_direction = (
                        "BULLISH"
                    )

                elif (
                    current_close
                    < current_open
                ):

                    displacement_direction = (
                        "BEARISH"
                    )

            if (
                displacement_direction
                in self.DIRECTIONS
            ):

                setup = active[
                    displacement_direction
                ]

                if setup is not None:

                    if (
                        int(
                            setup[
                                "first_displacement_index"
                            ]
                        )
                        < 0
                    ):

                        setup[
                            "first_displacement_index"
                        ] = i

                    setup[
                        "displacement"
                    ] = 1

                    self._update_displacement_quality(
                        setup,
                        row,
                    )

                    self._touch(
                        setup,
                        i,
                        timestamp,
                    )

            # =================================================================
            # STEP 4
            # Directional BOS.
            # =================================================================

            bos_inputs = (
                (
                    "BULLISH",
                    "bullish_bos",
                ),
                (
                    "BEARISH",
                    "bearish_bos",
                ),
            )

            for (
                direction,
                bos_column,
            ) in bos_inputs:

                if not self._flag(
                    row,
                    bos_column,
                ):

                    continue

                setup = active[
                    direction
                ]

                if setup is None:
                    continue

                setup[
                    "bos"
                ] = 1

                if (
                    int(
                        setup[
                            "first_bos_index"
                        ]
                    )
                    < 0
                ):

                    setup[
                        "first_bos_index"
                    ] = i

                scope = str(
                    row.get(
                        "bos_scope",
                        row.get(
                            "broken_swing_scale",
                            "MICRO",
                        ),
                    )
                ).upper()

                if (
                    scope
                    not in self.BOS_SCOPE_RANK
                ):

                    scope = "MICRO"

                self._update_bos_scope(
                    setup,
                    scope,
                )

                self._update_bos_quality(
                    setup,
                    row,
                    scope,
                )

                self._touch(
                    setup,
                    i,
                    timestamp,
                )

            # =================================================================
            # STEP 5
            # Directional FVG creation.
            # =================================================================

            current_fvg_id = int(
                self._to_float(
                    row.get(
                        "fvg_id",
                        0,
                    )
                )
            )

            if current_fvg_id > 0:

                fvg_direction = (
                    "NONE"
                )

                if self._flag(
                    row,
                    "bullish_fvg",
                ):

                    fvg_direction = (
                        "BULLISH"
                    )

                elif self._flag(
                    row,
                    "bearish_fvg",
                ):

                    fvg_direction = (
                        "BEARISH"
                    )

                if (
                    fvg_direction
                    in self.DIRECTIONS
                ):

                    setup = active[
                        fvg_direction
                    ]

                    if setup is not None:

                        fvg_ids = setup[
                            "fvg_ids"
                        ]

                        if isinstance(
                            fvg_ids,
                            set,
                        ):

                            fvg_ids.add(
                                current_fvg_id
                            )

                        if (
                            int(
                                setup[
                                    "first_fvg_index"
                                ]
                            )
                            < 0
                        ):

                            setup[
                                "first_fvg_index"
                            ] = i

                        setup[
                            "latest_fvg_id"
                        ] = (
                            current_fvg_id
                        )

                        setup[
                            "fvg"
                        ] = 1

                        self._touch(
                            setup,
                            i,
                            timestamp,
                        )

            # =================================================================
            # STEP 6
            # Exact FVG lifecycle event.
            # =================================================================

            interaction_events = (
                self._interaction_events(
                    row
                )
            )

            for event in (
                interaction_events
            ):

                event_fvg_id = int(
                    self._to_float(
                        event.get(
                            "fvg_id",
                            0,
                        )
                    )
                )

                if event_fvg_id <= 0:
                    continue

                event_direction = (
                    self._normalize_direction(
                        event.get(
                            "direction",
                            "NONE",
                        )
                    )
                )

                if (
                    event_direction
                    not in self.DIRECTIONS
                ):

                    continue

                setup = active[
                    event_direction
                ]

                if setup is None:
                    continue

                fvg_ids = setup[
                    "fvg_ids"
                ]

                if not isinstance(
                    fvg_ids,
                    set,
                ):

                    continue

                # -------------------------------------------------------------
                # Exact identity protection.
                # -------------------------------------------------------------

                if (
                    event_fvg_id
                    not in fvg_ids
                ):

                    continue

                event_type = str(
                    event.get(
                        "event_type",
                        "NONE",
                    )
                ).upper()

                fill_percent = (
                    self._to_float(
                        event.get(
                            "fill_percent",
                            0.0,
                        )
                    )
                )

                # -------------------------------------------------------------
                # Rejection
                # -------------------------------------------------------------

                if (
                    event_type
                    == "REJECTION"
                ):

                    setup[
                        "rejection"
                    ] = 1

                    setup[
                        "rejection_fvg_id"
                    ] = (
                        event_fvg_id
                    )

                    setup[
                        "latest_fvg_id"
                    ] = (
                        event_fvg_id
                    )

                    if (
                        int(
                            setup[
                                "first_rejection_index"
                            ]
                        )
                        < 0
                    ):

                        setup[
                            "first_rejection_index"
                        ] = i

                    self._update_rejection_quality(
                        setup,
                        event_fvg_id,
                        fill_percent,
                    )

                    self._touch(
                        setup,
                        i,
                        timestamp,
                    )

                # -------------------------------------------------------------
                # Mitigation
                # -------------------------------------------------------------

                elif (
                    event_type
                    == "MITIGATION"
                ):

                    setup[
                        "mitigation"
                    ] = 1

                    setup[
                        "mitigation_fvg_id"
                    ] = (
                        event_fvg_id
                    )

                    if (
                        int(
                            setup[
                                "first_mitigation_index"
                            ]
                        )
                        < 0
                    ):

                        setup[
                            "first_mitigation_index"
                        ] = i

                    setup[
                        "mitigation_fill_percent"
                    ] = max(
                        float(
                            setup[
                                "mitigation_fill_percent"
                            ]
                        ),
                        self._clamp_percent(
                            fill_percent
                        ),
                    )

                    self._touch(
                        setup,
                        i,
                        timestamp,
                    )

            # =================================================================
            # STEP 7
            # READY transition.
            # =================================================================

            for direction in (
                self.DIRECTIONS
            ):

                setup = active[
                    direction
                ]

                if setup is None:
                    continue

                if (
                    not bool(
                        setup[
                            "ready"
                        ]
                    )
                    and
                    self._is_ready(
                        setup
                    )
                ):

                    setup[
                        "ready"
                    ] = True

                    setup[
                        "ready_index"
                    ] = i

                    setup[
                        "ready_time"
                    ] = timestamp

                    ready_event[
                        direction
                    ] = 1

                    self._touch(
                        setup,
                        i,
                        timestamp,
                    )

            # =================================================================
            # STEP 8
            # Directional snapshots.
            # =================================================================

            structure_bias = str(
                row.get(
                    "structure_bias",
                    "NEUTRAL",
                )
            ).upper()

            for direction in (
                self.DIRECTIONS
            ):

                snapshot = (
                    self._snapshot(
                        setup=active[
                            direction
                        ],
                        direction=direction,
                        current_index=i,
                        structure_bias=(
                            structure_bias
                        ),
                    )
                )

                buffer = (
                    directional_buffers[
                        direction
                    ]
                )

                for suffix in (
                    self.SNAPSHOT_SUFFIXES
                ):

                    buffer[
                        suffix
                    ].append(
                        snapshot[
                            suffix
                        ]
                    )

                buffer[
                    "started_event"
                ].append(
                    started_event[
                        direction
                    ]
                )

                buffer[
                    "ready_event"
                ].append(
                    ready_event[
                        direction
                    ]
                )

                buffer[
                    "expired_event"
                ].append(
                    expired_event[
                        direction
                    ]
                )

            # =================================================================
            # STEP 9
            # Canonical primary setup.
            # =================================================================

            (
                primary,
                conflict,
            ) = (
                self._select_primary_setup(
                    active
                )
            )

            setup_conflict_buffer.append(
                int(
                    conflict
                )
            )

            primary_snapshot: dict[
                str,
                Any,
            ]

            canonical_ready_event: int

            if primary is None:

                primary_snapshot = (
                    self._empty_snapshot()
                )

                canonical_ready_event = 0

                if conflict:

                    primary_snapshot[
                        "direction"
                    ] = "CONFLICT"

                    primary_snapshot[
                        "state"
                    ] = "CONFLICT"

            else:

                primary_direction = str(
                    primary[
                        "direction"
                    ]
                ).upper()

                primary_snapshot = (
                    self._snapshot(
                        setup=primary,
                        direction=(
                            primary_direction
                        ),
                        current_index=i,
                        structure_bias=(
                            structure_bias
                        ),
                    )
                )

                canonical_ready_event = int(
                    ready_event[
                        primary_direction
                    ]
                )

            for suffix in (
                self.SNAPSHOT_SUFFIXES
            ):

                canonical_buffers[
                    suffix
                ].append(
                    primary_snapshot[
                        suffix
                    ]
                )

            setup_ready_event_buffer.append(
                canonical_ready_event
            )

        # =====================================================================
        # Build output columns in memory.
        #
        # No repeated df[column] insertion.
        # =====================================================================

        output_columns: dict[
            str,
            list[Any],
        ] = {}

        # ---------------------------------------------------------------------
        # Directional outputs
        # ---------------------------------------------------------------------

        for direction in (
            self.DIRECTIONS
        ):

            prefix = (
                direction.lower()
            )

            buffer = (
                directional_buffers[
                    direction
                ]
            )

            for suffix in (
                directional_suffixes
            ):

                output_columns[
                    f"{prefix}_setup_{suffix}"
                ] = buffer[
                    suffix
                ]

        # ---------------------------------------------------------------------
        # Canonical outputs
        # ---------------------------------------------------------------------

        for suffix in (
            self.SNAPSHOT_SUFFIXES
        ):

            output_columns[
                f"setup_{suffix}"
            ] = canonical_buffers[
                suffix
            ]

        output_columns[
            "setup_ready_event"
        ] = (
            setup_ready_event_buffer
        )

        output_columns[
            "setup_conflict"
        ] = (
            setup_conflict_buffer
        )

        # =====================================================================
        # Remove old setup output columns if generate() is called twice.
        # =====================================================================

        output_names = list(
            output_columns.keys()
        )

        existing_outputs = [
            column
            for column
            in output_names
            if column
            in df.columns
        ]

        if existing_outputs:

            df = df.drop(
                columns=(
                    existing_outputs
                )
            )

        # =====================================================================
        # Single-block output assignment.
        # =====================================================================

        output_frame = pd.DataFrame(
            output_columns,
            index=df.index,
        )

        result = pd.concat(
            [
                df,
                output_frame,
            ],
            axis=1,
        )

        return result


setup_state_engine = (
    SetupStateEngine()
)