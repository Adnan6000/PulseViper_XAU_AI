import importlib



repo_module = importlib.import_module("02_AI.Database.repository")

repository = repo_module.repository


def test_repository():

    row = repository.fetch_one(
        "SELECT name FROM sqlite_master WHERE type='table' LIMIT 1;"
    )

    assert row is not None
