# Dead Bounce Veto Replay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Test a replay-only dead-bounce entry veto that skips young v95 primary buys after a sharp peak-to-current crash plus creator/sell-pressure evidence, without increasing live risk.

**Architecture:** Keep the live bot untouched. Add disabled-by-default replay parameters to `src/pipeline/train_hybrid.py` and `src/pipeline/model_replay.py`, run a bounded validation-first grid, and only confirm the validation winner on sealed final. The veto runs after normal v95 score/quality gates and before opening a pending entry; it must use only causal sample fields such as `current_price`, `max_price`, `creator_is_seller`, `creator_sell_volume`, `buy_pressure`, `volume_30s`, `price_volatility`, and age.

**Tech Stack:** Python stdlib, `unittest`, existing `_run_eval_replay`, `run_model_replay`, and replay-grid CLI patterns.

---

## Live-First Context

- Current live model: `data/models/20260519_v95_v84_selective_nearmiss_gate`.
- Current risk policy: 10% position fraction, max 8 positions, no larger fixed stake.
- Live trigger: `domybest` was a high-confidence v95 primary buy, then lost money. It was already about `70.8%` below its pre-signal peak and had heavy pre-signal sell pressure.
- Similar live losses: `挠头` and `BNBGUY` also showed young age, about `70%` peak drawdown, creator sell pressure, and losses.
- Prior failed directions to avoid: global threshold lowering, static volume relaxation, quick-profit overlay, broad late-pump veto, broad path-state meta gate, blanket partial exits, and simply holding longer.

## Files

- Modify: `src/pipeline/train_hybrid.py`
- Modify: `src/pipeline/model_replay.py`
- Create: `tests/model/test_dead_bounce_veto_replay.py`
- Create: `scripts/run_dead_bounce_veto_replay.py`
- Create: `tests/model/test_dead_bounce_veto_replay_cli.py`
- Output: `data/replay_reports/dead_bounce_veto_replay_20260521_v95.json`
- Update if experiment runs: `docs/model_scoreboard.md`
- Do not modify: `docs/goals/live-model-optimization-goal.md`

---

### Task 1: Core Replay Veto Tests

**Files:**
- Create: `tests/model/test_dead_bounce_veto_replay.py`

- [ ] **Step 1: Write failing `_run_eval_replay` tests**

Create `tests/model/test_dead_bounce_veto_replay.py`:

