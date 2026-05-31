# 2026-05-31 Changzhang Freshness Refresh

## Question

After the direct-utility shadow-ranker hard reject, the latest live loss was `长涨`, a `TIME_EXIT` / `dead_flow_timeout` trade. Does this new accepted loss strengthen the replay-compatible execution-freshness direction enough to promote it beyond Research Alpha?

## Live Context

- Active live model stayed `data/models/20260519_v95_v84_selective_nearmiss_gate`.
- Live trading stayed enabled at the existing 10% sizing.
- Bot and collector stayed running.
- `data/bot_state.json` had no open positions during the refresh.
- No `.env`, model artifact, threshold, sizing, bot process, collector process, runtime enablement, or restart changed.

Latest committed attribution before this refresh:

- `data/replay_reports/live_trade_attribution_20260531_after_changzhang_close.json`
- `data/replay_reports/live_trade_attribution_20260531_after_changzhang_close.md`

That attribution found `长涨` closed at `2026-05-31 12:37:23.249196` as a `TIME_EXIT` / `dead_flow_timeout` loss of `-0.00005421706409925337` BNB.

## Prior Review

- `docs/research/20260531-replay-compatible-execution-freshness/summary.md` already classified execution freshness as Research Alpha, not shadow/live evidence.
- `docs/research/20260530-activation45-dead-flow-exit/summary.md` rejected bounded dead-flow min-hold / max-MFE overlays; activation45 remains useful because of the control branch, not the dead-flow overlay.
- `docs/research/20260530-next-structural-round/summary.md` hard-rejected non-broad quick-profit overlay replay because final net profit, win rate, drawdown, walk-forward, stress, and paired delta all collapsed.
- Direct utility shadow ranking was just rejected in `docs/research/20260531-direct-paired-delta-utility-ranker/summary.md`; do not micro-sweep that family.

## Hypothesis Portfolio

| Rank | Direction | Decision |
|---:|---|---|
| 1 | Accepted-trade execution-freshness abstention refresh | Selected. It targets repeated real accepted losses without adding trades or increasing sizing. |
| 2 | Signal-level freshness split shadow | Selected as a falsification check. A live gate needs more than accepted-trade proxy evidence. |
| 3 | Conditional dead-flow exit / entry abstention | Deferred. Latest loss matches the family, but bounded dead-flow overlays were just rejected and same-shape accepted support is still sparse. |
| 4 | Fast-profit / quick-harvest detector | Deferred. Live rejected support is large, but replay history says quick-profit overlays are high-risk unless the decision point or label changes materially. |

## Experiment

Accepted-trade proxy refresh:

```bash
venv/bin/python scripts/probe_execution_freshness_abstention.py \
  --since '2026-05-19 04:02:23' \
  --paper-trades data/paper_trades.jsonl \
  --signal-audit data/signal_audit.jsonl \
  --signal-match-tolerance-seconds 3 \
  --output data/replay_reports/execution_freshness_latency_volatility_probe_20260531_after_changzhang_close.json \
  --force \
  --max-sample-rows 100
```

Signal-level split shadow:

```bash
venv/bin/python scripts/probe_signal_freshness_shadow.py \
  --since '2026-05-31 00:19:40' \
  --recent-lifecycle-files 64 \
  --split-stability \
  --min-candidates 30 \
  --min-selected 5 \
  --min-split-candidates 5 \
  --min-split-selected 1 \
  --max-candidate-sample 200 \
  --output-json data/replay_reports/signal_freshness_shadow_20260531_after_changzhang_close.json \
  --output-md data/replay_reports/signal_freshness_shadow_20260531_after_changzhang_close.md \
  --force
```

## Result

Accepted-trade proxy:

- Outcome tier: `Research Alpha`.
- Decision: `research_alpha_proxy_requires_replay_and_signal_time_logging`.
- Paired real trades: `53`.
- Selected rule: `lifecycle_status_chain_lag_seconds >= 1.8176350593566895`.
- Train selected `16` trades: `12` losses, `4` winners, abstention delta `+0.0005545021460338318` BNB.
- Validation selected `3` trades: `3` losses, `0` winners, abstention delta `+0.00037092635873943236` BNB.
- Final selected `8` trades: `7` losses, `1` winner, abstention delta `+0.00034725861751158833` BNB.
- Final delta after removing the top skipped-loss benefit stayed positive at `+0.00018334987449325962` BNB.
- Final selected symbols included `TripleT`, `42`, `币安盲盒`, repeated `帕鲁`, `四川话`, and `长涨`.

Signal-level split shadow:

- Outcome tier: `Rejected`.
- Decision: `no_signal_freshness_train_rule_passed`.
- Signal decisions: `10885`.
- Freshness/path-evaluable candidates: `778`.
- Barrier classes: `fast_profit=24`, `fast_profit_then_collapse=39`, `flat_timeout=533`, `slow_runner=17`, `stop_first=165`.
- The best simple chain-lag-like rules selected very large rejected-signal buckets with high flat/stop precision, but also missed many opportunity paths. The top selected rule had `80` total opportunity misses across all splits.
- Stable rule count: `0`; train-eligible rule count: `0`.

## Tier

Execution freshness remains `Research Alpha`, not `Shadow Candidate`.

This refresh strengthens the accepted-trade abstention proxy because it now includes the latest `长涨` loss and remains positive after top-loss removal. It does not justify a live switch because the signal-level split shadow failed, and the evidence still lacks replay-integrated validation/final/walk-forward/stress/paired-delta support.

## Next Direction

Do not hard-code the chain-lag threshold. The next useful step is either:

- integrate decision-time freshness context into replay-compatible selected-trade delta or a queued/opened shadow evaluator; or
- if replay integration cannot be made causal enough, pivot to another structural direction rather than sweeping dead-flow or quick-profit parameters.

## Scoreboard

`docs/model_scoreboard.md` was updated because this refresh changes the current execution-freshness status after the latest live loss.
