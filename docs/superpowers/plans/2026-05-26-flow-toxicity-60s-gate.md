# Flow Toxicity 60s Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a replay-only 60s flow-toxicity abstention gate so the current round can test the strongest live-derived dead-flow signal without lowering thresholds or increasing risk.

**Architecture:** Extend the existing `flow_abstention` replay gate instead of adding a separate runtime path. The new fields are explicit 60s override keys that read decision-time `flow_*_60s` features already present in replay samples; a new focused CLI runs a bounded 60s grid and reuses the existing strict acceptance gates.

**Tech Stack:** Python 3.11, `unittest`, existing `src.pipeline.train_hybrid._run_eval_replay`, `src.pipeline.model_replay.run_model_replay`.

---

### Task 1: Runtime Replay Support

**Files:**
- Modify: `tests/model/test_flow_activation_replay.py`
- Modify: `tests/model/test_model_replay.py`
- Modify: `src/pipeline/train_hybrid.py`
- Modify: `src/pipeline/model_replay.py`

- [ ] **Step 1: Write the failing test for 60s overlap abstention**

Add this test to `tests/model/test_flow_activation_replay.py`:

```python
    def test_flow_abstention_rejects_60s_overlap_toxic_candidate(self):
        m = _load_module()
        toxic = _sample(sample_time=100, volume_30s=2.0, price_volatility=0.12)
        toxic["features"].update({
            "flow_buy_sell_overlap_ratio_60s": 0.95,
            "flow_buy_sell_ratio_60s": 0.004,
            "flow_sell_pressure_60s": 0.996,
            "flow_signed_imbalance_60s": -0.996,
        })
        episodes = [[toxic, _sample(sample_time=120, price=0.80)]]

        result = m._run_eval_replay(
            episodes,
            None,
            0.98,
            _SellNonePolicy(),
            buy_probabilities_by_episode=[{0: 0.991}],
            entry_scores_by_episode=[{0: 45.0}],
            min_entry_score=35.0,
            min_entry_volume_30s=1.5,
            min_entry_price_volatility=0.10,
            buy_flow_abstention_min_prob=0.98,
            buy_flow_abstention_max_age_seconds=60,
            buy_flow_abstention_min_entry_volume_30s=1.5,
            buy_flow_abstention_min_entry_price_volatility=0.10,
            buy_flow_abstention_min_buy_sell_overlap_ratio_60s=0.875,
            position_fraction=0.1,
            include_trade_log=True,
        )

        self.assertEqual(result["flow_abstention_veto_signal_count"], 1)
        self.assertEqual(result["flow_abstention_veto_reject_count"], 1)
        self.assertEqual(result["total_trades"], 0)
        self.assertEqual(result["trade_log"], [])
```

- [ ] **Step 2: Run the failing test**

Run:

```bash
python -m unittest tests.model.test_flow_activation_replay.TestFlowActivationReplay.test_flow_abstention_rejects_60s_overlap_toxic_candidate
```

Expected before implementation: `TypeError` or failure because `_run_eval_replay` does not accept/use `buy_flow_abstention_min_buy_sell_overlap_ratio_60s`.

- [ ] **Step 3: Write manifest/override failing coverage**

Extend `FLOW_ABSTENTION_KEYS` in `tests/model/test_model_replay.py` with:

```python
    "buy_flow_abstention_max_buy_sell_ratio_60s",
    "buy_flow_abstention_min_sell_pressure_60s",
    "buy_flow_abstention_max_signed_imbalance_60s",
    "buy_flow_abstention_min_buy_sell_overlap_ratio_60s",
```

Extend `test_live_replay_config_allows_explicit_flow_abstention_overrides` with:

```python
            "buy_flow_abstention_max_buy_sell_ratio_60s": 0.005,
            "buy_flow_abstention_min_sell_pressure_60s": 0.995,
            "buy_flow_abstention_max_signed_imbalance_60s": -0.995,
            "buy_flow_abstention_min_buy_sell_overlap_ratio_60s": 0.875,
```

- [ ] **Step 4: Run the manifest test red**

Run:

```bash
python -m unittest tests.model.test_model_replay.TestModelReplay.test_live_replay_config_allows_explicit_flow_abstention_overrides
```

Expected before implementation: failure because the new override keys are not in `live_replay_config_from_manifest`.

- [ ] **Step 5: Implement minimal runtime support**

In `src/pipeline/train_hybrid.py`, add `_run_eval_replay` parameters:

```python
    buy_flow_abstention_max_buy_sell_ratio_60s=None,
    buy_flow_abstention_min_sell_pressure_60s=None,
    buy_flow_abstention_max_signed_imbalance_60s=None,
    buy_flow_abstention_min_buy_sell_overlap_ratio_60s=None,
```

Parse them with existing validators:

```python
    flow_abstention_buy_sell_ratio_60s_ceiling = _optional_nonnegative_finite(
        buy_flow_abstention_max_buy_sell_ratio_60s,
        "buy_flow_abstention_max_buy_sell_ratio_60s",
    )
    flow_abstention_sell_pressure_60s_floor = _optional_unit_interval(
        buy_flow_abstention_min_sell_pressure_60s,
        "buy_flow_abstention_min_sell_pressure_60s",
    )
    flow_abstention_signed_imbalance_60s_ceiling = _optional_signed_unit_interval(
        buy_flow_abstention_max_signed_imbalance_60s,
        "buy_flow_abstention_max_signed_imbalance_60s",
    )
    flow_abstention_overlap_60s_floor = _optional_unit_interval(
        buy_flow_abstention_min_buy_sell_overlap_ratio_60s,
        "buy_flow_abstention_min_buy_sell_overlap_ratio_60s",
    )
```

