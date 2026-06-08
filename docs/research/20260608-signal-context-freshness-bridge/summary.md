# 2026-06-08 Signal-Context Freshness Bridge

## Live State

- Bot and collector were running under `./tools/memectl` in the expected `meme-bot` and `meme-collector` tmux sessions.
- `data/bot_state.json` showed balance `0.001559636535526772` BNB and no open positions.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, and `MIN_ENTRY_VOLUME_30S=1.5`.
- Latest real close remained `苹果人生`, closed `2026-06-07 12:25:39.499918` by `TRAILING_STOP` for `+0.00005553972801680855` BNB.
- Current node state at this boundary: active task not archived; no new non-`.ccg` commit or push yet.

## Fresh Attribution

Fresh report:

- `data/replay_reports/live_trade_attribution_20260608_freshness_bridge_entry.json`
- `data/replay_reports/live_trade_attribution_20260608_freshness_bridge_entry.md`

Since the `2026-06-07 12:25:39.499918` anchor, there were `0` closed trades and the attribution report stayed `NO_GO_FOR_LIVE_SWITCH`.

Rejected-path support:

- Signal decisions: `4827`.
- Per-token candidates: `393`.
- Barrier classes: `fast_profit=21`, `fast_profit_then_collapse=15`, `slow_runner=9`, `flat_timeout=289`, and `stop_first=59`.
- Recommended policies: `quick_take_profit=36`, `conditional_slow_hold=9`, and `skip=348`.

## Prior Research Reused

No new SmartSearch Deep Research was needed because this round did not introduce a new external method. It reused the existing SmartSearch-backed freshness/meta-labeling and uncertainty artifacts:

- `docs/research/20260608-after-apple-freshness-meta-proxy/summary.md`
- `docs/research/20260603-extended-loss-freshness-meta-proxy/summary.md`
- `docs/research/20260602-cumulative-activation45-freshness-meta-proxy/summary.md`
- `docs/research/20260531-replay-compatible-execution-freshness/summary.md`
- `docs/research/20260530-candidate-meta-gate-trade-delta/summary.md`
- `docs/research/20260529-bootstrap-uncertainty-gate/summary.md`

New live-derived angle: bridge the positive accepted-trade `freshness_latency_volume_risk` rule from `OPEN`-row context to matched queued `SIGNAL_DECISION` context, because the current blocker is missing strict replay context rather than a failed freshness signal.

## Tooling Change

Codex added an opt-in mode to `scripts/probe_execution_freshness_abstention.py` / `src/pipeline/execution_freshness_abstention_probe.py`:

- `--signal-context-policy-source signal-context`
- `--policy-field-scope signal-context-only`

The default behavior is unchanged. The new mode derives lifecycle chain lag/staleness and the composite freshness risk from matched queued `SIGNAL_DECISION` records, while excluding OPEN-row categorical/boolean rules from the scanned policy field set. It remains read-only diagnostic tooling and does not alter live runtime behavior.

TDD coverage:

- `tests/model/test_execution_freshness_abstention_probe.py::TestExecutionFreshnessAbstentionProbe::test_signal_context_only_policy_can_use_signal_chain_lag_for_volume_risk`

## Hypothesis

If the accepted-trade freshness proxy is genuinely a decision-time signal, then a signal-context-only policy scan should reproduce a conservative validation/final loss-removal rule using matched queued `SIGNAL_DECISION` fields, without relying on `OPEN`-row lifecycle freshness fields.

Falsification rule: reject this bridge if the signal-context-only probe cannot find a train-eligible rule, removes validation/final winners, has non-positive validation/final abstention delta, or cannot record which policy fields came from matched signal context.

## Experiment

