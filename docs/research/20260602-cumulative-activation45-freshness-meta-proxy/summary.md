# 2026-06-02 Cumulative Activation45 Freshness Meta-Proxy

## Live State

- Bot and collector were running under `./tools/memectl` in the expected `meme-bot` and `meme-collector` tmux sessions.
- `data/bot_state.json` had no open positions and balance `0.001857812463585878` BNB.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, `MAX_CONCURRENT_POSITIONS=8`, and `MIN_ENTRY_VOLUME_30S=1.5`.
- Latest public boundary before this experiment was `b38cc4a1685b6005242b8017a9d9d716dc87a70b`, pushed to `origin/main`, with GitHub Actions `CI` run `26771724971` passing.

## Live Attribution

Fresh watch artifacts after the cumulative activation45 boundary:

- `data/replay_reports/live_trade_attribution_20260602_post_cumulative_boundary_watch.json`
- `data/replay_reports/live_trade_attribution_20260602_post_cumulative_boundary_watch.md`
- `data/replay_reports/action_policy_live_shadow_20260602_post_cumulative_boundary_watch.json`
- `data/replay_reports/action_policy_live_shadow_20260602_post_cumulative_boundary_watch.md`
- `data/replay_reports/action_policy_activation_shadow_20260602_post_cumulative_boundary_watch.json`
- `data/replay_reports/action_policy_activation_shadow_20260602_post_cumulative_boundary_watch.md`

Since the last closed-trade boundary at `2026-06-01 21:38:26`, live attribution found no new closed trades, `785` signal decisions, and `95` rejected per-token candidates. Barrier classes were `fast_profit=5`, `fast_profit_then_collapse=3`, `flat_timeout=77`, and `stop_first=10`; recommended policies were `quick_take_profit=8` and `skip=87`. Action-policy live shadow scored all `785` signals as rejected production decisions, with `11` read-only `continue_hold` shadow routes but `0` queued rows, `0` matched trades, and `0` queued shadow-used matches. Activation45 shadow therefore had `0` matched rows and stayed insufficient support.

This does not reopen broad quick-profit, runner-retention, or scalar activation-threshold sweeps. The relevant live-derived trigger remains the cumulative activation45 cohort: `13` real trades since `2026-06-01 08:22:49`, with `10` `never_activated_loss` outcomes, `1` `never_activated_win`, and `2` activated profitable outcomes.

## Prior Research Reused

No new SmartSearch pass was opened because the method is a direct reuse of committed SmartSearch-backed work:

- `docs/research/20260601-execution-freshness-paired-delta-proxy/summary.md`
- `docs/research/20260530-candidate-meta-gate-trade-delta/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`
- `docs/research/20260601-audit-only-live-shadow-instrumentation/summary.md`

New angle: retest the accepted-trade freshness / signal-context abstention proxy on the cumulative activation45 cohort after the post-alpha winner/two-loss set, with a conservative gate that is not allowed to skip validation or final winners.

## Hypothesis Portfolio

1. **Conservative accepted-trade freshness / signal-context abstention proxy**. Selected because it directly targets the no-upside `never_activated_loss` population without changing runtime, sizing, or entry expansion. Expected impact is medium-high, evidence strength is medium from cumulative live trades, falsifiability is high through chronological train/validation/final paired delta, and cost is low using existing tooling.
2. **Strict replay-integrated accepted-entry / trade-delta meta gate**. Deferred until the proxy shows a fresh positive signal, because previous accepted-entry loss gates failed strict final/stress gates and another stale replay without a new live-derived feature would be low value.
3. **Rejected-entry quick-profit or slow-runner rescue**. Rejected for this boundary because the fresh watch window has only `8` quick-profit-shaped rejected candidates and no queued support, while prior broad quick-profit and runner-retention sweeps are already below shadow/live promotion.
4. **Activation45 / conditional-exit live enablement**. Deferred because cumulative activation45 is mixed and dominated by `never_activated_loss`; enabling it directly would not address the current risk.

