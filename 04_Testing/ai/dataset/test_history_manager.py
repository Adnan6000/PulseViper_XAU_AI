import importlib

import pandas as pd


context_module = importlib.import_module(
    "02_AI.Common.instrument_context"
)

exporter_module = importlib.import_module(
    "02_AI.Dataset.export_dataset"
)

history_module = importlib.import_module(
    "02_AI.Dataset.history_manager"
)

InstrumentDefinition = (
    context_module.InstrumentDefinition
)

InstrumentContext = (
    context_module.InstrumentContext
)

DatasetExporter = (
    exporter_module.DatasetExporter
)

HistoryManager = (
    history_module.HistoryManager
)


def make_context():

    definition = InstrumentDefinition(
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

    return InstrumentContext(
        definition=definition,
        broker_id="EXNESS",
        broker_symbol="XAUUSDm",
        account_scope_id="PRIMARY_DEMO",
        execution_environment="DEMO",
        contract_spec_id=(
            "EXNESS_XAUUSD_SPEC_D133951851B554C9"
        ),
        data_schema_version="MARKET_V1",
        feature_contract_version="FEATURES_V1",
    )


class FakeFetcher:

    def __init__(self):

        self.last_resolved_symbol = ""

        self.calls = []


    def fetch(
        self,
        *,
        symbol,
        timeframe,
        bars,
    ):

        self.last_resolved_symbol = (
            symbol
        )

        self.calls.append(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "bars": bars,
            }
        )

        return pd.DataFrame(
            {
                "time": [
                    pd.Timestamp(
                        "2026-01-01 00:00:00"
                    ),
                    pd.Timestamp(
                        "2026-01-01 00:01:00"
                    ),
                ],
                "open": [
                    4300.0,
                    4301.0,
                ],
                "high": [
                    4301.0,
                    4302.0,
                ],
                "low": [
                    4299.0,
                    4300.0,
                ],
                "close": [
                    4300.5,
                    4301.5,
                ],
                "tick_volume": [
                    100,
                    110,
                ],
                "spread": [
                    20,
                    20,
                ],
                "real_volume": [
                    0,
                    0,
                ],
            }
        )


def test_history(
    tmp_path,
):

    fetcher = FakeFetcher()

    history = HistoryManager(
        fetcher=fetcher,
        exporter=DatasetExporter(
            output_root=tmp_path
        ),
    )

    files = history.build_dataset(
        context=make_context(),
        bars=100,
    )

    assert len(files) == 7
    assert len(fetcher.calls) == 7

    assert all(
        item.dataset_path.is_file()
        for item in files
    )

    assert all(
        tmp_path.resolve()
        in item.dataset_path.resolve().parents
        for item in files
    )
