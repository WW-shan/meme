# 2026-05-23 CoolChina Abstention Refresh

## Context

This round continued from the post-restart no-switch closeout at commit `f49a0945163884fea7663eaa6e64c5b56eb717c3`. The live bot and collector were running under `./tools/memectl` / tmux, `data/bot_state.json` had zero open positions, and the live model context remained unchanged:

- `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`
- primary threshold `0.98`
- near-rescue threshold `0.94`
- `MIN_ENTRY_VOLUME_30S=1.5`
- `POSITION_SIZE=0.10`

No new external SmartSearch research was needed in this node because the live evidence did not introduce a deployable new method. The decision reuses the already committed research and replay evidence rejecting broad quick-TP overlays, low-volume rescue, and support-flow rules:

- `docs/research/20260523-post-restart-recovery-refresh/summary.md`
- `docs/research/20260523-flowparity-support-quicktp-replay/summary.md`
- `docs/research/20260521-ultra-short-runner-entry-exit/summary.md`

## Frozen Evidence

Report artifacts:

- `data/replay_reports/time_to_barrier_probe_20260523_2250_since_221344_correct_abstention.json`
- `data/replay_reports/low_volume_breakout_probe_20260523_2250_since_221344_prob94.json`
- `data/replay_reports/support_action_policy_20260523_2250_since_221344_correct_abstention.json`

Since the prior frozen cutoff, `2026-05-23 22:13:44`, there were `0` paper-trade rows. The bot and collector logs had no parsed errors; the collector showed catch-up warnings in the `51-75` block range, but no connection failures.

The frozen time-to-barrier report, generated at `2026-05-23 22:52:48`, saw `405` signal decisions, dropped `386` duplicate token decisions, and emitted `19` per-token-address candidates:

- classes: `fast_profit_then_collapse=1`, `flat_timeout=11`, `missing_path=1`, `stop_first=6`
- policies: `quick_take_profit=1`, `skip=18`
- current live primary shape selected `0` candidates
- v95 near-rescue shape selected `0` candidates
- old ultra-short quick-TP shape selected `1` candidate, `ChіnаPоwеr`, which was `stop_first` with `-18%` in `12.01s`
- `prob>=0.985 && PredReturn>=5` selected only that same `ChіnаPоwеr` stop-first candidate
- `prob>=0.98 && PredReturn>=0` selected `5`, all `stop_first`

The low-volume probe selected `4` candidates:

- classes: `low_volume_fakeout=3`, `low_volume_flat=1`
- policies: `skip=4`

The support-action probe used default `min_selected=3` and found `0` eligible rules.

## Watchpoint

This slice had a visible display-name copycat/homoglyph cluster around `CоolСhіnа` / `酷中国` variants. In the frozen TTB report, the exact `CоolСhіnа` display symbol appeared across `5` token addresses with outcomes:

- `stop_first=3`
- `fast_profit_then_collapse=1`
- `flat_timeout=1`

This is not enough for a hand-written copycat veto. It is useful watchpoint evidence for a future learned candidate-level meta-gate or stricter flow/path-state model, where duplicate-display or symbol-family behavior could be a feature if it remains predictive across more windows.

## Decision

`NO_GO_FOR_LIVE_SWITCH`.

Do not change `.env`, `MODEL_DIR`, thresholds, `MIN_ENTRY_VOLUME_30S`, sizing, model artifacts, or live bot runtime state. Do not restart the bot for this round.

The fresh evidence confirms correct abstention rather than a missed-runner opportunity. Entry-value floors protected against the low-return quick-TP-looking cases, volume/volatility floors rejected a stale high-PredReturn flat case, and every high-probability positive-PredReturn subset in the frozen report resolved as stop-first. The named next direction remains a learned candidate-level meta-gate or stricter flow/path-state model, not another broad low-volume rescue, broad quick-TP overlay, or copycat-symbol hard veto.

## Scoreboard

`docs/model_scoreboard.md` was updated for this round as a probe-only no-switch note. No accepted model metrics changed.
