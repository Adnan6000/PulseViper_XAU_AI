
# PulseViper XAUUSD — R03 V2 Scientific Protocol

Protocol ID: R03_COLLECTION_LANE_V2_1

Status: PROPOSED — AWAITING INDEPENDENT REVIEW

## 1. Purpose

Evaluate the existing frozen R03 ExtraTrees classifier
prospectively using a new, independent, genuine-market
observation cohort.

This experiment is research-only. It does not authorize
trading, model retraining, or strategy deployment.

## 2. Frozen model

The existing R03 frozen inference artifact, feature schema,
class mappings, and prediction semantics must remain
unchanged throughout this experiment.

No parameter tuning or model selection using V2 prospective
outcomes is permitted before the sealed evaluation.

## 3. Cohort definition

Cohort ID: V2_INDEPENDENT_PROSPECTIVE_COHORT

The V2 cohort begins only after protocol approval and
implementation validation.

Earlier V1 observations and outcomes remain historical
research records and are not part of the V2 evaluation
denominator.

V1 and V2 cohorts must not be pooled automatically.

## 4. Original session-gap observation

The October 5, 2026 V1 observation associated with:

febaf847ef5cd078cfc0e8223eb2120c81969a91645998968e9a1083caa1c1f8

has an observed discontinuity in its future M5 timestamps.

This observation must not receive a fabricated outcome.

Its original V1 record and pending state must be preserved.

The separate experimental V2 terminal evidence is retained
for audit only. It is not counted as a matured outcome.

V2 collection does not depend on modifying or deleting
this V1 observation.

## 5. Prospective capture

Only genuine XAUUSD broker-market data may be used.

The existing read-only MT5 acquisition adapter,
frozen feature pipeline, and frozen R03 inference
adapter must be reused.

Synthetic observations, backfilled predictions, and
historical reconstruction disguised as prospective
capture are forbidden.

Each new observation must have a genuine source snapshot,
stable logical ID, and corresponding prospective anchor.

At most one unresolved V2 observation is allowed.

## 6. Outcome horizon

Required horizon:

12 consecutive completed M5 future bars after
the decision bar.

Consecutive means each neighboring bar timestamp is
exactly five minutes apart.

A missing required bar invalidates strict-contiguous
maturation for that observation.

No interpolation, forward filling, timestamp rewriting,
or alternative relabeling is permitted.

The frozen outcome labeling rules remain unchanged.

## 7. Collection target

Minimum genuine matured V2 outcomes: 60

Minimum distinct V2 observation UTC dates: 5

Excluded, missing, unresolved, or diagnostic-only
observations must never contribute to the matured count.

## 8. Session-gap handling and terminal disposition

V2 uses the strict requirement of 12 consecutive completed
M5 future bars after the decision bar.

If the required future timestamps are missing, the
observation must not be assigned a fabricated outcome.

An observation may be classified as
UNSCORABLE_STRICT_M5_SESSION_GAP only when:

1. Genuine broker-market data establish the missing
   timestamps within the required future horizon.

2. The observation and prospective anchor are validated
   against their original append-only records.

3. The gap evidence identifies the exact missing UTC
   timestamps and preserves source fingerprints.

4. A separate versioned terminal-disposition record is
   appended atomically and idempotently.

5. Terminal dispositions never count as matured outcomes.

6. The number and timing of terminal exclusions are
   reported in the final prospective evaluation.

7. No retroactive adjustment of prediction probabilities,
   class labels, or observation timestamps is permitted.

8. A terminally resolved observation may release the
   single-pending collection slot only after its
   disposition record passes integrity validation.

9. Any ambiguous, incomplete, conflicting, or tampered
   evidence must block collection.

10. This rule applies prospectively to V2 only.
    Original V1 ledgers and outcomes remain unchanged.

The final evaluation must disclose the proportion of
excluded observations and assess whether exclusion
patterns could introduce session-time or market-regime
selection bias.

## 9. Data integrity

V2 observations, anchors, and outcomes use separate
append-only ledgers.

Existing V1 ledgers must remain unchanged.

Concurrent collector processes are forbidden.

Orphan anchors, duplicate conflicts, invalid records,
or ledger integrity failures block automation.

## 10. Evaluation

No prospective performance conclusion may be issued
before the collection target is met.

The evaluation must report class-wise performance,
macro F1, balanced accuracy, uncertainty behavior,
and relevant confidence/calibration analysis.

Any trading-cost, PnL, or profitability study requires
its own explicitly defined and validated methodology.

## 11. Stop conditions

Automation must stop or remain blocked when:

- Protocol authority is absent or invalid.
- Genuine market-data authority fails.
- Frozen artifact verification fails.
- Ledger integrity fails.
- An orphan anchor is detected.
- More than one unresolved V2 observation exists.
- The scientific collection target is reached.

## 12. Authorization boundaries

Protocol approval may authorize research-only
prospective collection and strict outcome maturation.

It does not authorize:

- Live trading
- Broker order placement
- Model retraining
- Strategy promotion
- Automatic profitability claims

## 13. Review

Independent reviewer: NOT YET RECORDED

Review decision: PENDING

Review date: PENDING

Protocol approval must be recorded explicitly before
the approved-protocol authority file is pinned.

END OF PROTOCOL
