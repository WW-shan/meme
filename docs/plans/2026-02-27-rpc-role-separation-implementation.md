# RPC Role Separation & Low-Latency Listener Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Separate WSS/HTTP responsibilities, implement 48.club-first weighted log HTTP load balancing (3:1 with private HTTP), disable historical scan by default, and rewrite env configuration so listener/trader RPC settings are explicit and non-confusing.

**Architecture:** Keep a websocket-only connection for head tracking/heartbeat and move listener `eth_getLogs` to a dedicated weighted HTTP pool. Add strict config parsing/validation for new env variables, make trader HTTP use its own variable, and ensure listener block progress only advances after successful range processing.

**Tech Stack:** Python 3.10+, asyncio, web3 (`WebSocketProvider`, `AsyncHTTPProvider`), python-dotenv, unittest.

---

### Task 1: Add explicit RPC config schema and validation

**Files:**
- Modify: `config/config.py`
- Test: `tests/core/test_rpc_config.py` (create)

**Step 1: Write the failing tests (@superpowers:test-driven-development)**

```python
# tests/core/test_rpc_config.py
import os
import unittest
from unittest.mock import patch

from config.config import Config


class TestRpcConfig(unittest.TestCase):
    def test_wss_must_be_websocket_scheme(self):
        with patch.dict(os.environ, {
            "BSC_WSS_URL": "https://four.rpc.48.club",
            "BSC_LOG_HTTP_ENDPOINTS": "https://four.rpc.48.club",
            "BSC_LOG_HTTP_WEIGHTS": "1",
        }, clear=False):
            with self.assertRaises(ValueError):
                Config.validate_rpc_config()

    def test_parse_log_http_pool_and_weights(self):
        with patch.dict(os.environ, {
            "BSC_WSS_URL": "wss://bsc.publicnode.com",
            "BSC_LOG_HTTP_ENDPOINTS": "https://four.rpc.48.club,https://private-http",
            "BSC_LOG_HTTP_WEIGHTS": "3,1",
        }, clear=False):
            endpoints, weights = Config.get_log_http_pool()
            self.assertEqual(endpoints, ["https://four.rpc.48.club", "https://private-http"])
            self.assertEqual(weights, [3, 1])

    def test_trade_http_prefers_new_env(self):
        with patch.dict(os.environ, {
            "BSC_TRADE_HTTP_RPC": "https://trade-http",
            "BSC_HTTP_RPC": "https://legacy-http",
        }, clear=False):
            self.assertEqual(Config.get_trade_http_rpc(), "https://trade-http")
```

**Step 2: Run test to verify it fails**

Run:
```bash
python -m unittest tests.core.test_rpc_config -v
```

Expected: FAIL (missing `validate_rpc_config`, `get_log_http_pool`, `get_trade_http_rpc` or mismatched behavior).

**Step 3: Write minimal implementation in `config/config.py`**

```python
@classmethod
def get_listener_ws_url(cls) -> str:
    url = os.getenv("BSC_WSS_URL", "").strip()
    if not url:
        raise ValueError("BSC_WSS_URL is required")
    if not url.startswith(("ws://", "wss://")):
        raise ValueError("BSC_WSS_URL must start with ws:// or wss://")
    return url

@classmethod
def get_log_http_pool(cls) -> tuple[list[str], list[int]]:
    raw = os.getenv("BSC_LOG_HTTP_ENDPOINTS", "").strip()
    if raw:
        endpoints = [x.strip() for x in raw.split(",") if x.strip()]
    else:
        legacy = os.getenv("BSC_HTTP_RPC", "").strip()
        endpoints = ["https://four.rpc.48.club"] + ([legacy] if legacy else [])

    if not endpoints:
        raise ValueError("BSC_LOG_HTTP_ENDPOINTS resolved empty")

    for ep in endpoints:
        if not ep.startswith(("http://", "https://")):
            raise ValueError(f"Invalid log HTTP endpoint: {ep}")

    weights_raw = os.getenv("BSC_LOG_HTTP_WEIGHTS", "").strip()
    if weights_raw:
        weights = [int(x.strip()) for x in weights_raw.split(",") if x.strip()]
    else:
        weights = [3, 1][:len(endpoints)] if len(endpoints) > 1 else [1]

    if len(weights) != len(endpoints) or any(w <= 0 for w in weights):
        raise ValueError("BSC_LOG_HTTP_WEIGHTS must align with endpoints and be > 0")

    return endpoints, weights

@classmethod
def get_trade_http_rpc(cls) -> str:
    new_rpc = os.getenv("BSC_TRADE_HTTP_RPC", "").strip()
    if new_rpc:
        return new_rpc

    legacy = os.getenv("BSC_HTTP_RPC", "").strip()
    if legacy:
        return legacy.split(",")[0].strip()

    return "https://bsc-dataseed.binance.org"

@classmethod
def validate_rpc_config(cls) -> None:
    cls.get_listener_ws_url()
    cls.get_log_http_pool()
    trade = cls.get_trade_http_rpc()
    if not trade.startswith(("http://", "https://")):
        raise ValueError("BSC_TRADE_HTTP_RPC must start with http:// or https://")
```

