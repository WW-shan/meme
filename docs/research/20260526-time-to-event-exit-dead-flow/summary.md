# 2026-05-26 Time-To-Event Exit / Runner-Retention Round

## Question

Today live evidence showed one real `TIME_EXIT` loss on `CHILLCAT` and a fresh rejected-signal path sample. The question was whether the best next model-improvement direction is a data-driven exit / hold policy using time-to-event, survival, or triple-barrier labels, rather than another static threshold, dead-flow rule, or global hold-time tweak.

## SmartSearch Commands

```bash
smart-search doctor --format json
smart-search deep "What method best supports a data-driven exit policy for trades that peak early and then decay, using time-to-event / survival / triple-barrier labels and execution-aware costs?" --format json --output docs/research/20260526-time-to-event-exit-dead-flow/plan.json
smart-search search "survival analysis trading exit time to event triple barrier meta labeling paper" --validation balanced --extra-sources 3 --format json --output docs/research/20260526-time-to-event-exit-dead-flow/01-search.json
smart-search fetch "https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/" --format markdown --output docs/research/20260526-time-to-event-exit-dead-flow/02-fetch-hudson-thames.md
smart-search fetch "https://link.springer.com/article/10.1007/s10614-024-10567-8" --format markdown --output docs/research/20260526-time-to-event-exit-dead-flow/03-fetch-springer.md
smart-search fetch "https://ideas.repec.org/a/kap/compec/v64y2024i6d10.1007_s10614-024-10567-8.html" --format markdown --output docs/research/20260526-time-to-event-exit-dead-flow/04-fetch-repec.md
```

## Fetched Sources

- Hudson & Thames, "Does Meta Labeling Add to Signal Efficacy?": supports event-based sampling, triple-barrier path labels, and meta-labeling as a secondary decision layer around a primary strategy.
- Springer, Hu and Zhou (2024), "Trading Signal Survival Analysis": supports integrating a primary trading signal with a survival model where the trading signal defines the observation start and an investment target is treated as the event of interest.
- RePEc entry for the same Hu and Zhou paper: bibliographic cross-check only; the Springer page is the stronger fetched evidence.

## What Applies To This Bot

- The live issue should be framed as time-to-event / path competition, not as a token-specific rule. `CHILLCAT` was classified as `dead_flow_timeout`, and rejected-signal paths contained `slow_runner=3`, `fast_profit_then_collapse=1`, `flat_timeout=22`, and `stop_first=8`.
- The fetched method evidence supports using path labels with a vertical time barrier and a secondary decision layer. For this bot, that maps better to a replay-integrated `conditional_slow_hold` / runner-retention candidate gate than to a static live dead-flow exit.
- The current best baseline remains `data/models/20260519_v95_v84_selective_nearmiss_gate` at 10% sizing.

## What We Reject

- Reject a live dead-flow / timeout exit rule now. The current feasibility probe kept `support_gate=NO_GO_FOR_LIVE_RULE`: validation positives were `0`, final positives were `4`, and the current live slice had only `1` closed trade.
- Reject any live switch, `.env` change, threshold change, sizing change, model artifact change, or bot restart from this round.
- Reject treating broad SmartSearch synthesis as proof without fetched source text.

## Experiments

```bash
python scripts/probe_live_trade_attribution.py \
  --paper-trades data/paper_trades.jsonl \
  --signal-audit data/signal_audit.jsonl \
  --collector-state data/training/collector_runtime_state.json \
  --lifecycle-dir data/training \
  --recent-lifecycle-files 2 \
  --output-json data/replay_reports/live_trade_attribution_20260526_today_round.json \
  --output-md data/replay_reports/live_trade_attribution_20260526_today_round.md \
  --since 2026-05-26T00:00:00 \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --force

python scripts/probe_conditional_exit_feasibility.py \
  --live-attribution data/replay_reports/live_trade_attribution_20260526_today_round.json \
  --train-post-target-report data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_train_enriched.json \
  --validation-post-target-report data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_validation.json \
  --final-post-target-report data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_final.json \
  --output-json docs/research/20260526-time-to-event-exit-dead-flow/10-exit-state-feasibility.json \
  --output-md docs/research/20260526-time-to-event-exit-dead-flow/10-exit-state-feasibility.md \
  --force

python scripts/probe_runner_retention_label_support.py \
  --model-dir data/models/20260519_v95_v84_selective_nearmiss_gate \
  --lifecycle-dir data/training \
  --live-attribution data/replay_reports/live_trade_attribution_20260526_today_round.json \
  --output docs/research/20260526-time-to-event-exit-dead-flow/11-runner-retention-label-support-12files.json \
  --force \
  --max-lifecycle-files 12 \
  --include-shadow-score-rejects \
  --shadow-min-prob 0.94 \
  --shadow-max-entry-score 35 \
  --shadow-min-entry-volume-30s 1.25 \
  --shadow-min-entry-price-volatility 0.08 \
  --shadow-max-age-seconds 300 \
  --group-bucket-seconds 30 \
  --horizon-seconds 600 \
  --quick-profit-seconds 25 \
  --slow-min-plus25-seconds 180 \
  --min-train-positives 3 \
  --min-validation-positives 3 \
  --min-final-positives 3 \
  --min-live-positives 3
```

Results:

- Live attribution: `1` closed trade, `0` wins, `1` loss, net `-0.0000253190` BNB; `CHILLCAT` labeled `dead_flow_timeout`. Rejected paths: `slow_runner=3`, `fast_profit_then_collapse=1`, `flat_timeout=22`, `stop_first=8`.
- Conditional-exit feasibility: `NO_GO_FOR_LIVE_RULE`; no replay-equivalent validation support for dead-flow or post-target collapse promotion.
- Runner-retention support: `PASS_OFFLINE_SUPPORT`; train / validation / final positives `375 / 60 / 50`, unique positive tokens `133 / 23 / 21`, and live slow-runner positives `3`, meeting the `min_live_positives=3` support gate. The report still says `NO_GO_FOR_LIVE_SWITCH` because it is read-only support evidence.

## Decision

Business decision: `continued with named next direction`.

The next highest-value direction is a replay-integrated runner-retention / `conditional_slow_hold` candidate gate using the slow-runner label, compared strictly against the current v95 baseline with validation, final, walk-forward, stress, trade-count, drawdown, and 10% sizing gates. This round does not change live config or switch models.
