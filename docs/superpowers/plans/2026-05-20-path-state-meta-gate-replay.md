# Path-State Meta Gate Replay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a replay-only v95 candidate filter that learns take/skip scores from causal path-state features and barrier-priority path labels, then accept it only if it beats the corrected v95 baseline.

**Architecture:** Keep `data/models/20260519_v95_v84_selective_nearmiss_gate` as the primary candidate generator. Add an explicit, default-off `path_state_meta_gate` to replay, fed by score maps built outside the live bot. The probe trains on train split only, selects thresholds on validation, and confirms once on final.

**Tech Stack:** Python `unittest`, existing `src.pipeline.train_hybrid` replay loop, `src.pipeline.model_replay`, CatBoost through `src.model.buy_catboost`, and `scripts/run_shadow_meta_gate_replay.py` as the CLI/report pattern.

---

## Current Live Evidence

- `黄金夏日` opened at `2026-05-20 19:00:43.889423` with `prob=0.9730`, `PredReturn=41.26`, `near_threshold_rescue_used=true`, and `+3.67%` entry slippage.
- Its lifecycle had a pre-entry peak around `1.4743379485e-08`; the signal price was already about `-60.44%` below that peak.
- This shows the live failure shape is a causal path-state issue: the model can buy after the pump has already retraced.
- Recent rejected runners show the opposite shape: many were high-probability but low/negative PredReturn, often with lower volume/volatility than live buys.

## Files

- Create: `src/pipeline/path_state_meta_probe.py`
- Create: `scripts/run_path_state_meta_gate_replay.py`
- Create: `tests/model/test_path_state_meta_probe.py`
- Create: `tests/model/test_path_state_meta_gate_replay.py`
- Create: `tests/model/test_path_state_meta_gate_replay_cli.py`
- Modify: `src/pipeline/train_hybrid.py`
- Modify: `src/pipeline/model_replay.py`
- Modify if needed: `tests/model/test_model_replay.py`
- Modify after results: `docs/model_scoreboard.md`

## Acceptance Gate

Use strict live-sized replay against corrected v95 baseline:

- `model_dir=data/models/20260519_v95_v84_selective_nearmiss_gate`
- `position_fraction=0.1`
- `max_position_fraction=0.1`
- `fixed_stake_bnb=None`
- `max_open_positions=8`
- `skip_all_in_replay=True`

Validation candidate must beat validation baseline on:

- `net_profit_bnb`
- `win_rate`
- `max_drawdown_pct`
- `walk_forward_worst_net_return_pct`
- `walk_forward_worst_max_drawdown_pct`
- stress worst return/profit/drawdown
- no trade-count expansion for a filter-only gate
- no trade-count reduction larger than 25% or 1 trade minimum tolerance
- `path_state_meta_gate_signal_count > 0`
- `path_state_meta_gate_reject_count > 0`

Final confirmation must repeat the same gates once on final split. Latest model is not best model; switch live only if final passes and beats current best v95.

## Task 1: Add Replay Gate Contract

**Files:**
- Modify: `src/pipeline/train_hybrid.py`
- Modify: `src/pipeline/model_replay.py`
- Test: `tests/model/test_path_state_meta_gate_replay.py`
- Test: `tests/model/test_model_replay.py`

- [ ] **Step 1: Write failing tests**

Add tests that prove the new gate is default-off and only filters when explicit score maps and threshold are provided:

```python
def test_path_state_meta_gate_default_off_preserves_primary_entry(self):
    # Build a tiny replay episode where the primary entry would normally fill.
    # Call _run_eval_replay without buy_path_state_meta_gate_min_score.
    # Assert total_trades == 1 and path_state_meta_gate_* counts are zero.
```

```python
def test_path_state_meta_gate_rejects_low_scored_primary_candidate(self):
    # Same sample, explicit buy_path_state_meta_gate_min_score=0.5.
    # path_state_scores_by_episode=[{0: 0.25}].
    # Assert total_trades == 0 and reject_count == 1.
```

```python
def test_path_state_meta_gate_allows_high_scored_primary_candidate(self):
    # Same sample, score 0.75.
    # Assert total_trades == 1, signal_count == 1, entry_count == 1.
```

```python
def test_live_replay_config_ignores_manifest_path_state_gate_by_default(self):
    manifest = {"selected_runtime_params": {"buy_path_state_meta_gate_min_score": 0.7}}
    config = live_replay_config_from_manifest(manifest, max_open_positions=8)
    self.assertIsNone(config["buy_path_state_meta_gate_min_score"])
```

- [ ] **Step 2: Verify red**

Run:

```bash
venv/bin/python -m unittest tests.model.test_path_state_meta_gate_replay tests.model.test_model_replay
```

Expected: failures because the path-state gate keys and counts do not exist.

- [ ] **Step 3: Implement minimal replay gate**

Add `_run_eval_replay` parameters:

```python
path_state_scores_by_episode=None,
buy_path_state_meta_gate_min_score=None,
```

