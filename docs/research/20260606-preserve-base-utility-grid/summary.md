# 2026-06-06 Preserve-Base Utility Grid

## Live State

- Bot and collector were running under `./tools/memectl` in the expected `meme-bot` and `meme-collector` tmux sessions.
- `data/bot_state.json` showed balance `0.001525176567509963` BNB and no open positions.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, and `MIN_ENTRY_VOLUME_30S=1.5`.
- Latest public boundary before this experiment was `cc61fceaa6aa93e18f15583f52410cc33ab06cbb`, pushed to `origin/main`, with GitHub Actions `CI` run `27063104969` passing.
- Recent logs still showed listener catch-up warnings, but no sampled open-position risk or failed buy/sell loop requiring a restart.

## Live Attribution

Fresh attribution artifacts:

- `data/replay_reports/live_trade_attribution_20260606_preserve_base_utility_grid_entry.json`
- `data/replay_reports/live_trade_attribution_20260606_preserve_base_utility_grid_entry.md`

There were no new closed trades since the `2026-06-02 21:27:41` close. The attribution report scanned `9727` signal decisions and found `969` per-token rejected candidate paths. Barrier classes were `fast_profit=34`, `fast_profit_then_collapse=29`, `slow_runner=22`, `flat_timeout=732`, and `stop_first=152`; recommended policies were `quick_take_profit=63`, `conditional_slow_hold=22`, and `skip=884`.

The report stayed `NO_GO_FOR_LIVE_SWITCH` and `safe_for_live_switch=false`. The same-shape live evidence was enough to finish the open preserve-base volceil020 utility-label falsifier, but not enough for a direct runtime change.

## Prior Research Reused

No new SmartSearch pass was opened because this experiment reused already committed research and replay tooling:

- `docs/research/20260528-runner-retention-boundary-feature/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`
- `docs/research/20260530-slow-runner-support-refresh/summary.md`

The explicit goal for this node was to rerun the preserve-base volceil020 utility-label grid on current data, classify it with the latest four-tier uncertainty gate, and stop runner-retention micro-sweeps if the result did not reach `Research Alpha`.

## Hypothesis

Because live evidence still showed rejected slow-runner paths and prior preserve-base volceil020 runs improved net profit while preserving base candidates, rerun the utility-label grid with current lifecycle data. Expected result was at least `Research Alpha` if the edge remained reproducible.

Falsification rule: reject utility-label continuation if validation/final net profit or expected utility did not improve, strict risk gates deteriorated materially, trade count or win rate collapsed, or paired delta remained too uncertain or top-winner dependent for the tiered gate.

## Experiment

Replay command:

```bash
venv/bin/python scripts/run_runner_retention_candidate_gate_replay.py \
  --candidate-grid-json docs/research/20260528-runner-retention-boundary-feature/train_boundary_soft_feature_preserve_base_volceil020_utility_label_grid.json \
  --preserve-base-candidates \
  --write-selected-trade-delta \
  --output data/replay_reports/runner_retention_candidate_gate_replay_20260606_preserve_base_volceil020_utility_label_grid.json \
  --force
```

Uncertainty command:

```bash
venv/bin/python scripts/probe_replay_uncertainty_gate.py \
  --report data/replay_reports/runner_retention_candidate_gate_replay_20260606_preserve_base_volceil020_utility_label_grid.json \
  --candidate-id preserve_base_volceil020_utility_label_20260606 \
  --output data/replay_reports/replay_uncertainty_gate_20260606_preserve_base_volceil020_utility_label_grid.json \
  --force
```

Strict assumptions were `position_fraction=0.1`, `max_position_fraction=0.1`, `max_open_positions=8`, `skip_all_in_replay=true`, and no fixed stake.

## Results

- Old strict replay decision: `accept`.
- Four-tier uncertainty decision: `Rejected` / `uncertainty_gate_rejected`.
- Candidate count: `13`.
- Selected candidate index: `4`.
- Selected candidate used `buy_runner_retention_rescue_max_entry_price_volatility=0.2`, utility label weights `mfe=1.0`, `mae_penalty=1.0`, `min_utility_score=35.0`, preserve-base candidates, and the train-boundary soft feature.
- Validation baseline: `23` trades, net profit `0.012252343033424175` BNB, win rate `0.7391304347826086`, max drawdown `-7.361964742920057%`, walk-forward worst return `2.8446315943470024%`, and stress worst net profit `0.004609956337437153` BNB.
- Validation candidate: `23` trades, net profit `0.012621051870639492` BNB, win rate `0.7391304347826086`, max drawdown `-7.361964742920057%`, walk-forward worst return `2.8446315943470024%`, and stress worst net profit `0.00496695959973896` BNB.
- Final baseline: `22` trades, net profit `0.001960790463800862` BNB, win rate `0.5454545454545454`, max drawdown `-18.206422038627302%`, walk-forward worst return `-3.927696685669879%`, and stress worst net profit `-0.0003650458326306498` BNB.
- Final candidate: `22` trades, net profit `0.0022064021728842717` BNB, win rate `0.5454545454545454`, max drawdown `-18.206422038627302%`, walk-forward worst return `-3.927696685669879%`, and stress worst net profit `-0.00019694988802181068` BNB.

The old strict gate accepted because headline validation/final profit and stress profit improved without worsening trade count, win rate, drawdown, or walk-forward metrics.

The uncertainty gate rejected because paired trade-delta evidence was weak and concentrated:

- Rejection reason: `final_positive_probability_below_research_min`.
- Shadow blockers: `validation_positive_probability_below_shadow_min`, `validation_top1_winner_dependent`, `final_positive_probability_below_shadow_min`, and `final_top1_winner_dependent`.
- Validation paired return delta: observed `+69.9634766410506%`, bootstrap positive probability `0.5965`, 95 percent interval `[-378.2934813372281%, +571.6648769012601%]`, and top-1 removal delta `-116.72180158220128%`.
- Final paired return delta: observed `+46.60547113816661%`, bootstrap positive probability `0.53375`, 95 percent interval `[-301.4013525862932%, +441.21776600079306%]`, and top-1 removal delta `-100.4671175287644%`.

## Decision

`Rejected`, not `Research Alpha`, `Shadow Candidate`, or `Live Switch Candidate`.

No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

`docs/model_scoreboard.md` was updated because this current-data replay changes the conclusion for the preserve-base volceil020 utility-label branch: an old strict-gate accept is not enough when the paired-delta uncertainty gate rejects the result.

Next direction: stop runner-retention utility/volceil parameter and label micro-sweeps. Fresh live support ranks rejected-entry `fast_profit` and `fast_profit_then_collapse` ahead of `slow_runner`, so the active node should pivot to a structural conditional-exit / fast-profit-harvest or accepted-action trade-delta selector, with the uncertainty gate retained as a promotion requirement.
