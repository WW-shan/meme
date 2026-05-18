# Candidate Runner/Collapse Gate Research

## Question

Can a candidate-level second-stage model improve live profitability by filtering v84-like buy candidates into likely runners versus quick collapses, without increasing the 10% live position risk?

## SmartSearch Commands

```bash
smart-search doctor --format json > docs/research/20260519-candidate-runner-collapse-gate/00-doctor.json
smart-search deep "candidate-level meta-labeling triple-barrier path labels for filtering trading signals runner collapse classifier" --budget deep --format json --output docs/research/20260519-candidate-runner-collapse-gate/plan.json
smart-search search "candidate-level meta-labeling triple-barrier path labels for filtering trading signals runner collapse classifier" --validation balanced --extra-sources 3 --timeout 90 --format json --output docs/research/20260519-candidate-runner-collapse-gate/01-search.json
smart-search exa-search "candidate-level meta-labeling triple-barrier path labels for filtering trading signals runner collapse classifier risks limitations comparison" --num-results 5 --format json --output docs/research/20260519-candidate-runner-collapse-gate/02-exa.json
smart-search fetch "https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/" --format markdown --output docs/research/20260519-candidate-runner-collapse-gate/03-fetch-hudsonthames.md
smart-search fetch "https://mlfinpy.readthedocs.io/en/latest/Labelling.html" --format markdown --output docs/research/20260519-candidate-runner-collapse-gate/04-fetch-mlfinpy-labelling.md
smart-search fetch "https://docs.quantreo.com/tutorials/tutorial-meta-labeling/" --format markdown --output docs/research/20260519-candidate-runner-collapse-gate/05-fetch-quantreo-meta-labeling.md
```

`00-doctor.json` was intentionally not committed because it records local provider configuration shape. The relevant blocker was that Exa was unavailable because `EXA_API_KEY` was not configured; broad SmartSearch discovery plus fetched pages were used instead. No native Codex web browsing was used.

## Fetched Sources

- Hudson & Thames, "Does Meta Labeling Add to Signal Efficacy?", fetched in `03-fetch-hudsonthames.md`.
- MLFinPy documentation, "Triple-Barrier and Meta-Labelling", fetched in `04-fetch-mlfinpy-labelling.md`.
- Quantreo documentation, "Meta-Labelling Explained: Filter Noise, Boost Precision, Win More", fetched in `05-fetch-quantreo-meta-labeling.md`.

## What Applies To This Bot

- The live evidence is not "hold everything longer." WAGMI and most high-PredReturn rejects after it were quick-collapse paths; xPBNB was the clean missed-runner case.
- The strongest existing stack should remain the primary candidate generator. Meta-labeling is a secondary take/pass layer over a primary model, not a replacement for the primary direction model.
- Triple-barrier/path labels match the local failure mode better than fixed-horizon labels because they encode which event happens first: runner target, stop, or vertical time limit.
- The secondary model should optimize precision on primary positives and accept fewer trades if needed. It must not be used to increase bet size; live size remains 10%.
- Candidate features should include the primary buy probability, entry-value score, lifecycle path/volume/unique-buyer context, and execution-aware fields already available around the signal.

## What We Reject

- Do not lower the global buy threshold again just to catch xPBNB-style outliers. The 2026-05-19 near-threshold sweep improved sealed final replay but had unacceptable validation risk.
- Do not repeat v94-style broad profit-path partial-exit training. It created too many weak trades, poor win rate, high drawdown, and negative stress replay.
- Do not train a raw binary runner-probability gate over all samples as in v91. It alternated between overtrading and no trading.
- Do not use meta-model probability for larger position sizing. That conflicts with the 10% risk rule.

## Next Experiment

After explicit design approval, test `v95` as a narrow candidate-level runner/collapse gate:

- Generate candidate events from the accepted v84-like primary stack rather than all tokens.
- Label candidates with live-like path barriers, for example runner if `+60%` is reached before `-18%` within the selected horizon, collapse if the stop arrives first, and neutral/timeout as pass unless replay shows a safer treatment.
- Train an optional `entry_filter_model` on candidate events only, with time-based validation and no final leakage.
- In replay, require the primary v84-like gate plus the secondary runner/collapse gate.
- Accept only if it beats the current best accepted baseline on validation, sealed final, walk-forward, and stress replay while preserving 10% sizing and enough trade count.
