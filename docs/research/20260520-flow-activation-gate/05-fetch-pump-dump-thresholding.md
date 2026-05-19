# Source Note: Crypto Pump-and-Dump Thresholding

- URL: https://arxiv.org/html/2503.08692v1
- Fetched with: `smart-search fetch ... --format markdown --output /tmp/meme-smartsearch-flow/pump-dump.md`
- Use in this repo: avoid treating every volume spike as a buy signal; require volume/price activation to clear context-sensitive noise filters.
- Relevant takeaway: low-liquidity crypto markets create many small spikes, and thresholding must account for noise to avoid over-flagging.
- Relevant takeaway: combining price and volume conditions with smoothed baselines and volatility filtering can improve precision for pump-like events.
- Live connection: recent high-score rejects with negative PredReturn and low volume were mostly correct skips, so the experiment should test a narrow flow gate, not a broad threshold relaxation.
