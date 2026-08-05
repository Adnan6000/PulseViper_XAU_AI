# PulseViper XAUUSD AI - Feature Engineering Architecture

## 1. Trend Features
- SMA / EMA Slopes (Short, Medium, Long-term: 9, 21, 50, 200)
- Trend Direction Classifiers (Bullish / Bearish / Ranging)
- ADX (Average Directional Index) & DI+ / DI-
- Supertrend Direction & Distance

## 2. Market Structure Features
- Higher Highs (HH), Higher Lows (HL), Lower Highs (LH), Lower Lows (LL)
- Break of Structure (BOS) Flags & Distances
- Change of Character (CHoCH) Detection
- Swing High / Swing Low Points & Age

## 3. Liquidity Features
- Equal Highs (EQH) & Equal Lows (EQL) Detection
- Liquidity Sweep Flags (Buy-side & Sell-side sweeps)
- Distance to Nearest Unmitigated Liquidity Pool
- Session High/Low Liquidity Points (Asia/London/NY)

## 4. Volatility Features
- ATR (Average True Range) & Normalized ATR Ratio
- Bollinger Bands Width & %B
- Historical Volatility (HV) Percentiles
- Spread Expansion / Compression Ratios

## 5. Volume Features
- On-Balance Volume (OBV) Slope
- Volume Delta (Buy vs. Sell Volume Pressure)
- Relative Volume (RVOL) against 20-period Average
- Volume Weighted Average Price (VWAP) & Standard Deviation Bands

## 6. Session Features
- Active Trading Session Flag (Asia, London, New York, NY/London Overlap)
- Session Progress Percentage (0% to 100% of current session)
- Session Open Price Distance Metrics
- Kill Zone Flags (London Open, NY Open, NY Close)

## 7. Time Features
- Day of Week (Monday to Friday seasonal patterns)
- Hour of Day (Cyclical Sine/Cosine Encodings)
- Minute of Hour Encodings
- High-Impact Economic News Proximity (Minutes to/from NFP, CPI, FOMC)

## 8. Pattern Features
- Candlestick Patterns (Pinbars, Engulfing, Inside Bars, Doji)
- Multi-candle Formations (Three White Soldiers, Evening Star, etc.)
- Price Compression / Triangle / Wedge Breakout Flags
- Pattern Success / Failure Historical Metrics

## 9. Order Block (OB) Features
- High-Probability Bullish / Bearish Order Block Identification
- Order Block Mitigation Status (Mitigated vs. Unmitigated)
- Distance from Current Price to Active OB
- OB Strength Metric (Volume & Displacement behind the OB move)

## 10. Fair Value Gap (FVG) / Imbalance Features
- Bullish & Bearish FVG Detection
- FVG Fill Percentage (Unfilled, Partially Filled, Fully Consequent Encroachment)
- Distance to Nearest Premium / Discount FVG
- FVG Creation Impulse Momentum

## 11. Risk Features
- Dynamic Stop Loss Multipliers (based on ATR & Liquidity Swings)
- Reward-to-Risk (RR) Ratio Calculations per Candidate Signal
- Maximum Drawdown Exposure Metrics
- Position Sizing Scaling Factors based on Current Volatility

## 12. Execution Features
- Real-Time Bid-Ask Spread vs. Historical Average
- Execution Latency & Slippage Estimates
- Broker Tick Velocity
- Trade Execution Trigger Confidence Score (AI Model Probability Output)
