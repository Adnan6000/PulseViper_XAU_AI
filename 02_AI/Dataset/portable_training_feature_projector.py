from __future__ import annotations

import hashlib
import json
import os
import tempfile

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd


class PortableTrainingFeatureProjectionError(
    RuntimeError
):
    pass


@dataclass(
    frozen=True
)
class PortableTrainingFeatureProjectionResult:
    dataset_id: str
    dataset_path: Path
    manifest_path: Path
    dataset_sha256: str
    manifest_sha256: str
    source_dataset_id: str
    source_dataset_sha256: str
    source_manifest_sha256: str
    row_count: int
    feature_count: int
    dropped_feature_count: int
    training_contract_version: str
    live_authorized: bool


class PortableTrainingFeatureProjector:
    """
    Immutable post-V3 feature projection stage.

    This projector does not rebuild technical/domain features and does not
    relabel targets. It takes one already validated frozen
    XAUUSD_MTF_TRAINING_V3 matrix and creates a new immutable dataset whose
    model feature contract removes exactly two broker-sensitive features:

        - m5_spread_points
        - m5_tick_volume_log1p

    m5_tick_volume_ratio20 is retained unchanged.

    The parent V3 artifact is never modified.
    """

    VERSION = (
        "1.0"
    )

    MANIFEST_VERSION = (
        "PULSEVIPER_PORTABLE_TRAINING_MATRIX_MANIFEST_V1"
    )

    SOURCE_CONTRACT = (
        "XAUUSD_MTF_TRAINING_V3"
    )

    TARGET_CONTRACT = (
        "XAUUSD_MTF_PORTABLE_FEATURE_V1"
    )

    CONTRACT_DESIGN_FINGERPRINT_VERSION = (
        "XAUUSD_PORTABLE_FEATURE_CONTRACT_FINGERPRINT_V1"
    )

    CONTRACT_DESIGN_FINGERPRINT_SHA256 = (
        "de389b1daa02b2d864490aa41776494baea4f9e42dbf2146c2c44b9c2660ff40"
    )

    EXPECTED_SOURCE_DATASET_ID = (
        "train_66ff363d25d8143d4e2c3410"
    )

    EXPECTED_SOURCE_DATASET_SHA256 = (
        "66ff363d25d8143d4e2c3410964ad26b5bd72f2e98806c3e0997ce420d18413d"
    )

    EXPECTED_SOURCE_MANIFEST_SHA256 = (
        "a205403a6cb5a2d1b17159a2296d1f4afb01ea5b9b90b2710feafa7dd9476aa3"
    )

    EXPECTED_PARENT_FEATURE_COUNT = (
        333
    )

    EXPECTED_PORTABLE_FEATURE_COUNT = (
        331
    )

    DROPPED_FEATURES = (
        "m5_spread_points",
        "m5_tick_volume_log1p",
    )

    RETAINED_RELATIVE_VOLUME_FEATURE = (
        "m5_tick_volume_ratio20"
    )

    DATASET_PREFIX = (
        "pv_portable_xauusd_"
    )

    OUTPUT_DIRECTORY_NAME = (
        "portable_v1"
    )

    REQUIRED_NON_FEATURE_COLUMNS = (
        "decision_time",
        "dataset_split",
    )

    def __init__(
        self,
        canonical_root: str | Path,
    ) -> None:

        self.canonical_root = Path(
            canonical_root
        )

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
                    1024 * 1024
                )

                if not chunk:
                    break

                digest.update(
                    chunk
                )

        return digest.hexdigest()

    @staticmethod
    def _canonical_json_bytes(
        document: Mapping[
            str,
            Any,
        ],
    ) -> bytes:

        return json.dumps(
            document,
            sort_keys=True,
            separators=(
                ",",
                ":",
            ),
            ensure_ascii=True,
            allow_nan=False,
        ).encode(
            "utf-8"
        )

    @staticmethod
    def _load_json(
        path: Path,
    ) -> dict[str, Any]:

        try:

            raw = path.read_bytes()

        except OSError as exc:

            raise (
                PortableTrainingFeatureProjectionError(
                    "SOURCE_MANIFEST_READ_FAILED"
                )
            ) from exc

        if raw.startswith(
            b"\xef\xbb\xbf"
        ):

            encoding = (
                "utf-8-sig"
            )

        elif (
            raw.startswith(
                b"\xff\xfe"
            )
            or
            raw.startswith(
                b"\xfe\xff"
            )
        ):

            encoding = (
                "utf-16"
            )

        else:

            encoding = (
                "utf-8"
            )

        try:

            text = raw.decode(
                encoding
            )

        except UnicodeDecodeError as exc:

            raise (
                PortableTrainingFeatureProjectionError(
                    "SOURCE_MANIFEST_ENCODING_INVALID"
                )
            ) from exc

        try:

            document = json.loads(
                text
            )

        except json.JSONDecodeError as exc:

            raise (
                PortableTrainingFeatureProjectionError(
                    "SOURCE_MANIFEST_JSON_INVALID"
                )
            ) from exc

        if not isinstance(
            document,
            dict,
        ):
            raise (
                PortableTrainingFeatureProjectionError(
                    "SOURCE_MANIFEST_ROOT_NOT_OBJECT"
                )
            )

        return document

    @staticmethod
    def _string_list(
        value: Any,
        *,
        field_name: str,
    ) -> list[str]:

        if not isinstance(
            value,
            list,
        ):
            raise (
                PortableTrainingFeatureProjectionError(
                    (
                        "SOURCE_MANIFEST_LIST_INVALID:"
                        f"{field_name}"
                    )
                )
            )

        result = [
            str(
                item
            )
            for item
            in value
        ]

        if any(
            not item
            for item
            in result
        ):
            raise (
                PortableTrainingFeatureProjectionError(
                    (
                        "SOURCE_MANIFEST_LIST_EMPTY_VALUE:"
                        f"{field_name}"
                    )
                )
            )

        return result

    @classmethod
    def _portable_feature_columns(
        cls,
        source_feature_columns: Sequence[
            str
        ],
    ) -> list[str]:

        features = [
            str(
                feature
            )
            for feature
            in source_feature_columns
        ]

        if (
            len(
                features
            )
            !=
            cls.EXPECTED_PARENT_FEATURE_COUNT
        ):
            raise (
                PortableTrainingFeatureProjectionError(
                    (
                        "SOURCE_FEATURE_COUNT_MISMATCH:"
                        f"{len(features)}:"
                        f"{cls.EXPECTED_PARENT_FEATURE_COUNT}"
                    )
                )
            )

        if (
            len(
                set(
                    features
                )
            )
            !=
            len(
                features
            )
        ):
            raise (
                PortableTrainingFeatureProjectionError(
                    "SOURCE_FEATURE_COLUMNS_NOT_UNIQUE"
                )
            )

        for feature in (
            cls.DROPPED_FEATURES
        ):

            if (
                feature
                not in
                features
            ):
                raise (
                    PortableTrainingFeatureProjectionError(
                        (
                            "DROP_FEATURE_NOT_IN_PARENT_CONTRACT:"
                            f"{feature}"
                        )
                    )
                )

        if (
            cls.RETAINED_RELATIVE_VOLUME_FEATURE
            not in
            features
        ):
            raise (
                PortableTrainingFeatureProjectionError(
                    "RETAINED_RELATIVE_VOLUME_FEATURE_MISSING"
                )
            )

        drop_set = set(
            cls.DROPPED_FEATURES
        )

        portable = [
            feature
            for feature
            in features
            if (
                feature
                not in
                drop_set
            )
        ]

        if (
            len(
                portable
            )
            !=
            cls.EXPECTED_PORTABLE_FEATURE_COUNT
        ):
            raise (
                PortableTrainingFeatureProjectionError(
                    (
                        "PORTABLE_FEATURE_COUNT_MISMATCH:"
                        f"{len(portable)}:"
                        f"{cls.EXPECTED_PORTABLE_FEATURE_COUNT}"
                    )
                )
            )

        if any(
            feature
            in
            portable
            for feature
            in cls.DROPPED_FEATURES
        ):
            raise (
                PortableTrainingFeatureProjectionError(
                    "DROPPED_FEATURE_RETAINED"
                )
            )

        if (
            cls.RETAINED_RELATIVE_VOLUME_FEATURE
            not in
            portable
        ):
            raise (
                PortableTrainingFeatureProjectionError(
                    "RELATIVE_VOLUME_FEATURE_DROPPED"
                )
            )

        return portable

    @classmethod
    def _project_frame(
        cls,
        *,
        source_frame: pd.DataFrame,
        source_feature_columns: Sequence[
            str
        ],
        target_columns: Sequence[
            str
        ],
    ) -> tuple[
        pd.DataFrame,
        list[str],
    ]:

        if source_frame.empty:
            raise (
                PortableTrainingFeatureProjectionError(
                    "SOURCE_MATRIX_EMPTY"
                )
            )

        portable_features = (
            cls._portable_feature_columns(
                source_feature_columns
            )
        )

        source_columns = [
            str(
                column
            )
            for column
            in source_frame.columns
        ]

        missing_features = [
            feature
            for feature
            in source_feature_columns
            if (
                str(
                    feature
                )
                not in
                source_columns
            )
        ]

        if missing_features:
            raise (
                PortableTrainingFeatureProjectionError(
                    (
                        "SOURCE_FEATURE_COLUMNS_MISSING_FROM_MATRIX:"
                        f"{','.join(sorted(missing_features))}"
                    )
                )
            )

        for column in (
            cls.REQUIRED_NON_FEATURE_COLUMNS
        ):

            if (
                column
                not in
                source_columns
            ):
                raise (
                    PortableTrainingFeatureProjectionError(
                        (
                            "REQUIRED_MATRIX_COLUMN_MISSING:"
                            f"{column}"
                        )
                    )
                )

        for target in (
            target_columns
        ):

            target_name = str(
                target
            )

            if (
                target_name
                not in
                source_columns
            ):
                raise (
                    PortableTrainingFeatureProjectionError(
                        (
                            "TARGET_COLUMN_MISSING_FROM_MATRIX:"
                            f"{target_name}"
                        )
                    )
                )

        projected = (
            source_frame.drop(
                columns=list(
                    cls.DROPPED_FEATURES
                )
            )
            .copy()
        )

        expected_columns = [
            column
            for column
            in source_columns
            if (
                column
                not in
                set(
                    cls.DROPPED_FEATURES
                )
            )
        ]

        observed_columns = [
            str(
                column
            )
            for column
            in projected.columns
        ]

        if (
            observed_columns
            !=
            expected_columns
        ):
            raise (
                PortableTrainingFeatureProjectionError(
                    "PROJECTED_MATRIX_COLUMN_ORDER_CHANGED"
                )
            )

        if (
            len(
                projected
            )
            !=
            len(
                source_frame
            )
        ):
            raise (
                PortableTrainingFeatureProjectionError(
                    "PROJECTED_MATRIX_ROW_COUNT_CHANGED"
                )
            )

        if (
            projected[
                "decision_time"
            ]
            .duplicated()
            .any()
        ):
            raise (
                PortableTrainingFeatureProjectionError(
                    "PROJECTED_MATRIX_DUPLICATE_DECISION_TIME"
                )
            )

        portable_matrix_features = [
            feature
            for feature
            in portable_features
            if (
                feature
                in
                projected.columns
            )
        ]

        if (
            portable_matrix_features
            !=
            portable_features
        ):
            raise (
                PortableTrainingFeatureProjectionError(
                    "PORTABLE_FEATURE_ORDER_NOT_PRESERVED"
                )
            )

        return (
            projected,
            portable_features,
        )

    @classmethod
    def _validate_source_manifest(
        cls,
        *,
        source_manifest: Mapping[
            str,
            Any,
        ],
        source_dataset_path: Path,
        source_manifest_path: Path,
    ) -> tuple[
        list[str],
        list[str],
    ]:

        source_manifest_sha256 = (
            cls._sha256_file(
                source_manifest_path
            )
        )

        if (
            source_manifest_sha256
            !=
            cls.EXPECTED_SOURCE_MANIFEST_SHA256
        ):
            raise (
                PortableTrainingFeatureProjectionError(
                    "SOURCE_MANIFEST_SHA256_MISMATCH"
                )
            )

        source_dataset_sha256 = (
            cls._sha256_file(
                source_dataset_path
            )
        )

        if (
            source_dataset_sha256
            !=
            cls.EXPECTED_SOURCE_DATASET_SHA256
        ):
            raise (
                PortableTrainingFeatureProjectionError(
                    "SOURCE_DATASET_SHA256_MISMATCH"
                )
            )

        source_dataset_id = str(
            source_manifest.get(
                "dataset_id",
                "",
            )
        )

        if (
            source_dataset_id
            !=
            cls.EXPECTED_SOURCE_DATASET_ID
        ):
            raise (
                PortableTrainingFeatureProjectionError(
                    "SOURCE_DATASET_ID_MISMATCH"
                )
            )

        manifest_dataset_sha256 = str(
            source_manifest.get(
                "dataset_sha256",
                "",
            )
        )

        if (
            manifest_dataset_sha256
            !=
            cls.EXPECTED_SOURCE_DATASET_SHA256
        ):
            raise (
                PortableTrainingFeatureProjectionError(
                    "SOURCE_MANIFEST_DATASET_SHA256_MISMATCH"
                )
            )

        training_contract_version = str(
            source_manifest.get(
                "training_contract_version",
                "",
            )
        )

        if (
            training_contract_version
            !=
            cls.SOURCE_CONTRACT
        ):
            raise (
                PortableTrainingFeatureProjectionError(
                    "SOURCE_TRAINING_CONTRACT_MISMATCH"
                )
            )

        if bool(
            source_manifest.get(
                "live_authorized",
                False,
            )
        ):
            raise (
                PortableTrainingFeatureProjectionError(
                    "SOURCE_MATRIX_UNEXPECTEDLY_LIVE_AUTHORIZED"
                )
            )

        source_feature_count = int(
            source_manifest.get(
                "feature_count",
                -1,
            )
        )

        if (
            source_feature_count
            !=
            cls.EXPECTED_PARENT_FEATURE_COUNT
        ):
            raise (
                PortableTrainingFeatureProjectionError(
                    "SOURCE_MANIFEST_FEATURE_COUNT_MISMATCH"
                )
            )

        source_feature_columns = (
            cls._string_list(
                source_manifest.get(
                    "feature_columns"
                ),
                field_name=(
                    "feature_columns"
                ),
            )
        )

        cls._portable_feature_columns(
            source_feature_columns
        )

        target_columns = (
            cls._string_list(
                source_manifest.get(
                    "target_columns"
                ),
                field_name=(
                    "target_columns"
                ),
            )
        )

        dataset_filename = str(
            source_manifest.get(
                "dataset_filename",
                "",
            )
        )

        if (
            dataset_filename
            and
            dataset_filename
            !=
            source_dataset_path.name
        ):
            raise (
                PortableTrainingFeatureProjectionError(
                    "SOURCE_DATASET_FILENAME_MISMATCH"
                )
            )

        return (
            source_feature_columns,
            target_columns,
        )

    @classmethod
    def _source_manifest_candidate(
        cls,
        manifest_path: Path,
    ) -> tuple[
        Path,
        dict[str, Any],
    ] | None:

        try:

            manifest = (
                cls._load_json(
                    manifest_path
                )
            )

        except (
            PortableTrainingFeatureProjectionError,
            OSError,
        ):
            return None

        if (
            str(
                manifest.get(
                    "training_contract_version",
                    "",
                )
            )
            !=
            cls.SOURCE_CONTRACT
        ):
            return None

        if (
            str(
                manifest.get(
                    "dataset_id",
                    "",
                )
            )
            !=
            cls.EXPECTED_SOURCE_DATASET_ID
        ):
            return None

        if (
            str(
                manifest.get(
                    "dataset_sha256",
                    "",
                )
            )
            !=
            cls.EXPECTED_SOURCE_DATASET_SHA256
        ):
            return None

        dataset_filename = str(
            manifest.get(
                "dataset_filename",
                "",
            )
        ).strip()

        if not dataset_filename:
            return None

        dataset_path = (
            manifest_path.parent
            /
            dataset_filename
        )

        if not dataset_path.is_file():
            return None

        return (
            dataset_path,
            manifest,
        )

    def _discover_source(
        self,
    ) -> tuple[
        Path,
        Path,
        dict[str, Any],
    ]:

        search_root = (
            self.canonical_root
            /
            "training"
        )

        if not search_root.is_dir():

            search_root = (
                self.canonical_root
            )

        candidates: list[
            tuple[
                Path,
                Path,
                dict[str, Any],
            ]
        ] = []

        for manifest_path in (
            search_root.rglob(
                "*.manifest.json"
            )
        ):

            candidate = (
                self._source_manifest_candidate(
                    manifest_path
                )
            )

            if (
                candidate
                is None
            ):
                continue

            (
                dataset_path,
                manifest,
            ) = candidate

            try:

                manifest_sha256 = (
                    self._sha256_file(
                        manifest_path
                    )
                )

                dataset_sha256 = (
                    self._sha256_file(
                        dataset_path
                    )
                )

            except OSError:
                continue

            if (
                manifest_sha256
                !=
                self.EXPECTED_SOURCE_MANIFEST_SHA256
            ):
                continue

            if (
                dataset_sha256
                !=
                self.EXPECTED_SOURCE_DATASET_SHA256
            ):
                continue

            candidates.append(
                (
                    dataset_path,
                    manifest_path,
                    manifest,
                )
            )

        if (
            len(
                candidates
            )
            !=
            1
        ):
            raise (
                PortableTrainingFeatureProjectionError(
                    (
                        "FROZEN_V3_SOURCE_DISCOVERY_COUNT_INVALID:"
                        f"{len(candidates)}"
                    )
                )
            )

        return candidates[
            0
        ]

    @classmethod
    def _write_dataframe_content_addressed(
        cls,
        *,
        frame: pd.DataFrame,
        directory: Path,
    ) -> tuple[
        str,
        Path,
        str,
    ]:

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        file_descriptor, temp_name = (
            tempfile.mkstemp(
                prefix=(
                    ".portable_training_"
                ),
                suffix=".csv.tmp",
                dir=str(
                    directory
                ),
            )
        )

        os.close(
            file_descriptor
        )

        temp_path = Path(
            temp_name
        )

        try:

            with temp_path.open(
                "w",
                encoding="utf-8",
                newline="",
            ) as handle:

                frame.to_csv(
                    handle,
                    index=False,
                    lineterminator="\n",
                )

                handle.flush()

                os.fsync(
                    handle.fileno()
                )

            dataset_sha256 = (
                cls._sha256_file(
                    temp_path
                )
            )

            dataset_token = (
                dataset_sha256[
                    :24
                ]
            )

            dataset_id = (
                "portable_"
                +
                dataset_token
            )

            final_path = (
                directory
                /
                (
                    cls.DATASET_PREFIX
                    +
                    dataset_token
                    +
                    ".csv"
                )
            )

            if final_path.exists():

                existing_sha256 = (
                    cls._sha256_file(
                        final_path
                    )
                )

                if (
                    existing_sha256
                    !=
                    dataset_sha256
                ):
                    raise (
                        PortableTrainingFeatureProjectionError(
                            "PORTABLE_DATASET_IMMUTABLE_COLLISION"
                        )
                    )

                temp_path.unlink(
                    missing_ok=True
                )

            else:

                os.replace(
                    temp_path,
                    final_path,
                )

            return (
                dataset_id,
                final_path,
                dataset_sha256,
            )

        finally:

            if temp_path.exists():

                temp_path.unlink(
                    missing_ok=True
                )

    @staticmethod
    def _write_immutable_bytes(
        *,
        path: Path,
        payload: bytes,
    ) -> None:

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if path.exists():

            existing = (
                path.read_bytes()
            )

            if (
                existing
                !=
                payload
            ):
                raise (
                    PortableTrainingFeatureProjectionError(
                        "PORTABLE_MANIFEST_IMMUTABLE_COLLISION"
                    )
                )

            return

        file_descriptor, temp_name = (
            tempfile.mkstemp(
                prefix=".portable_manifest_",
                suffix=".tmp",
                dir=str(
                    path.parent
                ),
            )
        )

        temp_path = Path(
            temp_name
        )

        try:

            with os.fdopen(
                file_descriptor,
                "wb",
            ) as handle:

                handle.write(
                    payload
                )

                handle.flush()

                os.fsync(
                    handle.fileno()
                )

            os.replace(
                temp_path,
                path,
            )

        finally:

            if temp_path.exists():

                temp_path.unlink(
                    missing_ok=True
                )

    @classmethod
    def _build_manifest(
        cls,
        *,
        source_manifest: Mapping[
            str,
            Any,
        ],
        source_manifest_sha256: str,
        portable_dataset_id: str,
        portable_dataset_filename: str,
        portable_dataset_sha256: str,
        portable_feature_columns: Sequence[
            str
        ],
        row_count: int,
    ) -> dict[str, Any]:

        manifest = dict(
            source_manifest
        )

        source_dataset_id = str(
            source_manifest.get(
                "dataset_id",
                "",
            )
        )

        source_dataset_sha256 = str(
            source_manifest.get(
                "dataset_sha256",
                "",
            )
        )

        source_feature_columns = (
            cls._string_list(
                source_manifest.get(
                    "feature_columns"
                ),
                field_name=(
                    "feature_columns"
                ),
            )
        )

        manifest[
            "manifest_version"
        ] = (
            cls.MANIFEST_VERSION
        )

        manifest[
            "builder_version"
        ] = (
            cls.VERSION
        )

        manifest[
            "dataset_id"
        ] = (
            portable_dataset_id
        )

        manifest[
            "dataset_filename"
        ] = (
            portable_dataset_filename
        )

        manifest[
            "dataset_sha256"
        ] = (
            portable_dataset_sha256
        )

        manifest[
            "row_count"
        ] = int(
            row_count
        )

        manifest[
            "feature_count"
        ] = int(
            len(
                portable_feature_columns
            )
        )

        manifest[
            "feature_columns"
        ] = [
            str(
                feature
            )
            for feature
            in portable_feature_columns
        ]

        manifest[
            "source_training_matrix"
        ] = {
            "dataset_id": (
                source_dataset_id
            ),
            "dataset_sha256": (
                source_dataset_sha256
            ),
            "manifest_sha256": (
                source_manifest_sha256
            ),
            "training_contract_version": (
                cls.SOURCE_CONTRACT
            ),
            "feature_count": (
                cls.EXPECTED_PARENT_FEATURE_COUNT
            ),
            "feature_columns_sha256": (
                cls._sha256_bytes(
                    json.dumps(
                        source_feature_columns,
                        separators=(
                            ",",
                            ":",
                        ),
                        ensure_ascii=True,
                    ).encode(
                        "utf-8"
                    )
                )
            ),
        }

        manifest[
            "portable_feature_contract"
        ] = {
            "version": (
                cls.TARGET_CONTRACT
            ),
            "parent_contract": (
                cls.SOURCE_CONTRACT
            ),
            "parent_feature_count": (
                cls.EXPECTED_PARENT_FEATURE_COUNT
            ),
            "portable_feature_count": (
                cls.EXPECTED_PORTABLE_FEATURE_COUNT
            ),
            "operation": (
                "PARENT_FEATURE_SET_MINUS_EXPLICIT_DROPS"
            ),
            "dropped_features": list(
                cls.DROPPED_FEATURES
            ),
            "added_features": [],
            "retained_existing_broker_sensitive_feature": (
                cls.RETAINED_RELATIVE_VOLUME_FEATURE
            ),
            "spread_model_feature_present": (
                False
            ),
            "absolute_tick_volume_level_present": (
                False
            ),
            "contract_design_fingerprint": {
                "version": (
                    cls.CONTRACT_DESIGN_FINGERPRINT_VERSION
                ),
                "sha256": (
                    cls.CONTRACT_DESIGN_FINGERPRINT_SHA256
                ),
            },
        }

        manifest[
            "feature_projection"
        ] = {
            "projector_version": (
                cls.VERSION
            ),
            "source_feature_count": (
                cls.EXPECTED_PARENT_FEATURE_COUNT
            ),
            "output_feature_count": (
                cls.EXPECTED_PORTABLE_FEATURE_COUNT
            ),
            "dropped_feature_count": (
                len(
                    cls.DROPPED_FEATURES
                )
            ),
            "dropped_features": list(
                cls.DROPPED_FEATURES
            ),
            "added_feature_count": (
                0
            ),
            "added_features": [],
            "target_columns_changed": (
                False
            ),
            "row_count_changed": (
                False
            ),
            "decision_time_changed": (
                False
            ),
            "dataset_split_changed": (
                False
            ),
        }

        manifest[
            "training_contract_version"
        ] = (
            cls.TARGET_CONTRACT
        )

        manifest[
            "live_authorized"
        ] = (
            False
        )

        return manifest

    def project(
        self,
        *,
        source_dataset_path: str | Path | None = None,
        source_manifest_path: str | Path | None = None,
        output_directory: str | Path | None = None,
    ) -> PortableTrainingFeatureProjectionResult:

        if (
            source_dataset_path
            is None
            and
            source_manifest_path
            is None
        ):

            (
                resolved_dataset_path,
                resolved_manifest_path,
                source_manifest,
            ) = (
                self._discover_source()
            )

        elif (
            source_dataset_path
            is not None
            and
            source_manifest_path
            is not None
        ):

            resolved_dataset_path = Path(
                source_dataset_path
            )

            resolved_manifest_path = Path(
                source_manifest_path
            )

            if not resolved_dataset_path.is_file():
                raise (
                    PortableTrainingFeatureProjectionError(
                        "SOURCE_DATASET_NOT_FOUND"
                    )
                )

            if not resolved_manifest_path.is_file():
                raise (
                    PortableTrainingFeatureProjectionError(
                        "SOURCE_MANIFEST_NOT_FOUND"
                    )
                )

            source_manifest = (
                self._load_json(
                    resolved_manifest_path
                )
            )

        else:

            raise (
                PortableTrainingFeatureProjectionError(
                    "SOURCE_DATASET_AND_MANIFEST_MUST_BE_SUPPLIED_TOGETHER"
                )
            )

        (
            source_feature_columns,
            target_columns,
        ) = (
            self._validate_source_manifest(
                source_manifest=(
                    source_manifest
                ),
                source_dataset_path=(
                    resolved_dataset_path
                ),
                source_manifest_path=(
                    resolved_manifest_path
                ),
            )
        )

        try:

            source_frame = pd.read_csv(
                resolved_dataset_path
            )

        except Exception as exc:

            raise (
                PortableTrainingFeatureProjectionError(
                    "SOURCE_MATRIX_READ_FAILED"
                )
            ) from exc

        source_manifest_row_count = int(
            source_manifest.get(
                "row_count",
                -1,
            )
        )

        if (
            source_manifest_row_count
            !=
            len(
                source_frame
            )
        ):
            raise (
                PortableTrainingFeatureProjectionError(
                    "SOURCE_MATRIX_ROW_COUNT_MISMATCH"
                )
            )

        (
            projected_frame,
            portable_feature_columns,
        ) = (
            self._project_frame(
                source_frame=(
                    source_frame
                ),
                source_feature_columns=(
                    source_feature_columns
                ),
                target_columns=(
                    target_columns
                ),
            )
        )

        if output_directory is None:

            resolved_output_directory = (
                resolved_dataset_path.parent
                /
                self.OUTPUT_DIRECTORY_NAME
            )

        else:

            resolved_output_directory = Path(
                output_directory
            )

        (
            portable_dataset_id,
            portable_dataset_path,
            portable_dataset_sha256,
        ) = (
            self._write_dataframe_content_addressed(
                frame=(
                    projected_frame
                ),
                directory=(
                    resolved_output_directory
                ),
            )
        )

        source_manifest_sha256 = (
            self._sha256_file(
                resolved_manifest_path
            )
        )

        portable_manifest = (
            self._build_manifest(
                source_manifest=(
                    source_manifest
                ),
                source_manifest_sha256=(
                    source_manifest_sha256
                ),
                portable_dataset_id=(
                    portable_dataset_id
                ),
                portable_dataset_filename=(
                    portable_dataset_path.name
                ),
                portable_dataset_sha256=(
                    portable_dataset_sha256
                ),
                portable_feature_columns=(
                    portable_feature_columns
                ),
                row_count=(
                    len(
                        projected_frame
                    )
                ),
            )
        )

        portable_manifest_bytes = (
            self._canonical_json_bytes(
                portable_manifest
            )
        )

        portable_manifest_sha256 = (
            self._sha256_bytes(
                portable_manifest_bytes
            )
        )

        portable_manifest_path = (
            portable_dataset_path.with_suffix(
                ".manifest.json"
            )
        )

        self._write_immutable_bytes(
            path=(
                portable_manifest_path
            ),
            payload=(
                portable_manifest_bytes
            ),
        )

        source_dataset_id = str(
            source_manifest.get(
                "dataset_id",
                "",
            )
        )

        source_dataset_sha256 = str(
            source_manifest.get(
                "dataset_sha256",
                "",
            )
        )

        return (
            PortableTrainingFeatureProjectionResult(
                dataset_id=(
                    portable_dataset_id
                ),
                dataset_path=(
                    portable_dataset_path
                ),
                manifest_path=(
                    portable_manifest_path
                ),
                dataset_sha256=(
                    portable_dataset_sha256
                ),
                manifest_sha256=(
                    portable_manifest_sha256
                ),
                source_dataset_id=(
                    source_dataset_id
                ),
                source_dataset_sha256=(
                    source_dataset_sha256
                ),
                source_manifest_sha256=(
                    source_manifest_sha256
                ),
                row_count=int(
                    len(
                        projected_frame
                    )
                ),
                feature_count=int(
                    len(
                        portable_feature_columns
                    )
                ),
                dropped_feature_count=int(
                    len(
                        self.DROPPED_FEATURES
                    )
                ),
                training_contract_version=(
                    self.TARGET_CONTRACT
                ),
                live_authorized=(
                    False
                ),
            )
        )