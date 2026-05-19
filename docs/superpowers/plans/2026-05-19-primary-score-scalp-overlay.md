# Primary Score Scalp Overlay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a replay-first primary-score rescue quick-take-profit overlay for v95 high-probability rejected signals, keeping 10% sizing and requiring strict validation/final/stress improvement before any live switch.

**Architecture:** Preserve v95 primary and near-threshold gates. Add disabled-by-default replay-only `buy_quick_profit_overlay_*` parameters that only affect score-rejected high-probability candidates inside `_run_eval_replay`; then add a bounded replay grid CLI that tests this overlay against the current v95 baseline. Do not add these parameters to live runtime manifests, `.env`, `.env.example`, or `src/trader/bot.py` in this experiment; if a candidate strictly wins, live support is a separate switch task.

**Tech Stack:** Python `unittest`, existing `src.pipeline.train_hybrid._run_eval_replay`, `src.pipeline.model_replay.run_model_replay`, `tools/memectl` for live process checks only.

---

### Task 1: Core Replay Quick-TP Support

**Files:**
- Modify: `src/pipeline/train_hybrid.py`
- Modify: `src/pipeline/model_replay.py`
- Test: `tests/model/test_low_volume_rescue_replay.py`
- Test: `tests/model/test_model_replay.py`

- [x] **Step 1: Write failing replay tests**

Add tests proving:

```python
def test_primary_score_rescue_quick_take_profit_exits_before_later_stop_loss(self):
    m = _load_module()
    episodes = [[
        _sample(sample_time=120, price=1.0, volume_30s=3.0, price_volatility=0.30),
        _sample(sample_time=130, price=1.25, volume_30s=3.2, price_volatility=0.32),
        _sample(sample_time=140, price=0.82, volume_30s=3.2, price_volatility=0.32),
    ]]

    result = m._run_eval_replay(
        episodes,
        None,
        0.98,
        _SellNonePolicy(),
        buy_probabilities_by_episode=[{0: 0.99}],
        entry_scores_by_episode=[{0: 30.0}],
        min_entry_score=35.0,
        min_entry_volume_30s=1.5,
        min_entry_price_volatility=0.10,
        stop_loss=-0.18,
        buy_quick_profit_overlay_min_prob=0.988,
        buy_quick_profit_overlay_min_pred_return=25.0,
        buy_quick_profit_overlay_max_pred_return=35.0,
        buy_quick_profit_overlay_min_entry_volume_30s=1.5,
        buy_quick_profit_overlay_min_entry_price_volatility=0.10,
        buy_quick_profit_overlay_max_age_seconds=60.0,
        buy_quick_profit_overlay_take_profit_pct=0.25,
        buy_quick_profit_overlay_max_hold_seconds=120.0,
        position_fraction=0.1,
        include_trade_log=True,
    )

    self.assertEqual(result["trade_log"][0]["exit_reason"], "QUICK_PROFIT_OVERLAY_TAKE_PROFIT")
    self.assertEqual(result["quick_profit_overlay_take_profit_count"], 1)
    self.assertTrue(result["trade_log"][0]["quick_profit_overlay_used"])
    self.assertGreater(result["trade_log"][0]["return_pct"], 0.0)
```

Also add invalid numeric coverage for `buy_quick_profit_overlay_take_profit_pct=-0.01`, `nan`, and `inf`.

Run:

```bash
venv/bin/python -m unittest tests.model.test_low_volume_rescue_replay
```

Expected before implementation: failure because the new argument/result counter/exit reason do not exist.

- [x] **Step 2: Implement minimal replay support**

In `src/pipeline/train_hybrid.py`, add replay-only arguments:

```python
buy_quick_profit_overlay_min_prob=None
buy_quick_profit_overlay_min_pred_return=None
buy_quick_profit_overlay_max_pred_return=None
buy_quick_profit_overlay_min_entry_volume_30s=None
buy_quick_profit_overlay_min_entry_price_volatility=None
buy_quick_profit_overlay_max_age_seconds=None
buy_quick_profit_overlay_take_profit_pct=None
buy_quick_profit_overlay_max_hold_seconds=None
```

