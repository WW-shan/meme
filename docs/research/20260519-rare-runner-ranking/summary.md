# Rare Runner Ranking Research

## Live Trigger

2026-05-19 v95 canary live evidence showed no new real trades after startup. From `2026-05-19 04:02:24` to `08:52:51`, `data/signal_audit.jsonl` had 164 rejected decisions and zero accepted buys. The strongest recent rejected signals were mostly correct skips:

- `SZN` (`0x8add...ffff`): `prob=0.9890`, `PredReturn=25.04`, rejected by `pred_return_below_min`; post-signal MFE about `+0.89%`, no `+25%` hit.
- `Neymar404` (`0xda50...ffff`): `prob=0.9759`, `PredReturn=15.62`; post-signal MFE about `+19.90%`, no `+25%` hit.
- `小鸟咪` (`0x01e8...4444`): `prob=0.9744`, `PredReturn=-0.42`; post-signal MFE about `+4.35%`, then hit `-18%` after about `155s`.
- `监狱来的妈妈` (`0x6765...4444`): `prob=0.9570`, `PredReturn=-0.60`; no positive path after signal in available lifecycle.

Failure tag for this round: `model_rejected_but_would_win` remains rare and not present in the newest v95 rejects; the current problem is preserving v95's abstention quality while finding a narrower way to rank the occasional clean runner.

## Commands

- `smart-search doctor --format json > docs/research/20260519-rare-runner-ranking/00-doctor.json`
- `smart-search deep "<rare-runner ranking question>" --format json --output docs/research/20260519-rare-runner-ranking/plan.json`
- `smart-search search "financial machine learning meta-labeling triple barrier method purged cross validation rare event trading learning to rank focal loss" --validation balanced --extra-sources 3 --format json --output docs/research/20260519-rare-runner-ranking/01-search.json`
- `smart-search fetch "https://mlfinpy.readthedocs.io/en/latest/Labelling.html" --format markdown --output docs/research/20260519-rare-runner-ranking/02-mlfinpy-labelling.md`
- `smart-search fetch "https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/" --format markdown --output docs/research/20260519-rare-runner-ranking/03-hudson-meta-labeling.md`
- `smart-search fetch "https://www.quantbeckman.com/p/with-code-combinatorial-purged-cross" --format markdown --output docs/research/20260519-rare-runner-ranking/04-cpcv.md`
- `smart-search fetch "https://catboost.ai/docs/en/concepts/loss-functions-ranking" --format markdown --output docs/research/20260519-rare-runner-ranking/05-catboost-ranking-losses.md`
- `smart-search fetch "https://catboost.ai/docs/en/concepts/python-reference_catboostranker" --format markdown --output docs/research/20260519-rare-runner-ranking/06-catboost-ranker.md`
- `smart-search fetch "https://aman.ai/primers/ai/loss/" --format markdown --output docs/research/20260519-rare-runner-ranking/07-loss-functions-focal.md`

## Evidence

- `mlfinpy` documents the triple-barrier method as a path label with upper, lower, and vertical barriers, and describes meta-labeling as deciding whether to take or pass a primary model's side rather than learning the side from scratch.
- Hudson & Thames' meta-labeling article supports the same architecture: use a primary model to create candidate sides, then a secondary model determines trade/no-trade. It also notes meta-labeling needs a good primary algorithm plus contextual features; a weak primary model only reduces downside.
- The CPCV article emphasizes robustness over one best backtest peak: use chronology-respecting, purged validation and prefer stable parameter regions rather than single sharp optima.
- CatBoost has native ranking support through `CatBoostRanker`, including ranking losses such as `YetiRank`, `PairLogit`, `LambdaMart`, `QuerySoftMax`, and metrics like `NDCG`, `PrecisionAt`, and `RecallAt`.
- The focal-loss reference supports the general idea of down-weighting easy majority examples in imbalanced classification, but this repo already uses CatBoost and the next local experiment is better served by native ranking losses before adding a custom neural objective.

