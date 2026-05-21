# Requirements

## User Workflow Contract

- This is one full business/research/experiment/cutover round, not a micro task.
- Do not open another CCG task while this one is active.
- Before ending the round, explicitly finish the loop: analysis, plan, implementation/probe, review, verification, research report, scoreboard update, archive, commit, push.
- Give external Claude analysis/review enough time; do not treat one slow response as a failed round, and do not open a new task while waiting.
- Do not edit `docs/goals/**` in this round.
- Do not change `.env`, live services, position sizing, or model artifacts unless replay evidence passes strict live-switch gates.

## Current Objective

Continue optimizing the active v95 model/live-trading stack toward better real-money performance. The previous round rejected direct runtime overlay promotion from support-only flow evidence, but found a post-hoc active-flow shape worth testing in replay.

## This Round's Hypothesis

A replay-integrated, pre-registered, default-off quick-profit overlay that only rescues young, high-probability, active-flow candidates may recover some missed runner/scalp opportunities without the over-expansion and drawdown failures seen in broader quick-profit overlays.

## Pre-registered Candidate Shape

Keep v95 primary and near-rescue behavior unchanged. Add optional active-flow filters only to quick-profit overlay rescue candidates:

- `buy_quick_profit_overlay_min_prob >= 0.985`
- young candidates: `buy_quick_profit_overlay_max_age_seconds <= 60`
- existing quality filters: positive bounded `PredReturn`, `volume_30s`, and `price_volatility`
- active-flow proxy filters available in the v95 replay schema: minimum `total_buys`, maximum `buy_sell_overlap_ratio_60s`, and maximum `recent_seller_reentry_ratio_30s`
- keep 10% position sizing and strict max 8 positions unchanged
- keep overlay default-off unless all new params are explicitly supplied by replay/runtime config

## Gates

- Replay reports must remain research evidence until validation/final/walk-forward/stress gates pass.
- Any live switch requires better profit without unacceptable trade-count expansion, drawdown, win-rate, walk-forward, or stress degradation versus current v95 replay baseline.
- If validation/final gates fail, stop as `NO_GO`, document the reason, and archive/commit/push.