Add validation using `_optional_runtime_probability` and `_optional_nonnegative_finite`. Include the values in the result payload, add `quick_profit_overlay_signal_count`, `quick_profit_overlay_entry_count`, `quick_profit_overlay_reject_count`, `quick_profit_overlay_take_profit_count`, and `quick_profit_overlay_timeout_count`.

In the entry-filter block where score/quality failures currently set `filter_rejected=True`, add an overlay candidate branch that can open a trade only when the normal v95 signal would otherwise be rejected, and only when all overlay gates pass. Store `quick_profit_overlay_used=True` on pending/open positions and in trade logs.

In the exit decision block add:

```python
if (
    quick_profit_overlay_take_profit is not None
    and bool(position.get("quick_profit_overlay_used", False))
    and pnl_pct >= float(quick_profit_overlay_take_profit)
):
    risk_exit_reason = "QUICK_PROFIT_OVERLAY_TAKE_PROFIT"
```

Add an overlay max-hold exit before normal `TIME_EXIT`:

```python
elif (
    quick_profit_overlay_max_hold_seconds is not None
    and bool(position.get("quick_profit_overlay_used", False))
    and sample_time - position["entry_time"] >= float(quick_profit_overlay_max_hold_seconds)
):
    risk_exit_reason = "QUICK_PROFIT_OVERLAY_TIME_EXIT"
```

- [x] **Step 3: Add model replay plumbing tests**

Add tests that:

```python
self.assertIsNone(config["buy_quick_profit_overlay_min_prob"])
self.assertIsNone(config["buy_quick_profit_overlay_take_profit_pct"])
```

when manifest evaluation/selected runtime params carry the key, and tests that explicit replay overrides work:

```python
config = live_replay_config_from_manifest(manifest, overrides={
    "buy_quick_profit_overlay_min_prob": 0.988,
    "buy_quick_profit_overlay_take_profit_pct": 0.25,
})
self.assertEqual(config["buy_quick_profit_overlay_min_prob"], 0.988)
self.assertEqual(config["buy_quick_profit_overlay_take_profit_pct"], 0.25)
```

Run:

```bash
venv/bin/python -m unittest tests.model.test_model_replay
```

Expected before implementation: failure because the key is not plumbed.

- [x] **Step 4: Implement model replay plumbing**

In `src/pipeline/model_replay.py`, default all `buy_quick_profit_overlay_*` keys to `None` so stale manifests cannot enable this experiment. Explicit replay overrides may enable them. Do not include these keys in live selected runtime params.

- [x] **Step 5: Verify core support**

Run:

```bash
venv/bin/python -m unittest tests.model.test_low_volume_rescue_replay tests.model.test_model_replay
venv/bin/python -m py_compile src/pipeline/train_hybrid.py src/pipeline/model_replay.py
```

Expected: all tests pass and py_compile emits no output.

### Task 2: Bounded Replay Grid CLI

**Files:**
- Create: `scripts/run_primary_score_scalp_replay.py`
- Create: `tests/model/test_primary_score_scalp_replay_cli.py`

- [x] **Step 1: Write CLI tests**

Create tests mirroring `tests/model/test_low_volume_rescue_replay_cli.py` but using quick-profit overlay keys:

```python
grid = [
    {"buy_quick_profit_overlay_min_prob": 0.988, "buy_quick_profit_overlay_min_pred_return": 32.0, "buy_quick_profit_overlay_take_profit_pct": 0.25},
    {"buy_quick_profit_overlay_min_prob": 0.988, "buy_quick_profit_overlay_min_pred_return": 25.0, "buy_quick_profit_overlay_take_profit_pct": 0.25},
]
```

Assert baseline/candidate calls preserve:

```python
position_fraction == 0.1
max_position_fraction == 0.1
fixed_stake_bnb is None
skip_all_in_replay is True
max_open_positions == 8
```

Assert selection uses validation first and only confirms the selected candidate on final.

Run:

```bash
venv/bin/python -m unittest tests.model.test_primary_score_scalp_replay_cli
```

Expected before implementation: import failure because the script does not exist.

