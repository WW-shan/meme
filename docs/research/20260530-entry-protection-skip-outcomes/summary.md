# Entry Protection Skip Outcome Probe

Generated: 2026-05-30

## Contract

- Active live model remains `data/models/20260519_v95_v84_selective_nearmiss_gate`.
- Live sizing remains 10% position fraction; no fixed stake was introduced.
- This node is read-only attribution and replay-direction evidence, not live-switch evidence.
- No `.env`, `.env.example`, model artifact, threshold, bot process, collector process, or runtime behavior changed.

## Live Trigger

The activation45 full-day shadow refresh after the replacement-pair selector rejection found one unmatched queued shadow-used signal:

- Token: `BTC` (`0x0c3E642757eFfd7797439Ba33be6e228a6664444`)
- Signal time: `2026-05-30 02:07:01 CST`
- Skip time: `2026-05-30 02:07:04 CST`
- `prob=0.9871236046862742`
- `PredReturn=85.43009813900393`
- `volume_30s=1.5718949900990098`
- `price_volatility=0.13208593329509666`
- `signal_price=8.811188132431943e-09`
- `candidate_price=1.9950613022e-08`
- `ENTRY_PRICE_PROTECTION_SKIP` signal-to-candidate jump: `+126.42364142205085%` versus live protection `25%`

Failure tag: `entry_slippage_high` / `data_freshness_or_execution_alignment_gap`.

## Prior Work Checked

This is intentionally different from the already rejected accepted-entry slippage veto branches:

- `docs/research/20260521-entry-slippage-pump-exhaustion/summary.md`
- `docs/research/20260522-entry-slippage-risk-veto/summary.md`
- `docs/research/20260526-postpeak-entry-slippage-veto/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`

Those branches tested replay-time accepted-entry veto thresholds. This probe asks the opposite question: when live protection skips an otherwise queued candidate, would that candidate have reached profit within the current hold window, or did protection avoid a chase?

## Implementation

Reusable files:

- `src/pipeline/entry_protection_skip_probe.py`
- `scripts/probe_entry_protection_skip_outcomes.py`
- `tests/model/test_entry_protection_skip_probe.py`
- `tests/model/test_entry_protection_skip_probe_cli.py`

The probe is data-driven and not token-specific. It parses all `ENTRY_PRICE_PROTECTION_SKIP` rows in `data/signal_audit.jsonl`, merges collector/lifecycle paths, anchors at `candidate_price`, and scores:

- current hold-window MFE/MAE and first `+25%`, `+60%`, `-18%`, `-25%`
- timeout mark at `max_hold_seconds`
- extended-horizon MFE/MAE and final observed return
- labels such as `missed_within_hold_profit`, `protected_flat_timeout`, `protected_stop_first_within_hold`, and `late_profit_after_hold`

## Command

```bash
venv/bin/python scripts/probe_entry_protection_skip_outcomes.py \
  --since '2026-05-29 21:19:42' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --lifecycle-file data/training/lifecycle_incremental_20260525_123016_part001.jsonl \
  --output-json data/replay_reports/entry_protection_skip_outcomes_20260530_after_shadow_direction_entry.json \
  --output-md data/replay_reports/entry_protection_skip_outcomes_20260530_after_shadow_direction_entry.md \
  --max-hold-seconds 560 \
  --horizon-seconds 10800 \
  --max-sample 0 \
  --force
```

## Result

Report:

- `data/replay_reports/entry_protection_skip_outcomes_20260530_after_shadow_direction_entry.json`
- `data/replay_reports/entry_protection_skip_outcomes_20260530_after_shadow_direction_entry.md`

Summary:

- `skip_count=1`
- `with_path_count=1`
- `missing_path_count=0`
- `supports_relaxing_entry_protection_count=0`
- `within_hold_label_counts={"protected_flat_timeout": 1}`
- `extended_label_counts={"late_profit_after_hold": 1}`
- `timeout_return_pct_median=3.9453389652795323`
- `extended_last_return_pct_median=-70.7896372732952`

BTC path from candidate price:

- current 560s hold window: max `+3.9453389652795323%`, min `-3.2431589267389094%`, no `+25%`, no `-18%`
- first `+25%`: `882.643365s` after skip
- first `+60%`: `4988.643365s` after skip
- max: `+89.2711611385804%`
- first `-18%/-25%`: `10589.643365s` after skip
- last observed return: `-70.7896372732952%`

## Decision

Outcome tier: `Rejected`.

Do not loosen entry price protection from this evidence. The single covered skip did not reach `+25%` within the current 560s hold window; the later runner would not have been harvested by the current runtime profile and ultimately collapsed deeply from the candidate price.

Scoreboard update: completed in `docs/model_scoreboard.md`.

Next direction: keep the skip-outcome probe as the systematic attribution path for future `ENTRY_PRICE_PROTECTION_SKIP` events, but return to direction selection rather than repeating static slippage threshold grids.