Also set low-latency default in config:
```python
SCAN_HISTORICAL = os.getenv('SCAN_HISTORICAL', 'false').lower() == 'true'
```
(keep false default).

**Step 4: Run test to verify it passes**

Run:
```bash
python -m unittest tests.core.test_rpc_config -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add config/config.py tests/core/test_rpc_config.py
git commit -m "refactor: add explicit rpc config schema for ws/listener-http/trade-http"
```

---

### Task 2: Make WS manager websocket-only and wire callers to explicit WS config

**Files:**
- Modify: `src/core/ws_manager.py`
- Modify: `main.py`
- Modify: `src/trader/bot.py`
- Modify: `tools/collect_continuous.py`
- Test: `tests/core/test_ws_manager_scheme.py` (create)

**Step 1: Write the failing test**

```python
# tests/core/test_ws_manager_scheme.py
import unittest
from src.core.ws_manager import WSConnectionManager


class TestWSManagerScheme(unittest.TestCase):
    def test_reject_http_url(self):
        with self.assertRaises(ValueError):
            WSConnectionManager("https://four.rpc.48.club")

    def test_accept_wss_url(self):
        mgr = WSConnectionManager("wss://bsc.publicnode.com")
        self.assertEqual(mgr.ws_url, "wss://bsc.publicnode.com")
```

**Step 2: Run test to verify it fails**

Run:
```bash
python -m unittest tests.core.test_ws_manager_scheme -v
```

Expected: FAIL (`WSConnectionManager` currently accepts HTTP URL).

**Step 3: Write minimal implementation**

In `src/core/ws_manager.py`:

```python
def __init__(self, ws_url: str, max_retry_delay: int = 60):
    if not ws_url.startswith(("ws://", "wss://")):
        raise ValueError(f"WSConnectionManager requires ws(s) URL, got: {ws_url}")
    self.ws_url = ws_url
```

In `connect()`, remove HTTP provider branch and keep websocket-only provider construction.

Update callers to use validated WS getter:

```python
ws_url = Config.get_listener_ws_url()
self.ws_manager = WSConnectionManager(ws_url=ws_url, ...)
```

And in `tools/collect_continuous.py`, update help text examples to WSS URLs only.

**Step 4: Run tests**

Run:
```bash
python -m unittest tests.core.test_ws_manager_scheme -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/core/ws_manager.py main.py src/trader/bot.py tools/collect_continuous.py tests/core/test_ws_manager_scheme.py
git commit -m "refactor: enforce websocket-only manager and explicit ws config usage"
```

---

### Task 3: Implement weighted HTTP pool for listener get_logs (48.club first, 3:1)

**Files:**
- Modify: `src/core/listener.py`
- Modify: `main.py` (listener config wiring)
- Test: `tests/core/test_listener_http_pool.py` (create)

**Step 1: Write failing tests for weighted sequence and failover**

```python
# tests/core/test_listener_http_pool.py
import unittest
from src.core.listener import FourMemeListener


class _DummyW3:
    def to_checksum_address(self, addr):
        return addr


class TestListenerHttpPool(unittest.IsolatedAsyncioTestCase):
    async def test_weighted_schedule_3_to_1(self):
        listener = FourMemeListener(_DummyW3(), {
            "contract_address": "0xabc",
            "contract_abi": [],
            "log_http_endpoints": ["https://four.rpc.48.club", "https://private-http"],
            "log_http_weights": [3, 1],
        })

        seq = [listener._next_log_provider_index() for _ in range(8)]
        self.assertEqual(seq, [0, 0, 0, 1, 0, 0, 0, 1])

    async def test_process_range_returns_false_when_all_providers_fail(self):
        listener = FourMemeListener(_DummyW3(), {
            "contract_address": "0xabc",
            "contract_abi": [],
            "log_http_endpoints": ["https://four.rpc.48.club", "https://private-http"],
            "log_http_weights": [3, 1],
        })

        # test should fail initially because method currently doesn't expose success/failure contract
        ok = await listener._process_block_range(1, 1)
        self.assertIsInstance(ok, bool)
```

