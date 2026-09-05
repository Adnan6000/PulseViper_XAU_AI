from __future__ import annotations

import importlib
import json

from pathlib import Path
from typing import Any

import pandas as pd
import pytest


pytestmark = pytest.mark.offline


context_module: Any = importlib.import_module(
    "02_AI.Common.instrument_context"
)

export_module: Any = importlib.import_module(
    "02_AI.Dataset.export_dataset"
)

manager_module: Any = importlib.import_module(
    "02_AI.Dataset.history_manager"
)


InstrumentDefinition: Any = (
    context_module.InstrumentDefinition
)

InstrumentContext: Any = (
    context_module.InstrumentContext
)

DatasetExporter: Any = (
    export_module.DatasetExporter
)

DatasetMaterializationError: Any = (
    export_module.DatasetMaterializationError
)

HistoryManager: Any = (
    manager_module.HistoryManager
)


def make_context(
    *,
    broker_symbol: str = "XAUUSDm",
    contract_spec_id: str = (
        "EXNESS_XAUUSD_SPEC_D133951851B554C9"
    ),
) -> Any:

    definition = (
        InstrumentDefinition(
            canonical_symbol="XAUUSD",
            asset_class="METAL",
            broker_symbols=(
                "XAUUSDm",
                "XAUUSD",
            ),
            definition_version=(
                "XAUUSD_BROKER_ALIASES_V1"
            ),
        )
    )

    return InstrumentContext(
        definition=definition,
        broker_id="EXNESS",
        broker_symbol=broker_symbol,
        account_scope_id="PRIMARY_DEMO",
        execution_environment="DEMO",
        contract_spec_id=(
            contract_spec_id
        ),
        data_schema_version="MARKET_V1",
        feature_contract_version="FEATURES_V1",
    )


def sample_frame() -> pd.DataFrame:

    return pd.DataFrame(
        {
            "time": pd.to_datetime(
                [
                    "2026-08-15 10:00:00",
                    "2026-08-15 10:01:00",
                    "2026-08-15 10:02:00",
                ]
            ),
            "open": [
                4330.0,
                4331.0,
                4332.0,
            ],
            "high": [
                4332.0,
                4333.0,
                4334.0,
            ],
            "low": [
                4329.0,
                4330.0,
                4331.0,
            ],
            "close": [
                4331.0,
                4332.0,
                4333.0,
            ],
            "tick_volume": [
                100,
                120,
                140,
            ],
            "spread": [
                30,
                31,
                29,
            ],
            "real_volume": [
                0,
                0,
                0,
            ],
        }
    )


def source_metadata() -> dict[str, Any]:

    return {
        "source": "TEST",
        "requested_symbol": "XAUUSDm",
        "resolved_symbol": "XAUUSDm",
        "timeframe": "M1",
        "returned_bars": 3,
    }


def test_materializes_identity_stamped_dataset_and_manifest(
    tmp_path,
):

    context = make_context()

    exporter = DatasetExporter(
        output_root=tmp_path
    )

    result = (
        exporter.materialize_history(
            dataframe=sample_frame(),
            context=context,
            source_metadata=(
                source_metadata()
            ),
        )
    )

    assert result.dataset_path.is_file()
    assert result.manifest_path.is_file()

    assert (
        "Instruments"
        in result.dataset_path.parts
    )

    assert (
        "XAUUSD"
        in result.dataset_path.parts
    )

    assert (
        "execution"
        in result.dataset_path.parts
    )

    stored = pd.read_csv(
        result.dataset_path
    )

    assert bool(
        stored[
            "pv_canonical_symbol"
        ]
        .eq(
            "XAUUSD"
        )
        .all()
    )

    assert bool(
        stored[
            "pv_broker_symbol"
        ]
        .eq(
            "XAUUSDm"
        )
        .all()
    )

    manifest = json.loads(
        result.manifest_path.read_text(
            encoding="utf-8"
        )
    )

    assert (
        manifest[
            "dataset_sha256"
        ]
        ==
        result.dataset_sha256
    )

    assert (
        manifest[
            "instrument_identity"
        ][
            "canonical_symbol"
        ]
        ==
        "XAUUSD"
    )

    assert (
        manifest[
            "live_authorized"
        ]
        is False
    )