```bash
venv/bin/python scripts/probe_execution_freshness_abstention.py \
  --since '2026-06-01 08:22:49' \
  --output data/replay_reports/execution_freshness_signal_context_only_paired_delta_20260608_freshness_bridge.json \
  --write-selected-trade-delta \
  --min-train-selected 3 \
  --min-train-loss-precision 0.75 \
  --max-train-winner-count 1 \
  --min-validation-selected 1 \
  --max-validation-winner-count 0 \
  --min-final-selected 1 \
  --max-final-winner-count 0 \
  --max-sample-rows 0 \
  --signal-context-policy-source signal-context \
  --policy-field-scope signal-context-only \
  --force
```

Uncertainty check:

```bash
venv/bin/python scripts/probe_replay_uncertainty_gate.py \
  --report data/replay_reports/execution_freshness_signal_context_only_paired_delta_20260608_freshness_bridge.json \
  --candidate-id execution_freshness_signal_context_only_20260608_freshness_bridge \
  --output data/replay_reports/replay_uncertainty_gate_20260608_signal_context_only_freshness_bridge.json \
  --force
```

## Results

Signal-context-only report:

- Outcome tier: `Research Alpha`.
- Decision: `research_alpha_proxy_requires_replay_and_signal_time_logging`.
- Policy parameters: `signal_context_policy_source=signal_context`, `policy_field_scope=signal_context_only`.
- Paired real trades: `21`, split into train/validation/final `12/4/5`.
- Selected rule: `freshness_latency_volume_risk >= 1.2906080427027575`.
- Train selected `10` trades: `9` losses and `1` winner, loss precision `0.9`, abstention delta `+0.00020449448519645953` BNB.
- Validation selected `4/4` trades, all `TIME_EXIT` losses (`合规`, `有没有分红`, `分红股`, `闭眼冲`), skipped `0` winners, abstention delta `+0.000086157758905629` BNB.
- Final selected `4/5` trades, all losses (`分红股`, `MARHABA`, `超级金融平台`, `美股焚诀`), skipped `0` winners, abstention delta `+0.0001243445783866875` BNB.
- Final candidate left only the `苹果人生` `TRAILING_STOP` winner, unchanged with `return_delta_pct=0.0`.

Trade-delta attribution:

- Validation removed `4` baseline `TIME_EXIT` losses and added `0` trades.
- Final removed `3` `TIME_EXIT` losses plus `1` `ENTRY_SLIPPAGE_PROTECTION` loss and added `0` trades.
- Final common trades: `1`, the `苹果人生` winner, unchanged; `0` worsened common trades.

Uncertainty gate:

- Outcome tier: `Research Alpha`.
- Decision: `uncertain_research_alpha_not_shadow`.
- Validation observed paired delta `+7.920792079219201%`, positive probability `1.0`, contribution count `4`, no top-1/top-3 dependency.
- Final observed paired delta `+30.380690410353502%`, lower bound `+3.960396039611438%`, positive probability `0.9995`, contribution count `5`, no top-1/top-3 dependency.
- Shadow blockers: `validation_contribution_count_below_shadow_min`, `final_contribution_count_below_shadow_min`, and `strict_replay_gate_context_missing`.

## Strict Evaluation

This is a stronger bridge than the previous OPEN-row-only proxy because the selected composite risk can now be reproduced from matched queued `SIGNAL_DECISION` context. It still is not a `Shadow Candidate` or live-switch candidate: strict replay matched sample rows remain missing these freshness fields, contribution counts are below shadow minimums, and no drawdown/walk-forward/stress replay exists for the rule.

## Decision

`Research Alpha`, not `Shadow Candidate` or `Live Switch Candidate`.

No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

`docs/model_scoreboard.md` was updated because this bridge changes the current interpretation of the freshness proxy: it is no longer only an OPEN-row diagnostic, but it remains blocked from promotion until strict replay samples can carry the same signal-context freshness fields.

Next direction: propagate or reconstruct the signal-context freshness fields inside strict replay matched sample/trade-delta inputs, or keep the bridge as Research Alpha until enough live queued/opened shadow rows raise contribution support.
