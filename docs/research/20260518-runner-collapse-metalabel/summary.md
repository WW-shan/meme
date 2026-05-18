# Runner Collapse Meta-Labeling Research

Date: 2026-05-18

## Question

How should the live model separate early fake runners / quick collapses from recoverable runners without increasing position size, using order-flow, holder concentration, path labels, and live execution costs?

## SmartSearch Evidence

Deep research was run through SmartSearch, not native browsing:

- `smart-search deep "For live microcap meme-token trading, how should we design candidate-level meta-labeling or conditional exit models to separate early fake runners / quick collapses from recoverable runners, using order-flow, holder concentration, path labels, and live execution costs?" --budget deep --format json --output docs/research/20260518-runner-collapse-metalabel/plan.json`
- `smart-search search "microcap crypto meme coin early pump dump collapse detection order flow holder concentration features" --validation balanced --extra-sources 3 --timeout 90 --format json --output docs/research/20260518-runner-collapse-metalabel/01-meme-collapse-search.json`
- `smart-search search "financial machine learning meta labeling triple barrier method conditional exit model order flow toxicity" --validation balanced --extra-sources 3 --timeout 90 --format json --output docs/research/20260518-runner-collapse-metalabel/02-metalabel-exit-search.json`
- `smart-search fetch "https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/" --format markdown --output docs/research/20260518-runner-collapse-metalabel/03-fetch-hudson-meta-labeling.md`
- `smart-search fetch "https://mlfinpy.readthedocs.io/en/latest/Labelling.html" --format markdown --output docs/research/20260518-runner-collapse-metalabel/04-fetch-mlfinpy-labeling.md`
- `smart-search fetch "https://arxiv.org/html/2602.13480v1" --format markdown --output docs/research/20260518-runner-collapse-metalabel/05-fetch-memetrans.md`
- `smart-search fetch "https://arxiv.org/html/2507.01963v2" --format markdown --output docs/research/20260518-runner-collapse-metalabel/06-fetch-midsummer-meme.md`

Fetched sources used for decisions:

- Hudson & Thames, "Does Meta Labeling Add to Signal Efficacy?": meta-labeling is useful as a second-stage filter when the primary model is already reasonable, and it should use contextual features around the candidate signal.
- mlfinpy labeling docs: triple-barrier labels use profit-taking, stop-loss, and time barriers; meta-labeling learns whether to act on a primary signal rather than generating the initial opportunity.
- MemeTrans paper: high-risk memecoin detection benefits from launch/trading activity, holder concentration, time-series dynamics, and bundle/account-control signals; tabular features can materially reduce losses.
- "A Midsummer Meme's Dream": manipulation in meme coins often appears as artificial growth, wash trading, concentrated ownership, and price inflation before later profit extraction.

## Live Evidence

Latest live losses show two different failure modes:

- `币安小子` `0xC183...FFfF`: stop-loss fired after a real drawdown, but the token later recovered and reached a much larger path high. This is a recoverable-runner / stop-before-recovery case.
- `币安小子` `0xef34...4444`: fast collapse after entry with weak activity depth and no meaningful post-entry upside. This is an early fake-runner / quick-collapse case.

The same global threshold cannot cleanly solve both. Raising the threshold can miss recoverable runners, while lowering it admits quick collapses.

## Decision

Do not replace the v67/v84-style primary buy model with a direct runner-probability model. The v91 probe already showed that direct binary runner gating produced too many trades, large drawdown, and broken walk-forward robustness.

Next experiments should preserve the current strong primary model and add one of these layers:

1. Candidate-level take/skip meta-label:
   - Train only on primary-model candidate signals.
   - Label with path barriers after live costs, for example target hit before stop within the configured hold window.
   - Use existing order-flow and concentration features: unique buyers, buy/sell overlap, repeat-buyer ratio, buyer churn, sell reentry, holder concentration, top-holder share, volume, volatility, and acceleration.

2. Conditional exit/recovery model:
   - Trigger only when stop-loss or sharp drawdown is near.
   - Hold through the stop only when activity, buyer diversity, and concentration signals still look like a recoverable runner.
   - Keep the default hard stop for toxic-flow collapses.

Risk constraints remain unchanged:

- Position fraction stays at 10%.
- A candidate must beat the accepted baseline on strict replay, walk-forward worst segment, and harsh execution stress before live switch.
- Research-backed changes must save SmartSearch plan, search, fetch, and decision files under `docs/research/`.

