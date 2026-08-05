# PulseViper Core Module Interfaces & Contracts

## 1. Module: market_structure.py
- **Input**: DataFrame (timestamp, open, high, low, close, volume)
- **Output**: Swing High/Low, BOS, CHoCH, Trend, Internal/External Legs
- **Class**: `MarketStructureEngine`
- **Dependencies**: `pandas`, `numpy`

## 2. Module: liquidity_engine.py
- **Input**: DataFrame + Structure Data
- **Output**: EQH, EQL, Buy-Side Sweep, Sell-Side Sweep, Inducement Flags
- **Class**: `LiquidityEngine`
- **Dependencies**: `pandas`, `numpy`

## 3. Module: pattern_engine.py
- **Input**: DataFrame + Volatility Context
- **Output**: Compression/Expansion States, Rectangles, Valid/Fake Breakout Score
- **Class**: `PatternEngine`
- **Dependencies**: `pandas`, `numpy`

## 4. Module: market_dna.py
- **Input**: Single Candle & Multi-Candle Vector Attributes
- **Output**: Candle Personality Encodings (Manipulation, Impulse, Trap, Expansion, Exhaustion)
- **Class**: `CandleDNAEngine`
- **Dependencies**: `pandas`, `numpy`

## 5. Module: db_archiver.py (Database Engine)
- **Input**: MT5 Bar Ticks & Calculated Feature DataFrames
- **Output**: SQLite Relational Archival (`01_Data/pulseviper_market.db`)
- **Class**: `MarketDatabaseArchiver`
- **Dependencies**: `sqlite3`, `pandas`
