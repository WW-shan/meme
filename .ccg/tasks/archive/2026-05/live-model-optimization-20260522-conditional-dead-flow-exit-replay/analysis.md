# Analysis

## Current State Check

- Worktree clean at start; latest commit is `616a2f5 research: refresh live trade attribution`.
- No active non-archive CCG task exists before this task.
- `docs/goals/**` guard is clean.
- `.ccg/spec` is absent.
- Bot and collector are running; bot has `0` open positions and balance `0.003471730065131376` BNB.
- `data/paper_trades.jsonl` still has last close `币安队长` at `2026-05-21 20:42:26`, `TIME_EXIT`, net `-0.000030418340289465923` BNB.
- `data/signal_audit.jsonl` is live through `2026-05-22 07:17:31` with rejected `发光法宝` decisions.

## Prior Round Result

The last completed round rebuilt live attribution from raw paper trades and lifecycle files. It confirmed v95 since restart has `18` closed real trades, `2` wins, `16` losses, net `-0.001256566334920428` BNB, and full lifecycle coverage. The dominant actionable bucket is near-threshold dead-flow timeout: near trades `8`, with `dead_flow_timeout=6` and `unprofitable_other=2`.

## Candidate Direction

The smallest next falsifiable experiment is a replay-only conditional dead-flow exit, not another broader entry overlay. Hypothesis: for positions that have not made meaningful MFE after a short post-entry window and match weak/dead flow conditions, exit earlier than current timeout/stop behavior to reduce losses without cutting durable runners.

Open questions before implementation:

- What exact replay fields are available at runtime decision time in `model_replay.py`?
- Can the exit be implemented default-off with manifest/replay overrides and no live change?
- Which grid is small enough to finish quickly while still falsifying the hypothesis?
- Which baseline splits/reports should be used for validation and sealed final?

External Claude analysis is pending.

## External Claude Analysis — 2026-05-22

- Claude agrees the dead-flow-exit-only replay is the right next experiment, because it only modifies exits for already accepted v95 entries and does not repeat the rejected entry-overlay expansion failure.
- Critical gates: freeze baseline entry set, avoid MFE lookahead, and protect profitable baseline exits from being worsened.
- Recommended grid: `buy_dead_flow_exit_min_hold_seconds in {90,120,180,240}` and `buy_dead_flow_exit_max_mfe_pct in {0.03,0.05,0.08}` for 12 bounded candidates.
- Required acceptance: validation + final + walk-forward + stress must beat/preserve baseline under 10% sizing and max 8 positions; validation net profit improvement should be material, and no candidate should pass if frozen entry signatures differ from baseline.
- Safe implementation shape: add a thin replay script and report using existing default-off `DEAD_FLOW_TIME_EXIT` support; do not alter live runtime defaults.

## Code Path Findings

- `src/pipeline/train_hybrid.py` already supports default-off `buy_dead_flow_exit_min_hold_seconds` and `buy_dead_flow_exit_max_mfe_pct` in `_run_eval_replay`.
- `src/pipeline/model_replay.py` already exposes both parameters in `live_replay_config_from_manifest` defaults as `None`.
- Existing tests in `tests/model/test_flow_activation_replay.py` cover the basic `DEAD_FLOW_TIME_EXIT` mechanics.
- Missing piece for this round is a dead-flow-only replay grid/report that freezes entries and does not include flow-activation entry-side gates.
