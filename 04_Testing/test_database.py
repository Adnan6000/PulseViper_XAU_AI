"""
Automated Pytest for Database Engine.
Path: 04_Testing/test_database.py
"""

import importlib
from pathlib import Path
import sys
import sqlite3

# Add Workspace Root to sys.path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Dynamic Module Imports
db_module = importlib.import_module("02_AI.Database.database")
DatabaseConnection = db_module.DatabaseConnection


def test_sqlite_in_memory_connection() -> None:
    """Verify in-memory SQLite initialization, pragmas, and execution."""
    db_engine = DatabaseConnection(db_path=Path(":memory:"))
    conn = db_engine.get_connection()
    
    assert isinstance(conn, sqlite3.Connection)
    
    # Check Pragmas
    cursor = conn.cursor()
    journal_mode = cursor.execute("PRAGMA journal_mode;").fetchone()[0]
    foreign_keys = cursor.execute("PRAGMA foreign_keys;").fetchone()[0]
    
    assert journal_mode.lower() in ["memory", "wal"]
    assert foreign_keys == 1
    conn.close()


def test_database_session_context_manager(tmp_path: Path) -> None:
    """Verify transaction commit and automatic connection closing."""
    temp_db = tmp_path / "test_run.db"
    db_engine = DatabaseConnection(db_path=temp_db)

    # Use Context Manager Session
    with db_engine.get_connection() as conn:
        conn.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, val TEXT);")
        conn.execute("INSERT INTO test_table (val) VALUES ('PulseViper');")
        conn.commit()

    # Reopen and read data
    with db_engine.get_connection() as conn:
        row = conn.execute("SELECT val FROM test_table WHERE id = 1;").fetchone()
        assert row["val"] == "PulseViper"

    assert temp_db.exists()