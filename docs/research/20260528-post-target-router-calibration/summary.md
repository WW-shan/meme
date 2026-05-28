# Post-Target Router Calibration Grid

## Question

After rejecting activation-gated lock-profit, can explicit calibration of `router_min_confidence`, `continue_hold_activation_pct`, and `continue_hold_release_pct` beat the current release-only post-target `continue_hold` candidate?

## Research Basis

SmartSearch evidence saved in this directory:

- `00-doctor.json`
- `00-deep-plan.json`
- `01-search.json`
- `02-fetch-conformal-off-policy.md`
- `03-fetch-conservative-ope.md`
- `04-fetch-conformalized-quantile-regression.md`
- `05-fetch-conformal-decision-theory.md`

The useful takeaway is conservative calibration discipline:

- evaluate a target policy offline before live deployment,
- prefer interval / lower-bound thinking over point estimates,
- calibrate decision aggressiveness directly against realized risk and utility.

## Experiment

Grid:

- `docs/research/20260528-post-target-router-calibration/calibration_grid.json`
- `36` release-only candidates
- `router_min_confidence`: `0.35`, `0.40`, `0.45`, `0.50`
- `continue_hold_activation_pct`: `0.30`, `0.35`, `0.45`
- `continue_hold_release_pct`: `0.70`, `0.75`, `0.85`

Command:

```bash
venv/bin/python scripts/run_action_policy_router_replay.py \
  --output data/replay_reports/action_policy_router_replay_20260528_post_target_calibration_grid.json \
  --candidate-grid-json docs/research/20260528-post-target-router-calibration/calibration_grid.json \
  --force
```

## Result

Replay output: `decision=accept`, `candidates=36`.

This is not a new best. It is a plateau:

- Every candidate passed the acceptance gate.
- Only two unique validation net profits appeared: `0.019373072110709603` and `0.019311974285645322` BNB.
- The selected final candidate net profit stayed `0.007592630952680585` BNB, exactly matching the prior accepted release-only result.

Selected tie:

- `buy_action_policy_router_min_confidence=0.35`
- `buy_action_policy_continue_hold_activation_pct=0.35`
- `buy_action_policy_continue_hold_release_pct=0.70`
- `buy_quick_profit_overlay_take_profit_pct=0.25`
- `buy_quick_profit_overlay_max_hold_seconds=120.0`

Validation baseline vs selected:

- Net profit BNB: `0.0192544647942539` -> `0.019373072110709603`
- Total trades: `32` -> `32`
- Win rate: `0.84375` -> `0.84375`
- Max drawdown: `-8.18251735324681` -> `-8.18251735324681`
- Stress worst profit BNB: `0.010166721706927569` -> `0.010811811094509526`

Final baseline vs selected:

- Net profit BNB: `0.006994210572241049` -> `0.007592630952680585`
- Total trades: `24` -> `24`
- Win rate: `0.6666666666666666` -> `0.6666666666666666`
- Max drawdown: `-12.90811269409964` -> `-12.90811269409964`
- Walk-forward worst return: `-7.064527500103712` -> `-1.6095918257340358`
- Walk-forward worst max drawdown: `-17.215985245205424` -> `-16.09502760883329`
- Stress worst profit BNB: `0.0028749898853279235` -> `0.00314782134332609`

## Decision

Reject as a new optimization win. The calibration region is flat around the existing release-only candidate.

Keep the previously accepted release-only post-target `continue_hold` branch as the current best offline replay candidate, and move the next experiment away from scalar threshold calibration.

No `.env`, threshold, sizing, model artifact, bot process, or live switch changed.

Scoreboard update: yes, `docs/model_scoreboard.md` records this plateau and the decision not to treat it as a new best.
