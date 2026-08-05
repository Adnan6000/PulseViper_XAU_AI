"""
PulseViper XAUUSD AI - Database Connection Manager
Path: 02_AI/Database/database.py
Provides SQLite connection lifecycle, WAL mode configuration, and Context Manager execution.
"""

import sqlite3
from pathlib import Path
from typing import Generator, Optional
import importlib

# Dynamic Import for Configuration Subsystem
settings_module = importlib.import_module("02_AI.Config.settings")
settings = settings_module.settings

# Dynamic Import for Logger Subsystem
logger_module = importlib.import_module("02_AI.Utils.logger")
get_logger = logger_module.get_logger

logger = get_logger("DATABASE_ENGINE")

ROOT_DIR: Path = Path(__file__).resolve().parents[2]
DATA_DIR: Path = ROOT_DIR / "Data"
DATA_DIR.mkdir(exist_ok=True)


class DatabaseConnection:
    """SQLite Database connection factory using WAL mode and Thread-Safe execution."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        if db_path is None:
            db_name = settings.database.get("filename", "pulseviper.db")
            self.db_path = DATA_DIR / db_name
        else:
            self.db_path = db_path

    def get_connection(self) -> sqlite3.Connection:
        """
        Establishes a connection to the SQLite database.
        Enforces foreign key constraints and WAL mode for high concurrency.
        """
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=20.0,
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row
            # Enforce Performance & Integrity Pragmas
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            conn.execute("PRAGMA synchronous=NORMAL;")
            return conn
        except sqlite3.Error as err:
            logger.error(f"Failed to connect to SQLite Database at {self.db_path}: {err}")
            raise err

    def session(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for handling automatic transaction commit/rollback."""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as err:
            conn.rollback()
            logger.error(f"Database Transaction Error, Rolling back: {err}")
            raise err
        finally:
            conn.close()