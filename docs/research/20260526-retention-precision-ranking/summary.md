# 2026-05-26 Retention Precision Ranking

## Live Evidence

- Live model: `data/models/20260519_v95_v84_selective_nearmiss_gate`.
- Runtime state during the round: bot and collector running, no open positions, no new closed trades.
- Attribution report: `data/replay_reports/live_trade_attribution_20260526_retention_precision_ranking_round.json`.
- Rejected signal path classes: `slow_runner=8`, `fast_profit=2`, `fast_profit_then_collapse=4`, `flat_timeout=45`, `stop_first=10`.
- Top live-derived direction: `rejected_slow_runner_conditional_slow_hold_replay`.

## Research Evidence

SmartSearch artifacts are in this directory. `xAI Responses` and `Tavily` were available; `ZHIPU_API_KEY` and `EXA_API_KEY` were missing, so those provider outputs are config errors and not used as evidence.

Fetched evidence supports:

- Rare-event prediction needs specialized training and evaluation, not ordinary accuracy on imbalanced data.
- Selective classification / abstention is a better fit than globally widening entry thresholds.
- Conformal/risk-control style thresholding requires monotone risk and calibration data; in this repo, the practical analogue is strict validation/final/walk-forward/stress gates.
- Sequential dependence makes one-shot confidence weaker, so same-shape support and validation stability matter before live use.

## Experiment

Implemented a preserve-base runner-retention replay mode:

- Existing v95 candidates that already pass the base runtime entry stack receive path-state score `1.0`.
- The runner-retention scorer only decides expanded rescue candidates.
- This tests whether slow-runner rescue can add profit without re-screening and damaging baseline primary/near entries.

Code and tests:

- `src/pipeline/runner_retention_replay_gate.py`
- `scripts/run_runner_retention_candidate_gate_replay.py --preserve-base-candidates`
- `tests/model/test_runner_retention_replay_gate.py`

Replay report:

- `data/replay_reports/runner_retention_precision_preserve_base_replay_20260526.json`

## Result

Decision: `reject`.

Best validation candidate:

- Baseline: `32` trades, `415.3104%` return, `0.02109487` BNB profit, `75.00%` win rate, `-9.8821%` max drawdown.
- Candidate: `42` trades, `453.1172%` return, `0.02301520` BNB profit, `69.05%` win rate, `-18.6685%` max drawdown.
- Failed gates: win rate, max drawdown, trade expansion, walk-forward drawdown, stress drawdown.

Final confirmation:

- Baseline: `21` trades, `101.8745%` return, `0.00517452` BNB profit, `52.38%` win rate, `-18.2292%` max drawdown.
- Candidate: `23` trades, `111.5202%` return, `0.00566445` BNB profit, `47.83%` win rate, `-17.9516%` max drawdown.
- Failed gate: win rate.

The preserve-base guard worked mechanically (`351` validation and `288` final base candidates preserved), but the expanded rescue universe was still too broad. Profit improved, but added trades reduced precision and worsened validation risk.

## Business Decision

No live switch. No `.env`, threshold, sizing, model artifact, or bot restart change.

Do not retry the same low-volume runner-retention grid. The next useful direction should reduce the rescue candidate universe before the retention scorer, preferably with decision-time flow/liquidity compatibility or a stricter coverage/LCB selector rather than another broad `prob>=0.85/0.875, volume_30s>=0.6` rescue.
