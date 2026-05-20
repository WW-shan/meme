# Late-Pump Entry Veto / Path-State Meta Gate Research

Date: 2026-05-20

## Live Trigger

The current live model is `data/models/20260519_v95_v84_selective_nearmiss_gate`.
The latest live v95 trades show that the main failure is not simply entry speed. The
bot often enters high-confidence, high-PredReturn tokens after a sharp pump, then
execution slippage and fast collapse erase the expected edge.

Observed live shapes:

- `FENGSHUI 0x1779...`: `prob=0.9947`, `PredReturn=103.27`, entry slippage about
  `+66%`, then immediate `ENTRY_SLIPPAGE_PROTECTION`, net about `-0.0004026 BNB`.
- `FENGSHUI 0xE0C6...`: reached a large post-entry MFE but then crashed before the
  current exit policy captured enough of it.
- `TSG`, `BNBGUY`, `x402`, and other v95 entries had high model confidence but did
  not develop durable MFE after entry.
- The clean winner, `ZhaoChangE`, hit `+25%` quickly and had no early drawdown before
  the PPO exit.

This points to a path-state problem: the current entry gate sees high model score,
volume, and volatility, but it does not reliably distinguish a clean early runner
from an exhausted pump/collapse.

## Research Question

Can v95 keep its current primary candidate generator and 10% sizing, while adding a
learned take/pass or path-state layer that rejects likely false-positive late-pump
entries without deleting the rare runners?

## Fetched Evidence

- `04-fetch-mlfinpy-labelling.md` from
  <https://mlfinpy.readthedocs.io/en/latest/Labelling.html>
- `05-fetch-hudsonthames-meta-labeling.md` from
  <https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/>
- `08-fetch-selective-classification-distribution-shift.md` from
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC12470254/>
- `09-fetch-trading-selective-classification-pdf.md` from
  <https://arxiv.org/abs/2110.14914> / fetched PDF text
- `07-fetch-crypto-pump-thresholding.md` from
  <https://arxiv.org/html/2503.08692v1>

## Findings

1. Triple-barrier labels are a better fit than fixed-horizon labels for this failure
   mode because the outcome depends on whether the token hits profit or stop barriers
   first, not only where price is at a fixed timestamp.

2. Meta-labeling fits the current architecture: v95 can remain the primary model
   that proposes the long trade, while a secondary model learns whether to take or
   skip that proposed trade.

3. Selective classification supports the same operational idea: abstain from trades
   whose predicted risk is too high, and evaluate the coverage/risk tradeoff rather
   than forcing every positive signal into a position.

4. Selective classification under distribution shift is relevant because live meme
   tokens are not drawn from a stable distribution. The selector should be judged on
   rejected false positives, live-stress behavior, and walk-forward robustness, not
   only on validation accuracy.

5. Pump-and-dump detection research supports using contextual price/volume anomaly
   features. A simple high price or high volume threshold is too noisy; relative
   price extension, volume surge relative to recent context, and volatility/volume
   co-movement are more defensible as features.

## Already-Rejected Directions To Avoid

- Lowering the global buy threshold.
- Relaxing entry volume globally.
- A hard late-pump veto based only on static thresholds.
- A hard flow activation or dead-flow gate.
- A blanket quick-profit or profit-lock exit.
- A generic candidate ranker using only the current static features.

These have already failed validation/final/stress or were too sparse to affect sealed
final replay.

## Next Hypothesis

Because recent live losses are high-confidence entries that look strong at signal time
but fail path-state tests after entry, add a replay-only v95 candidate meta-label probe
that uses triple-barrier / time-to-barrier outcomes and path-state features to learn
`take` versus `skip`.

Expected improvement:

- Reject a subset of v95 false-positive late-pump entries.
- Preserve current 10% sizing and the v95 primary threshold.
- Improve final net profit and drawdown versus corrected v95, without relying on a
  large trade-count reduction or one outlier.

Falsification:

- Reject if validation, sealed final, walk-forward worst, or stress replay fails
  versus corrected v95.
- Reject if profit improvement comes only from deleting too many trades.
- Reject if the feature set uses future path data at decision time.
- Reject if it cannot be reproduced with manifest-aware v95 runtime parameters.

## SmartSearch Commands

