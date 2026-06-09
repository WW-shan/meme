# 2026-06-09 Preserve-Base Utility-Label Current-Data Rerun

## Live State

- Bot and collector were running under `./tools/memectl` in the expected `meme-bot` and `meme-collector` tmux sessions.
- Processes matched the tmux-managed `src.trader.bot` and `tools.collect_continuous` commands.
- `data/bot_state.json` showed balance `0.001559636535526772` BNB and no open positions.
- `.env` stayed unchanged for live risk: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `MAX_CONCURRENT_POSITIONS=8`, and `POSITION_SIZE=0.10`.
- Branch `main` was even with `origin/main`; previous commit `369e598` was pushed and GitHub Actions `CI` completed successfully. The current node was active and not archived, not committed, not pushed, and had no CI run yet at experiment-record time.
- `docs/goals` status and diffs were clean, and `git ls-files .ccg` was empty.

## Live Attribution

There were no new real trades after the `2026-06-07 12:25:39.499918` `苹果人生` close. The latest trade remained a `TRAILING_STOP` winner with net profit `+0.00005553972801680855` BNB.

Recent live logs showed continued signal analysis and collector flushes without sampled buy or sell errors. Recent high-confidence rejects were still mostly blocked by low or negative `PredReturn`, low volatility, or `buy_model_reject`. The prior detailed reject attribution remains the live trigger set for this replay:

- `KAIKA`: `prob=0.991923`, `PredReturn=6.03`, rejected by `pred_return_below_min`; path reached only `+1.11%` MFE and `-62.67%` MAE, with early stop-zone breach.
- `FOURGIFT`: `prob=0.991390`, `PredReturn=6.74`, rejected by `pred_return_below_min`; path reached `+1.72%` MFE and `-43.87%` MAE.
- `FOURMEME`-style high-prob reject: `prob=0.990189`, `PredReturn=9.15`, rejected by `pred_return_below_min`; path reached `+3.00%` MFE and `-49.67%` MAE.
- `持续构建`: high-prob missed runner candidate with `+496.49%` MFE, but it first breached `-18%` about `8.5s` after signal and had `-24.49%` MAE.
- `国星宇航`: high-prob missed runner candidate with `+113.53%` MFE and later `+60%`, but this is a rare case relative to the many correct high-prob abstentions.

Failure tags: `correct_abstention`, `missed_runner_with_deep_early_drawdown`, `runner_retention_uncertainty`, and `top_winner_dependency`.

## Prior Review

Relevant prior artifact:

- `docs/research/20260606-preserve-base-utility-grid/summary.md`

The 2026-06-06 preserve-base `volceil020` utility-label branch already showed the same pattern: strict replay accepted, but paired-delta uncertainty rejected because positive probabilities were low and the edge was top-winner dependent. This 2026-06-09 rerun was required to finish the same branch on the latest data and classify it under the tiered gate.

Directions already weak or exhausted for this local family:

- runner-retention score-floor retuning,
- volatility ceiling retuning,
- binary MAE relabel plus score-floor calibration,
- utility-label micro-sweeps that only move a few added/removed trades,
- broad quick-profit and low-volume rescue overlays.

## Research Reused

No new SmartSearch run was opened for this rerun because it reused existing repo research summaries and added a new live-derived angle:

- `docs/research/20260528-runner-retention-boundary-feature/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`
- `docs/research/20260606-preserve-base-utility-grid/summary.md`

New angle: classify the preserve-base utility-label current-data replay with the four-tier uncertainty gate, then stop runner-retention utility/volceil parameter and label micro-sweeps if it does not reach `Research Alpha`.

## Hypothesis Portfolio

1. Preserve-base `volceil020` utility-label rerun.
   Expected impact: medium, because it directly targets drawdown-heavy rescues while preserving the base model. Evidence strength: high from prior strict replay and saved utility/meta-label research. Falsifiability: high because the replay and uncertainty commands already exist. Cost: low. Rank: first because it was the active required next step and the smallest remaining falsifier for this local family.
2. Conditional exit / early-profit harvest.
   Expected impact: high, because live history and reject paths contain early-profit-giveback and runner/hold timing issues. Evidence strength: medium, with prior blanket profit locks rejected but continue-hold router evidence retained. Falsifiability: medium-high through strict router or exit-policy replay. Cost: medium.
3. Trade-delta-trained meta gate.
   Expected impact: medium-high, because preserve-base added/removed trade deltas show the real question is whether a candidate improves the baseline decision. Evidence strength: medium-high. Falsifiability: medium. Cost: medium-high because it needs a new training target and replay bridge.
4. Live shadow evaluator.
   Expected impact: medium, mostly improving live/replay distribution alignment before any switch. Evidence strength: medium. Falsifiability: medium. Cost: medium.

Selected direction: preserve-base utility-label rerun, because it was the active goal step and the cheapest decisive falsifier. Falsification rule: if the strict replay gain fails the tiered uncertainty gate or remains top-winner dependent, reject the branch and pivot structural.

