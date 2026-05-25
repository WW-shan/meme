# Replay-Integrated Action-Policy Research Summary

Date: 2026-05-25

## Question

How should this bot convert the support-complete action-policy reward probe into a replay-integrated policy candidate without lookahead leakage, while enforcing support, lower-bound, walk-forward, stress, and execution-simulation gates before any deployment?

## Commands

```bash
smart-search doctor --format json
smart-search deep "How should an event-driven crypto trading system convert a support-complete action-policy reward probe into a replay-integrated policy candidate without lookahead leakage, while enforcing support, lower-bound, walk-forward, stress, and execution-simulation gates before deployment?" --budget deep --format json --output docs/research/20260525-replay-integrated-action-policy/01-plan.json
smart-search search "event driven trading backtest lookahead bias walk forward validation execution costs slippage policy simulation" --validation balanced --extra-sources 3 --timeout 90 --format json --output docs/research/20260525-replay-integrated-action-policy/02-search-event-driven-backtest.json
smart-search search "event driven backtesting walk forward validation slippage execution simulation trading" --providers tavily --validation balanced --extra-sources 3 --timeout 90 --format json --output docs/research/20260525-replay-integrated-action-policy/02-search-event-driven-backtest-tavily.json
smart-search fetch "https://www.quantstart.com/articles/Event-Driven-Backtesting-with-Python-Part-I/" --format markdown --output docs/research/20260525-replay-integrated-action-policy/03-fetch-quantstart-event-driven.md
smart-search fetch "https://www.quantstart.com/articles/Event-Driven-Backtesting-with-Python-Part-VII/" --format markdown --output docs/research/20260525-replay-integrated-action-policy/04-fetch-quantstart-execution.md
smart-search fetch "https://mlfinpy.readthedocs.io/en/latest/CrossValidation.html" --format markdown --output docs/research/20260525-replay-integrated-action-policy/05-fetch-mlfinpy-cross-validation.md
smart-search fetch "https://proceedings.neurips.cc/paper/2020/hash/0d2b2061826a5df3221116a5085a6052-Abstract.html" --format markdown --output docs/research/20260525-replay-integrated-action-policy/06-fetch-cql-neurips.md
smart-search fetch "https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html" --format markdown --output docs/research/20260525-replay-integrated-action-policy/07-fetch-sklearn-timeseriessplit.md
smart-search fetch "https://openreview.net/forum?id=kLo4TKh0OP" --format markdown --output docs/research/20260525-replay-integrated-action-policy/08-fetch-ceopl-openreview.md
```

The raw `smart-search doctor` output was not saved because it includes masked API-key fragments. `00-doctor-sanitized.json` records the usable capability state without credential material.

`02-search-event-driven-backtest.json` failed with an xAI HTTP 503, `02-search-event-driven-backtest-tavily.json` failed because `--providers tavily` did not match a configured main-search provider, and `05-fetch-mlfinpy-cross-validation.md` is empty. These failed artifacts are retained as negative evidence only and are not used for claim-level conclusions.

## Fetched Evidence

- QuantStart event-driven backtesting Part I: event-driven backtests are more realistic than vectorized backtests for trade execution simulation, and the architecture separates market data, strategy, portfolio, order, fill, and execution handling through an event queue.
- QuantStart event-driven backtesting Part VII: replay evaluation should be judged on portfolio outputs such as equity curve, Sharpe-style return/risk, maximum drawdown, and drawdown duration rather than signal precision alone.
- scikit-learn `TimeSeriesSplit`: time-ordered validation is required where ordinary cross-validation would train on future data and evaluate on past data; `gap` can exclude samples between train and test.
- Kumar et al. 2020 CQL NeurIPS page: offline RL can overestimate values under dataset-policy distribution shift; conservative value estimates are used to lower-bound policy value and avoid optimistic out-of-distribution action selection.
- CEOPL OpenReview page: offline policies should be evaluated before deployment with a conservative lower-bound estimate, including bootstrap confidence intervals, to control overestimation risk versus a baseline.

## Application To This Bot

The prior support-complete reward probe is useful evidence, but it is still not a live or model-switch candidate. It selected action classes with accepted and rejected support, yet it did not run through the same live-sized replay mechanics used by the current best baseline. A deployable candidate needs stricter evidence:

