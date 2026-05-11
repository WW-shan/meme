# Live Profit And Robustness Optimization Design

Date: 2026-05-11
Status: Approved for planning

## Goal

Improve the FourMeme hybrid model so it is both live-robust and more profitable under the actual intended trading envelope:

- Initial equity: 1.0 BNB.
- Fixed stake: 0.1 BNB per entry.
- Maximum concurrent open or pending positions: 8.
- Entry delay: 3 seconds.
- Exit delay: 3 seconds.
- Fees and slippage included in replay and labels.
- Preferred maximum drawdown: under 30% in primary live-capacity replay and walk-forward checks.
- Profit objective: maximize realistic fixed-stake BNB profit, not paper compounding or ideal fills.

The optimization should improve model quality, entry ranking, and exit timing. It must not rely on leverage, larger stakes, final-test parameter fitting, or hidden relaxation of live execution assumptions.

## Current Evidence

The latest available artifacts show a profit-quality tradeoff, not a simple threshold problem.

- `data/models/20260509_v33_live_3s_aggressive` is the latest model artifact by manifest timestamp.
- Its saved main replay reports `+25.176977 BNB`, `4045` trades, `45.41%` win rate, and `-9.59%` max drawdown, but that primary replay uses `max_open_positions=1000`.
- The same saved manifest reports a live-capacity stress scenario with `max_open_positions=8`: `+3.225351 BNB`, `368` trades, and `-9.59%` max drawdown.
- A fresh rerun with the current workspace loaded the same model and rebuilt final-test samples, but produced `+10.025355 BNB`, `4068` trades, and `-11.50%` max drawdown. This mismatch means replay reproducibility must be fixed before more training is trusted.
- v33 has strong expectancy but a weak median trade: median return is about `-2.07%`, average winner is about `+30.45%`, average loser is about `-13.93%`, and win rate is `45.41%`.
- `data/models/20260509_live_cash_v31` has higher trade quality but lower coverage: `218` trades, `54.13%` win rate, median return about `+3.64%`, and saved live-capacity profit about `+2.6876 BNB`.
- Saved threshold sweeps show that thresholds around `0.8` to `0.875` performed best for profit. Raising thresholds into the `0.94+` band cut too many opportunities and did not solve robustness by itself.

The immediate lesson is that we need slot-aware selection and better exit timing, not just a higher buy threshold.

## External Reference Notes

These references guide the design but do not override local code and tests.

- CatBoost ranking objectives support pairwise and groupwise ranking losses such as PairLogit, YetiRank, YetiRankPairwise, and LambdaMart. This is relevant because live trading is a ranked allocation problem when many token signals compete for 8 slots. Reference: https://catboost.ai/docs/en/concepts/loss-functions-ranking
- CatBoost regression objectives support return-style targets and quantile-style objectives, which can model expected live return and downside risk separately from a binary buy label. Reference: https://catboost.ai/docs/en/concepts/loss-functions-regression
- Probability calibration should use data separated from training; calibrated probabilities are most useful when the probability value itself drives decisions. Reference: https://scikit-learn.org/stable/modules/calibration.html
- Backtest overfitting risk rises when many strategies or parameter sets are searched and the best-looking result is selected from the final test period. The final test must remain sealed. Reference: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253

## Design Overview

The next optimization should run in three phases:

1. Build a reproducible replay and scoring foundation.
2. Tune existing models under the true 8-slot live envelope.
3. Add expected-value entry ranking, then improve exit timing.

This keeps fast, low-risk improvements ahead of deeper model changes.

## Phase 1: Replay-Only Evaluation Foundation

Add a replay-only CLI that can load existing model artifacts and evaluate them without retraining.

The CLI should:

- Load `buy_model.cbm`, `buy_threshold.json`, `feature_schema.json`, and optional `sell_policy.zip` from a model directory.
- Rebuild or load cached eval samples using the same chronological train/validation/final split recorded in the manifest.
- Run live-capacity replay with fixed 0.1 BNB stake and `max_open_positions=8` as the primary score path.
- Also report diagnostic high-capacity replay, mild friction, harsh friction, and walk-forward segments.
- Save a replay report outside the model artifact files, so old training outputs are not overwritten.
- Emit enough metadata to explain reproducibility: git commit, code dirty flag, lifecycle file list and mtimes, sample count, split config, model checksums, replay knobs, and dataset-builder knobs.

This phase solves the current problem where a saved manifest and a fresh rerun can disagree without a clear reason.

## Phase 2: Live Score And Existing-Model Parameter Search

Before retraining, run validation-only searches over existing v31, v32, and v33 artifacts.

The primary score should be live-capacity fixed-stake BNB profit with penalties:

```text
live_score = cap8_net_profit_bnb
             - drawdown_penalty
             - walk_forward_loss_penalty
             - harsh_friction_loss_penalty
             - concentration_penalty
             - instability_penalty
```

The search must use validation samples for selection and final samples for reporting only.

Candidate knobs:

- Buy threshold.
- Stop loss.
- Trailing start and trailing stop.
- Max hold seconds.
- Min policy hold seconds.
- Entry price protection.
- Max pending entries.
- Optional entry signal cooldown or per-time-bucket candidate cap.

Acceptance gates for a candidate:

