# Replay-Compatible Execution Freshness Probe

Generated: 2026-05-31

## Contract

- Active live model remains `data/models/20260519_v95_v84_selective_nearmiss_gate`.
- Live sizing remains 10% position fraction; no fixed stake was introduced.
- This node is read-only research evidence, not live-switch evidence.
- No `.env`, `.env.example`, model artifact, threshold, bot process, collector process, or runtime behavior changed.

## Trigger

The latest post-skip boundary closed the prior-skip follow-up direction as unsupported. The strongest remaining live-derived family is execution freshness:

- accepted-trade proxy has `52` paired real trades since `2026-05-19 04:02:23`;
- signal-level freshness shadow has hundreds of rejected/queued candidates after instrumentation;
- recent live losses (`币安盲盒`, repeated `帕鲁`, `四川话`) sit inside high-chain-lag or high-freshness-risk accepted-trade buckets.

The gap was that prior probes mostly used raw `lifecycle_status_chain_lag_seconds`. This experiment converts decision freshness into market-state-adjusted features instead of hard-coding a lag threshold.

## External Evidence

SmartSearch deep plan and fetched evidence are under `docs/research/20260531-replay-compatible-execution-freshness/evidence/`.

- Moallemi and Saglam's latency-cost model supports combining latency with short-horizon price volatility: latency cost rises with the uncertainty accumulated over the latency interval, not just elapsed time.
- Order-book imbalance and latency papers support using low-latency, decision-time market state as a policy input rather than a delayed post-fill feature.
- Adverse-selection and dynamic slippage/rejection evidence supports treating stale or high-volatility execution states as a utility penalty that must be validated out of sample.

The broad `smart-search search` call failed with an upstream xAI 503, so the evidence set relies on fetched primary/source pages and the offline deep plan rather than broad generated synthesis.

## Implementation

Reusable files:

- `src/pipeline/execution_freshness_abstention_probe.py`
- `scripts/probe_execution_freshness_abstention.py`
- `tests/model/test_execution_freshness_abstention_probe.py`

Changes:

- The accepted-trade proxy can optionally merge same-token queued `SIGNAL_DECISION` context by timestamp tolerance.
- Added decision-time policy fields:
  - `signal_price_volatility`
  - `signal_volume_30s`
  - `freshness_latency_volatility_risk = sqrt(lifecycle_status_chain_lag_seconds) * signal_price_volatility`
  - `freshness_latency_volume_risk = freshness_latency_volatility_risk * log1p(signal_volume_30s)`
- `signal_context_match_seconds` is diagnostic only.
- Existing post-order fields like `entry_fill_lag_seconds` remain diagnostic only.

This keeps the probe generic: train split selects thresholds from observed values; no token, threshold, or live rule is hard-coded.

## Command

```bash
venv/bin/python scripts/probe_execution_freshness_abstention.py \
  --since '2026-05-19 04:02:23' \
  --paper-trades data/paper_trades.jsonl \
  --signal-audit data/signal_audit.jsonl \
  --signal-match-tolerance-seconds 3 \
  --output data/replay_reports/execution_freshness_latency_volatility_probe_20260531_after_post_skip_reject.json \
  --force \
  --max-sample-rows 100
```

## Result

Report:

- `data/replay_reports/execution_freshness_latency_volatility_probe_20260531_after_post_skip_reject.json`

Primary selected proxy:

- outcome tier: `Research Alpha`
- decision: `research_alpha_proxy_requires_replay_and_signal_time_logging`
- paired real trades: `52`
- scanned rules: `248`
- train eligible rules: `150`
- selected rule: `lifecycle_status_chain_lag_seconds >= 1.8176350593566895`
- train selected `16`: `12` losses, `4` winners, delta `+0.0005545021460338318` BNB
- validation selected `3`: `3` losses, `0` winners, delta `+0.00037092635873943236` BNB
- final selected `7`: `6` losses, `1` winner, delta `+0.0002930415534123349` BNB
- final delta without top skipped-loss benefit: `+0.0001291328103940062` BNB

Important secondary signal-context candidate:

- rule: `signal_price_volatility >= 0.25062`
- train selected `20`: `20` losses, `0` winners, delta `+0.0014023322920452908` BNB
- validation selected `2`: `2` losses, `0` winners, delta `+0.00004645563321604892` BNB
- final selected `8`: `8` losses, `0` winners, delta `+0.00037603463581654115` BNB
- final selected symbols include `币安盲盒`, two `帕鲁` losses, and `四川话`

The selected rule remains the broader chain-lag rule because the existing ranking prioritizes validation delta before final delta. The signal-volatility rule is more selective and cleaner in final, but validation support is only two trades. This makes it a stronger replay-compatible feature lead, not a live switch candidate.

## Decision

Outcome tier: `Research Alpha`.

Do not switch live. Do not hard-code either the chain-lag or signal-volatility threshold into runtime. This experiment strengthens the execution-freshness direction because decision-time signal volatility and latency-volatility risk are now available as generic, train-selected policy candidates, and one volatility rule has zero winner skips across train/validation/final in the accepted-trade proxy.

Scoreboard update: completed in `docs/model_scoreboard.md`.

Next direction: promote this from live accepted-trade proxy to replay/paper-compatible evaluation: integrate the signal-context fields into replay selected-trade-delta output or a queued/opened shadow evaluator, then apply uncertainty / top-winner dependency gates before any Shadow Candidate promotion.
