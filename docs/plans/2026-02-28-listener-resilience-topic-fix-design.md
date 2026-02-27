# Listener Resilience & Topic Mapping Fix Design

Date: 2026-02-28
Status: Approved

## 1. Context and Evidence

Recent production logs show three concurrent issues in listener runtime behavior:

1. **HTTP get_logs timeout path still causes repeated range failure and lag growth**
   - Stack traces originate at `src/core/listener.py` `_process_block_range()` and `_get_logs_via_provider()`.
   - Underlying exceptions are `asyncio.TimeoutError` (often with inner `CancelledError` from `aiohttp`) on HTTP providers.
   - Resulting symptoms: repeated `Failed to process blocks ... will retry on next poll` and sustained lag warnings (`Listener ~70 blocks behind`).

2. **WS disconnects occur, but current reconnect path does recover**
   - `ConnectionClosedError` appears while polling `w3.eth.block_number` on WS.
   - `WSConnectionManager.ensure_connection()` / `reconnect()` successfully re-establishes connection shortly after.
   - This is a resilience/turbulence issue, not a fatal persistent outage.

3. **Known topic mapping mismatch causes false "Unrecognized event" warnings**
   - Runtime warning includes topic: `c18aa71171b358b706fe3dd345299685ba21a5316c66ffa9e319268b033c44b0`.
   - Current `known_topics` entry in `src/core/listener.py` uses `c18aa71171b358b706fe33dd345299685ba21a5316c66ffa9e319268b033c44b0` (typo and invalid 65-char length).
   - This breaks fast-path recognition for that sale topic variant.

Additionally, repeated "New Token Detected" logs for the same symbol are observed; this is tracked separately and intentionally out of scope for this minimal resilience patch.

## 2. Goals

1. Improve listener robustness under transient HTTP/WS instability with minimal code changes.
2. Ensure timeout-style HTTP failures are consistently treated as transient and routed through existing retry/failover/split logic.
3. Fix topic mapping typo so known event fast-path works reliably.
4. Keep all existing business logic, strategy behavior, and RPC role separation semantics unchanged.

## 3. Non-Goals

- No strategy/trading rule changes.
- No large architecture rewrite of listener polling model.
- No broad refactor of collector token lifecycle behavior.
- No schema/env variable changes.

## 4. Proposed Design

### 4.1 WS Reconnect Concurrency Guard

File: `src/core/ws_manager.py`

- Add an internal reconnect mutex (e.g. `self._reconnect_lock = asyncio.Lock()`).
- Update `ensure_connection()` to follow a double-check pattern:
  1. fast health check outside lock,
  2. acquire lock only when reconnection seems needed,
  3. re-check health inside lock,
  4. reconnect only if still unhealthy.

**Reasoning:** listener loop and heartbeat loop can concurrently call `ensure_connection()`. Guarding reconnect avoids duplicate disconnect/connect sequences during turbulence.

### 4.2 Listener Reconnect Trigger Cooldown

File: `src/core/listener.py`

- Add a short reconnect trigger cooldown timestamp (monotonic clock based).
- In `subscribe_to_events()` exception branch, avoid calling `ws_manager.ensure_connection()` on every immediate repeated exception; enforce minimal interval between reconnect attempts.

**Reasoning:** prevents reconnect hammering during bursty transient WS errors while preserving current recovery behavior.

### 4.3 Timeout Classification Hardening for get_logs

File: `src/core/listener.py`

- Expand transient error detection so timeout exceptions are recognized by type in addition to message string matching.
- Include at least:
  - `asyncio.TimeoutError`
  - timeout-like chained exceptions surfaced by HTTP stack (including `CancelledError` wrapped into timeout paths)

**Reasoning:** current message-based detection can miss real transient timeout failures, causing fallback/split logic to be skipped too often.

### 4.4 Correct Known Topic Hash Mapping

File: `src/core/listener.py`

- Fix `known_topics` TokenSale key to the observed valid 64-char topic:
  - `c18aa71171b358b706fe3dd345299685ba21a5316c66ffa9e319268b033c44b0`
- Keep existing normalization behavior (`TokenSale` family -> normalized `TokenSale`) unchanged.

**Reasoning:** removes false unrecognized warnings and restores fast-path decode for that event variant.

## 5. Data Flow Impact

- No new external inputs.
- No persisted data format changes.
- Listener processing flow remains:
  1. WS block head poll
  2. HTTP get_logs range fetch
  3. process logs
- Only resilience behavior is tightened at boundary failure points.

## 6. Testing Strategy

Target tests (unit-level, minimal scope):

1. **Transient timeout classification test**
   - Verify timeout exception path is classified as transient and follows existing alternate provider / split behavior.

2. **Known topic mapping test**
   - Feed event log with corrected topic hash and verify it is handled through known fast-path rather than unrecognized warning path.

3. **Reconnect concurrency test**
   - Simulate concurrent `ensure_connection()` calls and assert reconnect path is executed once (or at least de-duplicated by lock semantics).

Run existing listener/ws manager test suites to prevent regressions.

## 7. Risks and Mitigations

- **Risk:** Slightly slower reconnect trigger due to cooldown.
  - **Mitigation:** Keep cooldown short (e.g., ~1s), preserving responsiveness.

- **Risk:** Over-broad transient classification could hide hard failures.
  - **Mitigation:** Keep non-transient logging intact and do not suppress exception telemetry.

- **Risk:** Topic correction might affect old assumptions.
  - **Mitigation:** normalization output remains unchanged (`TokenSale`), only recognition key corrected.

## 8. Acceptance Criteria

1. Topic `c18aa71171b358b706fe3dd345299685ba21a5316c66ffa9e319268b033c44b0` is recognized as known sale event (no false unrecognized warning for this topic).
2. Timeout failures in `get_logs` are consistently treated as transient and routed through retry/failover/split path.
3. WS disconnect recovery remains successful and avoids duplicate reconnect storms under concurrent callers.
4. Existing listener and ws-manager tests pass with added coverage.

---

This design reflects validated runtime evidence and is intentionally scoped as a minimal resilience patch.