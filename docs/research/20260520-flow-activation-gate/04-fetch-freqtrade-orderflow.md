# Source Note: Freqtrade Orderflow

- URL: https://www.freqtrade.io/en/stable/advanced-orderflow/
- Fetched with: `smart-search fetch ... --format markdown --output /tmp/meme-smartsearch-flow/freqtrade-orderflow.md`
- Use in this repo: approximate orderflow with available on-chain lifecycle events: buy/sell volume, buy/sell counts, buy pressure, delta, and event counts near the signal.
- Relevant takeaway: raw trade data can be transformed into orderflow fields such as bid/ask volume, delta, total trades, imbalances, and cumulative delta.
- Relevant takeaway: orderflow data is larger and heavier than candle aggregates, so replay experiments should compute bounded windows around candidate signals instead of loading everything indiscriminately.
- Live connection: `赵长娥` had rapid post-signal activation; `x402` had no meaningful post-entry flow after signal. A bounded pre/post flow window is the right falsifiable unit.
