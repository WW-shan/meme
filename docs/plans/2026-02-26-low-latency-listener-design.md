# Low-Latency Listener & RPC Role Separation Design

Date: 2026-02-26
Status: Approved

## 1. Context and Problem

Current configuration mixes WS and HTTP responsibilities:
- `BSC_WSS_URL` is named as WS but can be passed an HTTP URL, which changes provider behavior implicitly.
- Listener `eth_getLogs` workload can run on the same connection path used for block polling, causing timeout/reconnect loops under load.
- HTTP usage for listener and trader is not clearly separated in env semantics, making operations confusing.

Observed symptoms include block lag warnings (e.g. 50+ blocks behind), `TimeExhausted`, and WS keepalive closures.

## 2. Goals

1. Keep listener lag stably at <= 3 blocks in normal conditions.
2. Disable historical scan by default for ultra-low-latency operation.
3. Enforce clear role separation:
   - WSS: head tracking / health only
   - HTTP(log): listener `eth_getLogs`
   - HTTP(trade): transaction/trading module
4. Support weighted load balancing for listener log HTTP endpoints:
   - Prefer `https://four.rpc.48.club`
   - Then use private HTTP endpoint from env
   - Ratio: 3:1
5. Rewrite env template so operators can configure without ambiguity.

## 3. Non-Goals

- No strategy/business-logic changes.
- No broad refactor outside connection/config and listener block-range retrieval path.
- No change to trading decision rules.

## 4. High-Level Architecture

### 4.1 Connection Roles

- **WS connection (single):**
  - source of latest block (`eth_blockNumber`)
  - heartbeat/connection liveness
  - must use ws/wss scheme only

- **Listener HTTP pool (weighted):**
  - dedicated for `eth_getLogs`
  - weighted round-robin (3:1): 48.club : private HTTP
  - fast failover and range splitting on timeout/rate limit

- **Trader HTTP endpoint (independent):**
  - dedicated for trade execution module
  - configured separately from listener HTTP pool

### 4.2 Data Flow

1. Listener reads latest head from WS.
2. If there are unprocessed blocks, listener computes small chunk range.
3. Listener scheduler selects HTTP endpoint by weighted RR.
4. `eth_getLogs` executes over selected HTTP provider.
5. On failure:
   - immediate retry on alternate provider once
   - if still failing, split range and retry recursively with backoff
6. Advance `last_block_processed` only after successful processing of requested range.

## 5. Configuration Design (Env)

### 5.1 New Variables

- `BSC_WSS_URL`
  - Required for listener head tracking
  - Must be `ws://` or `wss://`

- `BSC_LOG_HTTP_ENDPOINTS`
  - Comma-separated HTTP endpoints for listener `get_logs`
  - Example: `https://four.rpc.48.club,https://your-private-http`

- `BSC_LOG_HTTP_WEIGHTS`
  - Comma-separated weights aligned by index with endpoints
  - Example: `3,1`

- `BSC_TRADE_HTTP_RPC`
  - Independent HTTP endpoint for trading module

- `SCAN_HISTORICAL`
  - Default `false`

### 5.2 Compatibility

- Keep temporary compatibility for legacy `BSC_HTTP_RPC`, but mark deprecated in logs.
- Reject invalid schemes explicitly:
  - non-WS in `BSC_WSS_URL` => startup error
  - non-HTTP in log HTTP list => startup error

## 6. Listener Scheduling & Error Handling

### 6.1 Chunk Policy (Low-Latency First)

Use smaller chunks than current catch-up defaults:
- very small lag: 3-5 blocks
- moderate lag: up to 10 blocks
- avoid large 200-block pulls in normal flow

### 6.2 Weighted Load Balancing

Implement deterministic weighted round-robin sequence for endpoints:
- with weights 3:1 -> `A, A, A, B, A, A, A, B...`

### 6.3 Failure Policy

Treat as retry/split triggers:
- timeout (`TimeoutError`, `TimeExhausted`)
- node/rate-limit signals (`429`, `limit exceeded`, similar strings)

Order:
1. retry once on alternate endpoint
2. if fail, split range and retry children with bounded backoff

### 6.4 Safety

- Never mark range as processed when retrieval/processing failed.
- Preserve at-least-once semantics with existing dedup cache behavior.

## 7. Trading Module HTTP Separation

Current trade executor reads `BSC_HTTP_RPC`.
Design update:
- Trade executor should read `BSC_TRADE_HTTP_RPC` first.
- Legacy fallback to `BSC_HTTP_RPC` only for compatibility period.
- Listener log pool must not reuse trade endpoint implicitly.

## 8. Observability Requirements

Add/standardize logs and counters:
- selected provider for each `get_logs` call
- request latency (ms)
- current lag blocks
- provider switch count
- split count
- per-provider error counters

This is required to validate <=3 block target and diagnose node-level bottlenecks.

## 9. Acceptance Criteria

1. With historical scan disabled, startup begins from current head without backfill.
2. Listener runs with WS(head) + HTTP(log pool) split roles.
3. Weighted distribution approximately follows 3:1 over time.
4. During transient provider issues, system fails over and recovers automatically.
5. No false progress (no advancing `last_block_processed` on failed ranges).
6. In steady conditions, lag remains mostly <= 3 blocks.

## 10. Risk & Mitigation

- **Risk:** 48.club transient degradation.
  - **Mitigation:** immediate alternate retry + weighted fallback path.

- **Risk:** private endpoint strict rate limits.
  - **Mitigation:** low assigned weight + range splitting + bounded retries.

- **Risk:** operator misconfiguration.
  - **Mitigation:** strict startup validation and explicit role-based env naming.

## 11. Rollout Plan

1. Introduce new env variables + validation.
2. Implement listener HTTP pool scheduler and role split.
3. Switch trader config to `BSC_TRADE_HTTP_RPC` (with temporary legacy fallback).
4. Update `.env` template to reflect new model clearly.
5. Deploy and observe lag/provider metrics.

---

This design is approved by user conversation on 2026-02-26 and is ready for implementation planning.