## Commands

Replay:

```bash
venv/bin/python scripts/run_runner_retention_candidate_gate_replay.py \
  --candidate-grid-json docs/research/20260528-runner-retention-boundary-feature/train_boundary_soft_feature_preserve_base_volceil020_utility_label_grid.json \
  --preserve-base-candidates \
  --write-selected-trade-delta \
  --output data/replay_reports/runner_retention_candidate_gate_replay_20260609_preserve_base_volceil020_utility_label_grid.json \
  --force
```

Uncertainty gate:

```bash
venv/bin/python scripts/probe_replay_uncertainty_gate.py \
  --report data/replay_reports/runner_retention_candidate_gate_replay_20260609_preserve_base_volceil020_utility_label_grid.json \
  --candidate-id preserve_base_volceil020_utility_label_20260609 \
  --output data/replay_reports/replay_uncertainty_gate_20260609_preserve_base_volceil020_utility_label_grid.json \
  --force
```

Strict assumptions stayed live-sized: `position_fraction=0.1`, `max_position_fraction=0.1`, `max_open_positions=8`, `skip_all_in_replay=true`, and `fixed_stake_bnb=null`.

## Results

- Strict replay decision: `accept`.
- Tiered uncertainty outcome: `Rejected`.
- Candidate count: `13`.
- Selected candidate index: `4`.
- Selected params kept preserve-base candidates, `buy_runner_retention_rescue_max_entry_price_volatility=0.2`, `buy_runner_retention_label_mfe_weight=1.0`, `buy_runner_retention_label_mae_penalty=1.0`, and `buy_runner_retention_label_min_utility_score=35.0`.

Validation strict replay:

- Baseline: `23` trades, net profit `0.012252343033424175` BNB, win rate `0.7391304347826086`, max drawdown `-7.361964742920057%`, walk-forward worst return `2.8446315943470024%`, walk-forward worst drawdown `-14.377134762904564%`, stress worst net profit `0.004609956337437153` BNB, stress worst return `90.75962250093363%`, and stress worst drawdown `-12.245451556163134%`.
- Candidate: `23` trades, net profit `0.012621051870639492` BNB, win rate `0.7391304347826086`, max drawdown `-7.361964742920057%`, walk-forward worst return `2.8446315943470024%`, walk-forward worst drawdown `-14.377134762904564%`, stress worst net profit `0.00496695959973896` BNB, stress worst return `97.78820996389581%`, and stress worst drawdown `-12.245451556163134%`.

Final strict replay:

- Baseline: `24` trades, net profit `0.0020282580548887895` BNB, win rate `0.5416666666666666`, max drawdown `-18.206422038627302%`, walk-forward worst return `5.791910318976479%`, walk-forward worst drawdown `-18.206422038627302%`, stress worst net profit `-0.0005495624150332759` BNB, stress worst return `-10.819642026555643%`, and stress worst drawdown `-26.925411157799616%`.
- Candidate: `24` trades, net profit `0.0022738697639721993` BNB, win rate `0.5416666666666666`, max drawdown `-18.206422038627302%`, walk-forward worst return `5.791910318976479%`, walk-forward worst drawdown `-18.206422038627302%`, stress worst net profit `-0.0003868924234255496` BNB, stress worst return `-7.617037500640533%`, and stress worst drawdown `-26.925411157799616%`.

Paired-delta uncertainty:

- Rejection reason: `final_positive_probability_below_research_min`.
- Shadow blockers: `validation_positive_probability_below_shadow_min`, `validation_top1_winner_dependent`, `final_positive_probability_below_shadow_min`, and `final_top1_winner_dependent`.
- Validation observed paired delta was `+69.9634766410506%`, but positive probability was `0.5965`, the 95% interval was `[-378.2934813372281%, +571.6648769012601%]`, and removing the top positive contribution changed the delta to `-116.72180158220128%`.
- Final observed paired delta was `+46.60547113816661%`, but positive probability was `0.53275`, the 95% interval was `[-301.4013525862932%, +441.21776600079306%]`, and removing the single positive added trade changed the delta to `-100.4671175287644%`.

## Decision

Outcome tier: `Rejected`.

The strict replay gain is real in the point estimate, but it is not durable enough for `Research Alpha`. It depends on one large added/removed trade contribution in both validation and final, and the bootstrap positive probabilities are below the research threshold. This means the branch cannot justify a live switch, shadow candidate, or continued utility-label parameter micro-sweeps.

No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

`docs/model_scoreboard.md` was updated because this result changes the active branch conclusion: the current-data utility-label rerun is rejected by the latest tiered gate even though strict replay accepts it.

Next direction: pivot structural. The best next candidates are conditional exit / early-profit harvest, trade-delta-trained meta gate, and live shadow evaluation, with conditional exit currently ranked first because it is structurally different and already has saved research/replay artifacts to reuse.
