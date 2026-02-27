# Listener Resilience and Topic Mapping Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Harden listener recovery behavior under transient RPC instability and fix TokenSale topic mapping so known events decode reliably without false unrecognized warnings.

**Architecture:** Keep the current WS(head) + HTTP(get_logs) role separation and patch only failure boundaries. Improve transient timeout detection by exception type, add listener-side reconnect trigger cooldown, and serialize reconnect attempts in `WSConnectionManager` with a lock + double-check. Correct the known topic hash used by listener fast-path mapping. No strategy or data-format changes.

**Tech Stack:** Python 3.10 asyncio, web3 async providers, aiohttp/websockets exception classes, unittest (`IsolatedAsyncioTestCase`), existing `src/core` listener and ws manager modules.

---

Implementation discipline: use @superpowers:test-driven-development for each task and @superpowers:verification-before-completion before final completion claims.

### Task 1: Make timeout exceptions classify as transient

**Files:**
- Modify: `tests/core/test_listener_http_pool.py`
- Modify: `src/core/listener.py`
- Test: `tests/core/test_listener_http_pool.py`

**Step 1: Write the failing test**

Add a unit test that proves `asyncio.TimeoutError()` is treated as transient even when exception message is empty.

```python
import asyncio

...

def test_timeout_error_type_is_transient(self):
    listener_cls = _load_listener_class()
    listener = listener_cls(
        w3=types.SimpleNamespace(),
        config={
            'contract_address': '0x1',
            'contract_abi': [],
            'log_http_endpoints': [],
            'log_http_weights': [],
        },
        ws_manager=None,
    )

    self.assertTrue(listener._is_timeout_or_rate_limit_error(asyncio.TimeoutError()))
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.core.test_listener_http_pool.TestListenerHttpPool.test_timeout_error_type_is_transient -v`

Expected: FAIL (`False is not true`).

**Step 3: Write minimal implementation**

In `src/core/listener.py`, update `_is_timeout_or_rate_limit_error` to first classify known timeout exception types, then fallback to message markers.

```python
@staticmethod
def _is_timeout_or_rate_limit_error(error: Exception) -> bool:
    if isinstance(error, asyncio.TimeoutError):
        return True
    ...
```

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.core.test_listener_http_pool.TestListenerHttpPool.test_timeout_error_type_is_transient -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/core/test_listener_http_pool.py src/core/listener.py
git commit -m "fix: classify timeout exceptions as transient in listener"
```

---

### Task 2: Fix TokenSale known-topic typo used by fast-path decoding

**Files:**
- Modify: `tests/core/test_listener_http_pool.py`
- Modify: `src/core/listener.py`
- Test: `tests/core/test_listener_http_pool.py`

**Step 1: Write the failing test**

Add an async test that feeds the observed TokenSale topic (`c18aa71171b358b706fe3dd345299685ba21a5316c66ffa9e319268b033c44b0`) and confirms known-topic fast-path is used (contract ABI decode path must not execute).

```python
async def test_parse_observed_tokensale_topic_uses_known_fast_path(self):
    listener_cls = _load_listener_class()
    listener = listener_cls(...)

    class _ExplodingContract:
        @property
        def events(self):
            raise AssertionError('contract events decode should not run for known topic')

    listener.contract = _ExplodingContract()

    event_log = {
        'topics': [bytes.fromhex('c18aa71171b358b706fe3dd345299685ba21a5316c66ffa9e319268b033c44b0')],
        'data': b'\x00' * 32,
        'transactionHash': b'\x01' * 32,
        'blockNumber': 123,
    }

    await listener._parse_and_process_event(event_log)
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.core.test_listener_http_pool.TestListenerHttpPool.test_parse_observed_tokensale_topic_uses_known_fast_path -v`

Expected: FAIL (falls back to contract decode path and raises assertion).

**Step 3: Write minimal implementation**

In `src/core/listener.py`, correct the `known_topics` TokenSale hash literal to:

```python
'c18aa71171b358b706fe3dd345299685ba21a5316c66ffa9e319268b033c44b0': 'TokenSale'
```

Keep normalization behavior unchanged.

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.core.test_listener_http_pool.TestListenerHttpPool.test_parse_observed_tokensale_topic_uses_known_fast_path -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/core/test_listener_http_pool.py src/core/listener.py
git commit -m "fix: correct known TokenSale topic mapping"
```

---

### Task 3: Add reconnect trigger cooldown in listener exception loop

**Files:**
- Modify: `tests/core/test_listener_http_pool.py`
- Modify: `src/core/listener.py`
- Test: `tests/core/test_listener_http_pool.py`

**Step 1: Write the failing test**

Add a deterministic unit test for a small helper (to be added) that gates reconnect attempts by time.

