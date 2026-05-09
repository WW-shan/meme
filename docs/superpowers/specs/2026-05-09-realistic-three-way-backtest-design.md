# Realistic Three-Way Backtest Optimization Design

Date: 2026-05-09
Status: Approved for implementation

## Goal

Improve model selection and offline replay credibility before chasing higher multiples. The next training flow must avoid using the final evaluation set for threshold selection, and the replay must include more live-like execution failures around delayed fills.

The live assumptions remain:

- Initial equity: 1 BNB.
- Fixed stake: 0.1 BNB per entry.
- Maximum concurrent open or pending positions: 8.
- Entry delay: 3 seconds.
- Exit delay: 3 seconds.
- Preferred drawdown direction: keep main and walk-forward drawdown near or under 30% without optimizing into no-profit behavior.

## Current Problem

The current best-looking candidate, `v27`, was produced by manually sweeping thresholds on the evaluation period. Its metrics are useful as a diagnostic, but they are not a clean final-test result. The stricter `v28` train/validation/test experiment showed that validation-selected thresholds can fail on the final 20% period.

The replay is also still too optimistic in some execution details:

- A pending buy can fill at the first later sample even if that sample is far after the intended 3-second delay.
- A delayed buy can chase a token that has already moved too far from the signal price.
- A delayed sell can appear clean even when the first observed fill is much later than the intended exit delay.
- The manifest does not expose fill waits, skipped entries, or timeout-style execution quality metrics.

## Design

### 1. Three-Way Chronological Split

Add an optional training mode that splits lifecycle files into:

```text
train -> validation -> final test
```

The model and PPO policy train only on `train`.

Risk tuning and buy-threshold selection use only `validation`.

The final manifest reports `evaluation` from `final test`, and that final test must not affect training, validation threshold selection, or manual parameter selection.

The manifest also records:

- `three_way_split.enabled`
- train, validation, and final test file counts
- train, validation, and final test sample counts
- overlap/excluded-token counts used to avoid raw token leakage
- validation replay metrics under `validation_evaluation`

The default stays backward-compatible: if `validation_split_ratio` is `0`, the current train/eval flow remains active.

### 2. More Realistic Entry Fill Behavior

Replay pending entries gain these controls:

- `entry_max_fill_wait_seconds`: maximum tolerated time after the entry due time. If the first available sample arrives later than this, skip the buy and count `entry_timeout_count`.
- `entry_price_protection_pct`: maximum tolerated price increase from signal price to delayed fill price. If the delayed fill price is above `signal_price * (1 + pct)`, skip the buy and count `entry_price_protection_skip_count`.

The trade log and replay summary record:

- `entry_fill_count`
- `entry_timeout_count`
- `entry_price_protection_skip_count`
- `entry_pending_at_replay_end_count`
- average and maximum entry wait seconds

### 3. More Realistic Exit Fill Observability

Replay pending exits gain:

- `exit_max_fill_wait_seconds`: maximum expected time after exit due time before the fill is considered late.

If the first available exit sample appears after that limit, the replay still closes at the first observed price because there is no better price source in offline lifecycle data, but it records:

- `exit_timeout_count`
- average and maximum exit wait seconds

This avoids pretending late exits are normal while preserving deterministic replay.

### 4. CLI Controls

`scripts/run_hybrid_training.py` exposes:

- `--validation-split-ratio`
- `--min-validation-files`
- `--entry-max-fill-wait-seconds`
- `--exit-max-fill-wait-seconds`
- `--entry-price-protection-pct`

For `--live-replay-profile`, defaults are:

- `entry_max_fill_wait_seconds=3`
- `exit_max_fill_wait_seconds=6`
- `entry_price_protection_pct=0.25`

Explicit CLI values override the live-profile defaults.

### 5. Model Optimization After Replay Upgrade

After the code changes, train the next candidate with the realistic profile:

- three-way split around 60/20/20
- fixed 0.1 BNB stake
- live delayed labels
- risk-adjusted entry target as an experiment, but selection judged only by final test

A candidate is credible only if:

- validation and final test are directionally consistent
- final test is profitable
- final test and walk-forward drawdown are not far beyond 30%
- stress replay does not reveal complete collapse under mild friction
- profit is not dominated by a tiny number of trades

## Testing Strategy

Tests must prove:

- Entry pending fills time out when the first sample after due time exceeds `entry_max_fill_wait_seconds`.
- Entry price protection skips buys whose delayed fill price has moved too far above signal price.
- Exit pending fills record timeout metrics when the first sample after due time exceeds `exit_max_fill_wait_seconds`.
- Replay summary includes execution quality metrics.
- Three-way split sends risk tuning to validation samples and final evaluation to held-out test samples.
- CLI parses and passes the new split and execution controls.

## Non-Goals

- No leverage.
- No stake increase above fixed 0.1 BNB.
- No guarantee of 20x results.
- No use of final test data for threshold tuning.
- No chain-specific RPC simulation inside this offline replay step.
