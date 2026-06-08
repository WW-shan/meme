# 2026-06-08 After-Apple Freshness Meta-Proxy

## Live State

- Bot and collector were running under `./tools/memectl` in the expected `meme-bot` and `meme-collector` tmux sessions.
- `data/bot_state.json` showed balance `0.001559636535526772` BNB and no open positions.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, and `MIN_ENTRY_VOLUME_30S=1.5`.
- No `BUY_ACTION_POLICY_ROUTER*` values were set in `.env`; default-off router shadow audit remained inactive in the running bot.
- Current node state at entry to this boundary: active task was not archived; prior milestone `2064e21` was committed and pushed; GitHub Actions `CI` run `27111519513` passed.

## Fresh Attribution

Fresh artifacts:

- `data/replay_reports/live_trade_attribution_20260608_next_structural_round_entry.json`
- `data/replay_reports/live_trade_attribution_20260608_next_structural_round_entry.md`
- `data/replay_reports/action_policy_live_shadow_20260608_next_structural_round_entry.json`
- `data/replay_reports/action_policy_live_shadow_20260608_next_structural_round_entry.md`
- `data/replay_reports/action_policy_activation_shadow_20260608_next_structural_round_entry.json`
- `data/replay_reports/action_policy_activation_shadow_20260608_next_structural_round_entry.md`

Since the `2026-06-07 12:25:39.499918` after-`苹果人生` close anchor, there were `0` new closed trades and the attribution report stayed `NO_GO_FOR_LIVE_SWITCH`.

Rejected-path support in the fresh slice:

- Signal decisions: `4670`.
- Per-token candidates: `383`.
- Barrier classes: `fast_profit=20`, `fast_profit_then_collapse=14`, `slow_runner=8`, `flat_timeout=283`, and `stop_first=58`.
- Recommended policies: `quick_take_profit=34`, `conditional_slow_hold=8`, and `skip=341`.

Fresh action-policy live shadow was insufficient:

- Signal count: `4671`.
- Queued signal count: `1`.
- Shadow-used rows: `27`.
- Queued shadow-used rows: `1`.
- Queued shadow-used matched trades: `0`.
- Unique matched live trades: `0`.
- Decision: `insufficient_shadow_support`.

Fresh activation shadow was also insufficient:

- Queued shadow-used matched trades: `0`.
- Activation hits: `0`.
- Release hits: `0`.
- Activated then stop: `0`.
- Decision: `insufficient_activation_shadow_support`.

This ruled out router live enablement or another activation-threshold micro-sweep from fresh support alone.

## Prior Research Reused

No new SmartSearch Deep Research was needed because this boundary reused an already researched and implemented proxy method:

- `docs/research/20260602-cumulative-activation45-freshness-meta-proxy/summary.md`
- `docs/research/20260603-extended-loss-freshness-meta-proxy/summary.md`
- `docs/research/20260607-after-apple-life-continue-hold-router-refresh/summary.md`
- `docs/research/20260530-candidate-meta-gate-trade-delta/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`

New live-derived angle: retest the cumulative accepted-trade freshness / signal-context proxy after the clean `苹果人生` winner enters the holdout slice. The falsifier is whether the rule that previously removed dead-flow / entry-slippage losses now wrongly removes this new accepted winner.

## Hypothesis Portfolio

1. **Cumulative accepted-trade freshness / signal-context proxy refresh**. Selected because it directly tests whether the prior Research Alpha remains conservative after a new clean winner. It is read-only, cheap, and uses existing tooling.
2. **Audit-only in-process router shadow enablement**. Deferred because it is a live-risk config/restart action despite being default-off/audit-only.
3. **Strict replay-compatible accepted-entry / trade-delta bridge**. Deferred until the proxy refresh proves the signal still survives the new winner; this remains the next structural bridge if the proxy stays positive.
4. **Rejected-entry quick-profit or slow-runner rescue**. Deferred because same-shape support exists, but recent runner-retention, scalar flow, generic meta-label, and reward-selector branches were rejected or capped.

## Hypothesis