```python
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


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


def _sample(
    *,
    token="0xdead",
    sample_time=110,
    create_timestamp=100,
    price=0.30,
    max_price=1.0,
    creator_is_seller=1,
    creator_sell_volume=2.0,
    buy_pressure=0.25,
    volume_30s=2.5,
    price_volatility=0.25,
):
    return {
        "features": {
            "current_price": price,
            "max_price": max_price,
            "holder_count": 10,
            "volume_30s": volume_30s,
            "price_volatility": price_volatility,
            "creator_is_seller": creator_is_seller,
            "creator_sell_volume": creator_sell_volume,
            "buy_pressure": buy_pressure,
        },
        "meta": {
            "token_address": token,
            "sample_time": sample_time,
            "create_timestamp": create_timestamp,
        },
    }


class TestDeadBounceVetoReplay(unittest.TestCase):
    def test_dead_bounce_veto_rejects_primary_signal_after_peak_crash_and_creator_sell(self):
        m = _load_module()
        episodes = [[_sample(), _sample(sample_time=120, price=0.28, max_price=1.0)]]

        result = m._run_eval_replay(
            episodes,
            None,
            0.98,
            _SellNonePolicy(),
            buy_probabilities_by_episode=[{0: 0.991}],
            entry_scores_by_episode=[{0: 58.0}],
            min_entry_score=35.0,
            min_entry_volume_30s=1.5,
            min_entry_price_volatility=0.10,
            buy_dead_bounce_veto_max_age_seconds=30.0,
            buy_dead_bounce_veto_min_peak_drawdown_pct=0.55,
            buy_dead_bounce_veto_min_creator_sell_volume_bnb=1.0,
            buy_dead_bounce_veto_max_buy_pressure=0.35,
            buy_dead_bounce_veto_min_entry_volume_30s=1.5,
            buy_dead_bounce_veto_min_entry_price_volatility=0.10,
            position_fraction=0.1,
            include_trade_log=True,
        )

        self.assertEqual(result["entry_signal_count"], 1)
        self.assertEqual(result["entry_score_reject_count"], 0)
        self.assertEqual(result["entry_quality_reject_count"], 0)
        self.assertEqual(result["dead_bounce_veto_signal_count"], 1)
        self.assertEqual(result["dead_bounce_veto_reject_count"], 1)
        self.assertEqual(result["total_trades"], 0)
        self.assertEqual(result["trade_log"], [])

    def test_dead_bounce_veto_allows_peak_drawdown_without_creator_or_sell_pressure(self):
        m = _load_module()
        episodes = [[
            _sample(creator_is_seller=0, creator_sell_volume=0.0, buy_pressure=0.55),
            _sample(sample_time=120, price=0.40, max_price=1.0, creator_is_seller=0, creator_sell_volume=0.0, buy_pressure=0.55),
        ]]

        result = m._run_eval_replay(
            episodes,
            None,
            0.98,
            _SellNonePolicy(),
            buy_probabilities_by_episode=[{0: 0.991}],
            entry_scores_by_episode=[{0: 58.0}],
            min_entry_score=35.0,
            min_entry_volume_30s=1.5,
            min_entry_price_volatility=0.10,
            buy_dead_bounce_veto_max_age_seconds=30.0,
            buy_dead_bounce_veto_min_peak_drawdown_pct=0.55,
            buy_dead_bounce_veto_min_creator_sell_volume_bnb=1.0,
            buy_dead_bounce_veto_max_buy_pressure=0.35,
            buy_dead_bounce_veto_min_entry_volume_30s=1.5,
            buy_dead_bounce_veto_min_entry_price_volatility=0.10,
            position_fraction=0.1,
            include_trade_log=True,
        )

        self.assertEqual(result["dead_bounce_veto_signal_count"], 0)
        self.assertEqual(result["dead_bounce_veto_reject_count"], 0)
        self.assertEqual(result["total_trades"], 1)

    def test_dead_bounce_veto_uses_only_current_sample_features(self):
        m = _load_module()
        episodes = [[
            _sample(price=1.0, max_price=1.0, creator_is_seller=0, creator_sell_volume=0.0, buy_pressure=0.55),
            _sample(sample_time=120, price=0.30, max_price=2.0, creator_is_seller=1, creator_sell_volume=4.0, buy_pressure=0.1),
        ]]

        result = m._run_eval_replay(
            episodes,
            None,
            0.98,
            _SellNonePolicy(),
            buy_probabilities_by_episode=[{0: 0.991}],
            entry_scores_by_episode=[{0: 58.0}],
            min_entry_score=35.0,
            min_entry_volume_30s=1.5,
            min_entry_price_volatility=0.10,
            buy_dead_bounce_veto_max_age_seconds=30.0,
            buy_dead_bounce_veto_min_peak_drawdown_pct=0.55,
            buy_dead_bounce_veto_min_creator_sell_volume_bnb=1.0,
            buy_dead_bounce_veto_max_buy_pressure=0.35,
            buy_dead_bounce_veto_min_entry_volume_30s=1.5,
            buy_dead_bounce_veto_min_entry_price_volatility=0.10,
            position_fraction=0.1,
            include_trade_log=True,
        )

        self.assertEqual(result["dead_bounce_veto_reject_count"], 0)
        self.assertEqual(result["total_trades"], 1)

    def test_dead_bounce_veto_rejects_invalid_runtime_params(self):
        m = _load_module()
        invalid = [
            {"buy_dead_bounce_veto_max_age_seconds": -1.0},
            {"buy_dead_bounce_veto_min_peak_drawdown_pct": float("nan")},
            {"buy_dead_bounce_veto_min_creator_sell_volume_bnb": -0.01},
            {"buy_dead_bounce_veto_max_buy_pressure": 1.5},
            {"buy_dead_bounce_veto_min_entry_volume_30s": float("inf")},
            {"buy_dead_bounce_veto_min_entry_price_volatility": -0.01},
        ]

        for overrides in invalid:
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    m._run_eval_replay(
                        [[_sample()]],
                        None,
                        0.98,
                        _SellNonePolicy(),
                        buy_probabilities_by_episode=[{0: 0.991}],
                        entry_scores_by_episode=[{0: 58.0}],
                        min_entry_score=35.0,
                        **overrides,
                    )
```

