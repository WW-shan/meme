# Signal/Flow Parity Reward Probe

Date: 2026-06-01
Status: Research Alpha diagnostic; rejected for replay promotion

## Outcome

No live switch and no shadow promotion.

This pass tested whether the newly available replay trade-view signal context could separate profitable added trades from toxic added trades, then ran a richer signal/flow reward probe rather than another one-dimensional volume or volatility threshold.

The result is useful but not deployable: simple `entry_volume_30s` / `entry_price_volatility` cuts do not separate winners from losers, and the reward probe learns mostly accepted action-policy continuation support, not enough rejected-signal opportunity support.

No `.env`, model artifact, threshold, sizing, buy/sell logic, bot process, collector process, runtime enablement, restart, or live runtime behavior changed.

## Live State

- Bot and collector were running under `memectl` and tmux.
- Open positions: `0`; `data/bot_state.json` positions are `{}`.
- Balance after the latest close: `0.002177546984955065` BNB.
- Live model: `data/models/20260519_v95_v84_selective_nearmiss_gate`.
- Live sizing stayed at `POSITION_SIZE=0.10`.
- Collector remains active but continues to show catch-up lag bursts; recent inspected tails had no fatal traceback.

Fresh live evidence since the post-parity CI boundary at `2026-06-01 08:22:49`:

- Signal decisions: `2669`; `2667` rejected and `2` queued/opened.
- Rejection reasons: `near_threshold_pred_return_below_min=1229`, `buy_model_reject=973`, `pred_return_below_min=371`, `entry_volume_30s_below_min=76`, `entry_price_volatility_below_min=18`.
- New winning trade: `.bts` queued at `2026-06-01 11:14:34`, opened at `11:14:42`, closed by `TRAILING_STOP` at `11:16:49` for `+0.00009917993972640104` BNB. Signal context: `prob=0.983569264260497`, `PredReturn=47.999762055963636`, `volume_30s=1.986927108910891`, `price_volatility=0.20739126493897317`, `chain_lag=16.617237091064453s`. Lifecycle path through the bot close: MFE `+55.93245899072432%` from entry, MAE `-4.1458744290066125%`. Full post-close lifecycle peak reached `+114.90601546458082%` from entry about `211s` after signal, so the trade also remains useful for conditional-exit / runner-retention analysis.
- New losing trade: `世界有无限可能` queued at `2026-06-01 11:52:59`, opened at `11:53:06`, closed by `TIME_EXIT` at `12:02:38` for `-0.00002290724674930617` BNB. Signal context: `prob=0.9744671460785141`, `PredReturn=41.26624201860377`, `volume_30s=4.137378613861387`, `price_volatility=0.34021583415725526`, `chain_lag=27.540877103805542s`, `near_threshold_rescue_used=true`. Lifecycle path after the queued signal had no upside; MFE from entry was `-0.4093595712530651%`, MAE `-1.9801980198035252%`.

The new pair reinforces the current structural problem: higher decision-time volume and volatility did not make the losing trade safer than the winner.

## Prior Work Reused

No new SmartSearch Deep Research was opened for this pass because the method is a replay-compatible extension of recent committed research rather than a new external method. The reused evidence is:

- `docs/research/20260527-accepted-entry-feature-selected-gate/summary.md` for meta-label / logged-policy framing.
- `docs/research/20260531-replay-compatible-execution-freshness/summary.md` for replay-compatible execution-risk constraints.
- `docs/research/20260601-replay-freshness-feature-parity/summary.md` for the freshly added replay trade-context feature coverage.
- `docs/research/20260601-execution-freshness-paired-delta-proxy/summary.md` for paired-delta evidence and proxy limitations.
- `docs/research/20260601-post-postphone-live-shadow-refresh/summary.md` for the latest guarded live-shadow rejection.

## Direction Selection

Ranked hypothesis portfolio:

1. Signal/flow parity reward meta-gate.
   Highest expected value because it uses replay-compatible `prob`, `PredReturn`, and flow fields instead of hard-coded chain-lag/staleness thresholds. Selected as the smallest structural falsification after feature parity.
2. Queued/opened freshness shadow accumulation.
   Useful but deferred because the latest post-parity slice had no queued/opened freshness candidates before this pass, and the freshest queued-only shadow still selected `0` validation rows.
3. Simple signal volume/volatility hard veto or rescue.
   Deprioritized because prior high-volume abstention and entry-volatility veto attempts failed, and this pass confirms added-trade winners and losers overlap strongly in replay trade context.
4. Conditional exit / early-profit harvest.
   Still important after `.bts`, but this pass did not produce a new replay-safe exit label; keep it for the next structural branch, not for this milestone.

Hypothesis: a richer signal/flow reward probe can identify replay-compatible utility support where one-dimensional volume/volatility gates fail.

Falsification rule: reject replay promotion if validation/final support is dominated by accepted-only examples, if rejected-signal selection is below support minimums, if final drawdown/stress/replay promotion gates are missing, or if selected trade context cannot explain added winners versus losers.

## Commands

```bash
venv/bin/python -m unittest tests.model.test_replay_trade_delta_attribution
```

```bash
venv/bin/python scripts/run_primary_score_scalp_replay.py \
  --candidate-grid-json docs/research/20260601-negative-pred-ultrashort-quick-profit/negative_pred_ultrashort_grid.json \
  --output data/replay_reports/replay_freshness_signal_context_trade_view_20260601.json \
  --write-selected-trade-delta \
  --force
```

