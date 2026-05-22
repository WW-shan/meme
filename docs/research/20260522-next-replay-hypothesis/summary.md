# Next Replay Hypothesis Gate

Generated: `2026-05-22 11:03:07 +0800`

Contract: read-only diagnostic gate; no live model, runtime configuration, `.env`, threshold, sizing, or bot restart change.

## Live State

- Bot and collector are running.
- `data/bot_state.json` balance: `0.003471730065131376` BNB.
- Open positions: `0`.
- Latest real close remains `2026-05-21 20:42:26.327946`, `币安队长`, `TIME_EXIT`, net `-3.0418340289465923e-05` BNB.
- No new real `OPEN` or `CLOSE` exists after that close.

## Recent Signal State

Last `200` `SIGNAL_DECISION` rows:

- `buy_model_reject=91`
- `near_threshold_pred_return_below_min=86`
- `entry_volume_30s_below_min=12`
- `pred_return_below_min=9`
- `entry_price_volatility_below_min=2`

The newest high-probability rejects are mostly high-probability but low-`PredReturn` signals. They do not justify global threshold lowering, broad near-rescue widening, or another static entry overlay.

## Prior Work Reused

This round reuses committed research instead of running a new SmartSearch pass:

- `docs/research/20260521-post-target-exit-state/summary.md`
- `docs/research/20260521-conditional-exit-flow-state/summary.md`
- `docs/research/20260522-post-ci-research-round/summary.md`

The new angle is the next replay decision: whether the latest live state supports implementing a default-off giveback guard after `+25%` MFE.

## Second Perspective

External Claude analysis session `524ac560-40e4-4f1f-93bb-f1cf720bbdbe` recommended not rerunning `scripts/probe_conditional_exit_feasibility.py`, because the key gate is deterministic with the current frozen train/validation/final split and no new live closes. Rerunning the script would only refresh timestamps, not create new evidence.

## Gate Result

Source feasibility report: `docs/research/20260521-conditional-exit-flow-state/10-exit-state-attribution.json`.

| Bucket | Train positives | Validation positives | Final positives | Live positives | Decision |
|---|---:|---:|---:|---:|---|
| `post_target_collapse_or_live_mfe_giveback` | `5` | `0` | `4` | `3` | NO-GO |

Decision: `NO_GO_FOR_GIVEBACK_GUARD_REPLAY_IMPLEMENTATION`.

Reason: the live and final shapes are real, but validation has `0` post-target collapse positives. Implementing a giveback guard now would select from final/live evidence without validation support, which is exactly the overfit path the goal process forbids.

## Closeout Decision

Do not switch live, do not change `.env`, do not change model artifacts, do not change runtime overlays, and do not restart the bot.

The next useful path is data accumulation or a structurally different exit-state label/validation design after new lifecycle data exists. The scoreboard is updated so this round is not repeated as another "refresh feasibility" loop.
