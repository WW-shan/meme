# Adaptive Near-Miss Threshold Summary

## Live trigger

本轮研究由一次 live near-miss 触发：SZN 信号的模型概率已达 `prob >= 0.98`，但 `PredReturn` 低于当前最小入场门槛，因此未触发买入；后续路径出现约 `MFE +158%`。问题不是主模型完全没有识别到机会，而是“高概率、强路径潜力”的样本被 expected-return / threshold decision 层挡掉。

## Smart-search commands executed

```bash
smart-search doctor --format json
smart-search search "selective classification reject option conformal risk control threshold tuning classifier decision threshold meta-labeling trading triple barrier" --validation balanced --extra-sources 3 --format json --output docs/research/20260519-adaptive-nearmiss-threshold/01-search.json
smart-search fetch "https://scikit-learn.org/stable/modules/classification_threshold.html" --format markdown --output docs/research/20260519-adaptive-nearmiss-threshold/02-fetch-sklearn-threshold.md
smart-search fetch "https://jmlr.org/papers/v24/21-0048.html" --format markdown --output docs/research/20260519-adaptive-nearmiss-threshold/03-fetch-jmlr-reject-option.md
smart-search fetch "https://arxiv.org/html/2512.12844v2" --format markdown --output docs/research/20260519-adaptive-nearmiss-threshold/04-fetch-selective-conformal-risk-control.md
smart-search fetch "https://mlfinpy.readthedocs.io/en/latest/Labelling.html" --format markdown --output docs/research/20260519-adaptive-nearmiss-threshold/05-fetch-mlfinpy-labelling.md
```

`plan.json` also records the broader planned deep-research route: broad `search`, `zhipu-search`, `exa-search`, then fetched-page gap check. This directory's actual fetched evidence is the four markdown files above.

## Fetched sources

- scikit-learn, "Tuning the decision threshold for class prediction": separates probability estimation from the downstream decision rule, and supports post-training threshold tuning against a business metric.
- JMLR 2023, "Optimal Strategies for Reject Option Classifiers": frames reject-option classifiers as abstaining on uncertain cases, with selective risk / coverage tradeoffs.
- arXiv, "Selective Conformal Risk Control": combines selective classification with conformal risk control; accept confident samples, defer uncertain ones, and control risk on the accepted subset.
- mlfinpy, "Data Labelling": documents raw returns, fixed horizon labels, triple-barrier labels, and meta-labeling; explicitly notes fixed-horizon labels miss price path information, while triple-barrier uses upper/lower/vertical barriers and meta-labeling decides take/pass on primary signals.

## Conclusions for this repo

1. Keep `model probability` separate from `threshold decision`. The SZN miss suggests the classifier confidence can be right while the entry gate based on `PredReturn >= min` is too brittle for rare runner paths. Do not treat this as evidence that the global classifier threshold should be lowered.

2. Use a selective / reject-option layer for near-misses. The candidate design is a narrow rescue rule or meta-model that only considers already-exceptional primary signals, e.g. `prob >= 0.98` plus high-volume / high-volatility / runner-structure features, then outputs `rescue` vs `abstain`.

3. Prefer path-dependent labels over fixed return regression for this question. Triple-barrier / meta-labeling fits the failure mode: label whether the primary signal should have been acted on under upper profit, lower stop, and vertical timeout barriers. This can distinguish rare runners from fast collapses better than a single expected-return point estimate.

4. Conformal / selective risk control is useful as a calibration discipline, not as a promise of live market safety. If implemented, tune the rescue threshold on calibration/backtest data to bound an explicit accepted-trade loss metric, then monitor coverage, precision, false rescue rate, slippage, and post-entry drawdown.

## Test next

Test `primary-score rescue`: a small, isolated near-miss entry path for cases where the primary classifier score is extremely high but `PredReturn` is below the normal minimum. The test should compare rescued samples against non-rescued near-misses using path labels such as MFE before MAE/stop, time-to-runner, and collapse rate.

Do not spend this round retrying:

- global threshold lowering;
- loosening volume filters;
- loosening raw runner probability thresholds;
- blanket partial-exit changes.

Those alternatives change broad live behavior and do not target the specific observed failure: high primary confidence plus underestimated path return.