- Freeze the target action policy at decision time.
- Keep ex-post barrier outcomes only as labels/rewards.
- Use chronological train, validation, and final/fresh slices; do not let future examples tune earlier decisions.
- Require selected support in both accepted and rejected families.
- Compare against the current v95/v84 live-sized baseline with the same 10% sizing and position constraints.
- Add a conservative lower-bound or stress gate so small lucky selected pockets cannot pass.
- Keep the result no-switch unless replay, walk-forward, stress, and execution assumptions all pass.

## Direction Ranking

1. **Replay-integrated action-policy gate**: highest value. Convert the support-complete reward idea into a policy score or gate that is evaluated by existing replay machinery, with live-sized sizing and baseline comparison.
2. **Support/LCB diagnostic for reward probes**: useful fallback if replay mapping is not feasible in this round. It would prevent unsupported action-policy overlays from looking better than they are, but it does not directly optimize replay PnL.
3. **Another direct reward threshold stress**: lower value. Prior work already showed support disappears at stricter thresholds.
4. **Static quick-take-profit or volume relaxation**: reject. Fresh attribution still contains fast-profit near-misses, but also many flat/stop-first counterexamples. A static overlay repeats known failure modes.

Selected direction: attempt a replay-integrated action-policy gate first. If episode mapping is unsupported by the available reports, fall back to a reusable conservative support/lower-bound diagnostic and explicitly record why replay integration is blocked.

## Falsification Rule

Reject the direction for live/runtime use unless it improves or at least preserves the current best baseline in live-sized replay, passes chronological validation/final support, and keeps a conservative lower-bound or stress metric positive. If it improves diagnostic understanding but fails any of those gates, record it as shadow-only and do not change `.env`, sizing, model artifacts, thresholds, or bot processes.

## Experiment Result

Implementation:

- Replay hook: `src/pipeline/train_hybrid.py` now supports a default-off `low_volume_rescue_scores_by_episode` score map and `buy_low_volume_rescue_min_action_score`.
- Score-map builder: `src/pipeline/action_policy_replay_gate.py` trains the support-complete action-policy model only on decision-time fields and maps scores back to replay episode sample indices.
- CLI: `scripts/run_action_policy_low_volume_replay.py`.
- Tests: `tests/model/test_low_volume_action_policy_gate.py` and `tests/model/test_action_policy_low_volume_replay.py`.
- Report: `data/replay_reports/action_policy_low_volume_replay_20260525_replay_integrated.json`.

The first full replay surfaced an experiment wiring bug: score maps were generated against base runtime params, so no low-volume candidate universe was scored and every candidate was rejected for missing action score. The CLI was fixed to score the widest candidate-grid universe before applying candidate-specific score floors.

Final conservative replay result:

- Decision: `reject`.
- Action-policy model trained on `369` train candidates: `138` positive, `231` negative; source families `accepted=100`, `rejected=269`.
- Learned decision-time feature set: `near_threshold_rescue_used`, `pred_return`, `prob`; feature importance concentrated on `pred_return` (`0.8991`) and `prob` (`0.1009`).
- Validation baseline: `32` trades, net profit `0.021094872145773796` BNB, win rate `75.00%`, max drawdown `-9.8821%`, worst stress profit `0.011148541483943297` BNB.
- Wider score grid did generate low-volume rescue entries (`4-6` entries per active candidate), but the best active candidates reduced validation profit and win rate.
- Final conservative grid selected a no-entry candidate as raw best because active candidates were worse than baseline. It tied validation baseline by doing nothing, failed the required `low_volume_rescue_entry_count` gate, and failed final confirmation.
- Final confirmation candidate also had `0` low-volume rescue entries, tied final baseline profit `0.0051745153254758` BNB, and failed the profit-improvement and rescue-entry gates.

Business decision: no live switch, no `.env` change, no threshold/sizing/model-artifact change, and no bot restart. The low-volume action-policy rescue direction is now replay-integrated and falsified for this v95/v84 baseline. It should not be retried as a simple low-volume entry overlay; future work should shift to a different model-improvement direction, likely conditional exits or a better feature-rich action-policy scorer with actual flow/path-state support.
