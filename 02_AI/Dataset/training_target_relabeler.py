"""
===============================================================================
Module      : training_target_relabeler.py
Project     : PulseViper XAU AI
Version     : 1.0
Purpose     : Immutable XAUUSD Training Target Contract Relabeler
===============================================================================

V2 target contract
------------------
LONG:
    future upside excursion >= profit_atr
    AND
    future downside excursion <= max_adverse_atr

SHORT:
    future downside excursion >= profit_atr
    AND
    future upside excursion <= max_adverse_atr

NO_TRADE:
    everything else

This converts an already-built causal feature matrix without recomputing
features.

Future data remains strictly target-only.

No MT5 calls.
No trading.
No live authorization.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from importlib import import_module


ROOT_DIR = (
    Path(__file__)
    .resolve()
    .parents[2]
)

CANONICAL_ROOT = (
    ROOT_DIR
    /
    "01_Data"
    /
    "Canonical"
)


builder_module: Any = import_module(
    "02_AI.Dataset.training_matrix_builder"
)

TrainingMatrixBuilder: Any = (
    builder_module.TrainingMatrixBuilder
)


class TrainingTargetRelabelError(
    RuntimeError
):
    pass


@dataclass(frozen=True)
class TrainingTargetRelabelResult:

    dataset_id: str
    dataset_path: Path
    manifest_path: Path

    dataset_sha256: str
    manifest_sha256: str

    source_dataset_id: str
    source_dataset_sha256: str

    row_count: int
    feature_count: int

    class_distribution: dict[str, int]
    split_class_distribution: dict[
        str,
        dict[str, int],
    ]

    learning_scope_fingerprint: str

    training_contract_version: str

    live_authorized: bool = False


class TrainingTargetRelabeler:

    VERSION = "1.0"

    SOURCE_CONTRACT = (
        "XAUUSD_MTF_TRAINING_V1"
    )

    TARGET_CONTRACT = (
        "XAUUSD_MTF_TRAINING_V2"
    )

    TARGET_LABEL_CONTRACT = (
        "CLEAN_DIRECTIONAL_EXCURSION_V2"
    )

    def __init__(
        self,
        *,
        canonical_root: Path | None = None,
    ) -> None:

        self.canonical_root = (
            Path(canonical_root)
            if canonical_root is not None
            else CANONICAL_ROOT
        )

    @staticmethod
    def _sha256_file(
        path: Path,
    ) -> str:

        digest = hashlib.sha256()

        with path.open("rb") as handle:

            while True:

                chunk = handle.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                digest.update(chunk)

        return digest.hexdigest()

    @staticmethod
    def _sha256_bytes(
        payload: bytes,
    ) -> str:

        return hashlib.sha256(
            payload
        ).hexdigest()

    @staticmethod
    def _canonical_json_bytes(
        document: Mapping[str, Any],
    ) -> bytes:

        return (
            json.dumps(
                document,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
            +
            "\n"
        ).encode("utf-8")

    @staticmethod
    def _validate_context(
        context: Any,
    ) -> None:

        if context is None:

            raise TrainingTargetRelabelError(
                "INSTRUMENT_CONTEXT_REQUIRED"
            )

        if bool(
            getattr(
                context,
                "live_authorized",
                False,
            )
        ):

            raise TrainingTargetRelabelError(
                "LIVE_AUTHORIZED_CONTEXT_REJECTED"
            )

        if (
            str(
                getattr(
                    context,
                    "canonical_symbol",
                    "",
                )
            )
            !=
            "XAUUSD"
        ):

            raise TrainingTargetRelabelError(
                "CANONICAL_SYMBOL_MISMATCH"
            )

    def _source_directory(
        self,
        *,
        context: Any,
    ) -> tuple[Path, str]:

        learning_fingerprint = (
            TrainingMatrixBuilder
            .learning_scope_fingerprint(
                context
            )
        )

        directory = (
            self.canonical_root
            /
            "Instruments"
            /
            "XAUUSD"
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
            self.SOURCE_CONTRACT
        )

        return (
            directory,
            learning_fingerprint,
        )

    def _discover_source(
        self,
        *,
        context: Any,
    ) -> tuple[
        Path,
        Path,
        dict[str, Any],
        str,
    ]:

        (
            directory,
            learning_fingerprint,
        ) = self._source_directory(
            context=context
        )

        if not directory.is_dir():

            raise TrainingTargetRelabelError(
                "SOURCE_TRAINING_DIRECTORY_MISSING"
            )

        candidates: list[
            tuple[
                pd.Timestamp,
                str,
                Path,
                dict[str, Any],
            ]
        ] = []

        for manifest_path in directory.glob(
            "*.manifest.json"
        ):

            manifest = json.loads(
                manifest_path.read_text(
                    encoding="utf-8"
                )
            )

            if (
                str(
                    manifest.get(
                        "training_contract_version",
                        "",
                    )
                )
                !=
                self.SOURCE_CONTRACT
            ):

                continue

            if (
                str(
                    manifest.get(
                        "learning_scope_fingerprint",
                        "",
                    )
                )
                !=
                learning_fingerprint
            ):

                continue

            base_timeframe = str(
                manifest.get(
                    "base_timeframe",
                    "",
                )
            )

            snapshots = manifest.get(
                "source_historical_snapshots",
                {},
            )

            base_snapshot = (
                snapshots.get(
                    base_timeframe,
                    {},
                )
                if isinstance(
                    snapshots,
                    Mapping,
                )
                else
                {}
            )

            end_time_raw = (
                base_snapshot.get(
                    "end_time",
                    "",
                )
                if isinstance(
                    base_snapshot,
                    Mapping,
                )
                else
                ""
            )

            try:

                end_time = pd.to_datetime(
                    end_time_raw,
                    utc=True,
                )

            except Exception:

                end_time = pd.Timestamp(
                    "1970-01-01",
                    tz="UTC",
                )

            candidates.append(
                (
                    end_time,
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

            raise TrainingTargetRelabelError(
                "SOURCE_TRAINING_MANIFEST_MISSING"
            )

        candidates.sort(
            key=lambda value: (
                value[0],
                value[1],
            )
        )

        (
            _end,
            _id,
            manifest_path,
            manifest,
        ) = candidates[-1]

        filename = str(
            manifest.get(
                "dataset_filename",
                "",
            )
        ).strip()

        dataset_path = (
            manifest_path.parent
            /
            filename
        )

        if not dataset_path.is_file():

            raise TrainingTargetRelabelError(
                "SOURCE_TRAINING_DATASET_MISSING"
            )

        expected_hash = str(
            manifest.get(
                "dataset_sha256",
                "",
            )
        )

        actual_hash = (
            self._sha256_file(
                dataset_path
            )
        )

        if (
            actual_hash
            !=
            expected_hash
        ):

            raise TrainingTargetRelabelError(
                "SOURCE_TRAINING_DATASET_HASH_MISMATCH"
            )

        return (
            dataset_path,
            manifest_path,
            manifest,
            actual_hash,
        )

    def _write_dataframe(
        self,
        *,
        frame: pd.DataFrame,
        directory: Path,
        prefix: str,
    ) -> tuple[
        Path,
        str,
    ]:

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        temp_path: Path | None = None

        try:

            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                suffix=".tmp.csv",
                dir=directory,
                delete=False,
            ) as handle:

                temp_path = Path(
                    handle.name
                )

                frame.to_csv(
                    handle,
                    index=False,
                    lineterminator="\n",
                    float_format="%.10g",
                )

                handle.flush()

                os.fsync(
                    handle.fileno()
                )

            digest = (
                self._sha256_file(
                    temp_path
                )
            )

            final_path = (
                directory
                /
                (
                    prefix
                    +
                    "_"
                    +
                    digest[:16]
                    +
                    ".csv"
                )
            )

            if final_path.exists():

                if (
                    self._sha256_file(
                        final_path
                    )
                    !=
                    digest
                ):

                    raise TrainingTargetRelabelError(
                        "V2_DATASET_COLLISION"
                    )

                temp_path.unlink(
                    missing_ok=True
                )

                temp_path = None

                return (
                    final_path,
                    digest,
                )

            os.replace(
                temp_path,
                final_path,
            )

            temp_path = None

            return (
                final_path,
                digest,
            )

        finally:

            if temp_path is not None:

                temp_path.unlink(
                    missing_ok=True
                )

    @staticmethod
    def _write_immutable(
        *,
        path: Path,
        payload: bytes,
    ) -> None:

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

                raise TrainingTargetRelabelError(
                    "V2_MANIFEST_COLLISION"
                )

            return

        with path.open("xb") as handle:

            handle.write(payload)

            handle.flush()

            os.fsync(
                handle.fileno()
            )

    def relabel(
        self,
        *,
        context: Any,
        profit_atr: float = 1.25,
        max_adverse_atr: float = 0.75,
    ) -> TrainingTargetRelabelResult:

        self._validate_context(
            context
        )

        profit = float(
            profit_atr
        )

        adverse = float(
            max_adverse_atr
        )

        if (
            not np.isfinite(profit)
            or
            not np.isfinite(adverse)
            or
            adverse <= 0.0
            or
            profit <= adverse
        ):

            raise TrainingTargetRelabelError(
                "INVALID_V2_TARGET_THRESHOLDS"
            )

        (
            source_path,
            source_manifest_path,
            source_manifest,
            source_hash,
        ) = self._discover_source(
            context=context
        )

        frame = pd.read_csv(
            source_path
        )

        if frame.empty:

            raise TrainingTargetRelabelError(
                "SOURCE_MATRIX_EMPTY"
            )

        required = {
            "target_up_excursion_atr",
            "target_down_excursion_atr",
            "target_forward_return_atr",
            "target_entry_close",
            "dataset_split",
        }

        missing = (
            required
            -
            set(frame.columns)
        )

        if missing:

            raise TrainingTargetRelabelError(
                (
                    "SOURCE_TARGET_COLUMNS_MISSING: "
                    +
                    ", ".join(
                        sorted(missing)
                    )
                )
            )

        feature_columns = [
            str(value)
            for value
            in source_manifest.get(
                "feature_columns",
                [],
            )
        ]

        if not feature_columns:

            raise TrainingTargetRelabelError(
                "SOURCE_FEATURE_COLUMNS_MISSING"
            )

        if any(
            column not in frame.columns
            for column
            in feature_columns
        ):

            raise TrainingTargetRelabelError(
                "SOURCE_FEATURE_MATRIX_INCOMPLETE"
            )

        up = pd.to_numeric(
            frame[
                "target_up_excursion_atr"
            ],
            errors="coerce",
        )

        down = pd.to_numeric(
            frame[
                "target_down_excursion_atr"
            ],
            errors="coerce",
        )

        if bool(
            (
                ~np.isfinite(up)
                |
                ~np.isfinite(down)
            ).any()
        ):

            raise TrainingTargetRelabelError(
                "NONFINITE_V2_TARGET_SOURCE"
            )

        long_mask = (
            (up >= profit)
            &
            (down <= adverse)
        )

        short_mask = (
            (down >= profit)
            &
            (up <= adverse)
        )

        if bool(
            (
                long_mask
                &
                short_mask
            ).any()
        ):

            raise TrainingTargetRelabelError(
                "IMPOSSIBLE_TARGET_OVERLAP"
            )

        target_class = np.full(
            len(frame),
            "NO_TRADE",
            dtype=object,
        )

        target_class_id = np.zeros(
            len(frame),
            dtype=np.int8,
        )

        target_reason = np.full(
            len(frame),
            "NO_CLEAN_DIRECTIONAL_EXCURSION",
            dtype=object,
        )

        target_class[
            long_mask.to_numpy()
        ] = "LONG"

        target_class_id[
            long_mask.to_numpy()
        ] = 1

        target_reason[
            long_mask.to_numpy()
        ] = (
            "CLEAN_LONG_EXCURSION"
        )

        target_class[
            short_mask.to_numpy()
        ] = "SHORT"

        target_class_id[
            short_mask.to_numpy()
        ] = -1

        target_reason[
            short_mask.to_numpy()
        ] = (
            "CLEAN_SHORT_EXCURSION"
        )

        ambiguous = (
            (up >= profit)
            &
            (down >= profit)
        ).astype(
            np.int8
        )

        tradeable = (
            target_class
            !=
            "NO_TRADE"
        ).astype(
            np.int8
        )

        remove_columns = [
            column
            for column
            in (
                "target_class",
                "target_class_id",
                "target_resolved",
                "target_ambiguous",
                "target_resolution_bars",
                "target_upper_barrier",
                "target_lower_barrier",
                "target_reason",
                "target_profit_atr",
                "target_max_adverse_atr",
                "target_tradeable",
            )
            if column
            in frame.columns
        ]

        result_frame = frame.drop(
            columns=remove_columns
        ).copy()

        result_frame[
            "target_class"
        ] = target_class

        result_frame[
            "target_class_id"
        ] = target_class_id

        result_frame[
            "target_tradeable"
        ] = tradeable

        result_frame[
            "target_ambiguous"
        ] = ambiguous

        result_frame[
            "target_profit_atr"
        ] = profit

        result_frame[
            "target_max_adverse_atr"
        ] = adverse

        result_frame[
            "target_reason"
        ] = target_reason

        classes = set(
            result_frame[
                "target_class"
            ].unique()
        )

        if classes != {
            "SHORT",
            "NO_TRADE",
            "LONG",
        }:

            raise TrainingTargetRelabelError(
                (
                    "V2_REQUIRED_CLASSES_MISSING: "
                    f"{sorted(classes)}"
                )
            )

        split_values = set(
            result_frame[
                "dataset_split"
            ].unique()
        )

        if split_values != {
            "TRAIN",
            "VALIDATION",
            "TEST",
        }:

            raise TrainingTargetRelabelError(
                "V2_SPLIT_CONTRACT_MISMATCH"
            )

        learning_fingerprint = str(
            source_manifest[
                "learning_scope_fingerprint"
            ]
        )

        output_directory = (
            self.canonical_root
            /
            "Instruments"
            /
            "XAUUSD"
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
            self.TARGET_CONTRACT
        )

        base_timeframe = str(
            source_manifest.get(
                "base_timeframe",
                "M5",
            )
        )

        prefix = (
            "XAUUSD_"
            +
            base_timeframe
            +
            "_"
            +
            self.TARGET_CONTRACT
        )

        (
            dataset_path,
            dataset_hash,
        ) = self._write_dataframe(
            frame=result_frame,
            directory=output_directory,
            prefix=prefix,
        )

        dataset_id = (
            "train_"
            +
            dataset_hash[:24]
        )

        class_distribution = {
            str(key): int(value)
            for (
                key,
                value,
            )
            in result_frame[
                "target_class"
            ]
            .value_counts()
            .items()
        }

        split_class_distribution: dict[
            str,
            dict[str, int],
        ] = {}

        for split in (
            "TRAIN",
            "VALIDATION",
            "TEST",
        ):

            subset = result_frame[
                result_frame[
                    "dataset_split"
                ]
                ==
                split
            ]

            split_class_distribution[
                split
            ] = {
                str(key): int(value)
                for (
                    key,
                    value,
                )
                in subset[
                    "target_class"
                ]
                .value_counts()
                .items()
            }

        target_columns = [
            "target_class",
            "target_class_id",
            "target_tradeable",
            "target_ambiguous",
            "target_profit_atr",
            "target_max_adverse_atr",
            "target_entry_close",
            "target_up_excursion_atr",
            "target_down_excursion_atr",
            "target_forward_return_atr",
            "target_reason",
        ]

        manifest = {
            "manifest_version": (
                "PULSEVIPER_TRAINING_MATRIX_MANIFEST_V2"
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
                len(result_frame)
            ),
            "feature_count": int(
                len(feature_columns)
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
            "target_label_contract": {
                "name": (
                    self.TARGET_LABEL_CONTRACT
                ),
                "profit_atr": (
                    profit
                ),
                "max_adverse_atr": (
                    adverse
                ),
                "LONG": (
                    "UP_EXCURSION_GTE_PROFIT_AND_"
                    "DOWN_EXCURSION_LTE_MAX_ADVERSE"
                ),
                "SHORT": (
                    "DOWN_EXCURSION_GTE_PROFIT_AND_"
                    "UP_EXCURSION_LTE_MAX_ADVERSE"
                ),
                "NO_TRADE": (
                    "ALL_OTHER_FUTURE_PATHS"
                ),
            },
            "base_timeframe": (
                base_timeframe
            ),
            "context_timeframes": (
                source_manifest.get(
                    "context_timeframes",
                    [],
                )
            ),
            "target_horizon_bars": (
                source_manifest.get(
                    "target_horizon_bars"
                )
            ),
            "train_fraction": (
                source_manifest.get(
                    "train_fraction"
                )
            ),
            "validation_fraction": (
                source_manifest.get(
                    "validation_fraction"
                )
            ),
            "test_fraction": (
                source_manifest.get(
                    "test_fraction"
                )
            ),
            "split_purge_bars": (
                source_manifest.get(
                    "split_purge_bars"
                )
            ),
            "class_distribution": (
                class_distribution
            ),
            "split_class_distribution": (
                split_class_distribution
            ),
            "learning_scope": (
                source_manifest.get(
                    "learning_scope"
                )
            ),
            "learning_scope_fingerprint": (
                learning_fingerprint
            ),
            "source_execution_context_fingerprint": (
                source_manifest.get(
                    "source_execution_context_fingerprint"
                )
            ),
            "source_historical_snapshots": (
                source_manifest.get(
                    "source_historical_snapshots"
                )
            ),
            "source_training_matrix": {
                "dataset_id": (
                    source_manifest.get(
                        "dataset_id"
                    )
                ),
                "dataset_sha256": (
                    source_hash
                ),
                "manifest_sha256": (
                    self._sha256_file(
                        source_manifest_path
                    )
                ),
                "training_contract_version": (
                    self.SOURCE_CONTRACT
                ),
            },
            "feature_availability_rule": (
                source_manifest.get(
                    "feature_availability_rule"
                )
            ),
            "target_future_data_rule": (
                "FUTURE_DATA_ALLOWED_ONLY_IN_TARGET_COLUMNS"
            ),
            "training_contract_version": (
                self.TARGET_CONTRACT
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

        self._write_immutable(
            path=manifest_path,
            payload=manifest_bytes,
        )

        return TrainingTargetRelabelResult(
            dataset_id=dataset_id,
            dataset_path=dataset_path,
            manifest_path=manifest_path,
            dataset_sha256=dataset_hash,
            manifest_sha256=manifest_hash,
            source_dataset_id=str(
                source_manifest.get(
                    "dataset_id",
                    "",
                )
            ),
            source_dataset_sha256=(
                source_hash
            ),
            row_count=len(
                result_frame
            ),
            feature_count=len(
                feature_columns
            ),
            class_distribution=(
                class_distribution
            ),
            split_class_distribution=(
                split_class_distribution
            ),
            learning_scope_fingerprint=(
                learning_fingerprint
            ),
            training_contract_version=(
                self.TARGET_CONTRACT
            ),
            live_authorized=False,
        )