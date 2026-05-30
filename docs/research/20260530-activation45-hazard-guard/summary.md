# Activation45 Hazard Guard

Date: 2026-05-30

## Outcome

Tier: `Research Alpha`, not `Shadow Candidate` and not live-switch evidence.

This round tested a live-shadow-derived activation45 hazard guard:

- `buy_action_policy_router_min_confidence=0.40`
- `buy_action_policy_continue_hold_activation_pct=0.45`
- `buy_action_policy_continue_hold_release_pct=0.75`
- `buy_action_policy_router_min_prob=0.988`
- `buy_action_policy_router_max_pred_return=45.0`

The guard preserves the activation45 branch's strict replay lift versus the no-router baseline, but it does not add headline PnL over the activation45 control. Its practical value is exposure reduction: in validation, the control had `27` continue-hold entries and `107` forced holds, while the selected guard kept the same headline metrics with `11` continue-hold entries and `69` forced holds.

## Live Trigger

Fresh attribution report: `data/replay_reports/live_trade_attribution_20260530_activation45_hazard_guard_entry.md`.

No closed live trades were present. Recent rejected-signal paths still showed action-policy shapes:

- `fast_profit=13`
- `fast_profit_then_collapse=9`
- `slow_runner=12`
- `stop_first=34`
- `flat_timeout=139`

The new angle came from the latest activation45 live-shadow artifact, `data/replay_reports/action_policy_activation_shadow_20260530_activation45_after_unsupported_quote_alpha_full_day.json`: matched queued shadow-used trades had `2` activated-release winners and `5` never-activated losses. The two release winners had `prob>=0.988` and `PredReturn<=45`; the largest never-activated loss had `prob=0.9880821435743425` and `PredReturn=75.63785656871322`.

## Research

SmartSearch Deep Research artifacts:

- `00-deep-plan.json`
- `01-search.json`
- `02-fetch-hudson-meta-labeling.md`
- `03-fetch-coinbureau-bot-validation.md`
- `04-fetch-devto-meta-labeling.md`

The useful method constraints from fetched evidence were:

- Treat the router as a primary model and the guard as a secondary/meta filter.
- Use decision-time features only.
- Require out-of-sample, walk-forward, stress, and paired-delta evidence.
- Track the accuracy/coverage tradeoff and avoid overfitting small-split results.

## Experiment

Grid: `docs/research/20260530-activation45-hazard-guard/activation45_hazard_guard_grid.json`

Replay command:

```bash
venv/bin/python scripts/run_action_policy_router_replay.py \
  --candidate-grid-json docs/research/20260530-activation45-hazard-guard/activation45_hazard_guard_grid.json \
  --output data/replay_reports/action_policy_router_replay_20260530_activation45_hazard_guard.json \
  --write-selected-trade-delta \
  --force
```

Uncertainty command:

```bash
venv/bin/python scripts/probe_replay_uncertainty_gate.py \
  --report data/replay_reports/action_policy_router_replay_20260530_activation45_hazard_guard.json \
  --candidate-id activation45_prob988_predret45_guard \
  --output data/replay_reports/replay_uncertainty_gate_20260530_activation45_hazard_guard.json \
  --force
```

Selected candidate index: `1`.

## Strict Replay Result

Validation baseline to selected:

- Net profit: `0.022842003299308057 -> 0.022991375192791326` BNB
- Trades: `38 -> 38`
- Win rate: `0.8157894736842105 -> 0.8157894736842105`
- Max drawdown: `-10.187954315383251 -> -10.187954315383251`
- Walk-forward worst return: `101.88310806253628 -> 103.01533998554144`
- Stress worst net profit: `0.011661288085332917 -> 0.012392324169094096`

Final baseline to selected:

- Net profit: `0.002032913328044796 -> 0.0023052101782534947` BNB
- Trades: `18 -> 18`
- Win rate: `0.6666666666666666 -> 0.6666666666666666`
- Max drawdown: `-16.256141287806237 -> -15.359148087854347`
- Walk-forward worst return: `-5.576361956610565 -> -5.576361956610565`
- Stress worst net profit: unchanged at `-0.00006618025046541479` BNB

The strict replay script returned `decision=accept`, with all validation and final acceptance sub-gates passing.

## Paired Delta / Uncertainty

Uncertainty report: `data/replay_reports/replay_uncertainty_gate_20260530_activation45_hazard_guard.json`.

Validation paired delta:

- Common-trade return delta: `+28.34371169260293%`
- Improved/worsened common trades: `2 / 0`
- Bootstrap positive probability: `0.863`
- Top-1 dependency: `false`

Final paired delta:

- Common-trade return delta: `+51.669047215926945%`
- Improved/worsened common trades: `1 / 0`
- Bootstrap positive probability: `0.63525`
- Top-1 dependency: `true`

Shadow blockers:

- `final_positive_probability_below_shadow_min`
- `final_top1_winner_dependent`

## Decision

Do not switch live. Do not change `.env`, model artifacts, thresholds, sizing, bot process, or runtime config.

Keep this as `Research Alpha`: the hazard guard is useful because it preserves activation45 replay improvement while reducing router exposure, but the final evidence is still too dependent on one improved trade. The next activation45 work should either collect more live-shadow rows or train/test a richer decision-time selector that improves multiple final trades, not just a single top contributor.