```bash
venv/bin/python scripts/probe_action_policy_reward.py \
  --train-rejected-report data/replay_reports/live_trade_attribution_20260601_replay_compat_freshness_entry.json \
  --train-accepted-report data/replay_reports/post_target_exit_state_probe_20260521_v95_train.json \
  --validation-rejected-report data/replay_reports/live_trade_attribution_20260601_post_replay_parity_ci.json \
  --validation-accepted-report data/replay_reports/post_target_exit_state_probe_20260521_v95_validation.json \
  --final-rejected-report data/replay_reports/live_trade_attribution_20260601_post_phone_reject_refresh.json \
  --final-accepted-report data/replay_reports/post_target_exit_state_probe_20260521_v95_final.json \
  --output data/replay_reports/action_policy_reward_probe_20260601_signal_context_parity.json \
  --force
```

```bash
venv/bin/python scripts/probe_action_policy_reward.py \
  --train-rejected-report data/replay_reports/time_to_barrier_probe_20260523_1615_since_142149_flowparity.json \
  --train-accepted-report data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_train_enriched.json \
  --validation-rejected-report data/replay_reports/live_trade_attribution_20260601_replay_compat_freshness_entry.json \
  --validation-accepted-report data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_validation.json \
  --final-rejected-report data/replay_reports/live_trade_attribution_20260601_post_replay_parity_ci.json \
  --final-accepted-report data/replay_reports/post_target_exit_state_probe_20260526_support_complete_entryflow_final.json \
  --output data/replay_reports/action_policy_reward_probe_20260601_signal_flow_parity.json \
  --force
```

## Results

Replay trade-view context report:

- Artifact: `data/replay_reports/replay_freshness_signal_context_trade_view_20260601.json`.
- Decision: `reject`.
- Baseline validation: `0.022842003299308057` BNB net profit, `38` trades, `81.57894736842105%` win rate, `-10.187954315383251%` max drawdown.
- Best validation candidate: `0.0386373291806712` BNB net profit, `511` trades, `48.336594911937375%` win rate, `-19.539228260041263%` max drawdown.
- Final confirmation candidate: `-0.0038727655404503423` BNB net profit, `440` trades, `35.45454545454545%` win rate, `-85.7854786802085%` max drawdown, stress worst net profit `-0.005077346322729664` BNB.
- Final confirmation failed.

Selected trade-context inspection:

| Split / Delta Set | Trades | Winners | Losses | Return Sum | `entry_volume_30s` median | `entry_price_volatility` median |
|---|---:|---:|---:|---:|---:|---:|
| Validation added candidate | `474` | `217` | `257` | `+3122.874505%` | `2.265347` | `0.154462` |
| Validation removed baseline | `1` | `1` | `0` | `+119.844972%` | `1.549401` | `0.168793` |
| Final added candidate | `423` | `147` | `276` | `-2789.514015%` | `2.205815` | `0.159781` |
| Final removed baseline | `4` | `2` | `2` | `+118.985653%` | `1.777614` | `0.150084` |

Within added candidate trades, positive and negative examples overlap:

- Validation added positives: volume median `2.285879`, volatility median `0.155970`.
- Validation added negatives: volume median `2.245570`, volatility median `0.150924`.
- Final added positives: volume median `2.108157`, volatility median `0.154818`.
- Final added negatives: volume median `2.278841`, volatility median `0.161024`.

Diagnostic schema mismatch report:

- Artifact: `data/replay_reports/action_policy_reward_probe_20260601_signal_context_parity.json`.
- Decision: `diagnostic_only_support_blocked`.
- Support gate failed: `common_decision_features_below_min`.
- Interpretation: older accepted reports do not share enough decision-time fields with rejected reports; they are not a valid support base for this parity probe.

Support-complete signal/flow reward report:

- Artifact: `data/replay_reports/action_policy_reward_probe_20260601_signal_flow_parity.json`.
- Decision: `shadow_only_support_limited`.
- Support gate: failed.
- Failure reasons: `validation_rejected_selection_below_min`, `final_rejected_selection_below_min`.
- Model features: `pred_return` importance `0.8306789039018647`, `prob` `0.09568459219393464`, `flow_total_volume_30s` `0.04672498546814197`, `flow_buy_volume_10s` `0.02691151843605868`.
- Train selected `105` rows for `+13053.8700829708%` reward; family counts `accepted=100`, `rejected=5`.
- Validation selected `31` rows for `+2825.4735267161%` reward; family counts `accepted=31`, `rejected=0`.
- Final selected `20` rows for `+1394.2609933805%` reward; family counts `accepted=20`, `rejected=0`.

## Decision

Classification: Research Alpha diagnostic, rejected for replay promotion.

The signal/flow reward probe is not a live-switch candidate, not a Shadow Candidate, and not a strict replay model candidate. It indicates that richer flow context may help accepted action-policy continuation labels, but it does not select enough rejected-signal opportunities in validation/final to justify a replay-expanded rejected-signal branch.

`docs/model_scoreboard.md` was updated because this changes next-direction constraints: avoid simple volume/volatility threshold sweeps, and treat signal/flow reward evidence as accepted-action-policy support only until rejected-signal support appears.

Next direction: use the latest `.bts` winner versus `世界有无限可能` near-threshold loss as fresh live evidence for a conditional exit / early-profit harvest or accepted-only action-policy continuation probe, rather than another rejected-signal volume/volatility micro-sweep.
