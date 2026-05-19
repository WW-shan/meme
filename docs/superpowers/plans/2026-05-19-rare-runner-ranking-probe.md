# Rare Runner Ranking Probe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only offline probe that tests whether a candidate-level CatBoost ranking objective can rank rare clean runners above collapse/flat candidates inside the existing v95/v84 entry stack.

**Architecture:** Keep the live bot untouched. Add a small `CandidateRankCatBoostModel` wrapper, a `src.pipeline.candidate_ranker_probe` module that builds candidate rows from existing lifecycle samples and model artifacts, and a thin CLI that writes a JSON report under `data/replay_reports/`. The probe compares against the v95 incumbent and is evidence for the next model iteration, not a live switch by itself.

**Tech Stack:** Python `unittest`, CatBoost `CatBoostRanker`, existing `src.pipeline.train_hybrid` sample loading/splitting helpers, existing `src.pipeline.model_replay.load_model_artifacts`, SmartSearch research saved in `docs/research/20260519-rare-runner-ranking/`.

---

## Live Evidence Gate

Use this plan only after the live-first note for this cycle has been collected:

- Live model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Live sizing: `POSITION_SIZE=0.10`
- Current state: zero open positions, collector running, bot running under `memectl`/tmux
- New v95 live trades after startup: none in the checked window
- Strong v95 rejects: mostly correct skips; no newest missed runner
- Failure tag: `rare_clean_runner_detection_without_broadening_entries`
- Current incumbent to beat: v95 final `511.4778%`, `0.03067113` BNB profit, `44` trades, `79.5455%` win rate, `-8.0587%` max drawdown, `111.8292%` walk-forward worst return

Reject the direction if the report only improves headline return by increasing trade count broadly, weakening validation, or depending on all-in/gross metrics.

## Files

- Modify: `src/model/buy_catboost.py`
- Create: `src/pipeline/candidate_ranker_probe.py`
- Create: `scripts/run_candidate_ranker_probe.py`
- Modify: `tests/model/test_buy_catboost.py`
- Create: `tests/model/test_candidate_ranker_probe.py`
- Create: `tests/model/test_candidate_ranker_probe_cli.py`
- Update after experiment: `docs/research/20260519-rare-runner-ranking/summary.md`
- Update after experiment: `docs/model_scoreboard.md` only if the probe yields an accept/reject result worth recording

Do not touch:

- `.env`
- `.env.example`
- `src/trader/`
- `tools/memectl`
- live bot or collector process state

## Task 1: Add CandidateRankCatBoostModel

**Files:**
- Modify: `tests/model/test_buy_catboost.py`
- Modify: `src/model/buy_catboost.py`

- [ ] **Step 1: Write the failing test**

Append this test to `TestBuyCatBoost`:

```python
    def test_candidate_ranker_fit_passes_group_id_and_cat_features(self):
        module = _load_module()
        df = pd.DataFrame(
            {
                "creator_id": ["a", "b", "a", "c"],
                "current_price": [1.0, 1.1, 1.2, 1.3],
            }
        )
        fake_model = MagicMock()

        with patch.object(module, "CatBoostRanker", return_value=fake_model) as mock_cls:
            model = module.CandidateRankCatBoostModel(cat_feature_names=["creator_id"])
            model.fit(df, [0.0, 3.0, 1.0, 2.0], group_id=["g1", "g1", "g2", "g2"])

        self.assertTrue(fake_model.fit.called)
        self.assertEqual(fake_model.fit.call_args.kwargs["group_id"], ["g1", "g1", "g2", "g2"])
        self.assertEqual(fake_model.fit.call_args.kwargs["cat_features"], [0])
        self.assertEqual(mock_cls.call_args.kwargs["loss_function"], "YetiRank")
        self.assertFalse(mock_cls.call_args.kwargs["allow_writing_files"])
```

- [ ] **Step 2: Verify RED**

Run:

```bash
venv/bin/python -m unittest tests.model.test_buy_catboost.TestBuyCatBoost.test_candidate_ranker_fit_passes_group_id_and_cat_features
```

Expected: fail because `CandidateRankCatBoostModel` is not defined.

- [ ] **Step 3: Implement minimal wrapper**

In `src/model/buy_catboost.py`, import/fallback `CatBoostRanker`, add default ranker params, and add:

