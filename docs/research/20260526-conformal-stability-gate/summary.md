# Conformal Stability Gate Research

## Question

Which conservative replay-integrated gate is most suitable for a live candidate selector under distribution shift: conformal risk control, adaptive conformal inference, online conformal under arbitrary shifts, or strongly adaptive online CP?

## Search and sources

- `smart-search deep "Which methods are best suited for a replay-integrated candidate gate under distribution shift for a live trading model: conformal risk control, adaptive conformal prediction, selective classification with abstention, or concept-drift-aware stability selection? Focus on methods that can be implemented as a conservative, decision-time gate using past data only, and that can be evaluated with walk-forward or rolling-window validation." --format json --output docs/research/20260526-conformal-stability-gate/plan.json`
- Broad search saved to `docs/research/20260526-conformal-stability-gate/01-search.json`
- Fallback search outputs:
  - `docs/research/20260526-conformal-stability-gate/02-zhipu.json`
  - `docs/research/20260526-conformal-stability-gate/03-exa.json`
- Fetched evidence:
  - `04-fetch-conformal-risk-control.md`
  - `05-fetch-adaptive-conformal-inference.md`
  - `06-fetch-online-conformal-arbitrary-shift.md`
  - `07-fetch-strongly-adaptive-online-cp.md`

## Takeaway

Use a conservative lower-confidence / rolling-window stable selector, not a fixed threshold or a single-tree validation pick. The useful shape is a replay-integrated ensemble gate that can survive distribution shift checks, not a looser acceptance rule.

## Experiment

Implemented a stable-LCB accepted-entry scorer:

- `src/pipeline/accepted_entry_loss_meta_gate.py`
- `scripts/run_accepted_entry_loss_meta_gate_replay.py`
- `tests/model/test_accepted_entry_loss_meta_gate.py`

Added a `stable-lcb` score mode that trains small trees across contiguous windows and scores each candidate by the lower quantile of ensemble keep probabilities.

## Result

Strict replay rejected the gate:

- validation improved at `buy_path_state_meta_gate_min_score=0.35`
- final collapsed
- stress weakened
- feature importances were unstable across windows

Conclusion: the gate is useful as shadow-only tooling, but it is not live-ready.

## Limitations

- The stable-LCB ensemble includes a full-training model plus rolling-window models, so the models are not independent shift samples.
- The lower-quantile score is index-based; with few surviving windows, the effective quantile can become more conservative than the nominal setting.
- A surviving window only needs both labels present, so class-thin windows can contribute weak or nearly constant models.

These limitations do not change the rejection decision. They mean the current LCB implementation should not be reused as proof of a robust live gate without another stability-focused iteration.

## Next direction

Move toward a candidate-level selector that explicitly models distribution shift or richer temporal/path labels, instead of only learning keep/skip from accepted-entry outcomes.
