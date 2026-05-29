# 2026-05-30 Structural Alpha Round

## Live State

- Bot and collector were running under `memectl` in tmux sessions `meme-bot` and `meme-collector`.
- `data/bot_state.json` showed no open positions and balance `0.002752730398351113` BNB.
- Live config remained unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, and 10% live sizing.
- Collector was running but recent logs still showed recurring catch-up warnings around 50-77 blocks behind.

## Live Attribution

Artifact: `data/replay_reports/live_trade_attribution_20260530_structural_alpha_round.json` / `.md`.

Since `2026-05-29 21:19:42`, there were no new closed trades, but the live stream had `1711` signal decisions and `122` per-token rejected candidates. Rejected path classes were:

- `fast_profit=7`
- `fast_profit_then_collapse=8`
- `slow_runner=4`
- `flat_timeout=79`
- `stop_first=24`

The fresh quick-profit-shaped support now reaches `15` candidates, crossing the same-shape support threshold that the earlier `20260529-fast-profit-shadow-evaluator` window did not meet.

## Prior Review And Direction Selection

The quick-profit pocket is real, but prior scoreboard evidence says broad quick-profit overlays have repeatedly over-expanded trades, weakened win rate, failed stress, or failed final confirmation. The strongest current structural candidate is still the `+45%` activation conditional-exit branch because it already improved strict validation/final replay without adding trades.

Hypothesis portfolio:

| Rank | Direction | Decision |
|---:|---|---|
| 1 | `+45%` activation conditional-exit uncertainty/shadow refresh | Selected; highest evidence and lowest implementation risk |
| 2 | Rejected fast-profit / fast-profit-then-collapse quick-profit replay | Defer; fresh support crossed gate, but prior broad quick-TP failures make this the next falsification candidate, not the first move |
| 3 | Decision-time selector for `never_activated_loss` rows | Defer; prior low-flow selector failed out of sample |
| 4 | Missed slow-runner detector | Defer; current support is only `4`, below same-shape gate |

## Research Evidence

This round reused recent SmartSearch-backed artifacts rather than starting a new method search:

- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`
- `docs/research/20260529-activation-risk-filter/summary.md`

New live-derived angle: before diverting into a historically fragile quick-profit branch, test whether the already replay-positive `+45%` activation branch remains material after bootstrap/paired-delta uncertainty and refreshed live shadow evidence.

## Experiment

```bash
venv/bin/python scripts/probe_replay_uncertainty_gate.py \
  --report data/replay_reports/action_policy_router_replay_20260529_activation45_trade_delta.json \
  --candidate-id action_router_activation45_uncertainty_20260530 \
  --output data/replay_reports/replay_uncertainty_gate_20260530_activation45.json

venv/bin/python scripts/probe_action_policy_activation_shadow.py \
  --since '2026-05-29 00:00:00' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --activation-pct 45 \
  --release-pct 75 \
  --output-json data/replay_reports/action_policy_activation_shadow_20260530_activation45_full_day_refresh.json \
  --output-md data/replay_reports/action_policy_activation_shadow_20260530_activation45_full_day_refresh.md \
  --max-sample-rows 240
```

## Results

Uncertainty gate artifact: `data/replay_reports/replay_uncertainty_gate_20260530_activation45.json`.

- Outcome tier: `Shadow Candidate`.
- Decision: `paired_delta_uncertainty_shadow_candidate`.
- Rejection reasons: none.
- Shadow blockers: none.
- Validation paired-delta contributions: `38`; observed delta `+28.34371169260293%`; bootstrap positive probability `0.863`; no negative contributions; top-1 removal still `+10.912578033091052%`.
- Final paired-delta contributions: `17`; observed delta `+96.12071561162495%`; bootstrap positive probability `0.96875`; no negative contributions; top-1 removal still `+44.451668395698%`.
- Strict replay gate context passed on validation and final.

Refreshed activation shadow artifact: `data/replay_reports/action_policy_activation_shadow_20260530_activation45_full_day_refresh.json` / `.md`.

- Queued shadow-used matched trades: `7`.
- Matched net profit: `+0.00010067417568420197` BNB.
- Outcomes: `activated_released=2`, `never_activated_loss=5`.
- `activated_then_stop=0`, `stop_before_activation=0`.

## Tier

`Shadow Candidate` / material shadow-only evidence, not `Live Switch Candidate`.

The candidate remains no-switch because runtime enablement still needs live-risk review, zero-position cutover, and enough shadow/paper evidence. It also leaves `never_activated_loss` rows unresolved. No `.env`, model artifact, threshold, sizing, bot process, or runtime behavior changed.

## Scoreboard Decision

`docs/model_scoreboard.md` was updated because this round strengthens the evidence tier and records the new live-derived quick-profit support state.

Next best experiment if continuing this line: do not sweep activation thresholds again; either test a stricter, non-broad quick-profit falsification from the now-supported rejected pocket, or build a non-scalar selector for the remaining `never_activated_loss` cohort.
