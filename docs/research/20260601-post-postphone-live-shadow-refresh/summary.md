# Post-Postphone Guarded Live Shadow Refresh

Date: 2026-06-01

## Outcome

Rejected for live switch and rejected for shadow promotion.

This round added default-off probe support for replaying the existing activation45 hazard guard in live shadow reports, then reran the freshest post-phone rejected stream. The guarded router produced no shadow-used signals and no matched live trades, so it does not justify enabling the action-policy router branch.

No live runtime, `.env`, model artifact, threshold, sizing, buy/sell logic, bot/collector process, restart, or live switch changed.

## Live State

- Bot and collector were running under `memectl` and tmux.
- Open positions: `0`; `data/bot_state.json` positions are `{}`.
- Balance snapshot: `0.002140813491977969` BNB.
- Live model: `data/models/20260519_v95_v84_selective_nearmiss_gate`.
- Latest real trade remains `手机`, opened at `2026-06-01 00:48:27` and closed at `2026-06-01 00:58:01` by `TIME_EXIT` for `-0.000023685576496972164` BNB.
- Recent logs show bot/collector activity and repeated listener catch-up around `51-53` blocks behind, with no fatal traceback in the inspected tails.

## Hypothesis Portfolio

1. Guarded activation45 live shadow refresh.
   Expected impact is medium and falsifiability is high because it can test whether the already replayed hazard guard produces read-only live support without changing risk. Selected.
2. Replay-compatible execution freshness feature work.
   Expected impact is high from prior Research Alpha evidence, but implementation cost is higher and the freshest rejected stream does not add queued/opened freshness support.
3. Conditional quick-profit / early-profit harvest.
   Expected impact is medium after the new `绷` path, but same-shape support is only one fresh candidate, so it should be a next structural probe rather than a live change.

## Commands

```bash
venv/bin/python scripts/probe_live_trade_attribution.py \
  --since '2026-06-01 01:15:00' \
  --until '2026-06-01 02:15:00' \
  --recent-lifecycle-files 128 \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --output-json data/replay_reports/live_trade_attribution_20260601_post_postphone_live_refresh.json \
  --output-md data/replay_reports/live_trade_attribution_20260601_post_postphone_live_refresh.md \
  --max-candidate-sample 200 \
  --force
```

```bash
venv/bin/python scripts/probe_action_policy_live_shadow.py \
  --since '2026-06-01 01:15:00' \
  --until '2026-06-01 02:15:00' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --router-min-prob 0.988 \
  --router-max-pred-return 45.0 \
  --output-json data/replay_reports/action_policy_live_shadow_20260601_post_postphone_activation45_guard.json \
  --output-md data/replay_reports/action_policy_live_shadow_20260601_post_postphone_activation45_guard.md \
  --max-sample-rows 200 \
  --force
```

```bash
venv/bin/python scripts/probe_action_policy_activation_shadow.py \
  --since '2026-06-01 01:15:00' \
  --until '2026-06-01 02:15:00' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --recent-lifecycle-files 128 \
  --activation-pct 45.0 \
  --release-pct 75.0 \
  --router-min-prob 0.988 \
  --router-max-pred-return 45.0 \
  --output-json data/replay_reports/action_policy_activation_shadow_20260601_post_postphone_activation45_guard.json \
  --output-md data/replay_reports/action_policy_activation_shadow_20260601_post_postphone_activation45_guard.md \
  --max-sample-rows 200 \
  --force
```

```bash
venv/bin/python scripts/probe_flow_abstention_feature_scan.py \
  --input-report data/replay_reports/live_trade_attribution_20260601_post_postphone_live_refresh.json \
  --output data/replay_reports/flow_abstention_feature_scan_20260601_post_postphone_live_refresh.json \
  --min-selected 2 \
  --force
```

## Results

Live attribution over `2026-06-01 01:15:00` through `2026-06-01 02:15:00`:

- Closed trades: `0`.
- Signal decisions: `139`.
- Per-token rejected candidates: `10`.
- Barrier classes: `flat_timeout=9`, `fast_profit_then_collapse=1`.
- Ranked directions: `rejected_fast_profit_then_collapse_quick_take_profit_replay` count `1`; `rejected_flat_timeout_skip_replay` count `9`.
- Decision: `NO_GO_FOR_LIVE_SWITCH`.

Guarded action-policy live shadow:

- Runtime guard: `buy_action_policy_router_min_prob=0.988`, `buy_action_policy_router_max_pred_return=45.0`.
- Signals scored: `139`, all rejected.
- Shadow routes: `skip=137`, `continue_hold=2`.
- Shadow reasons: `non_continue_hold_route=137`, `prob_below_min=2`.
- Shadow-used signals: `0`; queued shadow-used matched trades: `0`.
- Decision: `insufficient_shadow_support`.

Activation-aware guarded shadow:

- Activation/release: `45% / 75%`.
- Queued shadow-used matched trades: `0`.
- Activation hits: `0`; release hits: `0`; activated-then-stop: `0`.
- Decision: `insufficient_activation_shadow_support`.

Fresh flow scan:

- Candidate rows: `10`.
- Outcomes: `flat_timeout=9`, `fast_profit_then_collapse=1`.
- Eligible one-rule cuts mostly isolate the nine flat-timeout skips and have no protected class support beyond the single `绷` example, so this is diagnostic only.

## Watchpoints

- `TetherAI`: `prob=0.9320889890224385`, `PredReturn=40.14741071813559`, MFE `+1.0778186253325384%`, MAE `-16.49151920741391%`; classified `flat_timeout` / `skip`.
- `DiddyButt`: `prob=0.981941074305537`, `PredReturn=8.673169457981977`, MFE `+7.368552934468142%`, MAE `-13.661670484156186%`; classified `flat_timeout` / `skip`.
- `绷`: `prob=0.9861301029760093`, `PredReturn=-3.5090795581680494`, `volume_30s=2.762079206940594`, MFE `+226.5028121997165%`, MAE `-20.985212898098037%`, `+25%` in `4.366549s`, `-18%` in `31.366549s`; classified `fast_profit_then_collapse` with `quick_take_profit` policy hint.

## Decision

No live switch and no shadow promotion.

The guarded activation45 branch filtered the broad-router `continue_hold` attempts and produced no actionable live support. The newest useful live-derived angle is not runner retention; it is a single quick-profit / early-harvest reject. Same-shape support is too thin for live action, but it is a concrete next structural falsification target.

`docs/model_scoreboard.md` was intentionally not updated because no model candidate, replay candidate, accepted baseline, live-risk interpretation, or outcome tier changed. This milestone records a rejected shadow-support refresh and a tooling improvement only.
