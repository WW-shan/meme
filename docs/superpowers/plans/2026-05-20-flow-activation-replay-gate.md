# Flow Activation Replay Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Test whether bounded flow-activation and dead-flow path state can improve live-sized v95 replay profit without increasing the 10% position risk.

**Architecture:** Keep the live bot and `.env` untouched. Add replay-only/default-off flow gate parameters to `_run_eval_replay`, expose them only through explicit replay overrides, and drive a small CLI grid that compares validation and sealed final against the current v95 baseline. Use existing v95/v84 primary and near-threshold candidate generation; the new logic may veto weak candidates or exit dead-flow positions early, but must not lower the global threshold or increase stake.

**Tech Stack:** Python `unittest`, existing `src.pipeline.train_hybrid._run_eval_replay`, `src.pipeline.model_replay.run_model_replay`, JSON replay reports, 10% live sizing.

---

## Live Evidence Gate

- `赵长娥` clean activation: `prob=0.990143`, `PredReturn=65.7099`, signal-to-open `2.4718s`, `+25%` from signal in about `4.13s`, `+35%` in about `6.13s`, `+60%` in about `11.13s`, PPO exit net `+0.0001979536` BNB.
- `TSG` fake/weak activation: `prob=0.989631`, `PredReturn=39.5631`, only about `+9.66%` MFE from signal, first `-18%` about `86.55s` after signal, STOP_LOSS.
- `WAGMI` collapse: first `-18%` about `3.66s` after signal, STOP_LOSS.
- `币安 x402` dead flow: no meaningful post-entry upside and TIME_EXIT after `565.77s` for a small loss.
- Recent high-score rejects mostly had negative PredReturn, so the obvious global threshold/volume relaxation remains rejected.

## Research Inputs

- `docs/research/20260520-flow-activation-gate/summary.md`
- `docs/research/20260520-flow-activation-gate/02-fetch-hudson-meta-labeling.md`
- `docs/research/20260520-flow-activation-gate/03-fetch-mlfinpy-labelling.md`
- `docs/research/20260520-flow-activation-gate/04-fetch-freqtrade-orderflow.md`
- `docs/research/20260520-flow-activation-gate/05-fetch-pump-dump-thresholding.md`

## Files

- Modify: `src/pipeline/train_hybrid.py`
- Modify: `src/pipeline/model_replay.py`
- Create: `scripts/run_flow_activation_replay.py`
- Create: `tests/model/test_flow_activation_replay.py`
- Create: `tests/model/test_flow_activation_replay_cli.py`
- Later, if the experiment runs: create `data/replay_reports/flow_activation_replay_20260520_v95.json`
- Later, after result: update `docs/model_scoreboard.md`

## Replay-Only Parameters

Add these explicit-only runtime keys. They must default to `None` and must not be read from stale manifests unless explicit overrides set them:

- `buy_flow_activation_min_prob`
- `buy_flow_activation_min_pred_return`
- `buy_flow_activation_max_age_seconds`
- `buy_flow_activation_lookback_seconds`
- `buy_flow_activation_min_volume_ramp_ratio`
- `buy_flow_activation_min_volume_ramp_delta`
- `buy_flow_activation_min_pred_return_delta`
- `buy_flow_activation_min_price_volatility_delta`
- `buy_flow_activation_min_current_volume_30s`
- `buy_dead_flow_exit_min_hold_seconds`
- `buy_dead_flow_exit_max_mfe_pct`

The first group is an entry gate for candidates that otherwise pass the primary/near v95 gate. The dead-flow group is an early exit rule for positions that have been held long enough but never achieved enough MFE.

## Task 1: Flow Metric Tests

**Files:**
- Create: `tests/model/test_flow_activation_replay.py`
- Modify: `src/pipeline/train_hybrid.py`

- [ ] **Step 1: Add failing test helpers**

Add helpers matching the existing replay tests:

```python
import importlib.util
import unittest
from pathlib import Path


def _load_module():
    path = Path(__file__).resolve().parents[2] / "src" / "pipeline" / "train_hybrid.py"
    spec = importlib.util.spec_from_file_location("train_hybrid", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class _SellNonePolicy:
    def predict(self, obs, deterministic=True):
        return 0, None


def _sample(token="0xflow", sample_time=100, price=1.0, volume_30s=1.0, price_volatility=0.10, create_timestamp=80):
    return {
        "features": {
            "current_price": price,
            "holder_count": 10,
            "volume_30s": volume_30s,
            "price_volatility": price_volatility,
        },
        "meta": {
            "token_address": token,
            "sample_time": sample_time,
            "create_timestamp": create_timestamp,
        },
    }
```

