# 2026-05-27 Action-Policy Router Flow Alias Replay

## Question

Did the previous multi-policy action router fail only because strict replay candidate rows lacked the `flow_*` decision-time fields used by the shadow probe?

## Change

Added replay-side aliasing from feature extractor names to the router training report names:

- `volume_30s` / `sell_volume_30s` -> `flow_buy_sell_ratio_30s`
- `total_flow_volume_*` -> `flow_total_volume_*`
- `sell_pressure_*` -> `flow_sell_pressure_*`
- `signed_imbalance_*` -> `flow_signed_imbalance_*`
- `buy_sell_overlap_ratio_60s`, `recent_seller_reentry_ratio_30s`, and `buyer_set_churn_10s_vs_prev50s` -> matching `flow_*` names

The router replay script now forces `include_flow_features=true` for this offline research path. This is not a live config change.

## Evidence

Report:

- `data/replay_reports/action_policy_router_replay_20260527_flow_alias.json`

Feature parity recovered. The route model now sees real flow features including:

- `flow_buy_sell_ratio_30s`
- `flow_total_volume_60s`
- `flow_total_volume_10s`
- `flow_signed_imbalance_30s`
- `flow_buy_sell_ratio_10s`
- `flow_buy_volume_10s`

Top importances moved from only `pred_return` / `prob` to a mixed score + flow model:

- `pred_return`: `0.3337`
- `prob`: `0.2987`
- `flow_buy_sell_ratio_30s`: `0.1241`
- `flow_total_volume_60s`: `0.0508`
- `flow_total_volume_10s`: `0.0500`

## Result

Decision: reject.

Validation:

- Baseline net profit: `0.021094872146` BNB
- Best alias router net profit: `0.018628768892` BNB
- Baseline trades: `32`
- Router trades: `30`
- Router signals / entries / rejects: `47 / 30 / 11`

Final confirmation:

- Baseline net profit: `0.005174515325` BNB
- Router net profit: `0.004750771325` BNB
- Baseline win rate: `52.38%`
- Router win rate: `45.00%`
- Router signals / entries / rejects: `26 / 20 / 6`

## Diagnosis

The alias fix answered the feature-parity question: replay can now score the same flow-style features as the shadow probe. The remaining failure is policy structure. The router used `skip` as a hard entry rejection and removed profitable baseline edge. It also produced `0` quick-profit overlay entries in the strict replay, so it did not add a compensating exit improvement.

Do not tune router confidence thresholds further as a main branch. The next useful direction is a positive-only or pass-through router: treat `skip` as "keep baseline behavior", and only let high-confidence positive routes modify exits or overlays after a baseline entry is already allowed.

## Decision

No live switch. No `.env`, threshold, sizing, model artifact, or bot restart change.
