# 2026-06-08 Strict Freshness Sample Bridge

## Live State

- Bot and collector were running under `./tools/memectl` in the expected `meme-bot` and `meme-collector` tmux sessions.
- `data/bot_state.json` showed balance `0.001559636535526772` BNB and no open positions.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, and `MIN_ENTRY_VOLUME_30S=1.5`.
- Latest real close remained `苹果人生`, closed `2026-06-07 12:25:39.499918` by `TRAILING_STOP` for `+0.00005553972801680855` BNB.

## Fresh Attribution

Fresh report:

- `data/replay_reports/live_trade_attribution_20260608_strict_freshness_sample_bridge_entry.json`
- `data/replay_reports/live_trade_attribution_20260608_strict_freshness_sample_bridge_entry.md`

Since the `2026-06-07 12:25:39.499918` anchor, there were `0` closed trades and the attribution report stayed `NO_GO_FOR_LIVE_SWITCH`.

Rejected-path support:

- Signal decisions: `5036`.
- Per-token candidates: `405`.
- Barrier classes: `fast_profit=21`, `fast_profit_then_collapse=15`, `slow_runner=10`, `flat_timeout=296`, and `stop_first=63`.
- Recommended policies: `quick_take_profit=36`, `conditional_slow_hold=10`, and `skip=359`.

## Prior Research Reused

No new SmartSearch Deep Research was needed because this round did not introduce a new outside method. It reused the existing SmartSearch-backed freshness/meta-labeling and uncertainty-gate direction, with a new live-derived implementation angle: preserve the signal-context freshness policy fields inside the selected trade-delta attribution handoff.

Relevant prior summary:

- `docs/research/20260608-signal-context-freshness-bridge/summary.md`

## Tooling Change

Codex updated `src/pipeline/execution_freshness_abstention_probe.py` so `_trade_delta_rows` preserves the probe's decision-time policy numeric fields when building the synthetic trade rows passed to `replay_trade_delta_attribution`.

The change is report-only. It does not alter live runtime behavior, model scoring, thresholds, sizing, exits, order submission, bot processes, collector processes, or `.env`.

TDD coverage:

- `tests/model/test_execution_freshness_abstention_probe.py::TestExecutionFreshnessAbstentionProbe::test_signal_context_only_policy_can_use_signal_chain_lag_for_volume_risk`

## Hypothesis

If the accepted-trade freshness proxy can be evaluated from signal-time context, then the selected trade-delta attribution should carry those signal-context fields into its policy-feature coverage block. The bridge should turn freshness coverage from missing to available without changing the selected rule or creating live-switch evidence.

Falsification rule: reject this bridge if the selected rule changes to an unrelated feature, if validation/final no longer remove only losses, if the coverage block still reports missing freshness fields for removed baseline trades, or if uncertainty classification promotes the result beyond the report's proxy-only contract.

## Experiment

```bash
venv/bin/python scripts/probe_execution_freshness_abstention.py \
  --since '2026-06-01 08:22:49' \
  --output data/replay_reports/execution_freshness_signal_context_only_paired_delta_20260608_strict_sample_bridge.json \
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
  --report data/replay_reports/execution_freshness_signal_context_only_paired_delta_20260608_strict_sample_bridge.json \
  --candidate-id execution_freshness_signal_context_only_20260608_strict_sample_bridge \
  --output data/replay_reports/replay_uncertainty_gate_20260608_strict_freshness_sample_bridge.json \
  --force
```

## Results

Signal-context-only report:

- Outcome tier: `Research Alpha`.
- Decision: `research_alpha_proxy_requires_replay_and_signal_time_logging`.
- Selected rule stayed `freshness_latency_volume_risk >= 1.2906080427027575`.
- Validation selected `4/4` trades, all `TIME_EXIT` losses (`合规`, `有没有分红`, `分红股`, `闭眼冲`), skipped `0` winners, and produced abstention delta `+0.000086157758905629` BNB.
- Final selected `4/5` trades, all losses (`分红股`, `MARHABA`, `超级金融平台`, `美股焚诀`), skipped `0` winners, and produced abstention delta `+0.0001243445783866875` BNB.
- Final candidate left only the `苹果人生` `TRAILING_STOP` winner, unchanged.

Trade-delta policy coverage:

- Validation removed-trade coverage is now `1.0` for `lifecycle_status_chain_lag_seconds`, `signal_price_volatility`, `signal_volume_30s`, and `freshness_latency_volume_risk`.
- Final removed-trade coverage is now `1.0` for the same fields.
- The coverage aliases are the signal-context names (`signal_price_volatility`, `signal_volume_30s`) plus `lifecycle_status_chain_lag_seconds` and the selected composite `freshness_latency_volume_risk`.

Uncertainty gate:

- Outcome tier: `Research Alpha`.
- Decision: `uncertain_research_alpha_not_shadow`.
- Validation observed paired delta `+7.920792079219201%`, positive probability `1.0`, contribution count `4`, no top-1/top-3 dependency.
- Final observed paired delta `+30.380690410353502%`, lower bound `+3.960396039611438%`, positive probability `0.9995`, contribution count `5`, no top-1/top-3 dependency.
- Shadow blockers remained `validation_contribution_count_below_shadow_min`, `final_contribution_count_below_shadow_min`, and `strict_replay_gate_context_missing`.
- Gate context reason: `proxy_report_requires_replay_before_live_change`.

## Strict Evaluation

This round closes the narrow trade-delta coverage gap from the previous signal-context bridge: selected trade-delta attribution now records the same signal-context freshness policy fields that produced the rule. It does not close the promotion gate. The report is still proxy-only, contribution counts remain below the shadow minimum, and there is no strict replay acceptance gate with drawdown, walk-forward, and stress evidence.

## Decision

`Research Alpha`, not `Shadow Candidate` or `Live Switch Candidate`.

No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

`docs/model_scoreboard.md` was updated because the current interpretation changed from "freshness policy fields missing from selected trade-delta attribution" to "freshness policy fields available in selected trade-delta attribution, but still blocked by proxy-only replay context and low contribution counts."

Next direction: build or connect a strict replay acceptance gate that can consume the same freshness context and produce validation/final drawdown, walk-forward, stress, and acceptance-gate details, or keep collecting until contribution support clears the shadow minimum.
