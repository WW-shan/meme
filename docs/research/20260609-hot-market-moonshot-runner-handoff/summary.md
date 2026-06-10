# Hot-Market Moonshot Runner Strategy Handoff

Created: 2026-06-09

Purpose: preserve the current findings and user intent for a fresh session. This is a research/design handoff only. Do not treat it as approval to implement runtime changes.

## Session State

- Repo: FourMeme Hybrid Trading System.
- Active CCG node: `live-model-optimization-20260528-flow-toxicity-meta-gate-refresh`.
- CCG node status at handoff: not archived.
- Latest non-`.ccg` code commit known good: `584830e research: reject conditional exit shadow refresh`.
- Commit/push/CI state: `584830e` was committed, pushed to `origin/main`, and GitHub Actions CI was green.
- Important project guardrails:
  - Do not edit `docs/goals/**` unless the user explicitly asks for goal-doc changes.
  - `.ccg/**` is local workflow state only. Do not commit or push `.ccg/**`.
  - For M+ work, use current Codex analysis plus external Claude as the second view before implementation.
  - Do not call Gemini, and do not spawn an external Codex instance.

## User Intent

The user is dissatisfied with the prior research loop because the short-hold strategy has consumed too much research time without yielding a formally live-ready strategy.

The user wants to change direction:

- Stop optimizing only for a few-minute holding period.
- Design a strategy for hot BNB Chain / FourMeme market conditions.
- The user will manually decide when the overall BNB/FourMeme market is hot and will only start live trading then.
- Do not add a new internal "market hot" switch. If the market is cold, the user simply will not start live trading.
- Keep the same position sizing idea as before: one trade uses 10% position size, then ends. No special new concurrency design is requested.
- The new model should identify tokens with large upside potential and buy them for long holding periods.
- The target examples are tokens like "币安人生 / Binance Life", where the user may want to wait for very large multiples before selling the first portion.
- Exit behavior should be chosen by backtest, not by assumption. Test many variants, including 10x/20x/50x/100x partial exits, trailing stops, very long holds, and never-selling-first approaches.

The user can judge macro heat through social media, but cannot provide real-time per-token narrative/social instructions. If narrative/social signals matter, the system needs an automated monitoring design.

## Current Runtime/Data Status From Last Check

Last checked around 2026-06-09 10:30 Asia/Shanghai:

- Collector was running.
- Bot was running.
- `data/signal_audit.jsonl` was still being updated, so live signal data was still being collected.
- Latest rows were around `2026-06-09 10:30:27`.
- The latest paper-trade close remained `2026-06-07 12:25:39.499918`.
- No new real trading activity was found after that point.

Recent signal slice from `signal_audit`:

- Last 15 minutes:
  - 101 `SIGNAL_DECISION` rows.
  - 6 unique tokens.
  - 0 queued.
  - `shadow_used=0`.
  - Routes: 91 `skip`, 10 `quick_take_profit`.
- Last 60 minutes:
  - 389 signals.
  - 19 unique tokens.
  - 0 queued.
  - `shadow_used=5`.
  - Routes: 341 `skip`, 42 `quick_take_profit`, 6 `continue_hold`.

Interpretation: the existing model/runtime path was still mostly abstaining and should not be treated as a green light for live long-hold trading.

## Existing Short-Hold System Findings

The current bot is structurally a short-hold system:

- `src/trader/bot.py` has a hard time exit around the `time_held >= hold_time_seconds` path, closing with `TIME_EXIT`.
- The current continue-hold path can suppress PPO sell decisions, but it does not override the hard time exit.
- Stop-loss enforcement remains active and should not be suppressed casually.
- `config/trading_config.py` contains `MOONSHOT_*` settings, but repository search found no active runtime use in `src/trader`, `config`, `.env.example`, or tests beyond the config definitions.

Conclusion: the old `MOONSHOT_*` knobs are not an active moonshot strategy. A real long-hold runner strategy needs a separate design rather than another small tweak to current continue-hold logic.

## Local Lifecycle Runner Scan

A read-only scan of local lifecycle data was performed:

- Files scanned: 36 lifecycle jsonl files.
- Approximate size: 4.1 GB.
- Rows scanned: 596,624.
- Unique tokens: 297,721.

Observed multiplier counts using `price_first -> price_max`:

| Threshold | Token count |
|---|---:|
| `>=2x` | 19,981 |
| `>=5x` | 4,762 |
| `>=10x` | 1,835 |
| `>=20x` | 0 |
| `>=50x` | 0 |
| `>=100x` | 0 |

