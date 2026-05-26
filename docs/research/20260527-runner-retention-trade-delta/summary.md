# Runner-Retention Trade Delta Diagnostic

## Question

Why does the runner-retention candidate gate improve validation net profit but lose win rate and fail final/stress, and which added or removed trades explain that gap?

## Reused research

This round reuses the committed runner-retention / conditional slow-hold research from `docs/research/20260526-time-to-event-exit-dead-flow/summary.md`.

New angle: compare baseline vs candidate trade logs directly, using decision-time sample features to explain added, removed, and common trades.

## Tooling

- `src/pipeline/replay_trade_delta_attribution.py`
- `tests/model/test_replay_trade_delta_attribution.py`
- `scripts/run_runner_retention_candidate_gate_replay.py --write-selected-trade-delta`

## Experiment

Command:

```bash
python scripts/run_runner_retention_candidate_gate_replay.py --write-selected-trade-delta --output data/replay_reports/runner_retention_candidate_gate_replay_20260527_trade_delta.json --force
```

Key replay result:

- validation baseline net profit `0.021094872145773796`
- best validation candidate net profit `0.023015195974737265`
- final baseline net profit `0.0051745153254758`
- final candidate net profit `0.005664450310188439`
- decision: `reject`

## Delta findings

- Validation added trades were mixed: `15` added trades with `8` wins and `7` losses.
- Final added trades were toxic overall: `7` added trades with `1` win and `6` losses.
- Final removed trades were also mixed but removed one large winner and several losers; the net profit bump was not enough to survive win-rate and stress gates.
- Common trades were unchanged in both validation and final, so the failure came from the added/removed boundary rather than the shared basket.

Most useful feature differences:

- Added bad-loss trades skewed toward higher `buy_pressure`, lower `buyer_concentration`, fewer `unique_sellers`, and much higher `retail_entry_rate_ratio_30s` on validation.
- Final added stop-loss trades skewed toward higher `early_buy_volume`, higher `early_volume_ratio`, higher `max_holder_ratio`, and higher `max_burst_volume`.
- Removed baseline stop-loss trades in both validation and final were the ones with stronger buy-activity slope / volume structure, which means the current gate is still not separating the right runners from the wrong ones.

## Decision

Reject as live evidence. Keep the trade-delta tool as reusable shadow-only attribution.

## Next direction

Use the trade-delta features to design a narrower second-stage filter for runner-retention, rather than widening the current gate or simply lowering thresholds.
