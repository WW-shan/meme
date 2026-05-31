# Slow-Runner Live-Support Refresh

Date: 2026-05-31

## Outcome

Outcome tier: `Research Alpha`.

No live switch. No `.env`, model artifact, threshold, sizing, buy/sell logic, bot process, collector process, runtime enablement, or restart changed.

The latest rejected-signal population now has stronger slow-runner support than the prior 2026-05-30 refresh, but this is still not `Shadow Candidate` evidence. It strengthens the existing runner-retention alpha record and justifies keeping the direction alive, while avoiding another replay rerun of the same `volceil020` preserve-base utility grid.

## Live Attribution

Artifact:

- `data/replay_reports/live_trade_attribution_20260531_after_quick_profit_support_reject_full.json`
- `data/replay_reports/live_trade_attribution_20260531_after_quick_profit_support_reject_full.md`

Command:

```bash
venv/bin/python scripts/probe_live_trade_attribution.py \
  --since '2026-05-31 00:19:40' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --recent-lifecycle-files 64 \
  --output-json data/replay_reports/live_trade_attribution_20260531_after_quick_profit_support_reject_full.json \
  --output-md data/replay_reports/live_trade_attribution_20260531_after_quick_profit_support_reject_full.md \
  --max-trade-sample 0 \
  --max-candidate-sample 0 \
  --force
```

Result:

- Closed trades: `1`
- Closed-trade net profit: `-0.00005421706409925337` BNB
- Failure label: `dead_flow_timeout`
- Signal decisions: `11295`
- Per-token rejected candidates: `801`
- Barrier classes: `fast_profit=25`, `fast_profit_then_collapse=40`, `flat_timeout=551`, `slow_runner=17`, `stop_first=168`
- Recommended policies: `conditional_slow_hold=17`, `quick_take_profit=65`, `skip=719`

## Label Support

Artifact:

- `data/replay_reports/runner_retention_label_support_20260531_after_quick_profit_support_reject_full.json`

Command:

```bash
venv/bin/python scripts/probe_runner_retention_label_support.py \
  --model-dir data/models/20260519_v95_v84_selective_nearmiss_gate \
  --lifecycle-dir data/training \
  --live-attribution data/replay_reports/live_trade_attribution_20260531_after_quick_profit_support_reject_full.json \
  --output data/replay_reports/runner_retention_label_support_20260531_after_quick_profit_support_reject_full.json \
  --force \
  --max-lifecycle-files 12 \
  --include-shadow-score-rejects \
  --shadow-min-prob 0.94 \
  --shadow-max-entry-score 35 \
  --shadow-min-entry-volume-30s 1.25 \
  --shadow-min-entry-price-volatility 0.08 \
  --shadow-max-age-seconds 300 \
  --group-bucket-seconds 30 \
  --horizon-seconds 600 \
  --quick-profit-seconds 25 \
  --slow-min-plus25-seconds 180 \
  --min-train-positives 3 \
  --min-validation-positives 3 \
  --min-final-positives 3 \
  --min-live-positives 17
```

Support gate:

- Offline status: `PASS_OFFLINE_SUPPORT`
- Live positives: `17`, exactly meeting the raised `min_live_positives=17` gate
- Train positives / tokens: `354 / 124`
- Validation positives / tokens: `33 / 15`
- Final positives / tokens: `112 / 46`
- Split positive rates remain small: validation `0.2219%`, final `0.3134%`

## Interpretation

This is useful alpha evidence, but not a reason to rerun or promote the old replay grid:

- The old `volceil020` preserve-base runner-retention replay already produced `Research Alpha`, not shadow/live. It improved validation/final profit and stress but failed shadow promotion on win-rate/drawdown guardrails, paired-delta uncertainty, and top-winner dependency.
- The new live count is an experiment-justification signal. The strict replay itself is offline and would not materially change just because the live support count increased from `7` to `17`.
- The latest quick-profit support pool was noisy, so broad rejected-candidate expansion remains dangerous.
- The only new closed real trade in the same window was a `dead_flow_timeout` loss, so the next higher-priority structural live-derived direction is conditional dead-flow exit / entry abstention or richer freshness live-shadow evidence, not another runner-retention parameter sweep.

Claude analysis was attempted for a second view, but the external wrapper returned a temporary `503 No available accounts` error. Because this boundary records read-only evidence only and does not change runtime/code, it was closed with local Codex review and no live promotion.

## Decision

Keep runner-retention / missed slow-runner as `Research Alpha`.

Do not switch live. Do not promote to shadow from this evidence alone. Do not rerun the same `volceil020` utility/volatility grid as a parameter sweep.

The direction can still be useful later if a structurally different narrow selector is available, such as a slow-runner clean detector with source-window stability and replay-integrated paired delta. Until then, prioritize dead-flow timeout / freshness / live-shadow evidence because those are closer to the latest accepted-trade failure family.

## Scoreboard

`docs/model_scoreboard.md` was updated because this boundary changes the current slow-runner support interpretation: stronger live support, still `Research Alpha`, no shadow/live promotion.
