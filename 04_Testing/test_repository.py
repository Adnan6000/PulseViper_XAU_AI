from pathlib import Path
import importlib
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

repo_module = importlib.import_module("02_AI.Database.repository")

repository = repo_module.repository


def test_repository():

    row = repository.fetch_one(
        "SELECT name FROM sqlite_master WHERE type='table' LIMIT 1;"
    )

    assert row is not None