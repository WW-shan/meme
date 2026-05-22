# Evidence

## Commands

```bash
python scripts/probe_time_to_barrier.py \
  --since "2026-05-22 00:00:00" \
  --max-candidate-sample 0 \
  --output data/replay_reports/time_to_barrier_probe_20260522_post_ci_current_day_all_candidates.json

python scripts/probe_support_action_policy.py \
  --time-to-barrier-report data/replay_reports/time_to_barrier_probe_20260522_post_ci_current_day_all_candidates.json \
  --output data/replay_reports/support_action_policy_20260522_post_ci_current_day.json \
  --force

python scripts/probe_support_action_policy_pool.py \
  --time-to-barrier-report data/replay_reports/time_to_barrier_probe_20260522_expanded_flow_since20260521_all_candidates.json \
  --time-to-barrier-report data/replay_reports/time_to_barrier_probe_20260522_post_ci_current_day_all_candidates.json \
  --output data/replay_reports/support_action_policy_pool_20260522_post_ci_current_plus_expanded.json \
  --force
```

## Results

- Current-day rejected-signal probe emitted `66` per-token candidates from `2010` signal decisions.
- Current-day class counts: `fast_profit=11`, `fast_profit_then_collapse=4`, `slow_runner=1`, `flat_timeout=38`, `stop_first=12`.
- Current-day support candidates: `16` positive, `50` negative.
- Best current-day eligible rule: `high_prob_low_toxic_overlap`, `7` selected, `4` positive, precision `57.14%`.
- Pooled report had `898` candidates, `172` positive and `726` negative.
- Pooled target flow rule selected `142`, `68` positive, precision `47.89%`.
- Pooled decision stayed `missing_flow_feature_parity`; required flow fields are incomplete.
- Live-loss forensic table is recorded at `docs/research/20260522-post-ci-research-round/summary.md`.

## Gate Check

- Current-day candidate count >= `150`: FAIL (`66`).
- Current-day active-flow support: FAIL by support insufficiency. The `high_prob_low_toxic_overlap` precision was `57.14%`, but it selected only `7` candidates and is not interpretable below the candidate support floor.
- Pooled precision >= `58%`: FAIL (`47.89%` for the target flow rule).
- Flow parity gate: FAIL (`missing_flow_feature_parity`).
- Live switch: FAIL / `NO_GO_FOR_LIVE_SWITCH`.

## Review Notes

- Future pre-registration must name the exact target active-flow rule string. This round used `high_prob_low_toxic_overlap` as the target pooled flow rule.
- The support file also contained non-eligible flow variants below `min_selected=3`; they were not considered evidence.

## Next Research Hypotheses

Use the loss table only to seed future pre-registered replay experiments:

- Entry-slippage veto/protection for high positive entry slippage.
- Giveback guard for trades with `+25%` MFE that later close at STOP_LOSS.
