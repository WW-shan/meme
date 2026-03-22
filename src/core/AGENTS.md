# CORE RUNTIME GUIDE

## OVERVIEW

Owns listener transport, WebSocket lifecycle, log-provider fallback/cooldown behavior, and trade submission transport rules.

## WHERE TO LOOK

| Topic | Location | Notes |
|---|---|---|
| Multi-provider log polling | `listener.py` | cooldown, retries, lag skip, topic fast paths |
| WS connection lifecycle | `ws_manager.py` | scheme checks, reconnect, heartbeat |
| Trade HTTP transport | `trader.py` | trade RPC selection, fixed gas policy |
| Infra contract tests | `tests/core/test_listener_http_pool.py` | behavioral spec |

## CONVENTIONS

- `listener.py` owns:
  - provider ordering and cooldown,
  - `get_logs` fallback/splitting behavior,
  - lag-skip behavior,
  - known-topic fast paths,
  - WS recovery decisions.
- `ws_manager.py` only accepts `ws://` or `wss://` URLs.
- `trader.py` keeps trade submission RPC separate from the listener HTTP log pool.
- Gas policy is config-driven and fixed; do not fall back to RPC gas quotes as the primary strategy.
- When behavior looks flaky, check `tests/core/*` first; this subtree is heavily contract-tested.

## ANTI-PATTERNS

- Passing `http://` or `https://` URLs into `WSConnectionManager`.
- Reusing trade RPC endpoints as the implicit listener log pool contract.
- Removing cooldown, lag-skip, or topic fast-path logic to simplify control flow.
- Reintroducing RPC gas quote dependence in trade submission.

## REFERENCES

- `tests/core/test_listener_http_pool.py`
- `tests/core/test_ws_manager_scheme.py`
- `tests/core/test_trade_http_env.py`
- `tests/core/test_rpc_config.py`
