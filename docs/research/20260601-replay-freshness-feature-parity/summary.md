# Replay Freshness Feature Parity

Date: 2026-06-01
Status: Research Alpha instrumentation

## Question

Can strict replay selected-trade-delta output expose enough decision-time context to move the execution-freshness direction away from accepted-trade proxy evidence?

This follows the rejected post-negative-PredReturn freshness refresh. The live freshness shadow still failed holdout, so this pass tests the structural blocker directly: whether replay trade logs can carry the signal-time volume and volatility fields needed for replay-compatible freshness policies.

## Artifacts

- Live attribution refresh: `data/replay_reports/live_trade_attribution_20260601_replay_compat_freshness_entry.json`
- Live attribution summary: `data/replay_reports/live_trade_attribution_20260601_replay_compat_freshness_entry.md`
- Signal freshness shadow: `data/replay_reports/signal_freshness_shadow_20260601_replay_compat_freshness_entry.json`
- Signal freshness shadow summary: `data/replay_reports/signal_freshness_shadow_20260601_replay_compat_freshness_entry.md`
- Strict replay parity report: `data/replay_reports/replay_freshness_feature_parity_negative_pred_quick_profit_20260601.json`

## Commands

```bash
venv/bin/python scripts/probe_live_trade_attribution.py \
  --since '2026-06-01 02:15:00' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --output-json data/replay_reports/live_trade_attribution_20260601_replay_compat_freshness_entry.json \
  --output-md data/replay_reports/live_trade_attribution_20260601_replay_compat_freshness_entry.md \
  --max-trade-sample 40 \
  --max-candidate-sample 200 \
  --force
```

```bash
venv/bin/python scripts/probe_signal_freshness_shadow.py \
  --since '2026-06-01 02:15:00' \
  --recent-lifecycle-files 160 \
  --output-json data/replay_reports/signal_freshness_shadow_20260601_replay_compat_freshness_entry.json \
  --output-md data/replay_reports/signal_freshness_shadow_20260601_replay_compat_freshness_entry.md \
  --max-candidate-sample 200 \
  --split-stability \
  --force
```

```bash
venv/bin/python scripts/run_primary_score_scalp_replay.py \
  --candidate-grid-json docs/research/20260601-negative-pred-ultrashort-quick-profit/negative_pred_ultrashort_grid.json \
  --output data/replay_reports/replay_freshness_feature_parity_negative_pred_quick_profit_20260601.json \
  --write-selected-trade-delta \
  --force
```

## Live Refresh

Fresh live attribution after `2026-06-01 02:15:00`:

- Closed trades: `0`.
- Rejected signal decisions: `393`.
- Per-token candidates: `38`.
- Barrier classes: `flat_timeout=31`, `slow_runner=3`, `stop_first=4`.
- Policy hints: `skip=35`, `conditional_slow_hold=3`.
- Decision: `NO_GO_FOR_LIVE_SWITCH`.

Signal-freshness split shadow:

- Outcome tier: `Rejected`.
- Decision: `signal_freshness_train_rule_failed_holdout`.
- Split counts: train `22`, validation `8`, final `8`.
- Selected rule: `lifecycle_status_staleness_seconds >= 0.00817704`.
- Validation precision: `0.6666666666666666`; validation opportunity misses: `1`.
- Stable rules: `0`.

## Replay Feature Parity Result

The strict replay itself still rejects the selected negative-PredReturn quick-profit candidate:

- Decision: `reject`.
- `live_switch_evidence=false`.
- Validation baseline: net profit `0.022842003299308057` BNB, trades `38`, win rate `0.8157894736842105`, max drawdown `-10.187954315383251`.
- Selected validation candidate: net profit `0.0386373291806712` BNB, trades `511`, win rate `0.48336594911937375`, max drawdown `-19.539228260041263`.
- Final candidate: net profit `-0.0038727655404503423` BNB, trades `440`, win rate `0.35454545454545455`, max drawdown `-85.7854786802085`.
- Final confirmation: failed.

The selected-trade-delta feature coverage is the useful result:

| Split / Delta Set | Trades | `entry_price_volatility` | `entry_volume_30s` | Chain Lag / Staleness |
|---|---:|---:|---:|---:|
| Validation removed baseline | `1` | `1/1` | `1/1` | `0/1` |
| Validation added candidate | `474` | `474/474` | `474/474` | `0/474` |
| Final removed baseline | `4` | `4/4` | `4/4` | `0/4` |
| Final added candidate | `423` | `423/423` | `423/423` | `0/423` |

## Decision

No live switch. No `.env`, model artifact, threshold, sizing, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

This does not promote the chain-lag or staleness freshness rule. Strict replay still lacks lifecycle lag and lifecycle staleness fields, so the accepted-trade chain-lag proxy remains blocked from promotion.

This does improve the replay path for the signal-context branch: selected trade logs now preserve decision-time `entry_price_volatility`, `entry_volume_30s`, and `entry_token_age_seconds`, and the trade-delta attribution report checks coverage explicitly.

`docs/model_scoreboard.md` was intentionally not updated because this is instrumentation and rejected-candidate evidence, not a model status promotion, live-risk interpretation change, accepted baseline change, Shadow Candidate, or Live Switch Candidate.

Next work should test a narrow strict replay policy using only replay-compatible signal volatility / volume context, or continue queued/opened freshness shadow accumulation. Do not hard-code the live-only chain-lag or staleness thresholds into runtime.
