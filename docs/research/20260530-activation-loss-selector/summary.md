# 2026-05-30 Activation Loss Selector

## Live State

- Bot and collector were running under `memectl`.
- `data/bot_state.json` showed no open positions and balance `0.002752730398351113` BNB.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, and no fixed stake.

## Live Attribution

Fresh attribution artifact: `data/replay_reports/live_trade_attribution_20260530_after_quick_profit_reject.json` / `.md`.

Since `2026-05-29 21:19:42`, there were no closed trades, but the live stream had `2055` signal decisions and `145` per-token rejected candidates:

- `fast_profit=8`
- `fast_profit_then_collapse=9`
- `slow_runner=4`
- `flat_timeout=98`
- `stop_first=26`

The quick-profit pocket stayed supported, but the immediately preceding strict replay hard-rejected the non-broad quick-profit family. This round therefore pivoted to the unresolved activation45 `never_activated_loss` cohort rather than continuing quick-profit parameter sweeps.

## Research Evidence

This round reused recent SmartSearch-backed research:

- `docs/research/20260529-activation-risk-filter/summary.md`
- `docs/research/20260529-dead-flow-structural-selector/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`

New live-derived angle: activation45 remains `Shadow Candidate` evidence, but the activation shadow still has `5` `never_activated_loss` matched queued rows. The previous scalar low-flow abstention probe failed out of sample, so the next falsification was a non-scalar conjunction selector using only decision-time fields.

## Tooling

`src/pipeline/activation_survival_abstention_probe.py` now supports multi-condition conjunction scans while preserving the default single-condition behavior.

New CLI options in `scripts/probe_activation_survival_abstention.py`:

- `--max-conditions`
- `--max-atomic-rules`

The scan still reports proxy evidence only. It is read-only, does not change live runtime behavior, and cannot be live-switch evidence without replay integration.

## Experiment

```bash
venv/bin/python scripts/probe_activation_survival_abstention.py \
  --train-report data/replay_reports/post_target_exit_state_probe_20260529_activation_meta_gate_train.json \
  --validation-report data/replay_reports/post_target_exit_state_probe_20260529_dead_flow_structural_validation.json \
  --final-report data/replay_reports/post_target_exit_state_probe_20260529_dead_flow_structural_final.json \
  --output data/replay_reports/activation_survival_abstention_probe_20260530_multicondition.json \
  --min-train-selected 3 \
  --min-train-bad-precision 0.65 \
  --max-train-protected 1 \
  --min-validation-selected 1 \
  --max-validation-protected 0 \
  --min-final-selected 1 \
  --max-final-protected 0 \
  --max-conditions 2 \
  --max-atomic-rules 120 \
  --force

venv/bin/python scripts/probe_activation_survival_abstention.py \
  --train-report data/replay_reports/post_target_exit_state_probe_20260529_activation_meta_gate_train.json \
  --validation-report data/replay_reports/post_target_exit_state_probe_20260529_dead_flow_structural_validation.json \
  --final-report data/replay_reports/post_target_exit_state_probe_20260529_dead_flow_structural_final.json \
  --output data/replay_reports/activation_survival_abstention_probe_20260530_multicondition_depth3.json \
  --min-train-selected 3 \
  --min-train-bad-precision 0.65 \
  --max-train-protected 1 \
  --min-validation-selected 1 \
  --max-validation-protected 0 \
  --min-final-selected 1 \
  --max-final-protected 0 \
  --max-conditions 3 \
  --max-atomic-rules 120 \
  --force
```

## Results

Depth-2 artifact: `data/replay_reports/activation_survival_abstention_probe_20260530_multicondition.json`.

- Outcome tier: `Rejected`.
- Decision: `train_candidate_failed_validation_or_final_proxy_gate`.
- Train rows: `69`; validation rows: `32`; final rows: `28`.
- Scanned train rules: `7815`.
- Train-eligible rules: `51`.
- Selected rule: `flow_buy_sell_ratio_10s >= 20.940253902417062` and `flow_sell_pressure_10s >= 0.006642493881926145`.
- Train selected `3` rows: `2` bad / `1` protected, utility delta `+28.2246960071%`.
- Validation selected `1` row, but it was protected `post_target_continuation` (`合一`), utility delta `-70.7560752262%`.
- Final selected `0` rows.

Depth-3 artifact: `data/replay_reports/activation_survival_abstention_probe_20260530_multicondition_depth3.json`.

- Outcome tier: `Rejected`.
- Decision: `train_candidate_failed_validation_or_final_proxy_gate`.
- Scanned train rules: `237923`.
- Train-eligible rules: `184`.
- Selected rule was the same validation-protected / final-empty conjunction as depth 2.

## Tier

`Rejected`.

This rejects the simple decision-time conjunction selector for the activation45 `never_activated_loss` cohort. The result is not a live-switch candidate and not `Research Alpha`: train-only rules do not generalize, validation selects protected continuation rows, and final has no selected bad rows. Do not continue expanding this family through more conjunction-depth or threshold sweeps unless new live evidence changes the sample population or target label.

## Scoreboard Decision

`docs/model_scoreboard.md` was updated because this round closes the next activation45 loss-selector attempt and records reusable multi-condition probe tooling.

No `.env`, model artifact, threshold, sizing, bot process, or live runtime behavior changed.

## Next Direction

The remaining higher-value directions are structurally different:

- Trade-delta/meta-gate trained on paired added/removed trade benefit rather than post-target no-activation proxy labels.
- Live shadow evaluator that records candidate would-buy/would-sell decisions on the live stream before any replay/live switch.
- Missed slow-runner detector only after same-shape support improves beyond the current `4` cases.
