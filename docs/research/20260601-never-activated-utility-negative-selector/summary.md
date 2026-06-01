# 2026-06-01 Never-Activated Utility-Negative Selector

## Live State

- Bot and collector were running under `./tools/memectl` in the expected tmux sessions.
- `data/bot_state.json` had no open positions and balance `0.002195742691061948` BNB.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, no fixed stake, and `MIN_ENTRY_VOLUME_30S=1.5`.
- Latest public boundary before this experiment was `4b65c0e`, pushed to `origin/main`, with GitHub Actions `CI` run `26736172040` passing.

## Live Attribution

Fresh entry artifact:

- `data/replay_reports/live_trade_attribution_20260601_never_activated_selector_entry.json`
- `data/replay_reports/live_trade_attribution_20260601_never_activated_selector_entry.md`

Command:

```bash
venv/bin/python scripts/probe_live_trade_attribution.py \
  --since '2026-06-01 12:44:58' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --recent-lifecycle-files 48 \
  --output-json data/replay_reports/live_trade_attribution_20260601_never_activated_selector_entry.json \
  --output-md data/replay_reports/live_trade_attribution_20260601_never_activated_selector_entry.md \
  --max-trade-sample 40 \
  --max-candidate-sample 220 \
  --force
```

Result:

- Decision: `NO_GO_FOR_LIVE_SWITCH`.
- Closed trades after `UP`: `0`.
- Signal decisions: `181`; per-token candidates: `22`.
- Barrier classes: `fast_profit=1`, `fast_profit_then_collapse=1`, `slow_runner=1`, `flat_timeout=17`, `stop_first=2`.
- Watchpoints: `MCDOGE` and `Grimacecoin` were negative-PredReturn quick-profit shapes; `证券代币` was a low-score slow runner. These do not override the recent hard rejection of broad negative-PredReturn quick-profit replay.

## Prior Review

The latest committed activation45 refresh is `Shadow Candidate` / material shadow-only evidence, not live switch:

- `.bts`: `activated_profitable_no_release`.
- `世界有无限可能`: `never_activated_loss`.
- `UP`: `never_activated_win`.

This showed that a simple never-activated skip would remove both a live loss and a live win. Prior work in `docs/research/20260530-activation-loss-selector/summary.md` already rejected expanding the target-not-hit selector through more conjunction depth. This experiment changed the label target instead of sweeping activation thresholds: treat utility-negative activation-path rows (`target_not_hit` plus `post_target_collapse`) as the bad class, and protect `post_target_continuation` / `post_target_unresolved`.

Reused SmartSearch-backed research:

- `docs/research/20260529-activation-risk-filter/summary.md`
- `docs/research/20260529-dead-flow-structural-selector/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`
- `docs/research/20260530-activation-loss-selector/summary.md`

## Hypothesis

Because live activation45 evidence now has both a never-activated timeout loss and a never-activated timeout win, use a utility-negative activation-path label rather than a pure no-activation label. Expected improvement: remove path-negative accepted candidates while preserving continuation rows, creating a safer secondary selector candidate for future activation45 / never-activated handling.

Falsification rule: reject if the selected train rule fails validation or final, selects a protected validation/final row, selects no final bad rows, has non-positive validation/final abstention utility delta, or is top-benefit dependent.

## Experiment

Depth 2:

```bash
venv/bin/python scripts/probe_activation_survival_abstention.py \
  --train-report data/replay_reports/post_target_exit_state_probe_20260529_activation_meta_gate_train.json \
  --validation-report data/replay_reports/post_target_exit_state_probe_20260529_dead_flow_structural_validation.json \
  --final-report data/replay_reports/post_target_exit_state_probe_20260529_dead_flow_structural_final.json \
  --output data/replay_reports/activation_survival_abstention_probe_20260601_utility_negative_label.json \
  --bad-class target_not_hit \
  --bad-class post_target_collapse \
  --protected-class post_target_continuation \
  --protected-class post_target_unresolved \
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
```

Depth 3 was run only because depth 2 was an ambiguous near-pass with clean validation but no final selection:

```bash
venv/bin/python scripts/probe_activation_survival_abstention.py \
  --train-report data/replay_reports/post_target_exit_state_probe_20260529_activation_meta_gate_train.json \
  --validation-report data/replay_reports/post_target_exit_state_probe_20260529_dead_flow_structural_validation.json \
  --final-report data/replay_reports/post_target_exit_state_probe_20260529_dead_flow_structural_final.json \
  --output data/replay_reports/activation_survival_abstention_probe_20260601_utility_negative_label_depth3.json \
  --bad-class target_not_hit \
  --bad-class post_target_collapse \
  --protected-class post_target_continuation \
  --protected-class post_target_unresolved \
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

Depth 2:

- Outcome tier: `Rejected`.
- Decision: `train_candidate_failed_validation_or_final_proxy_gate`.
- Train/validation/final rows: `69` / `32` / `28`.
- Train outcome counts: `target_not_hit=12`, `post_target_collapse=5`, `post_target_continuation=51`, `post_target_unresolved=1`.
- Validation outcome counts: `target_not_hit=5`, `post_target_collapse=1`, `post_target_continuation=25`, `post_target_unresolved=1`.
- Final outcome counts: `target_not_hit=3`, `post_target_collapse=6`, `post_target_continuation=18`, `post_target_unresolved=1`.
- Scanned train rules: `7831`; train-eligible rules: `91`.
- Selected rule: `flow_buy_sell_ratio_30s >= 151.66365555410877` and `flow_buy_sell_ratio_60s >= 480.49053077829393`.
- Train selected `3` rows: `2` bad / `1` protected, utility delta `+148.9731880077%`, without-top benefit `+89.1576712289%`.
- Validation selected `1` bad row (`X Revenue Sharing`) with no protected rows and utility delta `+43.6708142653%`.
- Final selected `0` rows, so the proxy gate failed.

Depth 3:

- Outcome tier: `Rejected`.
- Decision: `train_candidate_failed_validation_or_final_proxy_gate`.
- Scanned train rules: `239875`; train-eligible rules: `320`.
- Selected rule was unchanged from depth 2 and still selected `0` final rows.
- The next depth-3 rules either missed validation or selected a protected final continuation such as `幣學`, so increasing conjunction depth does not fix the split failure.

## Strict Evaluation

This is proxy-only evidence. It does not compute strict replay PnL, walk-forward, stress, drawdown, or live shadow matched-trade support. The candidate therefore cannot exceed `Research Alpha`; because both depth-2 and depth-3 fail the validation/final proxy gate, the correct tier is `Rejected`.

The useful conclusion is negative: changing from a pure no-activation label to a utility-negative activation-path label improves validation shape but still fails final support. Do not keep expanding this family through activation thresholds, conjunction depth, or hard-coded flow-ratio cuts without a new sample population or direct paired trade-delta training.

## Decision

`Rejected`.

No live switch. No `.env`, model artifact, threshold, sizing, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

`docs/model_scoreboard.md` was updated because this experiment rejects the latest activation45 never-activated secondary selector variant and changes the next-direction decision.

Next highest-value direction: pivot away from activation-path selector sweeps toward direct paired-delta/meta-gate training, replay-compatible signal-context freshness, or continued live-shadow accumulation when new queued trades appear.
