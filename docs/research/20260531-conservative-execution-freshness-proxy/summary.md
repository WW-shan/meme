# Conservative Execution-Freshness Proxy

Date: 2026-05-31

## Outcome

Outcome tier: `Research Alpha`, not `Shadow Candidate` and not live switch.

No live switch. No `.env`, model artifact, threshold, sizing, buy/sell logic, bot process, collector process, runtime enablement, or restart changed.

This boundary tightens the accepted-trade execution-freshness proxy after the quick-profit support rejection. The stricter final guard avoids skipping the `TripleT` winner that the previous proxy selected, while still selecting the latest accepted live losses. It remains proxy-only because the signal-level freshness shadow gate already showed broad chain-lag rules create too many opportunity misses.

## Why This Ran

The previous Changzhang freshness refresh selected:

- `lifecycle_status_chain_lag_seconds >= 1.8176350593566895`
- final selected `8` trades: `7` losses and `1` winner
- final abstention delta `+0.00034725861751158833` BNB

That was useful, but not conservative enough for a shadow/live path because it skipped the final winner `TripleT`. The new replay-promotion guard required final selected winners to be `0`.

## Experiment

```bash
venv/bin/python scripts/probe_execution_freshness_abstention.py \
  --since '2026-05-19 04:02:23' \
  --paper-trades data/paper_trades.jsonl \
  --signal-audit data/signal_audit.jsonl \
  --signal-match-tolerance-seconds 3 \
  --output data/replay_reports/execution_freshness_conservative_proxy_20260531_after_quick_profit_support_reject.json \
  --max-final-winner-count 0 \
  --force \
  --max-sample-rows 100
```

Report:

- `data/replay_reports/execution_freshness_conservative_proxy_20260531_after_quick_profit_support_reject.json`

Selected rule:

- `lifecycle_status_chain_lag_seconds >= 2.2289199829101562`

Candidate counts:

- paired real trades: `53`
- train / validation / final rows: `31 / 11 / 11`
- scanned rules: `248`
- train-eligible rules: `150`

## Results

Train:

- selected `13`
- losses / winners: `9 / 4`
- loss precision: `69.23%`
- abstention delta: `+0.00013578191663165585` BNB
- delta after removing top skipped-loss benefit: `-0.00009237487360547062` BNB

Validation:

- selected `2`
- losses / winners: `2 / 0`
- loss precision: `100.00%`
- abstention delta: `+0.0003500284027941525` BNB
- selected symbols: `光源light`, `Binance light source`

Final:

- selected `7`
- losses / winners: `7 / 0`
- loss precision: `100.00%`
- abstention delta: `+0.0004729108665257329` BNB
- delta after removing top skipped-loss benefit: `+0.0003090021235074042` BNB
- selected symbols: `42`, `币安盲盒`, repeated `帕鲁`, `四川话`, `长涨`

Compared with the previous proxy, this removes the final winner skip and increases final proxy delta from `+0.00034725861751158833` to `+0.0004729108665257329` BNB.

## Blocking Evidence

This still cannot promote to shadow/live.

Reasons:

- Train benefit is top-loss dependent: train delta after removing the top skipped loss is negative.
- The proxy is accepted-real-trade only and does not compute replay drawdown, walk-forward, stress, or paired trade delta.
- The existing signal-level freshness shadow report `data/replay_reports/signal_freshness_shadow_20260531_after_changzhang_close.json` rejected promotion: no train-selected signal-level freshness rule passed the holdout gate, and the broad chain-lag bucket had `80` opportunity misses.
- A live gate must not hard-code this threshold without replay-compatible or signal-level support.

## Decision

Keep execution freshness as `Research Alpha`.

This is stronger accepted-trade evidence than the previous proxy because it avoids final winner skips, but it is still not deployable. The next useful work is not another threshold sweep. It is either:

- make freshness causal/replay-compatible enough to evaluate drawdown, walk-forward, stress, and paired delta; or
- collect/live-shadow more queued/opened rows until signal-level opportunity-miss risk can be estimated without relying on a single broad chain-lag rule.

`docs/model_scoreboard.md` was updated because this boundary changes the current freshness proxy from "positive but skipped one final winner" to "conservative Research Alpha with zero final winner skips, still shadow-blocked."
