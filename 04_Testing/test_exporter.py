import importlib

import pandas as pd


context_module = importlib.import_module(
    "02_AI.Common.instrument_context"
)

exporter_module = importlib.import_module(
    "02_AI.Dataset.export_dataset"
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


def make_dataframe():

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


def make_source_metadata(
    dataframe,
    context,
):

    return {
        "source": "TEST_FIXTURE",
        "requested_symbol": (
            context.broker_symbol
        ),
        "resolved_symbol": (
            context.broker_symbol
        ),
        "canonical_symbol": (
            context.canonical_symbol
        ),
        "asset_class": (
            context.asset_class
        ),
        "broker_id": (
            context.broker_id
        ),
        "account_scope_id": (
            context.account_scope_id
        ),
        "execution_environment": (
            context.execution_environment
        ),
        "contract_spec_id": (
            context.contract_spec_id
        ),
        "data_schema_version": (
            context.data_schema_version
        ),
        "feature_contract_version": (
            context.feature_contract_version
        ),
        "timeframe": "M1",
        "requested_bars": len(
            dataframe
        ),
        "returned_bars": len(
            dataframe
        ),
        "start_time": (
            dataframe["time"].iloc[0]
        ),
        "end_time": (
            dataframe["time"].iloc[-1]
        ),
    }


def test_export(
    tmp_path,
):

    dataframe = make_dataframe()
    context = make_context()

    exporter = DatasetExporter(
        output_root=tmp_path
    )

    file = exporter.export(
        dataframe,
        "xauusd_m1_test.csv",
        context=context,
        source_metadata=(
            make_source_metadata(
                dataframe,
                context,
            )
        ),
    )

    assert file.is_file()

    assert tmp_path.resolve() in (
        file.resolve().parents
    )
