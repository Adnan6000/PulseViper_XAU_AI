import importlib



fetcher = importlib.import_module(
    "02_AI.Dataset.data_fetcher"
).fetcher

cleaner = importlib.import_module(
    "02_AI.Dataset.history_cleaner"
).cleaner


def test_cleaner():

    df = fetcher.fetch(bars=1000)

    df = cleaner.clean(df)

    df = cleaner.remove_invalid_prices(df)

    assert len(df) > 0
