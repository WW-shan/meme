# Flow-Enhanced Path-State Meta Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Test whether adding causal signal-time order-flow/toxicity features to the existing replay-only path-state meta gate creates a usable take/skip middle band that improves expected live profitability without increasing 10% live risk.

**Architecture:** Keep `data/models/20260519_v95_v84_selective_nearmiss_gate` as the primary candidate generator and keep the existing `path_state_scores_by_episode` replay hook as the only gate mechanism. Extend only the path-state meta-model feature vector with decision-time order-flow fields already produced by `src/data/feature_extractor.py`; then rerun validation/final replay through `scripts/run_path_state_meta_gate_replay.py` under strict live-sized assumptions. Do not add live runtime config or switch the bot from this experiment.

**Tech Stack:** Python `unittest`, CatBoost-backed `BuyCatBoostModel`, existing model replay pipeline, SmartSearch research artifacts under `docs/research/20260521-flow-meta-replay-gate/`.

---

### Task 1: Add Flow Features To Path-State Rows

**Files:**
- Modify: `src/pipeline/path_state_meta_probe.py`
- Modify: `tests/model/test_path_state_meta_probe.py`

- [ ] **Step 1: Write the failing feature test**

Add or extend a test in `tests/model/test_path_state_meta_probe.py` that builds a sample with these decision-time feature values:

```python
"total_buy_volume": 10.0,
"total_sell_volume": 2.5,
"volume_10s": 1.5,
"volume_30s": 2.0,
"buy_pressure": 0.80,
"buy_sell_overlap_ratio_60s": 0.25,
"recent_seller_reentry_ratio_30s": 0.10,
"buyer_set_churn_10s_vs_prev50s": 0.40,
"lp_resistance_ratio_10s": 3.0,
```

Assert that `build_path_state_features(...)` returns exact copied flow fields plus derived fields:

```python
self.assertEqual(features["total_buy_volume"], 10.0)
self.assertEqual(features["total_sell_volume"], 2.5)
self.assertEqual(features["volume_10s"], 1.5)
self.assertEqual(features["buy_pressure"], 0.80)
self.assertEqual(features["sell_pressure"], 0.20)
self.assertAlmostEqual(features["buy_sell_volume_ratio"], 4.0)
self.assertEqual(features["buy_sell_overlap_ratio_60s"], 0.25)
self.assertEqual(features["recent_seller_reentry_ratio_30s"], 0.10)
self.assertEqual(features["buyer_set_churn_10s_vs_prev50s"], 0.40)
self.assertEqual(features["lp_resistance_ratio_10s"], 3.0)
```

Run:

```bash
venv/bin/python -m unittest tests.model.test_path_state_meta_probe
```

Expected before implementation: fail because the new flow fields are missing.

- [ ] **Step 2: Implement minimal causal flow feature copy**

In `src/pipeline/path_state_meta_probe.py`, update `build_path_state_features()` to copy only signal-time feature-extractor fields from `features`, with safe numeric defaults:

```python
total_buy_volume = _as_float(features.get("total_buy_volume"), 0.0)
total_sell_volume = _as_float(features.get("total_sell_volume"), 0.0)
buy_pressure = _as_float(features.get("buy_pressure"), 0.5)
sell_pressure = 1.0 - max(0.0, min(1.0, buy_pressure))
```

Add returned feature keys:

```python
"total_buy_volume": float(total_buy_volume),
"total_sell_volume": float(total_sell_volume),
"volume_10s": float(_as_float(features.get("volume_10s"), 0.0)),
"buy_pressure": float(buy_pressure),
"sell_pressure": float(sell_pressure),
"buy_sell_volume_ratio": float(_buy_sell_volume_ratio(total_buy_volume, total_sell_volume)),
"buy_sell_overlap_ratio_60s": float(_as_float(features.get("buy_sell_overlap_ratio_60s"), 0.0)),
"recent_seller_reentry_ratio_30s": float(_as_float(features.get("recent_seller_reentry_ratio_30s"), 0.0)),
"buyer_set_churn_10s_vs_prev50s": float(_as_float(features.get("buyer_set_churn_10s_vs_prev50s"), 0.0)),
"lp_resistance_ratio_10s": float(_as_float(features.get("lp_resistance_ratio_10s"), 0.0)),
```

