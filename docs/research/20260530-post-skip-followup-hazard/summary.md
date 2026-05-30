# Post-Skip Follow-Up Hazard Probe

Generated: 2026-05-31

## Contract

- Active live model remains `data/models/20260519_v95_v84_selective_nearmiss_gate`.
- Live sizing remains 10% position fraction; no fixed stake was introduced.
- This node is read-only attribution and research evidence, not live-switch evidence.
- No `.env`, `.env.example`, model artifact, threshold, bot process, collector process, or runtime behavior changed.

## Live Trigger

The repeated `帕鲁` loss sequence showed a distinct adverse-selection shape:

- several `ENTRY_PRICE_PROTECTION_SKIP` rows occurred first for the same token because candidate price had already jumped hard from signal price;
- a later accepted buy on the same token then closed as a loss;
- the latest `四川话` loss did not have this prior-skip pattern, so it was handled under the execution-freshness refresh instead.

This branch intentionally tests the opposite of the earlier entry-protection skip-outcome probe. It does not ask whether protection should be loosened. It asks whether prior protection skips should become a pre-open abstention feature for later accepted entries on the same token.

## Prior Work Checked

Relevant rejected or non-deployable branches:

- `docs/research/20260530-entry-protection-skip-outcomes/summary.md`
- `docs/research/20260521-entry-slippage-pump-exhaustion/summary.md`
- `docs/research/20260522-entry-slippage-risk-veto/summary.md`
- `docs/research/20260526-postpeak-entry-slippage-veto/summary.md`

The new implementation avoids hard-coded token logic and avoids accepted-entry slippage veto thresholds. It uses only prior `ENTRY_PRICE_PROTECTION_SKIP` events before the accepted entry decision.

## External Evidence

SmartSearch evidence is stored under `docs/research/20260530-post-skip-followup-hazard/evidence/`.

- CFTC HFT price-process evidence: adverse microstructure states, volatility, noise, and jumps can make stale or chased states systematically worse.
- Kearns/Nevmyvaka HFT ML evidence: state-based policies should use recent market activity and out-of-sample validation rather than a static global threshold.
- Execution-cost evidence: slower or stale participants can face worse execution and non-execution risk, supporting prior failed/skip events as an adverse-selection feature candidate.

## Implementation

Reusable files:

- `src/pipeline/entry_protection_skip_probe.py`
- `scripts/probe_post_skip_followup_hazard.py`
- `tests/model/test_entry_protection_skip_probe.py`
- `tests/model/test_post_skip_followup_hazard_cli.py`

The probe:

- pairs real `OPEN`/`CLOSE` trades from `paper_trades`;
- finds same-token `ENTRY_PRICE_PROTECTION_SKIP` events before the accepted entry decision within a configurable lookback;
- builds train-derived abstention rules from prior-skip count, skip slippage, signal-to-candidate jump, probability, PredReturn, and recency;
- evaluates validation/final abstention delta, winner skips, and top-loss dependency;
- marks `live_switch_evidence=false`, `safe_for_live_switch=false`, and `requires_replay_before_live_change=true`.

## Commands

Primary 120s lookback:

```bash
venv/bin/python scripts/probe_post_skip_followup_hazard.py \
  --since '2026-05-19 04:02:23' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --recent-lifecycle-files 48 \
  --lookback-seconds 120 \
  --output-json data/replay_reports/post_skip_followup_hazard_probe_20260531_after_sichuanhua_loss.json \
  --output-md data/replay_reports/post_skip_followup_hazard_probe_20260531_after_sichuanhua_loss.md \
  --max-sample-rows 120 \
  --force
```

600s sensitivity:

```bash
venv/bin/python scripts/probe_post_skip_followup_hazard.py \
  --since '2026-05-19 04:02:23' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --recent-lifecycle-files 48 \
  --lookback-seconds 600 \
  --output-json data/replay_reports/post_skip_followup_hazard_probe_20260531_after_sichuanhua_loss_lookback600.json \
  --output-md data/replay_reports/post_skip_followup_hazard_probe_20260531_after_sichuanhua_loss_lookback600.md \
  --max-sample-rows 120 \
  --force
```

## Result

Primary 120s report:

- `data/replay_reports/post_skip_followup_hazard_probe_20260531_after_sichuanhua_loss.json`
- `data/replay_reports/post_skip_followup_hazard_probe_20260531_after_sichuanhua_loss.md`

600s sensitivity report:

- `data/replay_reports/post_skip_followup_hazard_probe_20260531_after_sichuanhua_loss_lookback600.json`
- `data/replay_reports/post_skip_followup_hazard_probe_20260531_after_sichuanhua_loss_lookback600.md`

Both runs were rejected:

- `outcome_tier=Rejected`
- `decision=no_train_post_skip_followup_candidate`
- paired real trades: `52`
- post-skip follow-up trades: `1`
- train post-skip trades: `0`
- validation post-skip trades: `0`
- final post-skip trades: `1`
- scanned rules: `0`
- train eligible rules: `0`

The 600s sensitivity check produced the same counts as the 120s run, so the rejection is not caused by a too-narrow two-minute window. The problem is support: the live history currently has one example, and it lands only in the final split.

## Decision

Outcome tier: `Rejected`.

Do not build a live/runtime gate from prior `ENTRY_PRICE_PROTECTION_SKIP` follow-up history yet. The direction remains conceptually valid and the generic probe should be reused when more live examples arrive, but the current evidence cannot train or validate a rule.

Scoreboard update: completed in `docs/model_scoreboard.md`.

Next direction: return to broader structural candidates with more support, especially replay-compatible execution-freshness features / queued-opened freshness shadow labels or direct paired-delta utility targets.