Normalize defaults:

```python
path_state_meta_gate_score_floor = _optional_nonnegative_finite(
    buy_path_state_meta_gate_min_score,
    "buy_path_state_meta_gate_min_score",
)
path_state_meta_gate_enabled = path_state_meta_gate_score_floor is not None
if path_state_scores_by_episode is None:
    path_state_scores_by_episode = [{} for _episode in episodes]
```

Apply after normal v95 primary/near/quality filters pass and before pending entry creation:

```python
path_state_meta_gate_used = False
if proposed_buy and path_state_meta_gate_enabled:
    path_state_meta_gate_signal_count += 1
    meta_score = path_state_score_by_index.get(sample_index)
    if meta_score is None or float(meta_score) < float(path_state_meta_gate_score_floor):
        path_state_meta_gate_reject_count += 1
        proposed_buy = False
    else:
        path_state_meta_gate_entry_count += 1
        path_state_meta_gate_used = True
```

Persist counts in `runtime_replay` and `evaluation`.

In `model_replay.live_replay_config_from_manifest`, add default-off keys:

```python
"buy_path_state_meta_gate_min_score": None,
"path_state_scores_by_episode": None,
```

Do not inherit these from manifests unless explicitly overridden.

- [ ] **Step 4: Verify green**

Run:

```bash
venv/bin/python -m unittest tests.model.test_path_state_meta_gate_replay tests.model.test_model_replay
```

Expected: OK.

## Task 2: Build Causal Path-State Probe

**Files:**
- Create: `src/pipeline/path_state_meta_probe.py`
- Test: `tests/model/test_path_state_meta_probe.py`

- [ ] **Step 1: Write failing tests**

Tests must cover leakage prevention:

```python
def test_path_state_features_use_only_prior_price_history(self):
    # Candidate at t=30 has prior prices at t=0,10,20 and future price at t=40.
    # Assert pre_entry_peak only uses <= t=30 and ignores t=40.
```

```python
def test_path_state_feature_builder_rejects_label_like_columns(self):
    # Include future_return_pct / live_target_hit_before_stop in source features.
    # Assert these do not appear in model feature output.
```

```python
def test_score_maps_preserve_episode_indices(self):
    # Two episode samples, only index 1 is a candidate.
    # Assert score map key is {1: score}, not {0: score}.
```

```python
def test_meta_labels_use_triple_barrier_fields(self):
    # live_target_hit_before_stop=1 -> positive.
    # live_stop_hit_before_target=1 -> negative.
```

- [ ] **Step 2: Verify red**

Run:

```bash
venv/bin/python -m unittest tests.model.test_path_state_meta_probe
```

Expected: import/attribute failures because the module does not exist.

- [ ] **Step 3: Implement probe helpers**

Create focused functions:

```python
def build_path_state_features(sample, prior_samples, *, buy_prob, entry_score) -> dict:
    # Only uses current sample features/meta and prior samples from the same token episode.
```

Feature families:

- `buy_prob`
- `entry_score`
- `age_seconds`
- `volume_30s`
- `price_volatility`
- `pre_entry_peak_drawdown_pct`
- `pre_entry_price_extension_pct`
- `recent_price_return_pct`
- `volume_ramp_ratio`
- `volatility_ramp_delta`
- `buy_prob_delta`
- `entry_score_delta`
- `prior_sample_count`

Label function:

```python
def path_state_meta_label(labels) -> int:
    if int(labels.get("live_target_hit_before_stop") or 0) == 1:
        return 1
    return 0
```

Use a small CatBoost classifier through `BuyCatBoostModel(catboost_params={"iterations": 120, "od_wait": 20})`.

- [ ] **Step 4: Verify green**

Run:

```bash
venv/bin/python -m unittest tests.model.test_path_state_meta_probe
```

Expected: OK.

## Task 3: Add Strict Replay CLI

**Files:**
- Create: `scripts/run_path_state_meta_gate_replay.py`
- Test: `tests/model/test_path_state_meta_gate_replay_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Tests:

```python
def test_refuses_non_strict_position_fraction(self):
    parse_args(["--position-fraction", "0.2"]) raises SystemExit or ArgumentTypeError.
```

```python
def test_report_contains_live_switch_false_until_final_gate_passes(self):
    # Patch run_model_replay and probe score builder.
    # Assert output report has live_switch_evidence false when final fails.
```

```python
def test_candidate_overrides_include_score_maps_and_threshold(self):
    # Patch run_model_replay, inspect calls.
    # Assert path_state_scores_by_episode and buy_path_state_meta_gate_min_score are passed only to candidate runs.
