"""
PulseViper Repository Layer
"""

from pathlib import Path
import sys
import importlib
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

database_module = importlib.import_module("02_AI.Database.database")

database = database_module.database


class Repository:

    def execute(self, query: str, params: tuple = ()) -> None:

        with database.session() as conn:

            conn.execute(query, params)

    def fetch_one(self, query: str, params: tuple = ()) -> Any:

        with database.session() as conn:

            cursor = conn.execute(query, params)

            return cursor.fetchone()

    def fetch_all(self, query: str, params: tuple = ()) -> list:

        with database.session() as conn:

            cursor = conn.execute(query, params)

            return cursor.fetchall()


repository = Repository()