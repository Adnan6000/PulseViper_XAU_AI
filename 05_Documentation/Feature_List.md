# PulseViper XAU AI
## Feature Contract & Research Feature Inventory

This document separates:

```text
IMPLEMENTED MODEL FEATURES
```

from:

```text
RESEARCH / FUTURE FEATURE IDEAS
```

---

# 1. Base Feature Registry

Source:

```text
02_AI/Features/feature_list.py
```

Current base registry:

```text
43 features
```

---

## Trend Features

```text
ema20
ema50
ema200

dist_ema20
dist_ema50
dist_ema200

ema20_slope
ema50_slope
ema200_slope

trend_strength
trend_direction
```

---

## Momentum Features

```text
rsi14
rsi_slope

macd
macd_signal
macd_hist

roc10
momentum10
```

---

## Volatility Features

```text
true_range
atr14
atr_percent
candle_range
avg_range20
volatility_ratio
rolling_std20
```

---

## Candle Features

```text
body
range

upper_wick
lower_wick

body_ratio
upper_wick_ratio
lower_wick_ratio

bullish
bearish

doji
marubozu
pinbar

bullish_engulfing
bearish_engulfing

inside_bar
outside_bar

expansion
compression
```

---

# 2. Multi-Timeframe Training Features

Current training base timeframe:

```text
M5
```

Context timeframes:

```text
M15
M30
H1
H4
D1
```

Each base feature is namespaced by timeframe.

Examples:

```text
m5_ema20
m15_ema20
h1_atr14
h4_trend_direction
d1_volatility_ratio
```

---

# 3. Higher-Timeframe Availability

A higher-timeframe feature becomes usable only after its source candle has completed.

Example:

```text
H1 candle:
10:00 -> 11:00
```

Its completed H1 feature state may be used only by decisions at or after:

```text
11:00
```

This prevents higher-timeframe look-ahead leakage.

---

# 4. Additional Base Context

Training matrices also contain causal context such as:

```text
spread points
log tick volume
relative tick volume
UTC hour sine
UTC hour cosine
UTC day sine
UTC day cosine
higher-timeframe age
```

---

# 5. Training V1 / V2 Feature Count

```text
270 features
```

These consist of causal multi-timeframe technical context.

---

# 6. Training V3 Gold-Domain Features

V3 adds:

```text
63 causal domain features
```

Total:

```text
333 features
```

---

## Market Regime Features

Examples:

```text
regime_ready
regime_atr_percentile
regime_range_atr
regime_efficiency
regime_directional_move_atr
regime_trend_strength
regime_trend_code
regime_volatility_code
```

---

## Market Structure Features

Examples:

```text
HH
HL
LH
LL

micro_high
micro_low

internal_high
internal_low

major_high
major_low

swing_score
swing_excursion_atr
swing_reversal_atr

swing_direction_code
swing_scale_code
structure_bias_code
```

---

## Structure Distance Features

Examples:

```text
last_swing_high_known
last_swing_low_known

last_major_high_known
last_major_low_known

dist_last_swing_high_atr
dist_last_swing_low_atr

dist_last_major_high_atr
dist_last_major_low_atr

structure_range_position
bars_since_swing
```

---

## BOS Features

Examples:

```text
bullish_bos
bearish_bos

micro_bos
internal_bos
major_bos

bos_strength_atr

bos_continuation
bos_reversal

bars_since_bullish_bos
bars_since_bearish_bos

last_bos_direction
```

---

## FVG Features

Examples:

```text
bullish_fvg
bearish_fvg

fvg_atr_ratio

bars_since_bullish_fvg
bars_since_bearish_fvg

last_fvg_direction
last_fvg_atr_ratio
```

---

## Institutional Zone Features

Only causal confirmation-event information is eligible.

Examples:

```text
iz_event
iz_direction
iz_strength
iz_displacement_score
iz_body_ratio
iz_zone_size_atr
iz_confirmation_delay_bars

bars_since_bullish_iz
bars_since_bearish_iz

last_iz_direction
last_iz_strength
```

---

# 7. Supervised Target Columns

Targets are never model features.

Current target classes:

```text
SHORT
NO_TRADE
LONG
```

Current V2/V3 label definition:

---

## LONG

```text
future upside excursion >= 1.25 ATR
AND
future downside excursion <= 0.75 ATR
```

---

## SHORT

```text
future downside excursion >= 1.25 ATR
AND
future upside excursion <= 0.75 ATR
```

---

## NO_TRADE

```text
all other future paths
```

---

# 8. Target / Outcome Diagnostics

Outcome columns may include:

```text
target_class
target_class_id
target_tradeable
target_ambiguous
target_profit_atr
target_max_adverse_atr
target_entry_close
target_up_excursion_atr
target_down_excursion_atr
target_forward_return_atr
target_reason
```

These columns must never accidentally appear inside `feature_columns`.

---

# 9. Existing Research Engines Not Automatically Used as ML Features

The repository includes additional information sources such as:

- liquidity pools
- liquidity sweeps
- liquidity lifecycle
- market-context liquidity
- setup state
- confidence
- FVG mitigation
- FVG quality
- execution friction
- risk context

Their existence does not automatically make them good ML inputs.

Before inclusion they require:

1. causality verification
2. stability testing
3. normalization review
4. leakage review
5. out-of-sample benefit

---

# 10. Future Candidate Features

Possible future features include:

## Liquidity

- ATR-normalized liquidity distance
- pool age
- pool strength
- sweep confirmation
- liquidity-side imbalance

## Sessions

- Asia session
- London session
- New York session
- London / New York overlap
- session progress
- session high / low distance

## Execution

- current spread regime
- historical spread percentile
- actual forward slippage
- commission burden
- execution quality

## Trade Context

- entry distance
- stop distance
- reward/risk
- MFE
- MAE
- time-to-resolution

Future-derived outcomes must remain targets/evaluation data, not causal features.