Highest locally observed multiplier was about `15.35x`.

Conclusion: local data cannot directly train a true 100x classifier. It can support a local `>=10x` runner proxy model, but true 20x/50x/100x labels need external historical data.

## Local `>=10x` Proxy Features

The `>=10x` proxy positive class is rare:

- Positive count: 1,835.
- Base positive rate: about 0.6163%.

Compared with `<2x` tokens, local `>=10x` runners showed much stronger early flow:

| Feature | `>=10x` median | `<2x` median |
|---|---:|---:|
| 30s buy volume | 10.1174 BNB | 0.6139 BNB |
| 30s unique buyers | 24 | 2 |
| 30s price change | 122.55% | 0% |
| 60s buy volume | 18 BNB | 0.6421 BNB |
| 60s unique buyers | 44 | 2 |
| 60s price change | 183.4% | 0% |
| 300s buy volume | 46.3137 BNB | 0.6535 BNB |
| 300s unique buyers | 153 | 2 |
| 300s price change | 515.47% | 0% |

Sell pressure was weaker as a separating feature:

- 30s sell pressure median: positive 0.3174 vs negative 0.3347.
- 60s sell pressure median: positive 0.3693 vs negative 0.4966.
- 300s sell pressure median: positive 0.4179 vs negative 0.5.

Single-feature lift examples:

| Rule | Selected | Precision | Coverage | Lift |
|---|---:|---:|---:|---:|
| `price_change_300s_pct >= 7.3683` | 29,773 | 5.57% | 90.41% | 9.04x |
| `unique_buyers_300s >= 15` | 29,773 | 5.23% | 88.83% | 8.49x |
| `price_change_60s_pct >= 18.5638` | 29,773 | 4.99% | 80.98% | 8.10x |
| `unique_buyers_60s >= 12` | 29,815 | 4.71% | 76.89% | 7.64x |

Interpretation:

- Early on-chain runner signals are learnable.
- The main early indicators are broad buyer diffusion, high BNB buy volume, and fast price appreciation.
- The base rate is very low, so a production strategy needs a multi-factor model and strong validation.
- Single-feature gates are useful diagnostics, not sufficient trading rules.

## External Moonshot Research Findings

Early source-backed research suggests that very large BNB/FourMeme meme runners are not explained by on-chain flow alone.

For "币安人生 / Binance Life":

- PANews/Foresight reporting described a move from about `$0.001` to above `$0.5` within days, with market cap above `$500M` and early-investor examples reaching very large multiples.
- The same reporting connected the move to Binance/FourMeme ecosystem heat, Chinese community attention, CZ/He Yi social interaction, and related BNB meme attention.
- CoinMarketCap described Binance Life as BNB Chain native and cultural/community/narrative-driven, with value driven by sentiment and cultural resonance rather than utility.

Interpretation:

- A long-hold runner model should include external attention and narrative features, not only local chain flow.
- The user can provide macro timing by choosing when to run live, but the system still needs automated token-level social/narrative monitoring.

## Candidate External Data Sources

These sources were identified for continued investigation. Verify access, pricing, rate limits, chain coverage, and historical depth before implementation.

### DEX Screener

Official API research found REST and WebSocket surfaces.

Potentially useful endpoints/signals:

- Token profiles and recent profile updates.
- Community takeovers.
- Ads.
- Token boosts, latest and top.
- Pair data and token-pair data.
- Trending metas.
- WebSocket streaming for token profiles, boosts, and community takeovers.

Use case:

- Candidate discovery.
- External attention and paid-attention features.
- Profile/social-link availability.
- Pair liquidity, volume, and DEX-level market context.

### X / Twitter API

Official API research found:

- Recent search.
- Filtered stream.
- Rule-based monitoring.

Use case:

- Monitor selected accounts, keywords, cashtags, contract-address mentions, and symbol mentions.
- Candidate account groups include CZ, He Yi, Binance, BNB Chain, FourMeme, and high-signal Chinese crypto KOLs.

Constraint:

- Do not design this as full-network social scraping. It should be bounded, deduped, and cost-aware.

### CoinGecko / GeckoTerminal

CoinGecko Onchain DEX API research found trending-pool style data that may include:

- Price changes over multiple windows.
- Transactions, buys, sells, buyers, sellers.
- Volume.
- Liquidity/reserve data.
- Community/suspicious reports depending on API tier/data availability.

Use case:

- External trending-pool context.
- Cross-check DEX Screener data.
- Historical labels and replay features if API tier supports it.

