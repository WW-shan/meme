# Realtime Per-Trade Analysis Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the bot trigger analysis immediately for every trade event so first-entry timing is not lost by token-level merge.

**Architecture:** Replace the token-level pending-analysis set/event with an event-level analysis queue in `MemeBot`. Collector will enqueue one analysis token per processed trade event (including repeated same-token events), and the analysis loop will consume queue items one-by-one. Keep listener dedupe and buy-signal dedupe unchanged.

**Tech Stack:** Python 3.12, asyncio (`Queue`, task loops), unittest (`python3 -m unittest`), existing runtime in `src/trader/bot.py`.

---

Execution discipline for every task: follow @superpowers:test-driven-development (failing test first, verify fail, minimal code, verify pass, commit).

### Task 1: Introduce analysis-event queue contract (tests + core loop)

**Files:**
- Modify: `tests/model/test_runtime_compatibility.py`
- Modify: `src/trader/bot.py`

**Step 1: Write failing tests for queue-based analysis primitives**

In `tests/model/test_runtime_compatibility.py`, add:

```python
def test_enqueue_analysis_token_keeps_duplicate_events(self):
    bot_module = _load_module(
        "worktree_bot_analysis_enqueue",
        Path(__file__).resolve().parents[2] / "src" / "trader" / "bot.py",
    )

    bot = bot_module.MemeBot.__new__(bot_module.MemeBot)
    bot.analysis_event_queue_size = 8
    bot._analysis_event_queue = bot_module.asyncio.Queue(maxsize=8)

    async def _run_once():
        await bot._enqueue_analysis_token("token-1")
        await bot._enqueue_analysis_token("token-1")

    asyncio.run(_run_once())

    queued = [
        bot._analysis_event_queue.get_nowait(),
        bot._analysis_event_queue.get_nowait(),
    ]
    self.assertEqual(queued, ["token-1", "token-1"])


def test_analysis_loop_consumes_analysis_event_queue(self):
    bot_module = _load_module(
        "worktree_bot_analysis_queue_loop",
        Path(__file__).resolve().parents[2] / "src" / "trader" / "bot.py",
    )

    bot = bot_module.MemeBot.__new__(bot_module.MemeBot)
    bot.active = True
    bot.analysis_event_queue_size = 8
    bot._analysis_event_queue = bot_module.asyncio.Queue(maxsize=8)
    bot._analysis_event_queue.put_nowait("token-1")

    processed = {"count": 0}

    async def _fake_process(_token):
        processed["count"] += 1
        bot.active = False

    bot._process_token_logic = _fake_process

    async def _run_once():
        await asyncio.wait_for(bot._analysis_loop(), timeout=0.5)
        return processed["count"]

    processed_count = asyncio.run(_run_once())
    self.assertEqual(processed_count, 1)
```

**Step 2: Run tests to verify they fail**

Run:
`python3 -m unittest tests.model.test_runtime_compatibility.TestRuntimeCompatibility.test_enqueue_analysis_token_keeps_duplicate_events tests.model.test_runtime_compatibility.TestRuntimeCompatibility.test_analysis_loop_consumes_analysis_event_queue -v`

Expected: FAIL (missing `_enqueue_analysis_token`, and analysis loop still depends on `_pending_analysis`).

**Step 3: Implement minimal queue-based analysis core**

In `src/trader/bot.py`:

1. In `__init__`, add analysis queue fields:

```python
self.analysis_event_queue_size = max(1, int(config.get('analysis_event_queue_size', 20000)))
self._analysis_event_queue: asyncio.Queue = asyncio.Queue(maxsize=self.analysis_event_queue_size)
```

2. Add helper:

```python
async def _enqueue_analysis_token(self, token_address: Optional[str]):
    if not token_address:
        return
    if self._analysis_event_queue is None:
        self._analysis_event_queue = asyncio.Queue(maxsize=self.analysis_event_queue_size)
    self._analysis_event_queue.put_nowait(token_address)
```

3. Update `_analysis_loop` to consume queue items one-by-one:

```python
async def _analysis_loop(self):
    logger.info("🔬 Analysis loop started")
    if self._analysis_event_queue is None:
        self._analysis_event_queue = asyncio.Queue(maxsize=self.analysis_event_queue_size)

    while self.active:
        try:
            token = await self._analysis_event_queue.get()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Analysis loop wait error: {e}")
            continue

        try:
            await self._process_token_logic(token)
        except Exception as e:
            logger.error(f"Analysis error: {e}")

        await asyncio.sleep(0)
```

**Step 4: Re-run tests to verify pass**

