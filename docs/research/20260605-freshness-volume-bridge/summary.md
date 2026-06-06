# 2026-06-05 Freshness Volume Replay Bridge

## Live State

- Bot and collector were running under `./tools/memectl` in the expected `meme-bot` and `meme-collector` tmux sessions.
- `data/bot_state.json` showed balance `0.001525176567509963` BNB and no open positions.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, `MAX_CONCURRENT_POSITIONS=8`, and `MIN_ENTRY_VOLUME_30S=1.5`.
- Latest public boundary before this experiment was `d7063d20b90d681805eabedd4ef11fd6549c28e0`, pushed to `origin/main`, with GitHub Actions `CI` run `26866917653` passing.
- Recent logs showed recurring listener catch-up lag warnings and catch-up diagnostics, but no sampled open-position risk or failed live buy/sell requiring a restart.

## Live Attribution

Fresh post-restart artifacts:

- `data/replay_reports/live_trade_attribution_20260605_post_restart_gap_refresh.json`
- `data/replay_reports/live_trade_attribution_20260605_post_restart_gap_refresh.md`
- `data/replay_reports/action_policy_live_shadow_20260605_post_restart_gap_refresh.json`
- `data/replay_reports/action_policy_live_shadow_20260605_post_restart_gap_refresh.md`
- `data/replay_reports/action_policy_activation_shadow_20260605_post_restart_gap_refresh.json`
- `data/replay_reports/action_policy_activation_shadow_20260605_post_restart_gap_refresh.md`

The post-restart attribution window had no new closed live trades. It saw `5746` signal decisions and `538` per-token rejected candidates. Barrier classes were `missing_path=532`, `flat_timeout=4`, and `slow_runner=2`; recommended policies were `skip=536` and `conditional_slow_hold=2`. This is not enough support to reopen another rejected-entry runner-retention sweep.

Action-policy live shadow scored the same `5746` rejected production decisions, with `3` read-only `continue_hold` routes and `0` queued or matched live trades. Activation shadow had `0` matched rows and stayed insufficient support.

The live-derived trigger for this experiment remained the cumulative accepted-loss cluster from `2026-06-01 08:22:49` through `2026-06-03`, where the proxy `freshness_latency_volume_risk >= 1.29061` selected only validation/final losing accepted trades. The bridge question was whether the same idea survives strict replay through decision-time volume thresholds.

## Prior Research Reused

No new SmartSearch pass was opened because this experiment directly replays an already researched signal family:

- `docs/research/20260603-extended-loss-freshness-meta-proxy/summary.md`
- `docs/research/20260602-replay-compatible-freshness-volatility-veto/summary.md`
- `docs/research/20260602-cumulative-activation45-freshness-meta-proxy/summary.md`
- `docs/research/20260530-candidate-meta-gate-trade-delta/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`

New live-derived angle: translate the positive `freshness_latency_volume_risk` proxy into a strict replay-compatible bridge using `buy_flow_abstention_min_toxic_entry_volume_30s`, while preserving the existing v95 primary and near-threshold entry gates and the 10% live sizing policy.

## Hypothesis Portfolio

1. **Replay-compatible freshness-volume veto over accepted entries**. Selected because it is the smallest falsifiable bridge from the positive accepted-trade proxy into strict validation/final/walk-forward/stress replay. Expected impact is medium-high; evidence strength is medium from the accepted-loss proxy; falsifiability is high; implementation cost is low.
2. **Signal-time logging / accepted-action trade-delta evaluator for freshness proxy fields**. Higher structural value if the strict bridge fails, but it requires new logging or feature-parity work before it can be falsified in replay.
3. **Conditional exit / early-profit harvest**. Still promising from prior router replay, but fresh live shadow has no matched support in this post-restart window and prior activation shadow warned against direct enablement.
4. **Rejected-entry slow-runner rescue**. Deferred because the fresh window found only `2` slow-runner-shaped rejects and prior runner-retention parameter/label sweeps failed strict gates.

## Hypothesis

Because cumulative live accepted-loss evidence showed that `freshness_latency_volume_risk` can select losing accepted trades without selecting validation/final winners in a real-trade proxy, try a replay-compatible volume bridge that vetoes high-probability accepted entries with high decision-time `entry_volume_30s`, expecting validation/final net profit and expected utility to improve without worsening drawdown, walk-forward, stress, win rate, or trade-count sufficiency.