Constraint:

- Likely needs a Pro API key for the useful onchain endpoints.

### GMGN

Search results suggest possible support for:

- Meme token trending.
- Smart money and KOL-related data.
- Holder/trader/security dimensions.
- BSC support.

Use case:

- Smart-money participation.
- KOL wallet activity.
- Holder/trader quality.
- Security/rug filtering.

Constraint:

- Official API usability, pricing, and terms still need to be verified from primary docs before relying on it.

### Four.meme / Bitquery / Codex

Search results suggest potentially useful FourMeme-specific data:

- Token creations.
- Live trades.
- Bonding curve progress.
- OHLCV.
- Liquidity/migration state.
- Top buyers/traders.
- Market cap.
- Lifecycle stage such as Created, Completing, Completed, Migrated.

Use case:

- Native launch lifecycle features.
- External backfill of true runner labels.
- Replay-compatible features at candidate decision time.

Constraint:

- Must verify official/primary documentation and API access before implementation.

### Lookonchain

No stable public developer API was confirmed in the initial search.

Use case:

- Treat as an optional attention feed if accessible through official channels, X, app, or Telegram.

Constraint:

- Do not make Lookonchain a core dependency unless a reliable API is confirmed.

## Recommended New Strategy Direction

The next research line should be a hot-market moonshot runner model:

1. Assume live trading is only started manually during hot BNB/FourMeme conditions.
2. Do not add an internal hot-market switch.
3. Train local `>=10x` runner proxy from existing lifecycle data.
4. Build an external label table for true 20x/50x/100x runners.
5. Add external attention, narrative, DEX, smart-money, and lifecycle features.
6. Backtest entries using only features available at decision time.
7. Backtest long-hold exits separately.
8. Run shadow scoring before any live deployment.

## Proposed Label Design

Create a moonshot label table with at least:

- Chain.
- Token contract.
- Pair address if available.
- Launch time.
- First observed price.
- Max observed price.
- `max_multiple`.
- `time_to_2x`.
- `time_to_5x`.
- `time_to_10x`.
- `time_to_20x`.
- `time_to_50x`.
- `time_to_100x`.
- Migration/completion time if FourMeme lifecycle data is available.
- DEX/profile/boost/CTO events.
- Social event timestamps.
- Narrative tags.
- Evidence URLs.
- Data-source provenance and fetch timestamp.

Important: labels must be time-aware. Do not leak future information into entry features.

## Proposed Feature Groups

Use only features visible at or before candidate decision time.

### Local On-Chain Flow

- Early buy volume over 30s/60s/300s.
- Early sell volume and sell pressure.
- Unique buyers and buyer diffusion.
- Price change over short windows.
- Transaction count, buy/sell count.
- Holder growth if available.
- Repeated buyer quality if inferable.

### FourMeme Lifecycle

- Token age.
- Bonding curve progress.
- Completion/migration status.
- Time since creation.
- Market cap/liquidity at each stage.
- Top buyer concentration.

### DEX Attention

- DEX Screener profile existence/update timing.
- Boost presence and boost amount if available.
- Community takeover status.
- Ads status.
- Trending/meta rank.
- Liquidity and volume context.

### Social/Narrative

- Mention velocity.
- Unique account count.
- High-signal KOL mentions.
- Official ecosystem account mentions/interactions.
- Contract-address mentions.
- Symbol/name mentions with collision controls.
- Chinese-language narrative keywords.
- Related ecosystem terms such as Binance, BNB, FourMeme, CZ, He Yi.

### Smart Money / Holder Quality

- Smart-money buys.
- KOL wallet participation.
- Top holder concentration.
- Suspicious bundle/rat-trader/security flags.
- Early buyer retention or rapid dumping behavior.

## Proposed Model Targets

Use a multi-target approach rather than one binary classifier:

- `P(max_multiple >= 10x)`.
- `P(max_multiple >= 20x)`.
- `P(max_multiple >= 50x)`.
- `P(max_multiple >= 100x)` if enough external positives exist.
- `expected_log_mfe`.
- Time-to-runner or hazard-style target for when the token reaches major thresholds.

The local model can start with `>=10x` proxy. True 50x/100x targets should wait for external labels.

## Proposed Entry Philosophy

Entry should require agreement between:

- Strong early on-chain runner shape.
- No major rug/security/liquidity red flags.
- Hot-market runtime context, supplied by the user's decision to start live trading.
- External attention confirmation when available.

