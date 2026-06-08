# Execution Freshness Replay Context Audit

- Generated: `2026-06-08T11:40:23.799426+00:00`
- Model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Selected proxy rule: `lifecycle_status_chain_lag_seconds >= 6.10941`
- Outcome: `Rejected`
- Decision: `rejected_strict_replay_context_degenerate`
- Live switch evidence: `false`
- Runtime behavior changed: `false`

## Split Coverage

### Final

- Samples: `212135`
- Baseline replay trades: `24`
- Baseline net profit BNB: `0.0020282580548887895`
- Baseline win rate: `0.5416666666666666`
- Sample `lifecycle_status_chain_lag_seconds`: `available` via `['lifecycle_status_chain_lag_seconds']`
- Trade-context `lifecycle_status_chain_lag_seconds`: `available` via `['lifecycle_status_chain_lag_seconds']`
- Selected rule replayable from samples: `True`
- Selected rule replayable from replay trade context: `True`
- Selected rule semantically replayable from samples: `False`
- Selected rule semantically replayable from replay trade context: `False`
- Selected rule sample match count: `0`
- Selected rule trade-context match count: `0`
- Selected rule sample values: `count=212135, min=0.0, p50=0.0, p95=0.0, max=0.0, unique=1`
- Selected rule trade-context values: `count=24, min=0.0, p50=0.0, p95=0.0, max=0.0, unique=1`

### Validation

- Samples: `140332`
- Baseline replay trades: `23`
- Baseline net profit BNB: `0.012252343033424175`
- Baseline win rate: `0.7391304347826086`
- Sample `lifecycle_status_chain_lag_seconds`: `available` via `['lifecycle_status_chain_lag_seconds']`
- Trade-context `lifecycle_status_chain_lag_seconds`: `available` via `['lifecycle_status_chain_lag_seconds']`
- Selected rule replayable from samples: `True`
- Selected rule replayable from replay trade context: `True`
- Selected rule semantically replayable from samples: `False`
- Selected rule semantically replayable from replay trade context: `False`
- Selected rule sample match count: `0`
- Selected rule trade-context match count: `0`
- Selected rule sample values: `count=140332, min=0.0, p50=0.0, p95=0.0, max=0.0, unique=1`
- Selected rule trade-context values: `count=23, min=0.0, p50=0.0, p95=0.0, max=0.0, unique=1`

## Decision

The required freshness fields are present, but degenerate under the current strict replay anchor: the selected threshold matches no validation/final samples or replay trade-context rows. This is a rejected read-only audit, not live-switch evidence.

JSON report: `data/replay_reports/execution_freshness_replay_context_audit_20260608_chain_lag_replay_context.json`