- [ ] **Step 2: Add red test for passing flow activation**

```python
class TestFlowActivationReplay(unittest.TestCase):
    def test_flow_activation_gate_allows_ramping_primary_candidate(self):
        m = _load_module()
        episodes = [[
            _sample(sample_time=100, price=1.0, volume_30s=0.8, price_volatility=0.08),
            _sample(sample_time=110, price=1.0, volume_30s=2.4, price_volatility=0.14),
            _sample(sample_time=120, price=1.35, volume_30s=2.8, price_volatility=0.16),
        ]]

        result = m._run_eval_replay(
            episodes,
            None,
            0.98,
            _SellNonePolicy(),
            buy_probabilities_by_episode=[{1: 0.99}],
            entry_scores_by_episode=[{0: 36.0, 1: 46.0}],
            min_entry_score=35.0,
            min_entry_volume_30s=1.5,
            min_entry_price_volatility=0.10,
            buy_flow_activation_min_prob=0.98,
            buy_flow_activation_min_pred_return=35.0,
            buy_flow_activation_max_age_seconds=60,
            buy_flow_activation_lookback_seconds=30,
            buy_flow_activation_min_volume_ramp_ratio=2.0,
            buy_flow_activation_min_volume_ramp_delta=1.0,
            buy_flow_activation_min_pred_return_delta=5.0,
            buy_flow_activation_min_price_volatility_delta=0.04,
            buy_flow_activation_min_current_volume_30s=1.5,
            position_fraction=0.1,
            include_trade_log=True,
        )

        self.assertEqual(result["flow_activation_signal_count"], 1)
        self.assertEqual(result["flow_activation_entry_count"], 1)
        self.assertEqual(result["total_trades"], 1)
        self.assertTrue(result["trade_log"][0]["flow_activation_used"])
```

- [ ] **Step 3: Add red test for fake/dead flow rejection**

```python
    def test_flow_activation_gate_rejects_flat_volume_candidate(self):
        m = _load_module()
        episodes = [[
            _sample(sample_time=100, price=1.0, volume_30s=1.5, price_volatility=0.10),
            _sample(sample_time=110, price=1.0, volume_30s=1.6, price_volatility=0.11),
            _sample(sample_time=120, price=0.82, volume_30s=1.4, price_volatility=0.09),
        ]]

        result = m._run_eval_replay(
            episodes,
            None,
            0.98,
            _SellNonePolicy(),
            buy_probabilities_by_episode=[{1: 0.99}],
            entry_scores_by_episode=[{0: 36.0, 1: 40.0}],
            min_entry_score=35.0,
            min_entry_volume_30s=1.5,
            min_entry_price_volatility=0.10,
            buy_flow_activation_min_prob=0.98,
            buy_flow_activation_min_pred_return=35.0,
            buy_flow_activation_max_age_seconds=60,
            buy_flow_activation_lookback_seconds=30,
            buy_flow_activation_min_volume_ramp_ratio=2.0,
            buy_flow_activation_min_volume_ramp_delta=1.0,
            buy_flow_activation_min_pred_return_delta=5.0,
            buy_flow_activation_min_price_volatility_delta=0.04,
            buy_flow_activation_min_current_volume_30s=1.5,
            position_fraction=0.1,
            include_trade_log=True,
        )

        self.assertEqual(result["flow_activation_signal_count"], 1)
        self.assertEqual(result["flow_activation_entry_count"], 0)
        self.assertEqual(result["flow_activation_reject_count"], 1)
        self.assertEqual(result["total_trades"], 0)
```

