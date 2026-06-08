# 2026-06-08 Post-Audit Shadow Refresh

## Live State

- Bot running: PID `62039`.
- Collector running: PID `4739`.
- `data/bot_state.json`: balance `0.001559636535526772`, `positions={}`.
- Live config remains `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, `MAX_CONCURRENT_POSITIONS=8`, and `MIN_ENTRY_VOLUME_30S=1.5`.
- Audit-only router telemetry is enabled locally with live router execution pinned off:
  - `BUY_ACTION_POLICY_ROUTER_ENABLED=false`
  - `BUY_ACTION_POLICY_ROUTER_SHADOW_AUDIT_ENABLED=true`
  - `BUY_ACTION_POLICY_ROUTER_MIN_CONFIDENCE=0.55`
  - continue-hold activation/release `0.40/0.85`
- No new paper trade appeared after the `2026-06-07 12:25:39.499918` `苹果人生` close.

Recent logs show listener catch-up/unrecognized-event warnings, but no traceback, buy/sell failure, live router load, or open-position mismatch in the sampled tails.

## Fresh Reports

Read-only reports from the post-audit restart window since `2026-06-08 15:02:20`:

- `data/replay_reports/live_trade_attribution_20260608_post_audit_shadow_refresh_entry.json` / `.md`
- `data/replay_reports/action_policy_live_shadow_20260608_post_audit_shadow_refresh_entry.json` / `.md`
- `data/replay_reports/action_policy_activation_shadow_20260608_post_audit_shadow_refresh_entry.json` / `.md`
- `data/replay_reports/action_policy_recorded_shadow_audit_20260608_post_audit_shadow_refresh_entry.json` / `.md`

Live attribution stayed `NO_GO_FOR_LIVE_SWITCH`: `0` closed trades, `583` signal decisions, and `44` per-token rejected candidates. Barrier classes were `fast_profit=1`, `fast_profit_then_collapse=2`, `flat_timeout=30`, and `stop_first=11`; no same-shape replay bucket met the minimum support gate.

The recomputed strict live-shadow report scored `583` rejected rows and found `skip=583`, `0` queued rows, `0` shadow-used rows, and `0` matched trades. Activation shadow likewise found `0` matched rows, `0` activation hits, and `0` release hits.

## Recorded Audit Bridge

The recomputed shadow report could not explain the actual in-process audit route distribution because it rebuilds router features from persisted `SIGNAL_DECISION` fields. The live bot's audit path may re-extract flow features for the shadow runtime, but those flow features are not persisted in `data/signal_audit.jsonl`. Therefore a report that recomputes routes from stored signal fields can disagree with the recorded `action_policy_shadow_*` fields.

This node added a reusable recorded-audit report path:

- `src/pipeline/action_policy_live_shadow.py`: `build_recorded_shadow_audit_report(...)` and `recorded_shadow_to_markdown_text(...)`.
- `scripts/probe_action_policy_recorded_shadow_audit.py`: CLI wrapper for JSON/Markdown reports.
- `tests/model/test_action_policy_live_shadow.py`: coverage for persisted recorded-shadow fields and CLI args.

The recorded-audit report consumed the actual in-process `action_policy_shadow_*` fields. It ran several minutes after the recomputed reports, so its `614` signal rows are not a row-for-row comparison against the recomputed report's `583` rows; the useful evidence is that the recorded fields preserve the in-process route distribution that recomputation cannot recover from persisted signal fields alone.

- Signal count: `614`.
- Rows with recorded shadow fields: `534`.
- Rows missing recorded shadow fields: `80` early post-restart rows before audited decisions were present.
- Queued signal count: `0`.
- Recorded shadow-used signals: `0`.
- Recorded shadow routes: `quick_take_profit=36`, `skip=498`.
- Recorded shadow reason counts: `non_continue_hold_route=534`.
- Matched trades: `0`.

## Hypothesis Portfolio

1. **Recorded in-process shadow telemetry bridge**: selected. Expected impact is high because future live-shadow conclusions must use the actual audit fields now being written, not a lossy recomputation path. Evidence strength is high from the route-count mismatch; falsifiability is high with a small report and tests; implementation cost is low.
2. **Class-specific rejected fast-profit selector**: deferred. The recorded audit sees `36` quick-take-profit routes, but post-audit lifecycle attribution has only `3` quick-profit-shaped candidates, below replay support. Older broad quick-profit overlays failed, so this needs a stricter class-specific selector rather than another static overlay.
3. **Accepted-action router continuation**: deferred until matched support arrives. The strict accepted-action router remains the strongest `Shadow Candidate`, but the post-audit window has `0` queued rows and `0` matched shadow rows, so another replay rerun would not add live-derived evidence yet.
4. **Replay-compatible freshness propagation**: deferred. Freshness remains `Research Alpha`, but strict replay still lacks decision-time lifecycle freshness fields; that is a larger data-surface task.

## Decision

Outcome tier: diagnostic bridge / no-switch.

The recorded-audit bridge is not a model candidate or live switch. It improves the evidence surface for future rounds by distinguishing actual in-process shadow telemetry from recomputed shadow scoring. Current post-audit telemetry has no matched support and does not justify runtime promotion, threshold changes, sizing changes, sell routing changes, or a bot restart.

`docs/model_scoreboard.md` was updated because this changes how future live-shadow evidence should be interpreted: the actual recorded audit fields are authoritative for post-enable telemetry, while recomputed reports remain useful only as offline diagnostics.
