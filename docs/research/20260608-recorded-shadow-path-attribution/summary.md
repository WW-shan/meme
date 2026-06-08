# Recorded Shadow Path Attribution

Date: 2026-06-08

## Decision

Outcome: rejected recorded `quick_take_profit` path precision. This is not a model pass, not a Shadow Candidate, and not live-switch evidence.

The in-process recorded action-policy shadow route distribution is useful telemetry, but recorded `quick_take_profit` route counts are not sufficient direction evidence on their own. Since the audit restart anchor `2026-06-08 15:02:20`, recorded `quick_take_profit` routes had enough path support (`108` path-evaluable rows) but only `22/108` quick-profit-shaped paths, precision `0.2037037037037037`, below the default `0.6` report gate.

## Evidence

- Report: `data/replay_reports/action_policy_recorded_shadow_path_attribution_20260608_post_chain_lag_reject_direction.json`
- Markdown: `data/replay_reports/action_policy_recorded_shadow_path_attribution_20260608_post_chain_lag_reject_direction.md`
- Context live attribution: `data/replay_reports/live_trade_attribution_20260608_post_chain_lag_reject_direction.json` / `.md`
- Context recorded shadow audit: `data/replay_reports/action_policy_recorded_shadow_audit_20260608_post_chain_lag_reject_direction.json` / `.md`
- Context activation shadow: `data/replay_reports/action_policy_activation_shadow_20260608_post_chain_lag_reject_direction.json` / `.md`
- Decision: `rejected_recorded_quick_take_profit_path_precision`
- Runtime behavior changed: `false`
- Live switch evidence: `false`
- Signals since anchor: `2325`
- Rows with recorded shadow fields: `2245`
- Path-evaluable recorded rows: `2245`
- Missing path count: `0`
- Recorded routes: `continue_hold=4`, `quick_take_profit=108`, `skip=2133`

Recorded `quick_take_profit` route path mix:

- `fast_profit=10`
- `fast_profit_then_collapse=12`
- `flat_timeout=25`
- `slow_runner=8`
- `stop_first=53`
- Quick-profit-shaped paths: `22`
- Quick-profit precision: `0.2037037037037037`

The broader recorded window still contains quick-profit-shaped rejected paths (`283` recommended quick-take-profit paths across all recorded routes), but the recorded route assignment did not isolate them well. Most quick-profit-shaped paths were still under recorded `skip` (`260`), while the recorded `quick_take_profit` route included many `stop_first` and `flat_timeout` cases.

## Implementation Notes

Added a read-only recorded-route path attribution probe:

- `scripts/probe_action_policy_recorded_shadow_path_attribution.py`
- `src.pipeline.action_policy_live_shadow.build_recorded_shadow_path_attribution_report`
- `src.pipeline.action_policy_live_shadow.recorded_shadow_path_to_markdown_text`

The implementation reuses the existing `time_to_barrier_probe.score_signal_time_to_barrier` classifier, so path classes remain consistent with live attribution reports. It consumes actual recorded `action_policy_shadow_*` fields instead of recomputing router routes from persisted signal fields.

## Scoreboard

`docs/model_scoreboard.md` was updated because this result changes the quick-profit next-direction interpretation. No model metrics changed, no runtime live-risk interpretation was promoted, and no live config changed.

## Next Step

Do not run another broad quick-profit replay from recorded `quick_take_profit` route counts. If quick-profit is revisited, it needs a separate decision-time selector that finds the `283` quick-profit-shaped paths without carrying the high stop-first/flat-timeout contamination seen in recorded route `quick_take_profit`.
