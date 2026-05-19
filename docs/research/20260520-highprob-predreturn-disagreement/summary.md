# High-Probability / PredReturn Disagreement

Date: 2026-05-20

## Live Trigger

The current live model is `data/models/20260519_v95_v84_selective_nearmiss_gate` with 10% sizing. Bot and collector are running, current state is flat, and no live config was changed in this pass.

The live problem is not a broad threshold miss. Since the last real close, the audit log shows many high primary buy probabilities rejected by the `PredReturn >= 35` entry-value gate. The key missed runner is `SZN`: primary `prob=0.9892655505`, `PredReturn=-4.4976`, `volume_30s=3.2244`, `price_volatility=0.2765`, `age=9s`, rejected by `pred_return_below_min`, then later reached roughly `+25%` in 84 seconds and `+511%` MFE. The same bucket also contains fast collapses such as `交易鸭` and `cwh`, so disabling PredReturn or lowering the global entry score would repeat already rejected directions.

## Research Question

How should a live memecoin trading system arbitrate cases where a strong primary classifier says "buy", while a secondary expected-return/entry-value model rejects the trade?

The question was expanded with SmartSearch Deep Research first, then source discovery/fetch:

```bash
smart-search deep "For a live memecoin trading classifier, high primary buy probability sometimes conflicts with a secondary expected-return/entry-value model. Recent live evidence: SZN had primary probability 0.989 but PredReturn -4.5 and was rejected, then reached +25% in 84 seconds and +511% MFE; other high-prob low-PredReturn tokens collapsed. Deep research robust methods for model-disagreement arbitration, meta-labeling, reject-option/selective classification, triple-barrier path labels, and cost-sensitive override gates that can rescue rare runners without globally disabling the second-stage filter." --format json --output docs/research/20260520-highprob-predreturn-disagreement/plan.json
smart-search search "high confidence classifier disagrees with secondary model meta-labeling trading triple barrier reject option selective classification cost-sensitive override gate" --validation balanced --extra-sources 3 --timeout 120 --format json --output docs/research/20260520-highprob-predreturn-disagreement/01-search.json
smart-search fetch "https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/" --format markdown --output docs/research/20260520-highprob-predreturn-disagreement/04-fetch-hudson.md
smart-search fetch "https://jmlr.org/papers/v24/21-0048.html" --format markdown --output docs/research/20260520-highprob-predreturn-disagreement/05-fetch-jmlr-reject-option.md
smart-search fetch "https://proceedings.mlr.press/v139/charoenphakdee21a/charoenphakdee21a.pdf" --format markdown --output docs/research/20260520-highprob-predreturn-disagreement/07-fetch-cost-sensitive-rejection.md
```

The ACM selective-classification fetch returned an empty file, so it is discovery evidence only, not claim evidence.

## Findings

Meta-labeling fits this setup better than a static override. The Hudson Thames article describes the primary model as the trade-side generator and the secondary model as the decision layer for whether to act. It also stresses that meta-labeling works best when the primary model is already useful and the secondary model has contextual features. That matches v95: the primary classifier is strong, but the entry-value gate is wrong on a narrow set of runners.

Triple-barrier labeling is directly relevant because this market is path-dependent. The useful label is not a fixed final return; it is whether the token reaches profit barriers before stop barriers, and how quickly. SZN, CI, ZESTER, and `交易鸭` are not the same failure class even though they all have high primary probability and low PredReturn.

Reject-option and selective-classification research supports keeping abstention as a first-class decision. The JMLR reject-option paper frames abstention as a way to preserve bounded risk/coverage tradeoffs when the classifier is uncertain. For this system, the correct action set should remain `skip`, `quick take profit`, and `conditional hold`, not just `buy`.

Cost-sensitive rejection is relevant because false positives and false negatives have asymmetric costs. Missing SZN is costly, but buying every SZN-like sample is also costly because many collapse quickly. A learned candidate-level gate should explicitly optimize the rare-runner rescue versus fakeout cost, not depend only on raw posterior confidence.

## Historical Constraints

Already rejected directions:

- Static high-probability rescue / primary-score override.
- `PredReturn [25,35]` quick-profit overlay.
- Low-volume / low-PredReturn blanket rescue.
- Global threshold lowering.
- Global PredReturn loosening.
- Blanket longer holding or blanket partial exits.

Those failed because they either over-expanded trades, reduced final profit, weakened stress results, or removed too much of the baseline edge. The next experiment must be structurally different.

## Hypothesis

Because live evidence shows the high-probability / low-PredReturn bucket contains both clean runners and fast collapses, test a candidate-level meta-ranker on "shadow disagreement" candidates instead of a static override. The probe should preserve v95 as the primary candidate generator, add rejected high-probability candidates only as an offline shadow universe, label them with path/barrier outcomes, and check whether a learned ranker separates runner-like candidates from collapse-like candidates across validation and final splits.

## Falsification Rule

Reject this direction if the learned shadow ranker fails to improve validation and final top-candidate relevance versus the entry-value ordering, or if it increases collapse selections. Even if the probe passes, do not switch live until a replay-integrated candidate beats current v95 on final profit, win rate, max drawdown, walk-forward worst return, stress, and trade-count discipline at 10% sizing.

## Next Experiment

Extend `candidate_ranker_probe` with a default-off `shadow_score_reject` universe:

- Include only high primary probability samples that pass quality gates but fail `min_entry_score`.
- Keep live runtime and manifests unchanged.
- Train/evaluate a candidate-level ranker on path labels.
- Save a report under `data/replay_reports/`.
- Use the result only as evidence for or against a replay-integrated meta-label gate.

## Probe Result

Implemented report:

```bash
venv/bin/python scripts/run_candidate_ranker_probe.py \
  --model-dir data/models/20260519_v95_v84_selective_nearmiss_gate \
  --lifecycle-dir data/training \
  --output data/replay_reports/v97_shadow_disagreement_ranker_probe_20260520.json \
  --train-split-ratio 0.40 \
  --validation-split-ratio 0.20 \
  --min-validation-files 1 \
  --min-eval-files 1 \
  --max-samples-per-token 120 \
  --sample-cache-dir .cache/candidate_ranker_probe_shadow5 \
  --top-k-per-group 1 \
  --lifecycle-file data/training/lifecycle_incremental_20260406_212641_part007.jsonl \
  --lifecycle-file data/training/lifecycle_incremental_20260406_212641_part008.jsonl \
  --lifecycle-file data/training/lifecycle_incremental_20260406_212641_part009.jsonl \
  --lifecycle-file data/training/lifecycle_incremental_20260516_212042.jsonl \
  --lifecycle-file data/training/lifecycle_incremental_20260516_212852.jsonl \
  --include-shadow-score-rejects \
  --shadow-min-prob 0.988 \
  --shadow-max-entry-score 10 \
  --shadow-min-entry-volume-30s 2.0 \
  --shadow-min-entry-price-volatility 0.20 \
  --shadow-max-age-seconds 60
```

Result: `supports_followup_replay_integration`.

Validation improved ranker top relevance from `122` to `133`, clean-runner selections from `30` to `32`, and reduced collapse selections from `28` to `24`. Final improved top relevance from `51` to `53`, clean-runner selections from `8` to `9`, and reduced collapse selections from `38` to `37`.

This is not a live-switch result because it is still a ranking probe, not a replay-integrated executable gate. The next round should convert this into a replay-only meta-gate and reject it unless strict live-sized replay beats v95 on profit, drawdown, win rate, walk-forward, stress, and trade-count discipline.
