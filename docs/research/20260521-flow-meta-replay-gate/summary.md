# Flow Meta Replay Gate Research Summary

## Live Evidence

The bot and collector stayed under `memectl`/tmux during this cycle, with live `.env` still on `data/models/20260519_v95_v84_selective_nearmiss_gate`, empty `FIXED_STAKE_BNB`, and 10% position sizing. No live config or bot restart was performed for this experiment.

Recent rejected-signal path attribution after `2026-05-21 14:52:41` produced `71` per-token candidates: `4` fast-profit, `8` fast-profit-then-collapse, `2` slow-runner, `11` stop-first, and `46` flat-timeout. `XYZ` was the cleanest missed runner, but `CTW` and `TEST` were high-score stop-first counterexamples, and `Fren` was a runner with noisy seller overlap. This kept the problem scoped to candidate-level separation, not global threshold lowering.

During the replay run, live v95 bought `🆙` (`0x6B51cf1a9BCe1C89fB6A5602736Bad981C554444`) at `prob=0.981609` and `PredReturn=44.3272`, with favorable entry slippage of `-5.5528%`, then closed by `TIME_EXIT` for `-0.00002809` BNB. The path was a post-pump decay: pre-signal peak was `+172.834%` above signal, peak-to-signal drawdown was `-63.348%`, pre-signal 10s flow was `0` BNB buy vs `4.516888` BNB sell, and post-signal MFE was only `-7.423%`. This supports a more specific sell-dominant post-pump veto as the next direction.

## Prior Experiments To Avoid

`docs/model_scoreboard.md` already rejects global threshold lowering, broad quick-profit overlays, blanket delayed profit-lock exits, token balancing alone, broad profit-path/partial-exit training, static dead-bounce vetoes, and simple low-toxicity rescue rules. The 2026-05-20 path-state meta gate failed by having no usable middle band: low thresholds were no-ops and high thresholds became no-trade. This experiment is structurally different only in adding causal order-flow/toxicity fields to the path-state rows.

## Research Evidence

Saved SmartSearch evidence in this directory supports the experiment shape:

- `03-fetch-meta-labeling-toy.md` and `04-fetch-meta-labeling-signal-efficacy.md`: meta-labeling should sit on top of a primary model and learn take/pass, not invent a new side.
- `05-fetch-mlfinpy-labelling.md`: path-dependent triple-barrier/meta-labels fit this market better than fixed-horizon returns.
- `07-fetch-vpin.md` and `08-fetch-order-flow-toxicity.md`: order-flow toxicity and imbalance are relevant short-horizon microstructure signals.
- `10-fetch-purged-cv.md` and `11-fetch-skfolio-cpcv.md`: validation must avoid leakage and selection bias; this repo enforces that through train/validation/final splits, walk-forward, stress replay, and causal feature use.

## Hypothesis

Because live evidence shows rare clean missed runners mixed with high-score stop-first collapses, adding causal signal-time flow/toxicity features to the existing v95 path-state meta gate might create a validation-stable take/pass middle band that rejects false positives without increasing 10% live risk.

## Experiment

Code change: `src/pipeline/path_state_meta_probe.py` now copies signal-time flow/toxicity fields already present in replay samples: cumulative buy/sell volume, `volume_10s`, `buy_pressure`, derived `sell_pressure`, `buy_sell_volume_ratio`, buyer/seller overlap, recent seller reentry, buyer churn, and `lp_resistance_ratio_10s`. `tests/model/test_path_state_meta_probe.py` covers the copied/derived fields.

Replay command:

```bash
venv/bin/python scripts/run_path_state_meta_gate_replay.py \
  --model-dir data/models/20260519_v95_v84_selective_nearmiss_gate \
  --lifecycle-dir data/training \
  --output data/replay_reports/path_state_meta_gate_replay_20260521_flow_enhanced_v95.json \
  --force
```

Cache note: the local report used the script's default cache setting. Before accepting the result, the relevant validation sample cache was checked and contained the copied flow fields; the train and final cache keys used by this run did not exist before the run and were rebuilt. For reproducing this feature-plumbing experiment on another machine, run the same command with `--no-cache` unless the cache contents are explicitly verified.

The replay report path is `data/replay_reports/path_state_meta_gate_replay_20260521_flow_enhanced_v95.json`; it is replay evidence, not a live-switch artifact.

Validation result:

- Baseline: `27` trades, `186.4281%` return, `0.00946925` BNB, `74.0741%` win, `-28.3080%` max DD.
- Thresholds `0.35` through `0.90`: no-op, `27` trades, `0` rejects, same metrics as baseline.
- Thresholds `0.95` through `0.99`: no-trade, `105` rejects, `0` entries, `0` profit.

Final confirmation for selected validation raw-best `0.35`:

- Baseline: `32` trades, `390.4589%` return, `0.01983259` BNB, `81.25%` win, `-4.6523%` max DD, harsh-execution worst `170.0026%`.
- Candidate: identical headline/stress metrics, `32` gate entries, `0` rejects.
- `final_confirmation.passes_acceptance_gate=false`.

## Decision

Reject. The added flow/toxicity fields did not produce a usable middle band. Low thresholds were no-ops, and high thresholds removed all trades. Do not live switch.

Next direction: a narrower replay-only post-pump decay / sell-only pre-signal veto. It should expose causal short-window sell volume and normalized sell pressure from `feature_extractor`, combine that with recent peak-to-signal drawdown, and feed a per-episode score map into the existing `path_state_scores_by_episode` replay hook. The first falsification target is cases like `🆙`: high v95 score and PredReturn, favorable fill, but sharp pre-signal peak collapse and sell-only recent flow.