Run:
`python3 -m unittest tests.model.test_runtime_compatibility.TestRuntimeCompatibility.test_enqueue_analysis_token_keeps_duplicate_events tests.model.test_runtime_compatibility.TestRuntimeCompatibility.test_analysis_loop_consumes_analysis_event_queue -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/model/test_runtime_compatibility.py src/trader/bot.py
git commit -m "refactor: switch analysis loop to event queue"
```

---

### Task 2: Trigger analysis once per trade event (collector + trade stop)

**Files:**
- Modify: `tests/model/test_runtime_compatibility.py`
- Modify: `src/trader/bot.py`

**Step 1: Write failing tests for per-trade trigger behavior**

Add to `tests/model/test_runtime_compatibility.py`:

```python
def test_collector_loop_enqueues_analysis_event_per_trade(self):
    bot_module = _load_module(
        "worktree_bot_collector_per_trade",
        Path(__file__).resolve().parents[2] / "src" / "trader" / "bot.py",
    )

    bot = bot_module.MemeBot.__new__(bot_module.MemeBot)
    bot.active = True
    bot.collector_loop_sleep = 0.01
    bot.collector_batch_size = 10
    bot.collector_events_processed = 0
    bot.analysis_event_queue_size = 16
    bot._analysis_event_queue = bot_module.asyncio.Queue(maxsize=16)
    bot._collector_event_queue = bot_module.asyncio.Queue(maxsize=16)
    bot._pending_analysis = set()
    bot._analysis_wakeup = bot_module.asyncio.Event()

    class _Collector:
        def __init__(self, owner):
            self.owner = owner

        def on_token_create(self, _evt):
            pass

        def on_token_purchase(self, _evt):
            pass

        def on_token_sale(self, _evt):
            self.owner.active = False

        def on_trade_stop(self, _evt):
            pass

    bot.collector = _Collector(bot)

    bot._collector_event_queue.put_nowait(("TokenPurchase", {"args": {"token": "token-1"}}))
    bot._collector_event_queue.put_nowait(("TokenSale", {"args": {"token": "token-1"}}))

    async def _run_once():
        await bot._collector_loop()

    asyncio.run(_run_once())

    queued = []
    while not bot._analysis_event_queue.empty():
        queued.append(bot._analysis_event_queue.get_nowait())

    self.assertEqual(queued, ["token-1", "token-1"])


def test_on_trade_stop_enqueues_analysis_token_and_closes_position(self):
    bot_module = _load_module(
        "worktree_bot_trade_stop_enqueue",
        Path(__file__).resolve().parents[2] / "src" / "trader" / "bot.py",
    )

    bot = bot_module.MemeBot.__new__(bot_module.MemeBot)
    bot.analysis_event_queue_size = 8
    bot._analysis_event_queue = bot_module.asyncio.Queue(maxsize=8)
    bot.collector = type("_Collector", (), {"on_trade_stop": lambda self, evt: None})()
    bot.positions = {"token-1": {"symbol": "T1"}}

    closed = []

    async def _fake_close(token, reason):
        closed.append((token, reason))

    bot._close_position = _fake_close

    async def _run_once():
        await bot._on_trade_stop("TradeStop", {"args": {"token": "token-1"}})

    asyncio.run(_run_once())

    self.assertEqual(bot._analysis_event_queue.get_nowait(), "token-1")
    self.assertEqual(closed, [("token-1", "GRADUATED")])
```

**Step 2: Run tests to verify they fail**

Run:
`python3 -m unittest tests.model.test_runtime_compatibility.TestRuntimeCompatibility.test_collector_loop_enqueues_analysis_event_per_trade tests.model.test_runtime_compatibility.TestRuntimeCompatibility.test_on_trade_stop_enqueues_analysis_token_and_closes_position -v`

Expected: FAIL (collector currently dedupes by token per batch; trade-stop path still writes `_pending_analysis`).

**Step 3: Implement per-event enqueue behavior**

In `src/trader/bot.py`:

1. Update `_on_trade_stop`:

```python
async def _on_trade_stop(self, event_name, event_data):
    self.collector.on_trade_stop(event_data)
    token_address = event_data.get('args', {}).get('token')
    await self._enqueue_analysis_token(token_address)
    if token_address in self.positions:
        logger.info(f"🎓 Token {token_address} Graduated! Closing position.")
        await self._close_position(token_address, reason="GRADUATED")
```

2. Update `_collector_loop` processing path:
- Remove `touched_tokens` set aggregation.
- After each event is applied to collector, enqueue that event’s token immediately.