If `freshness_latency_volume_risk` is still a useful accepted-trade risk proxy, the conservative rule should continue selecting validation/final losses and should preserve the `苹果人生` winner.

Falsification rule: reject if the selected rule removes any validation/final winner, has non-positive validation/final abstention delta, becomes top-contribution dependent, loses contribution support, or remains missing strict replay context for shadow/live promotion.

## Experiment

```bash
venv/bin/python scripts/probe_execution_freshness_abstention.py \
  --since '2026-06-01 08:22:49' \
  --output data/replay_reports/execution_freshness_signal_context_paired_delta_20260608_after_apple_conservative.json \
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
  --report data/replay_reports/execution_freshness_signal_context_paired_delta_20260608_after_apple_conservative.json \
  --candidate-id execution_freshness_signal_context_after_apple_20260608 \
  --output data/replay_reports/replay_uncertainty_gate_20260608_after_apple_conservative.json \
  --force
```

## Results

Proxy report:

- Outcome tier: `Research Alpha`.
- Decision: `research_alpha_proxy_requires_replay_and_signal_time_logging`.
- Paired real trades: `21`, split into train `12`, validation `4`, and final `5`.
- Selected rule: `freshness_latency_volume_risk >= 1.290612259556064`.
- Train selected `10` trades: `9` losses and `1` winner, abstention delta `+0.00020449448519645953` BNB, and delta without top skipped-loss benefit `+0.00012674604968689675` BNB.
- Validation selected `4` trades, all losses (`合规`, `有没有分红`, `分红股`, `闭眼冲`), skipped `0` winners, and produced abstention delta `+0.000086157758905629` BNB.
- Final selected `4` trades, all losses (`分红股`, `MARHABA`, `超级金融平台`, `美股焚诀`), skipped `0` winners, and produced abstention delta `+0.0001243445783866875` BNB.
- Final baseline had `5` trades, `1` winner, `4` losses, net `-0.00006880485036987895` BNB; after proxy abstention, the remaining final set was only the `苹果人生` winner with net `+0.00005553972801680855` BNB.

Trade-delta attribution:

- Validation removed `4` baseline `TIME_EXIT` losses and added `0` trades.
- Final removed `3` `TIME_EXIT` losses plus `1` `ENTRY_SLIPPAGE_PROTECTION` loss and added `0` trades.
- Final common trades: `1`, the `苹果人生` `TRAILING_STOP` winner, unchanged with `return_delta_pct=0.0`; there were `0` worsened common trades.

Uncertainty gate:

- Outcome tier: `Research Alpha`.
- Decision: `uncertain_research_alpha_not_shadow`.
- Validation observed paired delta `+7.920792079219201%`, positive probability `1.0`, contribution count `4`, no top-1 or top-3 dependency.
- Final observed paired delta `+30.380690410353502%`, lower bound `+3.960396039611438%`, positive probability `0.9995`, contribution count `5`, no top-1 or top-3 dependency.
- Shadow blockers: `validation_contribution_count_below_shadow_min`, `final_contribution_count_below_shadow_min`, and `strict_replay_gate_context_missing`.

## Strict Evaluation

This refresh strengthens the existing accepted-trade freshness proxy because it preserved the new clean `苹果人生` winner while still selecting only validation/final losses. It does not promote the method to `Shadow Candidate`: the evidence is live real-trade proxy evidence, not strict replay, and the holdout contribution counts are still below the shadow threshold.

The missing bridge is unchanged: `freshness_latency_volume_risk` needs replay-compatible signal-time logging or a strict replay feature path before any model/runtime promotion can be discussed.

## Decision

`Research Alpha`, not `Shadow Candidate` or `Live Switch Candidate`.

No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

`docs/model_scoreboard.md` was updated because this refresh changes the current accepted-action trade-delta interpretation after the `苹果人生` winner: the freshness proxy remains positive and conservative, but remains capped by missing strict replay context.

Next direction: convert the `freshness_latency_volume_risk` signal into replay-compatible accepted-entry / trade-delta evidence, or add audit-only signal-time logging needed to evaluate the same risk feature under strict replay before any shadow promotion.
