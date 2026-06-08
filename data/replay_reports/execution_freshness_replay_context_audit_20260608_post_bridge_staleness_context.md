# Execution Freshness Replay Context Audit

- Generated: `2026-06-08T09:09:52.094035+00:00`
- Model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Selected proxy rule: `lifecycle_status_staleness_seconds >= 0.015399`
- Outcome: `Rejected`
- Decision: `rejected_strict_replay_context_missing`
- Live switch evidence: `false`
- Runtime behavior changed: `false`

## Split Coverage

### Final

- Samples: `210376`
- Baseline replay trades: `24`
- Baseline net profit BNB: `0.0020282580548887895`
- Baseline win rate: `0.5416666666666666`
- Sample `lifecycle_status_staleness_seconds`: `missing` via `[]`
- Trade-context `lifecycle_status_staleness_seconds`: `missing` via `[]`
- Selected rule replayable from samples: `False`
- Selected rule replayable from replay trade context: `False`

### Validation

- Samples: `140332`
- Baseline replay trades: `23`
- Baseline net profit BNB: `0.012252343033424175`
- Baseline win rate: `0.7391304347826086`
- Sample `lifecycle_status_staleness_seconds`: `missing` via `[]`
- Trade-context `lifecycle_status_staleness_seconds`: `missing` via `[]`
- Selected rule replayable from samples: `False`
- Selected rule replayable from replay trade context: `False`

## Decision

The selected freshness rule is not strict-replayable in the current replay surface because one or more required decision-time freshness fields are missing from validation/final samples or replay trade context.

JSON report: `data/replay_reports/execution_freshness_replay_context_audit_20260608_post_bridge_staleness_context.json`
