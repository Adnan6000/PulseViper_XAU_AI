import importlib



schema_module = importlib.import_module("02_AI.Database.schema")

schema = schema_module.schema


def test_schema():

    schema.initialize()

    assert True
