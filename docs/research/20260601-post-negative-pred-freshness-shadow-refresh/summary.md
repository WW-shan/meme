# Post Negative-Pred Freshness Shadow Refresh

Date: 2026-06-01

## Outcome

Outcome tier: `Rejected`.

No live switch. No `.env`, model artifact, threshold, sizing, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

This boundary closes the immediate post negative-PredReturn quick-profit direction selection check. The latest live slice did not add runner, quick-profit, queued/opened, or freshness-shadow support, so the next meaningful work remains replay-compatible execution-freshness integration rather than another rejected-signal micro-sweep.

## Direction Review

Ranked options after the rejected negative-PredReturn ultrashort quick-profit replay:

1. Replay-compatible execution freshness / accepted-loss abstention.
   - Best evidence: repeated accepted live losses remain selected by the chain-lag / signal-context freshness proxy, and paired-delta evidence is still `Research Alpha`.
   - Current blocker: it is not strict replay-equivalent yet. It needs deployable signal-time feature parity, walk-forward, stress, drawdown, and selected-trade-delta context before any shadow or live promotion.
2. Queued/opened signal-freshness shadow accumulation.
   - Best evidence: it is the closest live-equivalent read-only path for freshness.
   - This round's smallest falsifiable check rejected it because the post-02:15 window had only six rejected candidates and no queued/opened support.
3. Conditional exit / early-profit harvest.
   - Best evidence: prior single-token fast-profit-then-collapse watchpoint `绷`.
   - Current blocker: the strict negative-PredReturn ultrashort replay expanded trades massively and failed final confirmation; the latest window added no new fast-profit support.
4. Runner-retention preserve-base / direct utility / volceil families.
   - Already rejected or left only as older `Research Alpha`; do not continue these parameter or utility-label micro-sweeps without new population evidence.

## Commands

```bash
venv/bin/python scripts/probe_live_trade_attribution.py \
  --since '2026-06-01 02:15:00' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --output-json data/replay_reports/live_trade_attribution_20260601_after_negative_pred_reject.json \
  --output-md data/replay_reports/live_trade_attribution_20260601_after_negative_pred_reject.md \
  --max-trade-sample 40 \
  --max-candidate-sample 160 \
  --force
```

```bash
venv/bin/python scripts/probe_signal_freshness_shadow.py \
  --since '2026-06-01 02:15:00' \
  --recent-lifecycle-files 128 \
  --output-json data/replay_reports/signal_freshness_shadow_20260601_after_negative_pred_reject.json \
  --output-md data/replay_reports/signal_freshness_shadow_20260601_after_negative_pred_reject.md \
  --max-candidate-sample 160 \
  --split-stability \
  --force
```

## Results

Fresh live attribution:

- Closed trades: `0`.
- Rejected path candidates: `6`.
- Barrier classes: `flat_timeout=5`, `stop_first=1`.
- Policy hints: `skip=6`.
- Ranked directions: `rejected_flat_timeout_skip_replay` count `5`; `rejected_stop_first_skip_replay` count `1`; neither meets same-shape support.
- Decision: `NO_GO_FOR_LIVE_SWITCH`.

Signal-freshness split shadow:

- Outcome tier: `Rejected`.
- Decision: `insufficient_signal_freshness_split_support`.
- Candidate counts: `44` signal decisions, `6` per-token candidates, `6` freshness candidates, `0` missing paths.
- Decisions represented: `6` rejected, `0` queued.
- Barrier classes: `flat_timeout=5`, `stop_first=1`.
- Stable rules: `0`.
- Train-eligible rules: `0/9`.
- All-window selected diagnostic rule: `lifecycle_status_has_chain_update == true`, selecting all `6` correct skips. This is not actionable because it is broad, below minimum support, and has no queued/opened or opportunity coverage.

Watchpoints:

- `币如人生`: `stop_first`, `prob=0.9653596653034184`, `PredReturn=-7.305174956388786`, MFE `+5.159202301235033%`, MAE `-21.342856536746936%`.
- `BNSTOCK`: `flat_timeout`, `prob=0.9743275645885954`, `PredReturn=2.5947900644070163`, MFE `+9.52804171920949%`, MAE `+2.5013960139135705%`.

## Decision

Do not promote or change live runtime.

This does not change the scoreboard conclusion: execution freshness remains `Research Alpha` from prior accepted-trade paired-delta evidence, while the latest post-negative-PredReturn live slice is a thin negative refresh. `docs/model_scoreboard.md` was intentionally not updated because there is no model status promotion, no live-risk interpretation change, and no accepted baseline change.

Next work should either:

- make the execution-freshness proxy replay-compatible with signal-time feature parity and strict replay gates, or
- keep collecting queued/opened freshness shadow evidence until support is materially larger.