## Actionable Conclusion

The next structurally different experiment should not be another global threshold or raw runner-probability classifier. It should be a candidate-level ranking probe:

- Keep v84/v95 as the primary candidate generator.
- Build labels from live-style path outcomes: high relevance for `+60% before -18%`, medium for `+25% before -18%`, low/zero for stop-first or flat paths.
- Group candidates by chronological slice or candidate batch and train a small `CatBoostRanker` probe to rank runner candidates above collapses.
- Use validation/final/walk-forward/stress replay against the current best v95 baseline.
- Reject immediately if validation gains depend on very few examples, if trade count explodes, or if walk-forward/stress worsens.

This is different from rejected v91/v93 because it does not replace the entry-value model with a raw binary runner probability. It keeps the strong primary model and tests whether a ranking objective can order plausible candidates better inside the already narrow candidate set.

## Local Probe Result

Implemented a read-only probe in `src/pipeline/candidate_ranker_probe.py` and `scripts/run_candidate_ranker_probe.py`. The first full-file attempts were stopped before completion because rebuilding all lifecycle samples used more than 5GB RAM for several minutes on the live machine. The probe was then bounded to four explicit closed lifecycle files for a smallest useful falsification pass, so the report is not tied to an actively appended collector file.

Commands:

- `venv/bin/python -m unittest tests.model.test_buy_catboost tests.model.test_candidate_ranker_probe tests.model.test_candidate_ranker_probe_cli`
- `venv/bin/python scripts/run_candidate_ranker_probe.py --model-dir data/models/20260519_v95_v84_selective_nearmiss_gate --lifecycle-dir data/training --output data/replay_reports/v96_candidate_ranker_probe_recent4_20260519.json --train-split-ratio 0.34 --validation-split-ratio 0.25 --min-validation-files 1 --min-eval-files 1 --max-samples-per-token 120 --sample-cache-dir .cache/candidate_ranker_probe_stable4 --top-k-per-group 1 --lifecycle-file data/training/lifecycle_incremental_20260406_212641_part007.jsonl --lifecycle-file data/training/lifecycle_incremental_20260406_212641_part008.jsonl --lifecycle-file data/training/lifecycle_incremental_20260406_212641_part009.jsonl --lifecycle-file data/training/lifecycle_incremental_20260516_212042.jsonl`

Results:

- `recent4`: validation improved (`ranker_top_relevance_sum=45.0` vs entry-value `41.0`, clean runners `12` vs `9`, collapse `1` vs `1`), but final got worse (`60.0` vs `61.0`, clean runners `15` vs `15`, collapse `5` vs `4`).
- The final `recent4` report records the complete v95 near gate, including `buy_near_min_age_seconds=0.0`, the explicit lifecycle file paths plus SHA-256 fingerprints, and post-load sample overlap counts of zero after train/validation token exclusion.

Decision: reject this direct YetiRank ranking probe as a model-improvement path for now. It is useful infrastructure, but the observed edge is not strong enough to justify full-data replay integration or live switching. The next iteration should use live path context more directly, for example conditional exit/re-entry state after STOP_LOSS or PPO exits, rather than a generic candidate ranker on the existing entry features.

## Rejected Ideas

- Do not lower the global threshold; latest v95 rejects and earlier v84 near-threshold sweeps both show collapse risk.
- Do not repeat token balancing alone; v80 and v93 already showed weak robustness.
- Do not repeat blanket partial exits or longer hold; v94 and the v84 partial-exit sweep were not robust enough.
- Do not prioritize focal loss first; it would require new custom objective plumbing, while CatBoost ranking is already available and better aligned with "rank rare winners above many rejects."
- Do not repeat a direct CatBoost `YetiRank` probe over the existing v95/v84 candidate features unless the candidate construction changes materially. The recent4 falsification showed only a small validation ranking gain and no final gain.