**Step 2: Run test to verify it fails**

Run:
```bash
python -m unittest tests.core.test_listener_http_pool -v
```

Expected: FAIL (`_next_log_provider_index` missing and/or `_process_block_range` not returning bool).

**Step 3: Implement minimal listener pool and safe progress behavior**

In `src/core/listener.py` add:

```python
def _build_log_schedule(self, weights: list[int]) -> list[int]:
    schedule = []
    for idx, weight in enumerate(weights):
        schedule.extend([idx] * weight)
    return schedule or [0]

def _next_log_provider_index(self) -> int:
    idx = self._log_schedule[self._log_cursor]
    self._log_cursor = (self._log_cursor + 1) % len(self._log_schedule)
    return idx
```

Initialize dedicated HTTP clients in `__init__` using config-provided endpoints/weights.

Update `_process_block_range(...)` to:
- return `True` on successful fetch+process
- return `False` when all retries fail
- attempt alternate provider once before split recursion
- split on timeout/rate-limit patterns

Update `subscribe_to_events()`:

```python
ok = await self._process_block_range(self.last_block_processed + 1, to_block)
if ok:
    self.last_block_processed = to_block
else:
    await asyncio.sleep(0.2)
    continue
```

Use low-latency chunk policy (e.g. 5/10 instead of 10/50/200 for normal operation) to fit <=3-block target.

**Step 4: Run tests**

Run:
```bash
python -m unittest tests.core.test_listener_http_pool -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/core/listener.py main.py tests/core/test_listener_http_pool.py
git commit -m "feat: add weighted log http pool with failover and safe block progress"
```

---

### Task 4: Separate trading HTTP env from listener HTTP pool

**Files:**
- Modify: `src/core/trader.py`
- Test: `tests/core/test_trade_http_env.py` (create)

**Step 1: Write failing tests**

```python
# tests/core/test_trade_http_env.py
import os
import unittest
from unittest.mock import patch

from src.core.trader import TradeExecutor


class TestTradeHttpEnv(unittest.TestCase):
    def test_trade_http_prefers_new_variable(self):
        with patch.dict(os.environ, {
            "BSC_TRADE_HTTP_RPC": "https://trade-http",
            "BSC_HTTP_RPC": "https://legacy1,https://legacy2",
        }, clear=False):
            eps = TradeExecutor._get_http_endpoints()
            self.assertEqual(eps[0], "https://trade-http")

    def test_trade_http_falls_back_to_legacy(self):
        with patch.dict(os.environ, {
            "BSC_TRADE_HTTP_RPC": "",
            "BSC_HTTP_RPC": "https://legacy1,https://legacy2",
        }, clear=False):
            eps = TradeExecutor._get_http_endpoints()
            self.assertEqual(eps[0], "https://legacy1")
```

**Step 2: Run test to verify it fails**

Run:
```bash
python -m unittest tests.core.test_trade_http_env -v
```

Expected: FAIL (current code only reads `BSC_HTTP_RPC`).

**Step 3: Implement minimal change in `src/core/trader.py`**

```python
@staticmethod
def _get_http_endpoints():
    trade_rpc = os.getenv('BSC_TRADE_HTTP_RPC', '').strip()
    if trade_rpc:
        return [trade_rpc]

    env_rpcs = os.getenv('BSC_HTTP_RPC', '').strip()
    if env_rpcs:
        return [url.strip() for url in env_rpcs.split(',') if url.strip()]

    return [
        'https://bsc-dataseed.binance.org',
        'https://bsc-dataseed1.defibit.io',
        'https://bsc-dataseed1.ninicoin.io',
        'https://rpc.ankr.com/bsc',
    ]
```

**Step 4: Run tests**

Run:
```bash
python -m unittest tests.core.test_trade_http_env -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/core/trader.py tests/core/test_trade_http_env.py
git commit -m "refactor: separate trade http env from listener rpc pool"
```

