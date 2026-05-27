# 2026-05-27 Action-Policy Router Multiroute

## Question

Can a replay-only multi-policy router improve the current v95 live-sized baseline by routing primary candidates into `skip`, `quick_take_profit`, `conditional_slow_hold`, `continue_hold`, or `lock_profit` instead of using another binary support gate?

## Research Basis

SmartSearch deep research pointed to selective classification, learning-to-defer, mixture-of-experts routing, and time-to-event / competing-risk framing as better matches than another static threshold. Key fetched sources used for the design:

- `https://arxiv.org/abs/2110.14914` / `https://arxiv.org/pdf/2110.14914.pdf`: trading selective classification frames abstention as a coverage/risk tradeoff.
- `http://proceedings.mlr.press/v119/mozannar20b/mozannar20b.pdf`: learning-to-defer supports routing difficult cases to alternate experts.
- `https://cs.nyu.edu/~mohri/pub/tdef.pdf`: two-stage deferral formalizes when a learned router should defer.
- `https://research.google/blog/mixture-of-experts-with-expert-choice-routing/`: MoE routing supports learned assignment among experts.
- `https://www.publichealth.columbia.edu/research/population-health-methods/time-event-data-analysis`: time-to-event framing supports route labels that depend on which barrier arrives first.

## Implementation

Added a read-only multi-policy router probe and a strict replay integration:

- `src/pipeline/action_policy_router_probe.py`
- `scripts/probe_action_policy_router.py`
- `scripts/run_action_policy_router_replay.py`
- replay-only support in `_run_eval_replay` for `action_policy_routes_by_episode` and `buy_action_policy_router_min_confidence`

The router is explicitly default-off and does not change live settings. It can reject base candidates with `skip` and can mark `quick_take_profit` routes so existing quick-profit exit logic handles them.

## Evidence

Shadow probe:

- `data/replay_reports/action_policy_router_probe_20260527_multiroute_best.json`
- Decision: `shadow_router_positive_replay_required`
- Validation selected `38` routes, reward `+2574.4838%`, average `+67.7496%`
- Final/latest selected `21` routes, reward `+1157.8294%`, average `+55.1347%`

Strict replay:

- `data/replay_reports/action_policy_router_replay_20260527_multiroute.json`
- Decision: `reject`
- Validation baseline `0.021094872146` BNB vs best router `0.020911793965` BNB
- Final baseline `0.005174515325` BNB vs router `0.005083918933` BNB
- Final win rate fell from `52.38%` to `50.00%`

## Diagnosis

The shadow result was positive because the probe could use decision-time flow features. In strict replay, route-map feature parity collapsed to only:

- `flow_metrics_available`
- `near_threshold_rescue_used`
- `pred_return`
- `prob`

Feature importances were only `pred_return` and `prob`. That means the route model could not use the flow separation that made the shadow probe look useful. The strict replay therefore mostly became another weak score/prob gate and rejected a small amount of profitable baseline edge.

## Decision

Reject. No live switch, no `.env`, threshold, sizing, model artifact, or bot restart change.

Next direction: do not continue tuning router confidence thresholds until replay candidate rows expose the same decision-time flow features as the accepted/rejected training reports. The next experiment should target replay/live feature parity for candidate rows, then rerun a stricter route model only if flow features are available in the actual replay scoring surface.
