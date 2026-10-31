import importlib



fetcher = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
).fetcher

validator = importlib.import_module(
    "02_AI.Dataset.history_validator"
).validator


def test_validator():

    df = fetcher.fetch(bars=1000)

    assert validator.validate(df)
