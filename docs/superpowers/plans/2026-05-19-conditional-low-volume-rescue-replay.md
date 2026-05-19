# Conditional Low-Volume Rescue Replay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a replay-only experiment gate that tests whether high-probability low-volume candidates can be rescued with bounded risk and a conditional quick-take-profit exit, without changing live bot behavior or increasing 10% position sizing.

**Architecture:** Keep v95/v84 as the primary signal generator. Extend `src/pipeline/train_hybrid.py` replay configuration with a `buy_low_volume_rescue_*` entry gate that only runs when the normal primary signal failed the quality gate, then tag rescued positions and optionally apply a full quick-take-profit exit only to those positions. Use `scripts/run_low_volume_rescue_replay.py` as the reproducible experiment runner so the live bot stays untouched.

**Tech Stack:** Python 3.12, existing `unittest` suite, `src.pipeline.model_replay.run_model_replay`, CatBoost model artifacts already present in `data/models/20260519_v95_v84_selective_nearmiss_gate`, JSON replay reports under `data/replay_reports/`.

---

## Live Trigger And Hypothesis

Live state at plan creation:

- Bot and collector are running under `./tools/memectl` and tmux.
- `.env` uses `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, and `MIN_ENTRY_VOLUME_30S=1.5`.
- `data/bot_state.json` has balance `0.005079303120051795` and `0` open positions.
- No new real `OPEN`/`CLOSE` exists after WAGMI.
- Latest probe artifacts:
  - `data/replay_reports/time_to_barrier_probe_20260519_v95_latest.json`
  - `data/replay_reports/low_volume_breakout_probe_20260519_v95_latest.json`

Live attribution:

- `low_volume_breakout_probe_20260519_v95_latest.json` has `21` per-token candidates: `5` low-volume runners, `3` low-volume fast-profit-then-stop, `7` low-volume fakeouts, `3` low-volume flat, and `3` missing path.
- Clean or profitable-before-stop examples: `A9自由`, `微信时刻`, `1Binance`, `Cheburashka`, `HERMANO`, plus quick-profit examples `AIOA`, `520`, `INTRUSO`.
- Fakeout examples: `MATRIX-3`, `PI-402 协议`, `币安社区`, `尼罗基金会`, `4lpha`, `Agora-1`.
- `BFC` confirms another missed runner mode, but it was mostly a low `PredReturn` / low `price_volatility` case rather than pure low-volume; this plan should not broaden to all low-PredReturn candidates.

Hypothesis:

Because live rejected signals show a mixed but material low-volume high-probability pocket, try a replay-only `buy_low_volume_rescue_*` gate with optional quick-take-profit for rescued positions, expecting to capture `+25%` spikes while preserving v95's normal primary and near-threshold gates. Reject if validation/final/walk-forward/stress do not beat the current best v95 baseline or if drawdown/trade count expands materially.

Prior rejected directions to avoid:

- Global threshold lowering.
- Global volume relaxation.
- Raw runner-probability gate.
- Token balancing alone.
- Blanket partial exits.
- Simply holding all positions longer.

Research artifact:

- `docs/research/20260519-conditional-low-volume-rescue/summary.md`

Acceptance gate:

- 10% sizing remains unchanged.
- Compare against current best v95 baseline, not just latest code.
- Candidate must improve net profit or return while not materially worsening max drawdown, walk-forward worst return/drawdown, stress replay, trade count, and win rate.
- Any live switch is out of scope for this plan unless a separate accepted-model/live-switch node is run.

Review gate:

- After the final edit in this plan node, run two strict review passes.
- Review pass 1: parent review of diff, tests, report artifacts, and live-risk boundary.
- Review pass 2: independent subagent review focused on bugs, replay/live mismatch, data leakage, missing tests, missing artifacts, and pull-and-run readiness.
- If either review causes a material edit, rerun both reviews after the last edit.

## Files

- Modify: `src/pipeline/train_hybrid.py`
  - Add replay-only low-volume rescue parameters, metrics, position flags, and conditional quick-take-profit exit.
- Create: `scripts/run_low_volume_rescue_replay.py`
  - Run a bounded parameter grid against v95 using strict live-sized replay assumptions and save a report.
- Create: `tests/model/test_low_volume_rescue_replay.py`
  - Unit tests for replay entry rescue, quality boundaries, quick-take-profit, and metric reporting.
- Create: `tests/model/test_low_volume_rescue_replay_cli.py`
  - CLI/report contract tests for the experiment runner.
- Modify: `docs/model_scoreboard.md`
  - Record accept/reject result after the report is generated.
- Keep unchanged: `.env`, `.env.example`, `src/trader/bot.py`, `config/trading_config.py`
  - This is replay-only unless a later accepted live-switch node is explicitly run.

## Subagent Ownership

- Worker A owns `tests/model/test_low_volume_rescue_replay.py` and the minimal `src/pipeline/train_hybrid.py` replay changes.
- Worker B owns `scripts/run_low_volume_rescue_replay.py` and `tests/model/test_low_volume_rescue_replay_cli.py`.
- Parent owns live monitoring, integration, final replay command, scoreboard update, reviews, commit, and push.

## Task 1: Replay Low-Volume Rescue Gate

**Files:**
- Modify: `src/pipeline/train_hybrid.py`
- Create: `tests/model/test_low_volume_rescue_replay.py`

- [ ] **Step 1: Add failing tests for rescue entry and metrics**

Add tests that call `_run_eval_replay` with tiny synthetic episodes and explicit buy probabilities. The first test must prove that a primary signal rejected by `min_entry_volume_30s=1.5` can enter only when these params are set:

```python
buy_low_volume_rescue_min_prob=0.98
buy_low_volume_rescue_min_entry_volume_30s=0.75
buy_low_volume_rescue_max_entry_volume_30s=1.5
buy_low_volume_rescue_min_entry_price_volatility=0.05
buy_low_volume_rescue_max_age_seconds=60
```

The expected failing assertions before implementation:

```python
self.assertEqual(result["low_volume_rescue_signal_count"], 1)
self.assertEqual(result["low_volume_rescue_entry_count"], 1)
self.assertEqual(result["entry_quality_reject_count"], 0)
self.assertTrue(result["trade_log"][0]["low_volume_rescue_used"])
```

- [ ] **Step 2: Run red test**

Run:

```bash
venv/bin/python -m unittest tests.model.test_low_volume_rescue_replay
```

Expected: fail because `_run_eval_replay` does not accept or report `buy_low_volume_rescue_*`.

- [ ] **Step 3: Implement minimal replay entry gate**

In `_run_eval_replay`, add parameters:

```python
buy_low_volume_rescue_min_prob=None
buy_low_volume_rescue_min_entry_volume_30s=None
buy_low_volume_rescue_max_entry_volume_30s=None
buy_low_volume_rescue_min_entry_price_volatility=None
buy_low_volume_rescue_max_age_seconds=None
buy_low_volume_rescue_take_profit_pct=None
```

Add helper logic that is enabled only when `buy_low_volume_rescue_min_prob` is not `None`. A candidate may be rescued only when:

- `buy_prob >= threshold`;
- normal entry score passes;
- normal quality filter would reject;
- `prob >= buy_low_volume_rescue_min_prob`;
- `volume_30s` is finite and within `[min_entry_volume_30s, max_entry_volume_30s]`;
- `price_volatility` is finite and at least the rescue floor;
- token age is finite, not negative, and no more than the rescue max age.

Track:

```python
low_volume_rescue_signal_count
low_volume_rescue_entry_count
low_volume_rescue_reject_count
```

Set `low_volume_rescue_used=True` on pending/opened positions and include the flag in trade log rows.

- [ ] **Step 4: Run green test**

Run:

```bash
venv/bin/python -m unittest tests.model.test_low_volume_rescue_replay
```

Expected: pass.

- [ ] **Step 5: Add failing tests for boundaries**

Add tests proving the rescue does not fire for:

- probability below the rescue floor;
- volume below rescue min;
- volume above rescue max;
- price volatility below rescue min;
- missing/NaN age;
- age above max;
- score below `min_entry_score`.

Run the test and verify it fails until all boundary checks are implemented.

- [ ] **Step 6: Implement boundary checks and config echo**

Return the configured rescue params in replay results:

```python
"buy_low_volume_rescue_min_prob": ...
"buy_low_volume_rescue_min_entry_volume_30s": ...
"buy_low_volume_rescue_max_entry_volume_30s": ...
"buy_low_volume_rescue_min_entry_price_volatility": ...
"buy_low_volume_rescue_max_age_seconds": ...
"buy_low_volume_rescue_take_profit_pct": ...
```

- [ ] **Step 7: Add failing test for rescued quick-take-profit**

Add a synthetic path where the rescued position reaches `+25%`, later hits `-18%`, and `buy_low_volume_rescue_take_profit_pct=0.25`. Expected:

```python
self.assertEqual(result["trade_log"][0]["exit_reason"], "LOW_VOLUME_TAKE_PROFIT")
self.assertGreater(result["trade_log"][0]["return_pct"], 0.0)
```

- [ ] **Step 8: Implement rescue-only quick-take-profit exit**

Before the normal `STOP_LOSS`, `TIME_EXIT`, trailing, and PPO policy checks, if the position has `low_volume_rescue_used` and `pnl_pct >= buy_low_volume_rescue_take_profit_pct`, exit the full position with reason `LOW_VOLUME_TAKE_PROFIT`.

- [ ] **Step 9: Run focused tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_low_volume_rescue_replay
```

