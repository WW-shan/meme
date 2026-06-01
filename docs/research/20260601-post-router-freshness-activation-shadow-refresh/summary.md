# 2026-06-01 Post-Router Freshness and Activation Shadow Refresh

## Live State

- Bot and collector were running through `./tools/memectl` in the expected tmux sessions.
- `data/bot_state.json` had no open positions and balance `0.002026614705196296` BNB.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, no fixed stake, and `MIN_ENTRY_VOLUME_30S=1.5`.
- Latest public boundary before this round was `c7d4029`, pushed to `origin/main`, with GitHub Actions `CI` run `26738514925` passing.
- Recent bot/collector logs showed continued listener catch-up bursts around `51-58` blocks behind, but no fatal traceback in inspected tails.

## Live Attribution

Fresh attribution artifacts:

- `data/replay_reports/live_trade_attribution_20260601_post_router_shadow_closes.json`
- `data/replay_reports/live_trade_attribution_20260601_post_router_shadow_closes.md`

Command:

```bash
venv/bin/python scripts/probe_live_trade_attribution.py \
  --since '2026-06-01 12:44:58' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --recent-lifecycle-files 96 \
  --output-json data/replay_reports/live_trade_attribution_20260601_post_router_shadow_closes.json \
  --output-md data/replay_reports/live_trade_attribution_20260601_post_router_shadow_closes.md \
  --max-trade-sample 80 \
  --max-candidate-sample 260 \
  --force
```

Result:

- Decision: `NO_GO_FOR_LIVE_SWITCH`.
- Closed trades after the prior `UP` boundary: `4`; wins/losses `0/4`.
- Net profit: `-0.00007714534586565443` BNB.
- Failure labels: `dead_flow_timeout=4`; close reasons: `TIME_EXIT=4`.
- Near-threshold-like trades: `2`, net `-0.00004108490610708974` BNB.
- Primary trades: `2`, net `-0.00003606043975856469` BNB.
- Lifecycle price paths: `4/4` available.

The four new accepted losses were all high-volume/high-volatility, helper-status entries with lifecycle chain lag around `19-23s`. Two were near-threshold rescues and two were primary entries, so a near-threshold-only adjustment would not address the whole cluster.

## Prior Review

Recent artifacts checked:

- `docs/research/20260601-post-selector-conditional-exit-router-refresh/summary.md`
- `docs/research/20260601-execution-freshness-phone-close-refresh/summary.md`
- `docs/research/20260601-execution-freshness-paired-delta-proxy/summary.md`
- `docs/research/20260601-flow-volume-abstention-freshness-proxy/summary.md`
- `docs/research/20260531-dead-flow-exit-replay-continuation/summary.md`
- `docs/research/20260601-signal-flow-parity-reward-probe/summary.md`
- `docs/research/20260601-activation45-after-up-shadow-refresh/summary.md`

Avoided repeats:

- Dead-flow min-hold / max-MFE exit overlay: rejected and inactive on final.
- Simple high-volume or high-volatility hard veto: already failed strict replay or depended on too little validation support.
- Simple volume/volatility micro-sweeps: added winners and losers overlap.
- Never-activated scalar selector expansion: selected no final rows in the latest utility-negative selector.

## Direction Selection

Ranked directions:

1. Execution-freshness accepted-trade paired-delta refresh plus queued-only shadow refresh. Selected first because the four new losses directly match the existing high-lag/no-upside family.
2. Activation45 live-shadow refresh on the enlarged matched accepted-trade sample. Selected after the freshness shadow remained rejected, because it directly checks whether the new no-upside losses fall into the activation-policy cohort without adding entries.
3. Conditional-exit router replay refresh. Deferred because the previous strict replay is already a `Shadow Candidate`, and the fresh no-upside cluster is more about entry/activation selection than release timing.
4. Rejected fast-profit / quick-take-profit replay. Deferred because fresh support is below same-shape gate and the branch has been historically fragile.

Research reuse: no new SmartSearch Deep Research was opened. This round reuses committed SmartSearch-backed freshness/meta-label/action-policy research from:

- `docs/research/20260530-execution-freshness-shadow-evaluator/summary.md`
- `docs/research/20260531-replay-compatible-execution-freshness/summary.md`
- `docs/research/20260601-execution-freshness-paired-delta-proxy/summary.md`
- `docs/research/20260601-execution-freshness-phone-close-refresh/summary.md`
- `docs/research/20260529-live-shadow-router-evaluator/summary.md`
- `docs/research/20260530-activation45-dead-flow-exit/summary.md`
- `docs/research/20260601-activation45-after-up-shadow-refresh/summary.md`

## Experiment 1: Execution Freshness

Commands:

