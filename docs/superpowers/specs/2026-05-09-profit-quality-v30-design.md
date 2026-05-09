# Profit Quality V30 Design

## Goal

Raise credible profit potential without optimizing against fake replay gains. The next iteration must first fix replay accounting, then expose enough signal/execution funnel metrics to tune toward roughly 1% real entry coverage with drawdown preferably under 30%.

## Current Evidence

The v29 three-way run is more realistic than prior runs, but two issues block trustworthy optimization:

- Final-test entry rate is about 0.49%, below the desired ~1% coverage.
- Replay end liquidation can double count open positions: a no-price-change one-position replay reports 1.1x instead of 1.0x because liquidation proceeds are added to cash while the position remains in mark-to-market equity.

Therefore profit work must start with replay correctness before training new models.

## Scope

This iteration changes the training/evaluation pipeline only. It does not change live bot execution, add leverage, or add position size beyond fixed 0.1 BNB / 10% stake controls.

## Design

### 1. Replay Accounting Fix

At `REPLAY_END`, closed positions must be removed or excluded from mark-to-market equity before final equity is computed. The test case is a single position bought and liquidated at the same price with zero fees/slippage; final equity must remain 1.0 and trade-log PnL must be zero.

### 2. Replay Funnel Metrics

Replay should report the path from model signal to filled trade:

- `entry_signal_count`: number of buy signals above threshold while no position is open.
- `entry_signal_rate`: signals divided by episode count.
- `entry_attempt_count`: immediate fills plus delayed entry attempts that reach fill evaluation.
- `entry_fill_rate`: filled entries divided by entry attempts.
- `entry_timeout_rate`: delayed entry timeouts divided by attempts.
- `entry_price_protection_skip_rate`: price-protection skips divided by attempts.

These metrics make it clear whether low trade count is caused by model selectivity, fill waits, price protection, or position capacity.

### 3. Entry Rate Targeting

Risk tuning should support a soft minimum entry rate, not just a target penalty. Add `risk_tune_min_entry_rate` to mark candidates infeasible when entry coverage is too low. For this user's current preference, the next training run should target roughly 1% with a practical band around 0.8%-2% rather than the previous nominal 20% target.

### 4. V30 Training Pass

After tests pass, run a corrected v30 training using the v29 realistic profile, but with entry-rate tuning near 1%:

- `--risk-tune-target-entry-rate 0.01`
- `--risk-tune-max-entry-rate 0.03`
- `--risk-tune-min-entry-rate 0.008`

Report validation and final-test results, stress replay, walk-forward, and funnel metrics. Do not call the result credible if final test or stress contradicts validation.

## Acceptance Criteria

- The replay-end accounting regression test fails before the fix and passes after the fix.
- Pipeline tests and CLI tests pass.
- Full `python -m unittest discover` passes.
- `git diff --check` passes.
- V30 manifest contains corrected final equity and funnel metrics.
- The final report clearly separates validation, final test, and stress outcomes.
