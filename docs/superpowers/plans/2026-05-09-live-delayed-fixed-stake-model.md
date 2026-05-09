# Live Delayed Fixed-Stake Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Train and evaluate the next FourMeme model against 3-second delayed execution, fixed 0.1 BNB stakes, 1 BNB starting equity, 8-way concurrency, and a preferred sub-30% drawdown band.

**Architecture:** Add live-delayed labels in the dataset layer, pass execution-label controls through the training pipeline, add a fixed-BNB stake mode to replay/risk tuning, and report BNB profit/multiple/drawdown-concentration metrics in the manifest. This plan implements the first production-useful version of the approved design; the existing PPO/BC sell policy remains the trainable exit mechanism while entry labels and replay become live-aligned.

**Tech Stack:** Python 3.12, `unittest`, CatBoost buy model, Stable-Baselines PPO sell policy, plain repo scripts under `scripts/`.

---

## File Map

- Modify `src/data/dataset_builder.py`: add `label_entry_delay_seconds` and `label_exit_delay_seconds`; compute `live_executable_return_pct` without changing legacy labels.
- Modify `src/pipeline/train_hybrid.py`: pass label delay controls into `DatasetBuilder`; add fixed-stake replay controls; score risk tuning by fixed-stake BNB return with drawdown penalties; add replay metrics.
- Modify `scripts/run_hybrid_training.py`: expose fixed-stake and initial-equity CLI flags; live profile defaults to `initial_equity_bnb=1.0`, `fixed_stake_bnb=0.1`, `entry/exit_delay=3`, `max_open_positions=8`.
- Modify `tests/model/test_dataset_builder_is_moon_target.py`: cover delayed entry/exit labels and missing live entry.
- Modify `tests/model/test_train_hybrid_pipeline.py`: cover builder config propagation, fixed-stake replay, risk scoring, and manifest metrics.
- Modify `tests/model/test_run_hybrid_training_cli.py`: cover new CLI flags and live profile defaults.

## Task 1: Add Delayed Live Labels

**Files:**
- Modify: `tests/model/test_dataset_builder_is_moon_target.py`
- Modify: `src/data/dataset_builder.py`

- [ ] **Step 1: Write failing dataset label tests**

Append these tests to `TestDatasetBuilderIsMoonTarget`:

```python
    def test_live_label_uses_delayed_entry_price(self):
        builder = DatasetBuilder(
            lifecycle_dir=self.tmp.name,
            label_entry_delay_seconds=3,
            label_exit_delay_seconds=0,
            label_fee_bps=0.0,
            label_slippage_bps=0.0,
            label_stop_loss_pct=-50.0,
            label_target_return_pct=40.0,
        )
        lifecycle = {
            "buys": [
                {"timestamp": 10, "price": 1.0},
                {"timestamp": 13, "price": 2.0},
                {"timestamp": 20, "price": 3.0},
            ],
            "sells": [],
        }

        label = builder._calculate_label_with_window(lifecycle, sample_time=10, future_window=30)

        self.assertIsNotNone(label)
        self.assertEqual(label["live_entry_available"], 1)
        self.assertAlmostEqual(label["max_return_pct"], 200.0)
        self.assertAlmostEqual(label["live_entry_price"], 2.0)
        self.assertAlmostEqual(label["live_executable_return_pct"], 50.0)
        self.assertEqual(label["live_target_hit_before_stop"], 1)
```

Also append:

```python
    def test_live_label_uses_delayed_exit_price(self):
        builder = DatasetBuilder(
            lifecycle_dir=self.tmp.name,
            label_entry_delay_seconds=3,
            label_exit_delay_seconds=3,
            label_fee_bps=0.0,
            label_slippage_bps=0.0,
            label_stop_loss_pct=-50.0,
            label_target_return_pct=80.0,
        )
        lifecycle = {
            "buys": [
                {"timestamp": 10, "price": 1.0},
                {"timestamp": 13, "price": 1.0},
                {"timestamp": 20, "price": 3.0},
                {"timestamp": 23, "price": 2.0},
            ],
            "sells": [],
        }

        label = builder._calculate_label_with_window(lifecycle, sample_time=10, future_window=30)

        self.assertIsNotNone(label)
        self.assertAlmostEqual(label["max_return_pct"], 200.0)
        self.assertAlmostEqual(label["live_cost_adjusted_max_return_pct"], 100.0)
        self.assertAlmostEqual(label["live_executable_return_pct"], 100.0)
        self.assertEqual(label["live_time_to_target_seconds"], 13)
```

Also append:

