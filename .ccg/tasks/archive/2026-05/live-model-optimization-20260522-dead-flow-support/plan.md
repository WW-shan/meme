# Dead-Flow Support Probe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only support probe that determines whether the live `dead_flow_timeout` bucket has replay-equivalent support before any replay or live rule change.

**Architecture:** Add a small probe module that classifies frozen replay candidate rows and live attribution rows with one shared shape definition. Add a CLI that emits split reports plus a combined support report. Extend the existing conditional-exit feasibility report to consume the dead-flow reports when present.

**Tech Stack:** Plain Python, JSON reports, `unittest`, existing replay reports and live attribution artifacts.

---

### Task 1: Core Probe

**Files:**
- Create: `src/pipeline/dead_flow_timeout_probe.py`
- Test: `tests/model/test_dead_flow_timeout_probe.py`

- [x] Write failing tests for classification, support counts, live recall, and JSON serialization.
- [x] Implement the minimal shared classifier and support report.
- [x] Run `venv/bin/python -m unittest tests.model.test_dead_flow_timeout_probe`.

### Task 2: CLI

**Files:**
- Create: `scripts/probe_dead_flow_timeout_support.py`
- Test: `tests/model/test_dead_flow_timeout_probe_cli.py`

- [x] Write failing tests for CLI defaults, output writing, and protected output paths.
- [x] Implement the CLI without touching model artifacts or live config.
- [x] Run `venv/bin/python -m unittest tests.model.test_dead_flow_timeout_probe_cli`.

### Task 3: Feasibility Integration

**Files:**
- Modify: `src/pipeline/conditional_exit_feasibility_probe.py`
- Modify: `scripts/probe_conditional_exit_feasibility.py`
- Test: `tests/model/test_conditional_exit_feasibility_probe.py`
- Test: `tests/model/test_conditional_exit_feasibility_probe_cli.py`

- [x] Extend the feasibility report to fill the `dead_flow_timeout` row from optional dead-flow reports.
- [x] Keep `NO_GO_FOR_LIVE_RULE` unless all support gates and live recall pass.
- [x] Run focused probe tests.

### Task 4: Evidence And Review

**Files:**
- Create/update: `docs/research/20260521-conditional-exit-flow-state/dead-flow-*`
- Modify: `.ccg/tasks/live-model-optimization-20260522-dead-flow-support/review.md`
- Modify: `.ccg/tasks/live-model-optimization-20260522-dead-flow-support/task.json`

- [x] Generate read-only reports.
- [x] Run full project verification with `venv/bin/python -m unittest discover -q`.
- [x] Confirm `docs/goals/` is untouched.
- [x] Run Codex local review plus external Claude review.
