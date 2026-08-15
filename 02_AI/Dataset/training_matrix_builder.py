"""
===============================================================================
Module      : training_matrix_builder.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Causal Multi-Timeframe XAUUSD Training Matrix Builder
===============================================================================

Responsibilities
----------------
- Load immutable canonical historical snapshots.
- Verify dataset SHA256 and exact InstrumentContext identity.
- Generate existing PulseViper causal technical/candle features.
- Align completed higher-timeframe bars without lookahead.
- Generate future-only 3-class training targets:
      LONG / SHORT / NO_TRADE
- Add outcome diagnostics:
      excursion, resolution time, ambiguous barrier events, forward return.
- Produce chronological TRAIN / VALIDATION / TEST partitions.
- Purge horizon overlap around split boundaries.
- Persist an immutable content-addressed training matrix + manifest.

Important
---------
Features never use future bars.

Future bars are used ONLY inside target_* columns.

No MT5 calls.
No broker calls.
No execution authority.
No live authorization.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import math
import os
import tempfile

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import pandas as pd


ROOT_DIR = (
    Path(
        __file__
    )
    .resolve()
    .parents[
        2
    ]
)

CANONICAL_ROOT = (
    ROOT_DIR
    /
    "01_Data"
    /
    "Canonical"
)


feature_generator_module: Any = (
    importlib.import_module(
        "02_AI.Features.feature_generator"
    )
)

feature_list_module: Any = (
    importlib.import_module(
        "02_AI.Features.feature_list"
    )
)

guard_module: Any = (
    importlib.import_module(
        "02_AI.Dataset.instrument_frame_guard"
    )
)


feature_generator: Any = (
    feature_generator_module.feature_generator
)

FEATURE_COLUMNS: tuple[str, ...] = tuple(
    feature_list_module.FEATURE_COLUMNS
)

InstrumentFrameGuard: Any = (
    guard_module.InstrumentFrameGuard
)


TIMEFRAME_MINUTES: dict[
    str,
    int,
] = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}


IDENTITY_COLUMNS: tuple[
    str,
    ...
] = (
    "pv_canonical_symbol",
    "pv_asset_class",
    "pv_broker_id",
    "pv_broker_symbol",
    "pv_account_scope_id",
    "pv_execution_environment",
    "pv_contract_spec_id",
    "pv_data_schema_version",
    "pv_feature_contract_version",
    "pv_instrument_definition_fingerprint",
    "pv_instrument_identity_fingerprint",
)


class TrainingMatrixError(
    RuntimeError
):
    pass


@dataclass(frozen=True)
class HistoricalSnapshot:

    timeframe: str

    dataset_id: str

    dataset_path: Path

    manifest_path: Path

    dataset_sha256: str

    manifest_sha256: str

    row_count: int

    start_time: str

    end_time: str


@dataclass(frozen=True)
class TrainingMatrixResult:

    dataset_id: str

    dataset_path: Path

    manifest_path: Path

    dataset_sha256: str

    manifest_sha256: str

    row_count: int

    feature_count: int

    base_timeframe: str

    class_distribution: dict[
        str,
        int,
    ]

    split_distribution: dict[
        str,
        int,
    ]

    learning_scope_fingerprint: str

    training_contract_version: str

    reused_existing_dataset: bool

    reused_existing_manifest: bool

    live_authorized: bool = False


class TrainingMatrixBuilder:

    VERSION = "1.0"

    TRAINING_CONTRACT_VERSION = (
        "XAUUSD_MTF_TRAINING_V1"
    )

    def __init__(
        self,
        *,
        canonical_root: Path | None = None,
    ) -> None:

        self.canonical_root = (
            Path(
                canonical_root
            )
            if canonical_root
            is not None
            else
            CANONICAL_ROOT
        )

    # =========================================================================
    # Generic helpers
    # =========================================================================

    @staticmethod
    def _sha256_bytes(
        payload: bytes,
    ) -> str:

        return hashlib.sha256(
            payload
        ).hexdigest()

    @staticmethod
    def _sha256_file(
        path: Path,
    ) -> str:

        digest = hashlib.sha256()

        with path.open(
            "rb"
        ) as handle:

            while True:

                chunk = handle.read(
                    1024
                    *
                    1024
                )

                if not chunk:
                    break

                digest.update(
                    chunk
                )

        return digest.hexdigest()

    @classmethod
    def _canonical_json_bytes(
        cls,
        document: Mapping[
            str,
            Any,
        ],
    ) -> bytes:

        return (
            json.dumps(
                document,
                sort_keys=True,
                separators=(
                    ",",
                    ":",
                ),
                ensure_ascii=False,
                allow_nan=False,
            )
            +
            "\n"
        ).encode(
            "utf-8"
        )

    @staticmethod
    def _safe_token(
        value: Any,
        name: str,
    ) -> str:

        raw = str(
            value
        ).strip()

        if (
            not raw
            or
            raw
            in {
                ".",
                "..",
            }
            or
            "/"
            in raw
            or
            "\\"
            in raw
            or
            "\x00"
            in raw
        ):

            raise TrainingMatrixError(
                f"INVALID_{name.upper()}"
            )

        cleaned = "".join(
            character
            for character
            in raw
            if (
                character.isalnum()
                or
                character
                in {
                    "_",
                    "-",
                    ".",
                }
            )
        )

        if not cleaned:

            raise TrainingMatrixError(
                f"INVALID_{name.upper()}"
            )

        return cleaned

    @staticmethod
    def _context_document(
        context: Any,
    ) -> dict[
        str,
        Any
    ]:

        if context is None:

            raise TrainingMatrixError(
                "INSTRUMENT_CONTEXT_REQUIRED"
            )

        if bool(
            getattr(
                context,
                "live_authorized",
                False,
            )
        ):

            raise TrainingMatrixError(
                "LIVE_AUTHORIZED_CONTEXT_REJECTED"
            )

        method = getattr(
            context,
            "identity_document",
            None,
        )

        if not callable(
            method
        ):

            raise TrainingMatrixError(
                "INVALID_INSTRUMENT_CONTEXT"
            )

        document = method()

        if not isinstance(
            document,
            Mapping,
        ):

            raise TrainingMatrixError(
                "INVALID_CONTEXT_IDENTITY_DOCUMENT"
            )

        return dict(
            document
        )

    # =========================================================================
    # Learning scope
    # =========================================================================

    @classmethod
    def learning_scope_document(
        cls,
        context: Any,
    ) -> dict[
        str,
        Any
    ]:

        context_document = (
            cls._context_document(
                context
            )
        )

        return {
            "canonical_symbol": str(
                context_document[
                    "canonical_symbol"
                ]
            ),
            "asset_class": str(
                context_document[
                    "asset_class"
                ]
            ),
            "broker_id": str(
                context_document[
                    "broker_id"
                ]
            ),
            "broker_symbol": str(
                context_document[
                    "broker_symbol"
                ]
            ),
            "contract_spec_id": str(
                context_document[
                    "contract_spec_id"
                ]
            ),
            "data_schema_version": str(
                context_document[
                    "data_schema_version"
                ]
            ),
            "feature_contract_version": str(
                context_document[
                    "feature_contract_version"
                ]
            ),
            "definition_version": str(
                context_document[
                    "definition_version"
                ]
            ),
            "definition_fingerprint": str(
                context_document[
                    "definition_fingerprint"
                ]
            ),
        }

    @classmethod
    def learning_scope_fingerprint(
        cls,
        context: Any,
    ) -> str:

        payload = (
            cls._canonical_json_bytes(
                cls.learning_scope_document(
                    context
                )
            )
        )

        return cls._sha256_bytes(
            payload
        )

    # =========================================================================
    # Historical snapshot discovery
    # =========================================================================

    def _historical_directory(
        self,
        *,
        context: Any,
        timeframe: str,
    ) -> Path:

        canonical_symbol = (
            self._safe_token(
                context.canonical_symbol,
                "canonical_symbol",
            )
        )

        identity_fingerprint = str(
            context.identity_fingerprint
        ).strip()

        if not identity_fingerprint:

            raise TrainingMatrixError(
                "CONTEXT_IDENTITY_FINGERPRINT_MISSING"
            )

        return (
            self.canonical_root
            /
            "Instruments"
            /
            canonical_symbol
            /
            "execution"
            /
            (
                "scope_"
                +
                identity_fingerprint
            )
            /
            "historical"
            /
            timeframe
        )

    def _select_historical_snapshot(
        self,
        *,
        context: Any,
        timeframe: str,
    ) -> HistoricalSnapshot:

        directory = (
            self._historical_directory(
                context=context,
                timeframe=timeframe,
            )
        )

        if not directory.is_dir():

            raise TrainingMatrixError(
                (
                    "HISTORICAL_TIMEFRAME_DIRECTORY_MISSING: "
                    f"{timeframe}"
                )
            )

        manifest_paths = sorted(
            directory.glob(
                "*.manifest.json"
            )
        )

        if not manifest_paths:

            raise TrainingMatrixError(
                (
                    "HISTORICAL_MANIFEST_MISSING: "
                    f"{timeframe}"
                )
            )

        expected_context_fingerprint = str(
            context.identity_fingerprint
        )

        candidates: list[
            tuple[
                pd.Timestamp,
                int,
                str,
                Path,
                dict[
                    str,
                    Any,
                ],
            ]
        ] = []

        for manifest_path in manifest_paths:

            try:

                raw_bytes = (
                    manifest_path.read_bytes()
                )

                manifest = json.loads(
                    raw_bytes.decode(
                        "utf-8"
                    )
                )

            except Exception as exc:

                raise TrainingMatrixError(
                    (
                        "INVALID_HISTORICAL_MANIFEST: "
                        f"{manifest_path}"
                    )
                ) from exc

            if (
                str(
                    manifest.get(
                        "context_identity_fingerprint",
                        "",
                    )
                )
                !=
                expected_context_fingerprint
            ):

                continue

            if (
                str(
                    manifest.get(
                        "timeframe",
                        "",
                    )
                ).upper()
                !=
                timeframe
            ):

                continue

            try:

                end_time = pd.to_datetime(
                    manifest[
                        "end_time"
                    ],
                    utc=True,
                    errors="raise",
                )

                row_count = int(
                    manifest[
                        "row_count"
                    ]
                )

            except Exception as exc:

                raise TrainingMatrixError(
                    (
                        "INVALID_HISTORICAL_MANIFEST_METADATA: "
                        f"{manifest_path}"
                    )
                ) from exc

            candidates.append(
                (
                    end_time,
                    row_count,
                    str(
                        manifest.get(
                            "dataset_id",
                            "",
                        )
                    ),
                    manifest_path,
                    manifest,
                )
            )

        if not candidates:

            raise TrainingMatrixError(
                (
                    "NO_MATCHING_CONTEXT_MANIFEST: "
                    f"{timeframe}"
                )
            )

        candidates.sort(
            key=lambda item: (
                item[
                    0
                ],
                item[
                    1
                ],
                item[
                    2
                ],
            )
        )

        (
            _end_timestamp,
            row_count,
            dataset_id,
            manifest_path,
            manifest,
        ) = candidates[
            -1
        ]

        dataset_filename = str(
            manifest.get(
                "dataset_filename",
                "",
            )
        ).strip()

        if not dataset_filename:

            raise TrainingMatrixError(
                "HISTORICAL_DATASET_FILENAME_MISSING"
            )

        dataset_path = (
            manifest_path.parent
            /
            dataset_filename
        )

        if not dataset_path.is_file():

            raise TrainingMatrixError(
                (
                    "HISTORICAL_DATASET_MISSING: "
                    f"{dataset_path}"
                )
            )

        expected_dataset_hash = str(
            manifest.get(
                "dataset_sha256",
                "",
            )
        ).strip()

        actual_dataset_hash = (
            self._sha256_file(
                dataset_path
            )
        )

        if (
            not expected_dataset_hash
            or
            actual_dataset_hash
            !=
            expected_dataset_hash
        ):

            raise TrainingMatrixError(
                (
                    "HISTORICAL_DATASET_HASH_MISMATCH: "
                    f"{timeframe}"
                )
            )

        manifest_hash = (
            self._sha256_file(
                manifest_path
            )
        )

        return HistoricalSnapshot(
            timeframe=timeframe,
            dataset_id=dataset_id,
            dataset_path=dataset_path,
            manifest_path=(
                manifest_path
            ),
            dataset_sha256=(
                actual_dataset_hash
            ),
            manifest_sha256=(
                manifest_hash
            ),
            row_count=row_count,
            start_time=str(
                manifest.get(
                    "start_time",
                    "",
                )
            ),
            end_time=str(
                manifest.get(
                    "end_time",
                    "",
                )
            ),
        )

    # =========================================================================
    # Historical frame loading
    # =========================================================================

    def _load_snapshot_frame(
        self,
        *,
        context: Any,
        snapshot: HistoricalSnapshot,
    ) -> pd.DataFrame:

        frame = pd.read_csv(
            snapshot.dataset_path
        )

        if frame.empty:

            raise TrainingMatrixError(
                (
                    "EMPTY_HISTORICAL_DATASET: "
                    f"{snapshot.timeframe}"
                )
            )

        if (
            len(
                frame
            )
            !=
            snapshot.row_count
        ):

            raise TrainingMatrixError(
                (
                    "HISTORICAL_ROW_COUNT_MISMATCH: "
                    f"{snapshot.timeframe}"
                )
            )

        if (
            "time"
            not in frame.columns
        ):

            raise TrainingMatrixError(
                "HISTORICAL_TIME_COLUMN_MISSING"
            )

        frame[
            "time"
        ] = pd.to_datetime(
            frame[
                "time"
            ],
            utc=True,
            errors="raise",
        )

        if bool(
            frame[
                "time"
            ].duplicated().any()
        ):

            raise TrainingMatrixError(
                (
                    "DUPLICATE_HISTORICAL_TIMESTAMPS: "
                    f"{snapshot.timeframe}"
                )
            )

        if not frame[
            "time"
        ].is_monotonic_increasing:

            raise TrainingMatrixError(
                (
                    "UNSORTED_HISTORICAL_TIMESTAMPS: "
                    f"{snapshot.timeframe}"
                )
            )

        guard = InstrumentFrameGuard(
            context
        )

        try:

            guard.validate(
                frame,
                require_nonempty=True,
            )

        except Exception as exc:

            raise TrainingMatrixError(
                (
                    "HISTORICAL_CONTEXT_VALIDATION_FAILED: "
                    f"{snapshot.timeframe}: {exc}"
                )
            ) from exc

        missing_identity = [
            column
            for column
            in IDENTITY_COLUMNS
            if column
            not in frame.columns
        ]

        if missing_identity:

            raise TrainingMatrixError(
                (
                    "HISTORICAL_IDENTITY_COLUMNS_MISSING: "
                    +
                    ", ".join(
                        missing_identity
                    )
                )
            )

        return frame

    # =========================================================================
    # Causal feature generation
    # =========================================================================

    @staticmethod
    def _feature_prefix(
        timeframe: str,
    ) -> str:

        return timeframe.lower()

    def _generate_feature_frame(
        self,
        *,
        frame: pd.DataFrame,
        timeframe: str,
    ) -> pd.DataFrame:

        if timeframe not in TIMEFRAME_MINUTES:

            raise TrainingMatrixError(
                (
                    "UNSUPPORTED_TIMEFRAME: "
                    f"{timeframe}"
                )
            )

        try:

            generated = (
                feature_generator.generate(
                    frame
                )
            )

        except Exception as exc:

            raise TrainingMatrixError(
                (
                    "FEATURE_GENERATION_FAILED: "
                    f"{timeframe}: {exc}"
                )
            ) from exc

        missing_features = [
            feature
            for feature
            in FEATURE_COLUMNS
            if feature
            not in generated.columns
        ]

        if missing_features:

            raise TrainingMatrixError(
                (
                    "FEATURE_COLUMNS_MISSING: "
                    f"{timeframe}: "
                    +
                    ", ".join(
                        missing_features
                    )
                )
            )

        prefix = (
            self._feature_prefix(
                timeframe
            )
        )

        result = pd.DataFrame(
            {
                "time": generated[
                    "time"
                ],
            }
        )

        result[
            "available_time"
        ] = (
            generated[
                "time"
            ]
            +
            pd.to_timedelta(
                TIMEFRAME_MINUTES[
                    timeframe
                ],
                unit="m",
            )
        )

        for feature in FEATURE_COLUMNS:

            result[
                f"{prefix}_{feature}"
            ] = pd.to_numeric(
                generated[
                    feature
                ],
                errors="coerce",
            ).astype(
                "float32"
            )

        feature_names = [
            f"{prefix}_{feature}"
            for feature
            in FEATURE_COLUMNS
        ]

        result[
            feature_names
        ] = result[
            feature_names
        ].replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )

        result = (
            result.dropna(
                subset=feature_names
            )
            .reset_index(
                drop=True
            )
        )

        if result.empty:

            raise TrainingMatrixError(
                (
                    "NO_VALID_FEATURE_ROWS: "
                    f"{timeframe}"
                )
            )

        if bool(
            result[
                "available_time"
            ].duplicated().any()
        ):

            raise TrainingMatrixError(
                (
                    "DUPLICATE_FEATURE_AVAILABILITY_TIME: "
                    f"{timeframe}"
                )
            )

        return result

    # =========================================================================
    # Target generation
    # =========================================================================

    @staticmethod
    def _build_targets(
        *,
        raw_frame: pd.DataFrame,
        featured_frame: pd.DataFrame,
        horizon_bars: int,
        barrier_atr: float,
    ) -> pd.DataFrame:

        if (
            isinstance(
                horizon_bars,
                bool,
            )
            or
            not isinstance(
                horizon_bars,
                int,
            )
            or
            horizon_bars
            <=
            0
        ):

            raise TrainingMatrixError(
                "INVALID_TARGET_HORIZON"
            )

        if (
            not math.isfinite(
                float(
                    barrier_atr
                )
            )
            or
            float(
                barrier_atr
            )
            <=
            0.0
        ):

            raise TrainingMatrixError(
                "INVALID_TARGET_BARRIER_ATR"
            )

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
                raw_frame.columns
            )
        )

        if missing:

            raise TrainingMatrixError(
                (
                    "TARGET_SOURCE_COLUMNS_MISSING: "
                    +
                    ", ".join(
                        sorted(
                            missing
                        )
                    )
                )
            )

        if (
            "atr14"
            not in featured_frame.columns
        ):

            raise TrainingMatrixError(
                "TARGET_ATR14_MISSING"
            )

        n = len(
            raw_frame
        )

        high = pd.to_numeric(
            raw_frame[
                "high"
            ],
            errors="coerce",
        ).to_numpy(
            dtype=float
        )

        low = pd.to_numeric(
            raw_frame[
                "low"
            ],
            errors="coerce",
        ).to_numpy(
            dtype=float
        )

        close = pd.to_numeric(
            raw_frame[
                "close"
            ],
            errors="coerce",
        ).to_numpy(
            dtype=float
        )

        atr = pd.to_numeric(
            featured_frame[
                "atr14"
            ],
            errors="coerce",
        ).to_numpy(
            dtype=float
        )

        target_class: list[
            str
            |
            None
        ] = [
            None
        ] * n

        target_class_id = np.full(
            n,
            np.nan,
            dtype=float,
        )

        target_resolved = np.full(
            n,
            np.nan,
            dtype=float,
        )

        target_ambiguous = np.full(
            n,
            np.nan,
            dtype=float,
        )

        target_resolution_bars = np.full(
            n,
            np.nan,
            dtype=float,
        )

        target_entry_close = np.full(
            n,
            np.nan,
            dtype=float,
        )

        target_upper_barrier = np.full(
            n,
            np.nan,
            dtype=float,
        )

        target_lower_barrier = np.full(
            n,
            np.nan,
            dtype=float,
        )

        target_up_excursion_atr = np.full(
            n,
            np.nan,
            dtype=float,
        )

        target_down_excursion_atr = np.full(
            n,
            np.nan,
            dtype=float,
        )

        target_forward_return_atr = np.full(
            n,
            np.nan,
            dtype=float,
        )

        target_reason: list[
            str
            |
            None
        ] = [
            None
        ] * n

        multiplier = float(
            barrier_atr
        )

        for index in range(
            0,
            n
            -
            horizon_bars,
        ):

            entry = close[
                index
            ]

            current_atr = atr[
                index
            ]

            if (
                not math.isfinite(
                    entry
                )
                or
                not math.isfinite(
                    current_atr
                )
                or
                current_atr
                <=
                0.0
            ):

                continue

            future_slice = slice(
                index
                +
                1,
                index
                +
                horizon_bars
                +
                1,
            )

            future_high = high[
                future_slice
            ]

            future_low = low[
                future_slice
            ]

            future_close = close[
                future_slice
            ]

            if (
                len(
                    future_high
                )
                !=
                horizon_bars
            ):

                continue

            if (
                not np.isfinite(
                    future_high
                ).all()
                or
                not np.isfinite(
                    future_low
                ).all()
                or
                not np.isfinite(
                    future_close
                ).all()
            ):

                continue

            upper = (
                entry
                +
                (
                    multiplier
                    *
                    current_atr
                )
            )

            lower = (
                entry
                -
                (
                    multiplier
                    *
                    current_atr
                )
            )

            upper_hits = np.flatnonzero(
                future_high
                >=
                upper
            )

            lower_hits = np.flatnonzero(
                future_low
                <=
                lower
            )

            first_upper = (
                int(
                    upper_hits[
                        0
                    ]
                )
                +
                1
                if len(
                    upper_hits
                )
                else
                None
            )

            first_lower = (
                int(
                    lower_hits[
                        0
                    ]
                )
                +
                1
                if len(
                    lower_hits
                )
                else
                None
            )

            ambiguous = False
            resolved = False

            if (
                first_upper
                is not None
                and
                first_lower
                is not None
                and
                first_upper
                ==
                first_lower
            ):

                label = (
                    "NO_TRADE"
                )

                class_id = 0

                reason = (
                    "AMBIGUOUS_SAME_BAR"
                )

                resolution = (
                    first_upper
                )

                ambiguous = True
                resolved = True

            elif (
                first_upper
                is not None
                and
                (
                    first_lower
                    is None
                    or
                    first_upper
                    <
                    first_lower
                )
            ):

                label = "LONG"

                class_id = 1

                reason = (
                    "UPPER_BARRIER_FIRST"
                )

                resolution = (
                    first_upper
                )

                resolved = True

            elif (
                first_lower
                is not None
            ):

                label = "SHORT"

                class_id = -1

                reason = (
                    "LOWER_BARRIER_FIRST"
                )

                resolution = (
                    first_lower
                )

                resolved = True

            else:

                label = (
                    "NO_TRADE"
                )

                class_id = 0

                reason = (
                    "UNRESOLVED_WITHIN_HORIZON"
                )

                resolution = (
                    horizon_bars
                )

            target_class[
                index
            ] = label

            target_class_id[
                index
            ] = class_id

            target_resolved[
                index
            ] = int(
                resolved
            )

            target_ambiguous[
                index
            ] = int(
                ambiguous
            )

            target_resolution_bars[
                index
            ] = resolution

            target_entry_close[
                index
            ] = entry

            target_upper_barrier[
                index
            ] = upper

            target_lower_barrier[
                index
            ] = lower

            target_up_excursion_atr[
                index
            ] = (
                float(
                    np.max(
                        future_high
                    )
                )
                -
                entry
            ) / current_atr

            target_down_excursion_atr[
                index
            ] = (
                entry
                -
                float(
                    np.min(
                        future_low
                    )
                )
            ) / current_atr

            target_forward_return_atr[
                index
            ] = (
                float(
                    future_close[
                        -1
                    ]
                )
                -
                entry
            ) / current_atr

            target_reason[
                index
            ] = reason

        return pd.DataFrame(
            {
                "time": raw_frame[
                    "time"
                ],
                "target_class": (
                    target_class
                ),
                "target_class_id": (
                    target_class_id
                ),
                "target_resolved": (
                    target_resolved
                ),
                "target_ambiguous": (
                    target_ambiguous
                ),
                "target_resolution_bars": (
                    target_resolution_bars
                ),
                "target_entry_close": (
                    target_entry_close
                ),
                "target_upper_barrier": (
                    target_upper_barrier
                ),
                "target_lower_barrier": (
                    target_lower_barrier
                ),
                "target_up_excursion_atr": (
                    target_up_excursion_atr
                ),
                "target_down_excursion_atr": (
                    target_down_excursion_atr
                ),
                "target_forward_return_atr": (
                    target_forward_return_atr
                ),
                "target_reason": (
                    target_reason
                ),
            }
        )

    # =========================================================================
    # Dataset split
    # =========================================================================

    @staticmethod
    def _assign_chronological_splits(
        *,
        frame: pd.DataFrame,
        horizon_bars: int,
        train_fraction: float,
        validation_fraction: float,
    ) -> pd.DataFrame:

        if (
            train_fraction
            <=
            0.0
            or
            validation_fraction
            <=
            0.0
            or
            train_fraction
            +
            validation_fraction
            >=
            1.0
        ):

            raise TrainingMatrixError(
                "INVALID_SPLIT_FRACTIONS"
            )

        data = frame.reset_index(
            drop=True
        ).copy()

        n = len(
            data
        )

        if n < (
            horizon_bars
            *
            10
        ):

            raise TrainingMatrixError(
                "TRAINING_DATASET_TOO_SMALL"
            )

        train_boundary = int(
            n
            *
            train_fraction
        )

        validation_boundary = int(
            n
            *
            (
                train_fraction
                +
                validation_fraction
            )
        )

        train_safe_end = (
            train_boundary
            -
            horizon_bars
        )

        validation_safe_end = (
            validation_boundary
            -
            horizon_bars
        )

        if (
            train_safe_end
            <=
            0
            or
            validation_safe_end
            <=
            train_boundary
            or
            validation_boundary
            >=
            n
        ):

            raise TrainingMatrixError(
                "INVALID_PURGED_SPLIT_BOUNDARIES"
            )

        split = np.full(
            n,
            "PURGED",
            dtype=object,
        )

        split[
            0:
            train_safe_end
        ] = "TRAIN"

        split[
            train_boundary:
            validation_safe_end
        ] = "VALIDATION"

        split[
            validation_boundary:
            n
        ] = "TEST"

        data[
            "dataset_split"
        ] = split

        data = (
            data[
                data[
                    "dataset_split"
                ]
                !=
                "PURGED"
            ]
            .reset_index(
                drop=True
            )
        )

        required = {
            "TRAIN",
            "VALIDATION",
            "TEST",
        }

        actual = set(
            data[
                "dataset_split"
            ].unique()
        )

        if actual != required:

            raise TrainingMatrixError(
                "MISSING_REQUIRED_DATASET_SPLIT"
            )

        return data

    # =========================================================================
    # Atomic immutable output
    # =========================================================================

    def _write_dataframe_content_addressed(
        self,
        *,
        frame: pd.DataFrame,
        output_directory: Path,
        filename_prefix: str,
    ) -> tuple[
        Path,
        str,
        bool,
    ]:

        output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_path: Path | None = None

        try:

            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                suffix=".tmp.csv",
                prefix="pv_training_",
                dir=output_directory,
                delete=False,
            ) as handle:

                temporary_path = Path(
                    handle.name
                )

                frame.to_csv(
                    handle,
                    index=False,
                    lineterminator="\n",
                    date_format=(
                        "%Y-%m-%dT%H:%M:%S.%fZ"
                    ),
                    float_format="%.10g",
                )

                handle.flush()

                os.fsync(
                    handle.fileno()
                )

            dataset_hash = (
                self._sha256_file(
                    temporary_path
                )
            )

            final_path = (
                output_directory
                /
                (
                    filename_prefix
                    +
                    "_"
                    +
                    dataset_hash[
                        :16
                    ]
                    +
                    ".csv"
                )
            )

            if final_path.exists():

                existing_hash = (
                    self._sha256_file(
                        final_path
                    )
                )

                if (
                    existing_hash
                    !=
                    dataset_hash
                ):

                    raise TrainingMatrixError(
                        "TRAINING_DATASET_IMMUTABLE_COLLISION"
                    )

                temporary_path.unlink(
                    missing_ok=True
                )

                return (
                    final_path,
                    dataset_hash,
                    True,
                )

            os.replace(
                temporary_path,
                final_path,
            )

            temporary_path = None

            return (
                final_path,
                dataset_hash,
                False,
            )

        finally:

            if (
                temporary_path
                is not None
            ):

                try:

                    temporary_path.unlink(
                        missing_ok=True
                    )

                except Exception:

                    pass

    @staticmethod
    def _write_immutable_bytes(
        *,
        path: Path,
        payload: bytes,
    ) -> bool:

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if path.exists():

            if (
                path.read_bytes()
                !=
                payload
            ):

                raise TrainingMatrixError(
                    "TRAINING_MANIFEST_IMMUTABLE_COLLISION"
                )

            return True

        try:

            with path.open(
                "xb"
            ) as handle:

                handle.write(
                    payload
                )

                handle.flush()

                os.fsync(
                    handle.fileno()
                )

        except FileExistsError:

            if (
                path.read_bytes()
                !=
                payload
            ):

                raise TrainingMatrixError(
                    "TRAINING_MANIFEST_IMMUTABLE_COLLISION"
                )

            return True

        return False

    # =========================================================================
    # Public build
    # =========================================================================

    def build(
        self,
        *,
        context: Any,
        base_timeframe: str = "M5",
        context_timeframes: Sequence[
            str
        ] = (
            "M15",
            "M30",
            "H1",
            "H4",
            "D1",
        ),
        horizon_bars: int = 12,
        barrier_atr: float = 1.0,
        train_fraction: float = 0.70,
        validation_fraction: float = 0.15,
    ) -> TrainingMatrixResult:

        self._context_document(
            context
        )

        base_tf = str(
            base_timeframe
        ).strip().upper()

        if base_tf not in TIMEFRAME_MINUTES:

            raise TrainingMatrixError(
                "UNSUPPORTED_BASE_TIMEFRAME"
            )

        resolved_context_timeframes: list[
            str
        ] = []

        seen = {
            base_tf
        }

        for raw in context_timeframes:

            timeframe = str(
                raw
            ).strip().upper()

            if timeframe not in TIMEFRAME_MINUTES:

                raise TrainingMatrixError(
                    (
                        "UNSUPPORTED_CONTEXT_TIMEFRAME: "
                        f"{timeframe}"
                    )
                )

            if timeframe in seen:
                continue

            resolved_context_timeframes.append(
                timeframe
            )

            seen.add(
                timeframe
            )

        if not resolved_context_timeframes:

            raise TrainingMatrixError(
                "CONTEXT_TIMEFRAMES_REQUIRED"
            )

        all_timeframes = (
            base_tf,
            *
            resolved_context_timeframes,
        )

        snapshots: dict[
            str,
            HistoricalSnapshot,
        ] = {}

        frames: dict[
            str,
            pd.DataFrame,
        ] = {}

        for timeframe in all_timeframes:

            snapshot = (
                self._select_historical_snapshot(
                    context=context,
                    timeframe=timeframe,
                )
            )

            snapshots[
                timeframe
            ] = snapshot

            frames[
                timeframe
            ] = (
                self._load_snapshot_frame(
                    context=context,
                    snapshot=snapshot,
                )
            )

        base_raw = frames[
            base_tf
        ]

        base_generated_full = (
            feature_generator.generate(
                base_raw
            )
        )

        targets = (
            self._build_targets(
                raw_frame=base_raw,
                featured_frame=(
                    base_generated_full
                ),
                horizon_bars=(
                    horizon_bars
                ),
                barrier_atr=(
                    barrier_atr
                ),
            )
        )

        base_features = (
            self._generate_feature_frame(
                frame=base_raw,
                timeframe=base_tf,
            )
        )

        base_prefix = (
            self._feature_prefix(
                base_tf
            )
        )

        base_features = (
            base_features.rename(
                columns={
                    "available_time": (
                        "decision_time"
                    ),
                }
            )
        )

        raw_auxiliary = (
            base_raw[
                [
                    "time",
                    "spread",
                    "tick_volume",
                ]
            ]
            .copy()
        )

        raw_auxiliary[
            "spread"
        ] = pd.to_numeric(
            raw_auxiliary[
                "spread"
            ],
            errors="coerce",
        )

        raw_auxiliary[
            "tick_volume"
        ] = pd.to_numeric(
            raw_auxiliary[
                "tick_volume"
            ],
            errors="coerce",
        )

        raw_auxiliary[
            f"{base_prefix}_spread_points"
        ] = raw_auxiliary[
            "spread"
        ].astype(
            "float32"
        )

        volume = raw_auxiliary[
            "tick_volume"
        ].clip(
            lower=0
        )

        raw_auxiliary[
            f"{base_prefix}_tick_volume_log1p"
        ] = np.log1p(
            volume
        ).astype(
            "float32"
        )

        rolling_volume = (
            volume
            .rolling(
                20
            )
            .mean()
        )

        raw_auxiliary[
            f"{base_prefix}_tick_volume_ratio20"
        ] = (
            volume
            /
            rolling_volume.replace(
                0,
                np.nan,
            )
        ).astype(
            "float32"
        )

        raw_auxiliary = (
            raw_auxiliary.drop(
                columns=[
                    "spread",
                    "tick_volume",
                ]
            )
        )

        matrix = (
            base_features.merge(
                raw_auxiliary,
                on="time",
                how="left",
                validate=(
                    "one_to_one"
                ),
            )
        )

        feature_columns: list[
            str
        ] = [
            f"{base_prefix}_{feature}"
            for feature
            in FEATURE_COLUMNS
        ]

        feature_columns.extend(
            [
                f"{base_prefix}_spread_points",
                f"{base_prefix}_tick_volume_log1p",
                f"{base_prefix}_tick_volume_ratio20",
            ]
        )

        # =====================================================================
        # Completed HTF context
        #
        # Historical timestamp represents bar OPEN.
        # A timeframe's features become available only after its bar CLOSE.
        # =====================================================================

        matrix = matrix.sort_values(
            "decision_time"
        ).reset_index(
            drop=True
        )

        for timeframe in resolved_context_timeframes:

            prefix = (
                self._feature_prefix(
                    timeframe
                )
            )

            right = (
                self._generate_feature_frame(
                    frame=frames[
                        timeframe
                    ],
                    timeframe=(
                        timeframe
                    ),
                )
            )

            available_column = (
                f"__{prefix}_available_time"
            )

            right = right.rename(
                columns={
                    "available_time": (
                        available_column
                    ),
                }
            )

            right = right.drop(
                columns=[
                    "time",
                ]
            )

            right = right.sort_values(
                available_column
            ).reset_index(
                drop=True
            )

            matrix = pd.merge_asof(
                matrix,
                right,
                left_on=(
                    "decision_time"
                ),
                right_on=(
                    available_column
                ),
                direction="backward",
                allow_exact_matches=True,
            )

            age_column = (
                f"{prefix}_age_minutes"
            )

            matrix[
                age_column
            ] = (
                (
                    matrix[
                        "decision_time"
                    ]
                    -
                    matrix[
                        available_column
                    ]
                )
                .dt.total_seconds()
                /
                60.0
            ).astype(
                "float32"
            )

            if bool(
                (
                    matrix[
                        age_column
                    ]
                    <
                    0
                ).fillna(
                    False
                ).any()
            ):

                raise TrainingMatrixError(
                    (
                        "FUTURE_TIMEFRAME_FEATURE_LEAKAGE: "
                        f"{timeframe}"
                    )
                )

            matrix = matrix.drop(
                columns=[
                    available_column
                ]
            )

            feature_columns.extend(
                [
                    f"{prefix}_{feature}"
                    for feature
                    in FEATURE_COLUMNS
                ]
            )

            feature_columns.append(
                age_column
            )

        # =====================================================================
        # UTC cyclical time context
        # =====================================================================

        decision_time = (
            matrix[
                "decision_time"
            ]
        )

        hour_value = (
            decision_time.dt.hour
            +
            (
                decision_time.dt.minute
                /
                60.0
            )
        )

        day_value = (
            decision_time.dt.dayofweek
            .astype(
                float
            )
        )

        matrix[
            "utc_hour_sin"
        ] = np.sin(
            2.0
            *
            np.pi
            *
            hour_value
            /
            24.0
        ).astype(
            "float32"
        )

        matrix[
            "utc_hour_cos"
        ] = np.cos(
            2.0
            *
            np.pi
            *
            hour_value
            /
            24.0
        ).astype(
            "float32"
        )

        matrix[
            "utc_day_sin"
        ] = np.sin(
            2.0
            *
            np.pi
            *
            day_value
            /
            7.0
        ).astype(
            "float32"
        )

        matrix[
            "utc_day_cos"
        ] = np.cos(
            2.0
            *
            np.pi
            *
            day_value
            /
            7.0
        ).astype(
            "float32"
        )

        feature_columns.extend(
            [
                "utc_hour_sin",
                "utc_hour_cos",
                "utc_day_sin",
                "utc_day_cos",
            ]
        )

        # =====================================================================
        # Attach future-only targets
        # =====================================================================

        matrix = matrix.merge(
            targets,
            on="time",
            how="left",
            validate="one_to_one",
        )

        target_columns = [
            "target_class",
            "target_class_id",
            "target_resolved",
            "target_ambiguous",
            "target_resolution_bars",
            "target_entry_close",
            "target_upper_barrier",
            "target_lower_barrier",
            "target_up_excursion_atr",
            "target_down_excursion_atr",
            "target_forward_return_atr",
            "target_reason",
        ]

        # =====================================================================
        # Sanitize / drop warmup and unresolved-tail NaNs
        # =====================================================================

        matrix[
            feature_columns
        ] = matrix[
            feature_columns
        ].replace(
            [
                np.inf,
                -np.inf,
            ],
            np.nan,
        )

        required_non_null = (
            feature_columns
            +
            target_columns
        )

        matrix = (
            matrix.dropna(
                subset=(
                    required_non_null
                )
            )
            .sort_values(
                "decision_time"
            )
            .reset_index(
                drop=True
            )
        )

        if matrix.empty:

            raise TrainingMatrixError(
                "TRAINING_MATRIX_EMPTY"
            )

        if bool(
            matrix[
                "decision_time"
            ].duplicated().any()
        ):

            raise TrainingMatrixError(
                "DUPLICATE_TRAINING_DECISION_TIME"
            )

        if not matrix[
            "decision_time"
        ].is_monotonic_increasing:

            raise TrainingMatrixError(
                "UNSORTED_TRAINING_DECISION_TIME"
            )

        for feature in feature_columns:

            matrix[
                feature
            ] = pd.to_numeric(
                matrix[
                    feature
                ],
                errors="raise",
            ).astype(
                "float32"
            )

        matrix[
            "target_class_id"
        ] = matrix[
            "target_class_id"
        ].astype(
            "int8"
        )

        matrix[
            "target_resolved"
        ] = matrix[
            "target_resolved"
        ].astype(
            "int8"
        )

        matrix[
            "target_ambiguous"
        ] = matrix[
            "target_ambiguous"
        ].astype(
            "int8"
        )

        matrix[
            "target_resolution_bars"
        ] = matrix[
            "target_resolution_bars"
        ].astype(
            "int16"
        )

        required_classes = {
            "LONG",
            "SHORT",
            "NO_TRADE",
        }

        actual_classes = set(
            matrix[
                "target_class"
            ].unique()
        )

        if actual_classes != required_classes:

            raise TrainingMatrixError(
                (
                    "REQUIRED_TARGET_CLASSES_MISSING: "
                    f"{sorted(actual_classes)}"
                )
            )

        # =====================================================================
        # Purged chronological split
        # =====================================================================

        matrix = (
            self._assign_chronological_splits(
                frame=matrix,
                horizon_bars=(
                    horizon_bars
                ),
                train_fraction=(
                    train_fraction
                ),
                validation_fraction=(
                    validation_fraction
                ),
            )
        )

        # =====================================================================
        # Preserve exact instrument identity
        # =====================================================================

        identity_values = {}

        for column in IDENTITY_COLUMNS:

            if column not in base_raw.columns:

                raise TrainingMatrixError(
                    (
                        "BASE_IDENTITY_COLUMN_MISSING: "
                        f"{column}"
                    )
                )

            values = (
                base_raw[
                    column
                ]
                .drop_duplicates()
            )

            if len(
                values
            ) != 1:

                raise TrainingMatrixError(
                    (
                        "MIXED_BASE_IDENTITY: "
                        f"{column}"
                    )
                )

            identity_values[
                column
            ] = values.iloc[
                0
            ]

        for (
            column,
            value,
        ) in identity_values.items():

            matrix[
                column
            ] = value

        # =====================================================================
        # Final column order
        # =====================================================================

        final_columns = (
            [
                "time",
                "decision_time",
            ]
            +
            list(
                IDENTITY_COLUMNS
            )
            +
            feature_columns
            +
            target_columns
            +
            [
                "dataset_split",
            ]
        )

        matrix = matrix[
            final_columns
        ]

        # =====================================================================
        # Learning namespace
        # =====================================================================

        learning_document = (
            self.learning_scope_document(
                context
            )
        )

        learning_fingerprint = (
            self.learning_scope_fingerprint(
                context
            )
        )

        canonical_symbol = (
            self._safe_token(
                context.canonical_symbol,
                "canonical_symbol",
            )
        )

        safe_contract = (
            self._safe_token(
                self.TRAINING_CONTRACT_VERSION,
                "training_contract",
            )
        )

        output_directory = (
            self.canonical_root
            /
            "Instruments"
            /
            canonical_symbol
            /
            "learning"
            /
            (
                "scope_"
                +
                learning_fingerprint
            )
            /
            "training"
            /
            safe_contract
        )

        prefix = (
            f"{canonical_symbol}_"
            f"{base_tf}_"
            f"{safe_contract}"
        )

        (
            dataset_path,
            dataset_hash,
            dataset_reused,
        ) = (
            self._write_dataframe_content_addressed(
                frame=matrix,
                output_directory=(
                    output_directory
                ),
                filename_prefix=(
                    prefix
                ),
            )
        )

        dataset_id = (
            "train_"
            +
            dataset_hash[
                :24
            ]
        )

        class_distribution = {
            str(
                key
            ): int(
                value
            )
            for (
                key,
                value,
            )
            in matrix[
                "target_class"
            ].value_counts().items()
        }

        split_distribution = {
            str(
                key
            ): int(
                value
            )
            for (
                key,
                value,
            )
            in matrix[
                "dataset_split"
            ].value_counts().items()
        }

        source_snapshots = {
            timeframe: {
                "dataset_id": (
                    snapshot.dataset_id
                ),
                "dataset_sha256": (
                    snapshot.dataset_sha256
                ),
                "manifest_sha256": (
                    snapshot.manifest_sha256
                ),
                "row_count": (
                    snapshot.row_count
                ),
                "start_time": (
                    snapshot.start_time
                ),
                "end_time": (
                    snapshot.end_time
                ),
            }
            for (
                timeframe,
                snapshot,
            )
            in snapshots.items()
        }

        manifest = {
            "manifest_version": (
                "PULSEVIPER_TRAINING_MATRIX_MANIFEST_V1"
            ),
            "builder_version": (
                self.VERSION
            ),
            "dataset_kind": (
                "XAUUSD_MULTI_TIMEFRAME_CLASSIFICATION_MATRIX"
            ),
            "dataset_id": (
                dataset_id
            ),
            "dataset_filename": (
                dataset_path.name
            ),
            "dataset_sha256": (
                dataset_hash
            ),
            "row_count": int(
                len(
                    matrix
                )
            ),
            "feature_count": int(
                len(
                    feature_columns
                )
            ),
            "feature_columns": (
                feature_columns
            ),
            "target_columns": (
                target_columns
            ),
            "target_classes": [
                "SHORT",
                "NO_TRADE",
                "LONG",
            ],
            "target_class_mapping": {
                "SHORT": -1,
                "NO_TRADE": 0,
                "LONG": 1,
            },
            "base_timeframe": (
                base_tf
            ),
            "context_timeframes": (
                resolved_context_timeframes
            ),
            "target_horizon_bars": (
                horizon_bars
            ),
            "target_barrier_atr": float(
                barrier_atr
            ),
            "train_fraction": float(
                train_fraction
            ),
            "validation_fraction": float(
                validation_fraction
            ),
            "test_fraction": float(
                1.0
                -
                train_fraction
                -
                validation_fraction
            ),
            "split_purge_bars": (
                horizon_bars
            ),
            "class_distribution": (
                class_distribution
            ),
            "split_distribution": (
                split_distribution
            ),
            "learning_scope": (
                learning_document
            ),
            "learning_scope_fingerprint": (
                learning_fingerprint
            ),
            "source_execution_context_fingerprint": str(
                context.identity_fingerprint
            ),
            "source_historical_snapshots": (
                source_snapshots
            ),
            "feature_availability_rule": (
                "BAR_FEATURES_AVAILABLE_ONLY_AFTER_BAR_CLOSE"
            ),
            "target_future_data_rule": (
                "FUTURE_DATA_ALLOWED_ONLY_IN_TARGET_COLUMNS"
            ),
            "training_contract_version": (
                self.TRAINING_CONTRACT_VERSION
            ),
            "live_authorized": False,
        }

        manifest_bytes = (
            self._canonical_json_bytes(
                manifest
            )
        )

        manifest_hash = (
            self._sha256_bytes(
                manifest_bytes
            )
        )

        manifest_path = (
            dataset_path.with_suffix(
                ".manifest.json"
            )
        )

        manifest_reused = (
            self._write_immutable_bytes(
                path=manifest_path,
                payload=(
                    manifest_bytes
                ),
            )
        )

        return TrainingMatrixResult(
            dataset_id=dataset_id,
            dataset_path=(
                dataset_path
            ),
            manifest_path=(
                manifest_path
            ),
            dataset_sha256=(
                dataset_hash
            ),
            manifest_sha256=(
                manifest_hash
            ),
            row_count=int(
                len(
                    matrix
                )
            ),
            feature_count=int(
                len(
                    feature_columns
                )
            ),
            base_timeframe=(
                base_tf
            ),
            class_distribution=(
                class_distribution
            ),
            split_distribution=(
                split_distribution
            ),
            learning_scope_fingerprint=(
                learning_fingerprint
            ),
            training_contract_version=(
                self.TRAINING_CONTRACT_VERSION
            ),
            reused_existing_dataset=(
                dataset_reused
            ),
            reused_existing_manifest=(
                manifest_reused
            ),
            live_authorized=False,
        )