```python
    def test_live_label_marks_missing_delayed_entry_as_not_executable(self):
        builder = DatasetBuilder(
            lifecycle_dir=self.tmp.name,
            label_entry_delay_seconds=10,
            label_exit_delay_seconds=0,
            label_fee_bps=0.0,
            label_slippage_bps=0.0,
        )
        lifecycle = {
            "buys": [
                {"timestamp": 10, "price": 1.0},
                {"timestamp": 15, "price": 3.0},
            ],
            "sells": [],
        }

        label = builder._calculate_label_with_window(lifecycle, sample_time=10, future_window=8)

        self.assertIsNotNone(label)
        self.assertEqual(label["live_entry_available"], 0)
        self.assertAlmostEqual(label["live_executable_return_pct"], 0.0)
        self.assertEqual(label["live_target_hit_before_stop"], 0)
```

- [ ] **Step 2: Verify the new tests fail for missing constructor args/labels**

Run:

```bash
venv/bin/python -m unittest tests.model.test_dataset_builder_is_moon_target
```

Expected: FAIL/ERROR because `DatasetBuilder.__init__()` does not accept `label_entry_delay_seconds` and live label keys do not exist.

- [ ] **Step 3: Add constructor fields and metadata**

In `src/data/dataset_builder.py`, extend `DatasetBuilder.__init__`:

```python
        label_entry_delay_seconds: int = 0,
        label_exit_delay_seconds: int = 0,
```

Store them after target-return config:

```python
        self.label_entry_delay_seconds = max(0, int(label_entry_delay_seconds or 0))
        self.label_exit_delay_seconds = max(0, int(label_exit_delay_seconds or 0))
```

Add both values to `metadata["dataset_config"]`:

```python
                'label_entry_delay_seconds': self.label_entry_delay_seconds,
                'label_exit_delay_seconds': self.label_exit_delay_seconds,
```

- [ ] **Step 4: Add helper functions for live fills**

Add these methods near `_calculate_label_with_window`:

```python
    @staticmethod
    def _trade_timestamp(trade: Dict) -> int:
        return int(trade.get('timestamp', 0) or 0)

    @staticmethod
    def _trade_price(trade: Dict) -> float:
        return float(trade.get('price', 0.0) or 0.0)

    @classmethod
    def _first_trade_at_or_after(cls, trades: List[Dict], due_time: int) -> Optional[Dict]:
        for trade in trades:
            if cls._trade_timestamp(trade) >= int(due_time):
                return trade
        return None
```

- [ ] **Step 5: Compute live label values**

Inside `_calculate_label_with_window`, after `future_trades_sorted` is defined, compute delayed live labels from sorted trades:

```python
        live_label = self._calculate_live_execution_label(
            future_trades_sorted,
            sample_time=sample_time,
            future_window=future_window,
            fee_rate=fee_rate,
            slippage_rate=slippage_rate,
        )
```

Then merge it into the returned `label`:

```python
        label.update(live_label)
```

Implement `_calculate_live_execution_label`:

```python
    def _calculate_live_execution_label(
        self,
        future_trades_sorted: List[Dict],
        *,
        sample_time: int,
        future_window: int,
        fee_rate: float,
        slippage_rate: float,
    ) -> Dict:
        entry_due_time = int(sample_time) + self.label_entry_delay_seconds
        entry_trade = self._first_trade_at_or_after(future_trades_sorted, entry_due_time)
        base = {
            'live_entry_delay_seconds': int(self.label_entry_delay_seconds),
            'live_exit_delay_seconds': int(self.label_exit_delay_seconds),
            'live_entry_available': 0,
            'live_entry_time': 0,
            'live_entry_wait_seconds': 0,
            'live_entry_price': 0.0,
            'live_cost_adjusted_max_return_pct': 0.0,
            'live_cost_adjusted_min_return_pct': 0.0,
            'live_cost_adjusted_final_return_pct': 0.0,
            'live_executable_return_pct': 0.0,
            'live_target_hit_before_stop': 0,
            'live_stop_hit_before_target': 0,
            'live_time_to_target_seconds': 0,
            'live_time_to_stop_seconds': 0,
        }
        if entry_trade is None:
            return base

        entry_time = self._trade_timestamp(entry_trade)
        entry_raw_price = self._trade_price(entry_trade)
        entry_effective_price = entry_raw_price * (1.0 + slippage_rate) / max(1e-12, 1.0 - fee_rate)
        if entry_effective_price <= 0.0:
            return base

        live_returns = []
        best_return_before_stop = None
        target_hit_before_stop = False
        stop_hit_before_target = False
        time_to_target_seconds = 0
        time_to_stop_seconds = 0

        for candidate in future_trades_sorted:
            candidate_time = self._trade_timestamp(candidate)
            if candidate_time <= entry_time:
                continue
            due_time = candidate_time + self.label_exit_delay_seconds
            exit_trade = self._first_trade_at_or_after(future_trades_sorted, due_time)
            if exit_trade is None:
                exit_trade = future_trades_sorted[-1]
            exit_price = self._trade_price(exit_trade)
            if exit_price <= 0.0:
                adjusted_return = 0.0
            else:
                exit_effective_price = exit_price * max(0.0, 1.0 - slippage_rate) * max(0.0, 1.0 - fee_rate)
                adjusted_return = ((exit_effective_price - entry_effective_price) / entry_effective_price) * 100.0
            live_returns.append((exit_trade, adjusted_return))

            if best_return_before_stop is None or adjusted_return > best_return_before_stop:
                best_return_before_stop = adjusted_return
            if not target_hit_before_stop and adjusted_return >= self.label_target_return_pct:
                target_hit_before_stop = True
                time_to_target_seconds = int(self._trade_timestamp(exit_trade) - int(sample_time))
            if adjusted_return <= self.label_stop_loss_pct:
                if not target_hit_before_stop:
                    stop_hit_before_target = True
                time_to_stop_seconds = int(self._trade_timestamp(exit_trade) - int(sample_time))
                break

        returns_only = [value for _trade, value in live_returns]
        base.update(
            {
                'live_entry_available': 1,
                'live_entry_time': int(entry_time),
                'live_entry_wait_seconds': int(entry_time - int(sample_time)),
                'live_entry_price': float(entry_raw_price),
                'live_cost_adjusted_max_return_pct': float(max(returns_only)) if returns_only else 0.0,
                'live_cost_adjusted_min_return_pct': float(min(returns_only)) if returns_only else 0.0,
                'live_cost_adjusted_final_return_pct': float(returns_only[-1]) if returns_only else 0.0,
                'live_executable_return_pct': float(best_return_before_stop) if best_return_before_stop is not None else 0.0,
                'live_target_hit_before_stop': 1 if target_hit_before_stop else 0,
                'live_stop_hit_before_target': 1 if stop_hit_before_target else 0,
                'live_time_to_target_seconds': int(time_to_target_seconds),
                'live_time_to_stop_seconds': int(time_to_stop_seconds),
            }
        )
        return base
```

