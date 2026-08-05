"""
PulseViper XAU AI
Database Connection Manager

Path:
02_AI/Database/database.py

Responsibility:
- Open SQLite connection
- Configure SQLite
- Handle transactions
- Close connection safely
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

from Config.settings import settings
from Utils.logger import get_logger

logger = get_logger("DATABASE")

ROOT_DIR = Path(__file__).resolve().parents[2]

# IMPORTANT:
# Database FILE always stays inside 01_Data
DATABASE_FILE = ROOT_DIR / "01_Data" / settings.database["filename"]


class DatabaseConnection:
    """
    Central SQLite connection manager.
    """

    def __init__(self) -> None:
        self.database_path = DATABASE_FILE

    def connect(self) -> sqlite3.Connection:
        """
        Create configured SQLite connection.
        """

        try:

            connection = sqlite3.connect(
                self.database_path,
                timeout=30,
                check_same_thread=False,
            )

            connection.row_factory = sqlite3.Row

            connection.execute("PRAGMA foreign_keys = ON;")
            connection.execute("PRAGMA journal_mode = WAL;")
            connection.execute("PRAGMA synchronous = NORMAL;")

            logger.info("Database Connected")

            return connection

        except sqlite3.Error as error:

            logger.exception("Database Connection Failed")

            raise error

    @contextmanager
    def session(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Transaction manager.
        """

        connection = self.connect()

        try:

            yield connection

            connection.commit()

        except Exception:

            connection.rollback()

            logger.exception("Transaction Rolled Back")

            raise

        finally:

            connection.close()

            logger.info("Database Closed")


database = DatabaseConnection()