Run:

```bash
venv/bin/python -m unittest tests.model.test_dead_bounce_veto_replay
```

Expected before implementation: fail because `_run_eval_replay` does not accept `buy_dead_bounce_veto_*`.

### Task 2: Core Replay Veto Implementation

**Files:**
- Modify: `src/pipeline/train_hybrid.py`

- [ ] **Step 1: Add replay-only parameters and validation**

Add `_run_eval_replay` keyword args:

```python
buy_dead_bounce_veto_max_age_seconds=None
buy_dead_bounce_veto_min_peak_drawdown_pct=None
buy_dead_bounce_veto_min_creator_sell_volume_bnb=None
buy_dead_bounce_veto_max_buy_pressure=None
buy_dead_bounce_veto_min_entry_volume_30s=None
buy_dead_bounce_veto_min_entry_price_volatility=None
```

Parse them with the existing `_optional_nonnegative_finite` helper. Validate:

```python
if dead_bounce_veto_min_peak_drawdown is not None and dead_bounce_veto_min_peak_drawdown > 1.0:
    raise ValueError("buy_dead_bounce_veto_min_peak_drawdown_pct must be <= 1.0")
if dead_bounce_veto_max_buy_pressure is not None and dead_bounce_veto_max_buy_pressure > 1.0:
    raise ValueError("buy_dead_bounce_veto_max_buy_pressure must be <= 1.0")
```

Enable the veto only when age, peak drawdown, creator/sell-pressure, volume, and volatility thresholds are all configured.

- [ ] **Step 2: Implement causal candidate check**

Add helper near existing `_late_pump_veto_candidate`:

```python
def _dead_bounce_veto_candidate(sample, buy_prob, entry_score):
    if not dead_bounce_veto_enabled:
        return False
    features = sample.get("features", {}) or {}
    age_seconds = _sample_age_seconds(sample)
    if age_seconds is None or age_seconds > float(dead_bounce_veto_max_age):
        return False
    current_price = _safe_float(features.get("current_price"), 0.0)
    max_price = _safe_float(features.get("max_price"), 0.0)
    if current_price <= 0.0 or max_price <= 0.0:
        return False
    peak_drawdown = max(0.0, 1.0 - (current_price / max_price))
    if peak_drawdown < float(dead_bounce_veto_min_peak_drawdown):
        return False
    creator_sell_volume = _safe_float(features.get("creator_sell_volume"), 0.0)
    creator_is_seller = bool(_safe_float(features.get("creator_is_seller"), 0.0) >= 1.0)
    buy_pressure = _safe_float(features.get("buy_pressure"), 1.0)
    has_creator_pressure = creator_is_seller or creator_sell_volume >= float(dead_bounce_veto_min_creator_sell_volume)
    has_sell_pressure = buy_pressure <= float(dead_bounce_veto_max_buy_pressure)
    if not (has_creator_pressure or has_sell_pressure):
        return False
    volume_30s = _safe_float(features.get("volume_30s"), 0.0)
    price_volatility = _safe_float(features.get("price_volatility"), 0.0)
    return (
        volume_30s >= float(dead_bounce_veto_volume_floor)
        and price_volatility >= float(dead_bounce_veto_price_volatility_floor)
    )
```

