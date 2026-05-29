# Fast-Profit Shadow Evaluator Follow-Up

## Question

Can the existing action-policy `continue_hold` shadow candidate produce live-aligned evidence on the May 29 live stream, and does the newest fast-profit reject pocket justify a quick-profit branch or continued `continue_hold` shadowing?

## Entry Evidence

- Current live model: `data/models/20260519_v95_v84_selective_nearmiss_gate`.
- Live risk unchanged: `.env` keeps `POSITION_SIZE=0.10`; this round is read-only.
- Bot/collector health at entry: both running under `memectl`, tmux sessions `meme-bot` / `meme-collector`, no open positions in `data/bot_state.json`.
- Prior material evidence: `docs/research/20260529-bootstrap-uncertainty-gate/` promoted the release-only `continue_hold` branch to `Shadow Candidate`; it did not authorize live switch.
- Prior caution: broad/static quick-profit overlays have repeatedly failed stress, win-rate, or final gates, so quick-profit needs fresh support rather than another parameter sweep.

## Hypothesis Portfolio

| Rank | Direction | Expected Impact | Evidence | Falsification Rule |
|---:|---|---|---|---|
| 1 | Full-day live shadow evaluator for the existing `continue_hold` router | High | Existing strict replay and uncertainty-gate `Shadow Candidate`; live stream has multiple queued trades today | Reject if live shadow has no matched queued trades, no activation evidence, or routes only losses without release hits |
| 2 | Quick-profit structural replay on newest `fast_profit` / `fast_profit_then_collapse` rejects | Medium | Fresh live attribution has quick-profit-shaped rejects, but current same-shape counts are below support and prior quick-TP branches failed | Reject or defer if support stays below same-shape threshold or repeats broad quick-TP failure mode |
| 3 | Trade-delta meta gate for the `continue_hold` branch | Medium | Trade-delta tooling exists and previous replay deltas were positive, but today's question is live alignment first | Defer if live shadow cannot produce enough matched route outcomes |

Selected direction: rank 1. It is the closest path to improving the live decision because it tests whether the already replay-positive `continue_hold` candidate is active on real queued trades before any live-risk switch.

## Research Evidence

This round reuses committed SmartSearch-backed artifacts rather than starting a new outside-method search:

- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`: bootstrap/top-winner dependency gate says the `conditional_exit_continue_hold` candidate is `Shadow Candidate`, not live switch.
- `docs/research/20260529-conditional-exit-early-profit-refresh/summary.md`: path-dependent triple-barrier/meta-label evidence supports conditional exits and release-only `continue_hold` over blanket quick-profit exits.
- `docs/research/20260529-live-shadow-router-evaluator/summary.md`: prior smaller live shadow pass requested activation-aware path outcomes before runtime enablement.

New live-derived angle: refresh the same read-only shadow evaluator across the full May 29 stream so the current-day queued trades are included, then add activation/release outcome attribution.

## Commands

```bash
venv/bin/python scripts/probe_live_trade_attribution.py \
  --since '2026-05-29 21:19:42' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --output-json data/replay_reports/live_trade_attribution_20260529_fast_profit_shadow_followup.json \
  --output-md data/replay_reports/live_trade_attribution_20260529_fast_profit_shadow_followup.md \
  --max-candidate-sample 200 \
  --force

venv/bin/python scripts/probe_action_policy_live_shadow.py \
  --since '2026-05-29 21:19:42' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --output-json data/replay_reports/action_policy_live_shadow_20260529_fast_profit_shadow_followup.json \
  --output-md data/replay_reports/action_policy_live_shadow_20260529_fast_profit_shadow_followup.md \
  --max-sample-rows 120 \
  --force

venv/bin/python scripts/probe_action_policy_live_shadow.py \
  --since '2026-05-29 00:00:00' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --output-json data/replay_reports/action_policy_live_shadow_20260529_full_day.json \
  --output-md data/replay_reports/action_policy_live_shadow_20260529_full_day.md \
  --max-sample-rows 200 \
  --force

venv/bin/python scripts/probe_action_policy_activation_shadow.py \
  --since '2026-05-29 00:00:00' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --output-json data/replay_reports/action_policy_activation_shadow_20260529_full_day.json \
  --output-md data/replay_reports/action_policy_activation_shadow_20260529_full_day.md \
  --max-sample-rows 200 \
  --force
