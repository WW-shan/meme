# Stop-Loss Re-Entry And Runner-Retention Research

Date: 2026-05-19

## Live Trigger

Current live model: `data/models/20260519_v95_v84_selective_nearmiss_gate`.

Current live state at 2026-05-19 04:15 CST:

- `./tools/memectl bot status`: running, PID `2422`.
- `./tools/memectl collector status`: running, PID `43888`.
- `data/bot_state.json`: zero open positions, balance `0.005079303120051795`.
- `.env`: `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, `FIXED_STAKE_BNB=`.
- No post-v95 live OPEN/CLOSE rows in `data/paper_trades.jsonl`.
- No traceback or buy/sell error in the inspected `logs/bot.log` tail.

The newest v95 live near-miss is `SZN`:

- 15 `SIGNAL_DECISION` audit rows since the v95 restart.
- Rejection reasons: 7 `buy_model_reject`, 4 `pred_return_below_min`, 2 `entry_volume_30s_below_min`, 2 `near_threshold_pred_return_below_min`.
- At 04:11:18, `SZN` had `prob=0.9890`, `pred_return=25.04`, `volume_30s=3.509`, and `price_volatility=0.320`, but was rejected by the pred-return gate.
- From that rejected point, lifecycle path reached `+25%` in about 78s, `+60%` in about 81s, and MFE about `+157.9%`, but later hit `-18%` after about 102s and had deep drawdown later.

This supports a path-dependent problem: some missed runners have real upside after a rejected or stopped point, but the same cohort can reverse sharply. The next experiment should not lower global thresholds or simply hold every position longer.

Recent live trade evidence from the previous attribution pass:

- `币安小子` first token: live STOP_LOSS was followed by a post-exit path of `+25%` in about 19s, `+60%` in about 54s, and MFE about `+141%`.
- `何赵`: PPO exit was followed by `+25%` in about 31s and MFE about `+58%`; this suggests possible early runner exit.
- `WAGMI`: STOP_LOSS had only a short bounce and no meaningful post-exit runner; this remains the counterexample.
- `BISMILLAH`: had rebound potential but also immediate deep whipsaw, so blind re-entry is unsafe.

## Prior Failed Directions To Avoid

Do not repeat these without a structural change:

- Global threshold lowering.
- Volume relaxation.
- Raw runner-probability gate.
- Token balancing alone.
- Blanket partial exit.
- Simply holding all positions longer.

The new direction must be conditional and path-aware: it should target whipsaw/rebound and runner-retention cases while rejecting WAGMI/BISMILLAH-style collapses.

## SmartSearch Deep Research Evidence

Research plan:

```bash
smart-search deep "For ultra-short-horizon crypto/memecoin trading, how should a strategy distinguish stop-loss collapses from stop-loss whipsaws that later become runners, and what evidence-backed designs exist for re-entry gates, conditional stop-loss debounce, or runner-retention exits without increasing position size? Focus on path-dependent labels, meta-labeling, purged time-series validation, and pump-and-dump microstructure." --budget deep --format json --output docs/research/20260519-stoploss-reentry-runner-retention/plan.json
```

Executed evidence commands:

- `smart-search search "stop loss whipsaw re-entry gate crypto trading confirmation volume volatility" --validation balanced --extra-sources 3 --format json --output docs/research/20260519-stoploss-reentry-runner-retention/01-search-reentry.json`
- `smart-search search "triple barrier meta labeling financial machine learning path dependent labels stop loss take profit" --validation balanced --extra-sources 3 --format json --output docs/research/20260519-stoploss-reentry-runner-retention/02-search-triple-barrier.json`
- `smart-search search "memecoin pump dump microstructure early volume concentration wash trading liquidity price inflation research" --validation balanced --extra-sources 3 --format json --output docs/research/20260519-stoploss-reentry-runner-retention/03-search-memecoin-microstructure.json`
- `smart-search fetch "https://www.okx.com/learn/what-is-a-whipsaw-crypto-trading" --format markdown --output docs/research/20260519-stoploss-reentry-runner-retention/04-fetch-okx-whipsaw.md`
- `smart-search fetch "https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/" --format markdown --output docs/research/20260519-stoploss-reentry-runner-retention/05-fetch-hudson-metalabel.md`
- `smart-search fetch "https://mlfinpy.readthedocs.io/en/latest/Labelling.html" --format markdown --output docs/research/20260519-stoploss-reentry-runner-retention/06-fetch-mlfinpy-labeling.md`
- `smart-search fetch "https://blog.quantinsti.com/cross-validation-embargo-purging-combinatorial/" --format markdown --output docs/research/20260519-stoploss-reentry-runner-retention/07-fetch-quantinsti-purged-cv.md`
- `smart-search fetch "https://arxiv.org/html/2507.01963v2" --format markdown --output docs/research/20260519-stoploss-reentry-runner-retention/08-fetch-midsummer-meme.md`
- `smart-search fetch "https://arxiv.org/html/2504.15790v1" --format markdown --output docs/research/20260519-stoploss-reentry-runner-retention/09-fetch-pump-microstructure.md`

Evidence conclusions:

- OKX describes whipsaw as a sudden reversal in high volatility and notes that volume indicators can help identify or react to whipsaw conditions. This supports using confirmation gates instead of immediate re-entry.
- Hudson & Thames reports that event-based sampling, triple-barrier labels, and meta-labeling improved strategy performance in their research setting. This supports a second-stage take/pass model on top of the primary signal, not a global threshold change.
- mlfinpy documents triple-barrier and meta-labeling as path-dependent labeling alternatives to fixed-horizon labels. This supports labels that know whether `+25%`, `+60%`, `-18%`, or `-25%` happens first.
- QuantInsti's purging/embargo discussion supports leakage control for overlapping path-dependent trade labels. This matters because the proposed labels use future path windows.
- The meme-coin manipulation paper reports that many high-return meme coins show artificial-growth indicators. This argues for extra collapse/manipulation features rather than indiscriminate runner chasing.
- The pump-and-dump microstructure paper describes rapid pump/collapse dynamics and staged liquidation scenarios. This supports studying conditional runner retention and fast profit capture, but local v94 results already rejected blanket partial exits.

## Hypothesis

Because live `币安小子` and `何赵` show profitable post-exit or post-rejection runner paths, while `WAGMI`, `BISMILLAH`, and late `SZN` show dangerous whipsaw/collapse risk, test a conditional path-aware re-entry or runner-retention gate rather than a global threshold change, volume relaxation, or blanket longer hold.

Expected improvement:

- Recover a subset of missed post-stop/post-reject runners.
- Keep live sizing at 10%.
- Do not increase concurrent exposure to the same token.
- Improve net return or worst walk-forward segment versus the accepted best baseline after strict live-sized replay.

Falsification rules:

- Reject if max drawdown worsens materially.
- Reject if walk-forward worst net return worsens versus the current best baseline.
- Reject if selected gains are mostly from a tiny number of outliers.
- Reject if it mainly selects paths that hit `-18%` before any realistic re-entry confirmation.
- Reject if it requires increasing position size, fixed stake, or concurrent duplicate exposure.

## Next Experiment

Run a minimal offline probe before touching live code:

1. Build a read-only attribution/probe over `data/paper_trades.jsonl`, `data/signal_audit.jsonl`, and lifecycle data.
2. Candidate trigger families:
   - Post-STOP_LOSS re-entry only after price reclaims `+25%` from exit within a short window and volume/buyer activity confirms.
   - PPO early-exit retention only when post-exit path quickly reclaims momentum without first hitting a fresh collapse barrier.
   - Late high-probability rejection rescue only when triple-barrier ordering is favorable and a fast-profit/trailing exit can realize gains before collapse.
3. Compare selected candidates against collapse controls: `WAGMI`, `BISMILLAH`, and late `SZN`.
4. If and only if the probe is promising, write an implementation plan and use subagents for replay-engine and label/tooling work.

