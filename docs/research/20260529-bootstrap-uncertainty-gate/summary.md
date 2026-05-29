## Question

For a live memecoin trading bot with small validation/final replay splits, how should we design an uncertainty-aware replay gate that uses paired trade delta, top-winner dependency, walk-forward/stress constraints, and live shadow evidence to classify candidates as `Rejected`, `Research Alpha`, `Shadow Candidate`, or `Live Switch Candidate` without increasing 10% live sizing risk?

## SmartSearch Commands

```bash
smart-search deep "For a live memecoin trading bot with small validation/final replay splits, how should we design a bootstrap or uncertainty-aware replay gate that uses paired trade delta, top-winner dependency, walk-forward and stress constraints, and live shadow evidence to classify candidates as Rejected, Research Alpha, Shadow Candidate, or Live Switch Candidate without increasing 10% live sizing risk?" --budget deep --format json --output docs/research/20260529-bootstrap-uncertainty-gate/01-deep-plan.json
smart-search search "bootstrap confidence intervals paired trade delta backtest overfitting small sample trading strategy reality check deflated sharpe ratio" --validation balanced --extra-sources 3 --timeout 90 --format json --output docs/research/20260529-bootstrap-uncertainty-gate/02-search.json
smart-search zhipu-search "交易策略 小样本 回测 bootstrap 置信区间 实盘 shadow evaluation" --count 5 --format json --output docs/research/20260529-bootstrap-uncertainty-gate/03-zhipu.json
smart-search exa-search "bootstrap confidence interval backtest overfitting trading strategy paired trade delta" --num-results 5 --format json --output docs/research/20260529-bootstrap-uncertainty-gate/04-exa.json
smart-search fetch "https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf" --format markdown --output docs/research/20260529-bootstrap-uncertainty-gate/05-fetch-deflated-sharpe.md
smart-search fetch "https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf" --format markdown --output docs/research/20260529-bootstrap-uncertainty-gate/06-fetch-probability-backtest-overfitting.md
smart-search fetch "https://quantdare.com/deflated-sharpe-ratio-how-to-avoid-been-fooled-by-randomness/" --format markdown --output docs/research/20260529-bootstrap-uncertainty-gate/07-fetch-quantdare-deflated-sharpe.md
smart-search fetch "https://www.pm-research.com/content/iijpormgmt/40/5/94" --format markdown --output docs/research/20260529-bootstrap-uncertainty-gate/08-fetch-pm-deflated-sharpe.md
```

Provider gap: `03-zhipu.json` and `04-exa.json` record missing `ZHIPU_API_KEY` and `EXA_API_KEY`, so they are not used as evidence.

## Fetched Sources

- `05-fetch-deflated-sharpe.md`: Bailey and Lopez de Prado's deflated Sharpe paper. The useful point for this bot is not the Sharpe formula itself, but the multiple-testing correction: after many backtests, headline performance is inflated unless the number of trials and non-normal returns are considered.
- `06-fetch-probability-backtest-overfitting.md`: Bailey, Borwein, Lopez de Prado, and Zhu on PBO/CSCV. The directly useful point is that simple holdout checks can be unreliable for investment backtests, especially after many configurations are tried; the method also supports evaluating generic performance metrics, not only Sharpe.
- `07-fetch-quantdare-deflated-sharpe.md`: implementation-oriented discussion of recording all trials and using DSR to separate real findings from statistical flukes.
- `08-fetch-pm-deflated-sharpe.md`: confirms the Journal of Portfolio Management article metadata, but the content is paywalled; do not use it for claim-level conclusions beyond title/authors.

## What Applies To This Bot

- The current workflow tests many candidate variants. The gate must record candidate/trial count and penalize or downgrade results that look good only after many nearby attempts.
- Small final split results should not be decided by raw win rate alone. Use paired candidate-vs-baseline trade deltas and bootstrap the total delta to estimate how often the improvement remains positive under resampling.
- Top-winner dependency must be explicit. If removing the top winner or top three positive delta contributors flips the candidate negative, it can remain `Research Alpha`, but it should not become `Shadow Candidate` or `Live Switch Candidate`.
- Walk-forward and stress remain hard risk constraints. Bootstrap can refine small-sample interpretation, but it cannot override drawdown/stress collapse.
- Live shadow evidence should be a promotion requirement, not a replacement for replay. Bootstrap can say a replay edge is stable enough to shadow; it cannot by itself justify live cutover.

## What We Reject

- Do not loosen live-switch gates because bootstrap says the mean is positive. A bootstrap gate is a research/shadow classifier, not a live switch mechanism.
- Do not rely on broad search-only or weak sources for method decisions. TikTok, Medium-style search hits, and paywalled pages without fetched claim text are discovery only.
- Do not use DSR mechanically on this bot's per-trade returns without a proper trial-count and non-normal-return implementation. For this node, DSR/PBO are used as design guidance: record trial count, bootstrap paired deltas, and downgrade overfit-looking results.
- Do not use one good final split or one large winner to advance a candidate when validation, stress, or paired delta says the edge is fragile.

## Next Experiment

Implement a reusable read-only uncertainty gate over existing replay/trade-delta reports:

- Candidate id `volceil020_utility_label_uncertainty_gate`: use `data/replay_reports/runner_retention_candidate_gate_replay_20260529_train_boundary_soft_feature_preserve_base_volceil020_utility_label_grid.json`. Expected falsification: the final delta is top-winner dependent, so the utility-label branch should remain below `Shadow Candidate`.
- Candidate id `conditional_exit_continue_hold_uncertainty_gate`: use `data/replay_reports/action_policy_router_replay_20260529_conditional_exit_current_refresh.json` for strict gate context plus the existing paired-delta files `data/replay_reports/action_policy_router_continue_hold_post_target_activation_trade_delta_validation_ppo.json` and `data/replay_reports/action_policy_router_continue_hold_post_target_activation_trade_delta_final_ppo.json`. Expected support: if validation/final bootstrap positive probabilities are high and top-winner removal stays positive, this strengthens the current post-target continue-hold `Shadow Candidate` evidence without changing live config.

Falsification rule: reject the uncertainty gate or keep the candidate at `Research Alpha` if validation or final observed paired delta is non-positive, bootstrap positive probability is below the research threshold, strict drawdown/stress/walk-forward gates fail, or top-winner dependency blocks shadow promotion.
