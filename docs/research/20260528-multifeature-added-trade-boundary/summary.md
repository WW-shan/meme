# 2026-05-28 Multifeature Added-Trade Boundary

## Question

Can the runner-retention path be improved by selecting only robust added trades with a support-constrained, cost-sensitive, multifeature rule, instead of repeating single-feature threshold sweeps?

## External Method Evidence

SmartSearch deep research artifacts:

- `00-deep-plan.json`
- `01-search.json`
- `02-fetch-copo.md`
- `03-fetch-hudson-meta-labeling.md`
- `04-fetch-supported-policy-optimization.md`
- `05-search-purged-cv.json`
- `06-fetch-purged-cv.md`

The method implications were:

- Constrained offline policy work supports keeping new policies within offline support and measuring costs under distribution shift.
- Meta-labeling supports using a secondary model or rule only to decide act/pass on opportunities already proposed by the primary system.
- Supported policy optimization supports staying close to behavior support so offline ranking is more reliable.
- Finance cross-validation guidance supports strict validation/final holdouts and avoiding repeated final-set tuning.

## Live Attribution Refresh

Command:

```bash
python scripts/probe_live_trade_attribution.py \
  --since 2026-05-28T00:00:00 \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --recent-lifecycle-files 3 \
  --output-json data/replay_reports/live_trade_attribution_20260528_multifeature_boundary_round.json \
  --output-md data/replay_reports/live_trade_attribution_20260528_multifeature_boundary_round.md \
  --max-trade-sample 0 \
  --max-candidate-sample 120
```

Result:

- Closed trades since `2026-05-28T00:00:00`: `2`
- Wins/losses: `1/1`
- Net profit: `+0.00010453043713559213` BNB
- Live labels: `mfe_then_giveback=1`, `profitable_exit=1`
- Rejected path classes: `fast_profit=8`, `fast_profit_then_collapse=9`, `flat_timeout=49`, `slow_runner=3`, `stop_first=14`

This remained read-only diagnostic evidence and did not justify a live switch.

## Code Change

`src/pipeline/added_trade_boundary_policy_probe.py` now supports an optional multifeature conjunction rule family:

- Default remains `max_conditions=1`, preserving the prior single-feature behavior.
- `--max-conditions 2/3` enables AND-rules over decision-time feature thresholds.
- Rules are selected only on validation added trades, then evaluated on final added trades.
- The report keeps `live_switch_evidence=false` and `safe_for_live_switch=false`.

Targeted validation:

```bash
python -m unittest tests.model.test_added_trade_boundary_policy_probe
```

Result: `6` tests passed.

## Experiment

Input:

```text
data/replay_reports/runner_retention_candidate_gate_replay_20260527_added_boundary_input.json
```

Commands:

```bash
python scripts/probe_added_trade_boundary_policy.py \
  --input data/replay_reports/runner_retention_candidate_gate_replay_20260527_added_boundary_input.json \
  --output data/replay_reports/added_trade_boundary_policy_probe_20260528_multifeature_loss3_c2.json \
  --loss-cost 3.0 --min-keep-count 4 --min-reject-count 2 --max-conditions 2 --beam-width 80 --force

python scripts/probe_added_trade_boundary_policy.py \
  --input data/replay_reports/runner_retention_candidate_gate_replay_20260527_added_boundary_input.json \
  --output data/replay_reports/added_trade_boundary_policy_probe_20260528_multifeature_loss5_c3.json \
  --loss-cost 5.0 --min-keep-count 4 --min-reject-count 2 --max-conditions 3 --beam-width 80 --force
```

Best low-cost rule:

```json
{
  "conditions": [
    {"feature": "retail_entry_rate_ratio_30s", "operator": "<=", "threshold": 1.1911726598514814},
    {"feature": "time_since_launch", "operator": "<=", "threshold": 226.0}
  ]
}
```

For `loss_cost=3.0`, `max_conditions=2`:

| Split | All | Kept | Rejected | Utility Delta |
|---|---:|---:|---:|---:|
| Validation | `15` trades, `8/7` win/loss | `8` trades, `7/1` win/loss | `7` trades, `1/6` win/loss | `+469.68665252923745` |
| Final | `7` trades, `1/6` win/loss | `6` trades, `1/5` win/loss | `1` trade, `0/1` win/loss | `+100.2027672230814` |

Best higher-loss-cost rule:

```json
{
  "conditions": [
    {"feature": "avg_holding", "operator": "<=", "threshold": 29974371.9385934},
    {"feature": "retail_entry_rate_ratio_30s", "operator": "<=", "threshold": 1.1911726598514814},
    {"feature": "time_since_launch", "operator": "<=", "threshold": 226.0}
  ]
}
```

For `loss_cost=5.0`, `max_conditions=3`:

- Validation kept `7/15` trades with `7` wins and `0` losses; utility delta `+849.2334300062147`.
- Final kept `6/7` trades, preserved the only final winner, rejected one `-33.4009224076938%` loser, and improved cost-adjusted utility by `+167.00461203846896`.

Rejected comparison:

- `loss_cost=5.0`, `max_conditions=2` improved final utility but kept `0` final winners, so it stayed rejected.

## Decision

This is a successful intermediate optimization result, not live-switch evidence.

The multifeature added-trade boundary is the first boundary in this branch that:

- improves validation added-trade utility,
- improves final added-trade utility,
- reduces final added-trade losses,
- preserves the only final added-trade winner,
- avoids hard-coded token-specific logic.

Next step: integrate this boundary into the runner-retention replay path and run strict live-sized validation/final/walk-forward/stress evaluation. No `.env`, model artifact, threshold, sizing, bot process, or live switch changed in this boundary.

Scoreboard update: yes, `docs/model_scoreboard.md` records this intermediate optimization direction.
