# CONFIG GUIDE

## OVERVIEW

Owns env contract shape, RPC role separation, trading toggles, risk knobs, and ABI loading.

## WHERE TO LOOK

| Topic | Location | Notes |
|---|---|---|
| Env template | `.env.example` | Required keys and comments are contract-tested |
| Listener / RPC config | `config.py` | `LISTENER_MODE`, RPC pools, ABI path, lag-skip |
| Trading knobs | `trading_config.py` | gas, slippage, stop-loss, risk limits |
| Contract checks | `tests/core/test_env_template_rpc_sections.py` | guards template content |
| RPC behavior checks | `tests/core/test_rpc_config.py` | validates schemes and fallbacks |

## CONVENTIONS

- `.env.example` is the source template for env keys.
- `config.py` owns:
  - `BSC_WSS_URL`
  - `BSC_LOG_HTTP_ENDPOINTS`
  - `BSC_TRADE_HTTP_RPC`
  - legacy `BSC_HTTP_RPC` fallback
  - listener lag-skip and provider cooldown settings
  - ABI loading from `CONTRACT_ABI_PATH`
- `trading_config.py` owns trading enablement and risk/gas/slippage thresholds.
- Keep role separation explicit: listener WS != listener log HTTP pool != trade HTTP RPC.
- If a new env knob changes runtime behavior, update both code and `.env.example`.

## ANTI-PATTERNS

- Treating `BSC_HTTP_RPC` as the preferred path when role-separated keys exist.
- Adding env-driven behavior only in code and not in `.env.example`.
- Moving trading risk settings into runtime modules.
- Hiding ABI or RPC fallback logic outside `config.py`.
- Committing secrets; `PRIVATE_KEY` is runtime config only.

## NOTES

- Config files define contracts; they should not absorb listener, bot, or dataset orchestration.
- For downstream runtime behavior, pair this file with `src/core/AGENTS.md`, `src/trader/AGENTS.md`, or `tools/AGENTS.md`.