```python
for evt_name, evt_data in batch:
    ...
    token = evt_data.get('args', {}).get('token')
    if token:
        await self._enqueue_analysis_token(token)
```

This preserves one enqueue per event, including repeated same-token events.

**Step 4: Re-run tests to verify pass**

Run:
`python3 -m unittest tests.model.test_runtime_compatibility.TestRuntimeCompatibility.test_collector_loop_enqueues_analysis_event_per_trade tests.model.test_runtime_compatibility.TestRuntimeCompatibility.test_on_trade_stop_enqueues_analysis_token_and_closes_position -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/model/test_runtime_compatibility.py src/trader/bot.py
git commit -m "feat: trigger analysis for every trade event"
```

---

### Task 3: Add full-queue backpressure for analysis enqueue

**Files:**
- Modify: `tests/model/test_runtime_compatibility.py`
- Modify: `src/trader/bot.py`

**Step 1: Write failing test for queue-full behavior**

Add to `tests/model/test_runtime_compatibility.py`:

```python
def test_enqueue_analysis_token_waits_when_queue_full(self):
    bot_module = _load_module(
        "worktree_bot_analysis_queue_backpressure",
        Path(__file__).resolve().parents[2] / "src" / "trader" / "bot.py",
    )

    bot = bot_module.MemeBot.__new__(bot_module.MemeBot)

    class _QueueStub:
        def __init__(self):
            self.awaited_put_items = []

        def put_nowait(self, _item):
            raise asyncio.QueueFull

        async def put(self, item):
            self.awaited_put_items.append(item)

        def qsize(self):
            return 1

    q = _QueueStub()
    bot.analysis_event_queue_size = 1
    bot._analysis_event_queue = q

    async def _run_once():
        await bot._enqueue_analysis_token("token-1")

    asyncio.run(_run_once())
    self.assertEqual(q.awaited_put_items, ["token-1"])
```

**Step 2: Run test to verify it fails**

Run:
`python3 -m unittest tests.model.test_runtime_compatibility.TestRuntimeCompatibility.test_enqueue_analysis_token_waits_when_queue_full -v`

Expected: FAIL (current helper only uses `put_nowait`, no await fallback).

**Step 3: Implement minimal backpressure fallback**

In `src/trader/bot.py`, update `_enqueue_analysis_token`:

```python
try:
    self._analysis_event_queue.put_nowait(token_address)
except asyncio.QueueFull:
    logger.error(
        f"❌ Analysis queue full ({self._analysis_event_queue.qsize()}/{self.analysis_event_queue_size}); "
        f"collector is backpressured for {token_address}"
    )
    await self._analysis_event_queue.put(token_address)
```

**Step 4: Re-run test to verify pass**

Run:
`python3 -m unittest tests.model.test_runtime_compatibility.TestRuntimeCompatibility.test_enqueue_analysis_token_waits_when_queue_full -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/model/test_runtime_compatibility.py src/trader/bot.py
git commit -m "fix: add backpressure fallback for analysis queue"
```

---

### Task 4: Final regression + verification

**Files:**
- Verify: `src/trader/bot.py`
- Verify: `tests/model/test_runtime_compatibility.py`
- Verify: `tests/core/test_listener_http_pool.py`
- Verify: `tests/core/test_ws_manager_scheme.py`

**Step 1: Run full runtime compatibility module**

Run:
`python3 -m unittest tests.model.test_runtime_compatibility -v`

Expected: PASS.

**Step 2: Run core listener/ws modules to ensure no regressions**

Run:
`python3 -m unittest tests.core.test_listener_http_pool tests.core.test_ws_manager_scheme -v`

Expected: PASS.

**Step 3: Run focused combined suite used for this change**

Run:
`python3 -m unittest tests.model.test_runtime_compatibility tests.core.test_listener_http_pool tests.core.test_ws_manager_scheme -v`

Expected: PASS.

**Step 4: Runtime smoke check (manual)**

Run bot in paper mode with a small live window and verify logs:
- repeated same-token trades should emit repeated `Analysis:` lines
- no repeated buy-signal explosion for same token

Suggested command (use your existing startup command/environment):
`python3 src/trader/bot.py`

Expected:
- trade event → analysis log latency visibly reduced
- same-token burst produces multiple analysis triggers

**Step 5: Commit final touch-ups (only if any changes remain)**

```bash
git add src/trader/bot.py tests/model/test_runtime_compatibility.py
git commit -m "test: finalize per-trade realtime analysis coverage"
```

---

Use @superpowers:verification-before-completion before claiming final success.