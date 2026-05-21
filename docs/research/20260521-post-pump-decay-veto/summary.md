# Post-Pump Decay Veto Research

## Live Trigger

- Current live model: `data/models/20260519_v95_v84_selective_nearmiss_gate`.
- Live risk constraint: 10% position sizing, no fixed stake expansion.
- Trigger trades:
  - `🆙` opened with `prob=0.9816`, `PredReturn=44.33`, favorable entry slippage, then closed by `TIME_EXIT` for about `-0.00002809` BNB. Reconstructed path showed about `-63.35%` drawdown from pre-signal peak and no post-entry recovery.
  - `披风` opened at `2026-05-21 16:52:58` with `prob=0.9705`, `PredReturn=38.76`, favorable entry slippage `-5.56%`, fast lifecycle status, then closed by `TIME_EXIT` for `-0.00002846` BNB. Reconstructed path peaked at `1.7081887772682805e-08`, while signal price was `6.209510991969182e-09`, a `-63.65%` drawdown from peak. Post-signal prices stayed below the signal/entry zone.
- Failure label: `model_bought_but_should_skip`, `post_pump_decay`, `peak_to_signal_drawdown`, `sell_dominant_or_no_clean_reactivation`.

## Research Commands

```bash
smart-search doctor --format json
smart-search deep "How can a trading model detect and avoid post-pump decay entries after a sharp memecoin pump using only causal pre-entry price path and order-flow features such as peak-to-signal drawdown, sell pressure, order-flow toxicity, VPIN, and purged time-series validation?" --format json --output docs/research/20260521-post-pump-decay-veto/00-deep-plan.json
smart-search search "post-pump decay trading model order flow toxicity VPIN peak drawdown meta-labeling purged cross validation" --validation balanced --extra-sources 3 --timeout 120 --format json --output docs/research/20260521-post-pump-decay-veto/01-search.json
smart-search fetch "https://www.quantresearch.org/From%20PIN%20to%20VPIN.pdf" --format markdown --output docs/research/20260521-post-pump-decay-veto/02-vpin-fetch.md
smart-search fetch "https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/" --format markdown --output docs/research/20260521-post-pump-decay-veto/03-meta-labeling-fetch.md
smart-search fetch "https://www.quantresearch.org/Innovations.htm" --format markdown --output docs/research/20260521-post-pump-decay-veto/04-purged-cv-fetch.md
smart-search fetch "https://alphaarchitect.com/a-new-wolf-in-town-pump-and-dump-manipulation-in-cryptocurrency-markets/" --format markdown --output docs/research/20260521-post-pump-decay-veto/05-crypto-pump-fetch.md
```

## Evidence

- Abad and Yague's VPIN introduction describes order flow toxicity as adverse selection risk in high-frequency trading and frames VPIN around buy/sell order imbalance, trade intensity, and volume-time sampling. For this repo, the deployable analogue is not a full VPIN implementation first; it is a causal imbalance/toxicity proxy at signal time: sell pressure, signed imbalance, peak-to-signal drawdown, and whether new buy flow reactivates after the peak.
- Hudson & Thames' meta-labeling article supports preserving the primary model and adding a secondary take/skip layer. It also stresses event-based sampling, triple-barrier labels, and contextual features. This matches the repo constraint: do not lower the global threshold; use v95 as the primary candidate generator and test a narrow candidate-level veto.
- Lopez de Prado's innovations page explicitly lists triple-barrier labeling, meta-labeling, K-fold CV with purging and embargo, CPCV, PBO, and VPIN/order-imbalance bars as distinct tools. For this repo, acceptance must stay on validation, sealed final, walk-forward, and stress replay, not just live anecdotes or one split.
- The Alpha Architect cryptocurrency pump-and-dump summary reports temporary short-term crypto price distortions and very large volumes. That aligns with the live `🆙` and `披风` shape: the dangerous buy is not "high score" by itself, but a high-score entry after the temporary pump has already faded sharply.

## Hypothesis

Because recent live losses show high model confidence after a sharp pre-signal pump already decayed roughly 63%, a narrower post-pump decay veto should reject only candidates with causal peak-to-signal drawdown plus weak/reactive buy flow, instead of reducing the global threshold or applying a broad path-state meta gate.

## How This Differs From Rejected Directions

- Not global threshold lowering: v95's primary threshold and near-rescue rules remain the candidate generator.
- Not broad path-state meta gate: previous score gate had no usable middle band and either did nothing or rejected everything.
- Not the old static dead-bounce veto alone: that used current sample `max_price`/creator/buy-pressure fields and had `reject_count=0` on validation.
- Not blanket longer hold or fixed profit lock: both have already cut durable winners in prior replays.

## Minimal Experiment

1. Re-run the existing strict late-pump exhaustion replay on current data to see whether new live data gives any validation/final activity.
2. If activity is still zero or gates fail, build a narrower replay-only post-pump decay probe using causal pre-entry path metrics and signal-time flow proxies.
3. Reject unless it beats the current best baseline on net profit, drawdown, win rate, walk-forward, stress replay, and trade-count discipline at 10% sizing.

## Deployment Rule

This research alone is not live-switch evidence. Any accepted candidate must pass strict replay gates versus the current best baseline, then only switch with zero open positions and `./tools/memectl bot restart`.