```bash
venv/bin/python scripts/probe_execution_freshness_abstention.py \
  --output data/replay_reports/execution_freshness_signal_context_paired_delta_20260601_post_router_shadow_closes.json \
  --write-selected-trade-delta \
  --force

venv/bin/python scripts/probe_replay_uncertainty_gate.py \
  --report data/replay_reports/execution_freshness_signal_context_paired_delta_20260601_post_router_shadow_closes.json \
  --candidate-id post_router_shadow_execution_freshness_proxy_20260601 \
  --output data/replay_reports/replay_uncertainty_gate_20260601_execution_freshness_post_router_shadow_closes.json \
  --force

venv/bin/python scripts/probe_signal_freshness_shadow.py \
  --since '2026-05-30 18:43:00' \
  --recent-lifecycle-files 192 \
  --output-json data/replay_reports/signal_freshness_queued_only_shadow_20260601_post_router_shadow_closes.json \
  --output-md data/replay_reports/signal_freshness_queued_only_shadow_20260601_post_router_shadow_closes.md \
  --max-candidate-sample 320 \
  --decision queued \
  --split-stability \
  --force
```

Accepted-trade proxy result:

- Outcome tier: `Research Alpha`.
- Decision: `research_alpha_proxy_requires_replay_and_signal_time_logging`.
- Paired real trades: `130`.
- Selected rule shifted to `signal_price_volatility >= 0.2506201076490986`.
- Validation selected `15/15` losses for `+0.000513362917` BNB abstention delta.
- Final selected `15` trades, `14` losses and `1` winner, for `+0.000462492459` BNB abstention delta.
- The final selected winner was `UP`, so the proxy cannot be promoted directly.

Uncertainty gate:

- Outcome tier: `Research Alpha`.
- Decision: `uncertain_research_alpha_not_shadow`.
- Validation bootstrap positive probability: `1.0`.
- Final bootstrap positive probability: `0.8955`.
- Shadow blockers: `final_top3_winner_dependent`, `strict_replay_gate_context_missing`.

Queued-only shadow result:

- Outcome tier: `Rejected`.
- Decision: `insufficient_signal_freshness_split_support`.
- Freshness candidates: `13`.
- Top rule: `lifecycle_status_chain_lag_seconds >= 18.403747081756592`.
- Top-rule all-sample selected `11`, with `10` correct skips and `1` opportunity miss.
- Validation selected `3` with only `0.6667` correct-skip precision because it would miss `UP`.
- Final selected `3/3` correct skips (`0x236f...`, `XBUBBL`, `QIFY`), but stable rule count remained `0`.

Interpretation: freshness remains useful `Research Alpha`, but not shadow/live. The new evidence strengthens the high-lag/high-volatility loss family while also showing why hard abstention is unsafe: `UP` is a profitable high-lag/high-volatility counterexample.

## Experiment 2: Activation45 Live Shadow

Command:

```bash
venv/bin/python scripts/probe_action_policy_activation_shadow.py \
  --since '2026-06-01 08:22:49' \
  --active-model data/models/20260519_v95_v84_selective_nearmiss_gate \
  --activation-pct 45 \
  --release-pct 75 \
  --recent-lifecycle-files 96 \
  --output-json data/replay_reports/action_policy_activation_shadow_20260601_post_router_shadow_closes_activation45.json \
  --output-md data/replay_reports/action_policy_activation_shadow_20260601_post_router_shadow_closes_activation45.md \
  --max-sample-rows 320 \
  --force
```

Result:

- Status: `activation_shadow_support`.
- Signal rows: `4224` (`queued=7`, `rejected=4217`).
- Shadow-used rows: `15`, all `continue_hold`.
- Queued shadow-used matched trades: `7/7`.
- Queued shadow-used matched net profit: `+0.00003640769321832326` BNB.
- Outcomes: `activated_profitable_no_release=1`, `never_activated_loss=5`, `never_activated_win=1`.
- The four post-router timeout losses all classified as `never_activated_loss`.
- The lone activated row remained `.bts`, a profitable trailing-stop trade with MFE `+55.932459%`.
- `UP` remained the important counterexample: profitable but `never_activated_win` with MFE `+26.294491%`, below the `45%` activation threshold.

## Tier

Classification: `Shadow Candidate` / material shadow-only evidence for activation45 cohort monitoring, not `Live Switch Candidate`.

This round does not justify a live switch. It does strengthen two practical conclusions:

- Freshness/high-volatility abstention remains a Research Alpha, not deployable: strict replay context is missing and `UP` is a profitable high-lag/high-volatility counterexample.
- Activation45 shadow support is still material after adding four fresh losses: the matched sample expanded from `3` to `7`, stayed net positive, and every new no-upside timeout loss joined the never-activated-loss bucket.

Next work should not be another scalar activation-threshold sweep or hard freshness/volatility threshold. The higher-value next structural direction is a secondary selector or paired-delta label for the never-activated cohort that protects `UP`-like sub-45% winners while avoiding the five no-upside never-activated losses.

## Scoreboard

`docs/model_scoreboard.md` was updated because this boundary changes the current live-shadow support state and next-direction constraints after four fresh real losses.

No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.
