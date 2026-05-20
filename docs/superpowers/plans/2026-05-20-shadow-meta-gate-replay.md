# Shadow Meta Gate Replay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the positive shadow PredReturn-disagreement ranker probe into a default-off, replay-only meta-gate experiment that can prove or reject whether rescued high-probability/low-PredReturn candidates improve strict live-sized v95 replay.

**Architecture:** Keep live runtime unchanged. Train the candidate ranker offline from existing v95 candidate rows, map its predictions back into replay sample indices, and allow score-rejected primary candidates only when both hard safety guards and the learned shadow score pass. Evaluate validation first, then final confirmation against the current v95 strict baseline at 10% sizing.

**Tech Stack:** Python `unittest`, existing `src.pipeline.train_hybrid._run_eval_replay`, `src.pipeline.candidate_ranker_probe`, CatBoost ranker wrapper, `scripts/run_*_replay.py` report pattern.

---

## Live-First Evidence

- Current live model: `data/models/20260519_v95_v84_selective_nearmiss_gate`.
- Current risk: `POSITION_SIZE=0.10`, `FIXED_STAKE_BNB=`; no position-size expansion is allowed.
- Current state: bot and collector are running under `memectl`/tmux; `data/bot_state.json` has zero open positions and balance `0.005093225171475348`.
- No new real trades after `2026-05-19 19:16:00` (`赵长娥`, profitable PPO close).
- Fresh time-to-barrier probe since that close: `data/replay_reports/time_to_barrier_probe_20260520_live_cycle_latest.json`.
  - `per_token_candidates=229`
  - `quick_take_profit=43`
  - `conditional_slow_hold=3`
  - `skip=183`
  - classes: `fast_profit=16`, `fast_profit_then_collapse=27`, `slow_runner=3`, `stop_first=37`, `flat_timeout=146`
- Trigger class: high primary probability candidates rejected by the PredReturn/entry-value gate. `SZN` is the clean missed runner, but `交易鸭`, `cwh`, and similar candidates prove the bucket is mixed.

## Research Reuse

Reuse `docs/research/20260520-highprob-predreturn-disagreement/summary.md`.

The reused research supports meta-labeling, triple-barrier path labels, selective classification/reject-option framing, and cost-sensitive override gates. This experiment is the replay-integration step explicitly called for by that research; no live switch is allowed from the probe alone.

## Hypothesis

Because live evidence shows the high-probability / low-PredReturn bucket contains both rare runners and many collapses, a learned shadow meta-ranker can rescue only the runner-like score rejects while preserving v95's abstention behavior. This is structurally different from global threshold lowering, static primary-score rescue, low-volume rescue, and quick-profit overlay because the decision depends on a learned candidate-level score and remains default-off/replay-only.

## Falsification Rule

Reject the direction if validation or final replay fails to beat the v95 baseline on strict live-sized metrics: net profit, win rate, max drawdown, walk-forward worst return/drawdown, stress replay, and trade-count discipline. Also reject if the shadow gate records zero shadow entries, expands trade count materially, or relies on 10% risk-policy violations.

## File Responsibilities

- Modify `src/pipeline/train_hybrid.py`: add default-off shadow meta-gate parameters, replay counters, trade-log flags, and optional `shadow_scores_by_episode`.
- Create `tests/model/test_shadow_meta_gate_replay.py`: direct unit tests for `_run_eval_replay` behavior with synthetic episodes and shadow scores.
- Create `scripts/run_shadow_meta_gate_replay.py`: strict 10% validation/final grid that trains the ranker, maps shadow scores into replay, runs `run_model_replay`, and writes a report.
- Create `tests/model/test_shadow_meta_gate_replay_cli.py`: CLI/risk/report contract tests with a mocked `run_model_replay`.
- Update `docs/model_scoreboard.md`: only after running the real report, record accept/reject and why.
- Do not modify `docs/goals/live-model-optimization-goal.md`.
- Do not modify live `.env`, `.env.example`, `config/`, `src/trader/`, or `data/models` unless a later accepted candidate passes live switch gates.

## Task 1: Replay Hook

**Files:**
- Modify: `src/pipeline/train_hybrid.py`
- Test: `tests/model/test_shadow_meta_gate_replay.py`

- [ ] **Step 1: Write failing test for default-off behavior**

Create `tests/model/test_shadow_meta_gate_replay.py` with a test that builds a one-token episode where buy probability passes v95 primary threshold but `entry_score` is below `min_entry_score`. Call `_run_eval_replay` with `shadow_scores_by_episode` present but no `buy_shadow_meta_gate_min_score`. Assert `total_trades == 0`, `shadow_meta_gate_signal_count == 0`, and `entry_score_reject_count == 1`.

- [ ] **Step 2: Write failing test for learned rescue**

In the same file, add a test that enables:

