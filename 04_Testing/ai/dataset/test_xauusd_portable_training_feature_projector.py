from __future__ import annotations

import importlib
import json

from pathlib import Path

import pandas as pd
import pytest


projector_module = importlib.import_module(
    "02_AI.Dataset.portable_training_feature_projector"
)


PortableTrainingFeatureProjector = (
    projector_module
    .PortableTrainingFeatureProjector
)

PortableTrainingFeatureProjectionError = (
    projector_module
    .PortableTrainingFeatureProjectionError
)


def _source_feature_columns() -> list[str]:

    ordinary_feature_count = (
        PortableTrainingFeatureProjector
        .EXPECTED_PARENT_FEATURE_COUNT
        -
        3
    )

    ordinary_features = [
        (
            "fixture_feature_"
            +
            f"{index:03d}"
        )
        for index
        in range(
            ordinary_feature_count
        )
    ]

    features = [
        ordinary_features[
            0
        ],
        PortableTrainingFeatureProjector.DROPPED_FEATURES[
            0
        ],
        ordinary_features[
            1
        ],
        PortableTrainingFeatureProjector.RETAINED_RELATIVE_VOLUME_FEATURE,
        ordinary_features[
            2
        ],
        PortableTrainingFeatureProjector.DROPPED_FEATURES[
            1
        ],
        *ordinary_features[
            3:
        ],
    ]

    assert (
        len(
            features
        )
        ==
        PortableTrainingFeatureProjector
        .EXPECTED_PARENT_FEATURE_COUNT
    )

    assert (
        len(
            set(
                features
            )
        )
        ==
        len(
            features
        )
    )

    return features


def _fixture_frame(
) -> tuple[
    pd.DataFrame,
    list[str],
    list[str],
]:

    features = (
        _source_feature_columns()
    )

    target_columns = [
        "target_class",
        "target_tradeable",
    ]

    data: dict[
        str,
        list[object],
    ] = {
        "decision_time": [
            "2025-01-01T00:00:00+00:00",
            "2025-01-01T00:05:00+00:00",
            "2025-01-01T00:10:00+00:00",
        ],
        "dataset_split": [
            "TRAIN",
            "VALIDATION",
            "TEST",
        ],
    }

    for index, feature in enumerate(
        features
    ):

        data[
            feature
        ] = [
            float(
                index
            ),
            float(
                index
                +
                1
            ),
            float(
                index
                +
                2
            ),
        ]

    data[
        "target_class"
    ] = [
        -1,
        0,
        1,
    ]

    data[
        "target_tradeable"
    ] = [
        1,
        0,
        1,
    ]

    frame = pd.DataFrame(
        data
    )

    return (
        frame,
        features,
        target_columns,
    )


def test_portable_feature_columns_drop_exactly_two(
) -> None:

    source_features = (
        _source_feature_columns()
    )

    portable = (
        PortableTrainingFeatureProjector
        ._portable_feature_columns(
            source_features
        )
    )

    assert (
        len(
            portable
        )
        ==
        331
    )

    assert (
        "m5_spread_points"
        not in
        portable
    )

    assert (
        "m5_tick_volume_log1p"
        not in
        portable
    )

    assert (
        "m5_tick_volume_ratio20"
        in
        portable
    )

    expected = [
        feature
        for feature
        in source_features
        if feature
        not in {
            "m5_spread_points",
            "m5_tick_volume_log1p",
        }
    ]

    assert (
        portable
        ==
        expected
    )


def test_portable_feature_columns_reject_missing_drop_feature(
) -> None:

    source_features = (
        _source_feature_columns()
    )

    source_features[
        source_features.index(
            "m5_spread_points"
        )
    ] = (
        "replacement_fixture_feature"
    )

    with pytest.raises(
        PortableTrainingFeatureProjectionError,
        match=(
            "DROP_FEATURE_NOT_IN_PARENT_CONTRACT"
        ),
    ):

        (
            PortableTrainingFeatureProjector
            ._portable_feature_columns(
                source_features
            )
        )