Use only fields already present in `sample["features"]`. Do not inspect later samples, post-entry fields, MFE/MAE, entry slippage, or trade logs.

- [ ] **Step 3: Wire veto after normal entry gates**

In the entry block, after `filter_rejected` handling and before `_late_pump_veto_candidate`, add:

```python
elif _dead_bounce_veto_candidate(sample, buy_prob, entry_score):
    dead_bounce_veto_signal_count += 1
    dead_bounce_veto_reject_count += 1
```

Add result fields:

```python
"dead_bounce_veto_signal_count": int(dead_bounce_veto_signal_count),
"dead_bounce_veto_reject_count": int(dead_bounce_veto_reject_count),
"buy_dead_bounce_veto_max_age_seconds": dead_bounce_veto_max_age,
"buy_dead_bounce_veto_min_peak_drawdown_pct": dead_bounce_veto_min_peak_drawdown,
"buy_dead_bounce_veto_min_creator_sell_volume_bnb": dead_bounce_veto_min_creator_sell_volume,
"buy_dead_bounce_veto_max_buy_pressure": dead_bounce_veto_max_buy_pressure,
"buy_dead_bounce_veto_min_entry_volume_30s": dead_bounce_veto_volume_floor,
"buy_dead_bounce_veto_min_entry_price_volatility": dead_bounce_veto_price_volatility_floor,
```

- [ ] **Step 4: Verify core tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_dead_bounce_veto_replay
venv/bin/python -m py_compile src/pipeline/train_hybrid.py
```

Expected: tests pass and compile emits no output.

### Task 3: Model Replay Plumbing And Runtime Guardrail

**Files:**
- Modify: `src/pipeline/model_replay.py`
- Modify: `tests/model/test_model_replay.py`
- Modify: `tests/model/test_dead_bounce_veto_replay.py`

- [ ] **Step 1: Add model replay config tests**

In `tests/model/test_model_replay.py`, add tests proving manifest/runtime values do not enable the replay-only veto by default, but explicit overrides do:

```python
def test_live_replay_config_ignores_manifest_dead_bounce_veto_by_default(self):
    manifest = {
        "evaluation": {
            "buy_dead_bounce_veto_max_age_seconds": 30.0,
            "buy_dead_bounce_veto_min_peak_drawdown_pct": 0.55,
        },
        "selected_runtime_params": {
            "buy_dead_bounce_veto_max_age_seconds": 30.0,
            "buy_dead_bounce_veto_min_peak_drawdown_pct": 0.55,
        },
    }
    config = live_replay_config_from_manifest(manifest)
    self.assertIsNone(config["buy_dead_bounce_veto_max_age_seconds"])
    self.assertIsNone(config["buy_dead_bounce_veto_min_peak_drawdown_pct"])


def test_live_replay_config_allows_explicit_dead_bounce_veto_overrides(self):
    config = live_replay_config_from_manifest(
        {},
        overrides={
            "buy_dead_bounce_veto_max_age_seconds": 30.0,
            "buy_dead_bounce_veto_min_peak_drawdown_pct": 0.55,
        },
    )
    self.assertEqual(config["buy_dead_bounce_veto_max_age_seconds"], 30.0)
    self.assertEqual(config["buy_dead_bounce_veto_min_peak_drawdown_pct"], 0.55)
```

Adjust imports to match the existing style in that file.

- [ ] **Step 2: Add selected-runtime exclusion test**

In `tests/model/test_dead_bounce_veto_replay.py`, add:

```python
def test_selected_runtime_params_exclude_dead_bounce_veto_replay_only_params(self):
    m = _load_module()
    selected = m._selected_runtime_params_from_evaluation({
        "buy_threshold": 0.98,
        "buy_dead_bounce_veto_max_age_seconds": 30.0,
        "buy_dead_bounce_veto_min_peak_drawdown_pct": 0.55,
        "runtime_replay": {
            "buy_dead_bounce_veto_max_age_seconds": 20.0,
        },
    })
    self.assertEqual(selected["buy_threshold"], 0.98)
    for key in selected:
        self.assertFalse(key.startswith("buy_dead_bounce_veto_"))
