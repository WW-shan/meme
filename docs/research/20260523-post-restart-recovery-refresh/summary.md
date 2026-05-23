# 2026-05-23 Post-Restart Recovery Refresh

## Context

This round started as an operations recovery after both live tmux services were found stopped. The bot state had zero open positions before restart, the local proxy on `127.0.0.1:10808` was reachable, and proxied RPC checks returned HTTP 200. The services were restarted with `./tools/memectl`, leaving the live model context unchanged:

- `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`
- primary threshold `0.98`
- near-rescue threshold `0.94`
- `MIN_ENTRY_VOLUME_30S=1.5`
- `MIN_ENTRY_PRICE_VOLATILITY=0.1`
- 10% sizing

No external research was needed in this node. The decision reuses the already recorded SmartSearch-backed and replay-integrated conclusions around ultra-short runner overlays, low-volume rescue, and support-flow quick-TP rules.

## Frozen Evidence

Post-restart report artifacts:

- `data/replay_reports/time_to_barrier_probe_20260523_2213_since_214839_post_restart.json`
- `data/replay_reports/low_volume_breakout_probe_20260523_2213_since_214839_prob94.json`
- `data/replay_reports/support_action_policy_20260523_2213_since_214839_post_restart.json`

Operational checks after restart showed:

- bot running under `memectl` / tmux after restart
- collector running under `memectl` / tmux after restart
- zero open positions in `data/bot_state.json`
- zero paper trades after `2026-05-23 21:48:39`
- zero bot errors after restart; the only bot warning was the expected `http_only` RPC mode warning
- zero collector errors after restart; collector warnings were only the initial catch-up lag messages

The down-window missed-opportunity check was intentionally out of scope for this node. The model decision below starts from the post-restart window beginning at `2026-05-23 21:48:39`.

The frozen time-to-barrier probe, generated at `2026-05-23 22:13:44`, saw `283` signal decisions, dropped `269` duplicate token decisions, and emitted `14` per-token-address candidates. These represented `14` unique token addresses and `12` distinct display symbols because `bnb³` and `傻小子` appeared on two different token addresses:

- classes: `fast_profit=1`, `fast_profit_then_collapse=2`, `stop_first=3`, `flat_timeout=8`
- policies: `quick_take_profit=3`, `skip=11`
- current live primary shape selected `0` candidates
- v95 near-rescue shape selected `0` candidates
- old ultra-short quick-TP shape selected `0` candidates

The only `prob>=0.985 && PredReturn>=5` stop/run split was mixed:

- `bnb³`: `prob=0.98936`, `PredReturn=7.38`, `volume_30s=1.99`, `age=9s`, stop-first with `-18%` in `0.64s`
- `existence`: `prob=0.98907`, `PredReturn=6.01`, `volume_30s=1.56`, `age=7s`, quick `+25%` in `21.05s`, then later hit `-18%`

The low-volume breakout probe selected only `3` candidates:

- `巫师佩佩`: flat/skip
- `傻小子`: runner by probe taxonomy, but `PredReturn=3.79`, below the `35` primary floor and the `32` near-rescue floor
- `JAILIFY`: runner by probe taxonomy, but `PredReturn=-2.08`, below every deployable entry-value floor

The support-action probe used its default `min_selected=3` and had `0` eligible rules. With the committed default report there is no support rule to replay from this post-restart slice.

## Decision

`NO_GO_FOR_LIVE_SWITCH`.

Do not change `.env`, `MODEL_DIR`, thresholds, `MIN_ENTRY_VOLUME_30S`, sizing, or live bot runtime state. Do not restart the bot for this round.

This evidence is useful as a post-restart abstention check, not as promotion evidence. The quick-profit examples remain below the entry-value floors that prior strict replay work already falsified when broadened into overlays. The high-probability positive-PredReturn cell is mixed and tiny, and the support rule finder has no eligible default rule.

The next named direction remains a learned candidate-level meta-gate or stricter flow/path-state model that must beat v95 under validation, final, walk-forward, and stress replay. Do not reopen broad low-volume rescue or broad quick-TP overlays from this slice alone.

## Scoreboard

`docs/model_scoreboard.md` was updated for this round as a probe-only rejected/no-switch note. No accepted model metrics changed.
