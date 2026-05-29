# 2026-05-30 Replacement-Pair Selector

## Question

Can the earlier same-token replacement signal from the replacement-oracle diagnostic be turned into a decision-time selector that predicts positive realized delta or avoids ties/losses?

## Live Context

Fresh attribution: `data/replay_reports/live_trade_attribution_20260530_goal_resume_current.json` / `.md`.

Since `2026-05-29 21:19:42`, there were `0` closed trades, `2187` signal decisions, and `159` per-token rejected candidates. Same-shape replay support stayed below gate: `fast_profit=5`, `slow_runner=5`, `fast_profit_then_collapse=4`. Because quick-profit, activation-loss, candidate meta-gate score-floor, runner-retention micro-sweeps, and activation45 dead-flow overlays were already rejected or below promotion, this round pivoted to a structurally different replacement-pair selector.

## Research Reuse

No new SmartSearch run was needed. This experiment reused committed SmartSearch-backed artifacts:

- `docs/research/20260527-replacement-oracle-upper-bound/summary.md`
- `docs/research/20260528-multifeature-added-trade-boundary/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`

The reused method guidance is: keep the primary model unchanged, use decision-time secondary selectors only, treat ex-post path simulation as diagnostic rather than OPE, and require paired/utility evidence plus robustness checks before promotion.

## Implementation

Added a reusable read-only selector path:

- `src/pipeline/replacement_oracle_upper_bound.py`
- `scripts/probe_replacement_pair_selector.py`
- `tests/model/test_replacement_oracle_upper_bound.py`

The selector report is explicit:

- `read_only=true`
- `live_switch_evidence=false`
- `safe_for_live_switch=false`
- `uses_ex_post_outcomes=true`
- `uses_decision_time_features_only=true`
- `not_deployable_policy=true`
- `max_outcome_tier=Research Alpha`

The initial full default-grid train/validation/final run was interrupted because replacement row generation over the full train split was too expensive for a minimal falsification pass. A single broad-rescue grid was then pre-registered in `replacement_selector_single_grid.json`. The train-selected single-grid run was also too expensive, so the completed falsification used validation-selected / final-evaluated mode, matching the existing added-trade boundary pattern and keeping the result below live-switch evidence.

## Command

```bash
venv/bin/python scripts/probe_replacement_pair_selector.py \
  --splits validation,final \
  --selection-split validation \
  --candidate-grid-json docs/research/20260530-replacement-pair-selector/replacement_selector_single_grid.json \
  --selector-lead-windows-seconds 120 \
  --max-conditions 1 \
  --beam-width 40 \
  --output data/replay_reports/replacement_pair_selector_probe_20260530_single_grid_validation_selected.json \
  --force
```

## Result

Report: `data/replay_reports/replacement_pair_selector_probe_20260530_single_grid_validation_selected.json`.

Outcome tier: `Rejected`.

The selector found no supported validation rule:

- Selected rule: `null`
- Rejection reasons: `no_train_supported_rule`, `validation_utility_delta_not_positive`, `validation_positive_rate_below_min`, `final_positive_rate_below_min`
- Validation/selection 120s rows: `370`
- Validation positives/ties/losses: `25/330/15`
- Validation positive rate: `6.7568%`
- Validation cost-adjusted utility: `-959.6987014662036`
- Final 120s rows: `166`
- Final positives/ties/losses: `39/125/2`
- Final positive rate: `23.4940%`
- Final cost-adjusted utility: `+923.4027095060229`
- Final top-1/top-3 positive removal stayed positive, but this was blanket replacement, not a validation-supported selector.

The split mismatch is the important result: final blanket replacement looks superficially profitable, but validation has mostly ties and losses with negative utility, and no single decision-time feature can select a robust positive-delta pocket.

## Decision

Reject this replacement-pair selector as a model-improvement candidate.

No live switch, `.env`, sizing, threshold, model artifact, bot process, or runtime behavior changed.

Do not continue replacement-pair selector sweeps from this exact broad-rescue/single-feature setup. The branch only deserves another attempt if the tooling can make full train-selected evaluation cheap enough or if a materially different direct replay integration target is available.

Scoreboard update: yes, `docs/model_scoreboard.md` records the rejection and next-direction constraint.
