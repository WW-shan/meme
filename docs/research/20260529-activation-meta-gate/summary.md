# Activation-Aware Meta Gate

## Question

Can the live-shadow `continue_hold` branch be improved by retraining the accepted-trade action-router labels around `+35%` activation and `+75%` release before `-18%` collapse?

## Live Trigger

The prior activation-aware shadow attribution found mixed live support:

- `6` queued shadow-used matched trades.
- `3` activation hits.
- `2` release hits.
- `1` activated-then-stop.
- `3` never-activated losses.

Fresh live attribution for this round found no new closed trades after `2026-05-29 18:38:00`; the only recent per-token candidate was FOMA, a correct-looking skip with `MFE=-1.0901%`, `MAE=-36.5628%`, and first `-18%` after `10.8744s`.

## Research Evidence

SmartSearch artifacts:

- `00-doctor.json`
- `01-deep-plan.json`
- `02-search.json`
- `03-fetch-mlfinpy-labeling.md`
- `04-fetch-hudson-meta-labeling.md`
- `05-fetch-hudson-toy-meta.md`

Method implication: use path-based labels and a secondary take/pass model on primary candidates, keep decision-time features only, and require strict out-of-sample replay plus shadow evidence before any live switch.

## Hypothesis

If the accepted-trade router is trained with stricter activation/release labels (`target_pct=0.35`, `continuation_pct=0.75`, `collapse_pct=-0.18`), it should reduce false-positive `continue_hold` routing while preserving or improving validation utility under 10% sizing.

Falsification rule: reject if the validation-selected candidate fails strict validation net-profit / utility-proxy, final confirmation, router activity, stress, walk-forward, drawdown, or paired-delta checks.

## Commands

The first full chunked train attempt was stopped after the first lifecycle file (`1.8G`) drove the child replay to about `5.4GB` RSS. The reproducible run used the probe's existing diagnostic size guard:

```bash
venv/bin/python scripts/probe_post_target_exit_state.py \
  --split train \
  --chunk-train-files \
  --max-train-file-size-mb 256 \
  --target-pct 0.35 \
  --continuation-pct 0.75 \
  --collapse-pct -0.18 \
  --output data/replay_reports/post_target_exit_state_probe_20260529_activation_meta_gate_train.json \
  --force
```

```bash
venv/bin/python scripts/run_action_policy_router_replay.py \
  --train-accepted-report data/replay_reports/post_target_exit_state_probe_20260529_activation_meta_gate_train.json \
  --candidate-grid-json docs/research/20260529-activation-meta-gate/action_policy_activation_router_grid.json \
  --output data/replay_reports/action_policy_router_replay_20260529_activation_meta_gate.json \
  --force
```

The paired-delta report was generated with the selected router params from the replay report and `src.pipeline.replay_trade_delta_attribution`.

## Results

Accepted-trade label report:

- `69` scored train candidates.
- `57` target-hit candidates.
- Policy counts: `continue_hold=51`, `lock_profit=5`, `monitor_after_target=1`, `no_action=12`.

Strict router replay:

- Decision: `reject`.
- Candidate grid: `8` explicit JSON candidates.
- Selected validation candidate: index `4`, `router_min_confidence=0.70`, `continue_hold_activation_pct=0.35`, `continue_hold_release_pct=0.75`.
- Validation baseline and candidate both had net profit `0.019254464794` BNB, `32` trades, `84.375%` win rate, `-8.1825%` max drawdown, and `79.5965%` WF worst return.
- The selected validation candidate had activity (`44` router signals, `8` continue-hold entries, `45` forced holds), but failed the net-profit improvement gate.
- Final improved from `0.007319912856` to `0.007554173984` BNB, WF worst return improved from `-2.6934%` to `1.6597%`, and stress worst profit improved from `0.002730499022` to `0.002917383784` BNB, with trade count, win rate, and drawdown tied.

Paired trade delta:

- Validation: no added/removed trades; `32/32` common trades unchanged.
- Final: no added/removed trades; `2` common trades improved, `0` worsened, `26` unchanged; common return delta sum `+44.4517%`.
- Top-winner dependency is not an added-trade issue here because the candidate did not add trades. On common-trade deltas, the largest improvement was `+40.8702%`; removing it leaves a small positive `+3.5814%`, but validation still has zero delta.

## Tier

`Rejected`, with useful diagnostic evidence.

It is not `Research Alpha` because validation net profit did not improve, and the tied drawdown / walk-forward / stress profile leaves the utility proxy unchanged. It is not a `Shadow Candidate` or `Live Switch Candidate` because it is weaker than the already accepted release-only router branch, which had positive validation and stronger final net profit.

## Decision

Do not switch live, update `.env`, change sizing, change thresholds, write model artifacts, restart the bot, or replace the release-only router with this stricter activation-label retrain.

Next direction: stop activation-label threshold sweeps. Prefer a structural dead-flow / never-activated-loss classifier or bootstrap/uncertainty evaluator that explains when final-only common-trade improvements are meaningful.
