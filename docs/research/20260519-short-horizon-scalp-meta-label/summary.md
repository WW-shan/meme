# Short-Horizon Scalp Meta-Label Research

## Live Trigger

- After the last real v95 trade (`赵长娥`, closed 2026-05-19 19:16), the bot stayed flat but continued rejecting high-probability candidates.
- `data/replay_reports/time_to_barrier_probe_20260519_post_1916_v95.json` found `3364` rejected decisions, deduped to `162` per-token candidates: `11` fast-profit, `21` fast-profit-then-collapse, `2` slow-runner, `25` stop-first, and `103` flat-timeout.
- `data/replay_reports/flow_activation_probe_20260519_post_1916_v95.json` accepted `0/162`; this falsifies a simple flow-only allow gate for the current live window.
- The live problem is therefore narrow: v95 sometimes rejects short-lived +25% opportunities, but those are mixed with many flat/stop-first paths.

## Research Evidence

- SmartSearch plan: `smart-search deep "For ultra-short-horizon meme-coin trading..." --format json --output docs/research/20260519-short-horizon-scalp-meta-label/plan.json`.
- Broad search: `docs/research/20260519-short-horizon-scalp-meta-label/01-search.json`.
- Fetched evidence:
  - Hudson & Thames, `Does Meta Labeling Add to Signal Efficacy?`: meta-labeling is useful only on top of a primary signal and needs contextual features plus out-of-sample testing.
  - mlfinpy labelling docs: triple-barrier labels encode profit, stop, and time barriers; meta-labeling should decide whether to act on a primary model's proposed opportunity.
  - Springer `Algorithmic crypto trading using information-driven bars, triple barrier labeling and deep learning`: crypto experiments showed triple-barrier labels can outperform next-bar labels when transaction costs are included, but parameter sensitivity and cross-regime validation matter.
  - Quantreo meta-labelling article: meta-labeling should filter noisy signals and evaluate precision on unseen data, not create broad new trades.

## Implication For This Repo

- Do not lower global thresholds or relax volume gates; earlier scoreboard entries already rejected those directions.
- Do not deploy a blanket quick-profit rule; the live window has `25` stop-first candidates and `103` flat candidates.
- The smallest falsifiable experiment is a replay-only quick-profit overlay on score-rejected, high-probability candidates, with a short take-profit and short max-hold.
- The overlay must keep `position_fraction=0.1`, preserve v95 primary and near-threshold gates, and be rejected unless validation, final, walk-forward, stress, win rate, drawdown, and bounded trade-count gates beat the current v95 baseline.

## Hypothesis

Because post-19:16 live rejects contain a small pocket of fast +25% moves but no flow-only clean activation, a replay-only primary-score quick-profit overlay may harvest short-lived spikes if it is restricted to high-probability score-near-fail candidates and exits with a dedicated quick take-profit/time stop.

## Falsification

Reject the direction if the selected validation candidate fails final confirmation versus v95, if stress replay worsens, if trade count expands materially, or if the improvement comes from one fragile outlier rather than a bounded set of overlay trades.

## Replay Result

- Report: `data/replay_reports/primary_score_scalp_replay_20260519_v95.json`.
- Decision: reject.
- Validation selected candidate `7`: `min_prob=0.988`, PredReturn `[25,35]`, `volume_30s>=2.0`, `price_volatility>=0.10`, `age<=60s`, `take_profit=35%`, `max_hold=120s`.
- Validation improved from `0.00683256` to `0.00893800` BNB profit, with `9` quick-overlay entries and all strict validation gates passing.
- Sealed final failed. Baseline final was `45` trades, `511.4749%` return, `0.02597936` BNB profit, `80.0000%` win rate, `-8.1825%` max drawdown, `119.7469%` walk-forward worst return, and `274.1801%` harsh-stress worst return. The selected overlay fell to `52` trades, `447.3709%` return, `0.02272332` BNB profit, `76.9231%` win rate, `-8.6427%` max drawdown, `78.4564%` walk-forward worst return, and `209.7333%` harsh-stress worst return.
- Implementation note: the replay-only overlay age gate was tightened after review so missing, malformed, non-finite, negative, or stale age data cannot be treated as fresh.

Conclusion: the short-horizon scalp pocket exists in validation but does not generalize enough for live deployment. Keep the evidence and safety fix; next work should use a learned candidate-level meta-label or conditional-exit model over live path state instead of a simple rule overlay.