def test_same_dataset_retry_is_idempotent(
    tmp_path,
):

    exporter = DatasetExporter(
        output_root=tmp_path
    )

    context = make_context()

    first = (
        exporter.materialize_history(
            dataframe=sample_frame(),
            context=context,
            source_metadata=(
                source_metadata()
            ),
        )
    )

    second = (
        exporter.materialize_history(
            dataframe=sample_frame(),
            context=context,
            source_metadata=(
                source_metadata()
            ),
        )
    )

    assert (
        first.dataset_path
        ==
        second.dataset_path
    )

    assert (
        second.reused_existing_dataset
        is True
    )

    assert (
        second.reused_existing_manifest
        is True
    )


def test_wrong_resolved_symbol_fails_closed(
    tmp_path,
):

    metadata = (
        source_metadata()
    )

    metadata[
        "resolved_symbol"
    ] = "BTCUSDm"

    with pytest.raises(
        DatasetMaterializationError,
        match=(
            "SOURCE_BROKER_SYMBOL_CONTEXT_MISMATCH"
        ),
    ):

        DatasetExporter(
            output_root=tmp_path
        ).materialize_history(
            dataframe=sample_frame(),
            context=make_context(),
            source_metadata=metadata,
        )


def test_contract_change_changes_namespace(
    tmp_path,
):

    exporter = DatasetExporter(
        output_root=tmp_path
    )

    first = (
        exporter.materialize_history(
            dataframe=sample_frame(),
            context=make_context(
                contract_spec_id="SPEC_A"
            ),
            source_metadata=(
                source_metadata()
            ),
        )
    )

    second = (
        exporter.materialize_history(
            dataframe=sample_frame(),
            context=make_context(
                contract_spec_id="SPEC_B"
            ),
            source_metadata=(
                source_metadata()
            ),
        )
    )

    assert (
        first.dataset_path
        !=
        second.dataset_path
    )


class FakeFetcher:

    def __init__(
        self,
        *,
        resolved_symbol: str = "XAUUSDm",
    ) -> None:

        self.last_resolved_symbol = ""

        self.resolved_symbol = (
            resolved_symbol
        )

        self.calls: list[
            tuple[
                str,
                int,
                int,
            ]
        ] = []

    def fetch(
        self,
        *,
        symbol: str,
        timeframe: int,
        bars: int,
    ) -> pd.DataFrame:

        self.calls.append(
            (
                symbol,
                timeframe,
                bars,
            )
        )

        self.last_resolved_symbol = (
            self.resolved_symbol
        )

        return sample_frame()


def test_manager_builds_selected_timeframes(
    tmp_path,
):

    fetcher = FakeFetcher()

    manager = HistoryManager(
        fetcher=fetcher,
        exporter=DatasetExporter(
            output_root=tmp_path
        ),
    )

    results = manager.build_dataset(
        context=make_context(),
        bars=100,
        timeframes=(
            "M1",
            "M5",
        ),
    )

    assert len(
        results
    ) == 2

    assert len(
        fetcher.calls
    ) == 2

    assert {
        result.timeframe
        for result
        in results
    } == {
        "M1",
        "M5",
    }


def test_manager_rejects_broker_resolution_drift(
    tmp_path,
):

    manager = HistoryManager(
        fetcher=FakeFetcher(
            resolved_symbol="XAUUSD"
        ),
        exporter=DatasetExporter(
            output_root=tmp_path
        ),
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "BROKER_SYMBOL_CONTEXT_DRIFT"
        ),
    ):

        manager.build_dataset(
            context=make_context(),
            bars=100,
            timeframes=(
                "M1",
            ),
        )


def test_manager_rejects_requested_symbol_mismatch(
    tmp_path,
):

    manager = HistoryManager(
        fetcher=FakeFetcher(),
        exporter=DatasetExporter(
            output_root=tmp_path
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "does not match"
        ),
    ):

        manager.build_dataset(
            context=make_context(),
            symbol="BTCUSDm",
            bars=100,
            timeframes=(
                "M1",
            ),
        )