Expected: OK.

## Task 2: Propagate Config And Add CLI Runner

**Files:**
- Modify: `src/pipeline/train_hybrid.py`
- Create: `scripts/run_low_volume_rescue_replay.py`
- Create: `tests/model/test_low_volume_rescue_replay_cli.py`

- [ ] **Step 1: Add failing propagation test**

Add a test proving `run_ab_evaluation` forwards `buy_low_volume_rescue_*` params to runtime, all-in, stress, and walk-forward replay by asserting they appear in the returned evaluation/config summaries.

- [ ] **Step 2: Implement propagation**

Add a `low_volume_rescue_params` dict next to `near_threshold_params` and `primary_score_rescue_params`, pass it to every `_run_eval_replay` call, and include the metrics in the final evaluation summary.

- [ ] **Step 3: Add CLI contract test**

Create `tests/model/test_low_volume_rescue_replay_cli.py` covering:

- `--model-dir` default is `data/models/20260519_v95_v84_selective_nearmiss_gate`;
- `--position-fraction` default is `0.1`;
- output contains `baseline`, `candidates`, `best_candidate`, `decision`, and `acceptance_gate`;
- the script refuses `--position-fraction` greater than `0.1`.

- [ ] **Step 4: Implement CLI**

Create `scripts/run_low_volume_rescue_replay.py` with a small deterministic grid:

```python
prob_floors = [0.982, 0.985]
volume_mins = [0.75, 0.95, 1.15]
volume_maxes = [1.5]
volatility_floors = [0.05, 0.08, 0.10]
max_ages = [60, 120]
take_profits = [0.25, 0.35]
```

For each candidate, call `run_model_replay` with strict live-sized assumptions copied from the current v95 baseline report and overrides:

```python
initial_equity_bnb=0.005079303120051795
position_fraction=0.1
max_position_fraction=0.1
fixed_stake_bnb=None
max_open_positions=8
skip_all_in_replay=True
```

The script must save the full report to:

```text
data/replay_reports/low_volume_rescue_replay_20260519_v95.json
```

It must mark `decision="reject"` unless a candidate beats current v95 baseline on the acceptance gates.

- [ ] **Step 5: Run CLI tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_low_volume_rescue_replay_cli
```

Expected: OK.

## Task 3: Replay, Scoreboard, Review, Commit

**Files:**
- Modify: `docs/model_scoreboard.md`
- Create/Update: `data/replay_reports/low_volume_rescue_replay_20260519_v95.json`

- [ ] **Step 1: Run focused unit tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_low_volume_rescue_replay tests.model.test_low_volume_rescue_replay_cli
```

Expected: OK.

- [ ] **Step 2: Run adjacent replay tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_model_replay tests.model.test_run_hybrid_training_cli tests.model.test_low_volume_breakout_probe tests.model.test_time_to_barrier_probe
```

Expected: OK.

- [ ] **Step 3: Run experiment**

Run:

```bash
venv/bin/python scripts/run_low_volume_rescue_replay.py --output data/replay_reports/low_volume_rescue_replay_20260519_v95.json
```

Expected: report JSON is written and includes baseline/candidate metrics.

- [ ] **Step 4: Update scoreboard**

Append one concise row or bullet to `docs/model_scoreboard.md` with:

- live trigger;
- research artifact;
- command;
- best candidate params;
- validation/final/walk-forward/stress metrics;
- accept/reject decision;
- explicit note that `.env` and live bot were not changed unless the candidate strictly beats v95.

- [ ] **Step 5: Verification**

Run:

```bash
venv/bin/python -m unittest tests.model.test_low_volume_rescue_replay tests.model.test_low_volume_rescue_replay_cli tests.model.test_model_replay tests.model.test_run_hybrid_training_cli tests.model.test_low_volume_breakout_probe tests.model.test_time_to_barrier_probe
venv/bin/python -m py_compile src/pipeline/train_hybrid.py scripts/run_low_volume_rescue_replay.py
git diff --check
python -m json.tool data/replay_reports/low_volume_rescue_replay_20260519_v95.json >/dev/null
```

Expected: all commands pass.

- [ ] **Step 6: Two strict reviews after the final edit**

Review pass 1: parent review of full diff, tests, report, scoreboard, and live-risk boundary.

Review pass 2: independent subagent review of the same final diff.

If either review causes changes, rerun tests as needed and rerun both reviews after the final edit.

- [ ] **Step 7: Commit and push**

If the experiment produces useful accepted or rejected evidence, commit and push:

```bash
git add src/pipeline/train_hybrid.py scripts/run_low_volume_rescue_replay.py tests/model/test_low_volume_rescue_replay.py tests/model/test_low_volume_rescue_replay_cli.py docs/model_scoreboard.md docs/research/20260519-conditional-low-volume-rescue docs/superpowers/plans/2026-05-19-conditional-low-volume-rescue-replay.md
git add -f data/replay_reports/low_volume_rescue_replay_20260519_v95.json data/replay_reports/time_to_barrier_probe_20260519_v95_latest.json data/replay_reports/low_volume_breakout_probe_20260519_v95_latest.json
git commit -m "Add conditional low-volume rescue replay"
git push origin main
```

Do not include `.env`, `.env.example`, `src/trader/bot.py`, or live runtime config unless a separate accepted live-switch node is run.