- [ ] **Step 6: Verify dataset tests pass**

Run:

```bash
venv/bin/python -m unittest tests.model.test_dataset_builder_is_moon_target
```

Expected: OK.

- [ ] **Step 7: Commit delayed-label change**

Run:

```bash
git add src/data/dataset_builder.py tests/model/test_dataset_builder_is_moon_target.py
git commit -m "Add live delayed execution labels"
```

## Task 2: Pass Label Delay Controls Through Training

**Files:**
- Modify: `tests/model/test_train_hybrid_pipeline.py`
- Modify: `src/pipeline/train_hybrid.py`

- [ ] **Step 1: Write failing propagation test**

Extend `test_load_samples_passes_execution_label_controls_to_builder` assertions:

```python
        self.assertEqual(kwargs["label_entry_delay_seconds"], 3)
        self.assertEqual(kwargs["label_exit_delay_seconds"], 4)
```

And pass the controls in that test config:

```python
                    "entry_delay_seconds": 3,
                    "exit_delay_seconds": 4,
```

- [ ] **Step 2: Verify propagation test fails**

Run:

```bash
venv/bin/python -m unittest tests.model.test_train_hybrid_pipeline.TestHybridTrainingPipeline.test_load_samples_passes_execution_label_controls_to_builder
```

Expected: FAIL because `_load_samples` does not pass `label_entry_delay_seconds` or `label_exit_delay_seconds`.

- [ ] **Step 3: Pass delay controls into `DatasetBuilder`**

In `_load_samples`, add these keyword args:

```python
            label_entry_delay_seconds=int(
                config.get("label_entry_delay_seconds", config.get("entry_delay_seconds", 0)) or 0
            ),
            label_exit_delay_seconds=int(
                config.get("label_exit_delay_seconds", config.get("exit_delay_seconds", 0)) or 0
            ),
```

- [ ] **Step 4: Verify pipeline test passes**

Run:

```bash
venv/bin/python -m unittest tests.model.test_train_hybrid_pipeline.TestHybridTrainingPipeline.test_load_samples_passes_execution_label_controls_to_builder
```

Expected: OK.

- [ ] **Step 5: Commit propagation change**

Run:

```bash
git add src/pipeline/train_hybrid.py tests/model/test_train_hybrid_pipeline.py
git commit -m "Pass live label delay controls"
```

## Task 3: Add Fixed 0.1 BNB Replay Mode

**Files:**
- Modify: `tests/model/test_train_hybrid_pipeline.py`
- Modify: `src/pipeline/train_hybrid.py`

- [ ] **Step 1: Write failing fixed-stake replay tests**

Add a test near the replay tests:

