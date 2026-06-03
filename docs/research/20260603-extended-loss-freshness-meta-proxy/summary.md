# 2026-06-03 Extended-Loss Freshness Meta-Proxy

## Live State

- Bot and collector were running under `./tools/memectl` in the expected `meme-bot` and `meme-collector` tmux sessions.
- `data/bot_state.json` showed balance `0.001525176567509963` BNB and no open positions.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, `MAX_CONCURRENT_POSITIONS=8`, and `MIN_ENTRY_VOLUME_30S=1.5`.
- Latest public boundary before this experiment was `e40e679ba3bc0c1f8bb6534b48b3650f89a5a6f1`, pushed to `origin/main`, with GitHub Actions `CI` run `26779334546` passing.

## Live Attribution

Fresh artifacts:

- `data/replay_reports/live_trade_attribution_20260603_after_extended_loss_cluster.json`
- `data/replay_reports/live_trade_attribution_20260603_after_extended_loss_cluster.md`
- `data/replay_reports/action_policy_live_shadow_20260603_after_extended_loss_cluster.json`
- `data/replay_reports/action_policy_live_shadow_20260603_after_extended_loss_cluster.md`
- `data/replay_reports/action_policy_activation_shadow_20260603_after_extended_loss_cluster.json`
- `data/replay_reports/action_policy_activation_shadow_20260603_after_extended_loss_cluster.md`

Since `2026-06-01 21:38:26`, live attribution found `7` closed trades, `0` wins, `7` losses, and net profit `-0.00018803661607591775` BNB. Failure labels were `dead_flow_timeout=6` and `entry_slippage_failure=1`; close reasons were `TIME_EXIT=6` and `ENTRY_SLIPPAGE_PROTECTION=1`. The near-threshold split had `3` dead-flow timeout losses (`-0.00006702131007131721` BNB), while primary trades had `4` losses (`-0.00012101530600460054` BNB).

Rejected-path support expanded to `10701` signal decisions and `942` per-token candidates. Barrier classes were `fast_profit=48`, `fast_profit_then_collapse=40`, `flat_timeout=657`, `slow_runner=23`, and `stop_first=174`; recommended policies were `quick_take_profit=88`, `conditional_slow_hold=23`, and `skip=831`.

Action-policy live shadow scored `10708` signals, with `7` queued signals, `50` `continue_hold` routes, and `7` queued shadow-used matched trades. Those matched trades had net profit `-0.00018803661607591775` BNB. Activation shadow matched the same `7` queued shadow-used trades and found `0` activation hits, `0` release hits, and outcomes `never_activated_loss=7`. This is negative live-risk evidence for direct conditional-exit router enablement even though the router remains a replay `Shadow Candidate`.

## Prior Research Reused

This pass reused and extended:

- `docs/research/20260602-cumulative-activation45-freshness-meta-proxy/summary.md`
- `docs/research/20260602-dividend-loss-accepted-entry-meta-gate/summary.md`
- `docs/research/20260602-current-lifecycle-conditional-exit-router-refresh/summary.md`
- `docs/research/20260602-replay-compatible-freshness-volatility-veto/summary.md`
- `docs/research/20260530-candidate-meta-gate-trade-delta/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`

New live-derived angle: the cumulative accepted-trade freshness proxy is retested after the live loss cluster expanded from `2` losses to `7` losses, including a distinct entry-slippage-protection failure. This checks whether the earlier `Research Alpha` signal survives broader negative live evidence rather than only fitting the first two dividend-loss trades.

## Deep Research

SmartSearch Deep Research plan and evidence were saved under this folder:

- `00-deep-plan.json`
- `01-meta-labeling.json`
- `02-uncertainty.json`
- `03-uplift.json`
- `04-counterfactual.json`
- `05-fetch-hudsonthames.md`
- `06-fetch-mlfinpy.md`
- `07-fetch-arxiv-uncertainty.md`
- `08-fetch-openreview-aegis.md`
- `09-fetch-causalml-counterfactual-value.md`

Provider note: `smart-search doctor --format json` reported main search and fetch capability available, but Exa and Zhipu were not configured. The plan listed Exa/Zhipu as possible cross-source tools; this run used configured SmartSearch broad search plus fetched page evidence.

Useful source-backed design constraints:

- Hudson & Thames and mlfinpy both frame meta-labeling as a secondary model that learns whether to act on a primary signal, while triple-barrier labels preserve path-dependent take-profit, stop-loss, and time-out outcomes.
- mlfinpy's meta-labeling docs emphasize that the secondary learner should decide whether to take or pass on an opportunity presented by the primary model, not invent a new primary side.
- The uncertainty-gating sources support using uncertainty as a routing or deferral signal, but thresholds must be calibrated per use case and proxy-only evidence should not be promoted to runtime without strict evaluation.
- The counterfactual value source reinforces that optimizing for expected value, not raw conversion or classification lift, matters when an action has costs.

## Hypothesis Portfolio

