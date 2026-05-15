# Live Alignment And Buy Speed Follow-up Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep the live bot on `v34` until a replay-backed candidate clearly beats it, while tightening the training/live execution match and measuring the remaining buy latency hotspots.

**Architecture:** Treat the live bot as the source of execution truth and keep all model selection decisions gated by replay with live calibration. Preserve the current `v34` deployment path, use the latest `signal_audit.jsonl` and `paper_trades.jsonl` to calibrate execution cost, search only a small hold-floor grid first, and only retrain or redeploy after the replay report beats the current live-calibrated baseline.

**Tech Stack:** Python, unittest, JSONL audit logs, existing replay/search/training CLIs, tmux + `tools/memectl` for the live bot.

---

### Task 1: Keep the live execution contract aligned

**Files:**
- Modify: `src/trader/bot.py`
- Modify: `scripts/calibrate_execution_costs.py`
- Modify: `tests/core/test_hybrid_requirements_contract.py`
- Modify: `tests/model/test_calibrate_execution_costs_cli.py`

- [x] **Step 1: Record buy preflight and token-status timing on OPEN rows**

```python
# Existing live OPEN payloads now include:
# - buy_preflight_seconds
# - token_status_check_seconds
```

- [x] **Step 2: Aggregate the new timing fields in execution calibration**

```python
# scripts/calibrate_execution_costs.py now reports:
# - avg_buy_preflight_seconds
# - avg_token_status_check_seconds
```

- [x] **Step 3: Verify the contract and CLI tests**

Run:
```bash
venv/bin/python -m unittest tests.core.test_hybrid_requirements_contract tests.model.test_calibrate_execution_costs_cli
```
Expected: PASS

### Task 2: Search the hold-floor grid against live-calibrated v34

**Files:**
- Modify: `scripts/search_replay_params.py`
- Modify: `tests/model/test_search_replay_params_cli.py`
- Create: `data/replay_reports/v34_hold_search_current_speed_20260514_1339.json`

- [ ] **Step 1: Run the focused search on `v34`**

Run:
```bash
nice -n 15 venv/bin/python scripts/search_replay_params.py \
  --model-dir data/models/20260512_v34_entry_value_live \
  --lifecycle-dir data/training \
  --execution-calibration-file data/execution_calibration/live_20260514_1339_current_speed.json \
  --thresholds 0.977244973928566 \
  --stop-losses -0.25 \
  --trailing-pairs 0.2:0.15 \
  --entry-ranking-modes entry_value \
  --min-entry-scores none \
  --min-policy-holds 5,10,20,30 \
  --output data/replay_reports/v34_hold_search_current_speed_20260514_1339.json
```
Expected: one candidate should win on the validation split, then a final replay report should be written.

- [ ] **Step 2: Compare the winner with the current live-calibrated baseline**

Check:
```bash
python - <<'PY'
import json, pathlib
report = json.loads(pathlib.Path('data/replay_reports/v34_hold_search_current_speed_20260514_1339.json').read_text())
print(report['selected_candidate']['overrides'])
print(report['final_report']['evaluation']['net_return_pct'])
print(report['final_report']['evaluation']['walk_forward_worst_net_return_pct'])
PY
```
Expected: only keep a candidate if it beats the current v34 live-calibrated final on return and does not worsen walk-forward stability.

- [ ] **Step 3: Keep or reject the hold-floor change**

If the winner is worse than the current live-calibrated `v34`, keep `min_policy_hold_seconds = 5` live and stop there. If it wins, capture the exact override values for the next training run.

### Task 3: Retrain only after replay proves a better candidate

**Files:**
- Modify: `scripts/run_hybrid_training.py`
- Modify: `src/pipeline/train_hybrid.py`
- Modify: `tests/model/test_run_hybrid_training_cli.py`
- Modify: `tests/model/test_train_hybrid_pipeline.py`

- [ ] **Step 1: Launch a new training run only with the winning replay overrides**

Run:
```bash
venv/bin/python scripts/run_hybrid_training.py \
  --lifecycle-dir data/training \
  --output-dir data/models \
  --execution-calibration-file data/execution_calibration/live_20260514_1339_current_speed.json
```

- [ ] **Step 2: Compare the new model against `v34` using the same calibration file**

Run:
```bash
venv/bin/python scripts/replay_model.py \
  --model-dir <new_model_dir> \
  --lifecycle-dir data/training \
  --split final \
  --execution-calibration-file data/execution_calibration/live_20260514_1339_current_speed.json
```
Expected: the new model must beat `v34` on calibrated final return and stay acceptable on walk-forward worst segment.

- [ ] **Step 3: Reject any candidate that is more conservative without better replay**

If the candidate still underperforms, discard it and keep using `v34`.

### Task 4: Deploy only after evidence, under tmux

**Files:**
- Modify: `tools/memectl` only if the restart flow needs tightening
- Modify: `.env.example` only if a new live model path becomes the default

- [ ] **Step 1: Update the live model pointer only after replay wins**

Use the winning model directory, then restart the bot under `tmux` and verify:
```bash
./tools/memectl bot status
```

- [ ] **Step 2: Confirm the post-restart bot still reports zero errors and no stale positions**

Check:
```bash
./tools/memectl bot status
python - <<'PY'
import json, pathlib
state = json.loads(pathlib.Path('data/bot_state.json').read_text())
print(len(state.get('positions') or {}))
PY
```
Expected: bot is running, positions are empty before any deployment cutover, and the log stays clean.
