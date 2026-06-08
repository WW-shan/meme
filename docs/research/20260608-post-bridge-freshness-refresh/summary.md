# 2026-06-08 Post-Bridge Freshness Refresh

## Live State

- Bot running: PID `62039`; collector running: PID `4739`.
- Both services remain in the expected `meme-bot` and `meme-collector` tmux sessions.
- `data/bot_state.json`: balance `0.001559636535526772`, `positions={}`.
- Live config remains unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, `MAX_CONCURRENT_POSITIONS=8`, `MIN_ENTRY_VOLUME_30S=1.5`.
- Router live execution remains off and audit-only shadow remains on: `BUY_ACTION_POLICY_ROUTER_ENABLED=false`, `BUY_ACTION_POLICY_ROUTER_SHADOW_AUDIT_ENABLED=true`.
- No new real paper trade appeared after the `2026-06-07 12:25:39.499918` `苹果人生` trailing-stop close.

Recent logs show active token detection and listener catch-up diagnostics, with no sampled traceback, buy/sell failure, open-position mismatch, or live router execution evidence.

## Fresh Reports

Read-only refresh reports from the post-audit window since `2026-06-08 15:02:20`:

- `data/replay_reports/live_trade_attribution_20260608_post_bridge_direction_refresh.json` / `.md`
- `data/replay_reports/action_policy_recorded_shadow_audit_20260608_post_bridge_direction_refresh.json` / `.md`
- `data/replay_reports/signal_freshness_split_stability_20260608_post_bridge_direction_refresh.json` / `.md`

Live attribution stayed `NO_GO_FOR_LIVE_SWITCH`: `0` closed trades, `957` signal decisions, and `81` per-token rejected candidates. Barrier classes were `fast_profit=1`, `fast_profit_then_collapse=4`, `slow_runner=1`, `flat_timeout=58`, and `stop_first=17`; same-shape quick-profit and slow-runner support remained below the replay trigger.

Recorded in-process shadow audit stayed insufficient: `957` rejected decisions, `877` rows with recorded shadow fields, `80` early rows missing audit fields, routes `quick_take_profit=47` and `skip=830`, `0` queued rows, `0` recorded shadow-used rows, and `0` matched trades.

Signal-level freshness split stability remained `Research Alpha`. It scanned `81` freshness candidates and selected `lifecycle_status_staleness_seconds >= 0.015399` with stable rejected-only correct-skip behavior:

- Train: `48` candidates; selected `16`, all correct skips (`12` flat-timeout, `4` stop-first).
- Validation: `16` candidates; selected `4`, all correct skips (`3` flat-timeout, `1` stop-first).
- Final: `17` candidates; selected `1`, a flat-timeout correct skip.
- All selected counts: `21`; opportunity misses: `0`.

## Prior Research Reused

No new SmartSearch Deep Research was needed because this refresh reused the existing SmartSearch-backed execution-freshness and uncertainty-gate research. The new live-derived angle is the larger post-audit rejected-signal window after the recorded-shadow audit bridge.

Relevant prior summaries:

- `docs/research/20260530-execution-freshness-shadow-evaluator/summary.md`
- `docs/research/20260608-signal-context-freshness-bridge/summary.md`
- `docs/research/20260608-strict-freshness-sample-bridge/summary.md`
- `docs/research/20260608-freshness-replay-acceptance-gate/summary.md`

## Hypothesis Portfolio

1. **Replay-compatible freshness propagation**: selected as the next structural direction. Expected impact remains high because freshness repeatedly isolates loss/correct-skip buckets without increasing sizing, and the current blocker is a known replay-surface gap rather than a failed signal. Evidence strength is medium-high from repeated Research Alpha and the fresh split-stable rejected-only result; falsifiability is high through strict replay context coverage and validation/final gate checks; implementation cost is medium.
2. **Class-specific quick-profit rejected selector**: deferred. Post-bridge attribution has only `5` quick-profit-shaped rejected candidates, below the same-shape replay trigger, and older broad quick-profit overlays already failed.
3. **Accepted-action router continuation**: deferred. The strict router remains prior `Shadow Candidate` evidence, but current audit telemetry has `0` queued rows and `0` matched shadow-used rows, so a rerun would not add live-derived support yet.
4. **Recorded-shadow route tuning**: deferred. Recorded audit fields are now authoritative, but current recorded routes are all non-used rejected rows with no matched outcome support.

## Decision

Outcome tier: `Research Alpha` refresh / no-switch.

The post-bridge evidence does not justify runtime promotion, threshold changes, sizing changes, model changes, sell routing changes, or a bot restart. Freshness remains the best structural path, but the selected post-bridge rule is rejected-only and final support is only one selected candidate. The next falsifiable step is to make or audit a strict replay-compatible freshness surface for `lifecycle_status_staleness_seconds` / decision-time lifecycle freshness before any shadow promotion.

`docs/model_scoreboard.md` was updated because this refresh changes the next-direction priority: continue freshness as a structural replay-surface task, not another runner-retention or quick-profit micro-sweep.