```

- [ ] **Step 3: Implement model replay defaults**

In `src/pipeline/model_replay.py`, add these config defaults beside other replay-only defaults:

```python
"buy_dead_bounce_veto_max_age_seconds": None,
"buy_dead_bounce_veto_min_peak_drawdown_pct": None,
"buy_dead_bounce_veto_min_creator_sell_volume_bnb": None,
"buy_dead_bounce_veto_max_buy_pressure": None,
"buy_dead_bounce_veto_min_entry_volume_30s": None,
"buy_dead_bounce_veto_min_entry_price_volatility": None,
```

Do not add these names to `LIVE_RUNTIME_PARAM_KEYS`.

- [ ] **Step 4: Verify plumbing**

Run:

```bash
venv/bin/python -m unittest tests.model.test_dead_bounce_veto_replay tests.model.test_model_replay
venv/bin/python -m py_compile src/pipeline/model_replay.py
```

Expected: all pass.

### Task 4: Replay Evaluation Propagation

**Files:**
- Modify: `src/pipeline/train_hybrid.py`
- Modify: `tests/model/test_dead_bounce_veto_replay.py`

- [ ] **Step 1: Add `run_ab_evaluation` propagation test**

Add fake replay test in `tests/model/test_dead_bounce_veto_replay.py`:

```python
def test_run_ab_evaluation_propagates_dead_bounce_veto_replay_params(self):
    m = _load_module()
    params = {
        "buy_dead_bounce_veto_max_age_seconds": 30.0,
        "buy_dead_bounce_veto_min_peak_drawdown_pct": 0.55,
        "buy_dead_bounce_veto_min_creator_sell_volume_bnb": 1.0,
        "buy_dead_bounce_veto_max_buy_pressure": 0.35,
        "buy_dead_bounce_veto_min_entry_volume_30s": 1.5,
        "buy_dead_bounce_veto_min_entry_price_volatility": 0.10,
    }
    calls = []

    def fake_replay(episodes, buy_model, threshold, sell_policy, **kwargs):
        calls.append(dict(kwargs))
        return {
            "total_trades": 1,
            "entry_count": 1,
            "entry_rate": 0.5,
            "win_rate": 1.0,
            "net_return_pct": 12.0,
            "max_drawdown_pct": 0.0,
            "sortino_ratio": 1.0,
            "stake_mode": "fraction",
            "final_equity_bnb": 1.01,
            "net_profit_bnb": 0.01,
            "account_multiple": 1.01,
            "max_open_positions": kwargs.get("max_open_positions"),
            "dead_bounce_veto_signal_count": 3,
            "dead_bounce_veto_reject_count": 2,
            **{key: kwargs.get(key) for key in params},
        }

    class _BuyModel:
        def predict_proba(self, rows):
            return [[0.01, 0.99] for _row in rows]

    eval_samples = [
        _sample(token="0xprop-a", sample_time=100),
        _sample(token="0xprop-a", sample_time=110),
        _sample(token="0xprop-b", sample_time=200),
        _sample(token="0xprop-b", sample_time=210),
    ]
    config = {
        "eval_samples": eval_samples,
        "position_fraction": 0.1,
        "stress_replay_scenarios": [{"name": "stress_dead_bounce"}],
        "walk_forward_segments": 2,
        **params,
    }

    with patch.object(m, "_run_eval_replay", side_effect=fake_replay):
        result = m.run_ab_evaluation(
            config,
            {"model": _BuyModel(), "threshold": 0.98},
            {"model": _SellNonePolicy(), "total_timesteps": 0},
            {"bc_samples": 0},
        )

    self.assertGreaterEqual(len(calls), 5)
    for call in calls:
        for key, value in params.items():
            self.assertEqual(call.get(key), value)
    for key, value in params.items():
        self.assertEqual(result.get(key), value)
        self.assertEqual(result["runtime_replay"].get(key), value)
        self.assertEqual(result["all_in_replay"].get(key), value)
        self.assertEqual(result["stress_replay"][0].get(key), value)
        self.assertEqual(result["walk_forward"][0].get(key), value)
    self.assertEqual(result["dead_bounce_veto_signal_count"], 3)
    self.assertEqual(result["dead_bounce_veto_reject_count"], 2)
