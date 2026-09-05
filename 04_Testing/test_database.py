import importlib

database_module = importlib.import_module(
    "02_AI.Database.database"
)

database = database_module.database


def test_database_connection():

    with database.session() as connection:

        cursor = connection.cursor()

        cursor.execute("SELECT sqlite_version();")

        version = cursor.fetchone()

        assert version is not None
