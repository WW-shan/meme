# Dead-Flow Toxicity Meta-Gate Research

## Question

For the live FourMeme bot, recent closed live trades were dominated by dead-flow
timeout losses after large peak-relative drawdowns. The research question was:
which decision-time order-flow toxicity, adverse-selection, order-imbalance, VPIN,
or meta-label abstention methods can support a replay-integrated entry veto
without using future data?

## SmartSearch Commands

```bash
smart-search doctor --format json > docs/research/20260526-dead-flow-toxicity-meta-gate/00-doctor.json
smart-search deep "For a live meme-token trading bot with repeated dead-flow timeout losses after large peak drawdowns, what decision-time order-flow toxicity, adverse-selection, VPIN/order-flow-imbalance, or meta-label abstention methods can build a replay-integrated entry veto without using future data?" --format json --output docs/research/20260526-dead-flow-toxicity-meta-gate/01-deep-plan.json
smart-search search "order flow toxicity VPIN adverse selection order imbalance entry filter trading meta-labeling abstention" --validation balanced --extra-sources 3 --format json --output docs/research/20260526-dead-flow-toxicity-meta-gate/02-search.json
smart-search zhipu-search "order flow toxicity VPIN adverse selection order imbalance entry filter trading meta-labeling abstention" --count 5 --format json --output docs/research/20260526-dead-flow-toxicity-meta-gate/03-zhipu.json
smart-search exa-search "order flow toxicity VPIN adverse selection order imbalance entry filter trading meta-labeling abstention" --num-results 5 --format json --output docs/research/20260526-dead-flow-toxicity-meta-gate/04-exa.json
smart-search fetch "https://questdb.com/glossary/order-flow-toxicity/" --format markdown --output docs/research/20260526-dead-flow-toxicity-meta-gate/05-fetch-questdb-order-flow-toxicity.md
smart-search fetch "http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html" --format markdown --output docs/research/20260526-dead-flow-toxicity-meta-gate/06-fetch-epchan-vpin.md
smart-search fetch "https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/" --format markdown --output docs/research/20260526-dead-flow-toxicity-meta-gate/07-fetch-hudson-meta-labeling.md
smart-search fetch "https://www.sciencedirect.com/science/article/abs/pii/S2173126812000344" --format markdown --output docs/research/20260526-dead-flow-toxicity-meta-gate/08-fetch-sciencedirect-vpin.md
smart-search fetch "https://pure.au.dk/ws/files/68359010/rp13_43.pdf" --format markdown --output docs/research/20260526-dead-flow-toxicity-meta-gate/09-fetch-vpin-critique.md
```

Provider state:

- `00-doctor.json` reported `ok=true` and `minimum_profile_ok=true`.
- `02-search.json` used xAI Responses plus Tavily successfully.
- `03-zhipu.json` and `04-exa.json` recorded missing provider keys, so their claims
  were not used as evidence.

## Fetched Sources

- `https://questdb.com/glossary/order-flow-toxicity/`
- `http://epchan.blogspot.com/2013/10/how-useful-is-order-flow-and-vpin.html`
- `https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/`
- `https://www.sciencedirect.com/science/article/abs/pii/S2173126812000344`
- `https://pure.au.dk/ws/files/68359010/rp13_43.pdf`

## What Applies To This Bot

- Order-flow toxicity is an adverse-selection concept: entries become dangerous
  when the visible buy/sell flow suggests that the bot is entering against better
  informed or better positioned traders.
- The live bot already has decision-time flow fields, so the useful local version
  is not a new magic VPIN indicator. It is a secondary abstention gate around the
  current v95 primary model using only decision-time flow/peak-state features.
- Meta-labeling is a good fit for this repo because the primary model is already
  strong enough to generate useful candidates, and the second stage can decide
  trade versus skip using path-based outcomes and no lookahead.
- Current local evidence from
  `data/replay_reports/flow_abstention_feature_scan_20260526_dead_flow_toxicity_meta_gate_round.json`
  supports the same direction: 60s `flow_buy_sell_overlap_ratio`,
  `flow_buy_sell_ratio`, `flow_sell_pressure`, and `flow_signed_imbalance` rules
  selected large `flat_timeout` buckets with zero protected runner selection in
  the live rejected-signal sample.

## What We Reject

- Do not deploy a standalone VPIN threshold. The fetched critique from Andersen
  and Bondarenko argues that VPIN can lose incremental explanatory power after
  controlling for volume/volatility and may be distorted by trade-classification
  errors.
- Do not use broad low/zero-PredReturn quick-profit overlays; the previous round
  already showed they explode trade count and fail stress/final gates.
- Do not treat the live rejected-signal feature scan as live-switch evidence.
  It is a direction selector only; it must be converted into strict replay and
  compared against the current v95 baseline.

## Next Experiment

The highest-value next experiment is a replay-integrated dead-flow abstention
gate that preserves the current v95 primary/near-threshold candidate generator
and only vetoes candidates with decision-time adverse-flow or peak-crash evidence.
The first no-code falsification is the existing 30s `flow_abstention` replay. If
that is rejected, the next structurally different direction is either:

- extend the flow-abstention replay path to support the locally promising 60s
  flow fields; or
- run the existing peak-drawdown `dead_bounce_veto` replay, which directly
  targets today's live bought losses that entered roughly 58%-77% below local
  lifecycle peaks.
