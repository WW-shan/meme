# BUY_NOT_READY Unsupported Quote Outcome Probe

Generated: 2026-05-30

## Question

The latest live trigger after the slow-runner `Research Alpha` boundary was a queued `美股` signal at `2026-05-30 09:42:39 CST` with `prob=0.952950793972124`, `PredReturn=52.63034186879594`, and `volume_30s=374.5802756686467`. It did not become a trade because the runtime quote guard emitted `BUY_NOT_READY` for unsupported quote asset `0x8d0D000Ee44948FC98c9B98A4FA4921476f08B0d`.

The question was whether these post-guard `BUY_NOT_READY` events are only correct non-tradeable protection, or whether they represent a model-positive opportunity segment worth future universe/routing research.

## Research Evidence

No new outside method search was needed for this node because this is a local runtime/data-quality attribution question, not a new model method. It reused committed artifacts:

- `docs/research/20260522-live-unsupported-quote-guard/summary.md`
- `docs/research/20260529-live-shadow-router-evaluator/summary.md`
- `docs/research/20260530-entry-protection-skip-outcomes/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`

New live-derived angle: the unsupported-quote guard is already accepted as a safety fix, but the goal had no reusable outcome probe to score whether post-guard skipped queued signals would have reached profit barriers.

## Implementation

Reusable read-only tooling:

- `src/pipeline/buy_not_ready_probe.py`
- `scripts/probe_buy_not_ready_outcomes.py`
- `tests/model/test_buy_not_ready_probe.py`
- `tests/model/test_buy_not_ready_probe_cli.py`

The probe scans `BUY_NOT_READY` audit rows, filters by reason substring, joins lifecycle paths, anchors at `signal_price` or `lifecycle_price_current`, and scores the current `560s` hold window plus a bounded `10800s` horizon. It records input fingerprints and marks the report as read-only with `live_switch_evidence=false`, `safe_for_live_switch=false`, and `max_outcome_tier=Research Alpha`.

## Command

```bash
venv/bin/python scripts/probe_buy_not_ready_outcomes.py \
  --since '2026-05-28 00:00:00' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --recent-lifecycle-files 24 \
  --output-json data/replay_reports/buy_not_ready_outcomes_20260530_unsupported_quote_recent.json \
  --output-md data/replay_reports/buy_not_ready_outcomes_20260530_unsupported_quote_recent.md \
  --max-hold-seconds 560 \
  --horizon-seconds 10800 \
  --min-support 3 \
  --max-sample 0 \
  --force
```

## Result

Report:

- `data/replay_reports/buy_not_ready_outcomes_20260530_unsupported_quote_recent.json`
- `data/replay_reports/buy_not_ready_outcomes_20260530_unsupported_quote_recent.md`

Summary:

- Matching unsupported-quote events since `2026-05-28 00:00:00`: `6`
- Lifecycle-covered events: `6`
- Support events hitting `+25%` before stop within `560s`: `3`
- Within-hold labels: `missed_within_hold_profit=3`, `guarded_flat_timeout=1`, `guarded_stop_first_within_hold=1`, `guarded_weak_timeout=1`
- Extended labels: `profit_within_hold=3`, `extended_stop_first=2`, `no_extended_profit=1`
- Timeout return average / median: `-7.328339972086526%` / `-7.577515688612579%`
- Extended last return average / median within the `10800s` horizon: `-18.70217684626068%` / `-15.983739761870934%`

Support examples:

- `SP500`: first `+25%` after `4.131587s`, `+66.345059%` MFE inside hold, timeout `+42.697753%`.
- `特朗普牛`: first `+25%` after `143.4899s`, but then hit `-18%` after `217.4899s` and timed out at `-43.556482%`; this is opportunity evidence only if a future route also has a fast harvest policy.
- `美股`: latest trigger; first `+25%` after `27.516073s`, MFE `+37.792776%`, timeout `-4.715229%`.

Negative/protective examples:

- `DONNY`: stop-first inside hold (`-18%` after `226.306249s`) before any `+25%`.
- `GOLDEN AGE`: flat within hold and extended stop-first.
- `Trump`: no extended profit and weak timeout.

## Tier

`Research Alpha`.

This is not a live-switch candidate and does not justify changing the accepted quote guard. The evidence says the unsupported-quote segment is not purely junk: half of recent covered events reached `+25%` before stop inside the current hold window, including the newest `美股` trigger. It is still mixed and includes sharp giveback paths, so any future work must be replay-only and must pair a quote-universe/routing question with fast-harvest risk controls.

## Decision

No live switch. No `.env`, `.env.example`, threshold, sizing, model artifact, quote guard, bot process, collector process, or runtime behavior changed.

Scoreboard update: completed in `docs/model_scoreboard.md`.

Next direction: keep the quote guard unchanged, but treat unsupported-quote post-guard events as a new research-alpha segment. The next falsifiable step should be a replay-only universe/routing feasibility or shadow-label design that asks whether these ERC20-quoted opportunities can be captured without increasing 10% live sizing risk or bypassing the native-quote safety guard.