- [ ] **Step 4: Run red tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m unittest tests.model.test_flow_activation_replay
```

Expected before implementation: failures because the new replay kwargs/counters are unknown.

## Task 2: Minimal Replay Implementation

**Files:**
- Modify: `src/pipeline/train_hybrid.py`
- Test: `tests/model/test_flow_activation_replay.py`

- [ ] **Step 1: Add parameter parsing and counters**

In `_run_eval_replay`, add the replay-only params to the signature after the quick-profit overlay params. Parse with existing `_optional_runtime_probability` and `_optional_nonnegative_finite` helpers. Add counters:

```python
flow_activation_signal_count = 0
flow_activation_entry_count = 0
flow_activation_reject_count = 0
dead_flow_exit_count = 0
```

- [ ] **Step 2: Add a bounded metric helper**

Create a local helper inside `_run_eval_replay`:

```python
def _flow_activation_metrics(episode, current_index, current_score):
    sample = episode[current_index]
    meta = sample.get("meta", {}) if isinstance(sample, dict) else {}
    sample_time = float(meta.get("sample_time", current_index) or current_index)
    lookback_start = sample_time - float(flow_activation_lookback_seconds)
    history = []
    for prior_index, prior_sample in enumerate(episode[:current_index]):
        prior_meta = prior_sample.get("meta", {}) if isinstance(prior_sample, dict) else {}
        prior_time = float(prior_meta.get("sample_time", prior_index) or prior_index)
        if prior_time >= lookback_start:
            history.append((prior_index, prior_time, prior_sample))
    baseline_index, _baseline_time, baseline_sample = history[0] if history else (current_index, sample_time, sample)
    current_features = sample.get("features", {}) if isinstance(sample, dict) else {}
    baseline_features = baseline_sample.get("features", {}) if isinstance(baseline_sample, dict) else {}
    current_volume = float(current_features.get("volume_30s", 0.0) or 0.0)
    baseline_volume = float(baseline_features.get("volume_30s", 0.0) or 0.0)
    current_volatility = float(current_features.get("price_volatility", 0.0) or 0.0)
    baseline_volatility = float(baseline_features.get("price_volatility", 0.0) or 0.0)
    baseline_score = entry_scores_by_episode[episode_idx].get(baseline_index) if entry_scores_by_episode else None
    return {
        "current_volume_30s": current_volume,
        "volume_ramp_ratio": None if baseline_volume <= 0.0 else current_volume / baseline_volume,
        "volume_ramp_delta": current_volume - baseline_volume,
        "price_volatility_delta": current_volatility - baseline_volatility,
        "pred_return_delta": None if baseline_score is None else float(current_score) - float(baseline_score),
        "history_count": len(history),
    }
```

Use the actual loop variable name for `episode_idx`; if the current loop does not expose it, change `for episode in episodes:` to `for episode_idx, episode in enumerate(episodes):`.

- [ ] **Step 3: Gate otherwise-qualified candidates**

When a candidate passes primary/near entry logic, increment `flow_activation_signal_count` if the flow gate is enabled and the probability/score floors are met. Reject when any required metric is missing or below its configured floor. If accepted, set `flow_activation_used=True` in the pending entry and increment `flow_activation_entry_count` when the entry fills.

- [ ] **Step 4: Add dead-flow early exit**

Track each position's max seen pnl as `mfe_pct`. If `buy_dead_flow_exit_min_hold_seconds` and `buy_dead_flow_exit_max_mfe_pct` are set, close with reason `DEAD_FLOW_TIME_EXIT` once hold time is above the floor and `mfe_pct` is less than or equal to the configured max.

- [ ] **Step 5: Return counters and config**

Add to result dict:

```python
"flow_activation_signal_count": int(flow_activation_signal_count),
"flow_activation_entry_count": int(flow_activation_entry_count),
"flow_activation_reject_count": int(flow_activation_reject_count),
"dead_flow_exit_count": int(dead_flow_exit_count),
"buy_flow_activation_min_prob": flow_activation_prob_floor,
...
"buy_dead_flow_exit_min_hold_seconds": dead_flow_exit_min_hold,
"buy_dead_flow_exit_max_mfe_pct": dead_flow_exit_max_mfe,
```

- [ ] **Step 6: Run tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m unittest tests.model.test_flow_activation_replay tests.model.test_low_volume_rescue_replay
```

Expected: all tests pass.

## Task 3: Model Replay Config Safety

**Files:**
- Modify: `src/pipeline/model_replay.py`
- Modify: `tests/model/test_model_replay.py`

- [ ] **Step 1: Add default-off config keys**

In `live_replay_config_from_manifest`, add all `buy_flow_activation_*` and `buy_dead_flow_exit_*` keys with `None` values beside the quick-profit overlay defaults.

- [ ] **Step 2: Extend test constants**

In `tests/model/test_model_replay.py`, add the new keys to the default-off replay-only key list and assert explicit overrides still pass through.

