# Freshness / Dead-Flow Structural Refresh

Date: 2026-05-31

## Outcome

Outcome tier: `Research Alpha`, not `Shadow Candidate` and not live switch.

No `.env`, model artifact, threshold, sizing, buy/sell logic, runtime enablement, or live switch changed. During the resumed run, the bot and collector were found stopped after a `Ctrl+C` shutdown. `data/bot_state.json` showed no open positions, so both services were restarted through `./tools/memectl` only to restore live health. This was not a model/config cutover.

## Live State

- Latest pushed boundary before this work: `dce417a` (`research: reject shallow support refresh`).
- Latest pushed CI: GitHub Actions `CI` run `26712172677`, success.
- Active worktree task: `.ccg/tasks/live-model-optimization-20260530-activation45-hazard-guard/task.json`.
- `docs/goals` was clean and `.ccg` was not tracked.
- Before service recovery, bot/collector status reported stopped and tmux had no sessions; `data/bot_state.json` showed `{}` positions and balance `0.002183078348474941` BNB.
- Recovery command: `./tools/memectl collector start && ./tools/memectl bot start`; post-recovery PIDs were collector `2342` and bot `2398`.

## Live Attribution

Report:

- `data/replay_reports/live_trade_attribution_20260531_after_shallow_support_refresh.json`
- `data/replay_reports/live_trade_attribution_20260531_after_shallow_support_refresh.md`

Command:

```bash
venv/bin/python scripts/probe_live_trade_attribution.py \
  --since '2026-05-31 12:37:23' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --recent-lifecycle-files 64 \
  --output-json data/replay_reports/live_trade_attribution_20260531_after_shallow_support_refresh.json \
  --output-md data/replay_reports/live_trade_attribution_20260531_after_shallow_support_refresh.md \
  --max-trade-sample 0 \
  --max-candidate-sample 0 \
  --force
```

Result:

- Closed trades after the latest `Changzhang` close: `0`.
- Signal decisions: `5585`.
- Per-token rejected candidates: `409`.
- Barrier classes: `fast_profit=11`, `fast_profit_then_collapse=22`, `flat_timeout=286`, `slow_runner=8`, `stop_first=82`.
- Policy hints: `quick_take_profit=33`, `conditional_slow_hold=8`, `skip=368`.
- Decision: `NO_GO_FOR_LIVE_SWITCH`.

This refreshed attribution still rejects shallow rejected-candidate promotion. The highest-value live-derived branch remains accepted-trade dead-flow / execution freshness rather than another runner-retention or quick-profit micro-sweep.

## Research Basis

SmartSearch Deep Research artifacts:

- `docs/research/20260531-freshness-deadflow-structural-refresh/evidence/00-deep-plan.json`
- `docs/research/20260531-freshness-deadflow-structural-refresh/evidence/01-search.json`
- `docs/research/20260531-freshness-deadflow-structural-refresh/evidence/02-fetch-moallemi-latency.md`
- `docs/research/20260531-freshness-deadflow-structural-refresh/evidence/03-fetch-arxiv-offline-policy-evaluation.md`
- `docs/research/20260531-freshness-deadflow-structural-refresh/evidence/04-fetch-talos-execution-alpha.md`
- `docs/research/20260531-freshness-deadflow-structural-refresh/evidence/05-fetch-hudson-meta-labeling.md`

The fetched evidence supports treating freshness as decision-time execution risk, not as a hard-coded live rule:

- Latency cost is tied to timely information and volatility over the delay interval.
- Crypto execution quality depends on forecasting volume, volatility, spreads, and feeding measured execution outcomes back into models.
- Meta-labeling / triple-barrier framing supports a secondary take/skip layer on top of an existing primary model.
- Offline policy evaluation evidence supports conservative validation before deploying any new policy from logged data.

## Hypothesis Portfolio

1. Replay-compatible execution-freshness / dead-flow abstention.
   Highest priority because recent accepted losses sit in stale/high-risk execution contexts, and shallow rejected-candidate selectors remain noisy.
2. Activation45 shadow continuation.
   Prior activation45 evidence remains material shadow context, but the latest refresh added no new activation/release positives.
3. Structurally different missed clean-runner detector.
   Slow-runner support is real, but shallow clean-flow rules have low precision and the old `volceil020` branch is already `Research Alpha` only.
4. Quick-profit / early-harvest replay.
   Fresh rejected candidates include quick-profit shapes, but recent support probes selected too many flat/stop-first negatives.

Selected hypothesis: a train-derived, signal-context accepted-trade abstention rule can identify dead-flow/high-execution-risk accepted losses with zero winner skips across train, validation, and final proxy splits.

