# Activation-Aware Shadow Attribution

## Question

Can the accepted `continue_hold` shadow branch be made more precise by splitting outcomes into activation, release, stop, and never-activated paths?

## Reused Research

This round reuses `docs/research/20260529-live-shadow-router-evaluator/summary.md`.

New live-derived angle: instead of only checking whether `continue_hold` matched profitable exits or a single MFE-giveback loser, classify the queued shadow routes by whether they ever reached `+35%` activation, then whether they reached `+75%` release first or `-18%` stop first.

## Live-First Trigger

Fresh live attribution since `2026-05-29 00:00:00` is saved at:

- `data/replay_reports/live_trade_attribution_20260529_activation_shadow_attribution.json`
- `data/replay_reports/live_trade_attribution_20260529_activation_shadow_attribution.md`

The attribution found 6 closed trades, net `+0.00012579707233376005` BNB:

- `Binance light source`: `mfe_then_giveback`, `STOP_LOSS`, net `-0.00015238787562031852` BNB, MFE `+42.1759%`, hit `+35%` activation after `7.3546s`, then hit `-18%` stop after `87.3546s`.
- `币安光源`: `profitable_exit`, `PPO_SELL100`, net `+0.00027378227534832425` BNB, MFE `+113.5298%`, hit `+35%` activation after `6.8016s` and `+75%` release after `16.8016s`.
- `TripleT`: `profitable_exit`, `TRAILING_STOP`, net `+0.00012565224901414461` BNB, MFE `+86.8858%`, hit `+35%` activation after `9.6993s` and `+75%` release after `46.6993s`.
- `CHILLCAT`: `dead_flow_timeout`, `TIME_EXIT`, net `-5.0867591077252965e-05` BNB, never reached `+35%` activation.
- `未来`: `unprofitable_other`, `PPO_SELL100`, net `-4.512376073509866e-05` BNB, never reached `+35%` activation.
- `CRY͏P͏TOM͏AXX͏ING`: `dead_flow_timeout`, `TIME_EXIT`, net `-2.525822459603866e-05` BNB, never reached `+35%` activation.

The live reject side stayed mixed and mostly below any clean same-shape support for a blind live rule:

- `fast_profit_then_collapse=34`
- `fast_profit=23`
- `slow_runner=6`
- `stop_first=69`
- `flat_timeout=231`

## Experiment

Artifacts:

- `src/pipeline/action_policy_live_shadow.py`
- `scripts/probe_action_policy_live_shadow.py`
- `scripts/probe_action_policy_activation_shadow.py`
- `tests/model/test_action_policy_live_shadow.py`
- `tests/model/test_action_policy_activation_shadow.py`
- `data/replay_reports/action_policy_live_shadow_20260529_activation_shadow_attribution.json`
- `data/replay_reports/action_policy_live_shadow_20260529_activation_shadow_attribution.md`
- `data/replay_reports/action_policy_activation_shadow_20260529_activation_shadow_attribution.json`
- `data/replay_reports/action_policy_activation_shadow_20260529_activation_shadow_attribution.md`

The shadow evaluator scored all queued live signal rows against the current action-policy router, then the activation-aware report split matched queued routes by lifecycle outcomes.

## Result

Key activation-aware counts:

- Queued shadow-used matched trades: `6`
- Activation hits: `3`
- Release hits: `2`
- Activated then stop: `1`
- Outcome counts: `activated_released=2`, `activated_then_stop=1`, `never_activated_loss=3`

Interpretation:

- The current `continue_hold` branch is not dead on arrival, because it cleanly captured 2 winners that reached the release band.
- It is also not safe for direct live enablement, because 3 matched queued routes never activated and still lost, and 1 activated route gave back into stop.
- This is a better basis for a candidate-level meta gate than for a simple release-threshold tweak.

## Tier Classification

`Research Alpha / material shadow-only evidence`, not `Live Switch Candidate`.

## Next Experiment

Test an activation-aware candidate-level meta gate first. If that fails, fall back to a dead-flow exit or entry-abstention gate rather than another small release-threshold sweep.
