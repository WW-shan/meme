# Queued-Only Freshness Shadow

Date: 2026-05-31

## Outcome

Outcome tier: small-sample `Research Alpha` diagnostic, but `Rejected` for split-stable shadow promotion.

No live switch. No `.env`, model artifact, threshold, sizing, buy/sell logic, bot process, collector process, runtime enablement, or restart changed.

This boundary fixes an important attribution mismatch in the prior signal-level freshness check. A runtime freshness abstention gate would only block signals the baseline was going to buy (`queued`), not signals already rejected by the entry model. The previous mixed `queued + rejected` signal-level check was still useful as a broad opportunity-risk warning, but it over-penalized a pure abstention gate by counting rejected opportunities that the current live bot would not have bought anyway.

## Experiments

Small-support queued-only shadow:

```bash
venv/bin/python scripts/probe_signal_freshness_shadow.py \
  --since '2026-05-19 04:02:23' \
  --decision queued \
  --recent-lifecycle-files 160 \
  --min-candidates 5 \
  --min-selected 2 \
  --max-opportunity-misses 0 \
  --max-candidate-sample 0 \
  --output-json data/replay_reports/signal_freshness_queued_only_shadow_20260531_small_support.json \
  --output-md data/replay_reports/signal_freshness_queued_only_shadow_20260531_small_support.md \
  --force
```

Split-stability queued-only shadow:

```bash
venv/bin/python scripts/probe_signal_freshness_shadow.py \
  --since '2026-05-19 04:02:23' \
  --decision queued \
  --recent-lifecycle-files 160 \
  --split-stability \
  --min-candidates 30 \
  --min-selected 2 \
  --min-split-candidates 5 \
  --min-split-selected 1 \
  --max-opportunity-misses 0 \
  --max-candidate-sample 0 \
  --output-json data/replay_reports/signal_freshness_queued_only_shadow_20260531_after_conservative_proxy.json \
  --output-md data/replay_reports/signal_freshness_queued_only_shadow_20260531_after_conservative_proxy.md \
  --force
```

## Results

Both reports saw the same queued freshness population:

- signal decisions: `80`
- per-token candidates: `75`
- queued freshness/path-evaluable candidates: `5`
- missing paths: `0`
- classes: `flat_timeout=2`, `stop_first=2`, `slow_runner=1`

The selected queued-only rule was:

- `lifecycle_status_chain_lag_seconds >= 18.403747081756592`

Small-support report:

- outcome tier: `Research Alpha`
- decision: `research_alpha_signal_freshness_shadow_candidate`
- selected `4`
- correct skips: `4`
- opportunity misses: `0`
- selected classes: `flat_timeout=2`, `stop_first=2`
- selected symbols: repeated `帕鲁`, `四川话`, `长涨`

Split-stability report:

- outcome tier: `Rejected`
- decision: `insufficient_signal_freshness_split_support`
- reason: only `5` queued freshness candidates exist, below the configured `30` candidate gate.
- the same selected rule had all-split `4/4` correct skips and `0` opportunity misses, but validation selected `0`, so it cannot become stable shadow evidence.

## Interpretation

This improves the freshness branch in one specific way: when scoped to baseline queued signals, the high-chain-lag freshness rule no longer shows the broad opportunity-miss problem seen in the mixed queued/rejected signal-level report.

It still cannot be promoted:

- Only `5` queued freshness candidates have signal-level freshness fields and path labels.
- Split-stability support is below gate.
- The accepted-trade proxy remains train top-loss dependent.
- No replay drawdown, walk-forward, stress, or paired-delta evidence exists.

## Decision

Keep execution freshness on the active watchlist as `Research Alpha`.

Do not hard-code the threshold. Do not switch live. The next useful step is to keep collecting queued freshness shadow rows, or build replay-compatible freshness instrumentation that lets this rule family be tested against strict replay metrics.

`docs/model_scoreboard.md` was updated because this boundary changes the signal-level interpretation: mixed queued/rejected freshness still rejects live promotion, but queued-only freshness is no longer contradicted by opportunity misses; it is blocked by insufficient support.
