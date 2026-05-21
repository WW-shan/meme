# 2026-05-21 Dead-Bounce Entry Veto Research

## Live Trigger

Latest live loss: `domybest` (`0xFb5EF82C8f06e96D644424a5Eb30c14b19A04444`) on 2026-05-21.

- Decision: `prob=0.9849279896585473`, `PredReturn=56.745787518509246`, queued by the v95 primary gate.
- Execution: lifecycle fast status was fresh, but entry slippage was `+11.5435%` and `signal_to_open_seconds=2.38906`.
- Path: before the signal, price had already fallen about `-70.81%` from the local peak. In the 5 seconds before the signal there were 6 sells and only 2 buys. After the entry fill, max favorable excursion stayed negative (`post_entry_max_vs_entry_pct=-1.98%`), so the live issue was not "held too short".
- Close: `PPO_SELL100`, `hold_duration=89.432451`, `net_profit=-0.00005994674454524784` BNB.

Failure tag: `primary_high_prob_dead_bounce_entry`.

## Prior Experiment Memory

Do not repeat these failed directions:

- Global threshold lowering or broad near-threshold rescue.
- Static volume relaxation.
- Broad late-pump veto that only looks for low-to-peak-to-current extension.
- Blanket delayed/full-position profit locks.
- Generic path-state meta gate without a usable middle band.

The new angle is different: it targets a peak-to-crash-to-small-bounce pattern where the entry candidate is already far below its own recent peak and insider/creator or early-holder sell pressure has already appeared before the model flips positive.

## SmartSearch Commands

```bash
smart-search doctor --format json
smart-search deep "How can short-horizon crypto/meme-coin trading models avoid buying dead-cat bounces after pump-and-dump crashes using causal order-flow/path features, meta-labeling, or triple-barrier labels?" --format json
smart-search search "dead cat bounce pump and dump crypto short horizon order flow imbalance meta labeling triple barrier entry filter" --validation balanced --extra-sources 3 --timeout 90 --format json --output docs/research/20260521-dead-bounce-entry-veto/01-search.json
smart-search fetch "https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/" --format markdown --output docs/research/20260521-dead-bounce-entry-veto/02-fetch-hudsonthames.md
smart-search fetch "https://mlfinpy.readthedocs.io/en/latest/Labelling.html" --format markdown --output docs/research/20260521-dead-bounce-entry-veto/03-fetch-mlfinpy-labeling.md
smart-search fetch "https://arxiv.org/html/2412.18848v1" --format markdown --output docs/research/20260521-dead-bounce-entry-veto/04-fetch-pump-dump-ml.md
smart-search fetch "https://dm13450.github.io/2022/02/02/Order-Flow-Imbalance.html" --format markdown --output docs/research/20260521-dead-bounce-entry-veto/05-fetch-ofi.md
smart-search fetch "https://www.altrady.com/crypto-trading/technical-analysis/dead-cat-bounce-pattern" --format markdown --output docs/research/20260521-dead-bounce-entry-veto/06-fetch-dead-cat.md
smart-search search "on-chain pump and dump rug pull detection features early buyer creator sell pressure token launch machine learning" --validation balanced --extra-sources 3 --timeout 90 --format json --output docs/research/20260521-dead-bounce-entry-veto/07-search-onchain-rug-features.json
smart-search fetch "https://arxiv.org/html/2509.01168v1" --format markdown --output docs/research/20260521-dead-bounce-entry-veto/09-fetch-dex-rug-detection.md
smart-search fetch "https://www.chainalysis.com/blog/crypto-crime-2024-pump-and-dump/" --format markdown --output docs/research/20260521-dead-bounce-entry-veto/10-fetch-chainalysis-pumpdump.md
```

`08-fetch-do-not-rug.md` was attempted from the MDPI source and failed through the configured fetch provider, so it is not used for claim-level conclusions.

## Evidence

- `mlfinpy` describes triple-barrier labeling as upper/lower/time barriers and meta-labeling as a secondary model that decides whether to take or pass on a primary model's bet. This matches the repo's need to keep v95 as the primary generator and add a narrowly falsifiable skip layer.
- Hudson & Thames' meta-labeling writeup emphasizes using contextual, relevant features on top of a primary signal and evaluating out-of-sample performance, not replacing the primary model blindly.
- The order-flow source frames imbalance as changes in supply and demand, but also warns that costs and fill assumptions can destroy high-frequency edge. That matches the live pattern where the whole post-signal bounce was smaller than realized entry slippage.
- The dead-cat-bounce source describes temporary recovery during a downtrend and flags volume surging without price progress as sell-pressure evidence. For this repo, the causal proxy is on-chain event flow: recent sells, creator/early-holder sell volume, peak-to-current drawdown, and failure to reclaim enough of the prior peak.
- The DEX rug-pull paper supports early-window fraud/rug detection using transaction, price, liquidity, and time features; it reports tree boosting as effective for early detection and identifies transaction volume and number of purchases as important features.
- Chainalysis uses on-chain data to surface pump-and-dump-like patterns and specifically looks at launches where a large holder or related actor later dumps/removes liquidity. For FourMeme, creator and early-holder sell behavior are available in `feature_extractor.py`.

## Hypothesis

Because live `domybest` was a high-confidence v95 buy after a sharp peak-to-crash and heavy immediate sell pressure, add a replay-only dead-bounce veto candidate that rejects only v95 primary entries with:

- very young age,
- large drawdown from pre-entry peak to current price,
- creator or early-holder sell pressure already visible,
- and high volatility/volume consistent with a post-pump unwind.

Expected improvement: reduce high-slippage dead-bounce losses without lowering position size, broadening entries, or clipping durable runners.

## Falsification Rule

Reject the direction if validation or sealed final shows any of:

- net profit below current v95 baseline,
- walk-forward/stress worse than v95,
- trade-count reduction greater than the accepted gate,
- veto mostly removes winners or does not remove any losing dead-bounce-like entries,
- or the rule is only supported by the single `domybest` live example.
