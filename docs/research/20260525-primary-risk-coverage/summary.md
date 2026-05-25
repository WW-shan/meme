# Primary Risk Coverage Research

## Question

How should the primary v95/v84 candidate stream be filtered or resized so replay-integrated risk/coverage improves live-sized profitability without overfitting?

## Sources

- [Mlfinpy labeling docs](https://mlfinpy.readthedocs.io/en/latest/Labelling.html)
- [Hudson & Thames meta-labeling article](https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/)
- [QuantConnect meta-labeling caution discussion](https://www.quantconnect.com/forum/discussion/14706/why-meta-labeling-is-not-a-silver-bullet/)

## What the sources support

- Triple-barrier and meta-labeling are path-based, not just next-step direction labels.
- The meta stage should act as a take/skip or sizing gate on top of a primary signal.
- Execution-aware features such as liquidity, slippage, spread, and volatility belong at decision time.
- Time-series validation must be leakage-safe and out-of-sample; the same information should not be expected to produce a free second edge.
- Meta-labeling can help when the primary signal is useful but noisy, but it is not guaranteed to improve an end-to-end ML model built on the same inputs.

## Implication for this repo

The next useful test is not another broad rejected-signal tree. It is a replay-integrated risk/coverage gate on actual primary v95/v84 candidates, with strict validation versus the current accepted baseline and explicit trade-count coverage constraints.

## Experiment result

Report: `data/replay_reports/shadow_meta_gate_replay_20260525_primary_risk_coverage.json`

Decision: rejected; no live switch.

The replay tested `48` shadow meta-gate candidates on the primary v95/v84 candidate stream. No candidate passed the validation acceptance gate.

- Validation baseline: `32` trades, net profit `0.021094872145773796` BNB, win rate `75.00%`, max drawdown `-9.8821%`, walk-forward worst return `87.2942%`, stress-worst profit `0.011148541483943297` BNB.
- Best validation raw candidate: candidate `26`, `36` trades, net profit `0.021349845205486273` BNB, win rate `69.44%`, max drawdown `-10.0096%`, walk-forward worst return `82.6501%`, stress-worst profit `0.010687028347564107` BNB.
- Candidate `26` had a small validation profit lift but failed drawdown, win-rate, walk-forward return, and stress gates.
- Final baseline: `20` trades, net profit `0.005083918932887389` BNB, win rate `50.00%`, stress-worst profit `0.0017914397178126493` BNB.
- Final candidate `26`: `22` trades, net profit `0.004756235388967994` BNB, win rate `45.45%`, stress-worst profit `0.0014796104887205598` BNB.

The grid would have skipped the new `啸天犬` loss because its selected shape used `buy_shadow_meta_gate_max_age_seconds=60.0` and `buy_shadow_meta_gate_min_prob=0.989`, while the live entry was about `265.5s` old with `prob=0.9778794193133864`. That is not sufficient for promotion: across historical validation and final replay, the same gate did not improve risk/coverage robustly.

Next implication:

- Do not deploy this shadow risk/coverage gate.
- Do not repeat the same static primary-risk grid.
- Preserve the late-pump/peak-proximity evidence as a feature direction, but move the next experiment toward conditional exit/retention from actual live trade paths or a richer source-stable candidate label before any replay integration.

## Live attribution addendum

While the replay run was still in progress, a new live paper trade appeared on `啸天犬` / `0x0CE1f53cdb23A16F93Cb1bA6A8D501d3D89b4444`.

- Signal: `2026-05-25 16:40:33.496010`
- Open: `2026-05-25 16:40:35.821197`
- Close: `2026-05-25 16:44:46.164058`
- Entry price: `1.3364814945595361e-08`
- Exit price: `9.77893408188555e-09`
- Net profit: `-0.00010323569176232312`

Path summary:

- The token launched at `2026-05-25 16:36:08`.
- At signal time, lifecycle age was about `265.5s` and lifecycle price had just reached a local peak.
- Pre-signal 60s path was a vertical late move: price moved from about `-54.45%` vs signal price up to the signal peak.
- From entry to close, MFE was `+18.137%` and realized/MAE was `-26.831%`.
- The path never reached `+25%` after entry and first crossed `-25%` about `249.2s` after entry.

Interpretation:

- This is a path-risk case, not a freshness or collector failure case.
- It strengthens the hypothesis that the next useful model work is candidate-level risk/coverage around late vertical moves and peak-proximity, not a global threshold relaxation.
