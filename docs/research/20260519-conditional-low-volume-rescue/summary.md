# Conditional Low-Volume Rescue Research

## Question

Live v95 has no new OPEN/CLOSE after WAGMI, but the latest rejected-signal probes show a recurring pocket of high primary buy probability candidates blocked by `entry_volume_30s_below_min`, `near_threshold_pred_return_below_min`, or `near_threshold_price_volatility_below_min`.

The local live trigger for this round is:

- `HERMANO`, `1Binance`, `A9自由`, `微信时刻`, and `Cheburashka` were rejected low-volume candidates that hit `+25%` before `-18%`.
- `MATRIX-3`, `PI-402 协议`, `币安社区`, `尼罗基金会`, `4lpha`, and `Agora-1` were similar low-volume/high-probability candidates that hit the stop barrier first.
- A separate `BFC` candidate reached `+25%` quickly but was blocked by low `PredReturn` / later low `price_volatility`; this warns that the current entry-value filter can miss runner paths, but prior broad threshold relaxation already failed.

The research question is how to test a conditional rescue and exit policy without increasing position size or repeating global threshold/volume relaxation.

## SmartSearch Commands

```bash
mkdir -p docs/research/20260519-conditional-low-volume-rescue
smart-search deep "For extremely early memecoin trading signals with high primary buy probability but low 30-second volume or low short-window volatility, what robust offline methods can distinguish true breakouts from fakeouts and design conditional quick-take-profit versus hold-runner exits without increasing position size? Focus on meta-labeling, triple-barrier labels, survival/competing-risk timing, and time-series validation." --budget deep --format json --output docs/research/20260519-conditional-low-volume-rescue/plan.json
smart-search search "meta-labeling triple barrier method financial machine learning breakout fakeout trading volume confirmation time series cross validation" --validation balanced --extra-sources 3 --timeout 90 --format json --output docs/research/20260519-conditional-low-volume-rescue/01-search-meta-triple.json
smart-search exa-search "triple barrier method meta labeling financial machine learning time series cross validation" --num-results 5 --include-highlights --format json --output docs/research/20260519-conditional-low-volume-rescue/02-exa-triple-meta.json
smart-search exa-search "breakout fakeout volume confirmation low volume false breakout trading" --num-results 5 --include-highlights --format json --output docs/research/20260519-conditional-low-volume-rescue/03-exa-breakout-fakeout.json
smart-search fetch "https://mlfinpy.readthedocs.io/en/latest/Labelling.html" --format markdown --output docs/research/20260519-conditional-low-volume-rescue/04-fetch-mlfinpy-labeling.md
smart-search fetch "https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/" --format markdown --output docs/research/20260519-conditional-low-volume-rescue/05-fetch-hudson-meta-labeling.md
smart-search fetch "https://bookmap.com/blog/breakout-or-fakeout-the-3-point-checklist-for-confirmation" --format markdown --output docs/research/20260519-conditional-low-volume-rescue/06-fetch-bookmap-breakout-fakeout.md
smart-search search "purged walk forward cross validation financial machine learning time series avoid leakage triple barrier meta labeling" --validation balanced --extra-sources 3 --timeout 90 --format json --output docs/research/20260519-conditional-low-volume-rescue/07-search-purged-cv.json
smart-search fetch "https://blog.quantinsti.com/cross-validation-embargo-purging-combinatorial/" --format markdown --output docs/research/20260519-conditional-low-volume-rescue/08-fetch-quantinsti-purging.md
smart-search fetch "https://www.sefidian.com/2021/06/26/labeling-financial-data-for-machine-learning/" --format markdown --output docs/research/20260519-conditional-low-volume-rescue/09-fetch-sefidian-labeling.md
```

Provider note: the two Exa commands failed because Exa was unavailable in this environment; those files are blocker evidence, not method evidence.

## Fetched Sources

- `https://mlfinpy.readthedocs.io/en/latest/Labelling.html`
- `https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/`
- `https://bookmap.com/blog/breakout-or-fakeout-the-3-point-checklist-for-confirmation`
- `https://blog.quantinsti.com/cross-validation-embargo-purging-combinatorial/`
- `https://www.sefidian.com/2021/06/26/labeling-financial-data-for-machine-learning/`

## What Applies To This Bot

- Triple-barrier labels fit the live problem better than fixed-horizon return labels because live losses and wins are path dependent: a token that hits `+25%` then `-18%` needs a different policy from a token that hits `-18%` first.
- Meta-labeling fits the current architecture: keep v95/v84 as the primary generator, then test a secondary "take/skip or quick-take-profit/hold" decision only on candidates the primary model already marks as high probability.
- The fetched breakout/fakeout evidence supports using volume, aggressive follow-through, and post-break continuation as confirmation features, but the live data shows simple low-volume relaxation is not enough because the latest low-volume pocket contains both clean runners and fakeouts.
- Purging/embargoing matters because each label uses future path time. Any learned version of this idea must evaluate chronologically and avoid mixing overlapping label windows into validation.

## What We Reject

- Do not lower the global buy threshold. The prior v84 near-threshold sweep improved final headline return but failed validation risk.
- Do not lower `MIN_ENTRY_VOLUME_30S` globally. The latest low-volume probe is mixed: `5` low-volume runners, `3` fast-profit-then-stop, `7` fakeouts, `3` flat, and `3` missing path.
- Do not use raw runner probability alone. v91 and v93 already showed overtrading, weak stress robustness, or worse validation.
- Do not turn on blanket partial exits or simply hold longer. Prior partial-exit and profit-path probes were not robust enough.

## Next Experiment

Run a replay-integrated conditional low-volume rescue experiment on top of the accepted v95 stack:

- keep 10% position sizing and the current v95 primary/near-threshold gate;
- only rescue candidates that fail the normal volume/volatility quality gate but meet a narrow high-probability, bounded-volume, volatility, and age window;
- mark those positions separately in replay metrics and trade logs;
- add an optional full quick-take-profit exit only for rescued positions;
- reject the direction unless validation/final/walk-forward/stress beat or clearly improve a real risk dimension versus the current best v95 baseline.

The first implementation should be replay-only. Do not wire this into live `.env` or runtime bot behavior unless the replay gate beats the current best baseline and passes the live switch procedure.
