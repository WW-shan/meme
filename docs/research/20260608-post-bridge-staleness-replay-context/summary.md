# 2026-06-08 Post-Bridge Staleness Replay Context Audit

## Question

Can the post-bridge split-stable freshness rule `lifecycle_status_staleness_seconds >= 0.015399` be computed from strict validation/final replay samples and replay trade-log context under the current live-sized 10 percent replay assumptions?

This follows the same active no-switch CCG round as the post-bridge freshness refresh. No new SmartSearch Deep Research was needed because this is a replay-surface audit of an already selected freshness rule, not a new method search.

## Implementation

Added reusable read-only tooling:

- `scripts/probe_execution_freshness_replay_context.py`
- `tests/model/test_execution_freshness_replay_context_cli.py`

The CLI:

- loads validation/final replay samples through the existing model replay split helpers;
- runs baseline strict replay with trade logs at `position_fraction=0.1`, `max_position_fraction=0.1`, `max_open_positions=8`, `fixed_stake_bnb=None`, and `skip_all_in_replay=True`;
- checks whether required freshness rule inputs are available in replay samples and replay trade-log entry context;
- writes only under `data/replay_reports`;
- marks the report as read-only and not live-switch evidence.

Command:

```bash
PYTHON_DOTENV_DISABLED=true venv/bin/python scripts/probe_execution_freshness_replay_context.py \
  --rule-field lifecycle_status_staleness_seconds \
  --rule-threshold 0.015399 \
  --output-json data/replay_reports/execution_freshness_replay_context_audit_20260608_post_bridge_staleness_context.json \
  --output-md data/replay_reports/execution_freshness_replay_context_audit_20260608_post_bridge_staleness_context.md
```

## Reports

- `data/replay_reports/execution_freshness_replay_context_audit_20260608_post_bridge_staleness_context.json`
- `data/replay_reports/execution_freshness_replay_context_audit_20260608_post_bridge_staleness_context.md`

Result:

- Outcome tier: `Rejected`
- Decision: `rejected_strict_replay_context_missing`
- Live switch evidence: `false`
- Runtime behavior changed: `false`

Coverage:

| Split | Samples | Baseline trades | Sample staleness coverage | Trade-context staleness coverage |
|---|---:|---:|---|---|
| Validation | `140332` | `23` | `missing`, `0.0` coverage | `missing`, `0.0` coverage |
| Final | `210376` | `24` | `missing`, `0.0` coverage | `missing`, `0.0` coverage |

The baseline replay metrics remained the expected current strict baseline for this model path:

- Validation: `0.012252343033424175` BNB net profit, `0.7391304347826086` win rate.
- Final: `0.0020282580548887895` BNB net profit, `0.5416666666666666` win rate.

## Decision

No live switch, no `.env` change, no model artifact change, no threshold/sizing change, no buy/sell logic change, no bot/collector process change, and no runtime router enablement.

The selected staleness rule remains useful `Research Alpha` evidence from rejected live signals, but it is not strict-replayable today. Both replay samples and replay trade logs lack `lifecycle_status_staleness_seconds`, so a strict replay acceptance gate cannot apply the rule without first propagating decision-time lifecycle freshness fields into the replay sample/trade context.

This does not reject execution freshness as a research direction. It rejects promoting the current post-bridge staleness rule through strict replay on the existing replay surface.

## Next Direction

The next falsifiable step is replay-surface propagation: add or locate the decision-time lifecycle freshness fields in replay sample construction, then rerun this audit. If validation/final samples gain coverage, run a strict replay gate. If the fields cannot be reconstructed from lifecycle history without lookahead or timestamp ambiguity, record that blocker and pivot back to strict-replayable accepted-action router shadow evidence or continued live shadow collection.

`docs/model_scoreboard.md` was updated because this boundary changes the freshness next step from "audit replay compatibility" to "propagate missing decision-time lifecycle freshness fields before strict replay can test the rule."
