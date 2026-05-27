# 2026-05-27 Post-Target Continue-Hold Overlay

## Decision

Accepted as a strict offline replay candidate; not live-switched.

- Selected candidate: `data/models/20260519_v95_v84_selective_nearmiss_gate` plus replay-only action-policy router exit overlay.
- Runtime overlay params selected by validation and confirmed on final:
  - `buy_action_policy_router_min_confidence=0.40`
  - `buy_action_policy_continue_hold_activation_pct=0.35`
  - `buy_action_policy_continue_hold_release_pct=0.75`
  - `buy_quick_profit_overlay_take_profit_pct=0.25`
  - `buy_quick_profit_overlay_max_hold_seconds=120.0`
- Strict replay report: `data/replay_reports/action_policy_router_replay_20260527_continue_hold_post_target_activation_selected_ppo.json`
- Trade-delta reports:
  - `data/replay_reports/action_policy_router_continue_hold_post_target_activation_trade_delta_validation_ppo.json`
  - `data/replay_reports/action_policy_router_continue_hold_post_target_activation_trade_delta_final_ppo.json`
- `live_switch_evidence=false`: this is an offline/replay-only candidate. Live deployment still needs a live-runtime integration plan, zero-position switch gate, and live-risk review.

## Live-First Trigger

Today's live attribution found one real closed trade since `2026-05-27T00:00:00`: `小鑫` (`0x949cd1a11aeed6a356c8b52d70edd2ebab7f4444`). It closed by `PPO_SELL100` after about `359.7s` with `+19.1031%` profit and `+0.0000344060` BNB net profit. The close was profitable, but post-exit path attribution classified it as `post_target_continuation`: it reached the first target area and later continued to a much higher MFE. The failure tag was not bad entry; it was runner retention after a target had already been reached.

Near-miss/live context in `data/replay_reports/live_trade_attribution_20260527_current.json` also showed rejected path buckets: `fast_profit=18`, `fast_profit_then_collapse=11`, `slow_runner=9`, `flat_timeout=130`, `stop_first=42`. This made a conditional post-target exit overlay more promising than another global threshold, volume, or static quick-profit change.

## Research Evidence Used

SmartSearch Deep Research evidence is saved in this directory:

- `00-deep-plan.json` and `01-search.json`: planned and executed the discovery pass for post-target continuation, triple-barrier/meta-labeling, and survival/time-to-event framing.
- `04-fetch-hudson-thames-meta-labeling.md`: supports a secondary model around a primary signal and path-dependent triple-barrier labels instead of a single unconditional rule.
- `05-fetch-mlfinpy-labeling.md`: documents triple-barrier event labeling with upper, lower, and time barriers, matching the target/stop/time path framing used here.
- `06-fetch-springer-survival.md`: supports time-to-event / survival framing for filtering or enhancing trading signals.
- `02-exa.json` and `03-zhipu.json`: attempted but blocked by missing API keys; no conclusions depend on them.

The resulting method choice was: do not force a blanket longer hold from entry. Activate the hold override only after the trade has already demonstrated target-like continuation evidence.

## Experiment Sequence

1. Code review of the existing router showed that `continue_hold` routes were only recorded at entry; only `quick_take_profit` had an exit-side effect.
2. First implementation tested a forced `continue_hold` take-profit and then a release-only overlay. It used true PPO replay under `venv/bin/python`, not the earlier system-Python fallback.
3. Release-only without post-target activation was rejected:
   - Report: `data/replay_reports/action_policy_router_replay_20260527_continue_hold_release_ppo.json`
   - Validation net profit improved slightly (`0.019254464794 -> 0.019309369660` BNB), but validation win rate fell (`84.375% -> 81.25%`) and WF worst return fell (`79.5965% -> 77.1692%`).
   - Final net profit improved (`0.006519184678 -> 0.006718348546` BNB), but win rate fell (`63.6364% -> 59.0909%`), WF worst return worsened (`-5.6055% -> -8.1578%`), and WF worst drawdown worsened (`-16.0255% -> -18.5656%`).
   - Trade deltas showed the problem: suppressing PPO sells before any achieved target can convert small/profitable exits into later losses.
4. New direction: post-target activation. The replay-only override now has an activation threshold; it suppresses sell-policy exits for `continue_hold` routes only after `peak_pnl_pct >= activation_pct`.
5. Final selected strict replay accepted the conservative post-target overlay with `activation=0.35` and `release=0.75`.

## Strict Replay Result

Validation baseline vs selected candidate:

| Metric | Baseline | Candidate |
|---|---:|---:|
| Net profit BNB | `0.019254464794` | `0.019373072111` |
| Max drawdown | `-8.1825%` | `-8.1825%` |
| Win rate | `84.3750%` | `84.3750%` |
| Total trades | `32` | `32` |
| WF worst return | `79.5965%` | `79.5965%` |
| WF worst drawdown | `-12.7265%` | `-12.7265%` |
| Stress worst return | `200.1598%` | `212.8601%` |
| Stress worst profit BNB | `0.010166721707` | `0.010811811095` |
| Stress worst drawdown | `-6.3003%` | `-6.3003%` |

Final baseline vs selected candidate:

| Metric | Baseline | Candidate |
|---|---:|---:|
| Net profit BNB | `0.006519184678` | `0.007117605059` |
| Max drawdown | `-12.9081%` | `-12.9081%` |
| Win rate | `63.6364%` | `63.6364%` |
| Total trades | `22` | `22` |
| WF worst return | `-5.6055%` | `-0.1026%` |
| WF worst drawdown | `-16.0255%` | `-14.9166%` |
| Stress worst return | `57.4526%` | `62.8240%` |
| Stress worst profit BNB | `0.002918190322` | `0.003191021780` |
| Stress worst drawdown | `-14.8055%` | `-14.8055%` |

Trade-delta attribution for the selected candidate:

- Validation: same 32 trades, `2` improved, `0` worsened, `30` unchanged, common-trade return delta `+22.5061pct`.
- Final: same 22 trades, `4` improved, `0` worsened, `18` unchanged, common-trade return delta `+113.5518pct`.

## Implementation Notes

Code changes are replay-only and default-off:

- `src/pipeline/train_hybrid.py`: added `buy_action_policy_continue_hold_activation_pct`, `buy_action_policy_continue_hold_release_pct`, and optional take-profit handling for `continue_hold` routes.
- `src/pipeline/model_replay.py`: preserved the new replay config knobs through manifest replay config.
- `scripts/run_action_policy_router_replay.py`: now searches post-target activation/release candidates and breaks metric ties by lower forced-hold intervention count.
- `tests/model/test_action_policy_router_replay.py`: covers forced take-profit, release-only behavior, pre-target sell passthrough, and post-target sell suppression.

No `.env`, model artifacts, position sizing, threshold, or live bot process was changed.

## Next Step

This round found a strict accepted offline candidate, but it is not yet a live switch. The next node should integrate or simulate the router path in the live runtime with the same decision-time feature contract, then run a live-switch-level review before any zero-position deployment.
