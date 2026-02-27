# Listener No-Stutter Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Eliminate perceived listener stutter while preserving real-time analysis by reducing event-loop blocking, controlling repeated analysis churn, and keeping listener catch-up throughput above incoming chain event rate over long runtimes.

**Architecture:** Keep listener on asyncio single-threaded control flow for order safety, but decouple heavy paths with bounded queues, adaptive chunking, and incremental collector math. Preserve real-time analysis by adding per-token short cooldown and dynamic backpressure (never disabling analysis globally), while introducing periodic lifecycle flush so long-running memory/GC pressure does not accumulate.

**Tech Stack:** Python 3 asyncio, existing web3 async stack, unittest (existing test style), project listener/bot/collector modules.

---

### Task 1: Add failing tests for adaptive catch-up chunk policy

**Files:**
- Modify: `tests/core/test_listener_http_pool.py`
- Modify: `src/core/listener.py`
- Test: `tests/core/test_listener_http_pool.py`

**Step 1: Write the failing test**

Add unit tests that assert deterministic chunk size selection from lag (gap):
- small lag (<=50) -> baseline chunk
- medium lag (>50)
- large lag (>200)
- very large lag (>500 and >1000)

Use a dedicated helper method target (to be introduced in implementation), e.g. `_compute_chunk_size(gap)`.

```python
def test_compute_chunk_size_adaptive_levels(self):
    listener = listener_cls(...)
    self.assertEqual(listener._compute_chunk_size(20), 8)
    self.assertEqual(listener._compute_chunk_size(80), 24)
    self.assertEqual(listener._compute_chunk_size(250), 64)
    self.assertEqual(listener._compute_chunk_size(700), 120)
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.core.test_listener_http_pool.TestListenerHttpPool.test_compute_chunk_size_adaptive_levels`
Expected: FAIL (helper missing or wrong values).

**Step 3: Write minimal implementation**

In `src/core/listener.py`, add `_compute_chunk_size(gap: int) -> int` and switch `subscribe_to_events` chunk assignment to use it.

Minimal policy (tunable but deterministic):
- `gap > 1000 -> 160`
- `gap > 500 -> 120`
- `gap > 200 -> 80`
- `gap > 50 -> 32`
- else `8`

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.core.test_listener_http_pool.TestListenerHttpPool.test_compute_chunk_size_adaptive_levels`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/core/test_listener_http_pool.py src/core/listener.py
git commit -m "feat: add adaptive listener catch-up chunk policy"
```

---

### Task 2: Add failing tests for alternate-provider path yielding behavior

**Files:**
- Modify: `tests/core/test_listener_http_pool.py`
- Modify: `src/core/listener.py`
- Test: `tests/core/test_listener_http_pool.py`

**Step 1: Write the failing test**

Add a test for alternate-provider success branch (`_get_logs_via_provider` first fails transiently, second returns many logs) and assert batched processing yields (`asyncio.sleep(0)`) between batches in that branch as well.

```python
async def test_alternate_provider_branch_yields_between_batches(self):
    ...
    self.assertEqual(sleep_mock.await_count, expected_yield_count)
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.core.test_listener_http_pool.TestListenerHttpPool.test_alternate_provider_branch_yields_between_batches`
Expected: FAIL (current alternate path processes full logs in one gather).

**Step 3: Write minimal implementation**

Refactor listener log dispatch into one helper used by both primary and alternate provider branches, e.g. `_process_logs_in_batches(logs)`, ensuring identical yielding semantics.

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.core.test_listener_http_pool.TestListenerHttpPool.test_alternate_provider_branch_yields_between_batches`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/core/test_listener_http_pool.py src/core/listener.py
git commit -m "fix: batch alternate-provider log processing to avoid loop stalls"
```

---

### Task 3: Add failing tests for collector incremental window update correctness

