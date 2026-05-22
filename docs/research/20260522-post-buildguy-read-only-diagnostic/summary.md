# 2026-05-22 Post-BUILDGUY Read-Only Diagnostic

## Context

This round continued the live v95 canary review after the BUILDGUY nonce failure had already been attributed as an execution-layer issue and archived in the prior round.

The goal was not to change live settings. It was to check whether the post-BUILDGUY signal stream had a new actionable model hypothesis or only a repeat of already-rejected low-volume / short-spike behavior. A new successful trade, `龙爪`, arrived during the round and was folded into the same active CCG node instead of opening a new task.

## Live Evidence

- Bot and collector were running throughout the round.
- After the `龙爪` close, `data/bot_state.json` had balance `0.003229380463438805`, `positions={}`, and no open position.
- `data/paper_trades.jsonl` had `186` rows after the `龙爪` open and close.
- The earlier `吃饱饱赚饱饱` row still has only an `OPEN` entry, but current bot state is clean because the zero-balance state guard prevented stale position resurrection.
- Since BUILDGUY at `2026-05-22 17:46:18`, there were `952` signal decisions: `950` rejected and `2` queued.
- Since this task start at `18:11:04`, there were `420` signal decisions: `419` rejected and `1` queued.
- Since the `龙爪` signal at `18:17:12`, there were `266` signal decisions: `265` rejected and `1` queued.

## Successful Primary Trade

`龙爪` (`0xF97Fca15242b659b85858F5167bC017B60B44444`) was a clean current-gate confirmation:

- Signal: `2026-05-22 18:17:12.430199`, `prob=0.9924232830169161`, `PredReturn=59.65499868749451`, `volume_30s=3.172212385073328`, `price_volatility=0.2425841856252674`, `age=0s`.
- Open: `18:17:14.443795`, lifecycle fast status, `signal_to_open=2.013963s`, `entry_fill_lag=0.793175s`, entry slippage `+3.4737%`, size `0.0002936275673819876` BNB.
- Path: MFE `+46.33%` versus signal and `+41.42%` versus entry; MAE `-6.55%` versus signal and `-9.69%` versus entry.
- Close: `18:17:47.929280`, `TRAILING_STOP`, hold `33.485485s`, net profit `+0.000030378124710234503` BNB.

This is useful positive evidence that the current v95 primary gates can catch a clean short runner. It is not evidence to loosen thresholds or volume gates because the trade passed the existing primary profile decisively.

## Read-Only Probes

Three local probes were rerun after `龙爪`:

- `data/replay_reports/time_to_barrier_probe_20260522_post_buildguy.json`
- `data/replay_reports/support_action_policy_20260522_post_buildguy.json`
- `data/replay_reports/low_volume_breakout_probe_20260522_post_buildguy.json`

### Time-to-barrier summary

- `40` per-token rejected-signal candidates.
- Class counts: `fast_profit=4`, `fast_profit_then_collapse=2`, `slow_runner=1`, `stop_first=11`, `flat_timeout=22`.
- Policy counts: `quick_take_profit=6`, `conditional_slow_hold=1`, `skip=33`.

### Support policy summary

- `40` input candidates.
- `7` positive candidates, `33` negative candidates.
- No eligible rule at `min_selected=5`.
- Decision: `probe_only_replay_required`.

### Low-volume breakout summary

- `8` per-token candidates.
- Class counts: `low_volume_fast_profit_then_stop=3`, `low_volume_fakeout=4`, `low_volume_flat=1`.
- Policy counts: `quick_take_profit_probe=3`, `skip=5`.

## Notable Cases

- `龙爪`: successful primary-gate trade, `+46.33%` MFE versus signal, `TRAILING_STOP` close for `+0.0000303781` BNB.
- `MVB`: `prob=0.9891`, `PredReturn=25.61`, low-volume reject, `+33.74%` MFE, `-28.21%` MAE, `+25%` in `9.87s`, `-18%` in `60.87s`.
- `金融平权`: low-volume reject, `+38.77%` MFE, `-43.66%` MAE, `+25%` in `10.40s`, `-18%` in `57.40s`.
- `币安梦`: low-volume reject, `+42.91%` MFE, `-22.95%` MAE, `+25%` in `22.52s`.
- `咪咪图`: `prob=0.9851`, `PredReturn=8.87`, low-volume reject, but only `+1.17%` MFE and `-24.64%` MAE.
- `Libra`: low-volume reject in the task-start window, `+0.68%` MFE, `-24.62%` MAE, `-18%` in `65.95s`.
- `丧彪`: low-volume/high-probability reject with `+152.38%` MFE, but `PredReturn=0.52`, `volume_30s=1.01`, and `-19.19%` MAE; this remains a mixed short-spike example, not a deployable rule.

## Decision

This round is rejected as a model-change round. The evidence confirms the current story:

- `龙爪` validates the existing primary gates rather than arguing for looser gates,
- short spikes exist,
- low-volume tokens remain a mixed bag,
- the support window is too small for a deployable overlay,
- and the obvious global fixes have already been rejected.

No live config, threshold, sizing, runtime, model artifact, or bot process change is justified.

`docs/model_scoreboard.md` was updated with a diagnostic note so this round is recorded publicly instead of remaining only in `.ccg` state.

## Verification

- `python scripts/probe_time_to_barrier.py ...`
- `python scripts/probe_support_action_policy.py ...`
- `python scripts/probe_low_volume_breakout.py ...`
- Claude analysis sessions `917aef53-dad0-4f4e-aa20-7dd662d5828a` and `d57b1705-142f-4474-8f79-3951c948f3f9`
- `git diff --check` passed
- Docs/report factual consistency review passed before commit