Falsification rule: reject shadow promotion unless train-derived rules show positive validation and final abstention utility, no skipped winners, positive top-loss-removed delta, and enough queued/opened signal-level support to estimate opportunity-miss risk. Without replay drawdown, walk-forward, stress, and paired-delta evidence, the result cannot exceed `Research Alpha`.

## Experiment

Accepted-trade proxy:

```bash
venv/bin/python scripts/probe_execution_freshness_abstention.py \
  --since '2026-05-19 04:02:23' \
  --paper-trades data/paper_trades.jsonl \
  --signal-audit data/signal_audit.jsonl \
  --signal-match-tolerance-seconds 3 \
  --output data/replay_reports/execution_freshness_zero_winner_signal_context_probe_20260531_after_shallow_support_refresh.json \
  --max-train-winner-count 0 \
  --max-validation-winner-count 0 \
  --max-final-winner-count 0 \
  --force \
  --max-sample-rows 100
```

Queued-only signal shadow:

```bash
venv/bin/python scripts/probe_signal_freshness_shadow.py \
  --since '2026-05-19 04:02:23' \
  --decision queued \
  --recent-lifecycle-files 160 \
  --split-stability \
  --min-candidates 30 \
  --min-selected 2 \
  --min-split-candidates 5 \
  --min-split-selected 1 \
  --max-opportunity-misses 0 \
  --max-candidate-sample 0 \
  --output-json data/replay_reports/signal_freshness_queued_only_shadow_20260531_after_shallow_support_refresh.json \
  --output-md data/replay_reports/signal_freshness_queued_only_shadow_20260531_after_shallow_support_refresh.md \
  --force
```

## Results

Accepted-trade proxy report:

- `data/replay_reports/execution_freshness_zero_winner_signal_context_probe_20260531_after_shallow_support_refresh.json`
- Outcome tier: `Research Alpha`.
- Decision: `research_alpha_proxy_requires_replay_and_signal_time_logging`.
- Paired real trades: `53`.
- Scanned rules: `248`; train-eligible rules: `48`.
- Selected rule: `signal_volume_30s >= 3.73949`.
- Train selected `20/20` losses, skipped `0` winners, abstention delta `+0.0014023322920452908` BNB, top-loss-removed delta `+0.000999727621370464` BNB.
- Validation selected `3/3` losses, skipped `0` winners, abstention delta `+0.00007182579886884903` BNB, top-loss-removed delta `+0.00004626812159807999` BNB.
- Final selected `7/7` losses, skipped `0` winners, abstention delta `+0.00022370408283356124` BNB, top-loss-removed delta `+0.00017283649175630828` BNB.

Queued-only signal shadow report:

- `data/replay_reports/signal_freshness_queued_only_shadow_20260531_after_shallow_support_refresh.json`
- `data/replay_reports/signal_freshness_queued_only_shadow_20260531_after_shallow_support_refresh.md`
- Outcome tier: `Rejected`.
- Decision: `insufficient_signal_freshness_split_support`.
- Freshness/path-evaluable queued candidates: `5`.
- Selected rule: `lifecycle_status_chain_lag_seconds >= 18.4037`.
- All selected: `4/4` correct skips, `0` opportunity misses.
- Chronological split support: train `3`, validation `1`, final `1`; selected validation `0`, so no stable shadow promotion.

## Strict Gate Assessment

- Net profit / expected utility: positive accepted-trade proxy deltas in train, validation, and final.
- Trade count / win rate: proxy abstention would remove only losing accepted trades in the tested splits and improves remaining win rate.
- Top winner dependency: no winners are skipped; top-loss-removed deltas remain positive.
- Opportunity misses: queued-only signal shadow still has only `5` candidates and therefore cannot estimate opportunity-miss risk robustly.
- Drawdown / walk-forward / stress / paired trade delta: missing because this is not yet replay-integrated.

## Decision

Keep freshness/dead-flow as `Research Alpha`.

Do not switch live. Do not hard-code `signal_volume_30s` or chain-lag thresholds into runtime. This result strengthens the structural freshness/dead-flow direction, but it remains blocked from `Shadow Candidate` because queued/opened signal support is too small and strict replay drawdown, walk-forward, stress, and paired-delta evidence are missing.

Next direction: convert the zero-winner signal-context rule into replay-compatible paired-delta evaluation, or keep accumulating queued/opened freshness shadow rows before any live-risk discussion.

Scoreboard: `docs/model_scoreboard.md` was updated because this boundary changes the freshness/dead-flow interpretation from "proxy evidence with one final winner skip" to "zero-winner accepted-trade proxy, still shadow-blocked by low signal support."
