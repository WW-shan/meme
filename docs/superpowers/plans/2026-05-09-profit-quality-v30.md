# Profit Quality V30 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix replay accounting, add entry funnel metrics, and train a corrected v30 run tuned toward roughly 1% entry coverage.

**Architecture:** Keep all behavior in the existing `src/pipeline/train_hybrid.py` replay and tuning path. Keep `scripts/run_hybrid_training.py` as a thin CLI adapter for the new `risk_tune_min_entry_rate` config. Use unittest coverage for every behavior change before production edits.

**Tech Stack:** Python 3.12, `unittest`, CatBoost buy model, Stable-Baselines PPO sell policy, existing hybrid training CLI.

---

## File Map

- Modify `tests/model/test_train_hybrid_pipeline.py`: regression tests for replay-end accounting, funnel metrics, and min entry-rate feasibility.
- Modify `src/pipeline/train_hybrid.py`: fix replay-end liquidation, emit funnel metrics, enforce `risk_tune_min_entry_rate`.
- Modify `tests/model/test_run_hybrid_training_cli.py`: CLI parsing/config tests for `--risk-tune-min-entry-rate`.
- Modify `scripts/run_hybrid_training.py`: expose `--risk-tune-min-entry-rate`.
- Output `data/models/20260509_profit_quality_v30/`: corrected v30 model artifacts and manifest.

## Task 1: Replay-End Accounting Fix

- [ ] Add `test_run_eval_replay_replay_end_liquidation_does_not_double_count_open_position` in `tests/model/test_train_hybrid_pipeline.py`.
- [ ] Run the single test and confirm it fails with final equity 1.1 instead of 1.0.
- [ ] Fix `src/pipeline/train_hybrid.py` so replay-end liquidation removes closed positions before appending final equity.
- [ ] Run the single test and the full pipeline test file.
- [ ] Commit with `Fix replay end liquidation accounting`.

## Task 2: Entry Funnel Metrics

- [ ] Add tests proving `_run_eval_replay` reports `entry_signal_count`, `entry_attempt_count`, `entry_fill_rate`, and skip rates.
- [ ] Run the new tests and confirm the metrics are missing or wrong.
- [ ] Add counters and derived rates in `_run_eval_replay`.
- [ ] Propagate metrics through `run_ab_evaluation` top-level output.
- [ ] Run pipeline tests.
- [ ] Commit with `Add replay entry funnel metrics`.

## Task 3: Risk Tune Minimum Entry Rate CLI

- [ ] Add CLI tests for `--risk-tune-min-entry-rate` default `None` and explicit config propagation.
- [ ] Run CLI tests and confirm failure.
- [ ] Add parser/config support in `scripts/run_hybrid_training.py`.
- [ ] Add tuning feasibility enforcement in `_tune_buy_threshold_by_replay` and include it in constraints.
- [ ] Run CLI and pipeline tests.
- [ ] Commit with `Tune buy threshold with minimum entry rate`.

## Task 4: Verification, Review, and V30 Training

- [ ] Run `venv/bin/python -m unittest discover`.
- [ ] Run `git diff --check`.
- [ ] Run v30 training with corrected replay and 1% entry-rate target.
- [ ] Parse `data/models/20260509_profit_quality_v30/hybrid_manifest.json` for validation/final/stress/funnel metrics.
- [ ] Perform code review before the final report.
- [ ] Report final status and next optimization recommendation.
