"""
PulseViper XAUUSD AI - Database Archiver Module
Manages SQLite Schema, Tables Initialization, Fast Indexing & Ingestion.
Path: 01_Data/db_archiver.py
"""

import os
import sqlite3
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

class PulseViperDatabase:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            self.db_path = os.path.join(base_dir, "pulseviper.db")
        else:
            self.db_path = db_path
            
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Returns SQLite Connection with WAL mode enabled for high performance."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_db(self):
        """Initializes all 10 core tables with proper constraints and fast indexes."""
        logging.info(f"Initializing PulseViper Database Engine at: {self.db_path}")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Table 1: Raw Candles
            cursor.execute("""
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
            """)

            # Table 2: Market Structure
            cursor.execute("""
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
            """)

            # Table 3: Liquidity
            cursor.execute("""
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
            """)

            # Table 4: Patterns
            cursor.execute("""
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
            """)

            # Table 5: Institutional Zones
            cursor.execute("""
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
            """)

            # Table 6: Synthetic Features (AI Feature Vector Dump)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS features (
                candle_id INTEGER PRIMARY KEY,
                feature_json TEXT NOT NULL,
                FOREIGN KEY (candle_id) REFERENCES candles (id) ON DELETE CASCADE
            );
            """)

            # Table 7: Labels (Triple-Barrier & Outcome Labels)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS labels (
                candle_id INTEGER PRIMARY KEY,
                signal TEXT CHECK(signal IN ('BUY', 'SELL', 'NO_TRADE')),
                sl_distance_pips REAL,
                tp_distance_pips REAL,
                holding_time_bars INTEGER,
                FOREIGN KEY (candle_id) REFERENCES candles (id) ON DELETE CASCADE
            );
            """)

            # Table 8: Model Predictions Dump
            cursor.execute("""
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
            """)

            # Table 9: Backtest Logs
            cursor.execute("""
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
            """)

            # Table 10: Learning Logs (Retraining Feedback Loop)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id TEXT NOT NULL,
                feature_state TEXT NOT NULL,
                predicted_prob REAL NOT NULL,
                actual_pnl REAL NOT NULL,
                execution_slippage REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Indexing for High-Performance Time-Series Queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_candles_time ON candles(symbol, timeframe, timestamp);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pred_candle ON predictions(candle_id);")

            conn.commit()
            logging.info("Database Architecture initialization complete with 10 Relational Tables & WAL Indexing!")

if __name__ == "__main__":
    db = PulseViperDatabase()