def test_project_frame_preserves_rows_targets_split_and_order(
) -> None:

    (
        source_frame,
        source_features,
        target_columns,
    ) = (
        _fixture_frame()
    )

    (
        projected,
        portable_features,
    ) = (
        PortableTrainingFeatureProjector
        ._project_frame(
            source_frame=(
                source_frame
            ),
            source_feature_columns=(
                source_features
            ),
            target_columns=(
                target_columns
            ),
        )
    )

    assert (
        len(
            projected
        )
        ==
        len(
            source_frame
        )
    )

    assert (
        len(
            portable_features
        )
        ==
        331
    )

    assert (
        "m5_spread_points"
        not in
        projected.columns
    )

    assert (
        "m5_tick_volume_log1p"
        not in
        projected.columns
    )

    assert (
        "m5_tick_volume_ratio20"
        in
        projected.columns
    )

    assert (
        projected[
            "decision_time"
        ].tolist()
        ==
        source_frame[
            "decision_time"
        ].tolist()
    )

    assert (
        projected[
            "dataset_split"
        ].tolist()
        ==
        source_frame[
            "dataset_split"
        ].tolist()
    )

    assert (
        projected[
            "target_class"
        ].tolist()
        ==
        source_frame[
            "target_class"
        ].tolist()
    )

    assert (
        projected[
            "target_tradeable"
        ].tolist()
        ==
        source_frame[
            "target_tradeable"
        ].tolist()
    )

    expected_columns = [
        column
        for column
        in source_frame.columns
        if column
        not in {
            "m5_spread_points",
            "m5_tick_volume_log1p",
        }
    ]

    assert (
        projected.columns.tolist()
        ==
        expected_columns
    )


def test_project_frame_rejects_duplicate_decision_time(
) -> None:

    (
        source_frame,
        source_features,
        target_columns,
    ) = (
        _fixture_frame()
    )

    source_frame.loc[
        1,
        "decision_time",
    ] = (
        source_frame.loc[
            0,
            "decision_time",
        ]
    )

    with pytest.raises(
        PortableTrainingFeatureProjectionError,
        match=(
            "PROJECTED_MATRIX_DUPLICATE_DECISION_TIME"
        ),
    ):

        (
            PortableTrainingFeatureProjector
            ._project_frame(
                source_frame=(
                    source_frame
                ),
                source_feature_columns=(
                    source_features
                ),
                target_columns=(
                    target_columns
                ),
            )
        )


def test_build_manifest_preserves_parent_metadata_and_changes_contract(
) -> None:

    source_features = (
        _source_feature_columns()
    )

    portable_features = (
        PortableTrainingFeatureProjector
        ._portable_feature_columns(
            source_features
        )
    )

    source_manifest = {
        "manifest_version": (
            "PULSEVIPER_TRAINING_MATRIX_MANIFEST_V3"
        ),
        "builder_version": (
            "fixture"
        ),
        "dataset_kind": (
            "XAUUSD_MULTI_TIMEFRAME_CLASSIFICATION_MATRIX"
        ),
        "dataset_id": (
            "fixture_source_dataset"
        ),
        "dataset_filename": (
            "fixture.csv"
        ),
        "dataset_sha256": (
            "a"
            *
            64
        ),
        "row_count": (
            3
        ),
        "feature_count": (
            333
        ),
        "feature_columns": (
            source_features
        ),
        "target_columns": [
            "target_class",
            "target_tradeable",
        ],
        "target_label_contract": (
            "CLEAN_DIRECTIONAL_EXCURSION_V2"
        ),
        "split_purge_bars": (
            12
        ),
        "learning_scope_fingerprint": (
            "fixture_scope"
        ),
        "source_historical_snapshots": {
            "M5": {
                "dataset_id": (
                    "fixture_hist"
                )
            }
        },
        "training_contract_version": (
            "XAUUSD_MTF_TRAINING_V3"
        ),
        "live_authorized": (
            False
        ),
    }

    manifest = (
        PortableTrainingFeatureProjector
        ._build_manifest(
            source_manifest=(
                source_manifest
            ),
            source_manifest_sha256=(
                "b"
                *
                64
            ),
            portable_dataset_id=(
                "portable_fixture"
            ),
            portable_dataset_filename=(
                "portable_fixture.csv"
            ),
            portable_dataset_sha256=(
                "c"
                *
                64
            ),
            portable_feature_columns=(
                portable_features
            ),
            row_count=(
                3
            ),
        )
    )

    assert (
        manifest[
            "training_contract_version"
        ]
        ==
        "XAUUSD_MTF_PORTABLE_FEATURE_V1"
    )

    assert (
        manifest[
            "feature_count"
        ]
        ==
        331
    )

    assert (
        manifest[
            "feature_columns"
        ]
        ==
        portable_features
    )

    assert (
        manifest[
            "target_columns"
        ]
        ==
        source_manifest[
            "target_columns"
        ]
    )

    assert (
        manifest[
            "target_label_contract"
        ]
        ==
        source_manifest[
            "target_label_contract"
        ]
    )

    assert (
        manifest[
            "split_purge_bars"
        ]
        ==
        source_manifest[
            "split_purge_bars"
        ]
    )

    assert (
        manifest[
            "learning_scope_fingerprint"
        ]
        ==
        source_manifest[
            "learning_scope_fingerprint"
        ]
    )

    assert (
        manifest[
            "source_historical_snapshots"
        ]
        ==
        source_manifest[
            "source_historical_snapshots"
        ]
    )

    assert (
        manifest[
            "source_training_matrix"
        ][
            "dataset_id"
        ]
        ==
        "fixture_source_dataset"
    )

    assert (
        manifest[
            "source_training_matrix"
        ][
            "dataset_sha256"
        ]
        ==
        (
            "a"
            *
            64
        )
    )

    assert (
        manifest[
            "source_training_matrix"
        ][
            "manifest_sha256"
        ]
        ==
        (
            "b"
            *
            64
        )
    )

    portable_contract = (
        manifest[
            "portable_feature_contract"
        ]
    )

    assert (
        portable_contract[
            "dropped_features"
        ]
        ==
        [
            "m5_spread_points",
            "m5_tick_volume_log1p",
        ]
    )

    assert (
        portable_contract[
            "added_features"
        ]
        ==
        []
    )

    assert (
        portable_contract[
            "retained_existing_broker_sensitive_feature"
        ]
        ==
        "m5_tick_volume_ratio20"
    )

    assert (
        manifest[
            "live_authorized"
        ]
        is
        False
    )