```python
    def test_run_eval_replay_fixed_stake_does_not_compound_position_size(self):
        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                return [[0.1, 0.9] for _ in range(len(X))]

        class _SellAllPolicy:
            def predict(self, obs, deterministic=True):
                return 3, None

        episodes = [
            [
                {"features": {"current_price": 1.0, "holder_count": 10}, "meta": {"token_address": "0xa", "sample_time": 100}},
                {"features": {"current_price": 2.0, "holder_count": 11}, "meta": {"token_address": "0xa", "sample_time": 110}},
            ],
            [
                {"features": {"current_price": 1.0, "holder_count": 10}, "meta": {"token_address": "0xb", "sample_time": 200}},
                {"features": {"current_price": 2.0, "holder_count": 11}, "meta": {"token_address": "0xb", "sample_time": 210}},
            ],
        ]

        out = m._run_eval_replay(
            episodes,
            _FakeBuyModel(),
            0.5,
            _SellAllPolicy(),
            position_fraction=1.0,
            fixed_stake_bnb=0.1,
            initial_equity_bnb=1.0,
            include_trade_log=True,
        )

        self.assertEqual(out["stake_mode"], "fixed_bnb")
        self.assertAlmostEqual(out["fixed_stake_bnb"], 0.1)
        self.assertAlmostEqual(out["initial_equity_bnb"], 1.0)
        self.assertAlmostEqual(out["net_profit_bnb"], 0.2)
        self.assertAlmostEqual(out["final_equity_bnb"], 1.2)
        self.assertAlmostEqual(out["account_multiple"], 1.2)
        self.assertEqual(len(out["trade_log"]), 2)
        self.assertTrue(all(row["stake_bnb"] == 0.1 for row in out["trade_log"]))
```

Add a second test:

```python
    def test_run_eval_replay_fixed_stake_requires_free_cash(self):
        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                return [[0.1, 0.9] for _ in range(len(X))]

        episodes = [
            [
                {"features": {"current_price": 1.0, "holder_count": 10}, "meta": {"token_address": "0xa", "sample_time": 100}},
                {"features": {"current_price": 1.0, "holder_count": 11}, "meta": {"token_address": "0xa", "sample_time": 200}},
            ],
            [
                {"features": {"current_price": 1.0, "holder_count": 10}, "meta": {"token_address": "0xb", "sample_time": 101}},
                {"features": {"current_price": 1.0, "holder_count": 11}, "meta": {"token_address": "0xb", "sample_time": 201}},
            ],
        ]

        out = m._run_eval_replay(
            episodes,
            _FakeBuyModel(),
            0.5,
            None,
            fixed_stake_bnb=0.6,
            initial_equity_bnb=1.0,
            max_open_positions=8,
        )

        self.assertEqual(out["entry_count"], 1)
        self.assertAlmostEqual(out["fixed_stake_bnb"], 0.6)
```

- [ ] **Step 2: Verify fixed-stake tests fail**

Run:

```bash
venv/bin/python -m unittest tests.model.test_train_hybrid_pipeline.TestHybridTrainingPipeline.test_run_eval_replay_fixed_stake_does_not_compound_position_size tests.model.test_train_hybrid_pipeline.TestHybridTrainingPipeline.test_run_eval_replay_fixed_stake_requires_free_cash
```

Expected: FAIL/ERROR because `_run_eval_replay` lacks `fixed_stake_bnb`, `initial_equity_bnb`, and BNB metrics.

- [ ] **Step 3: Add replay parameters and stake mode**

In `_run_eval_replay` signature add:

```python
    initial_equity_bnb=1.0,
    fixed_stake_bnb=None,
```

Replace:

```python
    initial_equity = 1.0
```

with:

```python
    initial_equity = max(1e-12, float(initial_equity_bnb or 1.0))
```

After `max_stake_fraction`, add:

```python
    fixed_stake = None if fixed_stake_bnb is None else max(0.0, float(fixed_stake_bnb))
    stake_mode = "fixed_bnb" if fixed_stake is not None else "fraction"
```

Update `_can_open_position`:

```python
        required_cash = fixed_stake if fixed_stake is not None else 0.0
        if fixed_stake is not None and cash + 1e-12 < required_cash:
            return False
```

Update `_stake_amount`:

```python
        if fixed_stake is not None:
            return min(cash, fixed_stake) if cash + 1e-12 >= fixed_stake else 0.0
```

Store `stake_bnb` in position:

```python
            "stake_bnb": float(stake),
```

Add `stake_bnb` to trade log rows:

```python
                    "stake_bnb": float(position.get("stake_bnb", position.get("cost_basis", 0.0))),
```

Add base result fields:

```python
        "initial_equity_bnb": float(initial_equity),
        "fixed_stake_bnb": None if fixed_stake is None else float(fixed_stake),
        "stake_mode": stake_mode,
```

Add final result fields in both zero-trade and nonzero-trade branches:

```python
            final_equity_bnb=float(final_equity),
            net_profit_bnb=float(final_equity - initial_equity),
            account_multiple=float(final_equity / initial_equity),
```

- [ ] **Step 4: Propagate fixed-stake args through evaluation**