- Primary `max_open_positions=8` final replay is profitable.
- Main and walk-forward drawdown are normally within 30%, or the profit gain is large enough and the breach is explicitly flagged.
- Mild friction remains profitable.
- Harsh friction does not indicate catastrophic collapse.
- Final test was not used to choose the parameters.

This phase should answer whether existing v33 can be made live-ready through selection logic alone.

## Phase 3: Expected-Value Entry Ranking

The current buy model acts mostly as a probability filter. Live trading needs an allocation ranker because many signals compete for limited cash and slots.

Add a return/risk head next to the existing buy classifier:

- `expected_live_return_pct`: delayed executable return estimate.
- `downside_quantile_pct`: lower-tail return estimate, for example 10th percentile or a proxy built from adverse excursion.
- `fill_quality_score`: probability that a 3-second delayed entry fills inside wait and price-protection constraints.
- `ev_score`: expected return minus downside, fee, slippage, and fill-risk penalties.

Replay behavior changes from immediate threshold-only buying to slot-aware ranking:

1. Collect candidate signals in a short chronological bucket.
2. Exclude candidates that fail minimum buy probability, entry age, or fill-quality checks.
3. Sort by `ev_score`.
4. Allocate free 0.1 BNB stakes to the highest-ranked candidates until the 8-slot limit is reached.
5. Record blocked candidates by reason and by score band.

Implementation can start with CatBoost regression/quantile models because they are easier to test and explain. CatBoost ranking objectives can be evaluated next if grouped ranking by time bucket gives better validation performance.

## Phase 4: Exit Quality Upgrade

The current v33 exit profile earns money through large right-tail winners but still has a negative median trade. Exit optimization should target better median trade quality without cutting off the right tail.

Add a supervised exit model before changing live bot execution:

- Generate per-position samples after entry.
- Label whether selling now beats holding under delayed-executable future paths.
- Predict `sell_now_score` or `hold_value_delta`.
- Keep hard safety rails: stop loss, rug sell pressure, max hold, replay-end liquidation.
- Let the learned model control normal profit-taking and continuation decisions.

PPO can remain available as an experiment, but the first live-oriented upgrade should prefer a deterministic, explainable exit score because it is easier to audit and tune under stress scenarios.

## Data Flow

```text
lifecycle files
  -> DatasetBuilder live delayed labels
  -> chronological train / validation / final split
  -> buy classifier + return/risk heads
  -> validation-only live-capacity parameter search
  -> sealed final replay report
  -> selected runtime params for bot config
```

The final test path must be write-protected conceptually: it reports selected candidates but never feeds back into parameter choice.

## Metrics To Report

Every replay report should include:

- Net profit BNB, final equity, account multiple, and net return percent.
- Total trades, entry rate, signal count, attempt count, fill rate, timeout rate, and price-protection skip rate.
- Win rate, median trade return, average winner, average loser, payoff ratio, and expectancy.
- Max drawdown, Sortino, worst walk-forward net return, worst walk-forward drawdown, and minimum walk-forward win rate.
- Stress scenario results for mild friction, harsh friction, and live capacity.
- Top-trade profit concentration.
- Exit-reason summary.
- Selection source: validation-only, final-report-only, or diagnostic.

## Testing Strategy

Use `unittest`, following existing repo conventions.

Phase 1 tests:

- Replay-only CLI loads a model directory and passes model artifacts into evaluation without retraining.
- Replay report records model checksums, split metadata, sample count, and replay knobs.
- Cached eval samples are invalidated when lifecycle file metadata or dataset-builder knobs change.
- Final replay reports are written to a new output path and do not overwrite model artifacts.

Phase 2 tests:

- Live score prefers higher cap8 BNB profit when drawdown and stress are acceptable.
- Live score penalizes drawdown breaches, harsh-friction collapse, and walk-forward losses.
- Parameter search uses validation results for selection and leaves final results as report-only.
- Search result manifest records all candidate metrics and the selected candidate rationale.

Phase 3 tests:

- EV scoring ranks higher expected return above lower expected return when downside is equal.
- EV scoring ranks lower downside above higher downside when expected return is equal.
- Slot-aware replay chooses the top-ranked candidates when more than 8 simultaneous signals appear.
- Blocked entries are reported by capacity, cash, entry timeout, price protection, and rank cutoff.

Phase 4 tests:

- Exit labels use delayed-executable sell prices, not signal-time prices.
- Learned exit score can close a decaying position before max hold.
- Safety exits override learned hold decisions.
- Median trade and right-tail metrics are reported after replay.

## Non-Goals

- No leverage.
- No increase above fixed 0.1 BNB stake for this optimization path.
- No final-test parameter fitting.
- No live RPC or transaction submission changes in the first implementation phase.
- No claim of live profitability based only on offline replay.

## Acceptance Criteria

The optimization work is acceptable when:

- A replay-only command can reproduce and compare v31, v32, and v33 under the same current-code live-capacity replay.
- Existing-model parameter search selects a candidate only from validation scoring and reports sealed final metrics separately.
- The selected candidate improves live-capacity profit or stress robustness versus the current v33 baseline without violating the drawdown policy silently.
- Any new entry model reports EV/risk metrics and demonstrates slot-aware improvement over threshold-only selection.
- Full `venv/bin/python -m unittest discover` passes before any final status claim.
