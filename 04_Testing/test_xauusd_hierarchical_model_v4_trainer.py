from __future__ import annotations

import hashlib
import importlib
import json

from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
import pytest


context_module: Any = importlib.import_module(
    "02_AI.Common.instrument_context"
)

matrix_module: Any = importlib.import_module(
    "02_AI.Dataset.training_matrix_builder"
)

trainer_module: Any = importlib.import_module(
    "02_AI.Models.xauusd_hierarchical_model_v4_trainer"
)


InstrumentDefinition: Any = (
    context_module.InstrumentDefinition
)

InstrumentContext: Any = (
    context_module.InstrumentContext
)

TrainingMatrixBuilder: Any = (
    matrix_module.TrainingMatrixBuilder
)

Trainer: Any = (
    trainer_module.XAUUSDHierarchicalModelV4Trainer
)

TrainingError: Any = (
    trainer_module.XAUUSDHierarchicalModelV4TrainingError
)


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


def _context() -> Any:

    definition = InstrumentDefinition(
        canonical_symbol="XAUUSD",
        asset_class="METAL",
        broker_symbols=(
            "XAUUSDm",
        ),
        definition_version="1",
    )

    return InstrumentContext(
        definition=definition,
        broker_id="EXNESS",
        broker_symbol="XAUUSDm",
        account_scope_id=(
            "PRIMARY_DEMO"
        ),
        execution_environment="DEMO",
        contract_spec_id=(
            "EXNESS_XAUUSD_SPEC_TEST"
        ),
        data_schema_version=(
            "MARKET_V1"
        ),
        feature_contract_version=(
            "FEATURES_V1"
        ),
    )


def _target_name(
    target_id: int,
) -> str:

    return {
        -1: "SHORT",
        0: "NO_TRADE",
        1: "LONG",
    }[
        int(
            target_id
        )
    ]


def _build_fixture_frame() -> pd.DataFrame:

    rows: list[
        dict[
            str,
            Any,
        ]
    ] = []

    split_sizes = {
        "TRAIN": 180,
        "VALIDATION": 90,
        "TEST": 90,
    }

    offset = 0

    for (
        split,
        size,
    ) in split_sizes.items():

        for local_index in range(
            size
        ):

            target_id = (
                -1,
                0,
                1,
            )[
                local_index
                %
                3
            ]

            tradeable = int(
                target_id
                !=
                0
            )

            # Synthetic test-only predictors.
            # The purpose is trainer contract validation, not real market
            # performance estimation.
            phase = float(
                (
                    local_index
                    %
                    17
                )
                /
                17.0
            )

            rows.append(
                {
                    "time": (
                        pd.Timestamp(
                            "2025-01-01T00:00:00Z"
                        )
                        +
                        pd.Timedelta(
                            minutes=(
                                5
                                *
                                (
                                    offset
                                    +
                                    local_index
                                )
                            )
                        )
                    ).isoformat(),
                    "feature_tradeability": (
                        float(
                            tradeable
                        )
                        +
                        0.05
                        *
                        phase
                    ),
                    "feature_direction": (
                        float(
                            target_id
                        )
                        +
                        0.03
                        *
                        phase
                    ),
                    "feature_context": (
                        float(
                            (
                                local_index
                                %
                                11
                            )
                            -
                            5
                        )
                        /
                        10.0
                    ),
                    "target_class": (
                        _target_name(
                            target_id
                        )
                    ),
                    "target_class_id": (
                        int(
                            target_id
                        )
                    ),
                    "target_tradeable": (
                        tradeable
                    ),
                    "target_profit_atr": (
                        1.25
                    ),
                    "target_max_adverse_atr": (
                        0.75
                    ),
                    "dataset_split": (
                        split
                    ),
                    "pv_canonical_symbol": (
                        "XAUUSD"
                    ),
                    "pv_asset_class": (
                        "METAL"
                    ),
                    "pv_broker_id": (
                        "EXNESS"
                    ),
                    "pv_broker_symbol": (
                        "XAUUSDm"
                    ),
                    "pv_contract_spec_id": (
                        "EXNESS_XAUUSD_SPEC_TEST"
                    ),
                    "pv_data_schema_version": (
                        "MARKET_V1"
                    ),
                    "pv_feature_contract_version": (
                        "FEATURES_V1"
                    ),
                }
            )

        offset += size

    return pd.DataFrame(
        rows
    )


