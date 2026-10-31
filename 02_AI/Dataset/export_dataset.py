"""
===============================================================================
Module      : export_dataset.py
Project     : PulseViper XAU AI
Version     : 2.0
Purpose     : Canonical Instrument-Isolated Dataset Materializer
===============================================================================

This module is the canonical persistence boundary for training/research data.

Safety / isolation:
- InstrumentContext is mandatory.
- Every row is stamped by InstrumentFrameGuard.
- Exact broker symbol is preserved.
- Cross-symbol data fails closed.
- Dataset paths are namespaced by canonical symbol + context fingerprint.
- Dataset bytes are content-addressed and immutable.
- A canonical JSON manifest is written beside every dataset.
- No MT5 calls.
- No execution authority.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

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

CANONICAL_DATA_ROOT = (
    ROOT_DIR
    /
    "01_Data"
    /
    "Canonical"
)


guard_module: Any = importlib.import_module(
    "02_AI.Dataset.instrument_frame_guard"
)

InstrumentFrameGuard: Any = (
    guard_module.InstrumentFrameGuard
)


validator_module: Any = importlib.import_module(
    "02_AI.Dataset.history_validator"
)

history_validator: Any = (
    validator_module.validator
)


class DatasetMaterializationError(
    RuntimeError
):
    pass


@dataclass(frozen=True)
class DatasetMaterializationResult:

    dataset_id: str

    dataset_path: Path

    manifest_path: Path

    dataset_sha256: str

    manifest_sha256: str

    row_count: int

    timeframe: str

    canonical_symbol: str

    broker_symbol: str

    context_identity_fingerprint: str

    reused_existing_dataset: bool

    reused_existing_manifest: bool

    live_authorized: bool = False


class DatasetExporter:

    MANIFEST_VERSION = (
        "PULSEVIPER_CANONICAL_HISTORY_MANIFEST_V1"
    )

    def __init__(
        self,
        output_root: Path | None = None,
    ) -> None:

        self.output_root = (
            Path(
                output_root
            )
            if output_root is not None
            else
            CANONICAL_DATA_ROOT
        )

    # =========================================================================
    # Helpers
    # =========================================================================

    @staticmethod
    def _safe_token(
        value: Any,
        *,
        field_name: str,
    ) -> str:

        raw = str(
            value
        ).strip()

        if not raw:

            raise DatasetMaterializationError(
                f"{field_name.upper()}_MISSING"
            )

        if raw in {
            ".",
            "..",
        }:

            raise DatasetMaterializationError(
                f"INVALID_{field_name.upper()}"
            )

        if (
            "/"
            in raw
            or
            "\\"
            in raw
            or
            "\x00"
            in raw
        ):

            raise DatasetMaterializationError(
                f"INVALID_{field_name.upper()}"
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
                    "-",
                    "_",
                    ".",
                }
            )
        )

        if not cleaned:

            raise DatasetMaterializationError(
                f"INVALID_{field_name.upper()}"
            )

        return cleaned

    @staticmethod
    def _sha256(
        payload: bytes,
    ) -> str:

        return hashlib.sha256(
            payload
        ).hexdigest()

    @staticmethod
    def _json_scalar(
        value: Any,
    ) -> Any:

        if value is None:

            return None

        if hasattr(
            value,
            "item",
        ):

            try:

                value = value.item()

            except Exception:

                pass

        if hasattr(
            value,
            "isoformat",
        ):

            try:

                return value.isoformat()

            except Exception:

                pass

        if isinstance(
            value,
            (
                str,
                int,
                float,
                bool,
            ),
        ):

            return value

        return str(
            value
        )

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
    def _context_document(
        context: Any,
    ) -> dict[
        str,
        Any
    ]:

        if context is None:

            raise DatasetMaterializationError(
                "INSTRUMENT_CONTEXT_REQUIRED"
            )

        if bool(
            getattr(
                context,
                "live_authorized",
                False,
            )
        ):

            raise DatasetMaterializationError(
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

            raise DatasetMaterializationError(
                "INVALID_INSTRUMENT_CONTEXT"
            )

        document = method()

        if not isinstance(
            document,
            Mapping,
        ):

            raise DatasetMaterializationError(
                "INVALID_CONTEXT_IDENTITY_DOCUMENT"
            )

        return dict(
            document
        )

    @staticmethod
    def _write_immutable(
        path: Path,
        payload: bytes,
    ) -> bool:
        """
        Return True when an existing identical artifact was reused.

        Existing different bytes at the same content-addressed path are treated
        as corruption/collision and fail closed.
        """

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if path.exists():

            existing = (
                path.read_bytes()
            )

            if existing != payload:

                raise DatasetMaterializationError(
                    "IMMUTABLE_ARTIFACT_COLLISION"
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

            existing = (
                path.read_bytes()
            )

            if existing != payload:

                raise DatasetMaterializationError(
                    "IMMUTABLE_ARTIFACT_COLLISION"
                )

            return True

        except Exception:

            try:

                if path.exists():

                    path.unlink()

            except Exception:

                pass

            raise

        return False

    # =========================================================================
    # Materialization
    # =========================================================================

    def materialize_history(
        self,
        *,
        dataframe: pd.DataFrame,
        context: Any,
        source_metadata: Mapping[
            str,
            Any,
        ],
    ) -> DatasetMaterializationResult:

        if not isinstance(
            dataframe,
            pd.DataFrame,
        ):

            raise DatasetMaterializationError(
                "DATAFRAME_REQUIRED"
            )

        if not isinstance(
            source_metadata,
            Mapping,
        ):

            raise DatasetMaterializationError(
                "SOURCE_METADATA_REQUIRED"
            )

        context_document = (
            self._context_document(
                context
            )
        )

        canonical_symbol = (
            self._safe_token(
                getattr(
                    context,
                    "canonical_symbol",
                    "",
                ),
                field_name=(
                    "canonical_symbol"
                ),
            )
        )

        broker_symbol = str(
            getattr(
                context,
                "broker_symbol",
                "",
            )
        ).strip()

        if not broker_symbol:

            raise DatasetMaterializationError(
                "BROKER_SYMBOL_MISSING"
            )

        identity_fingerprint = str(
            getattr(
                context,
                "identity_fingerprint",
                "",
            )
        ).strip()

        if not identity_fingerprint:

            raise DatasetMaterializationError(
                "CONTEXT_IDENTITY_FINGERPRINT_MISSING"
            )

        resolved_symbol = str(
            source_metadata.get(
                "resolved_symbol",
                "",
            )
        ).strip()

        if (
            resolved_symbol
            !=
            broker_symbol
        ):

            raise DatasetMaterializationError(
                "SOURCE_BROKER_SYMBOL_CONTEXT_MISMATCH"
            )

        timeframe = (
            self._safe_token(
                source_metadata.get(
                    "timeframe",
                    "",
                ),
                field_name="timeframe",
            )
            .upper()
        )

        # =====================================================================
        # Structural validation before identity stamping
        # =====================================================================

        try:

            history_validator.validate(
                dataframe
            )

        except Exception as exc:

            raise DatasetMaterializationError(
                f"HISTORY_VALIDATION_FAILED: {exc}"
            ) from exc

        if (
            "time"
            not in dataframe.columns
        ):

            raise DatasetMaterializationError(
                "TIME_COLUMN_MISSING"
            )

        if bool(
            dataframe[
                "time"
            ].duplicated().any()
        ):

            raise DatasetMaterializationError(
                "DUPLICATE_TIMESTAMPS"
            )

        # =====================================================================
        # Instrument identity stamping
        # =====================================================================

        guard = (
            InstrumentFrameGuard(
                context
            )
        )

        try:

            stamped = (
                guard.stamp(
                    dataframe
                )
            )

            guard.validate(
                stamped,
                require_nonempty=True,
            )

        except Exception as exc:

            raise DatasetMaterializationError(
                (
                    "INSTRUMENT_FRAME_"
                    f"VALIDATION_FAILED: {exc}"
                )
            ) from exc

        # =====================================================================
        # Canonical deterministic CSV bytes
        # =====================================================================

        csv_text = (
            stamped.to_csv(
                index=False,
                lineterminator="\n",
                date_format=(
                    "%Y-%m-%dT%H:%M:%S.%f"
                ),
            )
        )

        csv_bytes = (
            csv_text.encode(
                "utf-8"
            )
        )

        dataset_sha256 = (
            self._sha256(
                csv_bytes
            )
        )

        dataset_id = (
            "hist_"
            +
            dataset_sha256[
                :24
            ]
        )

        safe_broker_symbol = (
            self._safe_token(
                broker_symbol,
                field_name=(
                    "broker_symbol"
                ),
            )
        )

        namespace = (
            self.output_root
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

        filename_base = (
            f"{canonical_symbol}_"
            f"{safe_broker_symbol}_"
            f"{timeframe}_"
            f"{dataset_sha256[:16]}"
        )

        dataset_path = (
            namespace
            /
            (
                filename_base
                +
                ".csv"
            )
        )

        manifest_path = (
            namespace
            /
            (
                filename_base
                +
                ".manifest.json"
            )
        )

        start_time = (
            stamped[
                "time"
            ].iloc[
                0
            ]
        )

        end_time = (
            stamped[
                "time"
            ].iloc[
                -1
            ]
        )

        manifest = {
            "manifest_version": (
                self.MANIFEST_VERSION
            ),
            "dataset_kind": (
                "HISTORICAL_MARKET_BARS"
            ),
            "dataset_id": (
                dataset_id
            ),
            "dataset_sha256": (
                dataset_sha256
            ),
            "dataset_filename": (
                dataset_path.name
            ),
            "row_count": int(
                len(
                    stamped
                )
            ),
            "columns": list(
                stamped.columns
            ),
            "timeframe": (
                timeframe
            ),
            "start_time": (
                self._json_scalar(
                    start_time
                )
            ),
            "end_time": (
                self._json_scalar(
                    end_time
                )
            ),
            "instrument_identity": (
                context_document
            ),
            "context_identity_fingerprint": (
                identity_fingerprint
            ),
            "source": {
                key: (
                    self._json_scalar(
                        value
                    )
                )
                for (
                    key,
                    value,
                )
                in sorted(
                    source_metadata.items()
                )
            },
            "live_authorized": False,
        }

        manifest_bytes = (
            self._canonical_json_bytes(
                manifest
            )
        )

        manifest_sha256 = (
            self._sha256(
                manifest_bytes
            )
        )

        dataset_reused = (
            self._write_immutable(
                dataset_path,
                csv_bytes,
            )
        )

        try:

            manifest_reused = (
                self._write_immutable(
                    manifest_path,
                    manifest_bytes,
                )
            )

        except Exception:

            if not dataset_reused:

                try:

                    dataset_path.unlink(
                        missing_ok=True
                    )

                except Exception:

                    pass

            raise

        return DatasetMaterializationResult(
            dataset_id=dataset_id,
            dataset_path=dataset_path,
            manifest_path=manifest_path,
            dataset_sha256=(
                dataset_sha256
            ),
            manifest_sha256=(
                manifest_sha256
            ),
            row_count=int(
                len(
                    stamped
                )
            ),
            timeframe=timeframe,
            canonical_symbol=(
                canonical_symbol
            ),
            broker_symbol=(
                broker_symbol
            ),
            context_identity_fingerprint=(
                identity_fingerprint
            ),
            reused_existing_dataset=(
                dataset_reused
            ),
            reused_existing_manifest=(
                manifest_reused
            ),
            live_authorized=False,
        )

    # =========================================================================
    # Compatibility entrypoint
    # =========================================================================

    def export(
        self,
        dataframe: pd.DataFrame,
        filename: str | None = None,
        *,
        context: Any = None,
        source_metadata: Mapping[
            str,
            Any,
        ]
        | None = None,
    ) -> Path:
        """
        Legacy method retained as a fail-closed compatibility entrypoint.

        Flat filename-only exports are intentionally no longer permitted.
        """

        if context is None:

            raise DatasetMaterializationError(
                "INSTRUMENT_CONTEXT_REQUIRED"
            )

        if source_metadata is None:

            raise DatasetMaterializationError(
                "SOURCE_METADATA_REQUIRED"
            )

        result = (
            self.materialize_history(
                dataframe=dataframe,
                context=context,
                source_metadata=(
                    source_metadata
                ),
            )
        )

        return result.dataset_path


exporter = DatasetExporter()