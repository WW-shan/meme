# Execution Freshness Replay Context Audit

- Generated: `2026-06-08T03:38:14.343924+00:00`
- Model: `data/models/20260519_v95_v84_selective_nearmiss_gate`
- Selected proxy rule: `freshness_latency_volume_risk >= 1.29061`
- Outcome: `Rejected`
- Decision: `rejected_strict_replay_context_missing`
- Live switch evidence: `false`
- Runtime behavior changed: `false`

## Split Coverage

### Validation

- Samples: `140332`
- Baseline replay trades: `23`
- Baseline net profit BNB: `0.012252343033424175`
- Baseline win rate: `0.7391304347826086`
- Sample `lifecycle_status_chain_lag_seconds`: `missing`
- Sample `signal_volume_30s`: `available` via `['volume_30s']`
- Sample `signal_price_volatility`: `available` via `['price_volatility']`
- Trade-context `lifecycle_status_chain_lag_seconds`: `missing`
- Trade-context `signal_volume_30s`: `available` via `['entry_volume_30s', 'volume_30s']`
- Trade-context `signal_price_volatility`: `available` via `['entry_price_volatility', 'price_volatility']`
- Selected rule replayable from samples: `False`
- Selected rule replayable from replay trade context: `False`

### Final

- Samples: `204708`
- Baseline replay trades: `24`
- Baseline net profit BNB: `0.0020282580548887895`
- Baseline win rate: `0.5416666666666666`
- Sample `lifecycle_status_chain_lag_seconds`: `missing`
- Sample `signal_volume_30s`: `available` via `['volume_30s']`
- Sample `signal_price_volatility`: `available` via `['price_volatility']`
- Trade-context `lifecycle_status_chain_lag_seconds`: `missing`
- Trade-context `signal_volume_30s`: `available` via `['entry_volume_30s', 'volume_30s']`
- Trade-context `signal_price_volatility`: `available` via `['entry_price_volatility', 'price_volatility']`
- Selected rule replayable from samples: `False`
- Selected rule replayable from replay trade context: `False`

## Decision

The selected proxy freshness rule is not strict-replayable in the current dataset/replay surface because replay samples and replay trade logs do not carry `lifecycle_status_chain_lag_seconds`. The replay surface does carry `volume_30s` and `price_volatility`, so the missing input is specifically decision-time lifecycle freshness, not market-state context.

JSON report: `data/replay_reports/execution_freshness_replay_context_audit_20260608_freshness_replay_acceptance_gate.json`