In `run_ab_evaluation`, read:

```python
    initial_equity_bnb = float(config.get("initial_equity_bnb", 1.0))
    fixed_stake_bnb = config.get("fixed_stake_bnb")
    fixed_stake_bnb = None if fixed_stake_bnb is None else float(fixed_stake_bnb)
```

Pass these to every `_run_eval_replay` call, including runtime, all-in, stress, and walk-forward:

```python
            initial_equity_bnb=initial_equity_bnb,
            fixed_stake_bnb=fixed_stake_bnb,
```

Add to `result`:

```python
        "initial_equity_bnb": initial_equity_bnb,
        "fixed_stake_bnb": fixed_stake_bnb,
        "stake_mode": runtime_replay.get("stake_mode", "fraction"),
        "final_equity_bnb": float(runtime_replay.get("final_equity_bnb", 1.0)),
        "net_profit_bnb": float(runtime_replay.get("net_profit_bnb", 0.0)),
        "account_multiple": float(runtime_replay.get("account_multiple", 1.0)),
```

- [ ] **Step 5: Verify fixed-stake tests pass**

Run:

```bash
venv/bin/python -m unittest tests.model.test_train_hybrid_pipeline.TestHybridTrainingPipeline.test_run_eval_replay_fixed_stake_does_not_compound_position_size tests.model.test_train_hybrid_pipeline.TestHybridTrainingPipeline.test_run_eval_replay_fixed_stake_requires_free_cash
```

Expected: OK.

- [ ] **Step 6: Commit fixed replay mode**

Run:

```bash
git add src/pipeline/train_hybrid.py tests/model/test_train_hybrid_pipeline.py
git commit -m "Add fixed BNB replay mode"
```

## Task 4: Add CLI And Live Profile Defaults

**Files:**
- Modify: `tests/model/test_run_hybrid_training_cli.py`
- Modify: `scripts/run_hybrid_training.py`

- [ ] **Step 1: Write failing CLI tests**

In the full CLI config test, add CLI args:

```python
                    "--initial-equity-bnb", "2.0",
                    "--fixed-stake-bnb", "0.25",
```

Add assertions:

```python
        self.assertEqual(cfg["initial_equity_bnb"], 2.0)
        self.assertEqual(cfg["fixed_stake_bnb"], 0.25)
```

In `test_live_replay_profile_applies_default_execution_controls`, add:

```python
        self.assertEqual(cfg["initial_equity_bnb"], 1.0)
        self.assertEqual(cfg["fixed_stake_bnb"], 0.1)
```

- [ ] **Step 2: Verify CLI tests fail**

Run:

```bash
venv/bin/python -m unittest tests.model.test_run_hybrid_training_cli
```

Expected: FAIL/ERROR because CLI args/config fields do not exist.

- [ ] **Step 3: Add CLI args and config**

In `parse_args`, add:

```python
    parser.add_argument("--initial-equity-bnb", type=float, default=1.0, help="Starting BNB equity used by replay")
    parser.add_argument("--fixed-stake-bnb", type=float, default=None, help="Fixed BNB stake per replay entry; live profile defaults to 0.1")
```

In `main`, compute:

```python
    fixed_stake_bnb = args.fixed_stake_bnb
    if fixed_stake_bnb is None and replay_controls["live_replay_profile"]:
        fixed_stake_bnb = 0.1
```

Add to `config`:

```python
        "initial_equity_bnb": args.initial_equity_bnb,
        "fixed_stake_bnb": fixed_stake_bnb,
```

- [ ] **Step 4: Verify CLI tests pass**

Run:

```bash
venv/bin/python -m unittest tests.model.test_run_hybrid_training_cli
```

Expected: OK.

- [ ] **Step 5: Commit CLI change**

Run:

```bash
git add scripts/run_hybrid_training.py tests/model/test_run_hybrid_training_cli.py
git commit -m "Add fixed stake training CLI controls"
```

## Task 5: Score Risk Tuning By Fixed-Stake BNB With 30% Drawdown Preference

**Files:**
- Modify: `tests/model/test_train_hybrid_pipeline.py`
- Modify: `src/pipeline/train_hybrid.py`

- [ ] **Step 1: Write failing risk-score unit test**

Add:

```python
    def test_risk_tune_score_prefers_higher_bnb_profit_with_acceptable_drawdown(self):
        m = _load_module()
        high_return = {
            "net_return_pct": 100.0,
            "net_profit_bnb": 1.0,
            "account_multiple": 2.0,
            "max_drawdown_pct": -25.0,
            "entry_rate": 0.2,
        }
        low_return = {
            "net_return_pct": 20.0,
            "net_profit_bnb": 0.2,
            "account_multiple": 1.2,
            "max_drawdown_pct": -5.0,
            "entry_rate": 0.2,
        }

        high_score = m._risk_tune_replay_score(
            {"risk_tune_preferred_max_drawdown_pct": -30.0, "risk_tune_excess_drawdown_penalty": 4.0},
            high_return,
        )
        low_score = m._risk_tune_replay_score(
            {"risk_tune_preferred_max_drawdown_pct": -30.0, "risk_tune_excess_drawdown_penalty": 4.0},
            low_return,
        )

        self.assertGreater(high_score, low_score)
```

