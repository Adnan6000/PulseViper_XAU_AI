# PulseViper Core Execution & Decision Pipeline Architecture

## 1. Modular Core Architecture (`02_AI/Core/`)
All engine modules operate in strict isolation:
- `market_structure.py` -> Structure & Swings
- `liquidity_engine.py`  -> Sweeps & Pools
- `pattern_engine.py`    -> Compression, Expansion, Breakouts
- `institutional_zones.py` -> OB, FVG, Imbalances
- `market_regime.py`     -> Volatility & State Classification
- `feature_generator.py` -> Synthesizes engine outputs into AI feature vectors
- `confidence_engine.py` -> Individual engine & combined weighted scores
- `risk_engine.py`       -> 3-Stage Execution Pipeline & Position Sizing

## 2. The 3-Stage Order Execution Pipeline
1. **Permission Stage**: Macro filters (Spread, High-impact News, Market Regime)
2. **Timing & Direction Stage**: Structural Alignment + Confidence Engine Threshold Check
3. **Execution Stage**: Mode-based Sizing, SL/TP Computation, Order Routing

## 3. Execution Risk Profiles
- **Conservative Mode**: Max 1.0% Risk | A+ setups only | Base Lot
- **Balanced Mode**: Max 2.0% Risk | A & A+ setups | Trailing Stops
- **Aggressive Mode**: Dynamic Position Scaling | Triggered ONLY on Confidence >= 90% with low spread and A+ confluence.