def _write_v3_fixture(
    *,
    canonical_root: Path,
    context: Any,
    mutate_manifest: (
        Callable[
            [
                dict[
                    str,
                    Any,
                ]
            ],
            None,
        ]
        |
        None
    ) = None,
    mutate_frame: (
        Callable[
            [
                pd.DataFrame
            ],
            None,
        ]
        |
        None
    ) = None,
) -> tuple[
    Path,
    Path,
]:

    learning_fingerprint = (
        TrainingMatrixBuilder
        .learning_scope_fingerprint(
            context
        )
    )

    directory = (
        canonical_root
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
        "XAUUSD_MTF_TRAINING_V3"
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    frame = (
        _build_fixture_frame()
    )

    if (
        mutate_frame
        is not None
    ):

        mutate_frame(
            frame
        )

    dataset_path = (
        directory
        /
        "fixture_v3.csv"
    )

    frame.to_csv(
        dataset_path,
        index=False,
        lineterminator="\n",
    )

    dataset_hash = (
        _sha256_file(
            dataset_path
        )
    )

    feature_columns = [
        "feature_tradeability",
        "feature_direction",
        "feature_context",
    ]

    manifest: dict[
        str,
        Any,
    ] = {
        "manifest_version": (
            "PULSEVIPER_TRAINING_MATRIX_MANIFEST_V3"
        ),
        "builder_version": (
            "TEST"
        ),
        "dataset_kind": (
            "XAUUSD_MULTI_TIMEFRAME_CLASSIFICATION_MATRIX"
        ),
        "dataset_id": (
            "train_"
            +
            dataset_hash[
                :24
            ]
        ),
        "dataset_filename": (
            dataset_path.name
        ),
        "dataset_sha256": (
            dataset_hash
        ),
        "row_count": int(
            len(
                frame
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
        "target_columns": [
            "target_class",
            "target_class_id",
            "target_tradeable",
            "target_profit_atr",
            "target_max_adverse_atr",
        ],
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
                "CLEAN_DIRECTIONAL_EXCURSION_V2"
            ),
            "profit_atr": (
                1.25
            ),
            "max_adverse_atr": (
                0.75
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
            "M5"
        ),
        "context_timeframes": [
            "M15",
            "M30",
            "H1",
            "H4",
            "D1",
        ],
        "learning_scope_fingerprint": (
            learning_fingerprint
        ),
        "source_historical_snapshots": {
            "M5": {
                "dataset_id": (
                    "historical_fixture"
                ),
                "end_time": (
                    "2025-12-31T23:55:00Z"
                ),
            },
        },
        "source_training_matrix": {
            "dataset_id": (
                "fixture_v2"
            ),
            "dataset_sha256": (
                "0"
                *
                64
            ),
            "manifest_sha256": (
                "1"
                *
                64
            ),
            "training_contract_version": (
                "XAUUSD_MTF_TRAINING_V2"
            ),
        },
        "feature_availability_rule": (
            "ALL_FEATURES_CAUSAL_AT_DECISION_TIME"
        ),
        "target_future_data_rule": (
            "FUTURE_DATA_ALLOWED_ONLY_IN_TARGET_COLUMNS"
        ),
        "training_contract_version": (
            "XAUUSD_MTF_TRAINING_V3"
        ),
        "live_authorized": False,
    }

    if (
        mutate_manifest
        is not None
    ):

        mutate_manifest(
            manifest
        )

    manifest_path = (
        directory
        /
        "fixture_v3.manifest.json"
    )

    manifest_path.write_text(
        (
            json.dumps(
                manifest,
                indent=2,
                sort_keys=True,
            )
            +
            "\n"
        ),
        encoding="utf-8",
    )

    return (
        dataset_path,
        manifest_path,
    )


def test_combined_probability_contract_uses_hierarchical_formula() -> None:

    stage_a = np.asarray(
        [
            [
                0.20,
                0.80,
            ],
            [
                0.70,
                0.30,
            ],
        ],
        dtype=np.float64,
    )

    stage_b = np.asarray(
        [
            [
                0.25,
                0.75,
            ],
            [
                0.60,
                0.40,
            ],
        ],
        dtype=np.float64,
    )

    combined = (
        Trainer.combine_probabilities(
            stage_a_probabilities=(
                stage_a
            ),
            stage_b_probabilities=(
                stage_b
            ),
        )
    )

    expected = np.asarray(
        [
            [
                (
                    0.80
                    *
                    0.25
                ),
                0.20,
                (
                    0.80
                    *
                    0.75
                ),
            ],
            [
                (
                    0.30
                    *
                    0.60
                ),
                0.70,
                (
                    0.30
                    *
                    0.40
                ),
            ],
        ],
        dtype=np.float64,
    )

    assert np.allclose(
        combined,
        expected,
        rtol=0.0,
        atol=1e-12,
    )

    assert np.allclose(
        combined.sum(
            axis=1
        ),
        1.0,
        rtol=0.0,
        atol=1e-12,
    )


def test_v4_trains_two_stages_and_writes_immutable_artifacts(
    tmp_path: Path,
) -> None:

    context = (
        _context()
    )

    _write_v3_fixture(
        canonical_root=(
            tmp_path
        ),
        context=(
            context
        ),
    )

    trainer = Trainer(
        canonical_root=(
            tmp_path
        )
    )

    result = trainer.train(
        context=context,
        random_state=7,
        max_iter=35,
        learning_rate=0.08,
        max_leaf_nodes=15,
        min_samples_leaf=5,
        l2_regularization=0.5,
        stage_a_class_balance_power=(
            0.20
        ),
        stage_b_class_balance_power=(
            0.20
        ),
    )

    assert (
        result.model_id
        ==
        "XAUUSD_MODEL_v4_HIERARCHICAL"
    )

    assert (
        result.live_authorized
        is False
    )

    for path in (
        result.stage_a_model_path,
        result.stage_a_scaler_path,
        result.stage_b_model_path,
        result.stage_b_scaler_path,
        result.manifest_path,
    ):

        assert path.is_file()

    assert (
        result.stage_a_model_sha256
        ==
        _sha256_file(
            result.stage_a_model_path
        )
    )

    assert (
        result.stage_a_scaler_sha256
        ==
        _sha256_file(
            result.stage_a_scaler_path
        )
    )

    assert (
        result.stage_b_model_sha256
        ==
        _sha256_file(
            result.stage_b_model_path
        )
    )

    assert (
        result.stage_b_scaler_sha256
        ==
        _sha256_file(
            result.stage_b_scaler_path
        )
    )

    assert (
        result.feature_count
        ==
        3
    )

    assert (
        result.train_rows
        ==
        180
    )

    assert (
        result.validation_rows
        ==
        90
    )

    assert (
        result.test_rows
        ==
        90
    )

    assert (
        result.train_tradeable_rows
        ==
        120
    )

    assert (
        result.validation_tradeable_rows
        ==
        60
    )

    assert (
        result.test_tradeable_rows
        ==
        60
    )

    assert set(
        result.split_metrics
    ) == {
        "TRAIN",
        "VALIDATION",
        "TEST",
    }

    for split in (
        "TRAIN",
        "VALIDATION",
        "TEST",
    ):

        metrics = (
            result.split_metrics[
                split
            ]
        )

        assert set(
            metrics
        ) == {
            "stage_a_tradeability",
            "stage_b_direction",
            "combined",
        }

        assert (
            metrics[
                "stage_a_tradeability"
            ][
                "rows"
            ]
            >
            0
        )

        assert (
            metrics[
                "stage_b_direction"
            ][
                "rows"
            ]
            >
            0
        )

        assert (
            metrics[
                "combined"
            ][
                "rows"
            ]
            >
            0
        )

        assert (
            "binary_probability_ece"
            in
            metrics[
                "stage_a_tradeability"
            ]
        )

        assert (
            "binary_probability_ece"
            in
            metrics[
                "stage_b_direction"
            ]
        )

        assert (
            "multiclass_brier"
            in
            metrics[
                "combined"
            ]
        )

        assert (
            "top_class_ece"
            in
            metrics[
                "combined"
            ]
        )

        assert (
            "selective_confidence"
            in
            metrics[
                "combined"
            ]
        )

        assert (
            "trade_selection"
            in
            metrics[
                "combined"
            ]
        )

    manifest = json.loads(
        result.manifest_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        manifest[
            "manifest_version"
        ]
        ==
        "PULSEVIPER_HIERARCHICAL_MODEL_MANIFEST_V1"
    )

    assert (
        manifest[
            "training_dataset"
        ][
            "training_contract_version"
        ]
        ==
        "XAUUSD_MTF_TRAINING_V3"
    )

    assert (
        manifest[
            "training_dataset"
        ][
            "source_target_contract"
        ]
        ==
        "XAUUSD_MTF_TRAINING_V2"
    )

    assert (
        manifest[
            "training_dataset"
        ][
            "target_label_contract"
        ]
        ==
        {
            "name": (
                "CLEAN_DIRECTIONAL_EXCURSION_V2"
            ),
            "profit_atr": (
                1.25
            ),
            "max_adverse_atr": (
                0.75
            ),
        }
    )

    assert (
        manifest[
            "final_probability_contract"
        ][
            "prob_no_trade"
        ]
        ==
        "1-P(TRADEABLE)"
    )

    assert (
        manifest[
            "research_policy"
        ][
            "test_usage"
        ]
        ==
        "FINAL_HOLDOUT_EVALUATION_ONLY"
    )

    assert (
        manifest[
            "research_policy"
        ][
            "threshold_selection"
        ]
        ==
        "NONE_IN_THIS_TRAINER"
    )

    assert (
        manifest[
            "live_authorized"
        ]
        is False
    )

    expected_scope = (
        "scope_"
        +
        TrainingMatrixBuilder
        .learning_scope_fingerprint(
            context
        )
    )

    assert expected_scope in {
        path.name
        for path
        in result.output_directory.parents
    }


def test_v4_rejects_non_frozen_v2_target_lineage_before_artifacts(
    tmp_path: Path,
) -> None:

    context = (
        _context()
    )

    def mutate(
        manifest: dict[
            str,
            Any,
        ],
    ) -> None:

        manifest[
            "source_training_matrix"
        ][
            "training_contract_version"
        ] = (
            "XAUUSD_MTF_TRAINING_V1"
        )

    _write_v3_fixture(
        canonical_root=(
            tmp_path
        ),
        context=(
            context
        ),
        mutate_manifest=(
            mutate
        ),
    )

    trainer = Trainer(
        canonical_root=(
            tmp_path
        )
    )

    with pytest.raises(
        TrainingError,
        match=(
            "V3_SOURCE_TARGET_CONTRACT_MISMATCH"
        ),
    ):

        trainer.train(
            context=context,
            max_iter=10,
            min_samples_leaf=5,
        )

    models_root = (
        tmp_path
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
            TrainingMatrixBuilder
            .learning_scope_fingerprint(
                context
            )
        )
        /
        "models"
    )

    assert not models_root.exists()


def test_v4_rejects_target_tradeable_linkage_mismatch(
    tmp_path: Path,
) -> None:

    context = (
        _context()
    )

    def mutate_frame(
        frame: pd.DataFrame,
    ) -> None:

        frame.loc[
            frame.index[
                0
            ],
            "target_tradeable",
        ] = 0

    _write_v3_fixture(
        canonical_root=(
            tmp_path
        ),
        context=(
            context
        ),
        mutate_frame=(
            mutate_frame
        ),
    )

    trainer = Trainer(
        canonical_root=(
            tmp_path
        )
    )

    with pytest.raises(
        TrainingError,
        match=(
            "TARGET_TRADEABLE_LINKAGE_MISMATCH"
        ),
    ):

        trainer.train(
            context=context,
            max_iter=10,
            min_samples_leaf=5,
        )