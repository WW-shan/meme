# Replacement-Only Oracle Upper-Bound Diagnostic

## Question

After same-token early-replacement labels at `20s` and `60s` produced only `15/619787` train positives and no replay trade delta, this round tested whether the replacement direction is dead by support or only needs a better non-leaky selector.

The diagnostic is intentionally not a deployable policy. It uses ex-post lifecycle paths to estimate an upper-bound shape for earlier same-token candidate entries before later baseline entries.

## Evidence

SmartSearch Deep Research plan and fetched evidence:

- `plan.json`
- `01-search-oracle-bound.json`
- `02-fetch-counterfactual-risk-minimization.md`
- `03-fetch-data-efficient-ope.md`
- `04-fetch-mlfinpy-labeling.md`
- `05-zhipu-oracle-bound.json` and `06-exa-oracle-bound.json` record provider configuration blockers for supplemental search.

Key interpretation:

- Logged trading data is biased and incomplete; without exploration propensity, this is not valid IPS/OPE evidence.
- The report is therefore labeled `estimator_type=ex_post_path_simulation`, `uses_ex_post_outcomes=true`, `not_deployable_policy=true`, and `live_switch_evidence=false`.
- Triple-barrier-style path labels are appropriate for diagnosing stop/profit ordering; MFE is only a ceiling, not realized return.

## Implementation

Added a reusable offline diagnostic:

- `src/pipeline/replacement_oracle_upper_bound.py`
- `scripts/run_replacement_oracle_upper_bound_diagnostic.py`
- `tests/model/test_replacement_oracle_upper_bound.py`

The CLI reuses the current runner-retention candidate-grid helpers, pairs earlier same-token candidates to the immediate future baseline pass, deduplicates candidate rows by token/time, and reports by lead window.

## Commands

Phase 1 support and pre-baseline movement:

```bash
python scripts/run_replacement_oracle_upper_bound_diagnostic.py \
  --output data/replay_reports/replacement_oracle_upper_bound_20260527_phase1.json \
  --force
```

Phase 2 barrier-respecting realized upper bound:

```bash
python scripts/run_replacement_oracle_upper_bound_diagnostic.py \
  --phase barrier \
  --output data/replay_reports/replacement_oracle_upper_bound_20260527_barrier.json \
  --force
```

## Results

Phase 1 passed the support/pre-move gate:

- Validation replacement pairs: `251/290/341/369` for `20/60/120/300s`.
- Final replacement pairs: `154/171/212/254` for `20/60/120/300s`.
- Validation pre-baseline move p75: `26.36%/30.63%/36.59%/37.38%`.
- Final pre-baseline move p75: `27.20%/32.60%/39.80%/38.17%`.

Phase 2 rejected blanket replacement:

- Decision: `reject`.
- Reason: `delta_realized_p50_below_min`.
- Barrier config: `horizon_seconds=560`, `take_profit_pct=25`, `stop_loss_pct=-18`, equal cost parity.
- Validation `delta_realized_pct_p50=0.0` for all `20/60/120/300s` windows.
- Final `delta_realized_pct_p50=0.0` for all `20/60/120/300s` windows.
- Candidate stop-first ratios stayed below the `0.40` ceiling, but median realized delta still failed.

The useful signal is distributional, not blanket-actionable: MFE delta medians are strongly positive (`~37%-49%`), and candidate profit-first ratios are often higher than baseline, but the realized median is tied at `0.0` because many candidate and baseline anchors both reach the same `+25%` take-profit barrier.

## Decision

Reject this as a live model change or blanket early-replacement policy.

No `.env`, threshold, sizing, model artifact, bot process, or live switch changed.

Next direction should not mechanically widen the replacement window. If continuing this branch, the only plausible model-improvement path is a decision-time selector over replacement pairs that predicts positive realized delta or avoids ties/losses, with strict validation/final/walk-forward/stress replay before any live consideration.
