from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

sys.path.append(str(ROOT / "02_AI"))

from Database.database import database


def test_database_connection():

    with database.session() as connection:

        cursor = connection.cursor()

        cursor.execute("SELECT sqlite_version();")

        version = cursor.fetchone()

        assert version is not None