# 2026-05-19 Selective Abstention For Near-Miss Runners

## Live Trigger

The 2026-05-19 live pass found no new OPEN/CLOSE after WAGMI, so this round used high-score rejects as the live evidence.

- `BNBROCK_0104` (`0xF96c39016A4126a4a06EEC8a7cAe83180b354444`): max `PredReturn=36.79`, `prob=0.9582`, `volume_30s=2.42`; post-signal path reached only `+3.93%` MFE, hit `-18%` after about `26s`, and hit `-25%` after about `76s`. This was a correct skip.
- `BNBROCK_0214` (`0xeA3A13b49fA79F25a06532CF344e0831c7D44444`): max `PredReturn=38.30`, `prob=0.9475`, `volume_30s=1.01`; path reached only `+4.84%` MFE and stayed around `-5%` by the latest observed event. This was also a correct skip so far.
- `ERNIE_0212` (`0x56908D3D9bBe3E993043FC8bfec48976473c4444`): max `PredReturn=35.14`, `prob=0.9490`, `volume_30s=1.27`; path hit `+25%` about `39s` after the signal and reached about `+53%` MFE. This was a missed runner.

Live conclusion: the issue is not a broad threshold problem. The model must selectively rescue rare near-threshold runners like ERNIE while continuing to reject similar-looking fake runners like BNBROCK.

## Commands

```bash
smart-search doctor --format json
smart-search deep "For live microcap meme-token trading, how can a model selectively accept rare near-threshold missed runners when the primary model score is high but expected-return gate is below threshold, while abstaining from similar fake runners, using selective classification, conformal prediction, meta-labeling, or uncertainty-aware rejection?" --budget deep --format json --output docs/research/20260519-selective-abstention-nearmiss/plan.json
smart-search search "selective classification abstention conformal prediction meta-labeling trading signal filter near-threshold false positives" --validation balanced --extra-sources 3 --timeout 90 --format json --output docs/research/20260519-selective-abstention-nearmiss/01-search-selective.json
smart-search search "meta-labeling triple barrier method trading primary model filter false positives abstain" --validation balanced --extra-sources 3 --timeout 90 --format json --output docs/research/20260519-selective-abstention-nearmiss/02-search-metalabel.json
smart-search search "conformal prediction trading strategy uncertainty reject option classification finance" --validation balanced --extra-sources 3 --timeout 90 --format json --output docs/research/20260519-selective-abstention-nearmiss/03-search-conformal-finance.json
smart-search fetch "https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/" --format markdown --output docs/research/20260519-selective-abstention-nearmiss/04-fetch-hudson-metalabeling.md
smart-search fetch "https://mlfinpy.readthedocs.io/en/latest/Labelling.html" --format markdown --output docs/research/20260519-selective-abstention-nearmiss/05-fetch-mlfinpy-labelling.md
smart-search fetch "https://arxiv.org/html/2107.07511v6" --format markdown --output docs/research/20260519-selective-abstention-nearmiss/06-fetch-conformal-intro.md
smart-search fetch "https://arxiv.org/html/2512.12844v2" --format markdown --output docs/research/20260519-selective-abstention-nearmiss/07-fetch-selective-conformal-risk-control.md
smart-search fetch "https://www.diva-portal.org/smash/get/diva2:1259677/FULLTEXT01.pdf" --format markdown --output docs/research/20260519-selective-abstention-nearmiss/08-fetch-conformal-reject-option.md
```

## Evidence

- Hudson & Thames: meta-labeling uses a primary model for side/signal generation and a secondary model to decide whether to trade. It emphasizes that meta-labeling is useful when the primary model has recall but needs false-positive filtering.
- MLFinPy labeling docs: triple-barrier labels fix fixed-horizon label weaknesses by using path-dependent upper/lower/time barriers; meta-labeling turns the label into a binary take/pass decision when the side is supplied by the primary model.
- Angelopoulos & Bates conformal introduction: conformal prediction can wrap a pre-trained model with calibration data to produce uncertainty sets with finite-sample marginal coverage; the usefulness depends on the score function, and distribution shift/time-series settings require care.
- Selective Conformal Risk Control: selective classification adds a reject option and trades coverage for lower conditional risk; a two-stage procedure first selects confident samples, then calibrates risk on the accepted subset.
- Linusson et al. conformal reject option: conformal confidence can be interpreted as an expected error budget over accepted predictions; a user-chosen error budget `k` rejects predictions beyond that budget. The paper also warns that imbalance may require label-conditional/Mondrian conformal handling.

## Application To This Repo

The next experiment should not lower the global buy threshold or relax volume globally. Prior v84/v91/v93/v94 evidence already rejected those shapes.

The structurally different idea is a **selective near-miss gate**:

- Primary candidate stays conservative: current v84/v67-style high-score primary model remains the source of candidate events.
- The rescue region is narrow: high primary probability, expected-return gate just below threshold, and live-like volume/volatility constraints.
- The secondary label is path based: accept only if the candidate hits a useful profit barrier before a stop/collapse barrier under live execution assumptions.
- The selector is evaluated as a coverage/risk tradeoff: the gate must rescue enough clean missed runners without admitting BNBROCK-like collapses.
- Calibration must be chronological and compared to the current best baseline, not the latest artifact.

## Hypothesis

Because live ERNIE was a rare near-threshold missed runner while the two BNBROCK near-misses were correct skips, a selective abstention/meta-label gate trained only on near-threshold primary candidates may improve live profitability by rescuing a small number of clean runners without repeating the global threshold/volume relaxation failures.

## Falsification

Reject the direction if a validation/final probe:

- materially increases trade count or drawdown,
- fails walk-forward/stress robustness versus the current best v84 baseline,
- mostly earns from one or two outliers,
- admits BNBROCK-like early stop paths at a rate similar to the rejected global threshold sweeps,
- or cannot be implemented without future path leakage.

## Probe Result

The first no-code replay probe accepted the narrow gate as an implementation candidate and rejected broad relaxation as the implementation path.

- Validation report: `data/replay_reports/v95_selective_nearmiss_gate_validation_20260519.json`
- Final report: `data/replay_reports/v95_selective_nearmiss_gate_final_20260519.json`
- Candidate runtime artifact: `data/models/20260519_v95_v84_selective_nearmiss_gate`

Selected rule:

- keep v84 primary threshold at `0.98`
- rescue only `0.94 <= prob < 0.98`
- require `entry_score >= 32`
- require `volume_30s >= 1.25`
- require `price_volatility >= 0.08`
- require age inside the existing v84 max-age bound

Results versus v84 baseline:

- Validation: profit improved by `0.0005639744852279386` BNB with no trade-count increase.
- Final: return improved from `476.4288%` to `511.4778%`, profit from `0.02856940` to `0.03067113` BNB, and trades from `43` to `44`.
- Drawdown stayed bounded: max DD moved from `-7.8221%` to `-8.0587%`.
- Walk-forward worst return improved from `82.8426%` to `111.8292%`.

Risk note: this is a narrow, underpowered probe. The validation grid did not strongly discriminate (`144/144` rules passed), the top validation rule had only `2` near episodes and no trade-count increase, and the sealed final uplift came from one extra trade. The artifact is suitable for canary deployment with strict live attribution, not proof that the edge is durable.

Implementation constraint: the gate is manifest-scoped. Old models do not enable it by default; v95 carries the near-threshold parameters in `selected_runtime_params`, so live config can auto-align from the model artifact. Manual `BUY_NEAR_*` overrides must fail closed when invalid.
