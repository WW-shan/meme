# Chain-Lag Replay Context Bridge

Date: 2026-06-08

## Decision

Outcome: Research Alpha. This is not a Shadow Candidate and not live-switch evidence.

The selected execution-freshness proxy field `lifecycle_status_chain_lag_seconds` is now available in both strict replay samples and strict replay trade-log entry context for validation and final splits. This removes the replay-surface blocker for chain-lag freshness rules, but it does not by itself prove that a freshness gate improves replay PnL, drawdown, stress, or walk-forward metrics.

## Evidence

- Report: `data/replay_reports/execution_freshness_replay_context_audit_20260608_chain_lag_replay_context.json`
- Markdown: `data/replay_reports/execution_freshness_replay_context_audit_20260608_chain_lag_replay_context.md`
- Selected proxy rule checked for replayability: `lifecycle_status_chain_lag_seconds >= 6.109405994415283`
- Decision: `strict_replay_context_available`
- Runtime behavior changed: `false`
- Live switch evidence: `false`

Validation coverage:

- Samples: `140332`
- Baseline replay trades: `23`
- Sample `lifecycle_status_chain_lag_seconds`: `140332/140332`, coverage `1.0`
- Trade-context `lifecycle_status_chain_lag_seconds`: `23/23`, coverage `1.0`
- Baseline net profit BNB: `0.012252343033424175`
- Baseline win rate: `0.7391304347826086`

Final coverage:

- Samples: `211439`
- Baseline replay trades: `24`
- Sample `lifecycle_status_chain_lag_seconds`: `211439/211439`, coverage `1.0`
- Trade-context `lifecycle_status_chain_lag_seconds`: `24/24`, coverage `1.0`
- Baseline net profit BNB: `0.0020282580548887895`
- Baseline win rate: `0.5416666666666666`

## Implementation Notes

The bridge deliberately uses decision-time chain lag derived from observed historical trade timestamps at or before `sample_time`. It does not promote `lifecycle_status_staleness_seconds`, because historical lifecycle records do not contain per-event local ingestion timestamps needed to reconstruct live wall-clock staleness without lookahead.

The new replay context feature is excluded from model training and ignored for old artifact feature schemas. This keeps existing model scoring compatible while making the field available to replay policy/context audits and future strict replay freshness gates.

## Scoreboard

`docs/model_scoreboard.md` was updated for this Research Alpha boundary.

## Next Step

Run an actual strict replay freshness gate using the now-replayable chain-lag context, preserving 10% sizing and requiring validation/final/walk-forward/stress/paired-delta gates before any promotion beyond Research Alpha.