```

- [ ] **Step 2: Implement propagation**

In `run_ab_evaluation`, create a `dead_bounce_veto_params` dict, pass it into runtime, all-in, stress, and walk-forward `_run_eval_replay` calls, and copy counters/params into result summaries.

- [ ] **Step 3: Verify propagation**

Run:

```bash
venv/bin/python -m unittest tests.model.test_dead_bounce_veto_replay
```

Expected: all pass.

### Task 5: Bounded Replay Grid CLI

**Files:**
- Create: `scripts/run_dead_bounce_veto_replay.py`
- Create: `tests/model/test_dead_bounce_veto_replay_cli.py`

- [ ] **Step 1: Write CLI tests**

Create tests mirroring `tests/model/test_late_pump_exhaustion_replay_cli.py`.

Required assertions:

```python
args = cli.parse_args([])
self.assertEqual(args.model_dir, "data/models/20260519_v95_v84_selective_nearmiss_gate")
self.assertEqual(args.position_fraction, 0.1)
self.assertEqual(args.max_position_fraction, 0.1)
self.assertEqual(args.max_open_positions, 8)
with self.assertRaises(SystemExit):
    cli.parse_args(["--position-fraction", "0.2"])
```

Candidate grid assertions:

```python
candidates = list(cli.candidate_grid())
self.assertGreater(len(candidates), 0)
self.assertLessEqual(len(candidates), 64)
for candidate in candidates:
    self.assertTrue(all(key.startswith("buy_dead_bounce_veto_") for key in candidate))
    self.assertLessEqual(candidate["buy_dead_bounce_veto_min_peak_drawdown_pct"], 0.80)
```

Main-flow test must fake `run_model_replay` and assert call order:

```python
self.assertEqual([call["split"] for call in calls], ["validation", "validation", "validation", "final", "final"])
self.assertFalse(report["live_switch_evidence"])
self.assertEqual(calls[0]["overrides"]["position_fraction"], 0.1)
self.assertEqual(calls[0]["overrides"]["max_position_fraction"], 0.1)
self.assertIsNone(calls[0]["overrides"]["fixed_stake_bnb"])
self.assertTrue(calls[0]["overrides"]["skip_all_in_replay"])
self.assertEqual(calls[0]["overrides"]["max_open_positions"], 8)
```

- [ ] **Step 2: Implement CLI**

Create `scripts/run_dead_bounce_veto_replay.py` with:

```python
DEFAULT_MODEL_DIR = "data/models/20260519_v95_v84_selective_nearmiss_gate"
DEFAULT_OUTPUT = "data/replay_reports/dead_bounce_veto_replay_20260521_v95.json"
LIVE_POSITION_CAP = 0.1
STRICT_MAX_OPEN_POSITIONS = 8
```

Candidate grid:

```python
age_ceilings = [15.0, 30.0, 45.0]
peak_drawdowns = [0.50, 0.60, 0.70]
creator_sell_floors = [0.5, 1.0, 2.0]
buy_pressure_ceilings = [0.30, 0.35]
volume_floors = [1.5, 2.0]
volatility_floors = [0.10, 0.18]
```

Acceptance gate:

- Validation must improve `net_profit_bnb`.
- Validation must not worsen `max_drawdown_pct`, win rate, walk-forward worst return/drawdown, or stress worst return/profit/drawdown.
- Validation must have `dead_bounce_veto_reject_count > 0`.
- Trade count cannot shrink by more than 25% or expand at all.
- Only then run sealed final.
- Final must pass the same gates versus final baseline.
- Report must set `live_switch_evidence=false` and `safe_for_live_switch=false`.

- [ ] **Step 3: Verify CLI tests**

Run:

```bash
venv/bin/python -m unittest tests.model.test_dead_bounce_veto_replay_cli
venv/bin/python -m py_compile scripts/run_dead_bounce_veto_replay.py
```

Expected: pass.

### Task 6: Run Replay And Decide

**Files:**
- Output: `data/replay_reports/dead_bounce_veto_replay_20260521_v95.json`
- Modify: `docs/model_scoreboard.md`

- [ ] **Step 1: Run targeted tests**

```bash
venv/bin/python -m unittest \
  tests.model.test_dead_bounce_veto_replay \
  tests.model.test_dead_bounce_veto_replay_cli \
  tests.model.test_model_replay