Update `flow_abstention_enabled` so any 30s or 60s condition enables the veto. Update `_flow_abstention_veto_candidate` to OR toxic matches against:

```python
flow_buy_sell_ratio_60s <= ceiling
flow_sell_pressure_60s >= floor
flow_signed_imbalance_60s <= ceiling
flow_buy_sell_overlap_ratio_60s >= floor
```

Add these keys to `runtime_replay`, `flow_abstention_params`, `run_ab_evaluation`, stress replay forwarding, and `model_replay.live_replay_config_from_manifest` defaults.

- [ ] **Step 6: Run targeted tests green**

Run:

```bash
python -m unittest tests.model.test_flow_activation_replay.TestFlowActivationReplay.test_flow_abstention_rejects_60s_overlap_toxic_candidate
python -m unittest tests.model.test_model_replay.TestModelReplay.test_live_replay_config_excludes_manifest_flow_abstention_params tests.model.test_model_replay.TestModelReplay.test_live_replay_config_allows_explicit_flow_abstention_overrides
```

Expected: all pass.

### Task 2: Focused 60s Replay CLI

**Files:**
- Create: `scripts/run_flow_toxicity_meta_gate_replay.py`
- Create: `tests/model/test_flow_toxicity_meta_gate_replay_cli.py`

- [ ] **Step 1: Write CLI failing test**

Create `tests/model/test_flow_toxicity_meta_gate_replay_cli.py` with coverage that imports the new CLI, verifies a bounded 64-candidate grid, enforces 10% sizing and cap 8, and checks candidate params include only 60s flow-toxicity condition keys plus existing base flow-abstention floors.

- [ ] **Step 2: Run CLI test red**

Run:

```bash
python -m unittest tests.model.test_flow_toxicity_meta_gate_replay_cli
```

Expected before implementation: import/file-not-found failure.

- [ ] **Step 3: Implement CLI**

Create `scripts/run_flow_toxicity_meta_gate_replay.py`. Reuse helper functions from `scripts.run_flow_abstention_replay` and define:

```python
DEFAULT_OUTPUT = "data/replay_reports/flow_toxicity_meta_gate_replay_20260526_dead_flow_toxicity_meta_gate_round.json"
```

Candidate grid:

```python
min_probs = [0.94, 0.98]
max_ages = [60.0, 300.0]
volume_floors = [0.0, 1.5]
volatility_floors = [0.0, 0.08]
conditions = [
    {"buy_flow_abstention_min_buy_sell_overlap_ratio_60s": 0.875},
    {"buy_flow_abstention_max_buy_sell_ratio_60s": 0.005},
    {"buy_flow_abstention_min_sell_pressure_60s": 0.995},
    {"buy_flow_abstention_max_signed_imbalance_60s": -0.995},
]
```

Run validation baseline, 64 validation candidates, then final confirmation only for an accepted validation candidate. Use the same strict acceptance gate and output schema as `run_flow_abstention_replay.py`, with `live_switch_evidence=false` and `safe_for_live_switch=false`.

- [ ] **Step 4: Run CLI tests green**

Run:

```bash
python -m unittest tests.model.test_flow_toxicity_meta_gate_replay_cli
python -m unittest tests.model.test_flow_abstention_replay_cli
```

Expected: all pass.

### Task 3: Experiment Execution and Review

**Files:**
- Create: `data/replay_reports/flow_toxicity_meta_gate_replay_20260526_dead_flow_toxicity_meta_gate_round.json`
- Modify: `.ccg/tasks/live-model-optimization-20260526-dead-flow-toxicity-meta-gate-round/evidence.md`
- Modify: `docs/model_scoreboard.md` if the experiment changes future direction or rejection memory.

- [ ] **Step 1: Run strict 60s replay**

Run:

```bash
python scripts/run_flow_toxicity_meta_gate_replay.py --output data/replay_reports/flow_toxicity_meta_gate_replay_20260526_dead_flow_toxicity_meta_gate_round.json --force
```

- [ ] **Step 2: Extract decision metrics**

Run:

```bash
jq '{decision, baseline: .baseline.summary, selected_candidate: .selected_candidate, final_confirmation: .final_confirmation}' data/replay_reports/flow_toxicity_meta_gate_replay_20260526_dead_flow_toxicity_meta_gate_round.json
```

- [ ] **Step 3: Run verification**

Run:

```bash
python -m unittest tests.model.test_flow_activation_replay tests.model.test_model_replay tests.model.test_flow_toxicity_meta_gate_replay_cli
git diff --check
```

- [ ] **Step 4: Codex review pass 1**

Review the diff for data leakage, replay/live mismatch, risk expansion, missing test coverage, and protected file mistakes.

- [ ] **Step 5: Codex review pass 2**

Re-read the final diff and artifacts from scratch. Confirm `.ccg/**` remains local-only, `docs/goals/` is clean, and no live config/model switch was made.