**Files:**
- Modify: `tests/model/test_data_collector_incremental_flush.py`
- Modify: `tests/model/test_data_collector_reactivation.py` (if needed for compatibility)
- Modify: `src/data/collector.py`
- Test: `tests/model/test_data_collector_incremental_flush.py`

**Step 1: Write the failing test**

Add tests validating that `volume_1min/5min/15min/30min/1h` remain correct for ordered buy events without requiring full-list rescans.

Design tests to confirm:
- values increase as events arrive within windows
- old events drop out when timestamp advances
- outputs match exact expected sums

```python
def test_window_volumes_drop_expired_events(self):
    collector = DataCollector(...)
    ...
    self.assertAlmostEqual(lifecycle["volume_1min"], expected)
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.model.test_data_collector_incremental_flush.TestDataCollectorIncrementalFlush.test_window_volumes_drop_expired_events`
Expected: FAIL after introducing assertions tied to incremental state (before implementation).

**Step 3: Write minimal implementation**

In `src/data/collector.py`:
- Extend lifecycle record with buy-volume ring/deque state fields for rolling windows.
- Update `on_token_purchase` to append volume events into incremental window structure.
- Rewrite `_update_time_window_stats` to compute window totals from maintained rolling structure (bounded recent history), not full `lifecycle['buys']` rescans.
- Keep serialized output backward compatible by excluding internal helper fields in `_serialize_lifecycle`.

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.model.test_data_collector_incremental_flush.TestDataCollectorIncrementalFlush.test_window_volumes_drop_expired_events`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/model/test_data_collector_incremental_flush.py src/data/collector.py
git commit -m "perf: make collector window volume stats incremental"
```

---

### Task 4: Add periodic lifecycle flush in runtime bot loop (long-run stability)

**Files:**
- Modify: `src/trader/bot.py`
- Create/Modify: `tests/model/test_runtime_compatibility.py` or new `tests/model/test_bot_flush_loop.py`
- Modify: `src/data/collector.py` (only if API shape adjustment is required)
- Test: chosen test file above

**Step 1: Write the failing test**

Add test that simulates bot runtime and verifies periodic call of:
`collector.flush_eligible_tokens(current_time=..., min_age_seconds=..., inactivity_seconds=...)`
with deterministic intervals while bot is active.