1. **Cumulative accepted-trade freshness / signal-context abstention proxy**. Selected because it directly targets `7` accepted live losses and tests whether the prior Research Alpha survives the larger cluster. Expected impact is high for avoiding current dead-flow/entry-slippage losses; evidence strength is medium; falsifiability is high; cost is low.
2. **Replay-compatible accepted-action / trade-delta meta gate**. Deferred because the proxy remains useful but still lacks strict replay context. This is still the next structural bridge if signal-time features can be made replay-compatible.
3. **Direct conditional-exit router live enablement review**. Rejected for this boundary because activation shadow found `7/7` queued shadow-used matched outcomes as `never_activated_loss`.
4. **Rejected-entry quick-profit / slow-runner rescue**. Deferred because fresh rejected support is now larger (`48` fast-profit, `40` fast-profit-then-collapse, `23` slow-runner), but prior broad rejected-entry sweeps remain weak. This needs a structurally narrower replay, not another scalar threshold sweep.

## Hypothesis

If decision-time freshness, latency, and signal-context risk features identify accepted trades with no useful activation path, a conservative abstention proxy should remove validation/final losing accepted trades without removing validation/final winners. The train split is allowed one winner skip for rule discovery, but any validation/final winner skip falsifies the conservative proxy.

Falsification rule: reject or cap below shadow if the selected train rule skips validation/final winners, has non-positive validation/final abstention delta, is top-contribution dependent, lacks enough contribution count, or lacks strict replay coverage for net profit, drawdown, walk-forward, stress, and trade-count gates.

## Experiment

```bash
venv/bin/python scripts/probe_execution_freshness_abstention.py \
  --since '2026-06-01 08:22:49' \
  --output data/replay_reports/execution_freshness_signal_context_paired_delta_20260603_extended_loss_cluster_conservative.json \
  --write-selected-trade-delta \
  --min-train-selected 3 \
  --min-train-loss-precision 0.75 \
  --max-train-winner-count 1 \
  --min-validation-selected 1 \
  --max-validation-winner-count 0 \
  --min-final-selected 1 \
  --max-final-winner-count 0 \
  --max-sample-rows 0 \
  --force
```

Uncertainty check:

```bash
venv/bin/python scripts/probe_replay_uncertainty_gate.py \
  --report data/replay_reports/execution_freshness_signal_context_paired_delta_20260603_extended_loss_cluster_conservative.json \
  --candidate-id execution_freshness_signal_context_extended_loss_cluster_20260603 \
  --output data/replay_reports/replay_uncertainty_gate_20260603_extended_loss_cluster_conservative.json \
  --force
```

## Results

- Outcome tier: `Research Alpha`.
- Decision: `research_alpha_proxy_requires_replay_and_signal_time_logging`.
- Paired real trades: `20`, split into train `12`, validation `4`, final `4`.
- Selected rule: `freshness_latency_volume_risk >= 1.29061`.

Selected rule performance:

- Train selected `10` trades: `9` losses and `1` winner, abstention delta `+0.00020449448519645953` BNB, and delta without top skipped-loss benefit `+0.00012674604968689675` BNB.
- Validation selected `4` trades, all losses (`合规`, `有没有分红`, `分红股`, `闭眼冲`), skipped `0` winners, abstention delta `+0.000086157758905629` BNB, and delta without top skipped-loss benefit `+0.00006369194571307474` BNB.
- Final selected `4` trades, all losses (`分红股`, `MARHABA`, `超级金融平台`, `美股焚诀`), skipped `0` winners, abstention delta `+0.0001243445783866875` BNB, and delta without top skipped-loss benefit `+0.00006676317987008032` BNB.

Uncertainty gate:

- Outcome tier: `Research Alpha`.
- Decision: `uncertain_research_alpha_not_shadow`.
- Validation observed paired delta `+7.920792079219201%`, positive probability `1.0`, contribution count `4`, top-1 dependency `false`, top-3 dependency `false`.
- Final observed paired delta `+30.380690410353502%`, positive probability `1.0`, contribution count `4`, top-1 dependency `false`, top-3 dependency `false`.
- Shadow blockers: `validation_contribution_count_below_shadow_min`, `final_contribution_count_below_shadow_min`, and `strict_replay_gate_context_missing`.

## Strict Evaluation

This is a live real-trade paired-delta proxy, not strict replay. It improves expected utility over the selected accepted-trade cohort and does not remove validation/final winners, but it does not compute strict validation/final replay PnL, full trade-count sufficiency, win-rate guardrails over the complete replay set, drawdown, walk-forward, stress replay, or top-winner dependency over a strict replay gate.

The result therefore stays `Research Alpha`. It is useful because the same freshness-latency-volume risk family preserved the larger cumulative loss cluster and selected only validation/final losers. It is insufficient for shadow promotion or live switch because both holdout splits have only `4` contributing trades and strict replay context is missing.

## Decision

`Research Alpha`, not `Shadow Candidate` or `Live Switch Candidate`.

No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

`docs/model_scoreboard.md` was updated because this changes the current accepted-trade structural evidence: the cumulative freshness proxy remains positive after the larger live loss cluster, but activation shadow is negative for direct router enablement and strict replay remains the promotion blocker.

Next direction: convert `freshness_latency_volume_risk` into a replay-compatible accepted-entry / trade-delta gate, or build signal-time logging needed to make this proxy strict-replay evaluable before any shadow promotion.
