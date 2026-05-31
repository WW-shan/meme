# Execution Freshness Phone-Close Refresh

Date: 2026-06-01
Status: Research Alpha

## Question

Does the new live `手机` trade change the execution-freshness direction after it closed as another high-lag `TIME_EXIT` loss?

This is not a new method search. It reuses the existing execution-freshness paired-delta proxy and queued-only freshness shadow workflow from the 2026-06-01 freshness boundary. No new SmartSearch run was needed.

## Live Event

`手机` opened at `2026-06-01 00:48:27.271369` and closed at `2026-06-01 00:58:01.684785` by `TIME_EXIT`.

- Net profit: `-0.000023685576496972164` BNB
- Hold duration: `574.413416s`
- Entry signal probability: `0.9794600007036288`
- PredReturn: `51.21673163553452`
- Entry slippage: `+1.9363878503417586%`
- Token status source: `helper`
- Lifecycle chain lag at entry: `26.06060004234314s`
- Signal-to-open time: `8.212588s`

The bot and collector were left running. There was no `.env`, model artifact, threshold, sizing, buy/sell logic, runtime enablement, restart, or live switch change.

## Artifacts

- Live attribution: `data/replay_reports/live_trade_attribution_20260601_after_phone_close.json`
- Live attribution markdown: `data/replay_reports/live_trade_attribution_20260601_after_phone_close.md`
- Freshness proxy: `data/replay_reports/execution_freshness_signal_context_paired_delta_20260601_after_phone_close.json`
- Uncertainty gate: `data/replay_reports/replay_uncertainty_gate_20260601_execution_freshness_after_phone_close.json`
- Queued-only shadow: `data/replay_reports/signal_freshness_queued_only_shadow_20260601_after_phone_close.json`
- Queued-only shadow markdown: `data/replay_reports/signal_freshness_queued_only_shadow_20260601_after_phone_close.md`

## Results

Live attribution since the prior `长涨` close now has:

- Closed trades: `1`
- Wins/losses: `0/1`
- Net profit: `-0.000023685576496972164` BNB
- Failure label: `dead_flow_timeout`
- Decision: `NO_GO_FOR_LIVE_SWITCH`
- Rejected signal paths: `6454` signal decisions, `508` per-token candidates
- Barrier classes: `fast_profit=15`, `fast_profit_then_collapse=24`, `slow_runner=9`, `flat_timeout=360`, `stop_first=99`, `missing_path=1`

The accepted-trade paired-delta proxy now has `54` paired real trades. The selected train-derived rule stayed:

- `lifecycle_status_chain_lag_seconds >= 2.2289199829101562`

Proxy split metrics:

| Split | Selected | Winners | Losses | Abstention Delta BNB | Delta Without Top Loss Benefit |
|---|---:|---:|---:|---:|---:|
| Train | `13` | `4` | `9` | `+0.00013578191663165585` | `-0.00009237487360547062` |
| Validation | `2` | `0` | `2` | `+0.0003500284027941525` | `+0.00015238787562031852` |
| Final | `8` | `0` | `8` | `+0.0004965964430227051` | `+0.00033268770000437637` |

Final selected symbols were `42`, `币安盲盒`, repeated `帕鲁`, `四川话`, `长涨`, and `手机`. The new `手机` loss is selected by the same chain-lag rule.

Uncertainty gate:

- Outcome tier: `Research Alpha`
- Decision: `uncertain_research_alpha_not_shadow`
- Validation positive probability: `0.89475`
- Final positive probability: `1.0`
- Shadow blocker: `strict_replay_gate_context_missing`

Queued-only signal shadow increased from `5` to `6` freshness candidates after `手机`, but remains rejected:

- Decision: `insufficient_signal_freshness_split_support`
- Selected rule: `lifecycle_status_chain_lag_seconds >= 18.403747081756592`
- All selected: `5/5` correct skips, `0` opportunity misses
- Validation selected: `0`
- Stable rule count: `0`

## Decision

Keep execution freshness as stronger `Research Alpha`, not `Shadow Candidate` and not `Live Switch Candidate`.

The new live loss strengthens the same high-lag accepted-loss family, but the blocker is unchanged: the strongest evidence is still proxy/paired-delta evidence, not strict replay with drawdown, walk-forward, stress, and deployable runtime feature equivalence. Queued-only shadow support is growing but still far below the split-stability gate.

Scoreboard: `docs/model_scoreboard.md` was updated because this boundary adds a fresh real loss to the execution-freshness family and changes the proxy final support from `7/7` to `8/8` selected losses.
