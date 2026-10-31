import importlib



fetcher_module = importlib.import_module("02_AI.Dataset.data_fetcher")

fetcher = fetcher_module.fetcher


def test_fetch():

    df = fetcher.fetch(bars=100)

    assert len(df) == 100
