# Rare Exit-State Validation Research

Date: 2026-05-21

## Live Trigger

The current live strategy remains `data/models/20260519_v95_v84_selective_nearmiss_gate` with `POSITION_SIZE=0.10`, `MAX_CONCURRENT_POSITIONS=8`, and v95's primary/near-threshold entry gates. The latest real failure is still `CMC`: a high-confidence primary buy that reached delayed profit after entry, then collapsed to `STOP_LOSS` before the existing exit stack captured gains.

The committed post-target exit-state probe found the same failure shape in final/live-like data, but not in validation:

- Validation: `23` target-hit candidates, `0` post-target collapse examples.
- Final: `31` target-hit candidates, `4` post-target collapse examples, including live-like `CMC`.

This creates a rare-event validation problem: the live/final failure is plausible, but validation has no positives to select a rule without overfitting.

## SmartSearch Commands

```bash
smart-search deep "In event-driven algorithmic trading, when a rare exit-state failure is observed in live/final data but the validation split has zero positive examples, what robust validation and experiment design methods can be used to avoid overfitting while still improving exit policy? Focus on walk-forward validation, nested cross-validation for time series, purged/embargoed CV, rare event meta-labeling, sequential live shadow evaluation, and when to reject a strategy despite plausible final examples." --format json --output docs/research/20260521-rare-exit-validation/plan.json
smart-search search "rare event validation algorithmic trading zero positives validation split avoid overfitting walk-forward purged cross validation meta labeling" --validation balanced --extra-sources 3 --timeout 90 --format json --output docs/research/20260521-rare-exit-validation/01-search.json
smart-search exa-search "rare event validation trading strategy zero positive examples validation overfitting purged cross validation" --num-results 5 --format json --output docs/research/20260521-rare-exit-validation/02-exa.json
smart-search zhipu-search "rare event validation trading strategy zero positive examples validation overfitting purged walk-forward cross validation" --num-results 5 --format json --output docs/research/20260521-rare-exit-validation/03-zhipu.json
smart-search fetch "https://blog.quantinsti.com/cross-validation-embargo-purging-combinatorial/" --format markdown --output docs/research/20260521-rare-exit-validation/04-fetch-quantinsti-purging.md
smart-search fetch "https://blog.quantinsti.com/walk-forward-optimization-introduction/" --format markdown --output docs/research/20260521-rare-exit-validation/05-fetch-quantinsti-walkforward.md
smart-search fetch "https://www.quantbeckman.com/p/with-code-combinatorial-purged-cross" --format markdown --output docs/research/20260521-rare-exit-validation/06-fetch-quantbeckman-cpcv.md
smart-search fetch "https://hub.algotrade.vn/knowledge-hub/overfitting-and-how-to-mitigate-it" --format markdown --output docs/research/20260521-rare-exit-validation/07-fetch-algotrade-overfitting.md
```

Provider note: Exa and Zhipu were unavailable in this environment because `EXA_API_KEY` and `ZHIPU_API_KEY` were not configured. The saved `02-exa.json` and `03-zhipu.json` are blocker evidence, not method evidence.

## Fetched Sources

- QuantInsti, "Cross Validation in Finance: Purging, Embargoing, Combination": finance labels are path-dependent and can overlap in event time; purging and embargoing reduce leakage across train/test boundaries.
- QuantInsti, "Walk-Forward Optimization": static out-of-sample validation can give false confidence; repeated in-sample/out-of-sample cycles better approximate deployment across changing regimes.
- QuantBeckman, "Combinatorial Purged Cross-Validation": robust parameter selection should prefer broad performance plateaus and distributions of outcomes, not one peak from one split; insufficient data and repeated strategy mining still create meta-overfitting risk.
- AlgoTrade, "Overfitting and How to Mitigate It": many positive backtests fail live because of noise, regime change, costs, and slippage; use out-of-sample, cross-validation, walk-forward checks, and fewer parameters.

## Implications For This Bot

1. Do not deploy a post-target exit rule selected only from final/live-like examples. The validation split has zero post-target-collapse positives, so any threshold chosen from final alone would leak the sealed split into design.

2. Add more chronological evidence before training or selecting an exit-state rule. The next minimal step should expand the read-only post-target probe to the train split or multiple chronological folds, then ask whether post-target collapses exist outside final.

3. If train has enough positives, the next replay-integrated experiment should select parameters on train, require validation improvement, and only then confirm on sealed final. If train and validation remain sparse or contradictory, reject the live rule and keep collecting shadow evidence.

4. Keep the hypothesis exit-focused. Current live after CMC shows no clean missed-runner entry problem: recent high-probability rejects mostly have low or negative `PredReturn`. The failure to solve is post-target collapse after a valid entry, not broader entries or bigger sizing.

5. Preserve live risk constraints: 10% position fraction, max 8 positions, no fixed stake, no live switch unless the candidate strictly beats current best v95 on validation, sealed final, walk-forward, stress, drawdown, and trade-quality gates.

## Next Experiment

Implement a diagnostic-only train split for `scripts/probe_post_target_exit_state.py` and `src.pipeline.model_replay.run_model_replay` so the post-target state distribution can be checked outside validation/final.

Falsification rules:

- If train has zero or very few post-target-collapse positives, do not train/select a conditional exit model yet.
- If train has positives but validation still has zero positives, allow only a read-only replay probe; do not switch live.
- If a future rule improves drawdown or win rate but cuts net profit or stress profitability, reject it, matching the delayed profit-lock rejection.
- Any accepted future exit must be selected without final leakage and must beat the current best baseline, not merely the newest model.

## Diagnostic Result

Report: `data/replay_reports/post_target_exit_state_probe_20260521_v95_train.json`

The first full train no-cache attempt was stopped to protect the live bot: it ran for more than 11 minutes and reached about `6.7GB` RSS with active swap pressure. The safer run used `--chunk-train-files`, one replay subprocess per train lifecycle file, and an explicit `--max-train-file-size-mb 512` diagnostic safety limit.

Train diagnostic scope:

- Chunked replay files processed: `15`
- Equivalent to full strict train replay: `false`
- Diagnostic note: chunked train replay resets replay state per lifecycle file to avoid live-machine memory pressure, so it is valid for rare-state discovery only, not strict performance or deployment selection.
- Skipped files: `2`
  - `data/training/lifecycle_incremental_20260228_162728.jsonl`: `1.85GB`, skipped by safety limit.
  - `data/training/lifecycle_incremental_20260330_021903.jsonl`: no eval episodes.
- Samples scored by chunked replay: `218848`
- Trade log rows: `59`
- Target-hit candidates: `49`
- Class counts: `post_target_continuation=42`, `post_target_collapse=5`, `post_target_unresolved=2`, `target_not_hit=10`, `missing_path=0`
- Collapse examples: `模因`, `SUPERCYCLE`, `MALO`, `Binance Movie`, `COB`

Interpretation:

- The post-target collapse shape is not only a sealed-final artifact; it appears in older train-like data too.
- Validation still has zero post-target-collapse examples, so this remains insufficient for live switching or hand-selecting a rule from final.
- The next allowed step is a replay-integrated conditional exit experiment that selects only on train/diagnostic evidence, requires validation to improve total replay metrics despite zero collapse labels, and confirms on sealed final. If validation profit/stress fall, reject even if collapse examples look intuitively correct.
