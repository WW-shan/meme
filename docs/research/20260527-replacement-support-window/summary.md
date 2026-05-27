# Replacement Support Window Research

Date: 2026-05-27

## Question

Can the same-token early-replacement runner-retention target become useful by widening the support window from `20s` to `60s`, or is the current label universe still too sparse to improve the live-sized replay?

## Deep Search Evidence

- `smart-search doctor --format json` was run as preflight and returned `ok=true` in the terminal; no doctor file was saved because it contains masked local provider configuration.
- `smart-search deep "How can we evaluate whether same-token early replacement / replacement-only support windows improve live trading model precision without worsening drawdown? ..."` -> `plan.json`.
- Broad discovery:
  - `01-search-dtr.json`
  - `02-search-delayed-feedback.json`
- Fetched evidence:
  - `03-fetch-dtr-tutorial.md`: dynamic treatment regimes are sequential decision rules based on evolving observed history; the key implementation warning for this bot is that a replacement policy must be evaluated as a policy, not as an isolated label count.
  - `04-fetch-offline-delays.md`: offline-to-online delayed environments create distribution mismatch and require conservative, support-aware evaluation rather than blind offline extrapolation.
  - `05-fetch-belief-offline-rl.md`: OpenReview metadata for the same delayed offline RL line.
  - `06-fetch-data-efficient-ope.md`: OPE is relevant when deploying a bad policy is costly; for this repo, strict replay plus trade-delta attribution is preferred over pure OPE because replay has the actual lifecycle paths and current execution assumptions.

## Prior Result

The previous same-token early-replacement replay at `20s` was rejected:

- Raw training labels: `15` positives out of `619787` candidates.
- Validation and final candidate trades exactly matched baseline.
- Selected trade delta was empty on both validation and final.
- Conclusion: the `20s` target was too sparse and degenerated to a no-op.

Fresh live input after the delayed-confirmation commit was also checked in
`data/replay_reports/time_to_barrier_probe_20260527_post_delayed_confirmation_commit.json`.
The slice had only `3` per-token candidates since `2026-05-27 12:00:00`, all with `policy=skip`
(`2` flat timeouts and `1` stop-first), so it did not justify another quick-profit branch.

## Experiment

This follow-up did not change code. It kept the same strict runner-retention candidate-gate replay, preserved base candidates, and widened only the early-replacement label window to `60s`.

Command:

```bash
python scripts/run_runner_retention_candidate_gate_replay.py \
  --preserve-base-candidates \
  --early-replacement-max-lead-seconds 60 \
  --write-selected-trade-delta \
  --output data/replay_reports/runner_retention_candidate_gate_replay_20260527_early_replacement60.json \
  --force
```

## Result

Reject. The wider `60s` window produced the same no-op shape as `20s`.

- Decision: `reject`.
- Validation baseline: `32` trades, `0.021094872146` BNB, `75.00%` win rate, `-9.8821%` max drawdown.
- Validation selected: `32` trades, `0.021094872146` BNB, `75.00%` win rate, `-9.8821%` max drawdown.
- Final baseline: `21` trades, `0.005174515325` BNB, `52.38%` win rate, `-18.2292%` max drawdown.
- Final selected: `21` trades, `0.005174515325` BNB, `52.38%` win rate, `-18.2292%` max drawdown.
- Final gate failed only `net_profit_bnb` because the candidate tied the baseline instead of improving it.
- Raw training support stayed `15` positives out of `619787` candidates, identical to the `20s` run.
- Feature importance still collapsed to `pred_return=1.0`.
- Trade delta stayed empty:
  - validation added trades: `0`; removed baseline trades: `0`; common trades unchanged: `32`.
  - final added trades: `0`; removed baseline trades: `0`; common trades unchanged: `21`.

## Conclusion

Do not continue mechanically widening this same target to `120s` or `300s`. The issue is not simply that the `20s` window was too tight; even `60s` finds no additional positive support and no replay behavior change.

No live switch. No `.env`, threshold, sizing, model artifact, or bot process changed.

Next direction: build a replacement-only oracle upper-bound diagnostic before another deployable proxy. The useful question is whether there is any material counterfactual value in earlier same-token replacement at all; if the oracle bound is weak, this branch should be closed and the next search should move to richer early-collapse/toxicity separation.

Scoreboard update: `docs/model_scoreboard.md` records this rejected no-op experiment.
