# Entry Slippage / Pump Exhaustion Research - 2026-05-21

## Live Trigger

Current live model `data/models/20260519_v95_v84_selective_nearmiss_gate` has lost money since the 2026-05-19 04:02 restart. The most damaging live failures are high PredReturn entries that were already extended or had poor follow-through:

- `FENGSHUI` primary entry: `PredReturn=103.27`, entry slippage `+66.04%`, `ENTRY_SLIPPAGE_PROTECTION`, net `-0.00040260` BNB. Lifecycle path from signal had only `+1.44%` MFE and hit `-18%/-25%` within about `5.35s`; pre-entry extension over the prior 120s was about `+303%`.
- Second `FENGSHUI` primary entry: `PredReturn=70.21`, net `-0.00032684` BNB. It later had large MFE but also hit the stop zone before the bot could keep durable profit; pre-entry extension was about `+282%`.
- `挠头`: `PredReturn=58.58`, entry slippage `+34.82%`, slippage-protection exit. It hit `+25%` almost immediately after signal but the actual fill arrived after the spike, so entry-to-close MFE was `0%`.
- Near-threshold rescue trades after v95 restart were all losers in the current live sample: `币安 x402`, `BNBGUY`, `饼小龙`, `黄金夏日`, and `BNA`, together about `-0.00021918` BNB.

Failure tags: `late_pump_chase`, `entry_slippage_risk`, `fake_breakout_or_exhaustion`, `near_rescue_overreach`, `execution_fill_lag_exposure`.

## SmartSearch Evidence

Commands and saved evidence:

- `smart-search doctor --format json > docs/research/20260521-entry-slippage-pump-exhaustion/00-doctor.json`
- `smart-search deep "How can an automated crypto meme-token trading model identify pump exhaustion..." --format json > docs/research/20260521-entry-slippage-pump-exhaustion/01-deep-plan.json`
- `smart-search search "crypto pump exhaustion fake breakout entry slippage risk pre-entry price volume order flow features meta-labeling pump and dump detection time series validation" --validation balanced --extra-sources 3 --format json --output docs/research/20260521-entry-slippage-pump-exhaustion/02-search.json`
- Fetched source evidence:
  - `03-fetch-springer-pump-dump.md` from https://link.springer.com/article/10.1186/s40163-018-0093-5
  - `04-fetch-arxiv-detecting-pump.md` from https://arxiv.org/html/2503.08692v1
  - `05-fetch-talos-slippage.md` from https://www.talos.com/insights/execution-alphas-in-crypto-markets-predicting-volume-volatility-and-spreads-to-reduce-slippage
  - `06-fetch-mlfinpy-labelling.md` from https://mlfinpy.readthedocs.io/en/latest/Labelling.html

Doctor result: main search and fetch were available through xAI/Tavily; Exa/Zhipu were not configured, so this round used `smart-search search` plus fetched pages rather than Exa.

## Evidence Takeaways

- The Springer pump-and-dump paper frames crypto P&D as a sequence of accumulation, pump, and dump, and emphasizes anomalous price/volume behavior as detectable exchange-data evidence. This matches the live FENGSHUI failure where the bot bought after a large pre-entry extension and then saw a fast dump.
- The 2025 arXiv thresholding paper focuses on EWMA/volatility-aware thresholds for low-liquidity crypto P&D detection. The useful idea for this repo is not another broad classifier, but per-token relative features: extension vs recent lows, volume spike vs recent baseline, volatility-adjusted anomaly, and avoiding low-liquidity noise.
- The Talos execution/slippage article supports explicitly forecasting execution conditions such as volume, volatility, and spreads to reduce crypto slippage. For this bot, the analogous features are recent on-chain volume, price volatility, price jump between lifecycle samples, and fill-lag exposure under `entry_max_fill_wait_seconds`.
- MLFinPy labeling documentation supports triple-barrier/meta-labeling and trend-scanning labels. For this repo, the primary v95/v84 model should remain the side generator, while a second-stage meta-label or deterministic veto should answer: "will this specific signal survive the next fill-delay window and hit profit before stop?"

## Optimization Implications

Avoid repeating already rejected broad directions:

- Do not globally lower the buy threshold.
- Do not globally relax volume.
- Do not use raw runner probability alone.
- Do not use token balancing alone.
- Do not deploy blanket partial exits or blanket profit locks.
- Do not simply hold everything longer.

Promising next falsifiable experiment:

1. Keep v95 primary and near-threshold candidate generation unchanged.
2. Add a replay-only, candidate-level `entry_slippage_risk_veto` or meta-gate over the existing runtime candidates.
3. Candidate features should be causal and small:
   - pre-entry extension from recent 120s low;
   - drawdown from recent peak;
   - most recent price jump / return over last sample interval;
   - recent volume ramp vs previous samples;
   - volatility ramp;
   - buy probability and PredReturn deltas;
   - estimated fill-lag exposure using current live `signal_to_open`/fill-lag quantiles.
4. Labels should prioritize live-relevant failure:
   - negative if entry-delay simulated fill would exceed `entry_price_protection_pct`, hit `-18%` before `+25%`, or have high slippage with no post-fill MFE;
   - positive only if it reaches `+25%` or `+60%` after realistic fill delay before stop.
5. Validation must compare to the current best baseline with 10% sizing, walk-forward, stress replay, trade-count discipline, and no live switch unless it strictly improves.

Minimal first probe: a deterministic sweep using pre-entry extension and entry-slippage-risk features before training another broad model. This directly addresses the live `FENGSHUI` / `挠头` failures and is structurally different from the rejected broad path-state classifier because it targets only pump-extension/fill-risk conditions.