Do not use future label fields, `live_*` outcomes, MFE/MAE, or post-signal lifecycle events as features.

- [ ] **Step 3: Verify targeted tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_path_state_meta_probe
```

Expected: OK.

### Task 2: Run Strict Replay Falsification

**Files:**
- Read-only command output: `data/replay_reports/path_state_meta_gate_replay_20260521_flow_enhanced_v95.json`

- [ ] **Step 1: Run the replay-only sweep**

Run:

```bash
venv/bin/python scripts/run_path_state_meta_gate_replay.py \
  --model-dir data/models/20260519_v95_v84_selective_nearmiss_gate \
  --lifecycle-dir data/training \
  --output data/replay_reports/path_state_meta_gate_replay_20260521_flow_enhanced_v95.json \
  --force \
  --no-cache
```

Expected: report is written and includes validation baseline, validation candidates, final baseline, final confirmation, `decision`, and `live_switch_evidence=false`. Use `--no-cache` for feature-plumbing experiments unless the relevant sample caches are explicitly checked to contain the new feature fields.

- [ ] **Step 2: Extract decision metrics**

Run:

```bash
venv/bin/python - <<'PY'
import json
from pathlib import Path
p = Path("data/replay_reports/path_state_meta_gate_replay_20260521_flow_enhanced_v95.json")
d = json.loads(p.read_text())
print(json.dumps({
    "decision": d.get("decision"),
    "live_switch_evidence": d.get("live_switch_evidence"),
    "selected": d.get("selected_candidate", {}),
    "final": d.get("final_confirmation", {}),
}, ensure_ascii=False, indent=2, default=str))
PY
```

Accept only if validation and final both beat the current best v95 baseline on net profit, win rate, max drawdown, walk-forward, stress, and trade-count discipline. Otherwise reject and record why.

### Task 3: Record Evidence

**Files:**
- Modify: `docs/research/20260521-flow-meta-replay-gate/summary.md`
- Modify: `docs/model_scoreboard.md`

- [ ] **Step 1: Write the research summary**

Create `docs/research/20260521-flow-meta-replay-gate/summary.md` with:

```markdown
# Flow Meta Replay Gate Research Summary

## Live Evidence

...

## Prior Experiments To Avoid

...

## Research Evidence

...

## Hypothesis

...

## Experiment

...

## Decision

...
```

Include the live candidates from the current probe (`XYZ`, `Fren`, `CTW`, `TEST`, `🆙`) and cite saved SmartSearch evidence files in this directory.

- [ ] **Step 2: Update the scoreboard**

Add a dated row to `docs/model_scoreboard.md` with model/config, report path, strict metrics, accept/reject decision, and next direction. If the replay report is not committed because `data/` is ignored, explicitly say the report is a local generated artifact unless it is force-added.

### Task 4: Verification, Review, Commit

**Files:**
- All changed files from Tasks 1 and 3

- [ ] **Step 1: Run verification**

Run:

```bash
venv/bin/python -m unittest tests.model.test_path_state_meta_probe
venv/bin/python -m py_compile src/pipeline/path_state_meta_probe.py scripts/run_path_state_meta_gate_replay.py
git diff --check
git status --short --untracked-files=all -- docs/goals
git diff -- docs/goals/
git diff --cached -- docs/goals/
```

Expected: tests pass, compile passes, diff check clean, and no `docs/goals/` changes.

- [ ] **Step 2: Perform two strict reviews after the final edit**

Use two reviewer passes after the last code/docs edit. Reviews must check:

- no future leakage in meta-gate features
- replay report metrics match the written summary
- no live config switch
- 10% sizing remains enforced
- no `docs/goals/` edits
- pull-and-run implications are accurate

- [ ] **Step 3: Commit and push meaningful accepted/rejected node**

If there is a meaningful diff after reviews:

```bash
git add src/pipeline/path_state_meta_probe.py tests/model/test_path_state_meta_probe.py docs/research/20260521-flow-meta-replay-gate docs/superpowers/plans/2026-05-21-flow-enhanced-path-state-meta-gate.md docs/model_scoreboard.md
git add -f data/replay_reports/path_state_meta_gate_replay_20260521_flow_enhanced_v95.json
git commit -m "Test flow-enhanced path-state meta gate"
git push
```

Do not include live `.env` changes unless the candidate strictly passes every live-switch gate.
