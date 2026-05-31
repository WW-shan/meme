# Quick-Profit Support Pool Refresh

Date: 2026-05-31

## Outcome

Outcome tier: `Rejected` for replay promotion / `diagnostic_only` for research tracking.

No live switch. No `.env`, model artifact, threshold, sizing, buy/sell logic, bot process, collector process, runtime enablement, or restart changed.

The latest live rejected-signal pool is large, but the causal support rules are still too noisy to justify another quick-profit replay. This closes the immediate "run another quick-profit grid because the latest window has many fast-profit labels" path unless a materially different decision point or label is introduced.

## Live Basis

After the Changzhang execution-freshness boundary, there were no new real trades and no open positions. A fresh rejected-signal time-to-barrier scan covered the live stream after `2026-05-31 00:19:40`.

```bash
venv/bin/python scripts/probe_time_to_barrier.py \
  --since '2026-05-31 00:19:40' \
  --recent-lifecycle-files 64 \
  --max-candidate-sample 0 \
  --output data/replay_reports/time_to_barrier_probe_20260531_after_changzhang_freshness_boundary.json
```

Result:

- signal decisions: `10932`
- dropped duplicate signal decisions: `10151`
- per-token candidates: `781`
- sample limited: `false`
- path classes: `fast_profit=24`, `fast_profit_then_collapse=39`, `flat_timeout=538`, `slow_runner=16`, `stop_first=164`

This is real opportunity support, but it is also dominated by flat/stop paths. The experiment therefore used support diagnostics only, not a replay grid.

## Single-Window Support

```bash
venv/bin/python scripts/probe_support_action_policy.py \
  --time-to-barrier-report data/replay_reports/time_to_barrier_probe_20260531_after_changzhang_freshness_boundary.json \
  --output data/replay_reports/support_action_policy_probe_20260531_after_changzhang_freshness_boundary.json \
  --min-selected 5 \
  --force
```

Best eligible single-window rules:

- `young_high_prob_clean_flow`: selected `5`, positives `3`, negatives `2`, precision `60.00%`
- `high_prob_low_toxic_overlap`: selected `61`, positives `20`, negatives `41`, precision `32.79%`
- `high_prob_volume_volatility`: selected `100`, positives `24`, negatives `76`, precision `24.00%`
- `high_prob_positive_pred`: selected `33`, positives `7`, negatives `26`, precision `21.21%`
- `young_high_prob_positive_pred`: selected `32`, positives `6`, negatives `26`, precision `18.75%`

The cleanest rule is too small. The broad rules select too many stop/flat candidates.

## Pooled Support

To check whether the latest result was just a single-window artifact, the diagnostic pooled four all-candidate time-to-barrier reports:

- `data/replay_reports/time_to_barrier_probe_20260522_expanded_flow_since20260521_all_candidates.json`
- `data/replay_reports/time_to_barrier_probe_20260526_conditional_exit_flow_survival_round.json`
- `data/replay_reports/time_to_barrier_probe_20260527_live_rejects_since_midnight.json`
- `data/replay_reports/time_to_barrier_probe_20260531_after_changzhang_freshness_boundary.json`

```bash
venv/bin/python scripts/probe_support_action_policy_pool.py \
  --time-to-barrier-report data/replay_reports/time_to_barrier_probe_20260522_expanded_flow_since20260521_all_candidates.json \
  --time-to-barrier-report data/replay_reports/time_to_barrier_probe_20260526_conditional_exit_flow_survival_round.json \
  --time-to-barrier-report data/replay_reports/time_to_barrier_probe_20260527_live_rejects_since_midnight.json \
  --time-to-barrier-report data/replay_reports/time_to_barrier_probe_20260531_after_changzhang_freshness_boundary.json \
  --output data/replay_reports/support_action_policy_pool_20260531_after_changzhang_freshness_boundary.json \
  --min-selected 5 \
  --min-pooled-selected 60 \
  --min-pooled-positive 25 \
  --force
```

Pooled result:

- decision: `missing_flow_feature_parity`
- input candidates: `2030`
- positive candidates: `327`
- negative candidates: `1703`
- target `high_prob_low_toxic_overlap`: selected `260`, positives `109`, negatives `151`, precision `41.92%`
- `young_high_prob_clean_flow`: selected `78`, positives `33`, negatives `45`, precision `42.31%`
- `high_prob_volume_volatility`: selected `271`, positives `100`, negatives `171`, precision `36.90%`
- `v95_like_pred_rescue`: selected `7`, positives `5`, negatives `2`, precision `71.43%`

Flow parity remains incomplete:

- `flow_event_count_30s`: finite `2030/2030`
- `flow_buy_sell_overlap_ratio_60s`: finite `1805/2030`
- `flow_recent_seller_reentry_ratio_30s`: finite `1742/2030`

## Decision

Reject quick-profit replay promotion from this evidence.

Reasons:

- The latest fast-profit-shaped count is large, but most candidates are still flat/stop paths.
- The best narrow clean-flow rule has too few latest-window examples and only `42.31%` pooled precision.
- The broad target rule has enough pooled count but selects `151` negatives, so it repeats the known quick-profit failure mode: broad candidate expansion with toxic added trades.
- Required flow ratio parity is still incomplete, so missing overlap values must not be treated as clean flow.
- Prior strict replay already hard-rejected the non-broad quick-profit grid with worse validation/final profit, win rate, drawdown, walk-forward, stress, and paired delta.

## Next Direction

Do not sweep quick-profit thresholds from this branch. The next structural direction should use one of:

- replay-compatible freshness / accepted-trade abstention with better signal-time parity;
- conditional dead-flow exit or entry abstention that targets accepted losses without adding rejected candidates;
- live shadow evaluation that records candidate actions before any runtime change.

`docs/model_scoreboard.md` was updated because this diagnostic changes the current quick-profit branch status after the latest live window.