venv/bin/python -m py_compile \
  src/pipeline/train_hybrid.py \
  src/pipeline/model_replay.py \
  scripts/run_dead_bounce_veto_replay.py
```

- [ ] **Step 2: Run the replay grid**

```bash
venv/bin/python scripts/run_dead_bounce_veto_replay.py \
  --output data/replay_reports/dead_bounce_veto_replay_20260521_v95.json \
  --force
```

- [ ] **Step 3: Record decision**

If validation or final fails, add a rejected row to `docs/model_scoreboard.md`:

```text
2026-05-21 | v95 + dead-bounce veto replay | rejected/runtime replay | ... | Do not switch live. It either removed too few candidates, removed winners, or failed validation/final/stress versus v95.
```

If final strictly beats v95, do not immediately switch live. Create a separate live-runtime implementation/switch plan because this plan is replay-only and does not add `.env`, `.env.example`, or `src/trader/bot.py` support.

### Task 7: Review, Commit, Push

**Files:**
- All files changed by Tasks 1-6.

- [ ] **Step 1: Clean temporary artifacts**

Remove only generated temp replay files from this node:

```bash
rm -f data/replay_reports/_tmp_primary_score_rescue_*.json
rm -f data/replay_reports/_tmp_v95_final_tradelog_probe.json
rm -f data/replay_reports/_tmp_v95_final_tradelog_probe.trade_log.jsonl
rm -f docs/research/20260521-dead-bounce-entry-veto/08-fetch-do-not-rug.md
```

- [ ] **Step 2: Run goal-file guardrail check**

```bash
git status --short --untracked-files=all -- docs/goals
git diff -- docs/goals/
git diff --cached -- docs/goals/
```

Expected: no output.

- [ ] **Step 3: First strict review**

Review:

```bash
git diff -- src/pipeline/train_hybrid.py src/pipeline/model_replay.py scripts/run_dead_bounce_veto_replay.py tests/model/test_dead_bounce_veto_replay.py tests/model/test_dead_bounce_veto_replay_cli.py docs/model_scoreboard.md
```

Check for leakage, risk expansion, live-runtime drift, missing counters, and replay-only defaults.

- [ ] **Step 4: Second strict review**

Repeat the diff review after no further edits. If a material issue is found and fixed, reset review count and run two clean reviews again.

- [ ] **Step 5: Commit and push**

Only after tests, replay decision, docs, and two clean reviews:

```bash
git add src/pipeline/train_hybrid.py src/pipeline/model_replay.py scripts/run_dead_bounce_veto_replay.py tests/model/test_dead_bounce_veto_replay.py tests/model/test_dead_bounce_veto_replay_cli.py docs/model_scoreboard.md docs/research/20260521-dead-bounce-entry-veto docs/superpowers/plans/2026-05-21-dead-bounce-veto-replay.md
git add -f data/replay_reports/dead_bounce_veto_replay_20260521_v95.json
git commit -m "Test dead bounce replay veto"
git push
```

Do not include `docs/goals/` in the commit unless the user explicitly asked for a goal-document change in the current turn.
