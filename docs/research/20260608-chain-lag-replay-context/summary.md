# Chain-Lag Replay Context Bridge

Date: 2026-06-08

## Decision

Outcome: Rejected semantic replay audit. This is not a Research Alpha promotion, not a Shadow Candidate, and not live-switch evidence.

The selected execution-freshness proxy field `lifecycle_status_chain_lag_seconds` is available in both strict replay samples and strict replay trade-log entry context, but the selected rule is degenerate under the current `trade_event` strict replay anchor. All replayed values are `0.0`, so `lifecycle_status_chain_lag_seconds >= 6.109405994415283` selects no validation or final samples and no replay trade-context rows.

This corrects the earlier coverage-only interpretation of the same report. Coverage alone is not enough for strict replayability when the selected numeric rule has no non-zero or threshold-matching support.

## Evidence

- Report: `data/replay_reports/execution_freshness_replay_context_audit_20260608_chain_lag_replay_context.json`
- Markdown: `data/replay_reports/execution_freshness_replay_context_audit_20260608_chain_lag_replay_context.md`
- Selected proxy rule checked for replayability: `lifecycle_status_chain_lag_seconds >= 6.109405994415283`
- Decision: `rejected_strict_replay_context_degenerate`
- Runtime behavior changed: `false`
- Live switch evidence: `false`

Validation coverage:

- Samples: `140332`
- Baseline replay trades: `23`
- Sample `lifecycle_status_chain_lag_seconds`: `140332/140332`, coverage `1.0`
- Trade-context `lifecycle_status_chain_lag_seconds`: `23/23`, coverage `1.0`
- Selected rule sample matches: `0`
- Selected rule trade-context matches: `0`
- Selected rule value summary: min `0.0`, p50 `0.0`, p95 `0.0`, max `0.0`, unique values `1`
- Baseline net profit BNB: `0.012252343033424175`
- Baseline win rate: `0.7391304347826086`

Final coverage:

- Samples: `212135`
- Baseline replay trades: `24`
- Sample `lifecycle_status_chain_lag_seconds`: `212135/212135`, coverage `1.0`
- Trade-context `lifecycle_status_chain_lag_seconds`: `24/24`, coverage `1.0`
- Selected rule sample matches: `0`
- Selected rule trade-context matches: `0`
- Selected rule value summary: min `0.0`, p50 `0.0`, p95 `0.0`, max `0.0`, unique values `1`
- Baseline net profit BNB: `0.0020282580548887895`
- Baseline win rate: `0.5416666666666666`

## Implementation Notes

The bridge deliberately uses decision-time chain lag derived from observed historical trade timestamps at or before `sample_time`. Under strict `trade_event` replay sampling, however, `sample_time` is aligned to the triggering historical trade timestamp. Including rows with `timestamp <= sample_time` therefore includes that triggering event and collapses the computed chain lag to `0.0`.

The new replay context feature is excluded from model training and ignored for old artifact feature schemas. This keeps existing model scoring compatible while making the field available to replay policy/context audits and future strict replay freshness gates.

The audit tooling now records selected-rule match counts and numeric value summaries, and rejects fields that are present but semantically degenerate for the selected threshold.

## Scoreboard

`docs/model_scoreboard.md` was updated for this corrected rejection. No model score, live-risk interpretation, or runtime direction was promoted by this round.

## Next Step

Do not run a strict chain-lag freshness gate from this field as currently anchored. The next viable path is either a non-degenerate decision-time freshness proxy or a replay sample anchor that preserves the pre-decision lag instead of collapsing it to the triggering trade event.
