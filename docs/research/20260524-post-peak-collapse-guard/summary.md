# 2026-05-24 Post-Peak Collapse Guard

## Decision

No live switch.

The fresh live failure supports the existence of a post-peak-collapse entry problem, but the bounded late-pump exhaustion replay did not validate a deployable static guard. Keep `data/models/20260519_v95_v84_selective_nearmiss_gate`, current thresholds, 10% sizing, `.env`, and the running bot unchanged.

`docs/model_scoreboard.md` was updated with this rejection.

## Live Evidence

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`.
- Live sizing remains `POSITION_SIZE=0.10`; no risk expansion tested.
- New closed trade: `0xD8Fa540a36A9456775a3E021151EA20d58664444`.
  - Opened at `2026-05-24 14:02:00.465688` local.
  - `prob=0.9889313915107122`, `pred_return=70.36626970847468`.
  - Entry lifecycle fields showed `price_from_peak_pct=-0.6997895439988379`.
  - Closed by `TIME_EXIT` at `2026-05-24 14:11:26.601177`, net `-0.000026555076695223786` BNB.
  - Attribution: `bad_entry` / `model_bought_but_should_skip`.
- Fresh high-score near-miss reject `0xA1DC178C905849682F932966eB7258277BFF4444` had `prob=0.9666417118748988`, `pred_return=13.302609568250997`, `volume_30s=0.0`, and also faded after its local peak. This was a correct skip, not evidence for threshold or volume relaxation.

## Research

Smart-search evidence supports path-dependent labeling and candidate-level filtering:

- Triple-barrier labeling and meta-labeling fit this failure family because fixed-horizon labels can miss intra-trade path risk.
- Peak-to-valley drawdown is a path-dependent risk measure, making drawdown-from-peak a defensible signal-time feature.
- The right experiment is therefore a narrow post-peak / late-pump guard, not global threshold lowering.

Source notes:

- `01-search.json`
- `02-hudsonthames-triple-barrier.md`
- `03-mlfinpy-labeling.md`
- `04-mql5-labeling.md`
- `05-quantreo-triple-barrier.md`
- `06-risk-peak-to-valley.md`

External Claude analysis session `0e9fbc2f-3d7d-41ac-a905-0c816c8dd002` agreed to run only the bounded late-pump exhaustion replay first and not broaden the grid unless the narrow replay passed.

## Replay

Command:

```bash
python scripts/run_late_pump_exhaustion_replay.py --output data/replay_reports/late_pump_exhaustion_replay_20260524_v95.json
```

Environment note: `stable_baselines3` was unavailable, so the replay used the repo's rule-based exit fallback.

Report: `data/replay_reports/late_pump_exhaustion_replay_20260524_v95.json`

Result:

- `decision=reject`
- `live_switch_evidence=false`
- `candidates=16`
- Validation baseline:
  - `total_trades=32`
  - `net_profit_bnb=0.01849379681948987`
  - `win_rate=0.75`
  - `max_drawdown_pct=-27.449205901322237`
  - `walk_forward_worst_net_return_pct=60.41096553554461`
  - `stress_worst_net_return_pct=254.9323833540269`
  - `stress_worst_net_profit_bnb=0.012948788501723492`
  - `stress_worst_max_drawdown_pct=-19.090774369056398`
- Validation selected candidate index `0`:
  - `buy_late_pump_veto_min_age_seconds=15`
  - `buy_late_pump_veto_extension_window_seconds=30`
  - `buy_late_pump_veto_min_price_extension_pct=1.0`
  - `buy_late_pump_veto_min_drawdown_from_peak_pct=0.45`
  - `buy_late_pump_veto_min_entry_volume_30s=2.0`
  - `buy_late_pump_veto_min_entry_price_volatility=0.18`
- Validation falsification:
  - every candidate matched baseline profit exactly
  - `max_reject_count=0`
  - `nonzero_reject_candidates=0`
  - `best_validation_accepted_candidate=null`

Final confirmation was also not deployable:

- Final baseline: `27` trades, `0.010510733756195972` BNB, `55.5556%` win rate.
- Final selected candidate: `26` trades, `0.01092687316568585` BNB, `57.6923%` win rate, `late_pump_veto_reject_count=5`.
- Final stress degraded:
  - worst return `38.971983232728455%` vs baseline `49.299373057066084%`
  - worst profit `0.001979505160286039` vs baseline `0.0025040645938535317` BNB
  - worst drawdown `-22.910343999110694%` vs baseline `-20.145215257476657%`
- `final_confirmation.passes_acceptance_gate=false`

## Interpretation

The latest live loss is a real post-peak-collapse example, but this static late-pump guard still has no validation support. Validation produced zero veto firings, so the guard has no demonstrated ability to distinguish bad v95 validation entries from good ones. The final split's 5 rejects are not enough because the candidate failed the strict stress gate.

Do not rerun broad threshold lowering, broad low-volume rescue, broad path-state meta gates, or blanket quick-TP overlays from this evidence. Future work should either wait for more live failures of the same shape or test a learned candidate-level meta-gate with causal path/flow freshness features under the same validation/final/walk-forward/stress gates.
