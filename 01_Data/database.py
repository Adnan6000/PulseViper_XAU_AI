"""
PulseViper XAUUSD AI - Core Database Engine Foundation
Path: 01_Data/database.py
Rules: Strict modularity, PEP8 naming, thread-safe WAL connection, < 300 lines.
"""

import os
import shutil
import sqlite3
import logging
from datetime import datetime
from typing import Any, List, Optional, Tuple

# Set up clean institutional logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] DatabaseEngine: %(message)s")

MAX_BACKUP_RETENTION = 7  # Maximum rolling backup files


class DatabaseEngine:
    """Core Database Engine managing SQLite lifecycle, tables, queries, and backups."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.db_path = os.path.join(base_dir, "pulseviper.db")
        else:
            self.db_path = db_path

        self._initialize_database()

    def get_connection(self) -> sqlite3.Connection:
        """Returns a WAL-enabled SQLite connection instance."""
        connection = sqlite3.connect(self.db_path, timeout=30.0)
        connection.execute("PRAGMA journal_mode=WAL;")
        connection.execute("PRAGMA foreign_keys=ON;")
        return connection

    def execute_query(self, query: str, params: Tuple[Any, ...] = ()) -> Optional[List[Tuple[Any, ...]]]:
        """Executes a SQL query safely and returns fetched rows if applicable."""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                cursor.execute(query, params)
                connection.commit()
                if query.strip().upper().startswith("SELECT"):
                    return cursor.fetchall()
                return None
        except sqlite3.Error as error:
            logging.error(f"Database Query Failed: {error} | Query: {query[:60]}")
            raise error

    def execute_many(self, query: str, params_list: List[Tuple[Any, ...]]) -> None:
        """Executes bulk inserts/updates efficiently inside a single transaction."""
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                cursor.executemany(query, params_list)
                connection.commit()
                logging.info(f"Bulk transaction successful: {len(params_list)} records processed.")
        except sqlite3.Error as error:
            logging.error(f"Bulk Execution Failed: {error}")
            raise error

    def create_backup(self, backup_dir: Optional[str] = None) -> str:
        """Creates an automated timestamped backup copy of the database file."""
        if backup_dir is None:
            backup_dir = os.path.join(os.path.dirname(self.db_path), "Backups")

        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(backup_dir, f"pulseviper_backup_{timestamp}.db")

        shutil.copy2(self.db_path, backup_file)
        logging.info(f"Database Backup Created Successfully: {backup_file}")
        return backup_file

    def _initialize_database(self) -> None:
        """Initializes the database schema if tables do not exist."""
        logging.info(f"Initializing Core Database Schema at: {self.db_path}")

        table_schemas = [
            # 1. Raw Candles Table
            """
            CREATE TABLE IF NOT EXISTS candles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                tick_volume INTEGER,
                spread INTEGER,
                real_volume INTEGER,
                UNIQUE(symbol, timeframe, timestamp)
            );
            """,
            # 2. Market Structure Table
            """
            CREATE TABLE IF NOT EXISTS market_structure (
                candle_id INTEGER PRIMARY KEY,
                hh BOOLEAN DEFAULT 0,
                hl BOOLEAN DEFAULT 0,
                lh BOOLEAN DEFAULT 0,
                ll BOOLEAN DEFAULT 0,
                swing_high REAL,
                swing_low REAL,
                bos TEXT,
                choch TEXT,
                trend TEXT,
                trend_strength REAL,
                FOREIGN KEY (candle_id) REFERENCES candles (id) ON DELETE CASCADE
            );
            """,
            # 3. Liquidity Engine Table
            """
            CREATE TABLE IF NOT EXISTS liquidity (
                candle_id INTEGER PRIMARY KEY,
                equal_high REAL,
                equal_low REAL,
                liquidity_sweep TEXT,
                inducement BOOLEAN DEFAULT 0,
                stop_hunt BOOLEAN DEFAULT 0,
                liquidity_score REAL,
                FOREIGN KEY (candle_id) REFERENCES candles (id) ON DELETE CASCADE
            );
            """,
            # 4. Patterns Table
            """
            CREATE TABLE IF NOT EXISTS patterns (
                candle_id INTEGER PRIMARY KEY,
                is_rectangle BOOLEAN DEFAULT 0,
                is_triangle BOOLEAN DEFAULT 0,
                is_flag BOOLEAN DEFAULT 0,
                is_compression BOOLEAN DEFAULT 0,
                is_expansion BOOLEAN DEFAULT 0,
                breakout_type TEXT,
                pattern_score REAL,
                FOREIGN KEY (candle_id) REFERENCES candles (id) ON DELETE CASCADE
            );
            """,
            # 5. Institutional Zones Table
            """
            CREATE TABLE IF NOT EXISTS zones (
                candle_id INTEGER PRIMARY KEY,
                order_block TEXT,
                breaker_block TEXT,
                mitigation_block TEXT,
                fvg_status TEXT,
                ifvg_status TEXT,
                pricing_zone TEXT,
                zone_score REAL,
                FOREIGN KEY (candle_id) REFERENCES candles (id) ON DELETE CASCADE
            );
            """,
            # 6. Feature Storage Table
            """
            CREATE TABLE IF NOT EXISTS features (
                candle_id INTEGER PRIMARY KEY,
                feature_json TEXT NOT NULL,
                FOREIGN KEY (candle_id) REFERENCES candles (id) ON DELETE CASCADE
            );
            """,
            # 7. Labels Table
            """
            CREATE TABLE IF NOT EXISTS labels (
                candle_id INTEGER PRIMARY KEY,
                signal TEXT CHECK(signal IN ('BUY', 'SELL', 'NO_TRADE')),
                sl_distance_pips REAL,
                tp_distance_pips REAL,
                holding_time_bars INTEGER,
                FOREIGN KEY (candle_id) REFERENCES candles (id) ON DELETE CASCADE
            );
            """,
            # 8. Predictions Dump Table
            """
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candle_id INTEGER NOT NULL,
                model_version TEXT NOT NULL,
                ai_prediction TEXT NOT NULL,
                confidence REAL NOT NULL,
                actual_result TEXT,
                failure_reason TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (candle_id) REFERENCES candles (id) ON DELETE CASCADE
            );
            """,
            # 9. Backtest Logs Table
            """
            CREATE TABLE IF NOT EXISTS backtest (
                trade_id TEXT PRIMARY KEY,
                entry_time DATETIME NOT NULL,
                exit_time DATETIME NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL NOT NULL,
                profit_loss REAL NOT NULL,
                drawdown REAL,
                rr_ratio REAL,
                spread_pips REAL,
                trade_duration_min REAL
            );
            """,
            # 10. Continuous Learning Logs Table
            """
            CREATE TABLE IF NOT EXISTS learning_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT NOT NULL,
                feature_state TEXT NOT NULL,
                predicted_prob REAL NOT NULL,
                actual_pnl REAL NOT NULL,
                execution_slippage REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
        ]

        with self.get_connection() as connection:
            cursor = connection.cursor()
            for schema in table_schemas:
                cursor.execute(schema)

            # High-speed time-series index creation
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_candles_time ON candles(symbol, timeframe, timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pred_candle ON predictions(candle_id);")

            connection.commit()
        logging.info("Core Database Schema Initialized with Zero Errors.")


if __name__ == "__main__":
    db = DatabaseEngine()
    db.create_backup()
    print("Database initialization and initial backup successful!")