Open question for the next session: decide whether social/narrative should be a hard requirement for entry, or a score boost layered on top of on-chain runner candidates. Given source availability uncertainty, a practical first design may make it a score boost until reliable feeds are validated.

## Proposed Exit Research

Do not hard-code the user's 100x intuition before testing. Backtest a grid:

- Sell first portion at 10x, 20x, 50x, or 100x.
- Sell no portion until trailing stop.
- Hold indefinitely unless catastrophic risk trigger fires.
- Partial exit sizes such as 10%, 25%, 50%.
- Trailing stop after major milestones.
- Time-based maximum hold variants.
- Liquidity/rug-risk emergency exit variants.

Evaluate with:

- Return distribution.
- Median and tail return.
- Missed moonshot rate.
- Drawdown/giveback.
- Realistic liquidity and slippage.
- Number of trades during hot-market windows only.

## Suggested Next Work Plan

Phase 0: Source viability probes, no trading.

- Test DEX Screener REST and WebSocket.
- Verify X API access/cost and define bounded rules.
- Verify GMGN API access and useful BSC fields.
- Verify FourMeme native/API, Bitquery, or Codex access.
- Verify CoinGecko/GeckoTerminal onchain endpoint access.

Phase 1: External label backfill.

- Build a moonshot label table with evidence URLs and timestamps.
- Include Binance Life / 币安人生 and other known BNB/FourMeme runners.
- Backfill true max multiples and threshold times.

Phase 2: Local runner proxy model.

- Train and validate a `>=10x` local runner proxy using lifecycle data.
- Use time-split validation to avoid future leakage.
- Measure precision, coverage, lift, and simulated 10% position outcomes.

Phase 3: External feature integration.

- Add DEX attention, social mention, smart-money, and lifecycle features.
- Ensure every feature is reconstructible at the historical decision time.

Phase 4: Long-hold exit replay.

- Run exit-grid backtests over runner candidates.
- Compare 10x/20x/50x/100x partial exits and trailing-stop variants.

Phase 5: Shadow live scoring.

- During hot market periods, run scoring without trading first.
- Record decisions, feature snapshots, and eventual outcomes.
- Only consider real trading after shadow evidence supports the strategy.

## Explicit Non-Goals

- Do not continue only optimizing the old few-minute strategy.
- Do not add a new market-hot runtime switch.
- Do not assume current `MOONSHOT_*` config is active.
- Do not use future social/DEX data in historical features.
- Do not train a fake 100x classifier from local data that contains zero 20x/50x/100x examples.
- Do not make Lookonchain or any unverified third-party feed a hard dependency before confirming stable access.

## Source Commands Already Used

The prior session used `smart-search` for web research. Continue using `smart-search-cli` for reproducible web research if more current source checking is needed.

Representative commands/sources already investigated:

- `smart-search doctor --format json`
- `smart-search deep "...BNB Chain/FourMeme memecoin runner model..." --format json`
- `smart-search search "币安人生 meme coin FourMeme 币安人生 涨幅 特征 BNB chain" --format json`
- `smart-search fetch "https://www.panewslab.com/zh/articles/c2f68f3d-95a4-4f1e-bb63-006fceadcc2d" --format json`
- `smart-search fetch "https://coinmarketcap.com/cmc-ai/bianrensheng/what-is" --format json`
- `smart-search fetch "https://docs.dexscreener.com/api/reference" --format json`
- `smart-search fetch "https://docs.dexscreener.com/api/websockets" --format json`
- `smart-search fetch "https://docs.x.com/x-api/fundamentals/rate-limits" --format json`
- `smart-search fetch "https://docs.coingecko.com/reference/trending-pools-network" --format json`

## Recommended Prompt For The Next Session

Use this prompt in a fresh session:

```text
Read docs/research/20260609-hot-market-moonshot-runner-handoff/summary.md first.

We are changing the research direction away from short-hold few-minute trading.
Do not implement immediately. First continue the design/research for a hot-market BNB/FourMeme moonshot runner model.

User constraints:
- I manually decide when the overall BNB/FourMeme market is hot and only then start live trading.
- Do not add a new internal market-hot switch.
- Keep the old 10% one-position sizing idea.
- I cannot provide real-time per-token social/narrative signals, so any such signal must be automatically monitored.
- I want the model to learn features of coins that run many multiples, like 币安人生 / Binance Life.
- Local data has no 20x/50x/100x examples, so do not pretend it can train a true 100x classifier by itself.
- First research external data sources and design the label/feature/model/backtest plan.

Before coding, follow AGENTS.md and use current Codex analysis plus external Claude for M+ work.
```
