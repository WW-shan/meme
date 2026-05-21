# Analysis

## Current Authoritative State

- Worktree started clean at commit `7fa244c` (`origin/main`).
- No active CCG task existed before this round.
- `.ccg/spec/` is absent.
- `docs/goals/**` has no working-tree or staged changes and is protected for this round.
- Previous May 22 task was archived and pushed before this round.

## Prior Evidence

Previous round conclusion:

- `entry_slippage_risk_veto`: `NO_GO_FOR_LIVE_RULE`.
- `flow quick-profit overlay`: `NO_GO_FOR_RUNTIME_OVERLAY`.

The flow overlay failed for two reasons:

- Pooled target support was too small: `high_prob_low_toxic_overlap` selected `13` with `9` positives versus required `30` selected and `12` positives.
- Flow feature parity was incomplete across `104` candidates: `flow_event_count_30s` finite `103/104`, `flow_buy_sell_overlap_ratio_60s` finite `80/104`, `flow_recent_seller_reentry_ratio_30s` finite `71/104`.

## Local Codex Read

The current `time_to_barrier_probe.build_probe_report()` always emits only `candidate_sample = candidates[:100]`. This was fine for the two previous reports (`66` and `38` candidates), but it becomes a blocker for the next useful evidence expansion because any larger `--since` window can report more than 100 per-token candidates while the support gate can only evaluate the first 100 rows.

`support_action_policy_probe.build_pooled_support_report()` already records `input_reported_candidates`, `sample_limited`, and `unscored_reported_candidates`, so the safer next move is to make `probe_time_to_barrier` optionally emit all scored candidates for explicit research runs, rather than changing support gate semantics or live runtime behavior.

## Proposed Experiment

1. Add a default-preserving `--max-candidate-sample` option to `scripts/probe_time_to_barrier.py` and matching parameter in `src/pipeline/time_to_barrier_probe.build_probe_report()`.
2. Keep default behavior at `100` for compatibility.
3. Let `--max-candidate-sample 0` mean emit all candidates, with report metadata documenting whether the output is sample-limited.
4. Generate an expanded read-only report from `2026-05-21 00:00:00` using recent May lifecycle files and all candidates.
5. Pool the expanded report with prior flow evidence using the existing support gate. Do not implement runtime overlay unless the pre-registered support gate passes.

## Risk Assessment

- Complexity: M (CLI + pipeline + tests + reports/docs).
- Risk: medium (research tooling behavior changes; no live runtime changes planned).
- Requires external Claude analysis and review per CCG.

## External Claude Analysis Status

External Claude analysis was started via `~/.claude/bin/codeagent-wrapper --backend claude` with log `/Users/ww/.claude/logs/codeagent-wrapper-shim-28470.log`. It was allowed to run for about 20 minutes. The process repeatedly hit Claude API `504 server_error` retries and did not produce a final analysis. To avoid stalling the user-approved goal loop indefinitely, the process was stopped and this round proceeds with the conservative, default-off plan above. External Claude review will be retried after the code/report changes, and this failed analysis attempt remains recorded in the task evidence.

## Experiment Result

The expanded all-candidate report emitted `832/832` per-token candidates from `22093` rejected signal decisions since `2026-05-21 00:00:00`, with `156` positive oracle labels (`144` quick-take-profit and `12` conditional-slow-hold) and `676` skips.

The pre-registered pooled support gate still returned `decision=missing_flow_feature_parity`:

- target `high_prob_low_toxic_overlap`: `135` selected, `64` positives, `71` negatives, precision `47.41%`.
- count support now clears `30` selected and `12` positives.
- flow parity still fails: `flow_buy_sell_overlap_ratio_60s` finite `607/832`; `flow_recent_seller_reentry_ratio_30s` finite `544/832`.

A post-hoc diagnostic scan found a better active-flow shape (`prob>=0.985`, `age_seconds<=60`, `entry_volume_30s>=1.25`, `flow_event_count_30s>=10`, `flow_buy_sell_overlap_ratio_60s<=0.5`) with `38` selected, `23` positives, `15` negatives, precision `60.53%`. This is support-only and post-hoc, so it is not live-switch evidence.

Decision: `NO_GO_FOR_RUNTIME_OVERLAY`. The next research direction is a replay-integrated, pre-registered active-flow candidate overlay/meta-filter, not a direct runtime switch from this support evidence.
