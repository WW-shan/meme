# 2026-06-02 Replay-Compatible Freshness Volatility Veto

## Live State

- Bot and collector were running under `./tools/memectl` in the expected `meme-bot` and `meme-collector` tmux sessions.
- `data/bot_state.json` had no open positions and balance `0.001857812463585878` BNB at the live-health check.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, `MAX_CONCURRENT_POSITIONS=8`, and `MIN_ENTRY_VOLUME_30S=1.5`.
- Latest public boundary before this experiment was `9d35545c57f84c1e408659e47f2a124638b50875`, pushed to `origin/main`, with GitHub Actions `CI` run `26772788957` passing.

## Fresh Live Attribution

Fresh watch artifacts after the cumulative freshness meta-proxy boundary:

- `data/replay_reports/live_trade_attribution_20260602_replay_gate_continue_watch.json`
- `data/replay_reports/live_trade_attribution_20260602_replay_gate_continue_watch.md`
- `data/replay_reports/action_policy_live_shadow_20260602_replay_gate_continue_watch.json`
- `data/replay_reports/action_policy_live_shadow_20260602_replay_gate_continue_watch.md`
- `data/replay_reports/action_policy_activation_shadow_20260602_replay_gate_continue_watch.json`
- `data/replay_reports/action_policy_activation_shadow_20260602_replay_gate_continue_watch.md`

Since the last closed-trade boundary at `2026-06-01 21:38:26`, live attribution found `0` new closed trades, `790` signal decisions, and `98` rejected per-token candidates. Barrier classes were `fast_profit=5`, `fast_profit_then_collapse=3`, `flat_timeout=80`, and `stop_first=10`; recommended policies were `quick_take_profit=8` and `skip=90`. Action-policy live shadow scored `790` rejected production decisions, with `12` read-only `continue_hold` shadow routes, `0` queued rows, and `0` matched trades. Activation45 shadow had `0` matched rows and stayed insufficient support.

This does not reopen broad rejected-entry quick-profit, runner-retention, or scalar activation-threshold sweeps. The relevant trigger remains the prior cumulative activation45 freshness meta-proxy, which selected `freshness_latency_volatility_risk >= 1.33016` on accepted live trades but was capped at `Research Alpha` because strict replay context was missing.

## Prior Research Reused

No new SmartSearch pass was opened because this experiment directly replays an already researched signal family:

- `docs/research/20260602-cumulative-activation45-freshness-meta-proxy/summary.md`
- `docs/research/20260601-execution-freshness-paired-delta-proxy/summary.md`
- `docs/research/20260530-candidate-meta-gate-trade-delta/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`
- `docs/research/20260531-replay-compatible-execution-freshness/summary.md`

New live-derived angle: translate the proxy-only freshness-latency-volatility signal into a strict replay-compatible approximation using decision-time `buy_flow_abstention_min_entry_price_volatility` thresholds instead of live-only paired-trade proxy fields.

## Hypothesis Portfolio

1. **Replay-compatible freshness / volatility veto over accepted entries**. Selected for this boundary because it is the smallest falsifiable bridge from the positive accepted-trade freshness proxy into strict validation/final/walk-forward/stress replay, and it keeps 10% sizing unchanged.
2. **Trade-delta-trained accepted-action meta gate**. Deferred until the replay-compatible scalar bridge is falsified, because previous accepted-entry gates failed final/stress gates unless a fresh live-derived feature gives a better target.
3. **Conditional exit / early-profit harvest**. Kept as the next structural direction if this veto fails, because cumulative activation45 support suggests the useful population is post-entry outcome separation rather than another hard entry veto.
4. **Missed clean runner detector**. Deferred because the fresh rejected-path support remains small and mixed: `8` quick-profit-shaped policies, `0` queued rows, and many flat/stop-first outcomes.

## Hypothesis

If the cumulative freshness-latency-volatility proxy is a durable accepted-entry hazard signal, then a strict replay-compatible volatility/freshness veto should remove bad accepted entries without reducing validation net profit, stress profit, walk-forward robustness, win rate, or drawdown versus the current v95 live-sized baseline.