```python
class CandidateRankCatBoostModel:
    def __init__(self, cat_feature_names=None, random_state=42, catboost_params=None):
        self.cat_feature_names = list(cat_feature_names or [])
        self.random_state = int(random_state)
        self.catboost_params = dict(DEFAULT_CATBOOST_RANKER_PARAMS)
        self.catboost_params.update(dict(catboost_params or {}))
        self.model = None

    def _cat_feature_indices(self, X):
        if not hasattr(X, "columns"):
            return []
        return [int(X.columns.get_loc(name)) for name in self.cat_feature_names if name in X.columns]

    def fit(self, X, y, group_id, eval_set=None):
        if len(group_id) != len(y):
            raise ValueError("group_id length must match y length")
        cat_indices = self._cat_feature_indices(X)
        self.model = CatBoostRanker(
            loss_function="YetiRank",
            random_seed=self.random_state,
            verbose=False,
            allow_writing_files=False,
            **self.catboost_params,
        )
        fit_kwargs = {"group_id": list(group_id), "cat_features": cat_indices or None}
        if eval_set is not None:
            fit_kwargs["eval_set"] = eval_set
            fit_kwargs["use_best_model"] = True
        self.model.fit(X, y, **fit_kwargs)
        return self

    def predict(self, X):
        if self.model is None:
            raise ValueError("model is not fitted")
        return self.model.predict(X)
```

- [ ] **Step 4: Verify GREEN**

Run:

```bash
venv/bin/python -m unittest tests.model.test_buy_catboost.TestBuyCatBoost.test_candidate_ranker_fit_passes_group_id_and_cat_features
```

Expected: pass.

## Task 2: Add Pure Probe Helpers

**Files:**
- Create: `tests/model/test_candidate_ranker_probe.py`
- Create: `src/pipeline/candidate_ranker_probe.py`

- [ ] **Step 1: Write failing tests**

Create `tests/model/test_candidate_ranker_probe.py` with tests for:

```python
class TestCandidateRankerProbe(unittest.TestCase):
    def test_relevance_prefers_clean_runner_over_medium_and_collapse(self):
        m = _load_module()
        self.assertEqual(m.candidate_relevance({"live_target_hit_before_stop": 1, "live_risk_adjusted_return_pct": 75.0}), 3.0)
        self.assertEqual(m.candidate_relevance({"live_target_hit_before_stop": 0, "live_risk_adjusted_return_pct": 32.0}), 1.0)
        self.assertEqual(m.candidate_relevance({"live_target_hit_before_stop": 0, "live_risk_adjusted_return_pct": -20.0}), 0.0)

    def test_candidate_rows_keep_v95_primary_and_near_gate_only(self):
        m = _load_module()
        samples = [...]
        rows = m.build_candidate_rows(samples, buy_probabilities=[0.99, 0.95, 0.95, 0.93], entry_scores=[40.0, 33.0, 20.0, 80.0], runtime_params={...})
        self.assertEqual([row["token"] for row in rows], ["0xprimary", "0xnear"])
        self.assertEqual(rows[0]["candidate_source"], "primary")
        self.assertEqual(rows[1]["candidate_source"], "near")

    def test_group_ids_bucket_by_sample_time(self):
        m = _load_module()
        rows = [
            {"sample_time": 100, "token": "0xa"},
            {"sample_time": 119, "token": "0xb"},
            {"sample_time": 141, "token": "0xc"},
        ]
        self.assertEqual(m.assign_group_ids(rows, bucket_seconds=30), ["100", "100", "130"])
```

- [ ] **Step 2: Verify RED**

Run:

```bash
venv/bin/python -m unittest tests.model.test_candidate_ranker_probe
```

Expected: fail because the module does not exist.

- [ ] **Step 3: Implement helper module**

Implement:

- `candidate_relevance(labels, target_return_pct=60.0, medium_return_pct=25.0)`
- `assign_group_ids(rows, bucket_seconds=30)`
- `build_candidate_rows(samples, buy_probabilities, entry_scores, runtime_params)`
- `summarize_candidates(rows)`
- `evaluate_ranker_predictions(rows, predictions, top_k_per_group=1)`

Candidate filtering rules:

- primary candidate: `buy_prob >= buy_threshold`
- near candidate: `buy_prob >= buy_near_threshold_min_prob` and below primary threshold, with `entry_score >= buy_near_min_pred_return`, `entry_volume_30s >= buy_near_min_entry_volume_30s`, `entry_price_volatility >= buy_near_min_entry_price_volatility`, and `age >= buy_near_min_age_seconds`
- primary candidates must respect `max_entry_age_seconds`, `min_entry_score`, `min_entry_volume_30s`, and `min_entry_price_volatility` where configured
- near candidates must respect `max_entry_age_seconds` plus the `buy_near_*` score, volume, volatility, and age gates; do not apply the primary `min_entry_volume_30s=1.5` floor to the near band because v95 deliberately allows `buy_near_min_entry_volume_30s=1.25`

- [ ] **Step 4: Verify GREEN**

Run:

```bash
venv/bin/python -m unittest tests.model.test_candidate_ranker_probe
```

Expected: pass.

## Task 3: Add Probe CLI

**Files:**
- Create: `tests/model/test_candidate_ranker_probe_cli.py`
- Create: `scripts/run_candidate_ranker_probe.py`

