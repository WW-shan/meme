# Live Consistency Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align live bot behavior, replay controls, and training reports so the selected model can be replayed and executed with the same entry filters, ranking, and execution assumptions.

**Architecture:** Keep the live bot as the runtime owner, add audit-only logging for signal decisions and fills, make entry price protection and entry ranking configurable from the model manifest, and let training emit replay summaries that can be fed back into future runs. Reuse existing feature extraction and replay code paths instead of introducing parallel logic.

**Tech Stack:** Python, unittest, JSONL audit logs, existing training/replay CLI surfaces.

---

### Task 1: Signal audit logging

**Files:**
- Modify: `src/trader/bot.py`
- Modify: `tests/core/test_hybrid_requirements_contract.py`

- [x] **Step 1: Write the failing test**
- [x] **Step 2: Run test to verify it fails**
- [x] **Step 3: Write minimal implementation**
- [x] **Step 4: Run test to verify it passes**
### Task 2: Entry price protection

**Files:**
- Modify: `src/trader/bot.py`
- Modify: `tests/core/test_hybrid_requirements_contract.py`

- [x] **Step 1: Write the failing test**
- [x] **Step 2: Run test to verify it fails**
- [x] **Step 3: Write minimal implementation**
- [x] **Step 4: Run test to verify it passes**

### Task 3: Execution calibration report

**Files:**
- Create: `scripts/calibrate_execution_costs.py`
- Modify: `scripts/run_hybrid_training.py`
- Modify: `tests/model/test_calibrate_execution_costs_cli.py`
- Modify: `tests/model/test_run_hybrid_training_cli.py`

- [x] **Step 1: Write the failing test**
- [x] **Step 2: Run test to verify it fails**
- [x] **Step 3: Write minimal implementation**
- [x] **Step 4: Run test to verify it passes**

### Task 4: Rolling validation summary

**Files:**
- Modify: `src/pipeline/train_hybrid.py`
- Modify: `tests/model/test_train_hybrid_pipeline.py`

- [x] **Step 1: Write the failing test**
- [x] **Step 2: Run test to verify it fails**
- [x] **Step 3: Write minimal implementation**
- [x] **Step 4: Run test to verify it passes**

### Task 5: Feature consistency contract

**Files:**
- Create: `tests/model/test_feature_consistency_contract.py`

- [x] **Step 1: Write the failing test**
- [x] **Step 2: Run test to verify it fails**
- [x] **Step 3: Write minimal implementation**
- [x] **Step 4: Run test to verify it passes**
