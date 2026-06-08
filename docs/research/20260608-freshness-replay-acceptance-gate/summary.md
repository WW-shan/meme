# 2026-06-08 Freshness Replay Acceptance Gate

## Live State

- Bot and collector were running under `./tools/memectl` in the expected `meme-bot` and `meme-collector` tmux sessions.
- `data/bot_state.json` showed balance `0.001559636535526772` BNB and no open positions.
- Live config stayed unchanged: `ENABLE_TRADING=true`, `MODEL_DIR=data/models/20260519_v95_v84_selective_nearmiss_gate`, `POSITION_SIZE=0.10`, and `MIN_ENTRY_VOLUME_30S=1.5`.
- Latest real close remained the `2026-06-07 12:25:39.499918` trailing-stop winner for `+0.00005553972801680855` BNB.

## Fresh Attribution

Fresh report:

- `data/replay_reports/live_trade_attribution_20260608_freshness_replay_acceptance_gate_entry.json`
- `data/replay_reports/live_trade_attribution_20260608_freshness_replay_acceptance_gate_entry.md`

Since the `2026-06-07 12:25:39.499918` anchor, there were `0` closed trades and the attribution report stayed `NO_GO_FOR_LIVE_SWITCH`.

Rejected-path support:

- Signal decisions: `5221`.
- Per-token candidates: `417`.
- Barrier classes: `fast_profit=22`, `fast_profit_then_collapse=16`, `slow_runner=11`, `flat_timeout=304`, and `stop_first=64`.
- Recommended policies: `quick_take_profit=38`, `conditional_slow_hold=11`, and `skip=368`.

## Prior Research Reused

No new SmartSearch Deep Research was needed because this round did not introduce a new outside method. It reused the existing SmartSearch-backed freshness/meta-labeling, selected trade-delta, and strict replay methodology with a new live-derived question: can the selected proxy freshness rule be evaluated in strict replay validation/final samples before building a replay acceptance gate?

Relevant prior summaries:

- `docs/research/20260608-signal-context-freshness-bridge/summary.md`
- `docs/research/20260608-strict-freshness-sample-bridge/summary.md`

## Hypothesis

The selected proxy rule from the prior freshness bridge was:

```text
freshness_latency_volume_risk >= 1.2906080427027575
```

That rule can only advance beyond proxy `Research Alpha` if strict replay validation/final samples or replay trade logs contain enough decision-time context to compute it:

- `lifecycle_status_chain_lag_seconds`
- `signal_volume_30s`
- `signal_price_volatility`

Falsification rule: if strict replay sample/trade-log coverage has `lifecycle_status_chain_lag_seconds` missing and therefore cannot compute `freshness_latency_volume_risk`, reject this direction as a strict replay gate for now.

## Experiment

Strict replay context audit:

- `data/replay_reports/execution_freshness_replay_context_audit_20260608_freshness_replay_acceptance_gate.json`
- `data/replay_reports/execution_freshness_replay_context_audit_20260608_freshness_replay_acceptance_gate.md`

The audit loaded the same strict validation/final replay samples used by the existing replay gate scripts, then ran 10% live-sized baseline replay with trade logs and measured freshness-policy feature coverage from both matched replay samples and replay trade-log entry context.

Strict assumptions stayed fixed:

- `position_fraction=0.1`
- `max_position_fraction=0.1`
- `max_open_positions=8`
- `fixed_stake_bnb=None`
- `skip_all_in_replay=True`

## Results

Validation:

- Samples: `140332`.
- Baseline replay trades: `23`.
- Baseline net profit: `0.012252343033424175` BNB.
- Baseline win rate: `0.7391304347826086`.
- `signal_volume_30s`: available from sample `volume_30s` and trade context `entry_volume_30s` / `volume_30s`.
- `signal_price_volatility`: available from sample `price_volatility` and trade context `entry_price_volatility` / `price_volatility`.
- `lifecycle_status_chain_lag_seconds`: missing in samples and replay trade context.
- Selected rule replayable from strict replay context: `False`.

Final:

- Samples: `204708`.
- Baseline replay trades: `24`.
- Baseline net profit: `0.0020282580548887895` BNB.
- Baseline win rate: `0.5416666666666666`.
- `signal_volume_30s`: available from sample `volume_30s` and trade context `entry_volume_30s` / `volume_30s`.
- `signal_price_volatility`: available from sample `price_volatility` and trade context `entry_price_volatility` / `price_volatility`.
- `lifecycle_status_chain_lag_seconds`: missing in samples and replay trade context.
- Selected rule replayable from strict replay context: `False`.

## Strict Evaluation

The blocker is specific: strict replay already has the market-state inputs (`volume_30s` and `price_volatility`), but it does not carry decision-time lifecycle freshness (`lifecycle_status_chain_lag_seconds`). Therefore the selected proxy rule cannot be tested as a strict replay candidate gate today.

This does not invalidate the proxy freshness rule. It prevents promotion beyond proxy `Research Alpha` because strict replay cannot compute the rule's required decision-time freshness input.

## Decision

`Rejected` as a strict replay acceptance gate for now.

Replay-audit decision: `rejected_strict_replay_context_missing`.

No live switch. No `.env`, threshold, sizing, model artifact, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

`docs/model_scoreboard.md` was updated because the experiment changed the next-step interpretation: the selected freshness rule is not ready for strict replay promotion until replay sample construction records decision-time lifecycle freshness fields.

Next direction: either add decision-time lifecycle freshness fields to a replay-compatible sample surface before retesting this exact rule, or pivot to another strict-replayable direction such as the accepted-action router shadow evidence.
