# Post-Phone Reject Refresh

Date: 2026-06-01
Status: Rejected for promotion

## Question

After the `手机` TIME_EXIT loss closed, does the immediate post-close rejected-signal stream add enough support for a replay promotion, an action-policy shadow route, or stronger signal-freshness split evidence?

This is not a new method search. It reuses the existing live attribution, action-policy live-shadow, and signal-freshness split probes from the current execution-freshness research path. No new SmartSearch run was needed.

## Artifacts

- Live attribution: `data/replay_reports/live_trade_attribution_20260601_post_phone_reject_refresh.json`
- Live attribution markdown: `data/replay_reports/live_trade_attribution_20260601_post_phone_reject_refresh.md`
- Action-policy live shadow: `data/replay_reports/action_policy_live_shadow_20260601_post_phone_reject_refresh.json`
- Action-policy live shadow markdown: `data/replay_reports/action_policy_live_shadow_20260601_post_phone_reject_refresh.md`
- Signal-freshness split shadow: `data/replay_reports/signal_freshness_shadow_20260601_post_phone_reject_refresh.json`
- Signal-freshness split shadow markdown: `data/replay_reports/signal_freshness_shadow_20260601_post_phone_reject_refresh.md`

## Commands

```bash
venv/bin/python scripts/probe_live_trade_attribution.py \
  --since '2026-06-01 00:58:01' \
  --recent-lifecycle-files 96 \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --output-json data/replay_reports/live_trade_attribution_20260601_post_phone_reject_refresh.json \
  --output-md data/replay_reports/live_trade_attribution_20260601_post_phone_reject_refresh.md \
  --max-candidate-sample 160 \
  --force
```

```bash
venv/bin/python scripts/probe_action_policy_live_shadow.py \
  --since '2026-06-01 00:58:01' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --decision rejected \
  --decision queued \
  --output-json data/replay_reports/action_policy_live_shadow_20260601_post_phone_reject_refresh.json \
  --output-md data/replay_reports/action_policy_live_shadow_20260601_post_phone_reject_refresh.md \
  --max-sample-rows 120 \
  --force
```

```bash
venv/bin/python scripts/probe_signal_freshness_shadow.py \
  --since '2026-06-01 00:58:01' \
  --recent-lifecycle-files 96 \
  --output-json data/replay_reports/signal_freshness_shadow_20260601_post_phone_reject_refresh.json \
  --output-md data/replay_reports/signal_freshness_shadow_20260601_post_phone_reject_refresh.md \
  --max-candidate-sample 120 \
  --split-stability \
  --force
```

## Results

Live attribution:

- Closed trades: `0`
- Signal decisions: `55`
- Per-token rejected candidates: `7`
- Barrier classes: `flat_timeout=6`, `slow_runner=1`
- Ranked directions: `rejected_slow_runner_conditional_slow_hold_replay` with only `1` candidate, below the `7` same-shape minimum.
- Decision: `NO_GO_FOR_LIVE_SWITCH`

The single slow-runner watchpoint was `Cube`, first seen at `2026-06-01 01:00:22.556830`. It reached `+46.993145095386815%` MFE after signal, but its signal was below current entry quality: `prob=0.9772729778670873`, `PredReturn=-2.2983691526723984`, `volume_30s=1.5114580947395162`, and `price_volatility=0.0699030218147247`. This is useful watchlist evidence, not a replay trigger.

Action-policy live shadow:

- Signals: `56`
- Queued signals: `0`
- Matched live trades: `0`
- Shadow-used signals: `0`
- Router routes: `skip=56`
- Decision: `insufficient_shadow_support`

Signal-freshness split shadow:

- Outcome tier: `Rejected`
- Decision: `insufficient_signal_freshness_split_support`
- Signal decisions: `56`
- Per-token freshness candidates: `8`
- Decisions represented: `8` rejected, `0` queued
- Barrier classes: `flat_timeout=7`, `slow_runner=1`
- Selected rule: `lifecycle_status_fast_status_eligible == false`
- All-window selected precision: `7/8` correct skips with `1` opportunity miss
- Stable rules: `0`; train-eligible rules: `0/11`

## Decision

Do not promote this post-close slice. It does not change the current conclusion:

- Execution freshness remains `Research Alpha` from the broader accepted-trade paired-delta evidence, but still not `Shadow Candidate` or live-switch evidence.
- The narrow post-close rejected stream is too small for a slow-runner replay and contains no queued/opened freshness support.
- The action-policy router agrees with skipping every post-close signal in this window.

No `.env`, model artifact, threshold, sizing, buy/sell logic, bot process, collector process, runtime enablement, restart, or live switch changed.

Scoreboard: `docs/model_scoreboard.md` was intentionally not updated because this boundary does not change the model conclusion, live-risk interpretation, or next model direction. It is a thin negative refresh that preserves the latest post-`手机` rejected-signal evidence.

## Next Step

Keep the active node in collection / replay-compatibility mode:

1. Continue accumulating queued/opened signal-freshness support before trying to promote a freshness gate.
2. Only revisit slow-runner replay if multiple new same-shape `Cube`-like candidates appear under stronger signal quality.
3. Do not hard-code live chain-lag or fast-status thresholds without strict replay-equivalent context.
