# Conditional Exit Flow-State Research Summary

Generated: 2026-05-21T15:30:36Z

## Contract

- Active live model remains `data/models/20260519_v95_v84_selective_nearmiss_gate`.
- Live sizing remains 10% position fraction with max 8 open positions.
- This research is read-only diagnostic evidence, not live-switch evidence.
- No change is justified for `.env`, `data/models/**`, `docs/goals/**`, or live runtime thresholds from this node.

## Current State

Since the v95 restart anchor `2026-05-19 04:02:23`, live trading has closed 18 real trades:

- Net profit: `-0.001256566335` BNB.
- Wins/losses: `2` wins and `16` losses.
- Close reasons: `STOP_LOSS=4`, `TIME_EXIT=7`, `PPO_SELL100=5`, `ENTRY_SLIPPAGE_PROTECTION=2`.
- Failure labels from `live_attribution.json`: `dead_flow_timeout=7`, `mfe_then_giveback=3`, `entry_slippage_failure=2`, `stop_first_after_entry=1`, `unprofitable_other=3`, `profitable_exit=2`.
- Near-threshold split: `8` trades were `near_threshold_like=true` and they were mostly `dead_flow_timeout=6` plus `unprofitable_other=2`; the `10` primary trades contained all `3` `mfe_then_giveback` cases and both profitable exits.

The live failures are not one shape. The two largest actionable groups are:

- `dead_flow_timeout`: no meaningful post-entry MFE, often with heavy pre-signal sell pressure.
- `mfe_then_giveback`: reached meaningful MFE after entry, then collapsed into a loss. Current live examples are `FENGSHUI`, `CMC`, and `AUCA`.

## External Evidence

The fetched triple-barrier/meta-labeling sources support path-dependent labels. The useful concept for this repo is not a fixed future-return label, but a first-touch path with profit-taking, stop-loss, and vertical time barriers. Local evidence:

- `04-fetch-hudsonthames.md` explains that triple-barrier labeling uses take-profit, stop-loss, and vertical duration barriers, and labels a return path rather than the next directional move.
- `05-fetch-mlfinpy-labeling.md` defines the upper, lower, and vertical barriers, and documents profit-taking and stop-loss multiples as first-touch event inputs.

The MFE/MAE source supports the diagnostic shape used here:

- `06-fetch-mae-mfe.md` defines MAE as the worst move against the entry before close and MFE as the best move in favor before close.
- The same source frames MFE as useful for profit-target and trailing-exit review, while MAE supports stop and drawdown review.

The pump-and-dump microstructure sources support using high-frequency volume and flow, but also warn against overconfidence:

- `07-search-pumpdump.json` and `09-fetch-pumpdump-repec.md` highlight class imbalance, 30-second chunks, and moving-window features for crypto pump-and-dump detection.
- `08-fetch-pumpdump-arxiv.md` supports combining trade and order-book data, and shows useful signals can emerge only seconds before a pump. This fits the live slippage and late-pump problem, but it does not by itself justify a live rule.

Provider gaps:

- `02-zhipu.json` failed because `ZHIPU_API_KEY` is not configured.
- `03-exa.json` failed because `EXA_API_KEY` is not configured.

## Support Gate

The decisive replay support gate is in `10-exit-state-attribution.json` and `11-exit-state-attribution.md`.

| Bucket | Train positives | Validation positives | Final positives | Live positives | Decision |
|---|---:|---:|---:|---:|---|
| `post_target_collapse_or_live_mfe_giveback` | 5 | 0 | 4 | 3 | NO-GO |
| `dead_flow_timeout` | n/a | n/a | n/a | 7 | NO-GO |
| `entry_slippage_failure` | n/a | n/a | n/a | 2 | NO-GO |

The most tempting direction is post-target conditional exit, because final has 4 collapse examples and live has 3 similar MFE givebacks. It still fails the strict gate because validation has `0` post-target collapse examples. A deployable rule selected now would be fit to train/final/live evidence without validation support.

## Prior Rejections To Avoid Repeating

The scoreboard already rejects nearby static or blanket directions:

- Broad path-state meta gate: no usable middle band.
- Flow-enhanced path-state meta gate: no-op or no-trade behavior.
- Ultra-short runner quick-profit overlay: headline improvements did not survive final, drawdown, walk-forward, and stress gates.
- Dead-bounce entry veto: no actionable reject count.
- Fast and delayed blanket profit-lock: cut too much durable edge or failed stress.
- Conditional low-volume rescue plus pump-risk veto: reduced edge without robustly fixing slow-decay losses.
- Flow activation/dead-flow hard gate: over-reduced trades and profit.

## Decision

Do not switch live config or model artifacts from this research node.

The smallest falsifiable next node is a default-off replay-only feasibility probe that refuses to select a conditional exit unless a candidate bucket has enough support in validation, final, and live. Current evidence fails that gate for post-target exits, so the next profitable move is not a live exit rule. It is either:

1. Accumulate more live labels until validation-equivalent support exists, or
2. Build a replay-only support-gated probe that can say "no candidate" cleanly when support is missing.

A reproducible version of that probe now exists at `scripts/probe_conditional_exit_feasibility.py`, and it regenerates `10-exit-state-attribution.json` / `11-exit-state-attribution.md` from the frozen replay reports plus `live_attribution.json`.

## Acceptance Criteria For Any Next Candidate

A candidate can advance beyond diagnostic status only if all are true:

- Validation positives for the targeted bucket are at least `3`.
- Final positives for the targeted bucket are at least `3`.
- Live positives for the targeted bucket are at least `3`.
- Every decision feature is observable strictly before the exit decision time; no realized post-exit MFE or future bars are allowed in the feature set.
- The replay candidate is default-off and preserves 10% sizing.
- It strictly beats the current accepted v95 baseline on validation, sealed final, walk-forward, harsh stress, drawdown, and trade-count discipline.
- It does not touch `.env`, `data/models/**`, or `docs/goals/**` before passing those replay gates.

Current status: `NO_GO_FOR_LIVE_RULE`.
