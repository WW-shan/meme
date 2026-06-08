# Execution Freshness Replay Context Audit

- Generated: `2026-06-08T10:42:36.303129+00:00`
- Model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Selected proxy rule: `lifecycle_status_chain_lag_seconds >= 6.10941`
- Outcome: `Research Alpha`
- Decision: `strict_replay_context_available`
- Live switch evidence: `false`
- Runtime behavior changed: `false`

## Split Coverage

### Final

- Samples: `211439`
- Baseline replay trades: `24`
- Baseline net profit BNB: `0.0020282580548887895`
- Baseline win rate: `0.5416666666666666`
- Sample `lifecycle_status_chain_lag_seconds`: `available` via `['lifecycle_status_chain_lag_seconds']`
- Trade-context `lifecycle_status_chain_lag_seconds`: `available` via `['lifecycle_status_chain_lag_seconds']`
- Selected rule replayable from samples: `True`
- Selected rule replayable from replay trade context: `True`

### Validation

- Samples: `140332`
- Baseline replay trades: `23`
- Baseline net profit BNB: `0.012252343033424175`
- Baseline win rate: `0.7391304347826086`
- Sample `lifecycle_status_chain_lag_seconds`: `available` via `['lifecycle_status_chain_lag_seconds']`
- Trade-context `lifecycle_status_chain_lag_seconds`: `available` via `['lifecycle_status_chain_lag_seconds']`
- Selected rule replayable from samples: `True`
- Selected rule replayable from replay trade context: `True`

## Decision

The selected freshness rule is available in both strict replay samples and replay trade context for validation and final splits. This is a read-only Research Alpha audit, not live-switch evidence.

JSON report: `data/replay_reports/execution_freshness_replay_context_audit_20260608_chain_lag_replay_context.json`
