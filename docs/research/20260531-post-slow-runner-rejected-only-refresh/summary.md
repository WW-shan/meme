# Post-Slow-Runner Rejected-Only Refresh

Date: 2026-05-31

## Outcome

Outcome tier: `Rejected`.

No live switch. No `.env`, model artifact, threshold, sizing, buy/sell logic, bot process, collector process, runtime enablement, or restart changed.

This refresh tested whether the live rejected-only population after the latest `长涨` close had become clean enough to justify a new quick-profit, slow-runner, or broad near-threshold replay branch. It did not. Opportunity-shaped rejected paths exist, but the simple decision-time rules are still too noisy for replay promotion.

## Live Attribution

Artifacts:

- `data/replay_reports/live_trade_attribution_20260531_post_slow_runner_support_ci.json`
- `data/replay_reports/live_trade_attribution_20260531_post_slow_runner_support_ci.md`

Command:

```bash
venv/bin/python scripts/probe_live_trade_attribution.py \
  --since '2026-05-31 12:37:23' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --recent-lifecycle-files 64 \
  --output-json data/replay_reports/live_trade_attribution_20260531_post_slow_runner_support_ci.json \
  --output-md data/replay_reports/live_trade_attribution_20260531_post_slow_runner_support_ci.md \
  --max-trade-sample 0 \
  --max-candidate-sample 0 \
  --force
```

Result:

- Closed trades: `0`
- Signal decisions: `5443`
- Per-token rejected candidates: `389`
- Barrier classes: `fast_profit=11`, `fast_profit_then_collapse=21`, `flat_timeout=271`, `slow_runner=8`, `stop_first=78`
- Recommended policies: `conditional_slow_hold=8`, `quick_take_profit=32`, `skip=349`
- Decision: `NO_GO_FOR_LIVE_SWITCH`

## Support Rules

Artifacts:

- `data/replay_reports/time_to_barrier_probe_20260531_post_slow_runner_support_ci.json`
- `data/replay_reports/support_action_policy_probe_20260531_post_slow_runner_support_ci.json`

Commands:

```bash
venv/bin/python scripts/probe_time_to_barrier.py \
  --since '2026-05-31 12:37:23' \
  --recent-lifecycle-files 64 \
  --output data/replay_reports/time_to_barrier_probe_20260531_post_slow_runner_support_ci.json \
  --max-candidate-sample 0

venv/bin/python scripts/probe_support_action_policy.py \
  --time-to-barrier-report data/replay_reports/time_to_barrier_probe_20260531_post_slow_runner_support_ci.json \
  --output data/replay_reports/support_action_policy_probe_20260531_post_slow_runner_support_ci.json \
  --min-selected 3 \
  --force
```

Support probe:

- Input candidates: `389`
- Positive candidates: `40`
- Negative candidates: `349`
- Eligible rules: `4`
- Best eligible precision: `34.62%` for `high_prob_low_toxic_overlap` (`9` positives / `17` negatives)
- `high_prob_positive_pred`: `33.33%` precision (`6` positives / `12` negatives)
- `young_high_prob_positive_pred`: `29.41%` precision (`5` positives / `12` negatives)
- `high_prob_volume_volatility`: `25.93%` precision (`14` positives / `40` negatives)
- `young_high_prob_clean_flow` was `2/2`, but it failed the minimum selected support of `3`.

## Hypothesis Portfolio

1. Replay-compatible freshness / dead-flow abstention.
   Highest current priority. The newest accepted-trade failure remains `长涨` as a `dead_flow_timeout`, and queued-only freshness is already `Research Alpha`, but the signal-level rule still needs more queued support or a replay-compatible feature path before it can become a shadow candidate.
2. Structurally different missed slow-runner detector.
   Slow-runner support remains real (`8` in this fresh window and `17` in the prior full-window refresh), but shallow clean-flow rules are too imprecise. A future attempt should use source-window stability and paired-delta evaluation, not another simple high-probability rule.
3. Quick-profit / early-harvest replay branch.
   The live window contains `32` quick-profit-shaped candidates, but current decision-time rules select too many negatives. Do not replay or promote this branch until a rule can separate positives from flat/stop-first paths with materially better precision.
4. Activation45 live-shadow continuation.
   Prior activation45 evidence remains material shadow-only context, but there are no new queued/opened rows after `长涨`; it should continue accumulating matched queued rows rather than changing live behavior.

## Falsification

The tested hypothesis was: recent rejected paths contain a simple decision-time support rule clean enough to justify a new replay branch.

It was falsified because all eligible rules selected more negatives than positives, with best eligible precision only `34.62%`. The only perfect rule had just `2` selected candidates and failed minimum support. This is not enough for `Research Alpha` promotion, and it is far below any `Shadow Candidate` or `Live Switch Candidate` threshold.

## Decision

Do not run a quick-profit or slow-runner replay from these shallow support rules. Do not lower global thresholds. Do not switch live.

Keep the artifacts as negative evidence. The next useful work is either replay-compatible freshness/dead-flow evidence, a structurally different slow-runner selector, or continued live-shadow collection for activation/freshness branches.

## Scoreboard

`docs/model_scoreboard.md` was updated because this boundary changes the current direction ranking: the latest rejected-only support is too noisy for replay promotion, so shallow quick-profit and slow-runner support rules should be treated as rejected for this window.
