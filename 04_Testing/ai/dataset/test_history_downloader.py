import importlib



module = importlib.import_module("02_AI.Dataset.history_downloader")

downloader = module.downloader


def test_history():

    files = downloader.download(bars=500)

    assert len(files) == 7
