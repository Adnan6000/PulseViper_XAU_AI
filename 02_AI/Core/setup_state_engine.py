"""
===============================================================================
Module      : setup_state_engine.py
Project     : PulseViper XAU AI
Version     : 1.0
Author      : Muhammad Adnan
Purpose     : Causal Temporal Scalping Setup State Engine
===============================================================================

Purpose
-------
A real scalp setup does not normally complete on one candle.

Example:

    10:31  sell-side liquidity sweep
    10:32  bullish displacement
    10:33  bullish BOS
    10:34  bullish FVG
    10:37  bullish FVG rejection
           -> bullish setup READY

This engine preserves that evidence across candles.

Core principles
---------------
1. A setup starts from a directional liquidity sweep.
2. Evidence may arrive on different candles.
3. Bullish and bearish setups are tracked independently.
4. Opposite-direction evidence cannot contaminate a setup.
5. FVG rejection must belong to an FVG attached to that setup.
6. Setup memory expires after a configurable number of bars.
7. A fresh same-direction sweep starts a fresh setup.
8. No confidence threshold is applied here.
9. No trade is opened here.
10. This engine only builds truthful temporal market state.
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
    # Numeric Helpers
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
                row[column]
            )
            == 1.0
        )

    # =========================================================================
    # Validation
    # =========================================================================

    @staticmethod
    def _validate_input(
        df: pd.DataFrame,
    ) -> None:

        if "close" not in df.columns:

            raise ValueError(
                "Missing required setup column: close"
            )

    # =========================================================================
    # Setup Object
    # =========================================================================

    @staticmethod
    def _new_setup(
        setup_id: int,
        direction: str,
        index: int,
        timestamp: Any,
    ) -> dict[str, Any]:

        return {
            "setup_id": (
                setup_id
            ),
            "direction": (
                direction
            ),

            "start_index": (
                index
            ),
            "start_time": (
                timestamp
            ),

            "last_event_index": (
                index
            ),
            "last_event_time": (
                timestamp
            ),

            # -------------------------------------------------------------
            # Core evidence
            # -------------------------------------------------------------

            "sweep": 1,
            "displacement": 0,
            "bos": 0,
            "fvg": 0,
            "rejection": 0,

            # -------------------------------------------------------------
            # Lifecycle/context evidence
            # -------------------------------------------------------------

            "mitigation": 0,

            # -------------------------------------------------------------
            # Exact FVG linkage
            # -------------------------------------------------------------

            "fvg_ids": set(),

            "latest_fvg_id": 0,

            "rejection_fvg_id": 0,

            "mitigation_fvg_id": 0,

            # -------------------------------------------------------------
            # BOS metadata
            # -------------------------------------------------------------

            "bos_scope": (
                "NONE"
            ),

            # -------------------------------------------------------------
            # Ready state
            # -------------------------------------------------------------

            "ready": False,

            "ready_index": -1,

            "ready_time": None,
        }

    # =========================================================================
    # Touch Setup
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
    # BOS Scope
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
            setup[
                "bos_scope"
            ]
        ).upper()

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
    # Evidence Count
    # =========================================================================

    @staticmethod
    def _evidence_count(
        setup: dict[str, Any],
    ) -> int:

        return int(
            setup["sweep"]
            + setup["displacement"]
            + setup["bos"]
            + setup["fvg"]
            + setup["rejection"]
        )

    # =========================================================================
    # Ready Contract
    # =========================================================================

    @staticmethod
    def _is_ready(
        setup: dict[str, Any],
    ) -> bool:
        """
        Setup readiness does NOT require all evidence on one candle.

        Required temporal evidence:

            sweep
            + directional displacement
            + directional BOS
            + directional FVG
            + rejection of an attached FVG
        """

        return bool(
            setup["sweep"]
            and
            setup["displacement"]
            and
            setup["bos"]
            and
            setup["fvg"]
            and
            setup["rejection"]
        )

    # =========================================================================
    # State
    # =========================================================================

    @staticmethod
    def _state(
        setup: dict[str, Any],
    ) -> str:

        if setup["ready"]:
            return "READY"

        if not setup[
            "displacement"
        ]:
            return "WAITING_IMPULSE"

        if not setup[
            "fvg"
        ]:
            return "WAITING_FVG"

        if not setup[
            "bos"
        ]:
            return "WAITING_STRUCTURE"

        if not setup[
            "rejection"
        ]:
            return "WAITING_RETRACE"

        return "DEVELOPING"

    # =========================================================================
    # Structure Alignment
    # =========================================================================

    @staticmethod
    def _structure_alignment(
        direction: str,
        bias: str,
    ) -> int:

        normalized_bias = str(
            bias
        ).upper()

        if normalized_bias not in (
            "BULLISH",
            "BEARISH",
        ):
            return 0

        if (
            normalized_bias
            == direction
        ):
            return 1

        return -1

    # =========================================================================
    # Primary Setup Selection
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
                bullish[
                    "ready"
                ]
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
                bearish[
                    "ready"
                ]
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

        # -----------------------------------------------------------------
        # Exact tie:
        # do not invent directional preference.
        # -----------------------------------------------------------------

        return None, True

    # =========================================================================
    # FVG Interaction Events
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

        # -----------------------------------------------------------------
        # Scalar fallback for compatibility.
        # -----------------------------------------------------------------

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

        if "time" in df.columns:

            time_values = (
                df["time"]
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
        # Directional output buffers
        # =====================================================================

        directional_buffers: dict[
            str,
            dict[str, list[Any]],
        ] = {}

        for direction in (
            self.DIRECTIONS
        ):

            directional_buffers[
                direction
            ] = {
                "id": [],
                "state": [],
                "age": [],
                "evidence": [],
                "ready": [],
                "ready_event": [],
                "started_event": [],
                "expired_event": [],
                "start_index": [],
                "last_event_index": [],
                "fvg_id": [],
                "rejection_fvg_id": [],
                "bos_scope": [],
                "structure_alignment": [],
                "has_sweep": [],
                "has_displacement": [],
                "has_bos": [],
                "has_fvg": [],
                "has_rejection": [],
                "has_mitigation": [],
            }

        # =====================================================================
        # Canonical output buffers
        # =====================================================================

        setup_id_buffer: list[int] = []
        setup_direction_buffer: list[str] = []
        setup_state_buffer: list[str] = []
        setup_age_buffer: list[int] = []
        setup_evidence_buffer: list[int] = []
        setup_ready_buffer: list[int] = []
        setup_ready_event_buffer: list[int] = []
        setup_conflict_buffer: list[int] = []

        setup_start_index_buffer: list[
            int
        ] = []

        setup_last_event_index_buffer: list[
            int
        ] = []

        setup_fvg_id_buffer: list[
            int
        ] = []

        setup_rejection_fvg_id_buffer: list[
            int
        ] = []

        setup_bos_scope_buffer: list[
            str
        ] = []

        setup_structure_alignment_buffer: list[
            int
        ] = []

        setup_has_sweep_buffer: list[
            int
        ] = []

        setup_has_displacement_buffer: list[
            int
        ] = []

        setup_has_bos_buffer: list[
            int
        ] = []

        setup_has_fvg_buffer: list[
            int
        ] = []

        setup_has_rejection_buffer: list[
            int
        ] = []

        setup_has_mitigation_buffer: list[
            int
        ] = []

        # =====================================================================
        # Chronological Scan
        # =====================================================================

        for i in range(
            row_count
        ):

            row = df.iloc[i]

            timestamp = (
                time_values[i]
            )

            started_event = {
                "BULLISH": 0,
                "BEARISH": 0,
            }

            ready_event = {
                "BULLISH": 0,
                "BEARISH": 0,
            }

            expired_event = {
                "BULLISH": 0,
                "BEARISH": 0,
            }

            # =================================================================
            # STEP 1
            # Expire stale setups.
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
            # Directional liquidity sweep starts a fresh setup.
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

            # -----------------------------------------------------------------
            # Compatibility fallback:
            #
            # sell-side raid -> bullish
            # buy-side raid  -> bearish
            # -----------------------------------------------------------------

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
                    direction=(
                        "BULLISH"
                    ),
                    index=i,
                    timestamp=(
                        timestamp
                    ),
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
                    direction=(
                        "BEARISH"
                    ),
                    index=i,
                    timestamp=(
                        timestamp
                    ),
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

                    setup[
                        "displacement"
                    ] = 1

                    self._touch(
                        setup,
                        i,
                        timestamp,
                    )

            # =================================================================
            # STEP 4
            # Directional BOS.
            # =================================================================

            for (
                direction,
                column,
            ) in (
                (
                    "BULLISH",
                    "bullish_bos",
                ),
                (
                    "BEARISH",
                    "bearish_bos",
                ),
            ):

                if not self._flag(
                    row,
                    column,
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

                scope = str(
                    row.get(
                        "bos_scope",
                        row.get(
                            "broken_swing_scale",
                            "MICRO",
                        ),
                    )
                ).upper()

                self._update_bos_scope(
                    setup,
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

                        setup[
                            "latest_fvg_id"
                        ] = current_fvg_id

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
            # FVG lifecycle events.
            #
            # Rejection only counts when:
            # - direction matches setup
            # - FVG ID belongs to that setup
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

                event_direction = str(
                    event.get(
                        "direction",
                        "NONE",
                    )
                ).upper()

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
                # Identity protection:
                # unrelated FVG must not contaminate setup.
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

                    self._touch(
                        setup,
                        i,
                        timestamp,
                    )

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

                    self._touch(
                        setup,
                        i,
                        timestamp,
                    )

            # =================================================================
            # STEP 7
            # Ready transition.
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
                    not setup[
                        "ready"
                    ]
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

                setup = active[
                    direction
                ]

                buffer = (
                    directional_buffers[
                        direction
                    ]
                )

                if setup is None:

                    buffer[
                        "id"
                    ].append(
                        0
                    )

                    buffer[
                        "state"
                    ].append(
                        "NONE"
                    )

                    buffer[
                        "age"
                    ].append(
                        -1
                    )

                    buffer[
                        "evidence"
                    ].append(
                        0
                    )

                    buffer[
                        "ready"
                    ].append(
                        0
                    )

                    buffer[
                        "start_index"
                    ].append(
                        -1
                    )

                    buffer[
                        "last_event_index"
                    ].append(
                        -1
                    )

                    buffer[
                        "fvg_id"
                    ].append(
                        0
                    )

                    buffer[
                        "rejection_fvg_id"
                    ].append(
                        0
                    )

                    buffer[
                        "bos_scope"
                    ].append(
                        "NONE"
                    )

                    buffer[
                        "structure_alignment"
                    ].append(
                        0
                    )

                    for key in (
                        "has_sweep",
                        "has_displacement",
                        "has_bos",
                        "has_fvg",
                        "has_rejection",
                        "has_mitigation",
                    ):

                        buffer[
                            key
                        ].append(
                            0
                        )

                else:

                    buffer[
                        "id"
                    ].append(
                        int(
                            setup[
                                "setup_id"
                            ]
                        )
                    )

                    buffer[
                        "state"
                    ].append(
                        self._state(
                            setup
                        )
                    )

                    buffer[
                        "age"
                    ].append(
                        i
                        - int(
                            setup[
                                "start_index"
                            ]
                        )
                    )

                    buffer[
                        "evidence"
                    ].append(
                        self._evidence_count(
                            setup
                        )
                    )

                    buffer[
                        "ready"
                    ].append(
                        int(
                            setup[
                                "ready"
                            ]
                        )
                    )

                    buffer[
                        "start_index"
                    ].append(
                        int(
                            setup[
                                "start_index"
                            ]
                        )
                    )

                    buffer[
                        "last_event_index"
                    ].append(
                        int(
                            setup[
                                "last_event_index"
                            ]
                        )
                    )

                    buffer[
                        "fvg_id"
                    ].append(
                        int(
                            setup[
                                "latest_fvg_id"
                            ]
                        )
                    )

                    buffer[
                        "rejection_fvg_id"
                    ].append(
                        int(
                            setup[
                                "rejection_fvg_id"
                            ]
                        )
                    )

                    buffer[
                        "bos_scope"
                    ].append(
                        str(
                            setup[
                                "bos_scope"
                            ]
                        )
                    )

                    buffer[
                        "structure_alignment"
                    ].append(
                        self._structure_alignment(
                            direction=(
                                direction
                            ),
                            bias=(
                                structure_bias
                            ),
                        )
                    )

                    buffer[
                        "has_sweep"
                    ].append(
                        int(
                            setup[
                                "sweep"
                            ]
                        )
                    )

                    buffer[
                        "has_displacement"
                    ].append(
                        int(
                            setup[
                                "displacement"
                            ]
                        )
                    )

                    buffer[
                        "has_bos"
                    ].append(
                        int(
                            setup[
                                "bos"
                            ]
                        )
                    )

                    buffer[
                        "has_fvg"
                    ].append(
                        int(
                            setup[
                                "fvg"
                            ]
                        )
                    )

                    buffer[
                        "has_rejection"
                    ].append(
                        int(
                            setup[
                                "rejection"
                            ]
                        )
                    )

                    buffer[
                        "has_mitigation"
                    ].append(
                        int(
                            setup[
                                "mitigation"
                            ]
                        )
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

            if (
                primary is None
            ):

                setup_id_buffer.append(
                    0
                )

                setup_direction_buffer.append(
                    (
                        "CONFLICT"
                        if conflict
                        else "NONE"
                    )
                )

                setup_state_buffer.append(
                    (
                        "CONFLICT"
                        if conflict
                        else "NONE"
                    )
                )

                setup_age_buffer.append(
                    -1
                )

                setup_evidence_buffer.append(
                    0
                )

                setup_ready_buffer.append(
                    0
                )

                setup_ready_event_buffer.append(
                    0
                )

                setup_start_index_buffer.append(
                    -1
                )

                setup_last_event_index_buffer.append(
                    -1
                )

                setup_fvg_id_buffer.append(
                    0
                )

                setup_rejection_fvg_id_buffer.append(
                    0
                )

                setup_bos_scope_buffer.append(
                    "NONE"
                )

                setup_structure_alignment_buffer.append(
                    0
                )

                setup_has_sweep_buffer.append(
                    0
                )

                setup_has_displacement_buffer.append(
                    0
                )

                setup_has_bos_buffer.append(
                    0
                )

                setup_has_fvg_buffer.append(
                    0
                )

                setup_has_rejection_buffer.append(
                    0
                )

                setup_has_mitigation_buffer.append(
                    0
                )

            else:

                primary_direction = str(
                    primary[
                        "direction"
                    ]
                )

                setup_id_buffer.append(
                    int(
                        primary[
                            "setup_id"
                        ]
                    )
                )

                setup_direction_buffer.append(
                    primary_direction
                )

                setup_state_buffer.append(
                    self._state(
                        primary
                    )
                )

                setup_age_buffer.append(
                    i
                    - int(
                        primary[
                            "start_index"
                        ]
                    )
                )

                setup_evidence_buffer.append(
                    self._evidence_count(
                        primary
                    )
                )

                setup_ready_buffer.append(
                    int(
                        primary[
                            "ready"
                        ]
                    )
                )

                setup_ready_event_buffer.append(
                    ready_event[
                        primary_direction
                    ]
                )

                setup_start_index_buffer.append(
                    int(
                        primary[
                            "start_index"
                        ]
                    )
                )

                setup_last_event_index_buffer.append(
                    int(
                        primary[
                            "last_event_index"
                        ]
                    )
                )

                setup_fvg_id_buffer.append(
                    int(
                        primary[
                            "latest_fvg_id"
                        ]
                    )
                )

                setup_rejection_fvg_id_buffer.append(
                    int(
                        primary[
                            "rejection_fvg_id"
                        ]
                    )
                )

                setup_bos_scope_buffer.append(
                    str(
                        primary[
                            "bos_scope"
                        ]
                    )
                )

                setup_structure_alignment_buffer.append(
                    self._structure_alignment(
                        direction=(
                            primary_direction
                        ),
                        bias=(
                            structure_bias
                        ),
                    )
                )

                setup_has_sweep_buffer.append(
                    int(
                        primary[
                            "sweep"
                        ]
                    )
                )

                setup_has_displacement_buffer.append(
                    int(
                        primary[
                            "displacement"
                        ]
                    )
                )

                setup_has_bos_buffer.append(
                    int(
                        primary[
                            "bos"
                        ]
                    )
                )

                setup_has_fvg_buffer.append(
                    int(
                        primary[
                            "fvg"
                        ]
                    )
                )

                setup_has_rejection_buffer.append(
                    int(
                        primary[
                            "rejection"
                        ]
                    )
                )

                setup_has_mitigation_buffer.append(
                    int(
                        primary[
                            "mitigation"
                        ]
                    )
                )

        # =====================================================================
        # Assign directional outputs
        # =====================================================================

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

            df[
                f"{prefix}_setup_id"
            ] = buffer[
                "id"
            ]

            df[
                f"{prefix}_setup_state"
            ] = buffer[
                "state"
            ]

            df[
                f"{prefix}_setup_age_bars"
            ] = buffer[
                "age"
            ]

            df[
                f"{prefix}_setup_evidence_count"
            ] = buffer[
                "evidence"
            ]

            df[
                f"{prefix}_setup_ready"
            ] = buffer[
                "ready"
            ]

            df[
                f"{prefix}_setup_ready_event"
            ] = buffer[
                "ready_event"
            ]

            df[
                f"{prefix}_setup_started_event"
            ] = buffer[
                "started_event"
            ]

            df[
                f"{prefix}_setup_expired_event"
            ] = buffer[
                "expired_event"
            ]

            df[
                f"{prefix}_setup_start_index"
            ] = buffer[
                "start_index"
            ]

            df[
                f"{prefix}_setup_last_event_index"
            ] = buffer[
                "last_event_index"
            ]

            df[
                f"{prefix}_setup_fvg_id"
            ] = buffer[
                "fvg_id"
            ]

            df[
                f"{prefix}_setup_rejection_fvg_id"
            ] = buffer[
                "rejection_fvg_id"
            ]

            df[
                f"{prefix}_setup_bos_scope"
            ] = buffer[
                "bos_scope"
            ]

            df[
                f"{prefix}_setup_structure_alignment"
            ] = buffer[
                "structure_alignment"
            ]

            df[
                f"{prefix}_setup_has_sweep"
            ] = buffer[
                "has_sweep"
            ]

            df[
                f"{prefix}_setup_has_displacement"
            ] = buffer[
                "has_displacement"
            ]

            df[
                f"{prefix}_setup_has_bos"
            ] = buffer[
                "has_bos"
            ]

            df[
                f"{prefix}_setup_has_fvg"
            ] = buffer[
                "has_fvg"
            ]

            df[
                f"{prefix}_setup_has_rejection"
            ] = buffer[
                "has_rejection"
            ]

            df[
                f"{prefix}_setup_has_mitigation"
            ] = buffer[
                "has_mitigation"
            ]

        # =====================================================================
        # Assign canonical outputs
        # =====================================================================

        df[
            "setup_id"
        ] = setup_id_buffer

        df[
            "setup_direction"
        ] = setup_direction_buffer

        df[
            "setup_state"
        ] = setup_state_buffer

        df[
            "setup_age_bars"
        ] = setup_age_buffer

        df[
            "setup_evidence_count"
        ] = setup_evidence_buffer

        df[
            "setup_ready"
        ] = setup_ready_buffer

        df[
            "setup_ready_event"
        ] = setup_ready_event_buffer

        df[
            "setup_conflict"
        ] = setup_conflict_buffer

        df[
            "setup_start_index"
        ] = setup_start_index_buffer

        df[
            "setup_last_event_index"
        ] = setup_last_event_index_buffer

        df[
            "setup_fvg_id"
        ] = setup_fvg_id_buffer

        df[
            "setup_rejection_fvg_id"
        ] = (
            setup_rejection_fvg_id_buffer
        )

        df[
            "setup_bos_scope"
        ] = setup_bos_scope_buffer

        df[
            "setup_structure_alignment"
        ] = (
            setup_structure_alignment_buffer
        )

        df[
            "setup_has_sweep"
        ] = setup_has_sweep_buffer

        df[
            "setup_has_displacement"
        ] = (
            setup_has_displacement_buffer
        )

        df[
            "setup_has_bos"
        ] = setup_has_bos_buffer

        df[
            "setup_has_fvg"
        ] = setup_has_fvg_buffer

        df[
            "setup_has_rejection"
        ] = (
            setup_has_rejection_buffer
        )

        df[
            "setup_has_mitigation"
        ] = (
            setup_has_mitigation_buffer
        )

        return df


setup_state_engine = (
    SetupStateEngine()
)