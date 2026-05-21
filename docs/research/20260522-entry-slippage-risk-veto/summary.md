# Entry Slippage Risk Veto Research Summary

Generated: 2026-05-22T00:00:00Z

## Contract

- Active live model remains `data/models/20260519_v95_v84_selective_nearmiss_gate`.
- Live sizing remains 10% position fraction with max 8 open positions.
- This research is default-off replay evidence, not live-switch evidence.
- No change is justified for `.env`, `data/models/**`, `docs/goals/**`, or live runtime thresholds from this node.

## Current State

The active business round is `.ccg/tasks/live-model-optimization-business-round-20260522`.

The preceding live/execution checks showed:

- Since the v95 restart anchor, the live sample had `open_count=18` and `observed_entry_execution_failure_rate=0.18181818181818182`.
- The observed `p95_positive_entry_slippage_pct` was `0.13988759185875`, with a calibrated recommendation around `0.15988759185874998`.
- A direct validation sweep of `entry_price_protection_pct` from `0.05` through `0.25` did not produce a deployable improvement.

That evidence supported a replay-only candidate-level veto experiment, but not a live parameter change.

## Experiment

The implemented branch adds default-off replay parameters:

- `buy_entry_slippage_risk_veto_min_age_seconds`
- `buy_entry_slippage_risk_veto_extension_window_seconds`
- `buy_entry_slippage_risk_veto_min_price_extension_pct`
- `buy_entry_slippage_risk_veto_min_drawdown_from_peak_pct`
- `buy_entry_slippage_risk_veto_min_recent_jump_pct`
- `buy_entry_slippage_risk_veto_min_entry_volume_30s`
- `buy_entry_slippage_risk_veto_min_entry_price_volatility`

The replay uses only causal signal-time information: recent price extension, drawdown from recent peak, latest sample-to-sample jump, `volume_30s`, `price_volatility`, and candidate age. The branch records `entry_slippage_risk_veto_signal_count` and `entry_slippage_risk_veto_reject_count`.

Files:

- `src/pipeline/train_hybrid.py`
- `scripts/run_entry_slippage_risk_veto_replay.py`
- `tests/model/test_entry_slippage_risk_veto.py`
- `tests/model/test_entry_slippage_risk_veto_replay_cli.py`

Reports:

- `data/replay_reports/entry_slippage_risk_veto_replay_20260522_v95_limited8.json`
- `data/replay_reports/entry_slippage_risk_veto_probe_drawdown0_20260522_v95.json`
- `data/replay_reports/entry_slippage_risk_veto_probe_loose_trigger_20260522_v95.json`
- `data/replay_reports/entry_slippage_risk_veto_probe_small_sweep_20260522_v95.json`

## Results

The full 64-candidate replay command was attempted:

```bash
venv/bin/python scripts/run_entry_slippage_risk_veto_replay.py --output data/replay_reports/entry_slippage_risk_veto_replay_20260522_v95.json
```

It ran for about 30 minutes with high CPU and no report. Per the task runtime guard, it was stopped and replaced with bounded diagnostics.

Limited 8-candidate strict-grid report:

| Metric | Baseline | Best limited candidate |
|---|---:|---:|
| Trades | `32` | `32` |
| Net profit BNB | `0.016149475023616806` | `0.016149475023616806` |
| Win rate | `0.8125` | `0.8125` |
| Max DD | `-31.769381949238507%` | `-31.769381949238507%` |
| WF worst return | `62.679401031474534%` | `62.679401031474534%` |
| Stress worst return | `218.53760012497244%` | `218.53760012497244%` |
| Veto rejects | `0` | `0` |

The strict grid failed on `net_profit_bnb` and `entry_slippage_risk_veto_reject_count`.

Additional probes:

| Probe | Rejects | Trades | Net profit BNB | Win rate | Max DD | WF worst return | Stress worst return | Decision |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| Drawdown floor `0.0` | `0` | `32` | `0.016149475023616806` | `0.8125` | `-31.769381949238507%` | `62.679401031474534%` | `218.53760012497244%` | reject |
| Loose trigger | `127` | `5` | `0.0007549373864733479` | `0.8` | `-27.501862356933316%` | `0.0%` | `8.968596039232546%` | reject |
| Small sweep `extension=0.5`, `jump=0.0` | `40` | `24` | `0.012455451396960738` | `0.7916666666666666` | `-33.057699771298786%` | `49.56514496686037%` | `149.047939352997%` | reject |
| Small sweep `extension=0.5`, `jump=0.02` | `31` | `26` | `0.013733768179635217` | `0.8076923076923077` | `-33.057699771298786%` | `59.35138495626613%` | `174.45003583167284%` | reject |
| Small sweep `extension=0.5`, `jump=0.05` | `20` | `27` | `0.014500786592388841` | `0.8148148148148148` | `-33.057699771298786%` | `61.99963132808233%` | `197.94383036303634%` | reject |
| Small sweep `extension=1.0`, `jump=0.0` | `12` | `29` | `0.015320002866222052` | `0.8275862068965517` | `-31.769381949238507%` | `61.99963132808233%` | `206.34314029218515%` | reject |

## Decision

Current status: `NO_GO_FOR_LIVE_RULE`.

Reasons:

- Strict planned thresholds do not reject actual validation entries.
- Looser thresholds can reject real entries, but they cut too much profit and/or worsen drawdown.
- No candidate beats the v95 validation baseline across profit, drawdown, walk-forward, stress, and trade-count gates.
- The result does not justify changing `.env`, model artifacts, or live runtime parameters.

## Next Direction

Do not repeat another static price-extension/slippage threshold grid from this node.

The useful next direction is a richer candidate-level filter using causal flow/path-state features, or a learned support-constrained meta filter around existing v95 candidates. Any next candidate must stay default-off until it beats the current v95 baseline on validation, sealed final, walk-forward, harsh stress, drawdown, and trade-count discipline under 10% sizing.