Add:

```python
    def test_risk_tune_score_penalizes_drawdown_beyond_preferred_band(self):
        m = _load_module()
        acceptable = {"net_profit_bnb": 1.0, "account_multiple": 2.0, "max_drawdown_pct": -30.0, "entry_rate": 0.2}
        excessive = {"net_profit_bnb": 1.0, "account_multiple": 2.0, "max_drawdown_pct": -45.0, "entry_rate": 0.2}

        acceptable_score = m._risk_tune_replay_score(
            {"risk_tune_preferred_max_drawdown_pct": -30.0, "risk_tune_excess_drawdown_penalty": 4.0},
            acceptable,
        )
        excessive_score = m._risk_tune_replay_score(
            {"risk_tune_preferred_max_drawdown_pct": -30.0, "risk_tune_excess_drawdown_penalty": 4.0},
            excessive,
        )

        self.assertLess(excessive_score, acceptable_score)
```

- [ ] **Step 2: Verify score tests fail**

Run:

```bash
venv/bin/python -m unittest tests.model.test_train_hybrid_pipeline.TestHybridTrainingPipeline.test_risk_tune_score_prefers_higher_bnb_profit_with_acceptable_drawdown tests.model.test_train_hybrid_pipeline.TestHybridTrainingPipeline.test_risk_tune_score_penalizes_drawdown_beyond_preferred_band
```

Expected: FAIL because current score uses log return and does not implement the preferred 30% band.

- [ ] **Step 3: Implement fixed-stake score**

Replace `_risk_tune_replay_score` body with:

```python
    if "net_profit_bnb" in replay:
        base_score = float(replay.get("net_profit_bnb", 0.0))
    else:
        final_equity = max(1e-12, 1.0 + (float(replay.get("net_return_pct", 0.0)) / 100.0))
        base_score = math.log(final_equity)

    max_drawdown = float(replay.get("max_drawdown_pct", 0.0))
    preferred_drawdown = float(config.get("risk_tune_preferred_max_drawdown_pct", -30.0))
    excess_drawdown = max(0.0, abs(min(0.0, max_drawdown)) - abs(min(0.0, preferred_drawdown))) / 100.0
    excess_drawdown_penalty = excess_drawdown * float(config.get("risk_tune_excess_drawdown_penalty", 3.0))
    drawdown_penalty = (
        abs(min(0.0, max_drawdown)) / 100.0
    ) * float(config.get("risk_tune_drawdown_penalty", 0.0))
    entry_rate = _replay_entry_rate(replay)
    turnover_penalty = entry_rate * float(config.get("risk_tune_turnover_penalty", 0.0))
    entry_rate_penalty = 0.0
    target_entry_rate = config.get("risk_tune_target_entry_rate")
    if target_entry_rate is not None:
        entry_rate_penalty = abs(entry_rate - float(target_entry_rate)) * float(config.get("risk_tune_entry_rate_penalty", 0.0))
    return float(base_score - drawdown_penalty - excess_drawdown_penalty - turnover_penalty - entry_rate_penalty)
```

- [ ] **Step 4: Propagate fixed stake into risk tuning**

In `_tune_buy_threshold_by_replay`, read:

```python
    initial_equity_bnb = float(config.get("initial_equity_bnb", 1.0))
    fixed_stake_bnb = config.get("fixed_stake_bnb")
    fixed_stake_bnb = None if fixed_stake_bnb is None else float(fixed_stake_bnb)
```

Pass both to `_run_eval_replay`.

Add them to `constraints` and infeasible `replay` dictionaries:

```python
                "initial_equity_bnb": initial_equity_bnb,
                "fixed_stake_bnb": fixed_stake_bnb,
```

- [ ] **Step 5: Verify risk-score tests pass**

Run:

```bash
venv/bin/python -m unittest tests.model.test_train_hybrid_pipeline.TestHybridTrainingPipeline.test_risk_tune_score_prefers_higher_bnb_profit_with_acceptable_drawdown tests.model.test_train_hybrid_pipeline.TestHybridTrainingPipeline.test_risk_tune_score_penalizes_drawdown_beyond_preferred_band
```

Expected: OK.

- [ ] **Step 6: Commit risk tuning change**

Run:

```bash
git add src/pipeline/train_hybrid.py tests/model/test_train_hybrid_pipeline.py
git commit -m "Tune risk score for fixed stake replay"
```

