# Same-Token Early Replacement Replay Report

Date: 2026-05-27

## Question

Can the runner-retention rescue be made safer by learning a same-token early-entry replacement target: enter early only when a near-miss token appears likely to pass the current baseline gate soon, instead of admitting pure added rescue trades?

## Deep Search Evidence

- `smart-search doctor --format json` -> `00-doctor.json` (`ok=true`; configured keys redacted).
- `smart-search deep ... --budget deep --format json` -> `plan.json`.
- Broad method discovery -> `01-search.json`.
- Exa and Zhipu were attempted but unavailable: `02-exa.json`, `03-zhipu.json` record missing provider keys.
- Landmarking / dynamic time-to-event search -> `04-search-landmarking.json`; fetched source `07-fetch-landmarking-gradient-boosting.md`.
- Selective / conformal risk search -> `05-search-selective-risk.json`; fetched arXiv API evidence `08b-fetch-conformal-risk-control-arxiv-api.md` and `11-fetch-selective-conformal-risk-control-arxiv-api.md`.
- OPE / capacity search -> `06-search-ope-capacity.json`; fetched source `09-fetch-data-efficient-ope.md` and CPO note `10-fetch-constrained-policy-optimization.md`.

## Why This Direction Was Chosen

The prior preserve-base replay failed because pure added rescue trades stayed toxic, but trade-delta showed a promising substructure: many candidate trades were same-token earlier entries replacing a later baseline entry. That suggests a landmarking/time-to-threshold target: learn whether a current near-miss will become a baseline-accepted entry soon, then combine it with runner-retention quality.

Fetched evidence supports the shape:

- Landmarking/dynamic survival modeling uses information available up to a landmark time to predict an event in a future window; this maps to predicting baseline-gate crossing within a short horizon.
- Selective/conformal risk-control evidence supports abstaining unless a selected subset passes risk/coverage constraints.
- OPE/constrained-policy evidence supports offline evaluation before deployment when bad policies are costly and capacity/risk constraints matter.

## Implemented Probe

Code changed:

- `src/pipeline/runner_retention_replay_gate.py` adds `target_mode=runner_retention_early_replacement` by relabeling training positives to require both `runner_retention_positive` and a same-token baseline entry within `early_replacement_max_lead_seconds`.
- `scripts/run_runner_retention_candidate_gate_replay.py` adds `--early-replacement-max-lead-seconds` and reports the chosen value in `precision_guard`.
- `tests/model/test_runner_retention_replay_gate.py` covers early-replacement labels and CLI propagation.

Command:

```bash
python scripts/run_runner_retention_candidate_gate_replay.py \
  --preserve-base-candidates \
  --early-replacement-max-lead-seconds 20 \
  --write-selected-trade-delta \
  --output data/replay_reports/runner_retention_candidate_gate_replay_20260527_early_replacement20.json \
  --force
```

## Result

Reject. The new target was too conservative and produced a no-op versus the baseline.

- Decision: `reject`.
- Validation baseline: `32` trades, `0.02109487` BNB, win rate `75.00%`.
- Validation selected: `32` trades, `0.02109487` BNB, win rate `75.00%`.
- Final baseline: `21` trades, `0.00517452` BNB, win rate `52.38%`.
- Final selected: `21` trades, `0.00517452` BNB, win rate `52.38%`.
- Final gate failed `net_profit_bnb` because the candidate tied baseline instead of improving it.
- Trade delta was empty on validation and final: no added candidate trades and no removed baseline trades.
- Training support was only `15` positives out of `619787` raw candidates, and feature importance collapsed to `pred_return`, so the learned gate did not find a usable replacement boundary.

## Conclusion

The same-token early-replacement framing is directionally better than pure rescue, but a `20s` baseline-entry-soon target is too sparse and degenerates to the baseline. Do not switch live and do not change `.env`, thresholds, sizing, model artifacts, or bot processes.

Next experiment should either widen the maturity window / improve the label with a direct replacement-utility target, or build an oracle upper-bound diagnostic before another live-deployable proxy.

Scoreboard update: `docs/model_scoreboard.md` records this rejected no-op experiment.
