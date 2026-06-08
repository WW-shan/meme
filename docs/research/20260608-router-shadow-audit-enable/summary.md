# 2026-06-08 Router Shadow Audit Enablement

## Live State

- Bot and collector were running under `./tools/memectl` before the action.
- Precheck bot PID: `4797`; precheck collector PID: `4739`.
- `data/bot_state.json` showed balance `0.001559636535526772` BNB and `positions={}`.
- Live config stayed on `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, `MAX_CONCURRENT_POSITIONS=8`, and `MIN_ENTRY_VOLUME_30S=1.5`.
- Fresh attribution since the `2026-06-07 12:25:39.499918` `苹果人生` close still found `0` new closed trades and no live-switch evidence.

Fresh no-switch reports:

- `data/replay_reports/live_trade_attribution_20260608_post_shadow_live_evidence_entry.json` / `.md`
- `data/replay_reports/action_policy_live_shadow_20260608_post_shadow_live_evidence_entry.json` / `.md`
- `data/replay_reports/action_policy_activation_shadow_20260608_post_shadow_live_evidence_entry.json` / `.md`

These reports were generated before the local audit-only `.env` edit, so their embedded action-policy defaults reflect the pre-enable reporting context rather than the later strict-grid audit settings.

Live attribution scanned `8188` rejected signal decisions and `551` per-token candidates. Rejected-path support was `fast_profit=32`, `fast_profit_then_collapse=31`, `slow_runner=12`, `flat_timeout=381`, and `stop_first=95`. Live shadow had `8190` signals, `36` shadow `continue_hold` routes, and `0` matched rows. Activation shadow had `0` matched rows.

## Direction Decision

The strict accepted-action router from `docs/research/20260608-router-shadow-next-direction/summary.md` remained the strongest structural evidence, but it was blocked by missing current matched live-shadow rows. Generic accepted/rejected reward selectors and generic meta-label selectors were already rejected because they over-selected `flat_timeout` and `stop_first` rows. Repeating a static quick-profit overlay was also ruled out by prior rejected quick-profit/profit-lock evidence.

Selected direction: enable the existing default-off in-process action-policy router **shadow audit only**. This records `action_policy_shadow_*` fields on live `SIGNAL_DECISION` rows so future shadow reports can evaluate current live stream behavior. It does not enable live router execution.

No new SmartSearch Deep Research was opened because this node reused committed router/shadow/meta-label/uncertainty research:

- `docs/research/20260529-live-shadow-router-evaluator/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`
- `docs/research/20260521-conservative-action-policy-from-oracle-labels/summary.md`
- `docs/research/20260529-conditional-exit-early-profit-refresh/summary.md`

## Live-Risk Review

Because this required a local `.env` edit and bot restart, Codex recorded a local direction review in the active CCG task and escalated to Claude for live-risk review.

Claude session: `ff1d0c3d-7f9c-457e-a5b3-40cda834e170`.

Verdict: `PROCEED (audit-only)`.

Critical issues: none.

Main warnings and mitigations:

- Shadow prediction may add per-signal latency; monitor logs and signal timing.
- Explicitly pin `BUY_ACTION_POLICY_ROUTER_ENABLED=false`.
- Do not set quick-profit overlay live params; this audit validates route telemetry only.
- Check recent bot logs for in-flight buys before restart, not only `positions={}`.

## Runtime Action

Local `.env` was updated on this machine only. `.env` is ignored and was not staged or committed.

Audit-only values:

- `BUY_ACTION_POLICY_ROUTER_ENABLED=false`
- `BUY_ACTION_POLICY_ROUTER_SHADOW_AUDIT_ENABLED=true`
- `BUY_ACTION_POLICY_ROUTER_TRAIN_REJECTED_REPORTS=` the same four rejected train reports used by the strict-grid router candidate.
- `BUY_ACTION_POLICY_ROUTER_TRAIN_ACCEPTED_REPORTS=data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_train_enriched.json`
- `BUY_ACTION_POLICY_ROUTER_MIN_CONFIDENCE=0.55`
- `BUY_ACTION_POLICY_CONTINUE_HOLD_ACTIVATION_PCT=0.40`
- `BUY_ACTION_POLICY_CONTINUE_HOLD_RELEASE_PCT=0.85`

Dry validation before restart:

```bash
venv/bin/python -c "from config.trading_config import TradingConfig as T; T.validate(); print(T.BUY_ACTION_POLICY_ROUTER_ENABLED, T.BUY_ACTION_POLICY_ROUTER_SHADOW_AUDIT_ENABLED, T.BUY_ACTION_POLICY_ROUTER_MIN_CONFIDENCE, T.BUY_ACTION_POLICY_CONTINUE_HOLD_ACTIVATION_PCT, T.BUY_ACTION_POLICY_CONTINUE_HOLD_RELEASE_PCT); print(len(T.BUY_ACTION_POLICY_ROUTER_TRAIN_REJECTED_REPORTS), len(T.BUY_ACTION_POLICY_ROUTER_TRAIN_ACCEPTED_REPORTS))"
```

Output:

```text
False True 0.55 0.4 0.85
4 1
```

Bot restart:

```bash
./tools/memectl bot restart
```

Result: old bot PID `4797` stopped cleanly; new bot PID `62039` started. Collector remained PID `4739`.

## Verification

Post-restart checks:

- Bot running: PID `62039`.
- Collector running: PID `4739`, unchanged.
- `data/bot_state.json`: balance `0.001559636535526772`, `positions={}`.
- Startup log showed `Action policy router shadow audit loaded | routes=conditional_slow_hold,continue_hold,lock_profit,quick_take_profit,skip | features=28`.
- Postcheck log tail did not show `Action policy router loaded`, `Action policy router shadow audit disabled`, `ERROR`, `Traceback`, `BUY`, `OPEN`, `SELL`, or `CLOSE`.
- Follow-up `data/signal_audit.jsonl` verification found `129` post-restart `SIGNAL_DECISION` rows through `2026-06-08 15:20:22.464070`; the latest row contained `action_policy_shadow_*` fields and no live `action_policy_router_*` or `action_policy_continue_hold_*` fields.

## Decision

Outcome tier: audit-only shadow evaluation enabled.

This is not a live switch. It does not change model artifacts, position sizing, buy thresholds, sell routing, or live action-policy router execution. The local live bot now records router shadow telemetry that can be used by future no-switch attribution and activation-shadow reports.

`docs/model_scoreboard.md` was updated because this changes the next live-shadow evidence path. `.env.example` was not changed because the required env knobs and safe default-off contract already exist there.