Use small intervals and mocked collector to avoid long waits.

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest <target test path>`
Expected: FAIL (no periodic flush loop currently).

**Step 3: Write minimal implementation**

In `src/trader/bot.py`:
- Add config fields for flush controls:
  - `collector_flush_interval_seconds` (default e.g. 30)
  - `collector_flush_min_age_seconds` (default e.g. 600)
  - `collector_flush_inactivity_seconds` (default e.g. 180)
- Add background async task `_collector_flush_loop()`.
- Start this task in `start()` alongside analysis/price loops.
- Ensure cancellation/shutdown path includes this task.

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest <target test path>`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/trader/bot.py tests/model/<target_test>.py
git commit -m "feat: add periodic collector flush loop for long-run stability"
```

---

### Task 5: Add real-time analysis cooldown + lag-aware backpressure (without disabling analysis)

**Files:**
- Modify: `src/trader/bot.py`
- Modify: `src/core/listener.py`
- Create/Modify tests: `tests/core/test_listener_http_pool.py`, `tests/model/test_runtime_compatibility.py` (or dedicated bot test)
- Test: both files above

**Step 1: Write the failing tests**

Test A (bot): repeated rapid trade events for same token should not trigger full ML analysis more often than cooldown interval.

Test B (bot/listener integration seam): when listener lag is above threshold, analysis loop remains active but reduces per-iteration token budget or enforces stricter per-token cooldown.

Keep “real-time” semantics: first event still analyzed immediately.

**Step 2: Run tests to verify they fail**

Run:
- `python3 -m unittest <bot cooldown test>`
- `python3 -m unittest <lag backpressure test>`
Expected: FAIL.

**Step 3: Write minimal implementation**

In `src/trader/bot.py`:
- Add `token_last_analyzed_at: Dict[token, float]`.
- Add base cooldown config (e.g. 1.0s).
- Add dynamic cooldown multiplier based on listener lag snapshot (from listener stats).
- Keep immediate first analysis and queue behavior.

In `src/core/listener.py`:
- Ensure `get_stats()` lag data reflects current gap sufficiently for bot backpressure decisions (e.g. add `current_block_lag` field updated in poll loop).

**Step 4: Run tests to verify they pass**

Run both target test commands again.
Expected: PASS.

**Step 5: Commit**

```bash
git add src/trader/bot.py src/core/listener.py tests/core/test_listener_http_pool.py tests/model/<target_test>.py
git commit -m "perf: add lag-aware real-time analysis cooldown"
```

---

### Task 6: Verification sweep for listener no-stutter objective

**Files:**
- Modify if needed: `src/core/listener.py`, `src/trader/bot.py`, `src/data/collector.py`
- Test: all touched test files

**Step 1: Run focused test suites**

Run:
- `python3 -m unittest tests.core.test_listener_http_pool`
- `python3 -m unittest tests.model.test_data_collector_incremental_flush`
- `python3 -m unittest tests.model.test_data_collector_reactivation`
- `python3 -m unittest tests.model.test_runtime_compatibility`

Expected: all PASS.

**Step 2: Run any additional changed-file tests**

Run test modules added in this plan (e.g. bot-specific flush/cooldown tests).
Expected: PASS.

**Step 3: Manual runtime smoke checklist (non-commit step)**

Run bot in staging/dev environment and verify logs for 10+ minutes:
- catch-up warnings frequency reduced
- no prolonged freeze before warning
- analysis lines still real-time for fresh events
- periodic flush log lines appear

**Step 4: Commit final adjustments**

```bash
git add src/core/listener.py src/trader/bot.py src/data/collector.py tests/core/test_listener_http_pool.py tests/model/test_data_collector_incremental_flush.py tests/model/test_data_collector_reactivation.py tests/model/test_runtime_compatibility.py
git commit -m "perf: reduce listener stutter under sustained load"
```

---

### Task 7: Documentation of runtime tuning knobs

**Files:**
- Modify: `config/.env.template`
- Modify: `config/config.py` (if config helpers are centralized)
- Modify: `docs/plans/2026-02-27-listener-no-stutter-implementation.md` (append final tuned defaults)
- Test: `tests/core/test_env_template_rpc_sections.py` (or new env config test)

**Step 1: Write failing test (if template contract test exists)**

Add assertions for new env knobs presence and defaults in template.

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.core.test_env_template_rpc_sections`
Expected: FAIL until template updated.

**Step 3: Write minimal implementation**

Add documented knobs:
- `LISTENER_EVENT_BATCH_SIZE`
- `ANALYSIS_TOKEN_COOLDOWN_SECONDS`
- `ANALYSIS_LAG_BACKPRESSURE_THRESHOLD`
- `COLLECTOR_FLUSH_INTERVAL_SECONDS`
- `COLLECTOR_FLUSH_MIN_AGE_SECONDS`
- `COLLECTOR_FLUSH_INACTIVITY_SECONDS`

Ensure code reads these settings with safe defaults.

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.core.test_env_template_rpc_sections`
Expected: PASS.

**Step 5: Commit**

```bash
git add config/.env.template config/config.py tests/core/test_env_template_rpc_sections.py docs/plans/2026-02-27-listener-no-stutter-implementation.md
git commit -m "docs: add no-stutter runtime tuning configuration"
```

---

Plan complete and saved to `docs/plans/2026-02-27-listener-no-stutter-implementation.md`. Two execution options:

1. Subagent-Driven (this session) - I dispatch fresh subagent per task, review between tasks, fast iteration

2. Parallel Session (separate) - Open new session with executing-plans, batch execution with checkpoints

Which approach?