- [ ] **Step 1: Write failing CLI tests**

Tests must verify:

- default args: `--model-dir`, `--lifecycle-dir`, `--output`, `--split ratios`, `--sample-cache-dir`
- `main()` calls `run_candidate_ranker_probe(...)` with parsed args
- stdout prints compact JSON

- [ ] **Step 2: Verify RED**

Run:

```bash
venv/bin/python -m unittest tests.model.test_candidate_ranker_probe_cli
```

Expected: fail because script does not exist.

- [ ] **Step 3: Implement CLI**

`scripts/run_candidate_ranker_probe.py` should:

- load model artifacts with `src.pipeline.model_replay.load_model_artifacts`
- load selected runtime params from manifest
- split lifecycle files with `_split_lifecycle_files_three_way`
- load train/validation/final samples with `_load_samples`
- score buy probability with the loaded buy model and entry value scores with the loaded entry-value model
- train `CandidateRankCatBoostModel` on train candidate rows
- evaluate ranking quality on validation and final without changing live replay behavior
- write a JSON report to `data/replay_reports/v96_candidate_ranker_probe_recent4_20260519.json`

- [ ] **Step 4: Verify GREEN**

Run:

```bash
venv/bin/python -m unittest tests.model.test_candidate_ranker_probe_cli
```

Expected: pass.

## Task 4: Run the Probe

**Files:**
- Create: `data/replay_reports/v96_candidate_ranker_probe_recent4_20260519.json`
- Update: `docs/research/20260519-rare-runner-ranking/summary.md`
- Update: `docs/model_scoreboard.md` if the probe gives an accept/reject result that should prevent repeated work

- [ ] **Step 1: Run targeted tests**

```bash
venv/bin/python -m unittest tests.model.test_buy_catboost tests.model.test_candidate_ranker_probe tests.model.test_candidate_ranker_probe_cli
```

- [ ] **Step 2: Run the report**

```bash
venv/bin/python scripts/run_candidate_ranker_probe.py \
  --model-dir data/models/20260519_v95_v84_selective_nearmiss_gate \
  --lifecycle-dir data/training \
  --output data/replay_reports/v96_candidate_ranker_probe_recent4_20260519.json \
  --train-split-ratio 0.34 \
  --validation-split-ratio 0.25 \
  --min-validation-files 1 \
  --min-eval-files 1 \
  --max-samples-per-token 120 \
  --sample-cache-dir .cache/candidate_ranker_probe_stable4 \
  --top-k-per-group 1 \
  --lifecycle-file data/training/lifecycle_incremental_20260406_212641_part007.jsonl \
  --lifecycle-file data/training/lifecycle_incremental_20260406_212641_part008.jsonl \
  --lifecycle-file data/training/lifecycle_incremental_20260406_212641_part009.jsonl \
  --lifecycle-file data/training/lifecycle_incremental_20260516_212042.jsonl
```

- [ ] **Step 3: Decision rule**

Accept only if validation and final both support the direction:

- validation top-1 group relevance improves over baseline entry-value ordering
- final ranking quality improves without selecting materially more candidates
- clean-runner recall improves while collapse selection does not rise
- results are not dependent on one group or one outlier token

This task does not live switch. A live switch requires a later replay-integrated model that strictly beats v95 on final, validation, walk-forward, and stress replay.

## Task 5: Review, Commit, Push

**Files:**
- All changed files

- [ ] **Step 1: Run verification**

```bash
git diff --check
venv/bin/python -m unittest tests.model.test_buy_catboost tests.model.test_candidate_ranker_probe tests.model.test_candidate_ranker_probe_cli
```

- [ ] **Step 2: Strict review pass 1**

Parent-agent review of the final diff:

- no live bot/config changes
- no position-size increase
- no leakage from validation/final into train
- candidate filter matches v95 runtime params
- report contains incumbent comparison and reject/accept basis

- [ ] **Step 3: Strict review pass 2**

Independent subagent or fresh-pass review:

- code correctness
- tests cover behavior
- report paths reproducible after pull
- no uncommitted accidental artifacts
- no live switch claim without strict replay gate

If either review finds a material issue, fix it and rerun both reviews after the last edit.

- [ ] **Step 4: Commit and push**

```bash
git add src/model/buy_catboost.py src/pipeline/candidate_ranker_probe.py scripts/run_candidate_ranker_probe.py tests/model/test_buy_catboost.py tests/model/test_candidate_ranker_probe.py tests/model/test_candidate_ranker_probe_cli.py docs/research/20260519-rare-runner-ranking docs/superpowers/plans/2026-05-19-rare-runner-ranking-probe.md docs/model_scoreboard.md
git add -f data/replay_reports/v96_candidate_ranker_probe_recent4_20260519.json
git commit -m "Add rare runner ranking probe"
git push
```
