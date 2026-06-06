# 2026-06-07 Post-Selector Live Shadow Refresh

## Purpose

After the stop/timeout flow scan, generic action-policy meta-label scan, and reverse opportunity-selector scan were all rejected, this checkpoint refreshed live attribution and action-policy shadow support before choosing any new structural branch.

This is audit-only evidence. It does not support a live switch and did not change `.env`, thresholds, sizing, model artifacts, buy/sell logic, bot or collector processes, runtime enablement, or live runtime behavior.

## Artifacts

Fresh post-close window since `2026-06-02 21:27:41`:

- `data/replay_reports/live_trade_attribution_20260607_post_selector_since_last_close.json`
- `data/replay_reports/live_trade_attribution_20260607_post_selector_since_last_close.md`
- `data/replay_reports/action_policy_live_shadow_20260607_post_selector_since_last_close.json`
- `data/replay_reports/action_policy_live_shadow_20260607_post_selector_since_last_close.md`
- `data/replay_reports/action_policy_activation_shadow_20260607_post_selector_since_last_close.json`
- `data/replay_reports/action_policy_activation_shadow_20260607_post_selector_since_last_close.md`

Cumulative shadow-only audit:

- `data/replay_reports/action_policy_live_shadow_20260607_post_selector_refresh.json`
- `data/replay_reports/action_policy_live_shadow_20260607_post_selector_refresh.md`
- `data/replay_reports/action_policy_activation_shadow_20260607_post_selector_refresh.json`
- `data/replay_reports/action_policy_activation_shadow_20260607_post_selector_refresh.md`

The cumulative full-history live-attribution JSON was intentionally not archived because it was a large all-candidate historical sample and was not needed for the current live-risk decision; the bounded attribution report is the current post-close source of truth.

## Commands

Fresh post-close attribution:

```bash
venv/bin/python scripts/probe_live_trade_attribution.py \
  --since '2026-06-02 21:27:41' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --recent-lifecycle-files 256 \
  --output-json data/replay_reports/live_trade_attribution_20260607_post_selector_since_last_close.json \
  --output-md data/replay_reports/live_trade_attribution_20260607_post_selector_since_last_close.md \
  --max-trade-sample 0 \
  --max-candidate-sample 0 \
  --force
```

Fresh post-close live shadow and activation shadow used the same `--since` bound and active model, writing the matching `action_policy_*_20260607_post_selector_since_last_close` reports.

Cumulative live shadow and activation shadow used the same active model without a `--since` bound, writing the matching `action_policy_*_20260607_post_selector_refresh` reports.

## Results

Fresh post-close attribution remained `NO_GO_FOR_LIVE_SWITCH`:

- Closed trades: `0`.
- Rejected signal decisions: `10301`.
- Per-token candidates: `1010`.
- Barrier classes: `fast_profit=36`, `fast_profit_then_collapse=30`, `flat_timeout=759`, `slow_runner=25`, `stop_first=160`.
- Recommended policies: `quick_take_profit=66`, `conditional_slow_hold=25`, `skip=919`.

Fresh post-close live shadow stayed insufficient:

- Signal count: `10302`.
- Queued signal count: `1`.
- Shadow-used `continue_hold` rows: `121`.
- Queued shadow-used rows: `1`.
- Matched trades: `0`.
- Decision: `insufficient_shadow_support`.

Fresh post-close activation shadow also stayed insufficient:

- Queued shadow-used matched trades: `0`.
- Activation hits: `0`.
- Release hits: `0`.
- Activated then stop: `0`.
- Decision: `insufficient_activation_shadow_support`.

The cumulative shadow audit found historical matched support, but it is not current live-switch evidence:

- Signal count: `284439`.
- Queued signal count: `182`.
- Shadow-used `continue_hold` rows: `2003`.
- Queued shadow-used rows: `121`.
- Queued shadow-used matched trades: `94`.
- Queued shadow-used matched net profit: `-0.004918239711871068` BNB.
- Decision: `candidate_shadow_support`.

The cumulative activation audit was mixed and net-negative:

- Queued shadow-used matched trades: `94`.
- Activation hits: `17`.
- Release hits: `7`.
- Activated then stop: `4`.
- Outcomes: `activated_profitable_no_release=6`, `activated_released=7`, `activated_then_stop=4`, `missing_path_or_anchor=6`, `never_activated_loss=67`, `never_activated_win=4`.
- Decision: `mixed_activation_shadow_support`.

## Decision

No live switch and no replay escalation from this refresh.

The fresh post-close stream has no matched shadow or activation support. The cumulative support is historical and mixed, with negative matched net profit and many never-activated losses. This confirms that the current accepted-action router remains shadow-only context, not a live-risk candidate.

`docs/model_scoreboard.md` was updated because this checkpoint changes the live-risk interpretation after the scalar/generic selector rejections: future work should not enable or micro-sweep activation thresholds from this evidence. The next structural branch needs either fresh matched shadow rows, or a richer accepted-action trade-delta / utility model that explicitly handles no-activation losses and protects the known common-trade improvements.