```

- [ ] **Step 2: Verify red**

Run:

```bash
venv/bin/python -m unittest tests.model.test_path_state_meta_gate_replay_cli
```

Expected: import failure because script does not exist.

- [ ] **Step 3: Implement CLI by copying proven pattern**

Copy the structure of `scripts/run_shadow_meta_gate_replay.py`, renaming:

- `shadow` -> `path_state`
- `buy_shadow_meta_gate_min_score` -> `buy_path_state_meta_gate_min_score`
- `shadow_scores_by_episode` -> `path_state_scores_by_episode`

Candidate threshold grid:

```python
def candidate_grid():
    for min_score in [0.35, 0.50, 0.65, 0.80]:
        yield {"buy_path_state_meta_gate_min_score": min_score}
```

The CLI must:

- run validation baseline
- train score maps from train to validation
- run validation candidates
- select only candidates passing strict gates
- run final baseline
- score final episodes with the validation-selected threshold
- run final confirmation
- write `data/replay_reports/path_state_meta_gate_replay_20260520_v95.json`

- [ ] **Step 4: Verify green**

Run:

```bash
venv/bin/python -m unittest tests.model.test_path_state_meta_gate_replay_cli
```

Expected: OK.

## Task 4: Run Full Evaluation

**Files:**
- Write ignored artifact: `data/replay_reports/path_state_meta_gate_replay_20260520_v95.json`
- Modify if accepted/rejected: `docs/model_scoreboard.md`

- [ ] **Step 1: Run focused tests**

```bash
venv/bin/python -m unittest \
  tests.model.test_path_state_meta_probe \
  tests.model.test_path_state_meta_gate_replay \
  tests.model.test_path_state_meta_gate_replay_cli \
  tests.model.test_model_replay
```

- [ ] **Step 2: Run replay CLI**

```bash
venv/bin/python scripts/run_path_state_meta_gate_replay.py --force
```

- [ ] **Step 3: Decide**

Reject unless validation and final both beat corrected v95 on every acceptance gate.

- [ ] **Step 4: Update scoreboard**

Add one row to `docs/model_scoreboard.md` with:

- live trigger
- research path
- candidate report path
- validation metrics
- final metrics
- accept/reject decision
- explicit live switch decision

## Task 5: Review, Commit, Push

**Files:**
- All changed files from tasks above.

- [ ] **Step 1: Strict review #1**

Review for spec compliance:

- no `docs/goals/live-model-optimization-goal.md` changes
- no `.env` or live bot config changes unless candidate accepted and user/live switch gate permits
- 10% sizing enforced
- final split used only once after validation selection
- no future path leakage in feature inputs

- [ ] **Step 2: Strict review #2**

Review for code quality:

- focused files
- no duplicated acceptance gate drift from shadow script unless intentionally copied
- score maps summarized in reports
- ignored replay report force-added if cited by scoreboard
- tests cover default-off behavior

- [ ] **Step 3: Full relevant tests**

```bash
venv/bin/python -m unittest \
  tests.model.test_path_state_meta_probe \
  tests.model.test_path_state_meta_gate_replay \
  tests.model.test_path_state_meta_gate_replay_cli \
  tests.model.test_model_replay \
  tests.model.test_train_hybrid_pipeline
```

- [ ] **Step 4: Commit and push important node**

If no live switch:

```bash
git add src/pipeline/path_state_meta_probe.py src/pipeline/train_hybrid.py src/pipeline/model_replay.py \
  scripts/run_path_state_meta_gate_replay.py tests/model/test_path_state_meta_probe.py \
  tests/model/test_path_state_meta_gate_replay.py tests/model/test_path_state_meta_gate_replay_cli.py \
  tests/model/test_model_replay.py docs/model_scoreboard.md \
  docs/research/20260520-late-pump-entry-veto docs/superpowers/plans/2026-05-20-path-state-meta-gate-replay.md
git add -f data/replay_reports/path_state_meta_gate_replay_20260520_v95.json
git commit -m "test: evaluate v95 path-state meta gate"
git push
```

If accepted and live switch is safe:

- confirm zero open positions
- update `.env`/model artifacts only if needed
- run tests
- commit/push
- restart only through `./tools/memectl bot restart`

## Result

Decision: rejected; no live switch.

Report:

```text
data/replay_reports/path_state_meta_gate_replay_20260520_v95.json
```

Outcome after the pinned-sample replay rerun:

- validation baseline: `26` trades, `0.00683256302289737` BNB net profit
- validation thresholds `0.35` through `0.90`: no-op, `26` entries, `0` rejects, identical profit
- validation thresholds `0.95`, `0.98`, `0.99`: `0` trades
- final selected candidate: no-op threshold `0.35`, `46` trades, `0.025563218696053474` BNB net profit
- final gate failed on profit improvement and required reject count

The experiment fixed replay tooling but did not improve the model. Score maps now use
the same preloaded validation/final sample snapshots as the corresponding replay
runs, exclude terminal non-enterable samples, carry episode metadata for alignment
validation, normalize JSON-roundtripped numeric score keys, and propagate into stress
replay. Direct replay reports summarize path-state score maps instead of serializing
the raw maps, and preloaded eval samples still apply excluded-token filtering. The
model-level result is negative: the learned path-state classifier has no useful middle
band for live switch evidence.
