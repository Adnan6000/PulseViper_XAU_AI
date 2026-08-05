"""
PulseViper XAU AI
Database Connection Manager
"""

from pathlib import Path
import sqlite3
import sys
import importlib
from contextlib import contextmanager
from typing import Generator

ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

settings_module = importlib.import_module("02_AI.Config.settings")
settings = settings_module.settings

logger_module = importlib.import_module("02_AI.Utils.logger")
get_logger = logger_module.get_logger

logger = get_logger("DATABASE")

DATABASE_FILE = ROOT_DIR / "01_Data" / settings.database["filename"]


class DatabaseConnection:

    def __init__(self) -> None:
        self.database_path = DATABASE_FILE

    def connect(self) -> sqlite3.Connection:

        connection = sqlite3.connect(
            self.database_path,
            timeout=30,
            check_same_thread=False,
        )

        connection.row_factory = sqlite3.Row

        connection.execute("PRAGMA foreign_keys = ON;")
        connection.execute("PRAGMA journal_mode = WAL;")
        connection.execute("PRAGMA synchronous = NORMAL;")

        return connection

    @contextmanager
    def session(self) -> Generator[sqlite3.Connection, None, None]:

        connection = self.connect()

        try:
            yield connection
            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()


database = DatabaseConnection()