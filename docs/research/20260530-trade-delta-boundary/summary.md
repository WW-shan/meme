# 2026-05-30 Trade-Delta Boundary Replay

## Live State

- Bot and collector were running under `memectl` in `meme-bot` / `meme-collector`.
- `data/bot_state.json` had no open positions and balance `0.002752730398351113` BNB.
- Live config remained unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, and empty `FIXED_STAKE_BNB`.
- Latest boundary commit before this experiment was `7ca0920246fa962c18ab46351511fb1f3755434f`, pushed to `origin/main`, with GitHub Actions `CI` run `26655917188` passing.

## Live Attribution

Artifact: `data/replay_reports/live_trade_attribution_20260530_current_round.json` / `.md`.

Since `2026-05-29 21:19:42`, there were `0` closed trades, `2111` signal decisions, and `151` per-token rejected candidates.

Rejected path classes:

- `fast_profit=5`
- `fast_profit_then_collapse=4`
- `slow_runner=5`
- `flat_timeout=47`
- `stop_first=13`
- `missing_path=77`

The same-shape replay gate was not met for another quick-profit or slow-runner replay. That made the best current direction a structural follow-up on the already replay-positive but fragile `volceil020` runner-retention branch.

## Prior Review

Relevant prior evidence:

- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`: paired trade-delta bootstrap and top-winner dependency should decide whether a small-split candidate can be promoted.
- `docs/research/20260529-activation-risk-filter/summary.md`: activation45 remains a `Shadow Candidate`, but it is an exit-side branch rather than a direct entry-rescue fix.
- `data/replay_reports/runner_retention_candidate_gate_replay_20260529_train_boundary_soft_feature_preserve_base_volceil020_utility_label_grid.json`: the old `volceil020` control remained `Research Alpha` but not live-switch evidence because final win rate failed and final paired delta was top-winner dependent.

## Hypothesis Portfolio

1. Trade-delta boundary replay for `volceil020`.
   Expected impact high because it directly targets the known added-trade loser in the existing `Research Alpha` branch. Evidence medium/high from prior paired trade-delta. Falsifiability high through strict replay plus uncertainty gate. Selected.
2. Live shadow evaluator refresh for activation45.
   Evidence high and cost low, but less likely to immediately improve the entry model because activation45 is already a shadow candidate.
3. Missed clean runner detector.
   Expected impact medium, but latest live support was only `slow_runner=5`, below the same-shape replay gate of `7`.

## Experiment

Read-only added-trade boundary probes:

- `data/replay_reports/added_trade_boundary_policy_20260530_volceil020_utility_label_depth2.json`
- `data/replay_reports/added_trade_boundary_policy_20260530_volceil020_utility_label_depth3.json`

Both selected the same validation rule:

```text
max_price >= 7.075391670423928e-09
```

Strict replay:

```bash
venv/bin/python scripts/run_runner_retention_candidate_gate_replay.py \
  --candidate-grid-json docs/research/20260528-runner-retention-boundary-feature/train_boundary_soft_feature_preserve_base_volceil020_utility_label_grid.json \
  --preserve-base-candidates \
  --added-trade-boundary-report data/replay_reports/added_trade_boundary_policy_20260530_volceil020_utility_label_depth2.json \
  --write-selected-trade-delta \
  --output data/replay_reports/runner_retention_candidate_gate_replay_20260530_volceil020_utility_label_trade_delta_boundary.json \
  --force
```

Uncertainty gate:

```bash
venv/bin/python scripts/probe_replay_uncertainty_gate.py \
  --report data/replay_reports/runner_retention_candidate_gate_replay_20260530_volceil020_utility_label_trade_delta_boundary.json \
  --candidate-id volceil020_trade_delta_boundary_20260530 \
  --output data/replay_reports/replay_uncertainty_gate_20260530_volceil020_trade_delta_boundary.json \
  --force
```

## Result

Strict replay decision: `reject`.

Selected validation candidate:

- Candidate index: `1`
- `buy_runner_retention_label_min_utility_score=45.0`
- `buy_runner_retention_label_mfe_weight=1.0`
- `buy_runner_retention_label_mae_penalty=0.5`
- `buy_path_state_meta_gate_min_score=0.75`
- Added-trade boundary: `max_price >= 7.075391670423928e-09`

Validation baseline vs selected:

- Net profit BNB: `0.022842003299 -> 0.023438939618`
- Trades: `38 -> 42`
- Win rate: `0.815789 -> 0.785714`
- Max drawdown: `-10.187954% -> -10.075505%`
- Walk-forward worst return: `101.883108% -> 105.899132%`
- Walk-forward worst max drawdown: `-13.229438% -> -15.540216%`
- Stress worst net profit BNB: `0.011661288085 -> 0.012646300101`
- Stress worst max drawdown: `-6.777130% -> -7.635925%`

Final baseline vs selected:

- Net profit BNB: `0.001503449730 -> 0.002026624320`
- Trades: `17 -> 18`
- Win rate: `0.647059 -> 0.611111`
- Max drawdown: `-16.256141% -> -15.160846%`
- Walk-forward worst return: `-3.184010% -> 1.445882%`
- Walk-forward worst max drawdown: `-17.913261% -> -17.747333%`
- Stress worst net profit BNB: `-0.000373976890 -> 0.000186462547`
- Stress worst max drawdown: `-31.511910% -> -26.687670%`

Paired uncertainty gate classified the candidate as `Research Alpha`, not `Shadow Candidate`:

- Validation observed paired delta: `+114.845627%`
- Validation bootstrap positive probability: `0.62875`
- Validation top-1 removal delta: `-130.216507%`
- Validation top-3 removal delta: `-233.285806%`
- Final observed paired delta: `+99.273762%`
- Final bootstrap positive probability: `0.64675`
- Final top-1 removal delta: `-87.411517%`
- Final top-3 removal delta: `-184.194653%`

Shadow blockers:

- validation positive probability below shadow threshold
- validation top-1 and top-3 winner dependency
- final positive probability below shadow threshold
- final top-1 and top-3 winner dependency
- validation strict acceptance gate failed on stress drawdown, walk-forward drawdown, and win rate
- final strict acceptance gate still failed

## Outcome

Tier: `Research Alpha` for the underlying runner-retention evidence, but this boundary is rejected as a shadow/live promotion.

The experiment improves validation and final net profit, and final drawdown/stress are better than baseline. However, the edge is still fragile:

- validation risk guardrails worsened on walk-forward and stress drawdown
- win rate fell on both validation and final
- final added trades were `5` trades with only `1` win and `4` losses
- removing the top positive contribution flips both validation and final paired delta negative

Decision: no live switch, no `.env` change, no model artifact change, no threshold/sizing/runtime change, and no bot restart. Keep the result as `Research Alpha` evidence only. Do not continue runner-retention parameter or label micro-sweeps from this branch unless new live evidence changes the population; the next direction should be structurally different, such as live shadow evaluation or a conditional-exit refinement.

## Scoreboard

`docs/model_scoreboard.md` was updated for this boundary because the result changes the runner-retention branch status: the added-trade boundary strengthens the `Research Alpha` evidence but does not promote it to shadow.
