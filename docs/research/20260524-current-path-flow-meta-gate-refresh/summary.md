# 2026-05-24 Current Path/Flow Meta-Gate Refresh

## Decision

No live switch.

The fresh live slice after the previous closeout produced no new paper trades and one useful high-confidence reject cluster, `BDC`, that the current gates correctly skipped. A fresh strict live-sized rerun of the existing flow-enhanced path-state meta-gate on current lifecycle data still rejected the direction: low path-state score thresholds made no rejects and matched the baseline exactly, while high thresholds rejected all validation trades.

Keep `data/models/20260519_v95_v84_selective_nearmiss_gate`, current thresholds, 10% sizing, `.env`, and the running bot unchanged.

`docs/model_scoreboard.md` was updated with this rejection.

## Live Evidence

- Active model: `data/models/20260519_v95_v84_selective_nearmiss_gate`.
- `ENABLE_TRADING=true`; live sizing and entry settings were not changed.
- Bot and collector were running under `memectl`/tmux.
- `data/bot_state.json` had no open positions.
- There were no `data/paper_trades.jsonl` trade rows after `2026-05-24 17:43:00` local.
- Fresh high-confidence reject cluster: `BDC` (`0xB804554A59292b9b78eD2A6A3168D7Bf32074444`).
  - First signal at `2026-05-24 17:52:45.413533` local: `prob=0.9890895802603529`, `PredReturn=26.12130415866104`, `volume_30s=1.277227722772277`, rejected for `entry_volume_30s_below_min`.
  - Within seconds, `PredReturn` fell to `12.598678960865843`, then `8.816882322020327`, then negative.
  - Later near-threshold rejects stayed negative, so this was correct abstention, not evidence for lowering thresholds or volume floors.

External Claude analysis was attempted for the M/high-risk CCG analysis step, but the backend rejected the request before analysis:

```text
reasoning_effort=xhigh is invalid; expected low, medium, or high
SESSION_ID: 3e93cfb6-10c5-4f58-bda5-86e9070852b8
```

No Gemini or external Codex fallback was used.

## Replay

Command:

```bash
python scripts/run_path_state_meta_gate_replay.py \
  --model-dir data/models/20260519_v95_v84_selective_nearmiss_gate \
  --lifecycle-dir data/training \
  --output data/replay_reports/path_state_meta_gate_replay_20260524_current_flow_v95.json \
  --force \
  --no-cache
```

Environment note: `stable_baselines3` was unavailable, so the replay used the repo's rule-based exit fallback.

Report: `data/replay_reports/path_state_meta_gate_replay_20260524_current_flow_v95.json`

Result:

- `decision=reject`
- `live_switch_evidence=false`
- `candidates=9`
- training context: `894775` train samples; path-state training rows `782957` with `275621` positive / `507336` negative labels
- validation split: `3780` episodes, `178842` samples, `143` scored path-state candidates
- final split: `3646` episodes, `175381` samples, `128` scored path-state candidates

Validation baseline:

- `total_trades=32`
- `net_profit_bnb=0.01849379681948987`
- `win_rate=0.75`
- `max_drawdown_pct=-27.449205901322237`
- `walk_forward_worst_net_return_pct=60.41096553554461`

Validation candidates:

- `buy_path_state_meta_gate_min_score` from `0.35` through `0.90` matched baseline exactly:
  - `total_trades=32`
  - `net_profit_bnb=0.01849379681948987`
  - `path_state_meta_gate_signal_count=38`
  - `path_state_meta_gate_entry_count=32`
  - `path_state_meta_gate_reject_count=0`
  - acceptance failed because there was no profit improvement and no active reject behavior.
- `buy_path_state_meta_gate_min_score` at `0.95`, `0.98`, and `0.99` rejected all validation candidates:
  - `total_trades=0`
  - `net_profit_bnb=0.0`
  - `path_state_meta_gate_reject_count=143`
  - acceptance failed profit, trade-count, win-rate, walk-forward, and stress gates.

Final confirmation for selected candidate `0` (`min_score=0.35`) was not deployable because it still made no rejects:

- baseline and candidate both had `27` trades
- baseline and candidate both had `net_profit_bnb=0.010510733756195972`
- baseline and candidate both had `win_rate=0.5555555555555556`
- baseline and candidate both had `max_drawdown_pct=-15.951749821109928`
- baseline and candidate both had `walk_forward_worst_net_return_pct=-4.208571433609909`
- candidate had `path_state_meta_gate_signal_count=30`, `entry_count=27`, `reject_count=0`
- final stress was identical to baseline, with worst return `49.299373057066084%`, worst profit `0.0025040645938535317` BNB, and worst drawdown `-20.145215257476657%`

## Interpretation

The existing flow-enhanced path-state meta-gate still has no useful middle band on current data. It either behaves as a no-op or disables trading completely. That is not evidence for a live switch, and it is also not evidence for a static threshold or volume relaxation.

The next path/flow attempt should not rerun the same broad score threshold grid. If this direction continues, it should first diagnose why path-state scores have no usable selectivity for the live near-rescue/post-peak problem, then test a narrower candidate universe or richer causal freshness labels under the same validation, final, walk-forward, stress, and 10% sizing gates.
