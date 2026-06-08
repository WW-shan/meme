# Quick-Profit Support Selector Refresh - 2026-06-08

## Outcome

Rejected. No live switch, no model artifact change, no `.env` change, no sizing change, no bot or collector restart.

This was a no-switch falsification of whether the fresh live-derived support rules could isolate rejected-signal quick-profit opportunities after recorded shadow `quick_take_profit` route precision failed.

## Live State

- Active node: `.ccg/tasks/live-model-optimization-20260608-post-audit-shadow-refresh/task.json`
- Node archive state: not archived
- Latest committed milestone before this probe: `07e407a research: reject recorded shadow quick route`
- Latest pushed state before this probe: `origin/main` at `07e407a`
- Latest CI before this probe: GitHub Actions `CI` run `27136971669`, success
- Bot: running as PID `62039`
- Collector: running as PID `4739`
- Balance: `0.001559636535526772`
- Open positions: `{}`
- New real trades after `2026-06-07 12:25:39.499918`: none observed in the live health loop

Recent logs continued to show high-score rejects with weak or negative `PredReturn`, so there was no live evidence for a direct model switch.

## Live-Derived Hypothesis

Recorded in-process `quick_take_profit` route counts were too contaminated to trust directly, but a stricter decision-time support selector might still isolate a smaller quick-profit-shaped rejected-entry pocket.

The fresh support probe from `data/replay_reports/support_action_policy_probe_20260608_post_recorded_route_reject_direction.json` found:

- `high_prob_volume_volatility`: selected `17`, positives `7`, negatives `10`, precision `0.4117647058823529`
- `high_prob_low_toxic_overlap`: selected `12`, positives `4`, negatives `8`, precision `0.3333333333333333`
- `v95_like_pred_rescue`: selected `0`

This made the expected edge weak, but still falsifiable through strict replay.

## Experiment

Candidate grid:

- `data/replay_reports/quick_profit_support_candidate_grid_20260608_post_recorded_route_reject_direction.json`

Strict replay report:

- `data/replay_reports/quick_profit_support_replay_20260608_post_recorded_route_reject_direction.json`

Command:

```bash
PYTHON_DOTENV_DISABLED=true venv/bin/python scripts/run_primary_score_scalp_replay.py \
  --candidate-grid-json data/replay_reports/quick_profit_support_candidate_grid_20260608_post_recorded_route_reject_direction.json \
  --output data/replay_reports/quick_profit_support_replay_20260608_post_recorded_route_reject_direction.json \
  --write-selected-trade-delta \
  --force
```

The grid had `16` candidates and kept strict live assumptions:

- `position_fraction=0.1`
- `max_position_fraction=0.1`
- `max_open_positions=8`
- no fixed stake

## Result

Replay decision: `reject`.

Validation baseline:

- net profit `0.012252343033424175` BNB
- trades `23`
- win rate `0.7391304347826086`
- max drawdown `-7.361964742920057%`
- walk-forward worst return `2.8446315943470024%`
- stress worst profit `0.004609956337437153` BNB

Best raw validation candidate was index `4`:

- net profit `0.022117668389364364` BNB
- trades `788`
- win rate `0.4593908629441624`
- max drawdown `-18.795915286396948%`
- walk-forward worst max drawdown `-52.59660493510334%`
- stress worst profit `-0.004494779004026409` BNB
- overlay entries `771`

It failed validation gates on drawdown, stress return/profit/drawdown, trade-count expansion, walk-forward drawdown, and win rate.

Sealed final for the same selected candidate failed harder:

- baseline net profit `0.0020282580548887895` BNB
- candidate net profit `-0.005066395574538042` BNB
- baseline trades `24`
- candidate trades `237`
- baseline win rate `0.5416666666666666`
- candidate win rate `0.3333333333333333`
- baseline max drawdown `-18.206422038627302%`
- candidate max drawdown `-99.81790865432927%`
- candidate stress worst profit `-0.005076039166625179` BNB
- candidate walk-forward worst return `-99.74587959787637%`

Selected trade-delta confirmed the over-expansion:

- validation added trades: `771`, win rate `0.45525291828793774`
- validation removed baseline trades: `6`, all winners
- final added trades: `233`, win rate `0.33476394849785407`, return sum `-3054.008380750268%`
- final removed baseline trades: `20`, win rate `0.6`, return sum `447.8777875379374%`

The strict legacy support shape was also not viable. Candidates `12-15` added only `7` overlay entries, but all failed validation net-profit and stress gates.

## Decision

Tier: Rejected.

Falsification rule was met because no candidate passed validation acceptance, the raw validation winner over-expanded trade count and worsened risk, and sealed final produced negative net profit with catastrophic drawdown.

Do not continue this quick-profit support selector as another threshold micro-sweep. The fresh live support report is too noisy, and strict replay shows the decision-time rules either overtrade badly or fail profit/stress gates.

Next direction should be structural rather than a quick-profit parameter tweak. The current better-ranked paths remain:

- accepted-action router shadow evidence, still no live runtime enablement without live-risk review
- non-degenerate freshness/replay-surface work
- trade-delta or conditional-exit meta-gating that reduces no-upside accepted losses without expanding rejected entries broadly

## Scoreboard

`docs/model_scoreboard.md` was updated in this node because the experiment changes the quick-profit direction conclusion and should prevent repeating this support-selector grid.