```python
def test_ws_reconnect_cooldown_gate(self):
    listener_cls = _load_listener_class()
    listener = listener_cls(...)

    self.assertTrue(listener._should_attempt_ws_reconnect(100.0))
    self.assertFalse(listener._should_attempt_ws_reconnect(100.2))
    self.assertTrue(listener._should_attempt_ws_reconnect(101.2))
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.core.test_listener_http_pool.TestListenerHttpPool.test_ws_reconnect_cooldown_gate -v`

Expected: FAIL (helper missing).

**Step 3: Write minimal implementation**

In `src/core/listener.py`:
1. Add fields in `__init__`:
   - `self._last_ws_reconnect_attempt_at = 0.0`
   - `self._ws_reconnect_cooldown_seconds = 1.0`
2. Add helper:

```python
def _should_attempt_ws_reconnect(self, now: float) -> bool:
    if now - self._last_ws_reconnect_attempt_at < self._ws_reconnect_cooldown_seconds:
        return False
    self._last_ws_reconnect_attempt_at = now
    return True
```

3. In `subscribe_to_events()` exception branch, call `ensure_connection()` only when helper allows it.

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.core.test_listener_http_pool.TestListenerHttpPool.test_ws_reconnect_cooldown_gate -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/core/test_listener_http_pool.py src/core/listener.py
git commit -m "fix: throttle listener reconnect triggering during ws turbulence"
```

---

### Task 4: Serialize concurrent reconnect attempts in WSConnectionManager

**Files:**
- Modify: `tests/core/test_ws_manager_scheme.py`
- Modify: `src/core/ws_manager.py`
- Test: `tests/core/test_ws_manager_scheme.py`

**Step 1: Write the failing test**

Add async test proving concurrent `ensure_connection()` calls only trigger one reconnect action.

```python
class TestWSConnectionManagerReconnect(unittest.IsolatedAsyncioTestCase):
    async def test_ensure_connection_deduplicates_concurrent_reconnects(self):
        ws_manager = _load_ws_manager_class()
        manager = ws_manager('wss://bsc.publicnode.com')
        manager.is_connected = False
        manager.w3 = None

        reconnect_mock = AsyncMock(return_value=True)
        manager.reconnect = reconnect_mock

        await asyncio.gather(*(manager.ensure_connection() for _ in range(5)))

        self.assertEqual(reconnect_mock.await_count, 1)
```

**Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.core.test_ws_manager_scheme.TestWSConnectionManagerReconnect.test_ensure_connection_deduplicates_concurrent_reconnects -v`

Expected: FAIL (multiple reconnect calls).

**Step 3: Write minimal implementation**

In `src/core/ws_manager.py`:
1. Add `self._reconnect_lock = asyncio.Lock()` in `__init__`.
2. Update `ensure_connection()` to:
   - quick health-check outside lock,
   - lock around reconnect path,
   - perform lock-internal re-check before `reconnect()`.

```python
async with self._reconnect_lock:
    if self.is_connected and self.w3:
        try:
            await self.w3.eth.block_number
            return True
        except Exception:
            self.is_connected = False
    return await self.reconnect()
```

**Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.core.test_ws_manager_scheme.TestWSConnectionManagerReconnect.test_ensure_connection_deduplicates_concurrent_reconnects -v`

Expected: PASS.

**Step 5: Commit**

```bash
git add tests/core/test_ws_manager_scheme.py src/core/ws_manager.py
git commit -m "fix: serialize concurrent ws reconnect attempts"
```

---

### Task 5: Verification sweep and regression guard

**Files:**
- Verify: `tests/core/test_listener_http_pool.py`
- Verify: `tests/core/test_ws_manager_scheme.py`
- Modify only if required by failures: `src/core/listener.py`, `src/core/ws_manager.py`

**Step 1: Run focused new tests**

Run:
- `python3 -m unittest tests.core.test_listener_http_pool.TestListenerHttpPool.test_timeout_error_type_is_transient -v`
- `python3 -m unittest tests.core.test_listener_http_pool.TestListenerHttpPool.test_parse_observed_tokensale_topic_uses_known_fast_path -v`
- `python3 -m unittest tests.core.test_listener_http_pool.TestListenerHttpPool.test_ws_reconnect_cooldown_gate -v`
- `python3 -m unittest tests.core.test_ws_manager_scheme.TestWSConnectionManagerReconnect.test_ensure_connection_deduplicates_concurrent_reconnects -v`

Expected: all PASS.

**Step 2: Run module-level regression suites**

Run:
- `python3 -m unittest tests.core.test_listener_http_pool -v`
- `python3 -m unittest tests.core.test_ws_manager_scheme -v`

Expected: all PASS.

**Step 3: Fix only failing assertions (if any)**

Apply minimal code changes only to satisfy test expectations. No unrelated refactors.

**Step 4: Re-run regression suites**

Run the two module-level commands again.

Expected: PASS without flakes.

**Step 5: Commit**

```bash
git add tests/core/test_listener_http_pool.py tests/core/test_ws_manager_scheme.py src/core/listener.py src/core/ws_manager.py
git commit -m "fix: harden listener resilience and correct sale topic mapping"
```
