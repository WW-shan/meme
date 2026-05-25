## Question

For rejected signal candidates in the live FourMeme bot, can a learned candidate-level meta-label / segment model separate quick-profit runners from fast-profit-then-collapse and stop-first failures better than another static rule, under source-split validation?

## SmartSearch Commands

- `smart-search doctor --format json > docs/research/20260525-candidate-meta-label-research/00-doctor.json`
- `smart-search deep "For rejected signal candidates in a live meme-token trading system, what research-backed methods best support a learned candidate-level meta-label or segment model that separates quick-profit runners from fast-profit-then-collapse and stop-first collapses under purged walk-forward validation?" --budget deep --format json --output docs/research/20260525-candidate-meta-label-research/plan.json`
- `smart-search search "For rejected signal candidates in a live meme-token trading system, what research-backed methods best support a learned candidate-level meta-label or segment model that separates quick-profit runners from fast-profit-then-collapse and stop-first collapses under purged walk-forward validation?" --validation balanced --extra-sources 3 --format json --output docs/research/20260525-candidate-meta-label-research/01-search.json`
- `smart-search zhipu-search "meta-labeling triple barrier purged walk-forward validation trade selection crypto" --count 5 --format json --output docs/research/20260525-candidate-meta-label-research/02-zhipu.json`
- `smart-search search "meta-labeling triple barrier purged cross validation trade selection financial machine learning" --validation balanced --extra-sources 3 --timeout 90 --format json --output docs/research/20260525-candidate-meta-label-research/03-search-validation.json`
- `smart-search fetch "https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/" --format markdown --output docs/research/20260525-candidate-meta-label-research/04-fetch-hudsonthames.md`
- `smart-search fetch "https://mlfinpy.readthedocs.io/en/latest/Labelling.html" --format markdown --output docs/research/20260525-candidate-meta-label-research/05-fetch-mlfinpy-labeling.md`
- `smart-search fetch "https://www.quantconnect.com/forum/discussion/14706/why-meta-labeling-is-not-a-silver-bullet/" --format markdown --output docs/research/20260525-candidate-meta-label-research/06-fetch-quantconnect-limitations.md`
- `smart-search fetch "https://en.wikipedia.org/wiki/Purged_cross-validation" --format markdown --output docs/research/20260525-candidate-meta-label-research/07-fetch-purged-cv.md`

`EXA_API_KEY` and `ZHIPU_API_KEY` were not configured, so Exa/Zhipu outputs are recorded as provider gaps and are not used as positive evidence.

## Fetched Sources

- Hudson & Thames meta-labeling/triple-barrier article: `04-fetch-hudsonthames.md`
- mlfinpy labeling docs: `05-fetch-mlfinpy-labeling.md`
- QuantConnect limitations discussion: `06-fetch-quantconnect-limitations.md`
- Purged cross-validation page: `07-fetch-purged-cv.md`

## What Applies To This Bot

The fetched sources support a candidate-level design where the current bot/model remains the primary signal generator and a secondary model learns whether to act on a presented opportunity. The relevant local label already exists in the time-to-barrier probe: `quick_take_profit` / `conditional_slow_hold` are positives, while `skip`, `stop_first`, `flat_timeout`, and `missing_path` are not acceptable live-buy evidence.

For this bot, the learned layer must be evaluated as a read-only probe first. It must use only decision-time features such as probability, predicted return, age, volume, volatility, and flow metrics. It must not use ex-post path fields such as MFE/MAE/barrier class as inputs. Validation must be source/time split, with the latest live window held out, because overlapping future labels can leak into training.

## Live Evidence

The refreshed live window after `2026-05-25 13:25:41` had `0` paper-trade rows, so this was a high-confidence rejected-signal round. The committed time-to-barrier report `data/replay_reports/time_to_barrier_probe_20260525_next_round_since_132541.json` emitted `35` per-token candidates:

- `fast_profit=4`
- `fast_profit_then_collapse=4`
- `flat_timeout=17`
- `missing_path=2`
- `slow_runner=2`
- `stop_first=6`