- [ ] **Step 3: Run targeted tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m unittest tests.model.test_model_replay tests.model.test_flow_activation_replay
```

Expected: all tests pass.

## Task 4: Replay Grid CLI

**Files:**
- Create: `scripts/run_flow_activation_replay.py`
- Create: `tests/model/test_flow_activation_replay_cli.py`

- [ ] **Step 1: Create CLI with protected output**

Copy the structure from `scripts/run_low_volume_rescue_replay.py`, but use:

```python
DEFAULT_MODEL_DIR = "data/models/20260519_v95_v84_selective_nearmiss_gate"
DEFAULT_OUTPUT = "data/replay_reports/flow_activation_replay_20260520_v95.json"
LIVE_INITIAL_EQUITY_BNB = 0.005093225171475348
LIVE_POSITION_CAP = 0.1
STRICT_MAX_OPEN_POSITIONS = 8
```

Refuse output paths ending in protected model artifact names.

- [ ] **Step 2: Add bounded candidate grid**

Use a focused small grid first. This keeps the live loop moving; a broader grid should be
added only after the CLI has progress output or batching.

```python
prob_floors = [0.988, 0.989]
pred_return_floors = [35.0, 40.0]
max_ages = [60.0]
lookbacks = [30.0]
volume_ramp_ratios = [1.8, 2.2]
current_volume_floors = [1.5, 2.0]
dead_flow_mfes = [0.05]
```

This is 16 candidates. Keep the default under 300, and do not run broad grids in the live
loop until replay batching/progress has been added.

- [ ] **Step 3: Acceptance gate**

Require validation and final to beat baseline on:

- net profit BNB
- max drawdown not worse
- win rate not lower
- walk-forward worst return not lower
- walk-forward worst drawdown not worse
- stress worst return/profit/drawdown not worse
- trade count not materially lower or higher
- at least one flow activation entry or at least one dead-flow exit

- [ ] **Step 4: CLI tests**

Test strict 10% sizing, protected output refusal, grid size, and final rejection when final confirmation fails by monkeypatching `run_model_replay`.

- [ ] **Step 5: Run tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m unittest tests.model.test_flow_activation_replay_cli
```

Expected: all tests pass.

## Task 5: Run Experiment and Record Decision

**Files:**
- Create: `data/replay_reports/flow_activation_replay_20260520_v95.json`
- Modify: `docs/model_scoreboard.md`

- [ ] **Step 1: Run replay grid**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 venv/bin/python scripts/run_flow_activation_replay.py --output data/replay_reports/flow_activation_replay_20260520_v95.json --force
```

- [ ] **Step 2: Parse summary**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 venv/bin/python - <<'PY'
import json
from pathlib import Path
r=json.loads(Path("data/replay_reports/flow_activation_replay_20260520_v95.json").read_text())
print("decision", r.get("decision"))
print("candidates", len(r.get("candidates") or []))
fc=r.get("final_confirmation") or {}
print("final_passes", fc.get("passes_acceptance_gate"))
print("selected", (r.get("selected_candidate") or {}).get("candidate_index"))
PY
```

- [ ] **Step 3: Scoreboard update**

If rejected, add one row under rejected candidates with report path, selected parameters, validation result, final result, and why it failed. If accepted, update accepted baseline and only then prepare live switch procedure.

## Task 6: Reviews, Verification, Commit/Push

**Files:**
- All files changed by Tasks 1-5.

- [ ] **Step 1: Run final targeted tests**

```bash
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m unittest tests.model.test_flow_activation_replay tests.model.test_flow_activation_replay_cli tests.model.test_model_replay tests.model.test_low_volume_rescue_replay
```

- [ ] **Step 2: Compile changed Python files**

```bash
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m py_compile src/pipeline/train_hybrid.py src/pipeline/model_replay.py scripts/run_flow_activation_replay.py tests/model/test_flow_activation_replay.py tests/model/test_flow_activation_replay_cli.py
```

- [ ] **Step 3: Run full tests if the targeted suite passes**

```bash
PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m unittest discover
```

- [ ] **Step 4: Two strict reviews**

Run two independent strict review passes after the final edit. The reviewers must check default-off replay-only behavior, 10% sizing, no `.env` or live bot changes, no model artifact overwrite risk, no stale manifest activation, and scoreboard/report consistency.

- [ ] **Step 5: Commit and push important node**

```bash
git status --short
git diff --cached --check
git add src/pipeline/train_hybrid.py src/pipeline/model_replay.py scripts/run_flow_activation_replay.py tests/model/test_flow_activation_replay.py tests/model/test_flow_activation_replay_cli.py docs/research/20260520-flow-activation-gate docs/superpowers/plans/2026-05-20-flow-activation-replay-gate.md docs/model_scoreboard.md
git add -f data/replay_reports/flow_activation_replay_20260520_v95.json
git commit -m "Add flow activation replay gate"
git push origin main
```

Only include the replay report if the experiment has actually run.

## Acceptance Rule

Do not switch live unless the selected candidate strictly beats the current best baseline on validation, final, walk-forward, stress replay, drawdown, win rate, and trade-count sanity while preserving 10% sizing. Latest is not best.

## Self-Review

- Spec coverage: live-first attribution, SmartSearch research, no risk increase, replay-only implementation, strict baseline comparison, two reviews, commit/push are covered.
- Placeholder scan: no `TBD`/`TODO` remains.
- Type consistency: parameter names use the `buy_flow_activation_*` / `buy_dead_flow_exit_*` prefixes consistently.