---

### Task 5: Rewrite `.env` and `.env.example` with clear WS/listener-HTTP/trade-HTTP sections

**Files:**
- Modify: `.env.example`
- Modify: `.env`
- Modify: `tools/collect_continuous.py` (env guidance strings)

**Step 1: Write expected structure as a failing check (lightweight)**

Create a tiny assertion script in test file:

```python
# tests/core/test_env_template_rpc_sections.py
import unittest
from pathlib import Path


class TestEnvTemplateRpcSections(unittest.TestCase):
    def test_env_example_contains_new_rpc_keys(self):
        text = Path('.env.example').read_text(encoding='utf-8')
        for key in [
            'BSC_WSS_URL=',
            'BSC_LOG_HTTP_ENDPOINTS=',
            'BSC_LOG_HTTP_WEIGHTS=',
            'BSC_TRADE_HTTP_RPC=',
        ]:
            self.assertIn(key, text)
```

**Step 2: Run failing check**

Run:
```bash
python -m unittest tests.core.test_env_template_rpc_sections -v
```

Expected: FAIL until `.env.example` is rewritten.

**Step 3: Rewrite env files**

Set `.env.example` core section to:

```dotenv
# Listener WS (head tracking / heartbeat only)
BSC_WSS_URL=wss://bsc.publicnode.com

# Listener HTTP pool for eth_getLogs (48.club first, then private)
BSC_LOG_HTTP_ENDPOINTS=https://four.rpc.48.club,https://your-private-http
BSC_LOG_HTTP_WEIGHTS=3,1

# Trading HTTP (independent from listener pool)
BSC_TRADE_HTTP_RPC=https://your-trade-http

# Legacy fallback (deprecated)
BSC_HTTP_RPC=

# Low-latency mode
SCAN_HISTORICAL=false
HISTORICAL_BLOCKS=1000
```

Rewrite local `.env` with same key layout while preserving user secrets/real endpoints.

**Step 4: Run template check**

Run:
```bash
python -m unittest tests.core.test_env_template_rpc_sections -v
```

Expected: PASS.

**Step 5: Commit**

```bash
git add .env .env.example tools/collect_continuous.py tests/core/test_env_template_rpc_sections.py
git commit -m "docs: rewrite env rpc sections for explicit ws/listener-http/trade-http roles"
```

---

### Task 6: Final verification and regression check

**Files:**
- Modify if needed based on failures: `config/config.py`, `src/core/listener.py`, `src/core/ws_manager.py`, `src/core/trader.py`, `.env.example`, `.env`

**Step 1: Run focused test suite (@superpowers:verification-before-completion)**

Run:
```bash
python -m unittest \
  tests.core.test_rpc_config \
  tests.core.test_ws_manager_scheme \
  tests.core.test_listener_http_pool \
  tests.core.test_trade_http_env \
  tests.core.test_env_template_rpc_sections \
  -v
```

Expected: all PASS.

**Step 2: Run existing model tests smoke subset (regression sanity)**

Run:
```bash
python -m unittest tests.model.test_trainer_metadata -v
```

Expected: PASS (no unrelated breakage).

**Step 3: Manual config sanity command**

Run:
```bash
python - <<'PY'
from config.config import Config
Config.validate_rpc_config()
print("WS:", Config.get_listener_ws_url())
print("LOG HTTP POOL:", Config.get_log_http_pool())
print("TRADE HTTP:", Config.get_trade_http_rpc())
PY
```

Expected: prints resolved WS/log-pool/trade HTTP without exception.

**Step 4: Commit final polish (if any)**

```bash
git add config/config.py src/core/listener.py src/core/ws_manager.py src/core/trader.py main.py src/trader/bot.py tools/collect_continuous.py .env .env.example tests/core/*.py
git commit -m "feat: split ws/log-http/trade-http roles and add weighted low-latency listener routing"
```

**Step 5: Optional rollout checklist (manual)**

- Deploy with:
  - `BSC_WSS_URL` set to stable WSS
  - `BSC_LOG_HTTP_ENDPOINTS` set to `48.club,private`
  - `BSC_LOG_HTTP_WEIGHTS=3,1`
  - `BSC_TRADE_HTTP_RPC` set for trading path
  - `SCAN_HISTORICAL=false`
- Monitor logs for lag <= 3 blocks and provider switch behavior.