```python
buy_shadow_meta_gate_min_prob=0.988
buy_shadow_meta_gate_max_entry_score=10.0
buy_shadow_meta_gate_min_entry_volume_30s=2.0
buy_shadow_meta_gate_min_entry_price_volatility=0.20
buy_shadow_meta_gate_max_age_seconds=60.0
buy_shadow_meta_gate_min_score=0.50
shadow_scores_by_episode=[{0: 0.75}]
```

Use an episode whose first sample has `buy_prob=0.989`, `entry_score=-4.5`, `volume_30s=3.2`, `price_volatility=0.27`, `token_age_seconds=9`, and a later sample above the entry price. Assert one entry/trade, `shadow_meta_gate_signal_count == 1`, `shadow_meta_gate_entry_count == 1`, `entry_score_reject_count == 0`, and the trade log marks `shadow_meta_gate_used=True`.

- [ ] **Step 3: Write failing guard tests**

Add parameterized-style subtests showing the gate rejects when probability is below floor, entry score is above the shadow maximum, volume is below floor, volatility is below floor, age is above max, or shadow score is below floor. Assert `shadow_meta_gate_reject_count == 1` and no trade.

- [ ] **Step 4: Run red tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_shadow_meta_gate_replay
```

Expected: fail because `_run_eval_replay` has no shadow meta-gate parameters/counters yet.

- [ ] **Step 5: Implement minimal replay hook**

Add `_optional_runtime_probability` / `_optional_nonnegative_finite` initialization for:

```python
buy_shadow_meta_gate_min_prob
buy_shadow_meta_gate_max_entry_score
buy_shadow_meta_gate_min_entry_volume_30s
buy_shadow_meta_gate_min_entry_price_volatility
buy_shadow_meta_gate_max_age_seconds
buy_shadow_meta_gate_min_score
```

Add optional `_run_eval_replay(..., shadow_scores_by_episode=None, ...)`.

Only consider the shadow gate for primary candidates where:

- `buy_prob >= threshold`
- normal entry quality passes
- normal entry score fails
- hard shadow guards pass
- `shadow_scores_by_episode[episode_index][idx] >= buy_shadow_meta_gate_min_score`

Set `shadow_meta_gate_used=True` on pending/immediate entries and increment signal/entry/reject counters.

- [ ] **Step 6: Run green tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_shadow_meta_gate_replay
```

Expected: pass.

## Task 2: Replay CLI

**Files:**
- Create: `scripts/run_shadow_meta_gate_replay.py`
- Test: `tests/model/test_shadow_meta_gate_replay_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Add tests that import the script and verify:

- default model dir is `data/models/20260519_v95_v84_selective_nearmiss_gate`
- default output is `data/replay_reports/shadow_meta_gate_replay_20260520_v95.json`
- `--position-fraction`, `--max-position-fraction`, and `--max-open-positions` reject anything except `0.1`, `0.1`, and `8`
- output path refuses protected model artifact names inside the model dir
- mocked `run_model_replay` sees strict overrides: `position_fraction=0.1`, `max_position_fraction=0.1`, `fixed_stake_bnb=None`, `skip_all_in_replay=True`, `max_open_positions=8`

- [ ] **Step 2: Write failing validation/final selection test**

Mock `run_model_replay` so validation has one accepted candidate and one higher-profit but risk-worse candidate. Assert the script selects the accepted validation candidate, runs final only for baseline plus selected candidate, and emits `decision="accept"` only if final passes every gate and `shadow_meta_gate_entry_count > 0`.

- [ ] **Step 3: Implement CLI**

Follow the `scripts/run_primary_score_scalp_replay.py` pattern:

- strict risk arg parsers
- `_base_overrides`
- `_summary`
- `_gate_details`
- `_passes_gate`
- `_assert_output_writable`
- validation baseline run
- validation grid
- selected validation candidate
- final baseline plus final candidate confirmation
- `live_switch_evidence=False`

The grid should start small:

```python
min_scores = [0.35, 0.50, 0.65]
min_probs = [0.988, 0.989]
max_entry_scores = [5.0, 10.0]
volume_floors = [2.0, 3.0]
volatility_floors = [0.20, 0.25]
max_ages = [60.0]
```

Each candidate override must include the hard guards and `buy_shadow_meta_gate_min_score`.

- [ ] **Step 4: Run CLI unit tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_shadow_meta_gate_replay_cli
```

Expected: pass.

## Task 3: Shadow Score Mapping

**Files:**
- Modify: `src/pipeline/candidate_ranker_probe.py`
- Modify or create helper imports in `scripts/run_shadow_meta_gate_replay.py`
- Test: `tests/model/test_candidate_ranker_probe.py`

- [ ] **Step 1: Write failing tests for score map output**

Add tests proving a helper can train/predict shadow ranker scores and return a per-episode index map shaped like:

```python
[
    {0: 0.75, 3: -0.10},
    {2: 0.42},
]
```

The helper must preserve original sample indices and return scores only for candidates that pass the shadow universe guard.

- [ ] **Step 2: Implement helper**

Add a focused helper, for example:

```python
fit_shadow_ranker_and_score_episodes(train_samples, eval_episodes, buy_artifact, runtime_params, group_bucket_seconds=30)
```

It should reuse existing candidate-row filtering, `_train_ranker`, and `_predict_ranker`, but must not alter live artifacts.

- [ ] **Step 3: Connect CLI to helper**

In `run_shadow_meta_gate_replay.py`, train on the train split and pass `shadow_scores_by_episode` through `run_model_replay` via overrides or an explicit replay hook, depending on the existing `run_model_replay` API. If `run_model_replay` cannot accept non-JSON score maps in overrides cleanly, add a default-off keyword path to `run_model_replay` rather than serializing maps into manifests.

- [ ] **Step 4: Run relevant tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_candidate_ranker_probe tests.model.test_shadow_meta_gate_replay tests.model.test_shadow_meta_gate_replay_cli
```

Expected: pass.

## Task 4: Real Replay and Decision

**Files:**
- Create or update: `data/replay_reports/shadow_meta_gate_replay_20260520_v95.json`
- Update: `docs/model_scoreboard.md`

- [ ] **Step 1: Run strict replay**

Run:

```bash
venv/bin/python scripts/run_shadow_meta_gate_replay.py \
  --model-dir data/models/20260519_v95_v84_selective_nearmiss_gate \
  --lifecycle-dir data/training \
  --output data/replay_reports/shadow_meta_gate_replay_20260520_v95.json \
  --position-fraction 0.1 \
  --max-position-fraction 0.1 \
  --max-open-positions 8 \
  --force
```

- [ ] **Step 2: Inspect report**

Confirm:

- `live_switch_evidence` is `false`
- strict assumptions have 10% sizing and no fixed stake
- validation baseline/candidate/final confirmation are present
- accepted candidate, if any, has `shadow_meta_gate_entry_count > 0`
- final candidate beats baseline on all gate details

- [ ] **Step 3: Update scoreboard**

Add one concise row to `docs/model_scoreboard.md`.

- If rejected: record the exact failed gates and say do not switch live.
- If accepted: record that it is still replay-only until live-switch procedure runs; do not edit `.env` in this task.

## Task 5: Verification, Reviews, Commit

**Files:**
- All modified files from Tasks 1-4

- [ ] **Step 1: Run verification**

Run:

```bash
venv/bin/python -m unittest tests.model.test_candidate_ranker_probe tests.model.test_shadow_meta_gate_replay tests.model.test_shadow_meta_gate_replay_cli
venv/bin/python -m py_compile src/pipeline/train_hybrid.py src/pipeline/candidate_ranker_probe.py scripts/run_shadow_meta_gate_replay.py
python -m json.tool data/replay_reports/time_to_barrier_probe_20260520_live_cycle_latest.json >/dev/null
python -m json.tool data/replay_reports/shadow_meta_gate_replay_20260520_v95.json >/dev/null
git diff --check
git status --short --untracked-files=all -- docs/goals
git diff -- docs/goals/
git diff --cached -- docs/goals/
```

- [ ] **Step 2: Strict review pass 1**

Review the final diff for correctness, default-off behavior, live-risk safety, leakage risk, replay metric validity, and goal-doc immutability.

- [ ] **Step 3: Strict review pass 2**

Repeat review after pass 1 is clean. If any code changes after review, reset the two-review count.

- [ ] **Step 4: Commit and push**

Only if verification and both reviews are clean:

```bash
git add src/pipeline/train_hybrid.py src/pipeline/candidate_ranker_probe.py scripts/run_shadow_meta_gate_replay.py tests/model/test_shadow_meta_gate_replay.py tests/model/test_shadow_meta_gate_replay_cli.py tests/model/test_candidate_ranker_probe.py docs/superpowers/plans/2026-05-20-shadow-meta-gate-replay.md docs/model_scoreboard.md
git add -f data/replay_reports/time_to_barrier_probe_20260520_live_cycle_latest.json data/replay_reports/shadow_meta_gate_replay_20260520_v95.json
git commit -m "Add shadow meta gate replay experiment"
git push
```

## Self-Review

- Spec coverage: covers live-first trigger, research reuse, default-off replay hook, strict 10% risk, validation/final gate, scoreboard, two reviews, commit/push, and no goal-doc edits.
- Placeholder scan: no placeholders remain; all tasks include concrete files and commands.
- Type consistency: use `shadow_scores_by_episode` for replay score maps and `buy_shadow_meta_gate_*` for default-off runtime params.