Falsification rule: reject if no validation candidate passes the strict gate, if final confirmation fails, if stress or walk-forward risk worsens, or if the result depends on a no-op / no-trade threshold rather than an active accepted-entry bridge.

## Experiment

Custom grid artifact:

- `docs/research/20260605-freshness-volume-bridge/freshness_volume_bridge_grid.json`

Replay command:

```bash
venv/bin/python scripts/run_flow_abstention_replay.py \
  --candidate-grid-json docs/research/20260605-freshness-volume-bridge/freshness_volume_bridge_grid.json \
  --output data/replay_reports/flow_abstention_replay_20260605_freshness_volume_custom_grid.json \
  --force
```

The grid evaluated `12` replay-only candidates over:

- `buy_flow_abstention_min_prob`: `0.94`, `0.98`
- `buy_flow_abstention_max_age_seconds`: `60.0`, `300.0`
- `buy_flow_abstention_min_entry_volume_30s`: `1.5`
- `buy_flow_abstention_min_entry_price_volatility`: `0.0`
- `buy_flow_abstention_min_toxic_entry_volume_30s`: `2.4240056633663367`, `2.7334179633666937`, `3.9321634653465347`

## Results

- Outcome tier: `Rejected`.
- Report: `data/replay_reports/flow_abstention_replay_20260605_freshness_volume_custom_grid.json`.
- Overall decision: `reject`.
- Live-switch evidence: `false`.
- Validation baseline: `23` trades, net profit `0.006906022313991049` BNB, win rate `0.7391304347826086`, max drawdown `-7.83177553911969%`, walk-forward worst return `0.9912648838679594%`, stress worst net profit `0.0024873423452635027` BNB, stress worst return `83.1938331598507%`, and stress worst max drawdown `-13.12421618650992%`.
- Selected validation candidate `5` used `min_prob=0.94`, `max_age=300.0`, `min_entry_volume_30s=1.5`, `min_entry_price_volatility=0.0`, and `min_toxic_entry_volume_30s=3.9321634653465347`; candidate `11` tied those validation metrics at `min_prob=0.98`.
- The selected validation candidate rejected `5` entries and improved headline validation net profit to `0.007164279341323421` BNB, win rate to `0.7727272727272727`, and walk-forward worst return to `9.903975182173141%`.
- The selected validation candidate failed the strict acceptance gate because stress worsened: stress worst net profit fell to `0.0024384165569730273` BNB, stress worst return fell to `81.55741834304719%`, and stress worst max drawdown worsened to `-14.192130171674144%`.
- Lower volume thresholds were materially worse. Candidates with `min_toxic_entry_volume_30s` of `2.4240056633663367` or `2.7334179633666937` reduced validation net profit, win rate, drawdown, walk-forward, and stress metrics.
- Final confirmation for the selected validation candidate failed: final net profit fell from `0.0007045119955919922` to `0.0006597787909743916` BNB, win rate fell from `0.5238095238095238` to `0.5`, max drawdown worsened from `-19.48633852816448%` to `-19.707795426219278%`, walk-forward worst return worsened from `-6.247107342863412%` to `-7.40643032099495%`, stress worst net profit fell from `-0.00046354682921803366` to `-0.0005139393540588137` BNB, and stress worst drawdown worsened from `-30.073416865935364%` to `-30.879684707650267%`.

## Strict Evaluation

This was a strict live-sized replay with the current v95 canary model, 10% position sizing, `max_open_positions=8`, one entry per token, current replay costs/delays, walk-forward, and stress replay.

The bridge is rejected. A high-volume threshold can improve validation headline profit, but it does not preserve stress robustness and does not confirm on final. The failure is not only a small final win-rate issue: final net profit, max drawdown, walk-forward return, stress profit, stress return, and stress drawdown all worsened together.

## Decision

`Rejected`, not `Research Alpha`, `Shadow Candidate`, or `Live Switch Candidate`.

No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

`docs/model_scoreboard.md` was updated because this strict replay changes the conclusion of the `freshness_latency_volume_risk` proxy: the proxy remains useful real-trade diagnostic evidence, but a hard replay-compatible volume-threshold bridge is rejected.

Next direction: stop hard freshness/volume threshold micro-sweeps. The higher-value structural paths are either signal-time logging / accepted-action trade-delta tooling that can evaluate the original proxy fields directly in replay, or a conditional-exit / early-profit harvest direction when fresh live evidence supports it.
