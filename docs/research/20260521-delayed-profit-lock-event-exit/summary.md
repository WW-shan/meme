# Delayed Profit-Lock / Event-Driven Exit Research

Date: 2026-05-21

## Live Trigger

The latest live v95 primary trade, `CMC` (`0x6258Ee743fa685D01811Fc1d8d4DB2a334eF4444`), was not a simple bad entry. It opened with `prob=0.9885040177112403`, `PredReturn=43.31655736431087`, and about `+5.2151%` entry slippage, then closed by `STOP_LOSS` after about `491.6s` for `-0.00022816` BNB.

Lifecycle path reconstruction from `data/training/lifecycle_incremental_20260516_212852_part001.jsonl` and `data/bot_data/lifecycle_incremental_20260519_040224.jsonl` shows:

- From entry price, `+25%` was hit about `225s` after entry.
- From entry price, `+35%` was hit about `459s` after entry.
- Peak was about `+37.18%` around `477s` after entry.
- The path then dropped below `-18%` within seconds and live exited by `STOP_LOSS`.

This is a different failure shape from the earlier short spike cases: the profitable path occurred after the previously tested `30-120s` fast profit-lock window.

## History Check

Already rejected directions:

- Global threshold reduction and broad volume relaxation admitted too many weak signals.
- Earlier global trailing reduced replay return and is not supported as a blanket fix.
- Fast profit-lock with windows `30/60/90/120s` slightly improved validation headline metrics but worsened stress, so it was rejected.
- Quick-profit overlay for rescued/new entries did not generalize to sealed final.
- Blanket partial exits and broad profit-path policy training were too permissive.

This experiment is intentionally narrower: no new entries, no larger position size, no broader threshold, no global earlier trailing. It only tests delayed full-position take-profit on trades that the current v95 stack would already enter.

## External Evidence

SmartSearch commands:

```bash
smart-search doctor --format json
smart-search deep "For event-driven early meme-token crypto trading, a live position can rise +25% to +35% after 3-8 minutes and then collapse below stop-loss within seconds before a trailing stop realizes profit. What research-supported exit design is robust: delayed profit-lock, conditional take-profit, trailing-stop ordering, triple-barrier/event-time labels, or meta-labeled exits, while avoiding over-cutting durable runners?" --format json --output docs/research/20260521-delayed-profit-lock-event-exit/plan.json
smart-search search "triple barrier method meta labeling exit strategy take profit stop loss trailing stop financial machine learning" --validation balanced --extra-sources 3 --timeout 90 --format json --output docs/research/20260521-delayed-profit-lock-event-exit/01-triple-barrier-meta-labeling-search.json
smart-search search "event driven trading take profit stop loss order priority backtesting intrabar bias trailing stop" --validation balanced --extra-sources 3 --timeout 90 --format json --output docs/research/20260521-delayed-profit-lock-event-exit/03-event-driven-exit-ordering-search.json
smart-search fetch "https://blog.quantinsti.com/triple-barrier-method-gpu-python/" --format markdown --output docs/research/20260521-delayed-profit-lock-event-exit/04-fetch-quantinsti-triple-barrier.md
smart-search fetch "https://www.interactivebrokers.com/campus/ibkr-quant-news/a-practical-breakdown-of-vector-based-vs-event-based-backtesting/" --format markdown --output docs/research/20260521-delayed-profit-lock-event-exit/05-fetch-ibkr-event-backtesting.md
smart-search fetch "https://www.quantstart.com/articles/Event-Driven-Backtesting-with-Python-Part-IV/" --format markdown --output docs/research/20260521-delayed-profit-lock-event-exit/06-fetch-quantstart-event-driven.md
smart-search fetch "https://www.ig.com/en/trading-strategies/what-are-take-profit-and-stop-loss-orders--how-do-they-work--230605" --format markdown --output docs/research/20260521-delayed-profit-lock-event-exit/07-fetch-ig-tp-sl.md
```

Relevant conclusions:

- Triple-barrier labeling frames exits as competing profit, stop, and time barriers. This matches the need to distinguish first-hit `+25/+35/+60`, `-18/-25`, and timeout outcomes instead of judging only terminal return.
- Event-driven backtesting is the right mode for path-dependent exits because the order of market events, pending exits, and fills changes realized results.
- Take-profit and stop-loss orders are complementary risk controls. For this repo, the replay already models a full-position profit-lock before stop-loss, with sell delay and fill-success accounting.
- Backtest evidence must be validated out-of-sample and under realistic costs; a single live example like CMC can trigger the hypothesis but cannot justify live switching alone.

## Hypothesis

Because live v95 selected a high-probability primary trade that reached delayed profit after `225-459s` and then collapsed before the existing trailing stack realized profit, a default-off delayed profit-lock replay with windows `180/240/360/480s` may improve realized profit without increasing entry count, position size, or threshold risk.

## Experiment

Run a bounded replay-only grid:

- Model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Position sizing: `0.10`
- Max open positions: `8`
- Fixed stake: `None`
- Profit targets: `0.25`, `0.35`, `0.45`, `0.60`
- Profit windows: `180`, `240`, `360`, `480` seconds
- Report: `data/replay_reports/delayed_profit_lock_replay_20260521_v95.json`

The grid deliberately excludes `30-120s` windows because that range was already tested and rejected.

## Result

Report: `data/replay_reports/delayed_profit_lock_replay_20260521_v95.json`

Decision: reject.

Validation baseline:

- Trades: `27`
- Net return: `181.5530636715994%`
- Net profit: `0.007184573512824603` BNB
- Win rate: `74.07407407407408%`
- Max drawdown: `-28.885773417921754%`
- Walk-forward worst return: `18.70207417090701%`
- Stress-worst return: `139.4841021820726%`

Best raw validation candidate:

- Params: `profit_lock_take_profit_pct=0.60`, `profit_lock_max_hold_seconds=180` or `240`
- Trades: `27`
- Net return: `122.35676590258366%`
- Net profit: `0.004842006858164075` BNB
- Win rate: `85.18518518518519%`
- Max drawdown: `-4.729691222681787%`
- Walk-forward worst return: `34.42388193334078%`
- Stress-worst return: `69.90310327741544%`
- Profit-lock exits: `15`

The candidate reduced drawdown and increased win rate, but it failed the two gates that matter most for live use: net profit and stress profitability. It appears to harvest some CMC-like cases but over-cuts enough durable winners that total edge falls. This falsifies a blanket delayed full-position profit-lock for current v95 positions.

Next direction: keep the CMC evidence, but shift from fixed TP windows to a conditional exit-state model after target hit, using post-target flow/path decay features before deciding whether to lock profit or continue holding.

## Falsification Rules

Reject the direction if any of these are true:

- Validation does not select a candidate under the strict gate.
- Sealed final does not strictly beat the current v95 baseline on net profit.
- Win rate, max drawdown, walk-forward worst return/drawdown, or stress worst return/profit/drawdown regress versus baseline.
- `profit_lock_take_profit_count == 0`.
- Improvement depends on one outlier while stress or trade quality worsens.
- The candidate requires increasing position size, max positions, or expanding entries.

Only if the replay is accepted should the next node add live runtime support for an equivalent default-off profit-lock config and then consider a zero-position `./tools/memectl bot restart`.