Falsification rule: reject if the best validation candidate fails any acceptance gate, if the live-derived `0.2506201076490986` volatility threshold worsens validation or stress, or if gains appear only in final confirmation after validation rejection.

## Experiment

Custom grid artifact:

- `docs/research/20260602-replay-compatible-freshness-volatility-veto/freshness_volatility_flow_grid.json`

Replay command:

```bash
venv/bin/python scripts/run_flow_abstention_replay.py \
  --candidate-grid-json docs/research/20260602-replay-compatible-freshness-volatility-veto/freshness_volatility_flow_grid.json \
  --output data/replay_reports/flow_abstention_replay_20260602_freshness_volatility_custom_grid.json \
  --force
```

The grid evaluated `24` replay-only candidates over:

- `buy_flow_abstention_min_prob`: `0.94`, `0.98`
- `buy_flow_abstention_max_age_seconds`: `300.0`, `560.0`
- `buy_flow_abstention_min_entry_volume_30s`: `0.0`, `1.5`
- `buy_flow_abstention_min_entry_price_volatility`: `0.23`, `0.2506201076490986`, `0.3`
- `buy_flow_abstention_min_toxic_entry_volume_30s`: `0.0`

## Results

- Outcome tier: `Rejected`.
- Report: `data/replay_reports/flow_abstention_replay_20260602_freshness_volatility_custom_grid.json`.
- Overall decision: `reject`.
- Live-switch evidence: `false`.
- Validation baseline: `38` trades, net profit `0.012939792939249493` BNB, win rate `0.7894736842105263`, max drawdown `-10.888843581804252%`, walk-forward worst return `96.09750444876708%`, stress worst net profit `0.006478274907808795` BNB, stress worst return `216.6780631826524%`, and stress worst max drawdown `-6.904080205213258%`.
- Best validation candidate was candidate `2`: `min_prob=0.94`, `max_age=300.0`, `min_entry_volume_30s=0.0`, `min_entry_price_volatility=0.3`, and `min_toxic_entry_volume_30s=0.0`.
- Candidate `2` rejected `4` validation entries and tied baseline trades, net profit, win rate, max drawdown, and walk-forward metrics, but worsened stress worst net profit from `0.006478274907808795` to `0.0061666875239571395` BNB and stress worst return from `216.6780631826524%` to `206.25643832018383%`; it failed `net_profit_bnb`, `stress_worst_net_profit_bnb`, and `stress_worst_net_return_pct`.
- The live-derived volatility threshold candidate (`min_entry_price_volatility=0.2506201076490986`, candidate `1`) rejected `12` validation entries but reduced net profit to `0.01293277514585539` BNB, reduced trade count to `37`, lowered win rate to `0.7837837837837838`, worsened max drawdown to `-11.021588612800171%`, lowered walk-forward worst return to `95.8627811772033%`, and lowered stress worst net profit to `0.005848864377025475` BNB.
- Final confirmation for candidate `2` improved the weaker final baseline (`0.0009746464715070843` to `0.0012329034988394572` BNB), but this cannot promote the direction because validation had already failed strict acceptance.

## Strict Evaluation

This is a strict live-sized replay with the current v95 model, 10% position sizing, `max_open_positions=8`, one entry per token, current execution delays/costs, walk-forward, and stress replay. It directly tests a replay-compatible proxy for the positive accepted-trade freshness signal and shows that the strict replay bridge is not good enough.

The failure is not just a small-sample final split issue. The live-derived threshold worsened validation PnL, drawdown, walk-forward return, stress profit, stress return, and win rate. The selected validation candidate only survived by rejecting fewer rows and tying headline validation metrics, while still worsening stress.

## Decision

`Rejected`, not `Research Alpha`, `Shadow Candidate`, or `Live Switch Candidate`.

No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

`docs/model_scoreboard.md` was updated because this strict replay changes the conclusion of the prior freshness proxy: the proxy remains useful as diagnostic evidence, but a hard replay-compatible volatility/freshness veto is rejected.

Next direction: stop hard volatility/freshness veto micro-sweeps and pivot to a structural direction, preferably conditional exit / early-profit harvest or a trade-delta-trained accepted-action meta gate with bootstrap/uncertainty checks.
