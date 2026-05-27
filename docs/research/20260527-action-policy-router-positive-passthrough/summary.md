# 2026-05-27 Action-Policy Router Positive Pass-Through

## Question

Could the action router become useful if `skip`, missing route, low confidence, and unsupported route decisions pass through to the baseline instead of rejecting entries, leaving only high-confidence positive routes to modify behavior?

## Change

Added a default-off replay parameter:

- `buy_action_policy_router_skip_passthrough`

When enabled, the router no longer rejects on `skip`, missing route, low confidence, or unsupported route. Those cases preserve baseline behavior. The router replay script enables this only for offline research and sweeps lower confidence floors:

- `0.40`
- `0.45`
- `0.50`
- `0.55`

## Evidence

Report:

- `data/replay_reports/action_policy_router_replay_20260527_positive_passthrough.json`

The prior hard-rejection damage was removed. Validation and final primary metrics tied baseline at the selected point:

- Validation net profit: `0.021094872146` BNB baseline vs `0.021094872146` BNB pass-through router
- Validation trades: `32` vs `32`
- Final net profit: `0.005174515325` BNB baseline vs `0.005174515325` BNB pass-through router
- Final trades: `21` vs `21`

## Result

Decision: reject.

The pass-through router did not produce positive overlay activity on actual accepted entries:

- Validation `action_policy_router_quick_take_profit_entry_count`: `0`
- Final `action_policy_router_quick_take_profit_entry_count`: `0`

Stress still weakened:

- Validation stress worst net profit: `0.011148541483` baseline vs `0.009316506809` pass-through router
- Final stress worst net profit: `0.001874747768` baseline vs `0.001844250439` pass-through router

## Diagnosis

The route model has flow feature parity and no longer deletes baseline primary entries, but its positive routes do not line up with the actual entry indices used by strict replay. Most real entry-side router activity is no-op `continue_hold` / pass-through. The `quick_take_profit` route exists in the broad route maps, but not on the actual accepted entries in the strict replay path.

Do not continue confidence sweeps on the all-candidate route map. The next useful direction should train or diagnose on actual baseline entry indices / trade logs, then test a post-entry exit overlay where the label and action surface match the trades that the live-sized replay actually opens.

## Decision

No live switch. No `.env`, threshold, sizing, model artifact, or bot restart change.