The strongest live trigger remains the rejected-candidate segment around `BNBMIC`, `Memepedia`, `AWESOME`, `牛币`, and the fresh `战壕神曲` missing-path reject. `BNBMIC` is especially useful because it reached `+25%` in about `14.98s`, later reached `+60%`, and still hit the `-18%` zone about `31.98s` after signal. That is exactly the quick-profit versus collapse distinction this round is trying to learn.

## Experiment

Implemented a read-only learned probe:

- Core: `src/pipeline/candidate_meta_label_probe.py`
- CLI: `scripts/probe_candidate_meta_label.py`
- Tests: `tests/model/test_candidate_meta_label_probe.py`, `tests/model/test_candidate_meta_label_probe_cli.py`

The probe trains a small deterministic decision tree over numeric decision-time fields from multiple time-to-barrier reports. It keeps the latest report as validation and writes a read-only report that is explicitly not live-switch evidence.

Commands:

- Targeted tests: `python -m unittest tests.model.test_candidate_meta_label_probe tests.model.test_candidate_meta_label_probe_cli`
- Time-to-barrier refresh: `python scripts/probe_time_to_barrier.py ... --output data/replay_reports/time_to_barrier_probe_20260525_next_round_since_132541.json --since '2026-05-25 13:25:41' --max-candidate-sample 0`
- Support-rule refresh: `python scripts/probe_support_action_policy.py --time-to-barrier-report data/replay_reports/time_to_barrier_probe_20260525_next_round_since_132541.json --output data/replay_reports/support_action_policy_20260525_next_round_since_132541.json --min-selected 3 --force`
- Selected latest-window probe: `python scripts/probe_candidate_meta_label.py ... --time-to-barrier-report data/replay_reports/time_to_barrier_probe_20260525_next_round_since_132541.json --output data/replay_reports/candidate_meta_label_probe_20260525_selected_d3_l120_thr020.json --validation-report-count 1 --probability-threshold 0.20 --max-depth 3 --min-samples-leaf 120`
- Strict two-window probe: `python scripts/probe_candidate_meta_label.py ... --output data/replay_reports/candidate_meta_label_probe_20260525_two_window_validation_thr020.json --validation-report-count 2 --probability-threshold 0.20 --max-depth 3 --min-samples-leaf 3`
- Small in-process grid summary: `data/replay_reports/candidate_meta_label_probe_20260525_grid_summary.json`

## Result

Selected latest-window probe:

- Train: `3980` candidates, base precision `9.4724%`, selected `804`, selected precision `37.6866%`
- Latest validation: `35` candidates, base precision `28.5714%`, selected `15`, positives `7`, precision `46.6667%`
- Important learned features: `flow_buy_volume_10s`, `token_age_seconds`, `flow_buy_sell_ratio_60s`, `flow_signed_imbalance_30s`, `flow_metrics_available`

Strict two-window validation:

- Train: `246` candidates, base precision `19.1057%`, selected `104`, selected precision `43.2692%`
- Validation: `3769` candidates, base precision `9.0210%`, selected `1857`, positives `243`, precision `13.0856%`

The latest-window lift is real enough to keep as shadow evidence, but the two-window precision is too low and coverage too broad. It also does not beat the refreshed local support rule `high_prob_low_toxic_overlap` on the latest window (`6/9`, `66.6667%` precision), although that rule is still too small and static for live promotion. The learned probe is not a live-switch candidate and not strong enough to justify a runtime overlay.

## What We Reject

- Reject a live switch or runtime gate from this learned probe.
- Reject another static `high_prob_positive_pred`-style rule as the main path; the fresh support report still shows that simple high-probability positive-pred rules pick `战壕神曲` / `牦牛大叔`-style negatives.
- Reject using the broad-search summary alone as evidence; only fetched pages and local reports are decision evidence.

## Next Experiment

Keep the candidate-level learned direction, but narrow it before replay integration:

- train on a stricter candidate universe that matches live-actionable candidates rather than all rejected TTB rows;
- use risk-coverage selection, not a fixed `0.5` classifier threshold;
- require source-split validation precision materially above the current `13.0856%` two-window result before any replay/runtime integration;
- compare against `high_prob_low_toxic_overlap` and current v95/v84 baseline under live-sized replay before any live change.
