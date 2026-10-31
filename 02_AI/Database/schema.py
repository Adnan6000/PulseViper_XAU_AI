"""
PulseViper XAU AI
Database Schema
"""

from pathlib import Path
import sys
import importlib

ROOT_DIR = Path(__file__).resolve().parents[2]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

database_module = importlib.import_module("02_AI.Database.database")
logger_module = importlib.import_module("02_AI.Utils.logger")

database = database_module.database
logger = logger_module.get_logger("SCHEMA")


class DatabaseSchema:

    def initialize(self):

        with database.session() as conn:

            cursor = conn.cursor()

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS candles(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                tick_volume INTEGER,
                spread INTEGER,
                real_volume INTEGER,
                UNIQUE(symbol,timeframe,timestamp)
            );
            """)

            cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_candles
            ON candles(symbol,timeframe,timestamp);
            """)

        logger.info("Schema Initialized")


schema = DatabaseSchema()