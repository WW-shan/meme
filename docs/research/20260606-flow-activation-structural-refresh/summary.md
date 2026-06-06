# 2026-06-06 Flow Activation Structural Refresh

## Live State

- Bot and collector were running under `./tools/memectl` in the expected `meme-bot` and `meme-collector` tmux sessions.
- `data/bot_state.json` showed balance `0.001525176567509963` BNB and no open positions.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, current 10 percent position sizing, and `MAX_CONCURRENT_POSITIONS=8`.
- Latest public boundary before this experiment was `257e5ec1ce65bfd7f602d4f44da09076b39ca42b`, pushed to `origin/main`, with GitHub Actions `CI` run `27056538864` passing.
- Recent logs showed recurring listener catch-up lag warnings, but no sampled fatal traceback, failed buy/sell loop, or open-position risk requiring restart.

## Live Attribution

Fresh current-stream artifacts:

- `data/replay_reports/live_trade_attribution_20260606_current_stream_refresh.json`
- `data/replay_reports/live_trade_attribution_20260606_current_stream_refresh.md`
- `data/replay_reports/action_policy_live_shadow_20260606_current_stream_refresh.json`
- `data/replay_reports/action_policy_live_shadow_20260606_current_stream_refresh.md`
- `data/replay_reports/action_policy_activation_shadow_20260606_current_stream_refresh.json`
- `data/replay_reports/action_policy_activation_shadow_20260606_current_stream_refresh.md`

The 20260606 attribution window had no new closed live trades. The last paper-trade close remained the 2026-06-02 `ENTRY_SLIPPAGE_PROTECTION` close. The signal stream had `1985` rejected signal decisions and `288` per-token candidates. Barrier classes were `fast_profit=4`, `fast_profit_then_collapse=5`, `flat_timeout=258`, `slow_runner=2`, and `stop_first=19`; recommended policies were `quick_take_profit=9`, `conditional_slow_hold=2`, and `skip=277`.

Action-policy live shadow found `1` queued signal, `1985` rejected signals, `19` read-only `continue_hold` routes, and `0` matched trades. Activation-aware shadow had `0` matched rows, `0` activation hits, and `0` release hits. Both shadow reports stayed insufficient support and explicitly unsafe for live switch.

This made direct router enablement inappropriate and kept rejected-entry quick-profit / slow-runner rescue below the same-shape replay-promotion bar. The fresh live-derived angle was narrower: use the no-matched-activation support to falsify whether a hard flow-activation / dead-flow structure can improve strict replay before considering more conditional-exit work.

## Prior Research Reused

No new SmartSearch pass was opened because this experiment reused an existing researched and implemented replay family:

- `docs/research/20260520-flow-activation-gate/summary.md`
- `docs/research/20260602-current-lifecycle-conditional-exit-router-refresh/summary.md`
- `docs/research/20260601-signal-flow-parity-reward-probe/summary.md`
- `docs/research/20260605-freshness-volume-bridge/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`

New live-derived angle: fresh 20260606 shadow had no matched activation/release support, while the current stream was dominated by flat timeouts and low same-shape runner counts. This favored a strict replay falsifier for flow activation and dead-flow exits over another runner-retention or hard freshness/volume micro-sweep.

## Hypothesis Portfolio

1. **Accepted-action flow activation / dead-flow exit structure**. Selected because it directly tests whether requiring actual volume/volatility/pred-return ramp, plus cutting dead-flow positions, can improve strict replay while preserving the current 10 percent sizing and `8` max-open-position risk assumptions.
2. **Signal-time freshness trade-delta tooling for original lag/staleness proxy fields**. Higher long-term value, but larger implementation cost because strict replay still lacks the original live freshness fields.
3. **Rejected-entry quick-profit / runner rescue**. Deferred because fresh current-stream support was small (`9` quick-profit-shaped hints and `2` slow runners) and prior runner-retention sweeps failed strict gates.
4. **Bootstrap / uncertainty gating**. Kept as a confirmation method after a candidate has positive strict replay or paired-delta evidence, not as this round's primary intervention.

## Hypothesis

If the current no-activation / dead-flow risk is structural rather than just a live-shadow sample issue, a bounded flow-activation gate should improve validation and final net profit or expected utility while preserving drawdown, trade count, win rate, walk-forward, stress, and the 10 percent live-sizing assumptions.