## Hypothesis

If a decision-time freshness and signal-context risk feature can identify the low-upside cumulative activation45 losses, it should remove validation/final losing trades without removing validation/final winners. The train split is allowed one winner skip for rule discovery, but any validation/final winner skip falsifies this conservative proxy.

Falsification rule: reject or cap below shadow if the selected train rule skips validation/final winners, has non-positive validation/final abstention delta, is top-contribution dependent, lacks enough contribution count, or cannot be evaluated in strict replay.

## Experiment

```bash
venv/bin/python scripts/probe_execution_freshness_abstention.py \
  --since '2026-06-01 08:22:49' \
  --output data/replay_reports/execution_freshness_signal_context_paired_delta_20260602_cumulative_activation45_conservative.json \
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
  --report data/replay_reports/execution_freshness_signal_context_paired_delta_20260602_cumulative_activation45_conservative.json \
  --candidate-id execution_freshness_signal_context_cumulative_activation45_conservative_20260602 \
  --output data/replay_reports/replay_uncertainty_gate_20260602_cumulative_activation45_conservative.json \
  --force
```

## Results

- Outcome tier: `Research Alpha`.
- Decision: `research_alpha_proxy_requires_replay_and_signal_time_logging`.
- Paired real trades: `13`, split into train `7`, validation `3`, final `3`.
- Selected rule: `freshness_latency_volatility_risk >= 1.33016`.
- Train selected `6` trades: `5` losses and `1` winner, loss precision `0.8333333333333334`, abstention delta `+0.00006277224650807779` BNB, delta without the top skipped-loss benefit `+0.000039864999758771615` BNB.
- Validation selected `2` trades, both losses (`球股票交易平台`, `新时代。`), skipped `0` winners, abstention delta `+0.000041380646514476246` BNB, and delta without top skipped-loss benefit `+0.000018453680629394758` BNB.
- Final selected `2` trades, both losses (`宇宙所`, `合规`), skipped `0` winners, abstention delta `+0.000045058877880741464` BNB, and delta without top skipped-loss benefit `+0.000022465721216398746` BNB.
- The final candidate retained the `来了` winner and removed only the two final timeout losses.

Uncertainty gate:

- Outcome tier: `Research Alpha`.
- Decision: `uncertain_research_alpha_not_shadow`.
- Validation observed paired delta: `+4.0045477587369795%`; positive probability `0.9635`; top-1 dependency `false`.
- Final observed paired delta: `+3.9603960396069278%`; positive probability `0.96125`; top-1 dependency `false`.
- Shadow blockers: `validation_contribution_count_below_shadow_min`, `final_contribution_count_below_shadow_min`, and `strict_replay_gate_context_missing`.

## Strict Evaluation

This is proxy evidence over real accepted live trades, not strict replay. It computes paired validation/final trade delta over the selected live cohort and explicitly reports top-contribution dependency, but it does not compute strict validation/final replay PnL, walk-forward, stress replay, drawdown, or full trade-count sufficiency. Those missing gates cap the result at `Research Alpha`.

The useful signal is structural: the selected freshness-latency-volatility feature preserved the final `来了` winner and removed four validation/final timeout losses. The useful blocker is also explicit: contribution counts are only `3` per holdout split and strict replay context is missing, so there is no live switch or shadow promotion.

## Decision

`Research Alpha`, not `Shadow Candidate` or `Live Switch Candidate`.

No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

`docs/model_scoreboard.md` was updated because this adds a positive but proxy-only accepted-action / trade-delta meta-gate boundary after the cumulative activation45 live-risk refresh.

Next highest-value direction: convert this exact freshness-latency-volatility signal into a replay-compatible accepted-entry / trade-delta gate or strict replay feature so validation/final/walk-forward/stress can be evaluated before any shadow promotion.