```bash
mkdir -p docs/research/20260520-late-pump-entry-veto
smart-search deep "For a live meme-token trading model that is losing on high-probability, high PredReturn, high volume_30s, high price_volatility entries that appear to be late-pump or overheated fake runners, what researched methods can improve live profitability without increasing position size? Focus on candidate-level meta-labeling, triple-barrier/path labels, volatility/price-extension/slippage-risk features, abstention/selective classification, and robust time-series validation. The experiment must preserve a strong primary model and use a second-stage veto or conditional entry gate rather than global threshold lowering." --budget deep --format json --output docs/research/20260520-late-pump-entry-veto/plan.json
smart-search search "triple barrier method meta-labeling financial machine learning primary model filter false positives volatility breakout features slippage risk" --validation balanced --extra-sources 3 --format json --output docs/research/20260520-late-pump-entry-veto/01-triple-barrier-meta-labeling-search.json
smart-search search "selective classification abstention reject option machine learning trading signal confidence calibration false positives" --validation balanced --extra-sources 3 --format json --output docs/research/20260520-late-pump-entry-veto/02-selective-classification-search.json
smart-search search "cryptocurrency pump and dump detection features volume volatility price surge machine learning early warning" --validation balanced --extra-sources 3 --format json --output docs/research/20260520-late-pump-entry-veto/03-pump-dump-detection-search.json
smart-search fetch "https://mlfinpy.readthedocs.io/en/latest/Labelling.html" --format markdown --output docs/research/20260520-late-pump-entry-veto/04-fetch-mlfinpy-labelling.md
smart-search fetch "https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/" --format markdown --output docs/research/20260520-late-pump-entry-veto/05-fetch-hudsonthames-meta-labeling.md
smart-search fetch "https://arxiv.org/abs/2110.14914" --format markdown --output docs/research/20260520-late-pump-entry-veto/06-fetch-trading-selective-classification.md
smart-search fetch "https://arxiv.org/html/2503.08692v1" --format markdown --output docs/research/20260520-late-pump-entry-veto/07-fetch-crypto-pump-thresholding.md
smart-search fetch "https://pmc.ncbi.nlm.nih.gov/articles/PMC12470254/" --format markdown --output docs/research/20260520-late-pump-entry-veto/08-fetch-selective-classification-distribution-shift.md
smart-search fetch "https://arxiv.org/pdf/2110.14914" --format markdown --output docs/research/20260520-late-pump-entry-veto/09-fetch-trading-selective-classification-pdf.md
```

Artifacts:

- `plan.json`
- `00-deep-plan.json`
- `01-triple-barrier-meta-labeling-search.json`
- `02-selective-classification-search.json`
- `03-pump-dump-detection-search.json`
- `04-fetch-mlfinpy-labelling.md`
- `05-fetch-hudsonthames-meta-labeling.md`
- `06-fetch-trading-selective-classification.md`
- `07-fetch-crypto-pump-thresholding.md`
- `08-fetch-selective-classification-distribution-shift.md`
- `09-fetch-trading-selective-classification-pdf.md`

## Experiment Result

Implemented replay-only report:

- `docs/superpowers/plans/2026-05-20-path-state-meta-gate-replay.md`
- `data/replay_reports/path_state_meta_gate_replay_20260520_v95.json`

Decision: rejected.

The causal path-state meta gate used barrier-priority labels: `target_hit_before_stop`
wins positive, `stop_hit_before_target` wins negative, and risk-adjusted relevance is
only a fallback when neither barrier field is present. It also injects prior same-token
buy probability and entry-score deltas into the causal path-state features. Even with
those fixes, it did not produce a usable take/skip boundary. On validation, thresholds
`0.35` through `0.90` were no-ops: `26` entries, `0` rejects, and the same
`0.00683256` BNB profit as the v95 baseline. Thresholds `0.95`, `0.98`, and `0.99`
rejected every gated signal and produced `0` trades. Sealed final therefore selected
the raw no-op threshold and matched baseline exactly: `46` trades, `0.02556322` BNB
net profit, `78.2609%` win rate, `-8.1825%` max drawdown, and `119.7469%`
walk-forward worst return.

The implementation also fixed replay-tooling issues: path-state score maps are now
propagated into stress replay, use the same pinned eval sample snapshots as the replay
that consumes them, exclude terminal non-enterable samples, carry episode metadata for
required alignment validation, normalize JSON-roundtripped numeric score keys, keep
excluded-token filtering for preloaded eval samples, and are summarized rather than
serialized in direct replay reports. After the fix, candidate stress results no longer
show false zero-trade stress metrics when the runtime replay has gated entries.

Next implication: keep the live late-pump/slippage failure tag, but do not repeat this
broad learned path-state classifier. The next attempt should target more explicit
pump-extension / drawdown-from-peak / entry-slippage-risk features or a conditional
exit model that can harvest fast MFE without broadening entries.
