# Conditional Exit And Early Profit Research

## Question

How should this bot design a conditional exit or partial take-profit policy for highly volatile meme-token trades where live evidence shows a brief `+15%` to `+25%` rebound can disappear into a stop-loss cascade, while true runners still need room to continue?

## SmartSearch Commands

- `smart-search doctor --format json > docs/research/20260518-conditional-exit-early-profit/00-doctor.json`
- `smart-search deep "For highly volatile microcap meme-token trading, how should we design conditional exit or partial take-profit policies that capture early 15-25% rebounds before pump-and-dump stop cascades while still holding true runners, using path labels, order-flow features, and live execution costs?" --budget deep --format json --output docs/research/20260518-conditional-exit-early-profit/plan.json`
- `smart-search search "conditional exit partial take profit volatile crypto pump dump trading path labels order flow execution costs" --validation balanced --extra-sources 3 --timeout 90 --format json --output docs/research/20260518-conditional-exit-early-profit/01-search.json`
- `smart-search exa-search "triple barrier meta labeling conditional exit take profit stop loss path dependent trading" --num-results 5 --include-highlights --format json --output docs/research/20260518-conditional-exit-early-profit/02-exa-labeling-exit.json`
- `smart-search zhipu-search "加密货币 pump dump 早期止盈 条件退出 交易策略" --count 5 --format json --output docs/research/20260518-conditional-exit-early-profit/03-zhipu.json`
- `smart-search fetch "https://alphaarchitect.com/a-new-wolf-in-town-pump-and-dump-manipulation-in-cryptocurrency-markets/" --format markdown --output docs/research/20260518-conditional-exit-early-profit/04-fetch-alphaarchitect-pump-dump.md`
- `smart-search fetch "https://flipster.io/blog/cryptocurrency-trading-conditional-orders-guide" --format markdown --output docs/research/20260518-conditional-exit-early-profit/05-fetch-flipster-conditional-orders.md`
- `smart-search fetch "https://www.talos.com/insights/execution-alphas-in-crypto-markets-predicting-volume-volatility-and-spreads-to-reduce-slippage" --format markdown --output docs/research/20260518-conditional-exit-early-profit/06-fetch-talos-execution-alpha.md`
- `smart-search fetch "https://www.chainalysis.com/blog/crypto-crime-2024-pump-and-dump/" --format markdown --output docs/research/20260518-conditional-exit-early-profit/07-fetch-chainalysis-pump-dump.md`

`exa-search` and `zhipu-search` returned configuration errors because `EXA_API_KEY` and `ZHIPU_API_KEY` are not configured. No native web search fallback was used.

## Fetched Sources

- Alpha Architect: `https://alphaarchitect.com/a-new-wolf-in-town-pump-and-dump-manipulation-in-cryptocurrency-markets/`
- Flipster: `https://flipster.io/blog/cryptocurrency-trading-conditional-orders-guide`
- Talos: `https://www.talos.com/insights/execution-alphas-in-crypto-markets-predicting-volume-volatility-and-spreads-to-reduce-slippage`
- Chainalysis: `https://www.chainalysis.com/blog/crypto-crime-2024-pump-and-dump/`

## What Applies To This Bot

- Pump-and-dump paths are short-lived and can have large temporary price distortions. This matches the live `WAGMI` path: after entry it reached about `+18.2%` MFE, then fell to about `-30.6%` by receipt exit.
- Conditional orders and take-profit logic are useful as an automation pattern, but this bot cannot copy exchange-style OCO orders directly. The usable translation is a model/runtime policy that can trigger earlier partial or full exit when profit is available and order-flow quality weakens.
- Execution quality is part of the exit label, not an afterthought. Talos' execution framing supports feeding measured slippage and receipt timing back into model selection; for this bot, a `+15%` gross rebound is not enough unless it survives gas, sell delay, and exit slippage.
- On-chain manipulation indicators matter for the exit decision. Chainalysis highlights wash trading, low liquidity, and large-holder/liquidity removal patterns as investigation signals. This repo already has concentration, buyer/seller overlap, churn, repeat-buyer, and volume features that can feed a conditional exit model.

## What We Reject

- Do not add position size. The issue is path selection and exit timing, not insufficient stake.
- Do not globally lower the buy threshold to capture missed runners. The 2026-05-18 high-PredReturn rejection sweep found `王福满` as a real missed runner, but most rejected candidates with available paths still ended below the signal base.
- Do not globally force earlier trailing for every trade. Earlier sweeps already showed global early trailing reduced replay return; the research supports conditional exits, not one fixed shorter hold rule.
- Do not use broad SmartSearch summaries as proof. Only fetched sources above should be used as evidence.

## Next Experiment

Use the current v84-style entry stack as the primary entry gate and test a separate conditional-exit candidate:

- Label trades or path samples where price reaches `+15%`, `+20%`, or `+25%` after entry and then falls below stop before reaching a larger runner target.
- Add an exit action or policy rule that can take full profit, or a simulated partial profit if the replay engine supports it, when early MFE appears and order-flow deterioration features trigger.
- Penalize any exit target whose expected gross profit does not clear current gas, sell delay, and slippage assumptions.
- Compare against v84 `max_hold=560` baseline on final return, drawdown, walk-forward worst segment, harsh friction, and harsh execution before considering live deployment.
