# Flow Quick-Profit Overlay Diagnostic - 2026-05-22

## Objective

Test whether the same May 22 business round should advance from the failed `entry_slippage_risk_veto` branch into a default-off flow-aware quick-profit runtime/replay overlay for v95 rejected candidates.

## Inputs

- `data/replay_reports/time_to_barrier_probe_20260521_flow_fields_live.json`
- `data/replay_reports/time_to_barrier_probe_20260522_latest_rejects.json`
- `data/replay_reports/support_action_policy_pool_20260522_flow.json`

The pooled report contains `104` rejected-signal candidates: `22` oracle quick-profit positives and `82` negatives.

## Pre-Registered Gate

Target rule:

- `prob >= 0.985`
- `flow_event_count_30s >= 2`
- `flow_buy_sell_overlap_ratio_60s <= 0.5`
- `flow_recent_seller_reentry_ratio_30s <= 0.5`

Required before runtime/replay overlay implementation:

- at least `30` selected candidates;
- at least `12` positive candidates;
- required flow fields complete across candidates.

## Result

The pooled support gate failed.

- Report decision: `missing_flow_feature_parity`
- Target selected: `13`
- Target positives: `9`
- Target negatives: `4`
- Target precision: `69.2308%`
- Required selected: `30`
- Required positives: `12`

Flow completeness:

- `flow_event_count_30s`: finite `103/104`
- `flow_buy_sell_overlap_ratio_60s`: finite `80/104`
- `flow_recent_seller_reentry_ratio_30s`: finite `71/104`

Negative controls stayed weaker but do not rescue the branch:

- `young_high_prob_clean_flow`: `4` selected, `3` positives, precision `75.0000%`
- `high_prob_volume_volatility`: `15` selected, `7` positives, precision `46.6667%`
- `young_high_prob_positive_pred`: `7` selected, `3` positives, precision `42.8571%`
- `high_prob_positive_pred`: `9` selected, `3` positives, precision `33.3333%`
- `v95_like_pred_rescue`: `3` selected, `1` positive, precision `33.3333%`

## Decision

`NO_GO_FOR_RUNTIME_OVERLAY`.

Do not implement Tasks 2-4 from the flow quick-profit plan in this business round:

- no replay/live flow alias work;
- no `buy_flow_quick_profit_overlay_*` runtime params;
- no flow quick-profit replay grid;
- no `.env`, `data/models/**`, live service, or position-sizing change.

## Lesson

The flow-aware bucket is still better than static high-score or high-PredReturn buckets, so the direction is useful for future research. It is not strong enough to justify runtime overlay work in this round because the expanded evidence is too small and the required flow fields are incomplete.