- [x] **Step 2: Implement CLI by adapting low-volume rescue replay**

Create `scripts/run_primary_score_scalp_replay.py` with:

```python
DEFAULT_MODEL_DIR = "data/models/20260519_v95_v84_selective_nearmiss_gate"
DEFAULT_OUTPUT = "data/replay_reports/primary_score_scalp_replay_20260519_v95.json"
LIVE_POSITION_CAP = 0.1
STRICT_MAX_OPEN_POSITIONS = 8
```

Candidate grid should stay bounded:

```python
prob_floors = [0.988, 0.989, 0.990]
score_floors = [25.0, 30.0, 32.0]
volume_floors = [1.5, 2.0]
volatility_floors = [0.10, 0.14, 0.18]
take_profits = [0.25, 0.35]
```

Each candidate must set all quick-profit overlay parameters. Acceptance must require net profit, drawdown, win rate, walk-forward, stress metrics, and bounded trade count not worse than the current v95 baseline, plus `quick_profit_overlay_entry_count > 0`.

- [x] **Step 3: Verify CLI**

Run:

```bash
venv/bin/python -m unittest tests.model.test_primary_score_scalp_replay_cli
venv/bin/python -m py_compile scripts/run_primary_score_scalp_replay.py
```

Expected: pass.

### Task 3: Run Experiment And Document Decision

**Files:**
- Create: `data/replay_reports/primary_score_scalp_replay_20260519_v95.json`
- Modify: `docs/model_scoreboard.md`
- Create/modify: `docs/research/20260519-short-horizon-scalp-meta-label/summary.md`

- [x] **Step 1: Run bounded replay**

Run:

```bash
venv/bin/python scripts/run_primary_score_scalp_replay.py --output data/replay_reports/primary_score_scalp_replay_20260519_v95.json --force
```

Expected: JSON report with `decision` of `accept` or `reject`, validation baseline, selected validation candidate, and final confirmation.

- [x] **Step 2: Summarize research and decision**

Write `summary.md` with:

```markdown
# Short-Horizon Scalp Meta-Label Research

Live evidence:
- No new live trade after 2026-05-19 19:16.
- `time_to_barrier_probe_20260519_post_1916_v95.json` found 32 quick-profit rejected candidates and 25 stop-first candidates.
- `flow_activation_probe_20260519_post_1916_v95.json` accepted 0/162, so flow-only rescue is too narrow.

Research:
- Triple-barrier labels are better aligned to trade outcomes than fixed-horizon returns.
- Meta-labeling should filter an existing primary signal rather than generate broad new trades.
- Validation must use out-of-sample/final/stress checks because small quick-profit pockets overfit easily.

Decision:
- Accept only if the replay report beats v95 on validation, final, walk-forward, stress, win rate, and bounded trade count.
```

Update `docs/model_scoreboard.md` with the exact report path, metrics, and accept/reject reason.

- [x] **Step 3: Review, test, commit, push**

Run:

```bash
git status --short --untracked-files=all
venv/bin/python -m unittest tests.model.test_low_volume_rescue_replay tests.model.test_model_replay tests.model.test_primary_score_scalp_replay_cli
venv/bin/python -m py_compile src/pipeline/train_hybrid.py src/pipeline/model_replay.py scripts/run_primary_score_scalp_replay.py
python -m json.tool data/replay_reports/primary_score_scalp_replay_20260519_v95.json >/dev/null
```

Request two strict code reviews. Fix all Critical and Important findings. Then commit and push:

```bash
git add src/pipeline/train_hybrid.py src/pipeline/model_replay.py scripts/run_primary_score_scalp_replay.py tests/model/test_low_volume_rescue_replay.py tests/model/test_model_replay.py tests/model/test_primary_score_scalp_replay_cli.py docs/model_scoreboard.md docs/research/20260519-short-horizon-scalp-meta-label/summary.md
git add -f data/replay_reports/primary_score_scalp_replay_20260519_v95.json
git diff --cached -- docs/goals
git commit -m "Add primary score scalp replay"
git push
```

Expected: `git diff --cached -- docs/goals` is empty; push succeeds.