```

## Results

### Post-last-trade attribution

Report: `data/replay_reports/live_trade_attribution_20260529_fast_profit_shadow_followup.json` / `.md`.

- Closed trades since `2026-05-29 21:19:42`: `0`.
- Signal decisions: `1552`; per-token candidates: `103`.
- Barrier classes: `fast_profit=3`, `fast_profit_then_collapse=3`, `slow_runner=2`, `flat_timeout=11`, `stop_first=7`, `missing_path=77`.
- Recommended policies: `quick_take_profit=6`, `conditional_slow_hold=2`, `skip=95`.
- Same-shape quick-profit support stayed below the minimum gate, so the quick-profit branch was not selected as the next replay direction.

### Narrow post-last-trade live shadow

Report: `data/replay_reports/action_policy_live_shadow_20260529_fast_profit_shadow_followup.json` / `.md`.

- Signal count: `1527`.
- Queued signal count: `0`.
- Matched live trades: `0`.
- Shadow-used signals: `18`, all `continue_hold` on rejected rows.
- Decision: `insufficient_shadow_support` for this narrow window. This rejects the narrow-window shadow probe only; it does not reject the full-day live-shadow direction.

### Full-day live shadow

Report: `data/replay_reports/action_policy_live_shadow_20260529_full_day.json` / `.md`.

- Signal count: `12761`.
- Queued signal count: `9`.
- Matched signal rows: `32`; unique matched live trades: `7`.
- Shadow-used signals: `76`; queued shadow-used signals: `9`.
- Shadow routes: `continue_hold=76`, `skip=12685`; no quick-profit route won support.
- Queued shadow-used matched trades: `7`; matched net profit: `+0.00010067417568420197` BNB.
- Decision: `candidate_shadow_support`.

### Activation-aware shadow

Report: `data/replay_reports/action_policy_activation_shadow_20260529_full_day.json` / `.md`.

- Queued shadow-used matched trades: `7`.
- Matched net profit: `+0.00010067417568420197` BNB.
- Activation hits at `+35%`: `3`.
- Release hits at `+75%`: `2`.
- Activated then stop: `1`.
- Stop before activation: `0`.
- Outcomes: `activated_released=2`, `activated_then_stop=1`, `never_activated_loss=4`.
- Decision: `mixed_activation_shadow_support`.

Per-trade activation outcome summary:

| Symbol | Outcome | MFE | MAE | Net BNB | Note |
|---|---:|---:|---:|---:|---|
| Binance light source | `activated_then_stop` | `42.1759%` | `-48.1132%` | `-0.00015238787562031852` | Risk case for any live enablement. |
| 币安光源 | `activated_released` | `113.5298%` | `9.8192%` | `+0.00027378227534832425` | Continue-hold release-compatible winner. |
| TripleT | `activated_released` | `86.8864%` | `-1.2580%` | `+0.00012565224901414461` | Continue-hold release-compatible winner. |
| CHILLCAT | `never_activated_loss` | `-6.4420%` | `-10.6960%` | `-0.000050867591077252965` | No activation; continue-hold would not force a PPO hold. |
| 未来 | `never_activated_loss` | `-5.8938%` | `-13.1974%` | `-0.00004512376073509866` | No activation; continue-hold would not force a PPO hold. |
| CRYPTOMAXXING | `never_activated_loss` | `-1.9798%` | `-1.9805%` | `-0.00002525822459603866` | No activation; continue-hold would not force a PPO hold. |
| 42 | `never_activated_loss` | `-1.6596%` | `-1.9791%` | `-0.000025122896649558077` | No activation; continue-hold would not force a PPO hold. |

## Tiered Evaluation

Outcome tier: `Shadow Candidate` / material shadow-only evidence, not `Live Switch Candidate`.

Reasoning:

- Validation/final/walk-forward/stress support comes from the previously committed `continue_hold` strict replay and bootstrap/uncertainty gate, not from this live report alone.
- Today's live stream confirms the route is active on all queued signals that the router could score, with `7` matched live trades and positive matched net PnL.
- Activation-aware outcomes are mixed: `2` release-compatible winners, `1` activated stop, and `4` never-activated losses.
- No new quick-profit branch is justified: fresh quick-profit-shaped rejects are below same-shape support, and the full-day router selected `0` quick-profit routes.
- No live switch: support is still small, one activated-stop loss remains unexplained, and live-risk review has not been run.

## Business Decision

Keep live config unchanged. Preserve this as material shadow-only evidence for the release-only `continue_hold` branch and use it to guide the next optimization direction:

1. Continue collecting activation-aware live shadow outcomes.
2. Before live cutover, test whether an activation-aware risk filter can separate `activated_then_stop` from `activated_released` without losing the two release-compatible winners.
3. Do not run another broad quick-profit replay from this pocket unless future live attribution exceeds support gates.

`docs/model_scoreboard.md` was updated in the same boundary because this round changes the live-shadow evidence and next model direction.
