# 2026-05-30 Direct-Delta / Shadow-Ranker Refresh

## Live State

- Bot and collector were running under `memectl` in tmux sessions `meme-bot` and `meme-collector`.
- `data/bot_state.json` had no open positions and balance `0.002752730398351113` BNB.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, and empty `FIXED_STAKE_BNB`.
- Latest non-CCG boundary before this experiment was `43d8b2f3ca767e24b7bab2c7f02b6ee16ac75ca2`, pushed to `origin/main`, with GitHub Actions `CI` run `26674300979` passing.

## Live Attribution

Artifact: `data/replay_reports/live_trade_attribution_20260530_after_hazard_guard.json` / `.md`.

Since `2026-05-29 21:19:42`, there were no closed live trades, but the live stream had `4010` signal decisions and `261` per-token rejected candidates:

- `fast_profit=17`
- `slow_runner=13`
- `fast_profit_then_collapse=10`
- `flat_timeout=168`
- `stop_first=53`

This supported another structural experiment, but prior quick-profit overlays and runner-retention micro-sweeps were already rejected or only `Research Alpha`, so the selected direction was a secondary shadow ranker / meta gate evaluated with paired trade delta.

## Prior Review And Direction Portfolio

Avoided directions:

- Do not continue quick-profit overlay sweeps: `quick_profit_nonbroad_20260530` hard-rejected with negative final paired delta and severe final drawdown.
- Do not continue activation45 threshold/dead-flow micro-sweeps: activation45 remains useful, but the dead-flow overlay selected the no-overlay control and the hazard guard stayed top-1 dependent on final.
- Do not continue runner-retention utility/volceil threshold sweeps: those are `Research Alpha` at best and top-winner dependent.
- Do not retry the same candidate meta-gate score floor: it tied validation baseline at best and failed net-profit improvement.

Ranked candidates:

1. Direct-delta / shadow-ranker refresh.
   - Expected impact: high if it can learn which high-probability rejected candidates are clean runners without global threshold relaxation.
   - Evidence: current live rejects have enough fast-profit and slow-runner shape support, and repo already has shadow-ranker tooling.
   - Cost: moderate; requires adding paired trade-delta output to the shadow replay CLI.
2. Activation45 live-shadow accumulation only.
   - Evidence is strong, but this round needed an experiment that can improve model choice rather than only restating current shadow support.
3. Unsupported quote / `BUY_NOT_READY` route experiment.
   - Research Alpha evidence exists, but deployment risk and routing implementation cost are higher.
4. Bootstrap gate refinement only.
   - Useful for classification, not itself a model improvement.

Selected direction: direct-delta / shadow-ranker refresh.

## Deep Research

SmartSearch Deep Research artifacts:

- Plan: `docs/research/20260530-direct-delta-shadow-ranker/00-deep-plan.json`
- Broad search: `docs/research/20260530-direct-delta-shadow-ranker/evidence/01-search.json`
- Provider gap records: `02-zhipu.json` and `03-exa.json` show missing provider keys, so those routes were unavailable.
- Fetched evidence:
  - `04-fetch-hudson-meta-labeling.md`
  - `05-fetch-arxiv-doubly-robust.md`
  - `06-fetch-paybis-backtest.md`

Research takeaways applied here:

- A secondary model should operate on top of the primary model and decide take/pass or sizing, not replace the primary signal.
- Small-sample offline policy value needs conservative evaluation, paired trade-delta, and top-winner dependency checks before promotion.
- Crypto bot backtests need realistic friction, stress, walk-forward checks, and paper/shadow evidence before any live switch.

## Tooling

`scripts/run_shadow_meta_gate_replay.py` now supports:

- `--write-selected-trade-delta`

This reruns the selected validation and final candidate with trade logs and writes `selected_trade_delta_attribution`, so shadow-ranker experiments can be sent through `scripts/probe_replay_uncertainty_gate.py`.

## Experiment

```bash
venv/bin/python scripts/run_shadow_meta_gate_replay.py \
  --output data/replay_reports/shadow_meta_gate_replay_20260530_direct_delta_shadow_ranker.json \
  --write-selected-trade-delta \
  --force

venv/bin/python scripts/probe_replay_uncertainty_gate.py \
  --report data/replay_reports/shadow_meta_gate_replay_20260530_direct_delta_shadow_ranker.json \
  --candidate-id direct_delta_shadow_ranker_20260530 \
  --output data/replay_reports/replay_uncertainty_gate_20260530_direct_delta_shadow_ranker.json \
  --force
```

Selected validation candidate:

- Candidate index: `44`
- `buy_shadow_meta_gate_min_score=0.65`
- `buy_shadow_meta_gate_min_prob=0.989`
- `buy_shadow_meta_gate_max_entry_score=10.0`
- `buy_shadow_meta_gate_min_entry_volume_30s=2.0`
- `buy_shadow_meta_gate_min_entry_price_volatility=0.20`
- `buy_shadow_meta_gate_max_age_seconds=60.0`

## Result

Replay decision: `reject`.

Validation baseline to selected:

- Net profit BNB: `0.022842003299 -> 0.023423233603`
- Trades: `38 -> 57`
- Win rate: `0.815789 -> 0.701754`
- Max drawdown: `-10.187954% -> -10.205776%`
- Walk-forward worst return: `101.883108% -> 96.610178%`
- Walk-forward worst drawdown: `-13.229438% -> -13.275409%`
- Stress worst net profit BNB: `0.011661288085 -> 0.013504419189`
- Shadow meta-gate entries: `19`
- Failed validation gates: max drawdown, material trade expansion, walk-forward return, walk-forward drawdown, and win rate.

Final baseline to selected:

- Net profit BNB: `0.002032913328 -> 0.001759674532`
- Trades: `18 -> 29`
- Win rate: `0.666667 -> 0.482759`
- Max drawdown: `-16.256141% -> -23.593798%`
- Walk-forward worst return: `-5.576362% -> 1.928551%`
- Walk-forward worst drawdown: `-18.206422% -> -20.394208%`
- Stress worst net profit BNB: `-0.000066180250 -> 0.000838962643`
- Shadow meta-gate entries: `11`
- Failed final gates: net profit, max drawdown, stress drawdown, material trade expansion, walk-forward drawdown, and win rate.

Paired-delta / uncertainty result:

- Outcome tier: `Rejected`.
- Decision: `uncertainty_gate_rejected`.
- Rejection reasons: `final_observed_delta_non_positive`, `final_positive_probability_below_research_min`.
- Validation added trades: `19`, win rate `47.3684%`, return delta `+110.289987%`, but bootstrap positive probability only `0.78225` and top-3 winner dependent.
- Final added trades: `11`, win rate `18.1818%`, return delta `-51.410116%`; final observed paired delta `-51.453310%`, bootstrap positive probability `0.35125`.

## Tier

`Rejected`.

This is not a final small-sample win-rate noise case. The selected shadow ranker expanded trade count, lowered win rate, worsened validation walk-forward risk, failed final net profit, and introduced toxic final added trades. Do not continue this exact `shadow_meta_gate` score-floor / high-probability rejected-candidate grid.

Useful evidence: the direct-delta evaluation path is now stronger because the shadow replay can emit paired trade-delta. The next version should train or rank directly on paired added-trade utility, or use live-shadow labels, rather than relying on the current shadow ranker score grid.

## Scoreboard

`docs/model_scoreboard.md` was updated because this closes a structural shadow-ranker attempt and changes the next-direction constraints.

No `.env`, sizing, threshold, model artifact, bot process, collector process, runtime enablement, restart, or live switch changed.