Falsification rule: reject if no active candidate improves validation and final net profit while preserving the strict risk gates, or if activity exists only by removing too much baseline edge.

## Experiment

Replay command:

```bash
venv/bin/python scripts/run_flow_activation_replay.py \
  --output data/replay_reports/flow_activation_replay_20260606_no_activation_live_shadow_refresh.json \
  --force
```

The existing bounded grid evaluated `16` replay-only candidates over:

- `buy_flow_activation_min_prob`: `0.988`, `0.989`
- `buy_flow_activation_min_pred_return`: `35.0`, `40.0`
- `buy_flow_activation_max_age_seconds`: `60.0`
- `buy_flow_activation_lookback_seconds`: `30.0`
- `buy_flow_activation_min_volume_ramp_ratio`: `1.8`, `2.2`
- `buy_flow_activation_min_current_volume_30s`: `1.5`, `2.0`
- `buy_dead_flow_exit_min_hold_seconds`: `180.0`
- `buy_dead_flow_exit_max_mfe_pct`: `0.05`

Strict assumptions were `position_fraction=0.1`, `max_position_fraction=0.1`, `max_open_positions=8`, `skip_all_in_replay=true`, and no fixed stake.

## Results

- Outcome tier: `Rejected`.
- Report: `data/replay_reports/flow_activation_replay_20260606_no_activation_live_shadow_refresh.json`.
- Overall decision: `reject`.
- Live-switch evidence: `false`.
- Validation baseline: `23` trades, net profit `0.012287965049540807` BNB, win rate `0.7391304347826086`, max drawdown `-7.3601560332172244%`, walk-forward worst return `2.8517753731235773%`, stress worst net profit `0.004624099108476647` BNB, stress worst return `90.78921415793582%`, and stress worst max drawdown `-12.242079755254087%`.
- No validation candidate passed the strict acceptance gate.
- Selected validation candidate index `8` used `min_prob=0.989`, `min_pred_return=35.0`, `max_age=60.0`, `lookback=30.0`, `volume_ramp_ratio=1.8`, `volume_ramp_delta=0.8`, `pred_return_delta=4.0`, `price_volatility_delta=0.04`, `current_volume_30s=1.5`, and the `180s` / `5%` dead-flow exit settings.
- The selected validation candidate was active (`51` flow-activation signals, `44` flow-activation rejects, `6` flow-activation entries), but reduced net profit to `0.008526578728717657` BNB, reduced trades to `15`, reduced win rate to `0.7333333333333333`, and slightly worsened max drawdown to `-7.387393994296065%`. It improved stress metrics, but failed the net-profit, trade-count reduction, win-rate, and drawdown gates.
- The selected candidate had `0` dead-flow exits, so the dead-flow-exit part of the structure did not contribute in this replay.
- Final confirmation also failed the net-profit gate: final baseline net profit was `0.001968280392192024` BNB over `22` trades, while the candidate produced `0.0018619298980930973` BNB over `17` trades. Final win rate improved from `0.5454545454545454` to `0.5882352941176471`, drawdown improved from `-18.20143651802614%` to `-16.892463534877166%`, and stress improved, but the candidate still removed too much baseline profit.

## Strict Evaluation

This was a strict live-sized replay over the current v95 canary model, 10 percent position sizing, `max_open_positions=8`, current replay costs/delays, walk-forward checks, and stress replay.

The flow-activation structure is rejected for this current lifecycle refresh. It is active and can reduce some risk, but it behaves as an over-aggressive entry reducer: validation net profit falls by about `0.00376138632082315` BNB, validation trade count falls from `23` to `15`, and final net profit also falls. This is not a small final-split win-rate issue; the selected structure misses the main research objective of improving expected live profit.

## Decision

`Rejected`, not `Research Alpha`, `Shadow Candidate`, or `Live Switch Candidate`.

No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

`docs/model_scoreboard.md` was updated because this replay closes the 20260606 no-activation / flow-activation structural falsifier. It confirms that hard flow-activation gates should not be reopened as parameter sweeps without a new data population or learned trade-delta target.

Next direction: stop hard flow-activation / dead-flow parameter sweeps for this population. The higher-value next path is signal-time freshness / accepted-action trade-delta tooling for original freshness proxy fields, or a learned accepted-action conditional-exit selector that explains why the prior router improves common trades while fresh live activation support remains insufficient.
