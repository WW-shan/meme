# 2026-05-30 Next Structural Round

## Live State

- Bot and collector were running under `memectl` in tmux sessions `meme-bot` and `meme-collector`.
- `data/bot_state.json` showed no open positions and balance `0.002752730398351113` BNB.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, and no fixed stake.
- Recent logs showed listener catch-up/provider retry diagnostics but no fatal runtime error or new closed trade during the experiment.

## Live Attribution

Artifact: `data/replay_reports/live_trade_attribution_20260530_next_structural_round.json` / `.md`.

Since `2026-05-29 21:19:42`, there were no closed trades, but the live stream had `1749` signal decisions and `127` per-token rejected candidates. Rejected path classes were:

- `fast_profit=8`
- `fast_profit_then_collapse=8`
- `slow_runner=4`
- `flat_timeout=83`
- `stop_first=24`

The live-derived pocket had `16` quick-profit-shaped rejects, with both clean `fast_profit` and `fast_profit_then_collapse` over the same-shape support gate of `7`.

## Prior Review And Direction Selection

Recent scoreboard and research history say broad quick-profit overlays are dangerous: they repeatedly over-expanded trades, lowered win rate, worsened drawdown, or failed walk-forward/stress/final confirmation. This round therefore did not run another broad static quick-profit sweep. It tested a small explicit grid with high probability, bounded low PredReturn, volume/volatility/age/flow constraints, and confirmation limits.

Hypothesis portfolio:

| Rank | Direction | Decision |
|---:|---|---|
| 1 | Non-broad quick-profit falsification from the newly supported rejected pocket | Selected |
| 2 | Non-scalar selector for remaining `never_activated_loss` rows under activation45 | Deferred |
| 3 | Missed slow-runner detector | Deferred because support was only `4` |
| 4 | Activation45 live-shadow refresh only | Deferred because the previous round already promoted activation45 to `Shadow Candidate` |

## Research Evidence

This round reused recent SmartSearch-backed artifacts instead of starting a new outside-method search:

- `docs/research/20260526-conditional-exit-flow-survival/summary.md`
- `docs/research/20260527-delayed-confirmation-quick-profit/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`

New live-derived angle: current post-last-trade attribution had `16` quick-profit-shaped rejects with both subclasses over the support gate, which was materially stronger than earlier windows. That made a narrow falsification worthwhile, but not enough to justify a live switch or broad threshold relaxation.

## Tooling

`scripts/run_primary_score_scalp_replay.py` now supports:

- `--candidate-grid-json` for an explicit JSON grid artifact instead of hard-coded quick-profit candidates.
- `--write-selected-trade-delta` to rerun the selected validation/final candidate with trade logs and write paired trade-delta attribution into the replay report.

The grid artifact is `docs/research/20260530-next-structural-round/quick_profit_nonbroad_grid.json` with candidate id `quick_profit_nonbroad_20260530` and `8` candidates.

## Experiment

```bash
venv/bin/python scripts/run_primary_score_scalp_replay.py \
  --candidate-grid-json docs/research/20260530-next-structural-round/quick_profit_nonbroad_grid.json \
  --output data/replay_reports/quick_profit_nonbroad_replay_20260530.json \
  --write-selected-trade-delta \
  --force

venv/bin/python scripts/probe_replay_uncertainty_gate.py \
  --report data/replay_reports/quick_profit_nonbroad_replay_20260530.json \
  --candidate-id quick_profit_nonbroad_20260530 \
  --output data/replay_reports/replay_uncertainty_gate_20260530_quick_profit_nonbroad.json \
  --force
```

## Results

Replay artifact: `data/replay_reports/quick_profit_nonbroad_replay_20260530.json`.

- Replay decision: `reject`.
- Best validation candidate: candidate index `6`.
- Validation baseline: `0.022842003299308057` BNB net profit, `38` trades, `81.5789%` win rate, `-10.187954315383251%` max drawdown, `101.88310806253628%` walk-forward worst return, stress worst net profit `0.011661288085332917` BNB.
- Validation candidate: `0.022690412314059123` BNB net profit, `170` trades, `54.7059%` win rate, `-10.947074284173697%` max drawdown, `90.65586286807259%` walk-forward worst return, stress worst net profit `0.005995856796074152` BNB.
- Final baseline: `0.001503449729881195` BNB net profit, `17` trades, `64.7059%` win rate, `-16.256141287806237%` max drawdown, `-3.1840099359264684%` walk-forward worst return, stress worst net profit `-0.0003739768902472464` BNB.
- Final candidate: `-0.005075499318240881` BNB net profit, `122` trades, `20.4918%` win rate, `-99.9271397456354%` max drawdown, `-63.54826959737684%` walk-forward worst return, stress worst net profit `-0.0050742188907118065` BNB.

Uncertainty artifact: `data/replay_reports/replay_uncertainty_gate_20260530_quick_profit_nonbroad.json`.

- Outcome tier: `Rejected`.
- Decision: `uncertainty_gate_rejected`.
- Rejection reasons: `validation_observed_delta_non_positive`, `validation_positive_probability_below_research_min`, `final_observed_delta_non_positive`, `final_positive_probability_below_research_min`.
- Validation observed paired delta: `-17.710775980916097%`; bootstrap positive probability `0.45975`.
- Final observed paired delta: `-3467.2363709158226%`; bootstrap positive probability `0.0`.
- Final added candidate trades: `109`, with `20` wins, `89` losses, `18.3486%` win rate, and `-2972.4831152289853%` summed return.
- Removing the top 1 or top 3 positive contributions does not rescue the result: final delta after top-1 removal was `-3531.6251672114395%`, and after top-3 removal was `-3635.713200374629%`.

## Tier

`Rejected`.

This is a hard reject, not a small-sample final win-rate issue. The candidate materially expanded trades, turned final net profit negative, collapsed final win rate, breached drawdown risk, worsened walk-forward/stress, and showed strongly negative paired trade delta. Do not keep sweeping quick-profit overlay parameters in this family unless new live evidence changes the structure, label, or decision point.

## Scoreboard Decision

`docs/model_scoreboard.md` was updated because this round changes the quick-profit direction status and records a reusable replay-grid/trade-delta tool boundary.

No `.env`, model artifact, threshold, sizing, bot process, or live runtime behavior changed.

## Next Direction

Pivot away from quick-profit parameter sweeps. The next highest-value structural direction is a non-scalar selector for the activation45 `never_activated_loss` cohort, or a trade-delta/meta-gate that learns whether an added/removed decision improves the accepted baseline instead of relying on broad quick-profit entry overlays.
