from pathlib import Path
import importlib
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

schema_module = importlib.import_module("02_AI.Database.schema")

schema = schema_module.schema


def test_schema():

    schema.initialize()

    assert True