def test_content_addressed_dataset_write_is_idempotent(
    tmp_path: Path,
) -> None:

    frame = pd.DataFrame(
        {
            "decision_time": [
                "2025-01-01T00:00:00+00:00",
                "2025-01-01T00:05:00+00:00",
            ],
            "value": [
                1.0,
                2.0,
            ],
        }
    )

    first = (
        PortableTrainingFeatureProjector
        ._write_dataframe_content_addressed(
            frame=(
                frame
            ),
            directory=(
                tmp_path
            ),
        )
    )

    second = (
        PortableTrainingFeatureProjector
        ._write_dataframe_content_addressed(
            frame=(
                frame
            ),
            directory=(
                tmp_path
            ),
        )
    )

    assert (
        first
        ==
        second
    )

    (
        dataset_id,
        dataset_path,
        dataset_sha256,
    ) = first

    assert (
        dataset_id.startswith(
            "portable_"
        )
    )

    assert (
        dataset_path.is_file()
    )

    assert (
        len(
            dataset_sha256
        )
        ==
        64
    )


def test_immutable_manifest_write_rejects_collision(
    tmp_path: Path,
) -> None:

    path = (
        tmp_path
        /
        "fixture.manifest.json"
    )

    first_payload = json.dumps(
        {
            "value": (
                1
            )
        },
        sort_keys=True,
    ).encode(
        "utf-8"
    )

    second_payload = json.dumps(
        {
            "value": (
                2
            )
        },
        sort_keys=True,
    ).encode(
        "utf-8"
    )

    (
        PortableTrainingFeatureProjector
        ._write_immutable_bytes(
            path=(
                path
            ),
            payload=(
                first_payload
            ),
        )
    )

    (
        PortableTrainingFeatureProjector
        ._write_immutable_bytes(
            path=(
                path
            ),
            payload=(
                first_payload
            ),
        )
    )

    with pytest.raises(
        PortableTrainingFeatureProjectionError,
        match=(
            "PORTABLE_MANIFEST_IMMUTABLE_COLLISION"
        ),
    ):

        (
            PortableTrainingFeatureProjector
            ._write_immutable_bytes(
                path=(
                    path
                ),
                payload=(
                    second_payload
                ),
            )
        )