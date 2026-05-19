# Flow Activation Gate Research Summary

## Live Trigger

- Bot and collector were healthy under `memectl`; state had `0` open positions and balance `0.005093225171475348` BNB.
- Latest live model in `.env` is `data/models/20260519_v95_v84_selective_nearmiss_gate`, with 10% sizing semantics preserved by empty `FIXED_STAKE_BNB` and `MAX_CONCURRENT_POSITIONS=8`.
- Latest profitable trade: `赵长娥`, `prob=0.990143`, `PredReturn=65.7099`, entry slippage `+14.2831%`, signal-to-open `2.4718s`, PPO exit after `49.9187s`, net `+0.0001979536` BNB.
- `赵长娥` path from signal reached `+25%` in about `4.13s`, `+35%` in about `6.13s`, and `+60%` in about `11.13s`; from actual entry it reached `+25%` in about `5.66s` and `+35%` in about `7.66s`.
- Recent failures: `TSG` hit `-18%` about `86.55s` after signal with only about `+9.66%` MFE from signal; `WAGMI` hit `-18%` about `3.66s` after signal; `币安 x402` had no meaningful post-entry upside and exited by time at a small loss.
- Recent high-score rejects such as `彭湃`, `Alice`, `BBC`, and `BNBBurn` mostly had negative `PredReturn`, supporting the current entry-value filter.

## Research Takeaways

- Meta-labeling should be a secondary take/skip layer on a useful primary model, not a replacement for the primary v95/v84 signal stack.
- Triple-barrier labels match this market better than fixed-horizon labels because the order of first touch matters: fast profit, stop-first, and time-expiry are distinct outcomes.
- Orderflow features should come from bounded raw event windows: buy/sell volume, buy pressure, event count, volume acceleration, and flow delta around the candidate signal.
- Pump/fakeout research reinforces that low-liquidity volume spikes need context-sensitive filters; broad volume relaxation or threshold lowering is not justified by the live evidence.

## Hypothesis

Because live `赵长娥` shows clean flow activation while `TSG`, `WAGMI`, and `x402` show stop-first or dead-flow behavior, test a replay-level flow activation gate that keeps the v95 primary/near-threshold candidate generator unchanged but requires recent trajectory/flow confirmation or applies an early dead-flow exit. This should improve profit or reduce weak entries without increasing position size.

## Falsification

Reject the direction if validation or final replay loses to the current v95/best baseline on net profit, max drawdown, walk-forward worst return, harsh stress, or if the improvement comes only from materially reducing trade count.

## Commands

- `smart-search doctor --format json`
- `smart-search deep "How can order-flow activation, volume acceleration, and triple-barrier/meta-labeling be used to distinguish real crypto meme coin breakouts from fake pumps and improve live entry/exit decisions without increasing position size?" --budget standard --evidence-dir docs/research/20260520-flow-activation-gate --format json --output docs/research/20260520-flow-activation-gate/plan.json`
- `smart-search search "order-flow activation volume acceleration triple-barrier meta-labeling crypto breakout fake pump entry exit" --validation balanced --extra-sources 3 --format json --output docs/research/20260520-flow-activation-gate/01-search.json`
- `smart-search fetch "https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/" --format markdown --output /tmp/meme-smartsearch-flow/hudson-meta.md`
- `smart-search fetch "https://mlfinpy.readthedocs.io/en/latest/Labelling.html" --format markdown --output /tmp/meme-smartsearch-flow/mlfinpy-labelling.md`
- `smart-search fetch "https://www.freqtrade.io/en/stable/advanced-orderflow/" --format markdown --output /tmp/meme-smartsearch-flow/freqtrade-orderflow.md`
- `smart-search fetch "https://arxiv.org/html/2503.08692v1" --format markdown --output /tmp/meme-smartsearch-flow/pump-dump.md`