## Task 6: Add Model-Selection Metrics For Drawdown And Profit Concentration

**Files:**
- Modify: `tests/model/test_train_hybrid_pipeline.py`
- Modify: `src/pipeline/train_hybrid.py`

- [ ] **Step 1: Write failing metrics test**

Add:

```python
    def test_run_ab_evaluation_reports_drawdown_limit_and_profit_concentration(self):
        m = _load_module()

        class _FakeBuyModel:
            def predict_proba(self, X):
                return [[0.1, 0.9] for _ in range(len(X))]

        class _SellAllPolicy:
            def predict(self, obs, deterministic=True):
                return 3, None

        eval_samples = [
            {"features": {"current_price": 1.0, "holder_count": 10}, "meta": {"token_address": "0xa", "sample_time": 100}},
            {"features": {"current_price": 2.0, "holder_count": 11}, "meta": {"token_address": "0xa", "sample_time": 110}},
            {"features": {"current_price": 1.0, "holder_count": 10}, "meta": {"token_address": "0xb", "sample_time": 200}},
            {"features": {"current_price": 0.9, "holder_count": 11}, "meta": {"token_address": "0xb", "sample_time": 210}},
        ]

        out = m.run_ab_evaluation(
            {
                "eval_samples": eval_samples,
                "fixed_stake_bnb": 0.1,
                "initial_equity_bnb": 1.0,
                "preferred_max_drawdown_pct": -30.0,
                "include_trade_log": True,
            },
            {"model": _FakeBuyModel(), "threshold": 0.5},
            {"model": _SellAllPolicy(), "total_timesteps": 128},
            {"bc_samples": 10},
        )

        self.assertIn("drawdown_within_preferred_limit", out)
        self.assertTrue(out["drawdown_within_preferred_limit"])
        self.assertIn("top_trade_profit_concentration", out)
        self.assertIn("top_1_profit_share", out["top_trade_profit_concentration"])
```

- [ ] **Step 2: Verify metrics test fails**

Run:

```bash
venv/bin/python -m unittest tests.model.test_train_hybrid_pipeline.TestHybridTrainingPipeline.test_run_ab_evaluation_reports_drawdown_limit_and_profit_concentration
```

Expected: FAIL because fields are missing.

- [ ] **Step 3: Implement concentration helper**

Add near `_summarize_trade_log_by_exit_reason`:

```python
def _trade_profit_concentration(trade_log):
    profits = [
        float(row.get("stake_bnb", 0.0) or 0.0) * float(row.get("return_pct", 0.0) or 0.0) / 100.0
        for row in trade_log or []
    ]
    positive = sorted((value for value in profits if value > 0.0), reverse=True)
    total_positive = sum(positive)
    if total_positive <= 0.0:
        return {
            "positive_profit_bnb": 0.0,
            "top_1_profit_share": 0.0,
            "top_5_profit_share": 0.0,
            "top_10_profit_share": 0.0,
        }
    return {
        "positive_profit_bnb": float(total_positive),
        "top_1_profit_share": float(sum(positive[:1]) / total_positive),
        "top_5_profit_share": float(sum(positive[:5]) / total_positive),
        "top_10_profit_share": float(sum(positive[:10]) / total_positive),
    }
```

- [ ] **Step 4: Add metrics to `run_ab_evaluation`**

After `result` is built and after optional `trade_log` is available:

```python
    preferred_max_drawdown_pct = float(config.get("preferred_max_drawdown_pct", -30.0))
    result["preferred_max_drawdown_pct"] = preferred_max_drawdown_pct
    result["drawdown_within_preferred_limit"] = bool(float(result["max_drawdown_pct"]) >= preferred_max_drawdown_pct)
```

After walk-forward summary:

```python
        result["walk_forward_drawdown_within_preferred_limit"] = bool(
            result["walk_forward_worst_max_drawdown_pct"] >= preferred_max_drawdown_pct
        )
```

If `runtime_replay` has a trade log, add:

```python
    result["top_trade_profit_concentration"] = _trade_profit_concentration(runtime_replay.get("trade_log", []))
```

- [ ] **Step 5: Verify metrics test passes**

Run:

```bash
venv/bin/python -m unittest tests.model.test_train_hybrid_pipeline.TestHybridTrainingPipeline.test_run_ab_evaluation_reports_drawdown_limit_and_profit_concentration
```

Expected: OK.

- [ ] **Step 6: Commit metrics change**

Run:

```bash
git add src/pipeline/train_hybrid.py tests/model/test_train_hybrid_pipeline.py
git commit -m "Report live replay selection metrics"
```

## Task 7: Full Verification Before Training

**Files:**
- No code changes expected.

- [ ] **Step 1: Run full unit test suite**

Run:

```bash
venv/bin/python -m unittest discover
```

Expected: all tests pass.

- [ ] **Step 2: Check whitespace**

Run:

```bash
git diff --check
```

Expected: no output.

- [ ] **Step 3: Self-review changed code**

Run:

```bash
git diff HEAD~6..HEAD -- src/data/dataset_builder.py src/pipeline/train_hybrid.py scripts/run_hybrid_training.py tests/model/test_dataset_builder_is_moon_target.py tests/model/test_train_hybrid_pipeline.py tests/model/test_run_hybrid_training_cli.py
```

Expected: review confirms no future leakage in features, live labels use delayed fills, fixed-stake replay does not compound stake, and 30% drawdown preference is recorded.

## Task 8: Train V22 With Live Delayed Labels And Fixed 0.1 BNB Stake

**Files:**
- Creates untracked model output under `data/models/20260509_live_fixed_stake_v22/`.

- [ ] **Step 1: Run training**

Run:

```bash
venv/bin/python scripts/run_hybrid_training.py \
  --output-dir data/models/20260509_live_fixed_stake_v22 \
  --lifecycle-dir data/training \
  --train-split-ratio 0.7 \
  --min-eval-files 3 \
  --sample-mode trade_event \
  --max-sample-age-seconds 300 \
  --future-windows 300 \
  --max-hold-seconds 300 \
  --min-policy-hold-seconds 5 \
  --max-samples-per-token 20 \
  --target-label-column live_executable_return_pct \
  --target-threshold-value 20 \
  --total-timesteps 12000 \
  --stop-loss -0.35 \
  --initial-equity-bnb 1.0 \
  --fixed-stake-bnb 0.1 \
  --position-fraction 0.10 \
  --max-position-fraction 0.10 \
  --include-trade-log \
  --fee-bps 100 \
  --slippage-bps 200 \
  --one-entry-per-token \
  --max-trades-per-token 1 \
  --trailing-start-pct 0.25 \
  --trailing-stop-pct 0.20 \
  --rug-sell-pressure 0.92 \
  --live-replay-profile \
  --risk-tune-max-trades 6000 \
  --risk-tune-max-drawdown-pct -30 \
  --risk-tune-min-win-rate 0.30 \
  --risk-tune-target-entry-rate 0.15 \
  --risk-tune-entry-rate-penalty 0.03 \
  --risk-tune-candidate-entry-rates 0.02,0.05,0.10,0.15,0.25,0.40,0.60,0.80 \
  --risk-tune-drawdown-penalty 0.0 \
  --catboost-iterations 220 \
  --catboost-depth 5
```

Expected: command completes and writes `data/models/20260509_live_fixed_stake_v22/hybrid_manifest.json`.

- [ ] **Step 2: Extract key metrics**

Run:

```bash
venv/bin/python - <<'PY'
import json
from pathlib import Path
p = Path("data/models/20260509_live_fixed_stake_v22/hybrid_manifest.json")
data = json.loads(p.read_text())
e = data["evaluation"]
print(json.dumps({
    "threshold": data["artifacts"]["buy_model"]["threshold"],
    "total_trades": e["total_trades"],
    "entry_rate": e["entry_rate"],
    "win_rate": e["win_rate"],
    "net_profit_bnb": e["net_profit_bnb"],
    "final_equity_bnb": e["final_equity_bnb"],
    "account_multiple": e["account_multiple"],
    "net_return_pct": e["net_return_pct"],
    "max_drawdown_pct": e["max_drawdown_pct"],
    "drawdown_within_preferred_limit": e["drawdown_within_preferred_limit"],
    "walk_forward_worst_net_return_pct": e.get("walk_forward_worst_net_return_pct"),
    "walk_forward_worst_max_drawdown_pct": e.get("walk_forward_worst_max_drawdown_pct"),
    "walk_forward_drawdown_within_preferred_limit": e.get("walk_forward_drawdown_within_preferred_limit"),
    "top_trade_profit_concentration": e.get("top_trade_profit_concentration"),
}, indent=2, ensure_ascii=False))
PY
```

Expected: output contains the fixed-stake BNB curve metrics needed for the user report.

## Task 9: Final Verification And Report

**Files:**
- No new code changes expected unless training reveals a bug.

- [ ] **Step 1: Run final full tests**

Run:

```bash
venv/bin/python -m unittest discover
```

Expected: all tests pass.

- [ ] **Step 2: Run diff check**

Run:

```bash
git diff --check
```

Expected: no output.

- [ ] **Step 3: Confirm git status**

Run:

```bash
git status --short
```

Expected: only expected untracked model output and pre-existing untracked files remain.

- [ ] **Step 4: Report clearly in Chinese**

Report:

- Code commits created.
- Training output path.
- Fixed-stake account multiple and BNB profit.
- Maximum drawdown and whether it stays within 30%.
- Trade count, entry rate, win rate.
- Walk-forward worst segment and stress replay caveats.
- Whether result looks improved, underfit, or still overfit.

