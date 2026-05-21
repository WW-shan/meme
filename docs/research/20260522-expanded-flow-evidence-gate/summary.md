# Expanded Flow Evidence Gate - 2026-05-22

## Contract

- Active live model remains `data/models/20260519_v95_v84_selective_nearmiss_gate`.
- Live sizing remains 10% position fraction with max 8 open positions.
- This round is read-only research evidence plus safer probe tooling.
- No `.env`, `data/models/**`, live service, runtime threshold, position sizing, or `docs/goals/**` change is justified by this round.

## Why This Round Ran

The previous May 22 flow quick-profit overlay stopped before runtime/replay work because pooled support was too small and required flow fields were incomplete. The useful next question was whether that was just a sampling/tooling limit.

`src/pipeline/time_to_barrier_probe.py` previously emitted only `candidate_sample = candidates[:100]`. That cap was not a problem for the prior `66 + 38` candidate reports, but it blocked a larger evidence expansion. This round added a default-preserving all-candidate option:

- default remains `max_candidate_sample=100`;
- `--max-candidate-sample 0` emits all scored candidates;
- report metadata now records `emitted_candidate_count`, `sample_limited`, and `unemitted_candidate_count`.

## Reports

- Expanded all-candidate barrier report: `data/replay_reports/time_to_barrier_probe_20260522_expanded_flow_since20260521_all_candidates.json`
- Expanded pooled support gate: `data/replay_reports/support_action_policy_pool_20260522_expanded_flow_all_candidates.json`
- Post-hoc diagnostic rule scan: `data/replay_reports/support_action_policy_flow_rule_diagnostic_20260522_expanded.json`

Expanded barrier command:

```bash
venv/bin/python scripts/probe_time_to_barrier.py \
  --since '2026-05-21 00:00:00' \
  --recent-lifecycle-files 3 \
  --max-candidate-sample 0 \
  --output data/replay_reports/time_to_barrier_probe_20260522_expanded_flow_since20260521_all_candidates.json
```

Support gate command:

```bash
venv/bin/python scripts/probe_support_action_policy_pool.py \
  --time-to-barrier-report data/replay_reports/time_to_barrier_probe_20260522_expanded_flow_since20260521_all_candidates.json \
  --output data/replay_reports/support_action_policy_pool_20260522_expanded_flow_all_candidates.json \
  --min-pooled-selected 30 \
  --min-pooled-positive 12 \
  --force
```

## Expanded Evidence

The expanded time-to-barrier report covers `2026-05-21 00:00:00` through the current live audit snapshot:

| Metric | Value |
|---|---:|
| Signal decisions | `22093` |
| Per-token candidates | `832` |
| Emitted candidates | `832` |
| Sample limited | `false` |
| Quick-take-profit labels | `144` |
| Conditional slow-hold labels | `12` |
| Skip labels | `676` |
| Base positive rate | `18.75%` |

The pre-registered `high_prob_low_toxic_overlap` target rule selected a much larger support set than before:

| Metric | Prior pooled gate | Expanded gate |
|---|---:|---:|
| Input candidates | `104` | `832` |
| Positive candidates | `22` | `156` |
| Target selected | `13` | `135` |
| Target positives | `9` | `64` |
| Target negatives | `4` | `71` |
| Target precision | `69.23%` | `47.41%` |
| Required selected | `30` | `30` |
| Required positives | `12` | `12` |

This changes the diagnosis: the rule is no longer only too small. It now has enough count support, but it admits too many skip/stop/flat cases and still fails the required flow parity gate.

Flow parity stayed incomplete:

| Required field | Finite count |
|---|---:|
| `flow_event_count_30s` | `832/832` |
| `flow_buy_sell_overlap_ratio_60s` | `607/832` |
| `flow_recent_seller_reentry_ratio_30s` | `544/832` |

The missing ratio values are not just missing data; they often arise when the denominator buyer set is empty. Treating those as `0.0` would incorrectly let sell-only/no-recent-buyer cases pass a low-overlap rule, so this round keeps them non-finite and does not weaken the gate.

## Diagnostic Rule Scan

A post-hoc rule scan was run only to understand whether any simple support shape deserves a future replay experiment. It is not live-switch evidence.

Best broad diagnostic rule in the scan:

- `prob >= 0.985`
- `age_seconds <= 60`
- `entry_volume_30s >= 1.25`
- `flow_event_count_30s >= 10`
- `flow_buy_sell_overlap_ratio_60s <= 0.5`

Result: `38` selected, `23` positives, `15` negatives, precision `60.53%`.

Best tightened target-family rule reached `25` selected, `15` positives, `10` negatives, precision `60.00%`.

These are better than the base positive rate, but still post-hoc, still include many negatives, and still require replay validation before any runtime overlay.

## Decision

Current status: `NO_GO_FOR_RUNTIME_OVERLAY`.

Reasons:

- The pre-registered expanded support gate still fails because required flow ratios are not finite for all candidates.
- The target rule's expanded precision dropped to `47.41%` with `71` selected negatives, too noisy for a direct runtime overlay.
- The better-looking active-flow shapes are post-hoc support diagnostics, not replay/live-switch evidence.
- No candidate has beaten the v95 baseline on validation, sealed final, walk-forward, harsh stress, drawdown, and trade-count discipline under 10% sizing.

## New Learning

The flow direction is not dead, but the simple low-toxic-overlap rule is not the deployable rule. Expanded evidence shows a stronger shape around young, high-probability, active-flow candidates (`flow_event_count_30s >= 10`) than around generic low overlap alone.

The next profitable experiment should be a replay-integrated, pre-registered active-flow candidate overlay or take/skip meta-filter. It must use a separate validation/final replay split and should not treat undefined buyer-overlap ratios as clean flow.
